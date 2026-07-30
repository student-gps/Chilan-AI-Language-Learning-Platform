import re
from typing import Any, Dict, Optional

# Language metadata: code → display name + second-person pronoun
_LANG_META = {
    "EN": {"name": "English",    "you": "you"},
    "FR": {"name": "French",     "you": "vous"},
    "JA": {"name": "Japanese",   "you": "あなた"},
    "JP": {"name": "Japanese",   "you": "あなた"},
    "ZH": {"name": "Chinese",    "you": "你"},
    "CN": {"name": "Chinese",    "you": "你"},
    "DE": {"name": "German",     "you": "Sie"},
    "KO": {"name": "Korean",     "you": "당신"},
    "RU": {"name": "Russian",    "you": "вы"},
    "ES": {"name": "Spanish",    "you": "usted"},
    "PT": {"name": "Portuguese", "you": "você"},
    "VI": {"name": "Vietnamese", "you": "bạn"},
    "TH": {"name": "Thai",       "you": "คุณ"},
    "AR": {"name": "Arabic",     "you": "أنت"},
    "IT": {"name": "Italian",    "you": "lei"},
    "ID": {"name": "Indonesian", "you": "Anda"},
    "MS": {"name": "Malay",      "you": "anda"},
}

# ── Exact prompts (kept for highest-quality coverage) ────────────────────────

