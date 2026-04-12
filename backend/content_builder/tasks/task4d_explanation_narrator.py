"""
Task 4D — Explanation Narration Audio Generator

For each segment in the explanation render plan:
  1. Split narration text into sentences
  2. Generate TTS per sentence, record actual audio duration
  3. Pad the concatenated clip to match segment.duration_seconds
  4. Concatenate all padded clips into one narration track

Output:
  lesson{id}_narration.mp3          (full narration, same length as silent video)
  segment_timings: {seg_id: [t0, t1, t2, ...]}  (sentence start times in seconds)

.env switches:
  TTS_EXPLANATION_PROVIDER = openai        # openai (default) | edge
  TTS_EXPLANATION_VOICE    = nova          # openai: alloy/echo/fable/onyx/nova/shimmer
                                           # edge:   en-US-JennyNeural / etc.
  TTS_EXPLANATION_MODEL    = tts-1         # openai only: tts-1 | tts-1-hd
  TTS_EDGE_RATE            = +0%           # edge only
  LLM_OPENAI_API_KEY       = <key>
"""

import asyncio
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from config.env import get_env


_PINYIN_TONE_CHARS = set('āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛ')

def _process_zh_markers(text: str) -> str:
    """
    Convert [zh:hǎo] markers to 'hǎo,' for TTS input.
    The comma produces a natural pause after the Chinese word pronunciation.
    """
    return re.sub(r'\[zh:([^\]]+)\]', lambda m: m.group(1).strip() + ',', text)


def _strip_pinyin_parens(text: str) -> str:
    """
    Remove parenthetical pinyin from TTS input to avoid double-reading.
    Strips both （全角）and (half-width) brackets whose content contains
    pinyin tone marks, e.g. '你好 (Nǐ hǎo)' → '你好'.
    """
    def _is_pinyin(s: str) -> bool:
        return any(c in _PINYIN_TONE_CHARS for c in s)

    # Full-width brackets （…）
    text = re.sub(r'（([^）]*)）', lambda m: '' if _is_pinyin(m.group(1)) else m.group(0), text)
    # Half-width brackets (…)
    text = re.sub(r'\(([^)]*)\)', lambda m: '' if _is_pinyin(m.group(1)) else m.group(0), text)
    # Clean up any double spaces left behind
    text = re.sub(r'  +', ' ', text).strip()
    return text


_ABBREV_RE = re.compile(
    r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|e\.g|i\.e|approx|dept|fig|govt|ca|cf|vol|no)\.',
    re.IGNORECASE,
)
_PLACEHOLDER = '\x00'

def _split_sentences(text: str) -> list[str]:
    """
    Split narration text into sentences on .!?。！？ boundaries,
    while preserving common abbreviations like Mr. Dr. etc. from being split.
    """
    if not text:
        return []
    # Step 1: protect abbreviation periods with a placeholder
    protected = _ABBREV_RE.sub(lambda m: m.group(0)[:-1] + _PLACEHOLDER, text.strip())
    # Step 2: split on sentence-ending punctuation
    parts = re.split(r'(?<=[.!?。！？]["\'])\s+|(?<=[.!?。！？])\s+', protected)
    # Step 3: restore placeholders
    return [p.replace(_PLACEHOLDER, '.').strip() for p in parts if p.strip()]


