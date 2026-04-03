import io
import math
import os
import re
import wave
from typing import Any, Dict, Optional


class ASRService:
    NOISE_TRANSCRIPT_PATTERNS = (
        "字幕由amara.org社群提供",
        "字幕由 amara.org 社群提供",
        "subtitles by amara.org community",
        "amara.org",
    )
    NOISE_TRANSCRIPT_REGEXES = (
        r"^字幕\s*(?:by|由)\s*.+$",
        r"^字幕(?:由)?.*(?:提供|制作).*$",
        r"^subtitles?\s*by\s*.+$",
        r"^caption(?:s)?\s*by\s*.+$",
    )

    def __init__(self):
        self.provider = os.getenv("ASR_ACTIVE_PROVIDER", "openai").lower()
        self.max_audio_bytes = int(os.getenv("ASR_MAX_AUDIO_BYTES", str(10 * 1024 * 1024)))
        self.openai_model = os.getenv("ASR_OPENAI_MODEL", "whisper-1")

    @staticmethod
    def _to_optional_float(value: Any) -> Optional[float]:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clamp_01(value: float) -> float:
        return max(0.0, min(1.0, value))

    @staticmethod
    def _read_attr(obj: Any, key: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    @staticmethod
    def _normalize_transcript_text(text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip()).strip()

    def _sanitize_transcript(self, text: str) -> str:
        transcript = self._normalize_transcript_text(text)
        if not transcript:
            return ""

        lowered = transcript.lower()
        compact = re.sub(r"[\s.]+", "", lowered)
        for pattern in self.NOISE_TRANSCRIPT_PATTERNS:
            normalized_pattern = pattern.lower()
            compact_pattern = re.sub(r"[\s.]+", "", normalized_pattern)
            if lowered == normalized_pattern or compact == compact_pattern or normalized_pattern in lowered:
                return ""

        for regex in self.NOISE_TRANSCRIPT_REGEXES:
            if re.match(regex, transcript, flags=re.IGNORECASE):
                return ""
        return transcript

    def _extract_confidence(self, response: Any) -> Optional[float]:
        direct = self._to_optional_float(self._read_attr(response, "confidence"))
        if direct is not None:
            return self._clamp_01(direct)

        segments = self._read_attr(response, "segments") or []
        if not isinstance(segments, list):
            return None

        segment_conf = []
        segment_avg_logprob = []
        for seg in segments:
            conf = self._to_optional_float(self._read_attr(seg, "confidence"))
            if conf is not None:
                segment_conf.append(self._clamp_01(conf))
                continue

            avg_logprob = self._to_optional_float(self._read_attr(seg, "avg_logprob"))
            if avg_logprob is not None:
                segment_avg_logprob.append(self._clamp_01(math.exp(max(-8.0, min(0.0, avg_logprob)))))

        if segment_conf:
            return self._clamp_01(sum(segment_conf) / len(segment_conf))
        if segment_avg_logprob:
            return self._clamp_01(sum(segment_avg_logprob) / len(segment_avg_logprob))
        return None

    def _estimate_duration_ms(
        self,
        audio_bytes: bytes,
        filename: str = "",
        content_type: str = "",
    ) -> Optional[int]:
        lower_name = (filename or "").lower()
        lower_type = (content_type or "").lower()
        is_wav = lower_name.endswith(".wav") or "wav" in lower_type or "wave" in lower_type
        if not is_wav:
            return None

        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
                frame_rate = wav_file.getframerate()
                frame_count = wav_file.getnframes()
                if frame_rate <= 0:
                    return None
                return int(frame_count / frame_rate * 1000)
        except Exception:
            return None

    def _transcribe_with_openai(
        self,
        audio_bytes: bytes,
        filename: str,
        language: Optional[str],
        prompt: Optional[str],
    ) -> Dict[str, Any]:
        api_key = os.getenv("ASR_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OpenAI ASR key is missing. Set ASR_OPENAI_API_KEY or OPENAI_API_KEY.")

        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        file_obj = io.BytesIO(audio_bytes)
        file_obj.name = filename or "speech.webm"

        kwargs = {
            "model": self.openai_model,
            "file": file_obj,
            "response_format": "verbose_json",
        }
        if language:
            kwargs["language"] = language
        if prompt:
            kwargs["prompt"] = prompt

        response = client.audio.transcriptions.create(**kwargs)
        transcript = self._sanitize_transcript(getattr(response, "text", None) or "")
        if not transcript:
            raise ValueError("ASR transcript is empty. Please retry recording.")

        return {
            "transcript": transcript,
            "confidence": self._extract_confidence(response),
            "provider": "openai",
            "model": self.openai_model,
        }

    def transcribe(
        self,
        audio_bytes: bytes,
        filename: str = "",
        content_type: str = "",
        language: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not audio_bytes:
            raise ValueError("Audio payload is empty.")
        if len(audio_bytes) > self.max_audio_bytes:
            raise ValueError(f"Audio file is too large (>{self.max_audio_bytes} bytes).")
        if self.provider != "openai":
            raise RuntimeError(f"Unsupported ASR provider: {self.provider}")

        result = self._transcribe_with_openai(
            audio_bytes=audio_bytes,
            filename=filename,
            language=language,
            prompt=prompt,
        )
        result["duration_ms"] = self._estimate_duration_ms(audio_bytes, filename, content_type)
        return result
