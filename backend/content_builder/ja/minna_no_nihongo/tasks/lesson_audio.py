from __future__ import annotations

import os
import re
import subprocess
import tempfile
import time
import xml.sax.saxutils as sx
from pathlib import Path
from typing import Any

import requests

try:
    from config.env import get_env
except ImportError:
    def get_env(key: str, default: str | None = None):
        return os.environ.get(key, default)


def _split_secret_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in re.split(r"[,;\s]+", value) if part.strip()]


def _azure_tts_keys() -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()
    for value in (
        get_env("TTS_AZURE_KEY"),
        get_env("TTS_AZURE_KEYS"),
        get_env("TTS_AZURE_KEY_1"),
        get_env("TTS_AZURE_KEY_2"),
    ):
        for key in _split_secret_list(value):
            if key not in seen:
                seen.add(key)
                keys.append(key)
    return keys


class MinnaNoNihongoLessonAudioRenderer:
    """Build sentence-level audio assets for Minna no Nihongo lessons.

    The first pass is metadata-only so Stage 1 can expose stable audio IDs and
    voice assignments before we turn on real Azure TTS rendering.
    """

    PROVIDER = "azure_tts"
    DEFAULT_NARRATION_VOICE = "ja-JP-NanamiNeural"
    DEFAULT_MALE_VOICE = "ja-JP-KeitaNeural"
    DEFAULT_FEMALE_VOICE = "ja-JP-NanamiNeural"
    DEFAULT_DIALOGUE_VOICES = ("ja-JP-KeitaNeural", "ja-JP-NanamiNeural")
    INTERMEDIATE_DIALOGUE_VOICES = (
        "ja-JP-KeitaNeural",
        "ja-JP-NanamiNeural",
        "ja-JP-DaichiNeural",
        "ja-JP-ShioriNeural",
    )
    NARRATION_SPEAKERS = {"ナレーション", "語り手", "地の文"}

    BOOK1_ROLE_VOICE_MAP = {
        # Main IMC / early lesson cast
        "マイク・ミラー": "ja-JP-KeitaNeural",
        "ミラー": "ja-JP-KeitaNeural",
        "佐藤けい子": "ja-JP-NanamiNeural",
        "佐藤": "ja-JP-NanamiNeural",
        "ジョゼ・サントス": "ja-JP-DaichiNeural",
        "サントス": "ja-JP-DaichiNeural",
        "マリア・サントス": "ja-JP-ShioriNeural",
        "マリア": "ja-JP-ShioriNeural",
        "カリナ": "ja-JP-AoiNeural",
        "ワン・シュエ": "ja-JP-NaokiNeural",
        "ワン": "ja-JP-NaokiNeural",
        "山田一郎": "ja-JP-NaokiNeural",
        "山田": "ja-JP-NaokiNeural",
        "山田友子": "ja-JP-MayuNeural",
        "友子": "ja-JP-MayuNeural",
        # Later Book 1 cast from the character pages
        "松本正": "ja-JP-DaichiNeural",
        "松本良子": "ja-JP-MayuNeural",
        "良子": "ja-JP-MayuNeural",
        "木村いずみ": "ja-JP-NanamiNeural",
        "木村": "ja-JP-NanamiNeural",
        "ジョン・ワット": "ja-JP-NaokiNeural",
        "ワット": "ja-JP-NaokiNeural",
        "カール・シュミット": "ja-JP-KeitaNeural",
        "シュミット": "ja-JP-KeitaNeural",
        "イー・ジンジュ": "ja-JP-ShioriNeural",
        "イー": "ja-JP-ShioriNeural",
        "テレーザ・サントス": "ja-JP-AoiNeural",
        "テレーザ": "ja-JP-AoiNeural",
        "山田太郎": "ja-JP-KeitaNeural",
        "太郎": "ja-JP-KeitaNeural",
        "グプタ": "ja-JP-DaichiNeural",
        "タワポン": "ja-JP-NaokiNeural",
        # Generic classroom/service roles.
        "先生": "ja-JP-NaokiNeural",
        "教師": "ja-JP-NaokiNeural",
        "医者": "ja-JP-DaichiNeural",
        "医師": "ja-JP-DaichiNeural",
        "アナウンサー": "ja-JP-NanamiNeural",
        "店員": "ja-JP-ShioriNeural",
        "学生": "ja-JP-AoiNeural",
        "主婦": "ja-JP-MayuNeural",
        "社員": "ja-JP-KeitaNeural",
        "部長": "ja-JP-DaichiNeural",
    }

    INTERMEDIATE_ROLE_VOICE_MAP = {
        # みんなの日本語 中級 登場人物.
        "マイク・ミラー": "ja-JP-KeitaNeural",
        "ミラー": "ja-JP-KeitaNeural",
        "松本正": "ja-JP-DaichiNeural",
        "松本": "ja-JP-DaichiNeural",
        "佐藤けい子": "ja-JP-NanamiNeural",
        "佐藤": "ja-JP-NanamiNeural",
        "中村秋子": "ja-JP-MayuNeural",
        "中村": "ja-JP-MayuNeural",
        "山田一郎": "ja-JP-NaokiNeural",
        "山田友子": "ja-JP-ShioriNeural",
        "友子": "ja-JP-ShioriNeural",
        "ジョン・ワット": "ja-JP-NaokiNeural",
        "ワット": "ja-JP-NaokiNeural",
        "太郎": "ja-JP-KeitaNeural",
        "タワポン": "ja-JP-NaokiNeural",
        "森": "ja-JP-DaichiNeural",
        "イー・ジンジュ": "ja-JP-AoiNeural",
        "イー": "ja-JP-AoiNeural",
        "広田": "ja-JP-KeitaNeural",
        "佐野": "ja-JP-MayuNeural",
        "野村": "ja-JP-ShioriNeural",
        "ナレーション": DEFAULT_NARRATION_VOICE,
    }

    _HONORIFIC_RE = re.compile(r"(さん|先生|せんせい|君|くん|ちゃん|様|さま)$")

    def __init__(
        self,
        default_voice: str | None = None,
        role_voice_map: dict[str, str] | None = None,
        codec: str = "mp3",
        sample_rate: int = 24000,
        sentence_gap_ms: int = 300,
        rate: str = "-10%",
        request_timeout_seconds: int = 60,
    ):
        self.default_voice = default_voice or self.DEFAULT_NARRATION_VOICE
        self.role_voice_map = dict(self.BOOK1_ROLE_VOICE_MAP)
        if role_voice_map:
            self.role_voice_map.update(role_voice_map)
        self.codec = codec
        self.sample_rate = sample_rate
        self.sentence_gap_ms = sentence_gap_ms
        self.rate = rate
        self.request_timeout_seconds = request_timeout_seconds

    def render_sentence_audio_assets(
        self,
        lesson_data: dict,
        output_dir: str | Path,
        dry_run: bool = True,
        public_base_url: str = "/media/audio",
        only_audio_ids: set[str] | list[str] | tuple[str, ...] | None = None,
        existing_assets: dict[str, Any] | None = None,
        reuse_existing: bool = True,
        force: bool = False,
    ) -> dict[str, Any]:
        lesson_metadata = (
            lesson_data.get("lesson_metadata", {})
            if isinstance(lesson_data.get("lesson_metadata"), dict)
            else {}
        )
        lesson_id = lesson_metadata.get("lesson_id")
        lesson_slug = f"lesson{int(lesson_id):03d}" if str(lesson_id).isdigit() else f"lesson{lesson_id}"
        course_id = lesson_metadata.get("course_id")
        output_dir = Path(output_dir)
        if not dry_run:
            output_dir.mkdir(parents=True, exist_ok=True)

        only_set = {str(audio_id).strip() for audio_id in (only_audio_ids or []) if str(audio_id).strip()}
        existing_by_id = {
            item.get("audio_id"): item
            for item in ((existing_assets or {}).get("items") or [])
            if isinstance(item, dict) and item.get("audio_id")
        }
        items = self.extract_sentence_items(lesson_data)
        lesson_role_voice_map = self._lesson_role_voice_map(items, lesson_id=lesson_id)
        rendered_items = []
        for item in items:
            voice = self.resolve_voice(
                item.get("speaker", ""),
                source_section=item.get("source_section", ""),
                source_ref=item.get("source_ref", 0),
                lesson_id=lesson_id,
                lesson_role_voice_map=lesson_role_voice_map,
            )
            filename = f"{lesson_slug}_{item['audio_id']}.{self.codec}"
            audio_file = output_dir / filename
            lesson_folder = output_dir.name or f"lesson{lesson_id}"
            object_key = f"ja/audio/{lesson_folder}/sentences/{filename}"
            existing_item = existing_by_id.get(item["audio_id"], {}) if reuse_existing else {}
            if existing_item.get("local_audio_file"):
                existing_audio_file = Path(existing_item["local_audio_file"])
                if existing_audio_file.exists():
                    audio_file = existing_audio_file
            duration_seconds = 0.0
            status = "metadata_only" if dry_run else "pending"
            existing_ready = (
                reuse_existing
                and existing_item
                and existing_item.get("status") == "ready"
                and audio_file.exists()
            )
            should_render = (not only_set or item["audio_id"] in only_set) and (force or not existing_ready)
            if not dry_run and should_render:
                print(
                    f"  ▶️ [Azure JA TTS] {item['audio_id']} "
                    f"| voice={voice} | {item.get('source_text', '')[:80]}"
                )
                self._synthesize_azure(
                    text=item.get("source_text") or "",
                    output_path=audio_file,
                    voice=voice,
                )
                duration_seconds = self._probe_audio_duration_seconds(audio_file)
                status = "ready"
            elif not dry_run and reuse_existing and existing_item:
                duration_seconds = float(existing_item.get("duration_seconds") or 0.0)
                status = existing_item.get("status") or ("ready" if audio_file.exists() else "missing")
            elif not dry_run:
                status = "skipped"
            rendered_items.append({
                **item,
                "provider": self.PROVIDER,
                "mode": "sentence_audio",
                "voice": voice,
                "codec": self.codec,
                "sample_rate": self.sample_rate,
                "sentence_gap_ms": self.sentence_gap_ms,
                "duration_seconds": round(duration_seconds, 3),
                "start_time_seconds": 0.0,
                "end_time_seconds": 0.0,
                "status": status,
                "audio_url": "",
                "object_key": object_key,
                "local_audio_file": str(audio_file),
            })

        full_audio_items = [item for item in rendered_items if item.get("source_section") == "dialogue"]
        self._clear_timeline(rendered_items)
        timeline_cursor_seconds = self._assign_timeline(full_audio_items)

        full_audio_filename = f"{lesson_slug}_full_dialogue.{self.codec}"
        full_audio_path = output_dir / full_audio_filename
        existing_full_audio = (existing_assets or {}).get("full_audio") if isinstance(existing_assets, dict) else {}
        if reuse_existing and isinstance(existing_full_audio, dict) and existing_full_audio.get("local_audio_file"):
            existing_full_audio_path = Path(existing_full_audio["local_audio_file"])
            if existing_full_audio_path.exists():
                full_audio_path = existing_full_audio_path
        full_audio_status = "metadata_only" if dry_run else "missing"
        full_audio_duration = round(timeline_cursor_seconds, 3)
        full_audio_files = [
            Path(item.get("local_audio_file") or "")
            for item in full_audio_items
            if item.get("local_audio_file") and Path(item.get("local_audio_file")).exists()
        ]
        if not dry_run and full_audio_files and len(full_audio_files) == len(full_audio_items):
            full_audio_file = self._compose_full_audio(full_audio_files, full_audio_path)
            if full_audio_file:
                full_audio_status = "ready"
                full_audio_duration = self._probe_audio_duration_seconds(full_audio_file) or full_audio_duration
        elif not dry_run and full_audio_files:
            full_audio_status = "partial"
        return {
            "lesson_audio_assets": {
                "lesson_id": lesson_id,
                "course_id": course_id,
                "lesson_title": lesson_metadata.get("title", ""),
                "provider": self.PROVIDER,
                "mode": "sentence_audio",
                "dry_run": dry_run,
                "only_audio_ids": sorted(only_set),
                "default_voice": self.default_voice,
                "default_male_voice": self.DEFAULT_MALE_VOICE,
                "default_female_voice": self.DEFAULT_FEMALE_VOICE,
                "role_voice_map": self.role_voice_map,
                "codec": self.codec,
                "sample_rate": self.sample_rate,
                "rate": self.rate,
                "storage_backend": "local",
                "sentence_gap_ms": self.sentence_gap_ms,
                "public_base_url": public_base_url,
                "full_audio": {
                    "status": full_audio_status,
                    "audio_url": "",
                    "object_key": f"ja/audio/{output_dir.name or f'lesson{lesson_id}'}/full/{full_audio_filename}",
                    "local_audio_file": str(full_audio_path),
                    "codec": self.codec,
                    "duration_seconds": round(full_audio_duration, 3),
                },
                "items": rendered_items,
            }
        }

    def extract_sentence_items(self, lesson_data: dict) -> list[dict[str, Any]]:
        content = lesson_data.get("course_content", {}) if isinstance(lesson_data.get("course_content"), dict) else {}
        items = []

        for index, pattern in enumerate(content.get("sentence_patterns") or [], start=1):
            if not isinstance(pattern, dict):
                continue
            item = self._sentence_item(
                audio_id=f"pattern_{index:03d}",
                source_section="sentence_patterns",
                source_ref=pattern.get("pattern_id") or index,
                payload=pattern,
            )
            if item:
                items.append(item)

        for index, example in enumerate(content.get("example_sentences") or [], start=1):
            if not isinstance(example, dict):
                continue
            item = self._sentence_item(
                audio_id=f"example_{index:03d}",
                source_section="example_sentences",
                source_ref=example.get("line_ref") or index,
                payload=example,
            )
            if item:
                items.append(item)

        dialogue = content.get("dialogue") if isinstance(content.get("dialogue"), dict) else {}
        for index, line in enumerate(dialogue.get("lines") or [], start=1):
            if not isinstance(line, dict):
                continue
            item = self._sentence_item(
                audio_id=f"dialogue_{index:03d}",
                source_section="dialogue",
                source_ref=line.get("line_ref") or index,
                payload=line,
            )
            if item:
                items.append(item)

        return items

    def resolve_voice(
        self,
        speaker: str,
        source_section: str = "",
        source_ref: int = 0,
        lesson_id: int | str | None = None,
        lesson_role_voice_map: dict[str, str] | None = None,
    ) -> str:
        if source_section != "dialogue":
            return self.default_voice

        key = self._speaker_key(speaker)
        if key in self.NARRATION_SPEAKERS:
            return self.DEFAULT_NARRATION_VOICE

        if lesson_role_voice_map and key in lesson_role_voice_map:
            return lesson_role_voice_map[key]

        if key in self.role_voice_map:
            return self.role_voice_map[key]

        if self._is_intermediate_lesson(lesson_id) and key in self.INTERMEDIATE_ROLE_VOICE_MAP:
            return self.INTERMEDIATE_ROLE_VOICE_MAP[key]

        if key in {"a", "A"}:
            return self.DEFAULT_DIALOGUE_VOICES[0]
        if key in {"b", "B"}:
            return self.DEFAULT_DIALOGUE_VOICES[1]
        if not key or key.lower() == "speaker":
            index = int(source_ref or 0)
            return self.DEFAULT_DIALOGUE_VOICES[index % len(self.DEFAULT_DIALOGUE_VOICES)]
        return self.default_voice

    def _lesson_role_voice_map(self, items: list[dict[str, Any]], lesson_id: int | str | None = None) -> dict[str, str]:
        if not self._is_intermediate_lesson(lesson_id):
            return {}

        assigned: dict[str, str] = {}
        dynamic_index = 0
        for item in items:
            if item.get("source_section") != "dialogue":
                continue
            key = self._speaker_key(item.get("speaker") or "")
            if not key or key in assigned:
                continue
            if key in self.NARRATION_SPEAKERS:
                assigned[key] = self.DEFAULT_NARRATION_VOICE
                continue
            if key in self.role_voice_map:
                assigned[key] = self.role_voice_map[key]
                continue
            if key in self.INTERMEDIATE_ROLE_VOICE_MAP:
                assigned[key] = self.INTERMEDIATE_ROLE_VOICE_MAP[key]
                continue
            assigned[key] = self.INTERMEDIATE_DIALOGUE_VOICES[
                dynamic_index % len(self.INTERMEDIATE_DIALOGUE_VOICES)
            ]
            dynamic_index += 1
        return assigned

    def _is_intermediate_lesson(self, lesson_id: int | str | None) -> bool:
        try:
            return int(lesson_id) >= 51
        except (TypeError, ValueError):
            return False

    def _speaker_key(self, speaker: str) -> str:
        key = str(speaker or "").strip()
        key = key.replace("：", "").replace(":", "").strip()
        key = re.sub(r"\s+", "", key)
        key = self._HONORIFIC_RE.sub("", key).strip()
        return key

    def _sentence_item(
        self,
        *,
        audio_id: str,
        source_section: str,
        source_ref: int,
        payload: dict,
    ) -> dict[str, Any] | None:
        source_text = (payload.get("text") or "").strip()
        if not source_text:
            return None
        return {
            "audio_id": audio_id,
            "source_section": source_section,
            "source_ref": source_ref,
            "line_ref": source_ref,
            "speaker": (payload.get("speaker") or "").strip(),
            "source_text": source_text,
            "reading": (payload.get("reading") or "").strip(),
            "romaji": (payload.get("romaji") or "").strip(),
            "translation": (payload.get("translation") or "").strip(),
            "audio_language": "ja",
        }

    def _assign_timeline(self, items: list[dict[str, Any]]) -> float:
        cursor = 0.0
        for index, item in enumerate(items):
            duration = float(item.get("duration_seconds") or 0.0)
            item["start_time_seconds"] = round(cursor, 3)
            item["end_time_seconds"] = round(cursor + duration, 3)
            cursor = item["end_time_seconds"]
            if duration > 0 and self.sentence_gap_ms > 0 and index != len(items) - 1:
                cursor = round(cursor + (self.sentence_gap_ms / 1000), 3)
        return round(cursor, 3)

    def _clear_timeline(self, items: list[dict[str, Any]]) -> None:
        for item in items:
            item["start_time_seconds"] = 0.0
            item["end_time_seconds"] = 0.0

    def _synthesize_azure(self, text: str, output_path: Path, voice: str) -> None:
        api_keys = _azure_tts_keys()
        region = get_env("TTS_AZURE_REGION", default="eastus")
        if not api_keys:
            raise ValueError("TTS_AZURE_KEY/TTS_AZURE_KEYS 未配置，无法使用 Azure TTS。")
        endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        tts_text = self._prepare_tts_text(text)
        ssml = (
            '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="ja-JP">'
            f'<voice name="{sx.escape(voice)}">'
            f'<prosody rate="{sx.escape(self.rate)}">{sx.escape(tts_text)}</prosody>'
            "</voice></speak>"
        )
        response = None
        waits = [0, 2, 4, 8]
        last_status = None
        last_text = ""
        for attempt, wait in enumerate(waits, start=1):
            if wait:
                time.sleep(wait)
            for key_index, api_key in enumerate(api_keys, start=1):
                headers = {
                    "Ocp-Apim-Subscription-Key": api_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
                    "User-Agent": "Chilan-MinnaNoNihongo-ContentBuilder",
                }
                response = requests.post(
                    endpoint,
                    headers=headers,
                    data=ssml.encode("utf-8"),
                    timeout=self.request_timeout_seconds,
                )
                last_status = response.status_code
                last_text = response.text[:500] if response is not None else ""
                if response.status_code < 400 and response.content and len(response.content) >= 512:
                    break

                retry_with_next_key = response.status_code in {401, 403, 429} or response.status_code >= 500
                if retry_with_next_key and key_index < len(api_keys):
                    print(f"  ⚠️ Azure JA TTS key #{key_index} failed ({response.status_code}); trying next key.")
                    continue
                break

            if response is not None and response.status_code < 400 and response.content and len(response.content) >= 512:
                break
            retryable = bool(last_status == 429 or (last_status is not None and last_status >= 500))
            if not retryable or attempt == len(waits):
                break
            print(
                f"  ⚠️ Azure JA TTS attempt {attempt} failed "
                f"({last_status}), retrying in {waits[attempt]}s..."
            )
        if response is None or response.status_code >= 400:
            status = last_status if last_status is not None else "unknown"
            raise RuntimeError(f"Azure TTS error {status}: {last_text}")
        if not response.content or len(response.content) < 512:
            raise RuntimeError("Azure TTS returned empty/corrupt audio.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

    def _prepare_tts_text(self, text: str) -> str:
        text = str(text or "").strip()
        text = text.replace("[", "").replace("]", "")
        text = re.sub(r"[･・]{2,}", "。", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text and text[-1] not in "。！？.!?":
            text += "。"
        return text

    def _probe_audio_duration_seconds(self, audio_file: Path) -> float:
        if not audio_file.exists():
            return 0.0
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
                capture_output=True,
                text=True,
                check=True,
            )
            return round(float(result.stdout.strip()), 3)
        except Exception:
            return 0.0

    def _compose_full_audio(self, audio_files: list[Path], output_path: Path) -> Path | None:
        audio_files = [path for path in audio_files if path.exists()]
        if not audio_files:
            return None
        output_path.parent.mkdir(parents=True, exist_ok=True)
        gap_seconds = max(0.0, self.sentence_gap_ms / 1000)
        if gap_seconds > 0 and len(audio_files) > 1:
            cmd = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
            ]
            concat_parts: list[str] = []
            input_index = 0
            for index, audio_file in enumerate(audio_files):
                cmd.extend(["-i", str(audio_file)])
                concat_parts.append(f"[{input_index}:a]")
                input_index += 1
                if index != len(audio_files) - 1:
                    cmd.extend([
                        "-f",
                        "lavfi",
                        "-t",
                        f"{gap_seconds:.3f}",
                        "-i",
                        "anullsrc=r=24000:cl=mono",
                    ])
                    concat_parts.append(f"[{input_index}:a]")
                    input_index += 1
            cmd.extend([
                "-filter_complex",
                "".join(concat_parts) + f"concat=n={len(concat_parts)}:v=0:a=1[aout]",
                "-map",
                "[aout]",
                "-ar",
                "24000",
                "-ac",
                "1",
                "-c:a",
                "libmp3lame",
                "-b:a",
                "96k",
                str(output_path),
            ])
            try:
                subprocess.run(cmd, check=True)
                return output_path if output_path.exists() else None
            except Exception:
                return None

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as tmp:
            concat_file = Path(tmp.name)
            for audio_file in audio_files:
                safe_path = str(audio_file.resolve()).replace("'", "'\\''")
                tmp.write(f"file '{safe_path}'\n")
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    str(concat_file),
                    "-c",
                    "copy",
                    str(output_path),
                ],
                check=True,
            )
            return output_path if output_path.exists() else None
        except Exception:
            return None
        finally:
            try:
                concat_file.unlink()
            except OSError:
                pass
