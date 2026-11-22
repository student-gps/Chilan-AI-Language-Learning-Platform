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
  TTS_EXPLANATION_PROVIDER = openai        # openai (default) | azure | edge | ali | siliconflow
  TTS_EXPLANATION_VOICE    = nova          # openai: alloy/echo/fable/onyx/nova/shimmer
                                           # azure:  fr-FR-DeniseNeural / ja-JP-NanamiNeural / etc.
                                           # edge:   en-US-JennyNeural / fr-FR-DeniseNeural / etc.
  TTS_EXPLANATION_MODEL    = tts-1         # openai only: tts-1 | tts-1-hd
  TTS_EDGE_RATE            = +0%           # edge only

  Azure TTS (recommended for non-English with Chinese code-switching):
  TTS_AZURE_KEY            = <key>         # Azure Cognitive Services key
  TTS_AZURE_KEYS           = <key1>,<key2> # optional failover keys
  TTS_AZURE_REGION         = eastus        # Azure region
  TTS_AZURE_CONNECT_TIMEOUT_SECONDS = 30   # optional REST connection timeout
  TTS_AZURE_READ_TIMEOUT_SECONDS    = 180  # optional REST read timeout

  Per-language overrides (take precedence over the global settings above):
  TTS_EXPLANATION_PROVIDER_FR = azure      # use Azure TTS for French (SSML Chinese switching)
  TTS_EXPLANATION_VOICE_FR    = fr-FR-VivienneMultilingualNeural  # MUST be a *Multilingual* voice for <lang> switching
  TTS_EXPLANATION_PROVIDER_JA = azure
  TTS_EXPLANATION_VOICE_JA    = ja-JP-MasaruMultilingualNeural
  TTS_EXPLANATION_PROVIDER_KO = azure
  TTS_EXPLANATION_VOICE_KO    = ko-KR-HyunsuMultilingualNeural
  TTS_EXPLANATION_PROVIDER_DE = azure
  TTS_EXPLANATION_VOICE_DE    = de-DE-FlorianMultilingualNeural
  TTS_EXPLANATION_PROVIDER_ES = azure
  TTS_EXPLANATION_VOICE_ES    = es-ES-ArabellaMultilingualNeural
  # NOTE: Azure <lang xml:lang="zh-CN"> switching ONLY works with *MultilingualNeural voices.
  #       Standard voices (e.g. fr-FR-DeniseNeural) will return HTTP 400.
  # ... add more languages as needed

  LLM_OPENAI_API_KEY       = <key>