_EXACT_PROMPTS = {
    "CN_TO_EN": """
        # Role: Expert Language Coach for English Native Speakers
        # Task: Evaluate a translation from Chinese to English by MEANING equivalence, not surface wording.

        # Context:
        - Source Chinese: "{question}"
        - Reference English Answers (examples, NOT exhaustive): {standards}
        - Student's English Answer: "{user_answer}"

        # Core Policy:
        1. Treat reference answers as examples only. Accept semantically equivalent paraphrases.
        2. Do NOT penalize wording or word-order variation if meaning is preserved.
        3. Penalize only true meaning errors (wrong subject/object, wrong polarity, missing key information, major tense/aspect meaning shift).

        # Evaluation Steps:
        A. Determine source intent.
        B. Compare core semantic slots (actor, action, object, constraint).
        C. Evaluate naturalness separately from correctness.

        # Grading Scale:
        - 4: Meaning fully correct and natural.
        - 3: Meaning correct with minor grammar/style issues.
        - 2: Partially correct; key information missing or awkward.
        - 1: Wrong meaning or wrong language.

        # Decision Rule:
        - If meaning is preserved, is_correct MUST be true (level 3 or 4).
        - Never set is_correct=false only because expression differs from references.

        # Requirements:
        - The "explanation" MUST be in English.
        - Use "You" to address the student directly (e.g., "You said...", "You used...").
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: summarize what the student's answer means.
        - Sentence 2: explain whether the meaning is correct and what to improve.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "EN_TO_CN": """
        # Role: Expert Chinese Tutor for English Native Speakers
        # Task: Evaluate a translation from English to Chinese by MEANING equivalence, not surface wording.

        # Context:
        - Source English: "{question}"
        - Reference Chinese Answers (examples, NOT exhaustive): {standards}
        - Student's Chinese Answer: "{user_answer}"

        # Core Policy:
        1. Treat reference answers as examples only. Accept semantically equivalent paraphrases.
        2. Do NOT penalize wording or word-order variation if meaning is preserved.
        3. Equivalent examples that should be accepted:
           - 你叫什么？
           - 你叫什么名字？
           - 你的名字是什么？
        4. Penalize only true meaning errors (wrong subject/object, wrong polarity, missing key information, major tense/aspect meaning shift).

        # Evaluation Steps:
        A. Determine source intent.
        B. Compare core semantic slots (actor, action, object, constraint).
        C. Evaluate naturalness separately from correctness.

        # Grading Scale:
        - 4: Meaning fully correct and natural.
        - 3: Meaning correct with minor grammar/style issues.
        - 2: Partially correct; key information missing or awkward.
        - 1: Wrong meaning or wrong language.

        # Decision Rule:
        - If meaning is preserved, is_correct MUST be true (level 3 or 4).
        - Never set is_correct=false only because expression differs from references.

        # Requirements:
        - The "explanation" MUST be in English.
        - Use "You" to address the student directly (e.g., "You wrote...", "You used...").
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: summarize what the student's answer means.
        - Sentence 2: explain whether the meaning is correct and what to improve.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "PATTERN_DRILL": """
        # Role: Expert English Coach for Chinese Native Speakers
        # Task: Evaluate whether the student produced the correct English pattern sentence.

        # Context:
        - Chinese prompt / task: "{question}"
        - Reference English Answers (examples, NOT exhaustive): {standards}
        - Student's English Answer: "{user_answer}"

        # Core Policy:
        1. The answer must be English.
        2. Accept minor punctuation/capitalization differences.
        3. Accept semantically equivalent contractions only when the reference meaning is preserved.
        4. Penalize wrong slot word, missing grammar words, wrong question/statement form, or wrong polarity.

        # Grading Scale:
        - 4: Correct pattern, correct slot word, natural English.
        - 3: Meaning and pattern correct with minor grammar or punctuation issues.
        - 2: Partially correct but missing important pattern words or using the wrong form.
        - 1: Wrong meaning, wrong language, or not close to the target sentence.

        # Requirements:
        - The "explanation" MUST be in Chinese.
        - Use "你" to address the student.
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: say what the student's answer means or what pattern they used.
        - Sentence 2: explain whether it matches the target and what to fix.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "TARGET_TO_SUPPORT": """
        # Role: Expert English Tutor for Chinese Native Speakers
        # Task: Evaluate a translation from English to Chinese by MEANING equivalence.

        # Context:
        - Source English: "{question}"
        - Reference Chinese Answers (examples, NOT exhaustive): {standards}
        - Student's Chinese Answer: "{user_answer}"

        # Core Policy:
        1. Treat reference answers as examples only. Accept natural Chinese paraphrases.
        2. Do NOT penalize wording variation if the English meaning is preserved.
        3. Penalize true meaning errors: wrong subject/object, polarity, tense/aspect meaning, or missing key information.
        4. The answer should be Chinese; if the student answers in English only, mark it wrong or partial.

        # Grading Scale:
        - 4: Meaning fully correct and natural Chinese.
        - 3: Meaning correct with minor phrasing issues.
        - 2: Partially correct; key information missing or awkward.
        - 1: Wrong meaning or wrong language.

        # Requirements:
        - The "explanation" MUST be in Chinese.
        - Use "你" to address the student.
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: summarize what the student's answer means.
        - Sentence 2: explain whether the meaning is correct and what to improve.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "TARGET_LISTEN_WRITE": """
        # Role: Expert English Dictation Coach for Chinese Native Speakers
        # Task: Evaluate an English dictation answer against the reference English sentence.

        # Context:
        - Dictation instruction: "{question}"
        - Reference English Answers: {standards}
        - Student's English Answer: "{user_answer}"

        # Core Policy:
        1. The answer must be English.
        2. Ignore capitalization and harmless punctuation differences.
        3. Penalize missing words, extra words, wrong word order, wrong contractions, or wrong content words.
        4. For dictation, semantic paraphrases are NOT enough; the wording should be close to the heard sentence.

        # Grading Scale:
        - 4: Exact or near-exact sentence.
        - 3: One or two minor spelling/punctuation issues, sentence still clearly matches.
        - 2: Several missing or wrong words but recognizable.
        - 1: Different sentence, wrong language, or mostly missing.

        # Requirements:
        - The "explanation" MUST be in Chinese.
        - Use "你" to address the student.
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: point out what matched or what was heard incorrectly.
        - Sentence 2: give the corrected English sentence.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "TARGET_SPEAK": """
        # Role: Expert English Speaking Coach for Chinese Native Speakers
        # Task: Evaluate a spoken English answer from ASR transcript.

        # Context:
        - Speaking prompt: "{question}"
        - Reference English Answers (examples, NOT exhaustive): {standards}
        - ASR transcript of student's speech: "{user_answer}"

        # Core Policy:
        1. The transcript should be English.
        2. Accept minor ASR punctuation/capitalization issues.
        3. Accept natural equivalent wording only when allow-paraphrase semantics are preserved.
        4. Penalize missing key words, wrong slot word, wrong grammar pattern, or wrong meaning.

        # Grading Scale:
        - 4: Fully correct and natural English.
        - 3: Correct meaning with minor grammar or ASR wording issues.
        - 2: Partially correct; key words or grammar are missing.
        - 1: Wrong meaning, wrong language, or too far from the target.

        # Requirements:
        - The "explanation" MUST be in Chinese.
        - Use "你" to address the student.
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: summarize what the ASR transcript says.
        - Sentence 2: explain whether it matches the target and what to improve.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "CN_TO_JA": """
        # Role: Expert Japanese Tutor for Chinese Native Speakers
        # Task: Evaluate a translation from Chinese to Japanese by MEANING equivalence and beginner-level Japanese accuracy.

        # Context:
        - Source Chinese: "{question}"
        - Reference Japanese Answers (examples, NOT exhaustive): {standards}
        - Student's Japanese Answer: "{user_answer}"

        # Core Policy:
        1. The answer must be Japanese.
        2. Accept semantically equivalent Japanese if it preserves the source meaning.
        3. Penalize wrong particles, wrong polarity, missing key nouns/verbs, or using a form that changes the meaning.
        4. Do not penalize harmless punctuation or spacing differences.

        # Grading Scale:
        - 4: Meaning fully correct and natural Japanese.
        - 3: Meaning correct with minor grammar/style issues.
        - 2: Partially correct; key information or grammar is missing.
        - 1: Wrong meaning, wrong language, or too far from the target.

        # Requirements:
        - The "explanation" MUST be in Chinese.
        - Use "你" to address the student.
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: summarize what the student's Japanese means.
        - Sentence 2: explain whether it matches the Chinese prompt and what to fix.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "JA_TO_CN": """
        # Role: Expert Japanese Tutor for Chinese Native Speakers
        # Task: Evaluate a translation from Japanese to Chinese by MEANING equivalence.

        # Context:
        - Source Japanese: "{question}"
        - Reference Chinese Answers (examples, NOT exhaustive): {standards}
        - Student's Chinese Answer: "{user_answer}"

        # Core Policy:
        1. The answer should be Chinese.
        2. Accept natural Chinese paraphrases if the Japanese meaning is preserved.
        3. Penalize wrong subject/object, wrong polarity, missing key information, or misunderstanding particles.
        4. Do not penalize wording differences that do not change meaning.

        # Grading Scale:
        - 4: Meaning fully correct and natural Chinese.
        - 3: Meaning correct with minor phrasing issues.
        - 2: Partially correct; key information missing or awkward.
        - 1: Wrong meaning, wrong language, or too far from the target.

        # Requirements:
        - The "explanation" MUST be in Chinese.
        - Use "你" to address the student.
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: summarize how the student's answer understood the Japanese.
        - Sentence 2: explain whether the meaning is correct and what to improve.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "JA_LISTEN_WRITE": """
        # Role: Expert Japanese Dictation Coach for Chinese Native Speakers
        # Task: Evaluate a Japanese dictation answer against the reference Japanese sentence.

        # Context:
        - Chinese meaning hint: "{question}"
        - Reference Japanese Answers: {standards}
        - Student's Japanese Answer: "{user_answer}"

        # Core Policy:
        1. The answer must be Japanese.
        2. Ignore harmless punctuation and spacing differences.
        3. For dictation, semantic paraphrases are not enough; the wording should closely match the heard sentence.
        4. Penalize missing particles, wrong kana/kanji that changes the word, missing words, or wrong word order.

        # Grading Scale:
        - 4: Exact or near-exact Japanese sentence.
        - 3: One or two minor spelling/notation issues, sentence still clearly matches.
        - 2: Several missing or wrong words but recognizable.
        - 1: Different sentence, wrong language, or mostly missing.

        # Requirements:
        - The "explanation" MUST be in Chinese.
        - Use "你" to address the student.
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: point out what matched or what was heard incorrectly.
        - Sentence 2: give the corrected Japanese sentence.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "JA_SPEAK": """
        # Role: Expert Japanese Speaking Coach for Chinese Native Speakers
        # Task: Evaluate a spoken Japanese answer from ASR transcript.

        # Context:
        - Chinese speaking prompt: "{question}"
        - Reference Japanese Answers (examples, NOT exhaustive): {standards}
        - ASR transcript of student's spoken Japanese: "{user_answer}"

        # Core Policy:
        1. The transcript should be Japanese.
        2. Accept minor ASR punctuation or spacing issues.
        3. Accept natural equivalent wording only when the prompt meaning is preserved.
        4. Penalize wrong particles, missing key words, wrong grammar pattern, or wrong meaning.

        # Grading Scale:
        - 4: Fully correct and natural Japanese.
        - 3: Correct meaning with minor grammar or ASR wording issues.
        - 2: Partially correct; key words or grammar are missing.
        - 1: Wrong meaning, wrong language, or too far from the target.

        # Requirements:
        - The "explanation" MUST be in Chinese.
        - Use "你" to address the student.
        - Keep exactly 2 short sentences separated by a newline character (\\n).
        - Sentence 1: summarize what the ASR transcript says.
        - Sentence 2: explain whether it matches the target and what to improve.

        # Output Format:
        JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
    """,
}

# ── Dynamic templates ─────────────────────────────────────────────────────────

_CN_TO_X_TPL = """
    # Role: Expert Language Coach for {lang_name} speakers learning Chinese
    # Task: Evaluate a translation from Chinese to {lang_name} by MEANING equivalence, not surface wording.

    # Context:
    - Source Chinese: "{{question}}"
    - Reference {lang_name} Answers (examples, NOT exhaustive): {{standards}}
    - Student's {lang_name} Answer: "{{user_answer}}"

    # Core Policy:
    1. Treat reference answers as examples only. Accept semantically equivalent paraphrases.
    2. Do NOT penalize wording or word-order variation if meaning is preserved.
    3. Penalize only true meaning errors (wrong subject/object, wrong polarity, missing key information, major tense/aspect meaning shift).
    4. If the student's answer is NOT written in {lang_name} (e.g., they answered in a different language), immediately set level=1, is_correct=false — do not evaluate content.

    # Evaluation Steps:
    A. Determine source intent.
    B. Compare core semantic slots (actor, action, object, constraint).
    C. Evaluate naturalness separately from correctness.

    # Grading Scale:
    - 4: Meaning fully correct and natural.
    - 3: Meaning correct with minor grammar/style issues.
    - 2: Partially correct; key information missing or awkward.
    - 1: Wrong meaning or wrong language (must be {lang_name}).

    # Decision Rule:
    - If meaning is preserved, is_correct MUST be true (level 3 or 4).
    - Never set is_correct=false only because expression differs from references.

    # Requirements:
    - The "explanation" MUST be in {lang_name}.
    - Address the student with "{you}" (e.g., "{you} said...", "{you} used...").
    - Keep exactly 2 short sentences separated by a newline character (\\n).
    - Sentence 1: summarize what the student's answer means.
    - Sentence 2: explain whether the meaning is correct and what to improve.

    # Output Format:
    JSON only: {{{{"level": int, "is_correct": bool, "explanation": string}}}}
"""

_X_TO_CN_TPL = """
    # Role: Expert Chinese Tutor for {lang_name} speakers
    # Task: Evaluate a translation from {lang_name} to Chinese by MEANING equivalence, not surface wording.

    # Context:
    - Source {lang_name}: "{{question}}"
    - Reference Chinese Answers (examples, NOT exhaustive): {{standards}}
    - Student's Chinese Answer: "{{user_answer}}"

    # Core Policy:
    1. Treat reference answers as examples only. Accept semantically equivalent paraphrases.
    2. Do NOT penalize wording or word-order variation if meaning is preserved.
    3. Equivalent examples that should be accepted: 你叫什么？/ 你叫什么名字？/ 你的名字是什么？
    4. Penalize only true meaning errors (wrong subject/object, wrong polarity, missing key information, major tense/aspect meaning shift).
    5. If the student's answer is NOT written in Chinese (e.g., they answered in {lang_name} or another language), immediately set level=1, is_correct=false — do not evaluate content.

    # Evaluation Steps:
    A. Determine source intent.
    B. Compare core semantic slots (actor, action, object, constraint).
    C. Evaluate naturalness separately from correctness.

    # Grading Scale:
    - 4: Meaning fully correct and natural Chinese.
    - 3: Meaning correct with minor grammar/style issues.
    - 2: Partially correct; key information missing or awkward.
    - 1: Wrong meaning or wrong language (must be Chinese).

    # Decision Rule:
    - If meaning is preserved, is_correct MUST be true (level 3 or 4).
    - Never set is_correct=false only because expression differs from references.

    # Requirements:
    - The "explanation" MUST be in {lang_name}.
    - Address the student with "{you}" (e.g., "{you} wrote...", "{you} used...").
    - Keep exactly 2 short sentences separated by a newline character (\\n).
    - Sentence 1: summarize what the student's answer means.
    - Sentence 2: explain whether the meaning is correct and what to improve.

    # Output Format:
    JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
"""

_X_TO_CN_SPEAK_TPL = """
    # Role: Expert Chinese Speaking Coach for {lang_name} speakers
    # Task: Evaluate a spoken Chinese answer from ASR transcript.

    # Context:
    - Speaking prompt ({lang_name}): "{{question}}"
    - Reference Chinese Answers (examples, NOT exhaustive): {{standards}}
    - ASR transcript of student's spoken Chinese: "{{user_answer}}"

    # Core Policy:
    1. The transcript should be Chinese.
    2. Accept minor ASR punctuation/capitalization issues.
    3. Accept natural equivalent wording when meaning is preserved.
    4. Penalize missing key words, wrong grammar pattern, or wrong meaning.

    # Grading Scale:
    - 4: Fully correct and natural Chinese.
    - 3: Correct meaning with minor grammar or ASR wording issues.
    - 2: Partially correct; key words or grammar are missing.
    - 1: Wrong meaning, wrong language, or too far from the target.

    # Requirements:
    - The "explanation" MUST be in {lang_name}.
    - Address the student with "{you}".
    - Keep exactly 2 short sentences separated by a newline character (\\n).
    - Sentence 1: summarize what the ASR transcript says.
    - Sentence 2: explain whether it matches the target and what to improve.

    # Output Format:
    JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
"""


_LANG_CODE_ALIASES = {
    "cn": "zh",
    "zh": "zh",
    "jp": "ja",
    "ja": "ja",
    "en": "en",
    "fr": "fr",
    "de": "de",
    "ko": "ko",
    "ru": "ru",
    "es": "es",
    "pt": "pt",
    "vi": "vi",
    "th": "th",
    "ar": "ar",
    "it": "it",
    "id": "id",
    "ms": "ms",
}


_SPEAK_TPL = """
    # Role: Expert {target_name} Speaking Coach for {support_name} speakers
    # Task: Evaluate a spoken {target_name} answer from ASR transcript.

    # Context:
    - Speaking prompt ({support_name}): "{{question}}"
    - Reference {target_name} Answers (examples, NOT exhaustive): {{standards}}
    - ASR transcript of student's spoken {target_name}: "{{user_answer}}"

    # Core Policy:
    1. The transcript should be {target_name}.
    2. Accept minor ASR punctuation/capitalization issues.
    3. Accept natural equivalent wording when meaning is preserved.
    4. Penalize missing key words, wrong grammar pattern, or wrong meaning.

    # Grading Scale:
    - 4: Fully correct and natural {target_name}.
    - 3: Correct meaning with minor grammar or ASR wording issues.
    - 2: Partially correct; key words or grammar are missing.
    - 1: Wrong meaning, wrong language, or too far from the target.

    # Requirements:
    - The "explanation" MUST be in {support_name}.
    - Address the student with "{you}".
    - Keep exactly 2 short sentences separated by a newline character (\\n).
    - Sentence 1: summarize what the ASR transcript says.
    - Sentence 2: explain whether it matches the target and what to improve.

    # Output Format:
    JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
"""


_LISTEN_WRITE_TPL = """
    # Role: Expert {target_name} Dictation Coach for {support_name} speakers
    # Task: Evaluate a {target_name} dictation answer against the reference {target_name} sentence.

    # Context:
    - Dictation prompt ({support_name}): "{{question}}"
    - Reference {target_name} Answers: {{standards}}
    - Student's {target_name} Answer: "{{user_answer}}"

    # Core Policy:
    1. The answer must be {target_name}.
    2. Ignore capitalization and harmless punctuation differences.
    3. For dictation, semantic paraphrases are NOT enough; the wording should be close to the heard sentence.
    4. Penalize missing words, extra words, wrong word order, or wrong content words.

    # Grading Scale:
    - 4: Exact or near-exact sentence.
    - 3: One or two minor spelling/punctuation issues, sentence still clearly matches.
    - 2: Several missing or wrong words but recognizable.
    - 1: Different sentence, wrong language, or mostly missing.

    # Requirements:
    - The "explanation" MUST be in {support_name}.
    - Address the student with "{you}".
    - Keep exactly 2 short sentences separated by a newline character (\\n).
    - Sentence 1: point out what matched or what was heard incorrectly.
    - Sentence 2: give the corrected {target_name} sentence.

    # Output Format:
    JSON only: {{"level": int, "is_correct": bool, "explanation": string}}
"""


def _normalize_lang_code(code: Optional[str], default: str = "en") -> str:
    normalized = (code or "").strip().lower()
    if not normalized:
        return default
    return _LANG_CODE_ALIASES.get(normalized, normalized)


def _lang_meta(code: str) -> dict:
    normalized = _normalize_lang_code(code, code or "en")
    return _LANG_META.get(normalized.upper(), {"name": normalized.capitalize(), "you": "you"})


def _derive_support_language(target_code: str) -> str:
    return "en" if target_code == "zh" else "zh"


def _resolve_speak_languages(q_type: str, metadata: Optional[Dict[str, Any]] = None) -> tuple[str, str]:
    meta = metadata if isinstance(metadata, dict) else {}
    normalized_q_type = (q_type or "").strip().upper()

    target_code = _normalize_lang_code(
        meta.get("target_language") or meta.get("speech_language"),
        default="",
    )
    support_code = _normalize_lang_code(
        meta.get("support_language") or meta.get("source_language") or meta.get("audio_language") or meta.get("tts_language"),
        default="",
    )

    if normalized_q_type == "SPEAK":
        target_code = target_code or _normalize_lang_code(meta.get("speech_language"), default="zh")
        support_code = support_code or _derive_support_language(target_code)
        return target_code, support_code

    if normalized_q_type == "TARGET_SPEAK":
        return target_code or "en", support_code or "zh"

    if normalized_q_type == "JA_SPEAK":
        return target_code or "ja", support_code or "zh"

    if m := re.match(r"^(\w+)_TO_CN_SPEAK$", normalized_q_type):
        return target_code or "zh", support_code or _normalize_lang_code(m.group(1), default="en")

    return target_code or "zh", support_code or _derive_support_language(target_code or "zh")


def _resolve_listen_write_languages(q_type: str, metadata: Optional[Dict[str, Any]] = None) -> tuple[str, str]:
    meta = metadata if isinstance(metadata, dict) else {}
    normalized_q_type = (q_type or "").strip().upper()

    target_code = _normalize_lang_code(
        meta.get("target_language") or meta.get("audio_language"),
        default="",
    )
    support_code = _normalize_lang_code(
        meta.get("support_language") or meta.get("source_language") or meta.get("tts_language"),
        default="",
    )

    if normalized_q_type == "LISTEN_WRITE":
        target_code = target_code or _normalize_lang_code(meta.get("audio_language"), default="zh")
        support_code = support_code or _derive_support_language(target_code)
        return target_code, support_code

    if normalized_q_type == "TARGET_LISTEN_WRITE":
        return target_code or "en", support_code or "zh"

    if normalized_q_type == "JA_LISTEN_WRITE":
        return target_code or "ja", support_code or "zh"

    if normalized_q_type == "CN_LISTEN_WRITE":
        return target_code or "zh", support_code or "en"

    return target_code or "zh", support_code or _derive_support_language(target_code or "zh")


def _render_cn_to_x(target_code: str) -> str:
    m = _lang_meta(target_code)
    return _CN_TO_X_TPL.format(lang_name=m["name"], you=m["you"])


def _render_x_to_cn(source_code: str) -> str:
    m = _lang_meta(source_code)
    return _X_TO_CN_TPL.format(lang_name=m["name"], you=m["you"])


def _render_x_to_cn_speak(source_code: str) -> str:
    m = _lang_meta(source_code)
    return _X_TO_CN_SPEAK_TPL.format(lang_name=m["name"], you=m["you"])


def _render_speak_prompt(q_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    target_code, support_code = _resolve_speak_languages(q_type, metadata)
    target_meta = _lang_meta(target_code)
    support_meta = _lang_meta(support_code)
    return _SPEAK_TPL.format(
        target_name=target_meta["name"],
        support_name=support_meta["name"],
        you=support_meta["you"],
    )


def _render_listen_write_prompt(q_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    target_code, support_code = _resolve_listen_write_languages(q_type, metadata)
    target_meta = _lang_meta(target_code)
    support_meta = _lang_meta(support_code)
    return _LISTEN_WRITE_TPL.format(
        target_name=target_meta["name"],
        support_name=support_meta["name"],
        you=support_meta["you"],
    )


def get_eval_prompt(q_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Return the evaluation prompt for a given question type."""
    normalized_q_type = (q_type or "").strip().upper()

    if normalized_q_type == "SPEAK":
        return _render_speak_prompt(normalized_q_type, metadata)

    if normalized_q_type == "LISTEN_WRITE":
        return _render_listen_write_prompt(normalized_q_type, metadata)

    if normalized_q_type in _EXACT_PROMPTS:
        return _EXACT_PROMPTS[normalized_q_type]

    if m := re.match(r"^CN_TO_(\w+)$", normalized_q_type):
        return _render_cn_to_x(m.group(1))

    if m := re.match(r"^(\w+)_TO_CN_SPEAK$", normalized_q_type):
        return _render_x_to_cn_speak(m.group(1))

    if m := re.match(r"^(\w+)_TO_CN$", normalized_q_type):
        return _render_x_to_cn(m.group(1))

    # Legacy / New Concept English types
    if normalized_q_type in ("SUPPORT_TO_TARGET",):
        return _EXACT_PROMPTS["PATTERN_DRILL"]
    if normalized_q_type in {"CN_LISTEN_WRITE", "JA_LISTEN_WRITE", "TARGET_LISTEN_WRITE"}:
        return _render_listen_write_prompt(normalized_q_type, metadata)
    if normalized_q_type in {"JA_SPEAK", "TARGET_SPEAK"}:
        return _render_speak_prompt(normalized_q_type, metadata)

    return _EXACT_PROMPTS["CN_TO_EN"]
