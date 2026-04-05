import hashlib
import hmac
import json
import os
import time
import uuid
import base64
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import sys

import requests

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from config.env import get_env, get_env_float, get_env_int
from services.storage.tencent_cos_storage import TencentCOSStorage


class Task4BLessonAudioRenderer:
    HOST = "tts.tencentcloudapi.com"
    ENDPOINT = f"https://{HOST}"
    SERVICE = "tts"
    VERSION = "2019-08-23"
    ALGORITHM = "TC3-HMAC-SHA256"
    DEFAULT_ROLE_VOICE_MAP = {
        "王朋": 601011,
        "李友": 601009,
        "高文中": 601008,
        "高小音": 601013,
        "白英爱": 601010,
        "常老师": 601013,
        "王红": 601010,
        "海伦": 501004,
        "费先生": 501005,
        "王朋的父母": 501005,
    }

    def __init__(
        self,
        secret_id: str | None = None,
        secret_key: str | None = None,
        voice_type: int | None = None,
        codec: str = "mp3",
        sample_rate: int = 16000,
        speed: float | None = None,
        volume: float = 0.0,
        model_type: int = 1,
        primary_language: int = 1,
        project_id: int = 0,
        sentence_gap_ms: int = 300,
        poll_interval_seconds: int = 3,
        request_timeout_seconds: int = 60,
    ):
        self.secret_id = (secret_id or get_env("TTS_TENCENT_SECRET_ID", default="") or "").strip()
        self.secret_key = (secret_key or get_env("TTS_TENCENT_SECRET_KEY", default="") or "").strip()
        self.voice_type = voice_type or get_env_int("TTS_TENCENT_DEFAULT_VOICE_TYPE", default=301001)
        self.role_voice_map = self._load_role_voice_map()
        self.codec = codec
        self.sample_rate = sample_rate
        self.speed = speed if speed is not None else get_env_float("TTS_TENCENT_SPEED", default=-0.2)
        self.volume = volume
        self.model_type = model_type
        self.primary_language = primary_language
        self.project_id = project_id
        self.sentence_gap_ms = get_env_int("TTS_TENCENT_SENTENCE_GAP_MS", default=sentence_gap_ms)
        self.poll_interval_seconds = poll_interval_seconds
        self.request_timeout_seconds = request_timeout_seconds
        self.cos_storage = TencentCOSStorage.from_env(optional=True)

    def _require_credentials(self):
        if not self.secret_id or not self.secret_key:
            raise ValueError("TTS_TENCENT_SECRET_ID / TTS_TENCENT_SECRET_KEY 未配置，无法调用腾讯云 TTS。")

    def _load_role_voice_map(self) -> dict[str, int]:
        env_mapping = (get_env("TTS_TENCENT_ROLE_VOICE_MAP_JSON", default="") or "").strip()
        role_map = dict(self.DEFAULT_ROLE_VOICE_MAP)
        if not env_mapping:
            return role_map

        try:
            parsed = json.loads(env_mapping)
        except json.JSONDecodeError:
            return role_map

        if not isinstance(parsed, dict):
            return role_map

        for role, voice in parsed.items():
            try:
                role_map[str(role)] = int(voice)
            except (TypeError, ValueError):
                continue
        return role_map

    def _sha256_hex(self, value: str) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    def _hmac_sha256(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _sign_headers(self, action: str, payload: dict[str, Any]) -> dict[str, str]:
        self._require_credentials()

        timestamp = int(time.time())
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

        canonical_headers = f"content-type:application/json; charset=utf-8\nhost:{self.HOST}\n"
        signed_headers = "content-type;host"
        canonical_request = "\n".join([
            "POST",
            "/",
            "",
            canonical_headers,
            signed_headers,
            self._sha256_hex(payload_json),
        ])

        credential_scope = f"{date}/{self.SERVICE}/tc3_request"
        string_to_sign = "\n".join([
            self.ALGORITHM,
            str(timestamp),
            credential_scope,
            self._sha256_hex(canonical_request),
        ])

        secret_date = self._hmac_sha256(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = self._hmac_sha256(secret_date, self.SERVICE)
        secret_signing = self._hmac_sha256(secret_service, "tc3_request")
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization = (
            f"{self.ALGORITHM} "
            f"Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        return {
            "Authorization": authorization,
            "Content-Type": "application/json; charset=utf-8",
            "Host": self.HOST,
            "X-TC-Action": action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": self.VERSION,
        }

    def _post(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(
            self.ENDPOINT,
            headers=self._sign_headers(action, payload),
            data=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
            timeout=self.request_timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        response_body = data.get("Response", {}) if isinstance(data.get("Response"), dict) else {}
        error = response_body.get("Error", {}) if isinstance(response_body.get("Error"), dict) else {}
        if error:
            code = error.get("Code", "UnknownError")
            message = error.get("Message", "Unknown Tencent TTS error")
            request_id = response_body.get("RequestId", "")
            raise RuntimeError(f"Tencent TTS API error [{code}] {message} | RequestId={request_id}")
        return data

    def _build_dialogue_text(self, dialogues: list, include_speakers: bool = False) -> str:
        lines_out = []
        for block in dialogues:
            if not isinstance(block, dict):
                continue
            lines = block.get("lines", [])
            if not isinstance(lines, list):
                continue
            for line in lines:
                if not isinstance(line, dict):
                    continue
                words = line.get("words", [])
                hanzi = "".join(
                    word.get("cn", "")
                    for word in words
                    if isinstance(word, dict)
                ).strip()
                if not hanzi:
                    continue
                role = (line.get("role") or "").strip()
                line_text = f"{role}：{hanzi}" if include_speakers and role else hanzi
                lines_out.append(line_text)
        return "\n".join(lines_out).strip()

    def _resolve_voice_type(self, role: str) -> int:
        role = (role or "").strip()
        return self.role_voice_map.get(role, self.voice_type)

    def _extract_sentence_items(self, lesson_data: dict, include_speakers: bool = False) -> list[dict[str, Any]]:
        course_content = lesson_data.get("course_content", {}) if isinstance(lesson_data.get("course_content"), dict) else {}
        dialogues = course_content.get("dialogues", []) if isinstance(course_content.get("dialogues"), list) else []

        items = []
        global_ref = 1
        for block in dialogues:
            if not isinstance(block, dict):
                continue
            lines = block.get("lines", [])
            if not isinstance(lines, list):
                continue
            for line in lines:
                if not isinstance(line, dict):
                    continue
                role = (line.get("role") or "").strip()
                words = line.get("words", [])
                hanzi = "".join(
                    word.get("cn", "")
                    for word in words
                    if isinstance(word, dict)
                ).strip()
                if not hanzi:
                    global_ref += 1
                    continue
                line_text = f"{role}：{hanzi}" if include_speakers and role else hanzi
                items.append({
                    "line_ref": global_ref,
                    "role": role,
                    "hanzi": hanzi,
                    "source_text": line_text,
                })
                global_ref += 1
        return items

    def build_audio_plan(self, lesson_data: dict, include_speakers: bool = False) -> dict[str, Any]:
        lesson_metadata = lesson_data.get("lesson_metadata", {}) if isinstance(lesson_data.get("lesson_metadata"), dict) else {}
        course_content = lesson_data.get("course_content", {}) if isinstance(lesson_data.get("course_content"), dict) else {}
        dialogues = course_content.get("dialogues", []) if isinstance(course_content.get("dialogues"), list) else []

        dialogue_text = self._build_dialogue_text(dialogues, include_speakers=include_speakers)
        return {
            "audio_plan": {
                "lesson_id": lesson_metadata.get("lesson_id"),
                "course_id": lesson_metadata.get("course_id"),
                "lesson_title": lesson_metadata.get("title", ""),
                "provider": "tencent_tts",
                "mode": "full_dialogue_audio",
                "voice_type": self.voice_type,
                "codec": self.codec,
                "sample_rate": self.sample_rate,
                "source_text": dialogue_text,
                "text_length": len(dialogue_text),
                "include_speakers": include_speakers,
            }
        }

    def _text_to_voice(
        self,
        text: str,
        session_id: str | None = None,
        enable_subtitle: bool = False,
        voice_type: int | None = None,
    ) -> dict[str, Any]:
        payload = {
            "Text": text,
            "SessionId": session_id or f"tts-{uuid.uuid4()}",
            "ProjectId": self.project_id,
            "ModelType": self.model_type,
            "Volume": self.volume,
            "Codec": self.codec,
            "VoiceType": voice_type or self.voice_type,
            "SampleRate": self.sample_rate,
            "PrimaryLanguage": self.primary_language,
            "Speed": self.speed,
            "EnableSubtitle": enable_subtitle,
        }
        response = self._post("TextToVoice", payload)
        return response.get("Response", {}) if isinstance(response.get("Response"), dict) else {}

    def _compose_full_lesson_audio(
        self,
        audio_files: list[Path],
        output_path: Path,
    ) -> Path | None:
        if not audio_files:
            return None

        concat_manifest = output_path.with_suffix(".concat.txt")
        silence_file = output_path.with_suffix(".gap.mp3")

        lines = []

        try:
            if self.sentence_gap_ms > 0 and len(audio_files) > 1:
                silence_duration_seconds = max(self.sentence_gap_ms, 0) / 1000
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "lavfi",
                        "-i",
                        f"anullsrc=r={self.sample_rate}:cl=mono",
                        "-t",
                        f"{silence_duration_seconds:.3f}",
                        "-q:a",
                        "9",
                        "-acodec",
                        "libmp3lame",
                        str(silence_file),
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

            for index, file in enumerate(audio_files):
                normalized_path = file.resolve().as_posix().replace("'", "'\\''")
                lines.append(f"file '{normalized_path}'")
                if silence_file.exists() and index < len(audio_files) - 1:
                    silence_path = silence_file.resolve().as_posix().replace("'", "'\\''")
                    lines.append(f"file '{silence_path}'")

            concat_manifest.write_text("\n".join(lines), encoding="utf-8")

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_manifest),
                    "-c",
                    "copy",
                    str(output_path),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return output_path if output_path.exists() else None
        finally:
            if concat_manifest.exists():
                concat_manifest.unlink()
            if silence_file.exists():
                silence_file.unlink()

    def _probe_audio_duration_seconds(self, audio_file: Path) -> float:
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(audio_file),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            return max(0.0, float((result.stdout or "").strip() or 0.0))
        except Exception:
            return 0.0

    def submit_full_dialogue_audio(self, lesson_data: dict, include_speakers: bool = False) -> dict[str, Any]:
        plan = self.build_audio_plan(lesson_data, include_speakers=include_speakers)
        audio_plan = plan["audio_plan"]
        text = audio_plan.get("source_text", "")
        if not text:
            raise ValueError("当前 lesson 没有可用于合成的课文原文。")

        payload = {
            "Text": text,
            "ProjectId": self.project_id,
            "ModelType": self.model_type,
            "Volume": self.volume,
            "Codec": self.codec,
            "VoiceType": self.voice_type,
            "SampleRate": self.sample_rate,
            "PrimaryLanguage": self.primary_language,
            "Speed": self.speed,
            "EnableSubtitle": False,
        }
        response = self._post("CreateTtsTask", payload)
        response_data = response.get("Response", {}) if isinstance(response.get("Response"), dict) else {}
        raw_task_data = response_data.get("Data")
        if isinstance(raw_task_data, dict):
            task_id = (raw_task_data.get("TaskId") or "").strip()
        elif isinstance(raw_task_data, str):
            task_id = raw_task_data.strip()
        else:
            task_id = ""

        if not task_id:
            raise RuntimeError(
                "Tencent TTS 提交成功但未返回 task_id，请检查音色、服务开通状态或计费配置。"
            )

        return {
            "audio_render_artifacts": {
                **audio_plan,
                "status": "submitted",
                "task_id": task_id,
                "request_id": response_data.get("RequestId", ""),
                "result_url": "",
                "error_message": "",
            }
        }

    def render_sentence_audio_assets(
        self,
        lesson_data: dict,
        output_dir: str | Path,
        include_speakers: bool = False,
        enable_subtitle: bool = False,
        public_base_url: str = "/media/audio",
    ) -> dict[str, Any]:
        lesson_metadata = lesson_data.get("lesson_metadata", {}) if isinstance(lesson_data.get("lesson_metadata"), dict) else {}
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        items = self._extract_sentence_items(lesson_data, include_speakers=include_speakers)
        rendered_items = []
        sentence_audio_files: list[Path] = []
        storage_backend = "cos" if self.cos_storage else "local"
        timeline_cursor_seconds = 0.0

        for item in items:
            line_ref = item["line_ref"]
            source_text = item["source_text"]
            role = item.get("role", "")
            voice_type = self._resolve_voice_type(role)
            print(f"  ▶️ [Tencent TTS] 正在生成 line {line_ref} | role={role or 'N/A'} | voice={voice_type}: {source_text}")
            response = self._text_to_voice(
                text=source_text,
                session_id=f"lesson-{lesson_metadata.get('lesson_id', 'unknown')}-line-{line_ref}",
                enable_subtitle=enable_subtitle,
                voice_type=voice_type,
            )

            audio_base64 = response.get("Audio", "") if isinstance(response.get("Audio"), str) else ""
            if not audio_base64:
                raise RuntimeError(f"腾讯云 TextToVoice 未返回音频数据，line_ref={line_ref}")

            audio_bytes = base64.b64decode(audio_base64)
            filename = f"lesson{lesson_metadata.get('lesson_id')}_line{line_ref}.{self.codec}"
            audio_file = output_dir / filename
            audio_file.write_bytes(audio_bytes)
            sentence_audio_files.append(audio_file)
            sentence_duration_seconds = self._probe_audio_duration_seconds(audio_file)
            start_time_seconds = round(timeline_cursor_seconds, 3)
            end_time_seconds = round(start_time_seconds + sentence_duration_seconds, 3)
            lesson_folder = output_dir.name
            audio_url = f"{public_base_url.rstrip('/')}/{lesson_folder}/{filename}"
            object_key = ""

            if self.cos_storage:
                try:
                    upload_result = self.cos_storage.upload_file(
                        local_path=audio_file,
                        object_key=f"audio/{lesson_folder}/sentences/{filename}",
                        content_type="audio/mpeg",
                    )
                    object_key = upload_result.get("object_key", "")
                    audio_url = upload_result.get("public_url", audio_url)
                except Exception as upload_error:
                    print(f"  ⚠️ [Tencent COS] line {line_ref} 上传失败，暂时保留本地 URL: {upload_error}")
                    storage_backend = "local"

            rendered_items.append({
                "line_ref": line_ref,
                "role": item.get("role", ""),
                "hanzi": item.get("hanzi", ""),
                "source_text": source_text,
                "provider": "tencent_tts",
                "mode": "sentence_audio",
                "voice_type": voice_type,
                "codec": self.codec,
                "sample_rate": self.sample_rate,
                "sentence_gap_ms": self.sentence_gap_ms,
                "duration_seconds": round(sentence_duration_seconds, 3),
                "start_time_seconds": start_time_seconds,
                "end_time_seconds": end_time_seconds,
                "status": "ready",
                "session_id": response.get("SessionId", ""),
                "request_id": response.get("RequestId", ""),
                "audio_url": audio_url,
                "object_key": object_key,
                "local_audio_file": str(audio_file),
                "subtitles": response.get("Subtitles", []) if isinstance(response.get("Subtitles"), list) else [],
            })
            timeline_cursor_seconds = end_time_seconds
            if self.sentence_gap_ms > 0 and item != items[-1]:
                timeline_cursor_seconds = round(timeline_cursor_seconds + (self.sentence_gap_ms / 1000), 3)

        full_audio_filename = f"lesson{lesson_metadata.get('lesson_id')}_full_dialogue.{self.codec}"
        full_audio_path = output_dir / full_audio_filename
        full_audio_file = self._compose_full_lesson_audio(sentence_audio_files, full_audio_path)
        full_audio_payload = {
            "status": "missing",
                "audio_url": "",
                "local_audio_file": "",
                "codec": self.codec,
                "duration_seconds": round(timeline_cursor_seconds, 3),
            }
        if full_audio_file:
            lesson_folder = output_dir.name
            full_audio_duration_seconds = self._probe_audio_duration_seconds(full_audio_file) or timeline_cursor_seconds
            full_audio_payload = {
                "status": "ready",
                "audio_url": f"{public_base_url.rstrip('/')}/{lesson_folder}/{full_audio_filename}",
                "object_key": "",
                "local_audio_file": str(full_audio_file),
                "codec": self.codec,
                "duration_seconds": round(full_audio_duration_seconds, 3),
            }
            if self.cos_storage:
                try:
                    upload_result = self.cos_storage.upload_file(
                        local_path=full_audio_file,
                        object_key=f"audio/{lesson_folder}/full/{full_audio_filename}",
                        content_type="audio/mpeg",
                    )
                    full_audio_payload["audio_url"] = upload_result.get("public_url", full_audio_payload["audio_url"])
                    full_audio_payload["object_key"] = upload_result.get("object_key", "")
                except Exception as upload_error:
                    print(f"  ⚠️ [Tencent COS] 整课音频上传失败，暂时保留本地 URL: {upload_error}")
                    storage_backend = "local"

        return {
            "lesson_audio_assets": {
                "lesson_id": lesson_metadata.get("lesson_id"),
                "course_id": lesson_metadata.get("course_id"),
                "lesson_title": lesson_metadata.get("title", ""),
                "provider": "tencent_tts",
                "mode": "sentence_audio",
                "default_voice_type": self.voice_type,
                "role_voice_map": self.role_voice_map,
                "codec": self.codec,
                "sample_rate": self.sample_rate,
                "include_speakers": include_speakers,
                "storage_backend": storage_backend,
                "sentence_gap_ms": self.sentence_gap_ms,
                "full_audio": full_audio_payload,
                "items": rendered_items,
            }
        }

    def get_task_status(self, task_id: str) -> dict[str, Any]:
        payload = {"TaskId": task_id}
        response = self._post("DescribeTtsTaskStatus", payload)
        response_data = response.get("Response", {}) if isinstance(response.get("Response"), dict) else {}
        return response_data.get("Data", {}) if isinstance(response_data.get("Data"), dict) else {}

    def wait_for_task(self, task_id: str, timeout_seconds: int = 1800) -> dict[str, Any]:
        started = time.time()
        while True:
            data = self.get_task_status(task_id)
            status = data.get("Status")
            if status == 2:
                return data
            if status == 3:
                return data
            if time.time() - started > timeout_seconds:
                raise TimeoutError(f"Tencent TTS polling timed out after {timeout_seconds} seconds.")
            print(f"    ... task {task_id} 当前状态: {data.get('StatusStr', 'unknown')}")
            time.sleep(self.poll_interval_seconds)

    def download_audio(self, result_url: str, output_path: str | Path) -> Path:
        if not result_url:
            raise ValueError("result_url 为空，无法下载音频。")
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(result_url, timeout=self.request_timeout_seconds)
        response.raise_for_status()
        output_path.write_bytes(response.content)
        return output_path