"""

import asyncio
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[4]
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

from config.env import get_env
from content_builder.core.artifacts import fingerprint, narration_fingerprint


_PINYIN_TONE_CHARS = set('āáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜĀÁǍÀĒÉĚÈĪÍǏÌŌÓǑÒŪÚǓÙǕǗǙǛ')
_TRUE_ENV_VALUES = {"1", "true", "yes", "on"}
_LANG_MARKER_RE = re.compile(r'\[(zh|ja):([^\]]+)\]')
_JAPANESE_KANA_RE = re.compile(r'([\u3040-\u30ff\u31f0-\u31ffー]+)')
_SHORT_JA_TEACHING_RE = re.compile(r'^[\u3040-\u30ff\u31f0-\u31ff]$')


def _truthy_env(name: str) -> bool:
    return str(get_env(name, default="")).strip().lower() in _TRUE_ENV_VALUES


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


def _float_env(name: str, default: float) -> float:
    try:
        value = float(str(get_env(name, default=str(default))).strip())
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _azure_tts_timeout() -> tuple[float, float]:
    connect_timeout = _float_env("TTS_AZURE_CONNECT_TIMEOUT_SECONDS", 30.0)
    read_timeout = _float_env("TTS_AZURE_READ_TIMEOUT_SECONDS", 180.0)
    return (connect_timeout, read_timeout)


def _strip_zh_markers(text: str) -> str:
    return _LANG_MARKER_RE.sub(lambda m: m.group(2).strip(), text)

def _process_zh_markers(text: str) -> str:
    """
    Convert [zh:...] / [ja:...] markers to plain text plus a comma for TTS input.
    The comma produces a natural pause after the marked word pronunciation.
    """
    return _LANG_MARKER_RE.sub(lambda m: m.group(2).strip() + ',', text)


def _strip_pinyin_parens(text: str) -> str:
    """
    Remove pinyin from TTS input to avoid garbled reading of tone-marked syllables.
    Handles:
      - （全角括号）containing pinyin → removed
      - (half-width brackets) containing pinyin → removed
      - 'single-quoted' text containing pinyin → removed (LLM sometimes writes incorrect
        forms as pinyin in quotes, e.g. "not 'wǒ guì xìng Wáng'")
    """
    def _is_pinyin(s: str) -> bool:
        return any(c in _PINYIN_TONE_CHARS for c in s)

    # Full-width brackets （…）
    text = re.sub(r'（([^）]*)）', lambda m: '' if _is_pinyin(m.group(1)) else m.group(0), text)
    # Half-width brackets (…)
    text = re.sub(r'\(([^)]*)\)', lambda m: '' if _is_pinyin(m.group(1)) else m.group(0), text)
    # Single-quoted text 'like this' that contains tone marks
    text = re.sub(r"'([^']*)'", lambda m: '' if _is_pinyin(m.group(1)) else m.group(0), text)
    # Clean up orphaned "not" / "instead of" etc. before removed pinyin, and double spaces
    text = re.sub(r',?\s*(not|instead of|rather than)\s*[,.]?\s*([,.])', r'\2', text, flags=re.IGNORECASE)
    text = re.sub(r'\s+(not|instead of|rather than)\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'  +', ' ', text).strip()
    return text


_ABBREV_RE = re.compile(
    r'\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|e\.g|i\.e|approx|dept|fig|govt|ca|cf|vol|no)\.',
    re.IGNORECASE,
)
_PLACEHOLDER = '\x00'


def _ensure_tts_terminal_punctuation(text: str) -> str:
    text = text.strip()
    if text and text[-1] not in '.!?,:;。！？，：；»”」』)]':
        return text + '.'
    return text

def _smooth_inline_quotes_for_tts(text: str) -> str:
    """
    Remove quote marks that Azure often reads as a noticeable pause.

    This is TTS-only normalization: subtitles and source JSON keep the original
    punctuation. Keep book/title brackets such as 《...》 because those convey
    visible text semantics and are less likely to appear mid-sentence.
    """
    if not text:
        return text
    text = re.sub(r'[“”„‟＂"「」『』‘’]', '', text)
    text = re.sub(r'(?<=[\u3400-\u9fff])\s*[·・]\s*(?=[\u3400-\u9fff])', '', text)
    text = re.sub(r'\s+([，。！？、；：,.!?;:])', r'\1', text)
    text = re.sub(r'([，。！？、；：,.!?;:]){2,}', lambda m: m.group(0)[0], text)
    return text.strip()

def _split_sentences(text: str) -> list[str]:
    """
    Split narration text on sentence boundaries while protecting paired
    quotation spans. This keeps quoted examples such as
    « Le temps passe vite. Nous allons bientôt être en vacances. » aligned
    with the single TTS clip/subtitle sentence that should contain them.
    """
    if not text:
        return []

    ellipsis_placeholder = '\x01'
    protected = text.strip().replace('…', ellipsis_placeholder)
    protected = re.sub(r'\.{2,}', ellipsis_placeholder, protected)
    protected = _ABBREV_RE.sub(lambda m: m.group(0)[:-1] + _PLACEHOLDER, protected)

    terminators = '.!?。！？'
    trailing_closers = '"”\')]}」』'
    sentences: list[str] = []
    start = 0
    quote_stack: list[str] = []
    quote_pairs = {
        '«': '»',
        '»': '«',
        '„': '“',
        '“': '”',
        '‘': '’',
        '「': '」',
        '『': '』',
    }
    i = 0

    def restore(value: str) -> str:
        return value.replace(_PLACEHOLDER, '.').replace(ellipsis_placeholder, '...').strip()

    def prev_non_space(index: int) -> str:
        j = index
        while j >= 0 and protected[j].isspace():
            j -= 1
        return protected[j] if j >= 0 else ''

    def is_boundary(next_index: int, terminator: str) -> bool:
        return (
            next_index == len(protected)
            or protected[next_index].isspace()
            or terminator in '。！？'
        )

    while i < len(protected):
        ch = protected[i]

        marker = _LANG_MARKER_RE.match(protected, i)
        if marker:
            i = marker.end()
            continue

        if quote_stack and ch == quote_stack[-1]:
            quote_stack.pop()
            if not quote_stack and prev_non_space(i - 1) in terminators:
                j = i + 1
                while j < len(protected) and protected[j] in trailing_closers:
                    j += 1
                if j == len(protected) or protected[j].isspace():
                    sentence = restore(protected[start:j])
                    if sentence:
                        sentences.append(sentence)
                    while j < len(protected) and protected[j].isspace():
                        j += 1
                    start = j
                    i = j
                    continue
        elif ch in quote_pairs:
            quote_stack.append(quote_pairs[ch])
        elif ch in terminators and not quote_stack:
            j = i + 1
            while j < len(protected) and protected[j] in trailing_closers:
                j += 1
            if is_boundary(j, ch):
                sentence = restore(protected[start:j])
                if sentence:
                    sentences.append(sentence)
                while j < len(protected) and protected[j].isspace():
                    j += 1
                start = j
                i = j
                continue

        i += 1

    tail = restore(protected[start:])
    if tail:
        sentences.append(tail)
    return sentences




class Task4DExplanationNarrator:
    _EDGE_DEFAULT_VOICE   = "en-US-JennyNeural"
    _OPENAI_DEFAULT_VOICE = "nova"
    _OPENAI_DEFAULT_MODEL = "tts-1"
    _ALI_DEFAULT_VOICE    = "longanyang"
    _ALI_DEFAULT_MODEL    = "cosyvoice-v3-plus"
    _ALI_ENDPOINT         = "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer"
    _AZURE_DEFAULT_VOICES = {
        "ar": "ar-SA-HamedNeural",
        "de": "de-DE-ConradNeural",
        "es": "es-ES-AlvaroNeural",
        "fr": "fr-FR-ClaudeNeural",
        "id": "id-ID-ArdiNeural",
        "it": "it-IT-DiegoNeural",
        "ja": "ja-JP-KeitaNeural",
        "ko": "ko-KR-BongJinNeural",
        "ms": "ms-MY-OsmanNeural",
        "pt": "pt-BR-AntonioNeural",
        "ru": "ru-RU-DmitryNeural",
        "th": "th-TH-NiwatNeural",
        "vi": "vi-VN-NamMinhNeural",
    }

    def __init__(self):
        self.rate = get_env("TTS_EDGE_RATE", default="+0%")
        self.duration_mode = "planned_floor"
        self.duration_buffer_seconds = 0.5
        # Set initial state using global defaults; run() calls _configure_for_lang(lang)
        self._configure_for_lang("en")

    def _configure_for_lang(self, lang: str) -> None:
        """
        Resolve provider and voice for the given language code.
        Per-language env vars (TTS_EXPLANATION_PROVIDER_FR, TTS_EXPLANATION_VOICE_FR, etc.)
        take precedence over the global TTS_EXPLANATION_PROVIDER / TTS_EXPLANATION_VOICE.
        """
        lang_up = lang.upper()
        default_azure_voice = self._AZURE_DEFAULT_VOICES.get(lang.lower())
        self.provider = (
            get_env(f"TTS_EXPLANATION_PROVIDER_{lang_up}") or
            ("azure" if default_azure_voice else None) or
            get_env("TTS_EXPLANATION_PROVIDER") or
            "openai"
        ).strip().lower()

        _provider_default_voices = {
            "edge":        self._EDGE_DEFAULT_VOICE,
            "ali":         self._ALI_DEFAULT_VOICE,
            "siliconflow": "FunAudioLLM/CosyVoice2-0.5B:bella",
        }
        self.voice = (
            get_env(f"TTS_EXPLANATION_VOICE_{lang_up}") or
            default_azure_voice or
            get_env("TTS_EXPLANATION_VOICE") or
            _provider_default_voices.get(self.provider, self._OPENAI_DEFAULT_VOICE)
        ).strip()

        if self.provider == "siliconflow":
            self.model = get_env("TTS_EXPLANATION_MODEL") or "FunAudioLLM/CosyVoice2-0.5B"
        elif self.provider == "ali":
            self.model = get_env("TTS_ALI_TTS_MODEL") or self._ALI_DEFAULT_MODEL
        else:
            self.model = get_env("TTS_EXPLANATION_MODEL") or self._OPENAI_DEFAULT_MODEL


    # ── Public entry point ────────────────────────────────────────────────────

    def run(self, render_plan: dict, output_dir: Path, lang: str = "en") -> dict:
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
        self._configure_for_lang(lang)
        self._lang = lang  # used by _synthesize_ali for language_hints and voice selection

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        segments = render_plan.get("segments", [])
        if not segments:
            return {"status": "skipped", "reason": "no segments in render plan"}

        lesson_id = render_plan.get("lesson_id", "unknown")
        lang_suffix = f"_{lang}" if lang != "en" else ""
        output_file = output_dir / f"lesson{lesson_id}_narration{lang_suffix}.mp3"
        temporary_output = output_file.with_suffix(".building.mp3")
        sentence_cache = output_dir / ".sentence_cache"
        sentence_cache.mkdir(exist_ok=True)
        tts_recipe = narration_fingerprint({"video_render_plan": {"explanation": {"segments": []}}}, lang)
        voice_recipe = {key: getattr(self, key, None) for key in ("provider", "model", "voice", "rate")}
        requested_audio = False

        tmp_dir = output_dir / "_tmp_narration"
        tmp_dir.mkdir(exist_ok=True)
        try:
            padded_files = []
            segment_timings: dict[str, list[float]] = {}
            segment_actual_durations: dict[str, float] = {}
            segment_sentences: dict[str, list[str]] = {}

            for seg in segments:
                seg_id = seg.get("segment_id") or seg.get("segment_order") or len(padded_files)
                seg_key = str(seg_id)
                narration_track = seg.get("narration_track") if isinstance(seg.get("narration_track"), dict) else {}
                text = (
                    narration_track.get(f"subtitle_{lang}")
                    or narration_track.get("script")
                    or narration_track.get("subtitle_en")
                    or narration_track.get("subtitle_zh")
                    or ""
                ).strip()
                planned_duration = max(1.0, float(seg.get("duration_seconds") or 10.0))
                padded_file = tmp_dir / f"padded_{seg_id:03d}.mp3"

                if text:
                    print(f"  🔊 [TTS] segment {seg_id}: {text[:60]}{'...' if len(text) > 60 else ''}")
                    sentences = _split_sentences(text)
                    if not sentences:
                        sentences = [text]
                    segment_sentences[seg_key] = sentences

                    # Generate TTS per sentence and record actual durations
                    timings: list[float] = []
                    sentence_files: list[Path] = []
                    cumulative = 0.0

                    for si, sentence in enumerate(sentences):
                        sent_file = tmp_dir / f"raw_{seg_id:03d}_{si:02d}.mp3"
                        # Edge / Azure: keep [zh:] / [ja:] markers intact for bilingual synthesis
                        if self.provider in ("edge", "azure"):
                            tts_text = sentence
                        else:
                            tts_text = _process_zh_markers(sentence)
                        if lang == "en":
                            tts_text = _strip_pinyin_parens(tts_text)
                        tts_text = tts_text.strip()
                        if not tts_text or not any(c.isalpha() or c.isdigit() for c in tts_text):
                            continue  # skip empty or punctuation-only fragments
                        try:
                            cache_file = sentence_cache / f"{fingerprint({'recipe': tts_recipe, 'voice': voice_recipe, 'text': tts_text})}.mp3"
                            cache_hit = cache_file.is_file() and self._get_audio_duration(cache_file) > 0
                            if cache_hit:
                                shutil.copyfile(cache_file, sent_file)
                            else:
                                if requested_audio:
                                    time.sleep(0.5 if si > 0 else 1.5)
                                requested_audio = True
                                self._synthesize(tts_text, sent_file)
                        except Exception as e:
                            preview = tts_text.replace("\n", " ")[:240]
                            raise RuntimeError(
                                f"TTS failed at segment {seg_id}, sentence {si}, "
                                f"provider={self.provider}, voice={self.voice}: {e}. "
                                f"Text preview: {preview}"
                            ) from e
                        sent_dur = self._get_audio_duration(sent_file)
                        if sent_dur <= 0:
                            raise ValueError(f"Unreadable narration at segment {seg_id}, sentence {si}")
                        if not cache_hit:
                            cache_tmp = cache_file.with_suffix(".tmp.mp3")
                            shutil.copyfile(sent_file, cache_tmp)
                            cache_tmp.replace(cache_file)
                        timings.append(round(cumulative, 3))
                        cumulative += sent_dur
                        sentence_files.append(sent_file)

                    segment_timings[seg_key] = timings

                    duration_buffer = max(0.0, float(getattr(self, "duration_buffer_seconds", 0.5) or 0.0))
                    if getattr(self, "duration_mode", "planned_floor") == "actual":
                        actual_duration = round(max(1.0, cumulative + duration_buffer), 3)
                    else:
                        # Legacy behavior: preserve planned video duration unless TTS overruns it.
                        actual_duration = round(max(planned_duration, cumulative + duration_buffer), 3)
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
                    segment_sentences[seg_key] = []

                padded_files.append(padded_file)

            self._concat_audio(padded_files, temporary_output)
            if self._get_audio_duration(temporary_output) <= 0:
                raise ValueError("Narration master is unreadable")
            temporary_output.replace(output_file)

        except Exception as e:
            return {"status": "error", "reason": str(e)}
        finally:
            temporary_output.unlink(missing_ok=True)
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
            "segment_sentences": segment_sentences,
        }

    # ── TTS ──────────────────────────────────────────────────────────────────

    def _synthesize(self, text: str, output_path: Path, max_retries: int = 5):
        """Call TTS with retry logic. Raises on final failure."""
        # connection-reset errors need longer cool-down; other errors use shorter waits
        _waits = [5, 10, 20, 40]
        last_err = None
        for attempt in range(1, max_retries + 1):
            try:
                if self.provider == "azure":
                    self._synthesize_azure(text, output_path)
                elif self.provider == "edge":
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
                    is_conn_err = "ConnectionReset" in type(e).__name__ or "10054" in str(e)
                    wait = _waits[min(attempt - 1, len(_waits) - 1)] if is_conn_err else attempt * 2
                    print(f"  ⚠️ TTS attempt {attempt} failed ({e}), retrying in {wait}s...")
                    time.sleep(wait)

        raise RuntimeError(f"TTS failed after {max_retries} attempts: {last_err}")

    def _synthesize_azure(self, text: str, output_path: Path):
        """
        Azure Cognitive Services TTS via REST API.
        If [zh:text] / [ja:text] markers are present, splits the text into chunks and synthesizes
        each with the appropriate voice (learner-language voice vs. language-specific voices),
        then concatenates. If no markers, synthesizes with the learner-language voice only.
        Set TTS_EXPLANATION_SINGLE_VOICE=1 to keep the whole clip in self.voice.
        """
        import requests as _requests

        api_keys = _azure_tts_keys()
        region  = get_env("TTS_AZURE_REGION", default="eastus")
        if not api_keys:
            raise ValueError("TTS_AZURE_KEY/TTS_AZURE_KEYS 未配置，无法使用 Azure TTS。")

        endpoint = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        request_timeout = _azure_tts_timeout()

        def _request_ssml(ssml: str) -> bytes:
            last_error: RuntimeError | None = None
            for key_index, api_key in enumerate(api_keys, start=1):
                headers = {
                    "Ocp-Apim-Subscription-Key": api_key,
                    "Content-Type": "application/ssml+xml",
                    "X-Microsoft-OutputFormat": "audio-24khz-96kbitrate-mono-mp3",
                }
                resp = _requests.post(endpoint, headers=headers, data=ssml.encode("utf-8"), timeout=request_timeout)
                if resp.ok and len(resp.content) >= 100:
                    return resp.content

                if resp.ok:
                    content_type = resp.headers.get("Content-Type", "")
                    raise RuntimeError(
                        f"Azure returned empty/corrupt audio "
                        f"(bytes={len(resp.content)}, content-type={content_type}, body={resp.text[:200]!r})"
                    )

                last_error = RuntimeError(f"Azure TTS error {resp.status_code}: {resp.text[:500]}")
                retry_with_next_key = resp.status_code in {401, 403, 429} or resp.status_code >= 500
                if retry_with_next_key and key_index < len(api_keys):
                    print(f"  ⚠️ Azure TTS key #{key_index} failed ({resp.status_code}); trying next key.")
                    continue
                raise last_error
            raise last_error or RuntimeError("Azure TTS failed: no key attempted")

        def _call(voice: str, content: str) -> bytes:
            lang_code = "-".join(voice.split("-")[:2]) if "-" in voice else "en-US"
            import xml.sax.saxutils as _sx
            content = _smooth_inline_quotes_for_tts(content)
            content = _ensure_tts_terminal_punctuation(content)
            ssml = (
                f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
                f'xml:lang="{lang_code}">'
                f'<voice name="{voice}">{_sx.escape(content)}</voice>'
                f'</speak>'
            )
            return _request_ssml(ssml)

        def _call_mixed_ssml(content: str, default_voice: str, zh_voice_name: str, ja_voice_name: str) -> bytes:
            import xml.sax.saxutils as _sx

            def _voice_lang(voice: str) -> str:
                return "-".join(voice.split("-")[:2]) if "-" in voice else "en-US"

            spans: list[tuple[str, str]] = []

            def _append(voice: str, piece: str) -> None:
                if not piece:
                    return
                if spans and spans[-1][0] == voice:
                    spans[-1] = (voice, spans[-1][1] + piece)
                else:
                    spans.append((voice, piece))

            def _append_unmarked(piece: str) -> None:
                for part in _JAPANESE_KANA_RE.split(piece):
                    if not part:
                        continue
                    if _JAPANESE_KANA_RE.fullmatch(part):
                        _append(ja_voice_name, part)
                    else:
                        _append(default_voice, part)

            pos = 0
            for marker in _LANG_MARKER_RE.finditer(content):
                _append_unmarked(content[pos:marker.start()])
                marker_lang = marker.group(1)
                marker_text = marker.group(2).strip()
                _append(ja_voice_name if marker_lang == "ja" else zh_voice_name, marker_text)
                pos = marker.end()
            _append_unmarked(content[pos:])

            spans = [(voice, text) for voice, text in spans if text and text.strip()]
            if not spans:
                raise RuntimeError("No mixed SSML spans generated")

            primary_lang = _voice_lang(default_voice)
            def _voice_span(voice: str, piece: str) -> str:
                escaped_voice = _sx.escape(voice)
                if voice == ja_voice_name and _SHORT_JA_TEACHING_RE.fullmatch(piece.strip()):
                    short_piece = piece.strip()
                    escaped_piece = _sx.escape(f"{short_piece}ー")
                    return (
                        f'<voice name="{escaped_voice}">'
                        f'<break time="110ms"/>'
                        f'<prosody rate="-34%" volume="x-loud">{escaped_piece}</prosody>'
                        f'<break time="110ms"/>'
                        f'</voice>'
                    )
                escaped_piece = _sx.escape(piece)
                return f'<voice name="{escaped_voice}">{escaped_piece}</voice>'

            body = "".join(_voice_span(voice, piece) for voice, piece in spans)
            ssml = (
                f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" '
                f'xml:lang="{primary_lang}">{body}</speak>'
            )
            return _request_ssml(ssml)

        if _truthy_env("TTS_EXPLANATION_SINGLE_VOICE"):
            output_path.write_bytes(_call(self.voice, _strip_zh_markers(text)))
            return

        text = _smooth_inline_quotes_for_tts(text)
        text = _ensure_tts_terminal_punctuation(text)
        has_lang_marker = bool(_LANG_MARKER_RE.search(text))
        has_cjk = bool(re.search(r'[\u3400-\u9fff]', text))
        has_japanese = bool(re.search(r'[\u3040-\u30ff\u31f0-\u31ff]', text))
        if not has_lang_marker and not has_cjk and not has_japanese:
            output_path.write_bytes(_call(self.voice, text))
            return

        zh_voice = (
            get_env("TTS_AZURE_ZH_VOICE")
            or get_env("TTS_EXPLANATION_VOICE_ZH")
            or get_env("TTS_CHINESE_VOICE", default="zh-CN-XiaoxiaoNeural")
        )
        ja_voice = (
            get_env("TTS_AZURE_JA_VOICE")
            or get_env("TTS_EXPLANATION_VOICE_JA")
            or get_env("TTS_JAPANESE_VOICE", default="ja-JP-KeitaNeural")
        )
        if _truthy_env("TTS_AZURE_MIXED_SINGLE_SSML") or not get_env("TTS_AZURE_MIXED_SINGLE_SSML", default="").strip():
            try:
                output_path.write_bytes(_call_mixed_ssml(text, self.voice, zh_voice, ja_voice))
                return
            except Exception as exc:
                if "429" in str(exc) or "Throttled" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                    raise
                print(f"  ⚠️ Azure mixed single-SSML failed ({exc}); falling back to chunk concat.")

        chunks = re.split(r'(\[(?:zh|ja):[^\]]+\]|[\u3400-\u9fff]+|[\u3040-\u30ff\u31f0-\u31ffー]+)', text)

        tmp_dir = output_path.parent / f"_tmp_azure_{output_path.stem}"
        tmp_dir.mkdir(exist_ok=True)
        segment_files = []
        try:
            for ci, chunk in enumerate(chunks):
                m = re.match(r'\[(zh|ja):([^\]]+)\]', chunk)
                if m:
                    content = m.group(2).strip()
                    voice = ja_voice if m.group(1) == "ja" else zh_voice
                elif re.fullmatch(r'[\u3400-\u9fff]+', chunk.strip()):
                    content, voice = chunk.strip(), zh_voice
                elif re.fullmatch(r'[\u3040-\u30ff\u31f0-\u31ffー]+', chunk.strip()):
                    content, voice = chunk.strip(), ja_voice
                else:
                    content = chunk.strip()
                    if not content or not any(c.isalpha() or '一' <= c <= '鿿' or '\u3040' <= c <= '\u30ff' for c in content):
                        continue
                    voice = self.voice
                chunk_file = tmp_dir / f"chunk_{ci:03d}.mp3"
                chunk_file.write_bytes(_call(voice, content))
                if chunk_file.stat().st_size > 100:
                    segment_files.append(chunk_file)

            if not segment_files:
                raise RuntimeError("No audio segments generated")
            if len(segment_files) == 1:
                import shutil
                shutil.copy(str(segment_files[0]), str(output_path))
            else:
                self._concat_audio(segment_files, output_path)
        finally:
            for f in tmp_dir.iterdir():
                try: f.unlink()
                except Exception: pass
            try: tmp_dir.rmdir()
            except Exception: pass

    def _synthesize_ali(self, text: str, output_path: Path):
        import requests as _requests
        api_key = get_env("LLM_ALI_API_KEY")
        if not api_key:
            raise ValueError("LLM_ALI_API_KEY 未配置，无法使用 CosyVoice TTS。")
        lang = getattr(self, "_lang", "en")
        lang_voice_key = f"TTS_EXPLANATION_VOICE_{lang.upper()}"
        voice = get_env(lang_voice_key, default=None) or self.voice
        # CosyVoice clips the last word when the sentence lacks a terminal punctuation mark.
        if text and text[-1] not in '.!?,。！？，':
            text = text + '.'
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
                    "voice": voice,
                    "format": "mp3",
                    "sample_rate": 24000,
                    "language_hints": [lang],
                },
            },
            timeout=60,
        )
        if not resp.ok:
            print(f"  ❌ CosyVoice API error {resp.status_code}: {resp.text[:500]}")
        resp.raise_for_status()
        data = resp.json()
        audio_url = (data.get("output") or {}).get("audio", {}).get("url", "")
        if not audio_url:
            raise RuntimeError(f"CosyVoice 未返回音频 URL，响应: {data}")
        audio_resp = _requests.get(audio_url, timeout=30)
        audio_resp.raise_for_status()
        output_path.write_bytes(audio_resp.content)

    def _synthesize_edge(self, text: str, output_path: Path):
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        if '[zh:' not in text:
            async def _simple():
                import edge_tts
                communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
                await asyncio.wait_for(communicate.save(str(output_path)), timeout=30)
            asyncio.run(_simple())
            return

        # Mixed content: split on [zh:...] markers, synthesize each chunk with the
        # appropriate voice (learner-language voice vs. Chinese voice), then concatenate.
        zh_voice = get_env("TTS_CHINESE_VOICE", default="zh-CN-XiaoxiaoNeural")
        zh_rate  = get_env("TTS_CHINESE_RATE",  default="-15%")
        chunks = re.split(r'(\[zh:[^\]]+\])', text)

        tmp_dir = output_path.parent / f"_tmp_edge_{output_path.stem}"
        tmp_dir.mkdir(exist_ok=True)
        segment_files = []

        async def _synthesize_chunks():
            import edge_tts
            for ci, chunk in enumerate(chunks):
                m = re.match(r'\[zh:([^\]]+)\]', chunk)
                if m:
                    content, voice, rate = m.group(1).strip(), zh_voice, zh_rate
                else:
                    content = chunk.strip()
                    if not content or not any(c.isalpha() or '一' <= c <= '鿿' for c in content):
                        continue
                    voice, rate = self.voice, self.rate
                chunk_file = tmp_dir / f"chunk_{ci:03d}.mp3"
                communicate = edge_tts.Communicate(content, voice, rate=rate)
                await asyncio.wait_for(communicate.save(str(chunk_file)), timeout=30)
                if chunk_file.exists() and chunk_file.stat().st_size > 100:
                    segment_files.append(chunk_file)

        try:
            asyncio.run(_synthesize_chunks())
            if not segment_files:
                raise RuntimeError("No audio segments generated")
            if len(segment_files) == 1:
                import shutil
                shutil.copy(str(segment_files[0]), str(output_path))
            else:
                self._concat_audio(segment_files, output_path)
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