class Task4DExplanationNarrator:
    _EDGE_DEFAULT_VOICE   = "en-US-JennyNeural"
    _OPENAI_DEFAULT_VOICE = "nova"
    _OPENAI_DEFAULT_MODEL = "tts-1"
    _ALI_DEFAULT_VOICE    = "longanyang"
    _ALI_DEFAULT_MODEL    = "cosyvoice-v3-plus"
    _ALI_ENDPOINT         = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"

    def __init__(self):
        self.provider = get_env("TTS_EXPLANATION_PROVIDER", default="openai").strip().lower()
        if self.provider == "edge":
            self.voice = get_env("TTS_EXPLANATION_VOICE", default=self._EDGE_DEFAULT_VOICE)
            self.rate  = get_env("TTS_EDGE_RATE", default="+0%")
        elif self.provider == "siliconflow":
            self.voice = get_env("TTS_EXPLANATION_VOICE", default="FunAudioLLM/CosyVoice2-0.5B:bella")
            self.model = get_env("TTS_EXPLANATION_MODEL", default="FunAudioLLM/CosyVoice2-0.5B")
        elif self.provider == "ali":
            self.voice = get_env("TTS_EXPLANATION_VOICE", default=self._ALI_DEFAULT_VOICE)
            self.model = get_env("TTS_ALI_TTS_MODEL", default=self._ALI_DEFAULT_MODEL)
        else:
            self.provider = "openai"
            self.voice = get_env("TTS_EXPLANATION_VOICE", default=self._OPENAI_DEFAULT_VOICE)
            self.model = get_env("TTS_EXPLANATION_MODEL", default=self._OPENAI_DEFAULT_MODEL)


    # ── Public entry point ────────────────────────────────────────────────────

    def run(self, render_plan: dict, output_dir: Path) -> dict:
        """
        Generate a single narration audio file from the explanation render plan.

        Returns:
            {
                "status": "ok" | "skipped" | "error",
                "audio_file": "<absolute path>",
                "segment_count": int,
                "segment_timings": {"1": [0.0, 2.3, 5.1], "2": [0.0, 3.4], ...},
                "reason": "..."   # only when status != "ok"
            }
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        segments = render_plan.get("segments", [])
        if not segments:
            return {"status": "skipped", "reason": "no segments in render plan"}

        lesson_id = render_plan.get("lesson_id", "unknown")
        output_file = output_dir / f"lesson{lesson_id}_narration.mp3"

        tmp_dir = output_dir / "_tmp_narration"
        tmp_dir.mkdir(exist_ok=True)
        try:
            padded_files = []
            segment_timings: dict[str, list[float]] = {}
            segment_actual_durations: dict[str, float] = {}

            for seg in segments:
                seg_id = seg.get("segment_id") or seg.get("segment_order") or len(padded_files)
                seg_key = str(seg_id)
                text = (seg.get("narration_track") or {}).get("subtitle_en", "").strip()
                planned_duration = max(1.0, float(seg.get("duration_seconds") or 10.0))
                padded_file = tmp_dir / f"padded_{seg_id:03d}.mp3"

                if text:
                    print(f"  🔊 [TTS] segment {seg_id}: {text[:60]}{'...' if len(text) > 60 else ''}")
                    sentences = _split_sentences(text)
                    if not sentences:
                        sentences = [text]

                    # Generate TTS per sentence and record actual durations
                    timings: list[float] = []
                    sentence_files: list[Path] = []
                    cumulative = 0.0

                    for si, sentence in enumerate(sentences):
                        if si > 0:
                            time.sleep(0.5)  # brief pause between calls to avoid rate limiting
                        sent_file = tmp_dir / f"raw_{seg_id:03d}_{si:02d}.mp3"
                        tts_text = _strip_pinyin_parens(_process_zh_markers(sentence)).strip()
                        if not tts_text:
                            continue  # skip sentences that become empty after processing
                        self._synthesize(tts_text, sent_file)
                        sent_dur = self._get_audio_duration(sent_file)
                        if sent_dur <= 0:
                            continue  # skip corrupt/empty audio files
                        timings.append(round(cumulative, 3))
                        cumulative += sent_dur
                        sentence_files.append(sent_file)

                    segment_timings[seg_key] = timings

                    # Use actual TTS duration + small buffer if it exceeds the plan
                    actual_duration = round(max(planned_duration, cumulative + 0.5), 3)
                    segment_actual_durations[seg_key] = actual_duration

                    # Merge all sentence clips into one raw clip for this segment
                    if len(sentence_files) == 1:
                        raw_file = sentence_files[0]
                    else:
                        raw_file = tmp_dir / f"raw_{seg_id:03d}.mp3"
                        self._concat_audio(sentence_files, raw_file)

                    # Pad to actual duration (never trim)
                    self._pad_to_duration(raw_file, padded_file, actual_duration)
                else:
                    self._generate_silence(padded_file, planned_duration)
                    segment_timings[seg_key] = []
                    segment_actual_durations[seg_key] = planned_duration

                padded_files.append(padded_file)

            self._concat_audio(padded_files, output_file)

        except Exception as e:
            return {"status": "error", "reason": str(e)}
        finally:
            for f in tmp_dir.iterdir():
                try:
                    f.unlink()
                except Exception:
                    pass
            try:
                tmp_dir.rmdir()
            except Exception:
                pass

        return {
            "status": "ok",
            "audio_file": str(output_file),
            "segment_count": len(padded_files),
            "segment_timings": segment_timings,
            "segment_actual_durations": segment_actual_durations,
        }

    # ── TTS ──────────────────────────────────────────────────────────────────

    def _synthesize(self, text: str, output_path: Path, max_retries: int = 3):
        """Call TTS with retry logic. Raises on final failure."""
        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                if self.provider == "edge":
                    self._synthesize_edge(text, output_path)
                elif self.provider == "siliconflow":
                    self._synthesize_siliconflow(text, output_path)
                elif self.provider == "ali":
                    self._synthesize_ali(text, output_path)
                else:
                    self._synthesize_openai(text, output_path)

                # Validate output — must be a non-trivial audio file
                if not output_path.exists() or output_path.stat().st_size < 100:
                    raise RuntimeError(f"TTS returned empty/corrupt file (attempt {attempt})")
                return  # success

            except Exception as e:
                last_err = e
                if attempt < max_retries:
                    wait = attempt * 2  # 2s, 4s
                    print(f"  ⚠️ TTS attempt {attempt} failed ({e}), retrying in {wait}s...")
                    time.sleep(wait)

        raise RuntimeError(f"TTS failed after {max_retries} attempts: {last_err}")

    def _synthesize_ali(self, text: str, output_path: Path):
        import requests as _requests
        api_key = get_env("LLM_ALI_API_KEY")
        if not api_key:
            raise ValueError("LLM_ALI_API_KEY 未配置，无法使用 CosyVoice TTS。")
        resp = _requests.post(
            self._ALI_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": {
                    "text": text,
                    "voice": self.voice,
                    "format": "mp3",
                    "sample_rate": 24000,
                    "language_hints": ["en"],
                },
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        audio_url = (data.get("output") or {}).get("audio", {}).get("url", "")
        if not audio_url:
            raise RuntimeError(f"CosyVoice 未返回音频 URL，响应: {data}")
        audio_resp = _requests.get(audio_url, timeout=30)
        audio_resp.raise_for_status()
        output_path.write_bytes(audio_resp.content)

    def _synthesize_edge(self, text: str, output_path: Path):
        async def _coro():
            import edge_tts
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
            await asyncio.wait_for(communicate.save(str(output_path)), timeout=30)

        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(_coro())

    def _synthesize_siliconflow(self, text: str, output_path: Path):
        from openai import OpenAI
        api_key = get_env("LLM_SILICONFLOW_API_KEY")
        if not api_key:
            raise ValueError("LLM_SILICONFLOW_API_KEY 未配置，无法使用硅基流动 TTS。")
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1",
        )
        response = client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3",
        )
        output_path.write_bytes(response.content)

    def _synthesize_openai(self, text: str, output_path: Path):
        from openai import OpenAI
        api_key = get_env("LLM_OPENAI_API_KEY") or get_env("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("LLM_OPENAI_API_KEY 未配置，无法使用 OpenAI TTS。")
        client = OpenAI(api_key=api_key, timeout=60.0)
        response = client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            response_format="mp3",
        )
        output_path.write_bytes(response.content)

    # ── ffmpeg / ffprobe helpers ──────────────────────────────────────────────

    def _get_audio_duration(self, audio_file: Path) -> float:
        """Return the duration of an audio file in seconds using ffprobe.
        Returns 0.0 if the file is missing, empty, or unreadable."""
        try:
            if not audio_file.exists() or audio_file.stat().st_size < 100:
                return 0.0
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(audio_file),
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError, OSError):
            return 0.0

    def _pad_to_duration(self, input_file: Path, output_file: Path, duration: float):
        """Extend with silence to reach target duration; trim if TTS ran longer."""
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(input_file),
                "-af", f"apad=pad_dur={duration}",
                "-t", str(duration),
                "-ar", "44100", "-ac", "2",
                str(output_file),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _generate_silence(self, output_file: Path, duration: float):
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                "-q:a", "9", "-acodec", "libmp3lame",
                str(output_file),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _concat_audio(self, audio_files: list, output_file: Path):
        concat_list = output_file.with_suffix(".concat.txt")
        try:
            with open(concat_list, "w", encoding="utf-8") as f:
                for af in audio_files:
                    f.write(f"file '{str(af).replace(chr(92), '/')}'\n")
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", str(concat_list),
                    "-c:a", "libmp3lame", "-q:a", "4",
                    str(output_file),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        finally:
            try:
                concat_list.unlink()
            except Exception:
                pass
