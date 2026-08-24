from typing import Any, Dict, Optional

from services.study.practice_item_schema import PracticeItemSchemaError, canonicalize_practice_item


_LANG_META = {
    "en": {"name": "English", "you": "you", "correct_answer_lead": "A correct answer is", "corrected_sentence_lead": "The corrected sentence is"},
    "fr": {"name": "French", "you": "vous", "correct_answer_lead": "Une réponse correcte est", "corrected_sentence_lead": "La phrase corrigée est"},
    "ja": {"name": "Japanese", "you": "あなた", "correct_answer_lead": "正しい答えは", "corrected_sentence_lead": "訂正した文は"},
    "zh": {"name": "Chinese", "you": "你", "correct_answer_lead": "正确答案是", "corrected_sentence_lead": "订正后的句子是"},
    "de": {"name": "German", "you": "Sie", "correct_answer_lead": "Eine richtige Antwort ist", "corrected_sentence_lead": "Der korrigierte Satz lautet"},
    "ko": {"name": "Korean", "you": "당신", "correct_answer_lead": "정답은", "corrected_sentence_lead": "수정한 문장은"},
    "ru": {"name": "Russian", "you": "вы", "correct_answer_lead": "Правильный ответ", "corrected_sentence_lead": "Исправленное предложение"},
    "es": {"name": "Spanish", "you": "usted", "correct_answer_lead": "Una respuesta correcta es", "corrected_sentence_lead": "La frase corregida es"},
    "pt": {"name": "Portuguese", "you": "você", "correct_answer_lead": "Uma resposta correta é", "corrected_sentence_lead": "A frase corrigida é"},
    "vi": {"name": "Vietnamese", "you": "bạn", "correct_answer_lead": "Một đáp án đúng là", "corrected_sentence_lead": "Câu đã sửa là"},
    "th": {"name": "Thai", "you": "คุณ", "correct_answer_lead": "คำตอบที่ถูกต้องคือ", "corrected_sentence_lead": "ประโยคที่แก้ไขแล้วคือ"},
    "ar": {"name": "Arabic", "you": "أنت", "correct_answer_lead": "إجابة صحيحة هي", "corrected_sentence_lead": "الجملة المصححة هي"},
    "it": {"name": "Italian", "you": "lei", "correct_answer_lead": "Una risposta corretta è", "corrected_sentence_lead": "La frase corretta è"},
    "id": {"name": "Indonesian", "you": "Anda", "correct_answer_lead": "Jawaban yang benar adalah", "corrected_sentence_lead": "Kalimat yang telah diperbaiki adalah"},
    "ms": {"name": "Malay", "you": "anda", "correct_answer_lead": "Jawapan yang betul ialah", "corrected_sentence_lead": "Ayat yang dibetulkan ialah"},
}

_TRANSLATE_TPL = """
# Role: Expert {answer_name} Tutor for {feedback_name} Speakers
# Task: Evaluate a translation from {prompt_name} to {answer_name} by MEANING equivalence, not surface wording.

# Core Policy:
1. Treat reference answers as examples only. Accept semantically equivalent paraphrases.
2. Do NOT penalize wording or word-order variation if meaning is preserved.
3. Penalize only true meaning errors: wrong subject/object, wrong polarity, missing key information, or a major tense/aspect meaning shift.
4. The student's answer must be written in {answer_name}; if it is in another language, set level=1 and is_correct=false.

# Evaluation Steps:
A. Determine the source intent.
B. Compare core semantic slots: actor, action, object, and constraint.
C. Evaluate naturalness separately from correctness.

# Grading Scale:
- 4: Meaning fully correct and natural.
- 3: Meaning correct with minor grammar or style issues.
- 2: Partially correct; key information is missing or awkward.
- 1: Wrong meaning, wrong language, or too far from the target.

# Decision Rule:
- If meaning is preserved, is_correct MUST be true with level 3 or 4.
- Never set is_correct=false only because wording differs from the references.

# Requirements:
- The "explanation" MUST be in {feedback_name}.
- Address the student with "{you}".
- Keep exactly 2 short sentences separated by a newline character (\\n).
- Sentence 1: summarize what the student's answer means.
- Sentence 2: if is_correct=false, begin with the exact {feedback_name} phrase “{correct_answer_lead}” and quote one or two appropriate answers from Reference {answer_name} Answers, then state why they correct the error; if is_correct=true, confirm correctness and give a concise improvement only if useful.

# Output Format:
JSON only: {{{{"level": int, "is_correct": bool, "explanation": string}}}}

# Evaluation Input:
- Source {prompt_name}: "{{question}}"
- Reference {answer_name} Answers (examples, NOT exhaustive): {{standards}}
- Student's {answer_name} Answer: "{{user_answer}}"
"""

_SPEAK_TPL = """
# Role: Expert {answer_name} Speaking Coach for {feedback_name} Speakers
# Task: Evaluate a spoken {answer_name} answer from an ASR transcript.

# Core Policy:
1. The transcript should be {answer_name}.
2. Accept minor ASR punctuation or capitalization issues.
3. Accept natural equivalent wording when the prompt meaning is preserved.
4. Penalize missing key words, wrong grammar patterns, wrong polarity, or wrong meaning.

# Grading Scale:
- 4: Fully correct and natural {answer_name}.
- 3: Correct meaning with minor grammar or ASR wording issues.
- 2: Partially correct; key words or grammar are missing.
- 1: Wrong meaning, wrong language, or too far from the target.

# Requirements:
- The "explanation" MUST be in {feedback_name}.
- Address the student with "{you}".
- Keep exactly 2 short sentences separated by a newline character (\\n).
- Sentence 1: summarize what the ASR transcript says.
- Sentence 2: if is_correct=false, begin with the exact {feedback_name} phrase “{correct_answer_lead}” and quote one or two appropriate answers from Reference {answer_name} Answers, then state why they correct the error; if is_correct=true, confirm correctness and give a concise improvement only if useful.

# Output Format:
JSON only: {{{{"level": int, "is_correct": bool, "explanation": string}}}}

# Evaluation Input:
- Speaking prompt ({prompt_name}): "{{question}}"
- Reference {answer_name} Answers (examples, NOT exhaustive): {{standards}}
- ASR transcript of the student's {answer_name}: "{{user_answer}}"
"""

_LISTEN_WRITE_TPL = """
# Role: Expert {answer_name} Dictation Coach for {feedback_name} Speakers
# Task: Evaluate a {answer_name} dictation answer against the reference {answer_name} sentence.

# Core Policy:
1. The answer must be {answer_name}.
2. Ignore harmless capitalization, punctuation, and spacing differences.
3. For dictation, semantic paraphrases are NOT enough; the wording must closely match the heard sentence.
4. Penalize missing words, extra words, wrong word order, wrong content words, or script changes that alter the word.

# Grading Scale:
- 4: Exact or near-exact sentence.
- 3: One or two minor spelling or notation issues; the sentence clearly matches.
- 2: Several missing or wrong words but the sentence remains recognizable.
- 1: Different sentence, wrong language, or mostly missing.

# Requirements:
- The "explanation" MUST be in {feedback_name}.
- Address the student with "{you}".
- Keep exactly 2 short sentences separated by a newline character (\\n).
- Sentence 1: point out what matched or what was heard incorrectly.
- Sentence 2: if is_correct=false, begin with the exact {feedback_name} phrase “{corrected_sentence_lead}” and quote the most appropriate Reference {answer_name} Answer; if is_correct=true, confirm that the dictation matches.

# Output Format:
JSON only: {{{{"level": int, "is_correct": bool, "explanation": string}}}}

# Evaluation Input:
- Dictation prompt ({prompt_name}): "{{question}}"
- Reference {answer_name} Answers: {{standards}}
- Student's {answer_name} Answer: "{{user_answer}}"
"""

_PATTERN_DRILL_TPL = """
# Role: Expert {answer_name} Pattern Coach for {feedback_name} Speakers
# Task: Evaluate whether the student produced the required {answer_name} pattern sentence.

# Core Policy:
1. The answer must be {answer_name}.
2. Accept minor punctuation or capitalization differences.
3. Accept semantically equivalent contractions only when the required pattern and meaning are preserved.
4. Penalize wrong slot words, missing grammar words, wrong question/statement form, wrong polarity, or a different pattern.

# Grading Scale:
- 4: Correct pattern, correct slot word, and natural {answer_name}.
- 3: Meaning and pattern are correct with minor grammar or punctuation issues.
- 2: Partially correct but missing important pattern words or using the wrong form.
- 1: Wrong meaning, wrong language, or not close to the target sentence.

# Requirements:
- The "explanation" MUST be in {feedback_name}.
- Address the student with "{you}".
- Keep exactly 2 short sentences separated by a newline character (\\n).
- Sentence 1: say what the student's answer means or which pattern they used.
- Sentence 2: if is_correct=false, begin with the exact {feedback_name} phrase “{correct_answer_lead}” and quote one or two appropriate answers from Reference {answer_name} Answers, then state which pattern element needs correction; if is_correct=true, confirm correctness and give a concise improvement only if useful.

# Output Format:
JSON only: {{{{"level": int, "is_correct": bool, "explanation": string}}}}

# Evaluation Input:
- {prompt_name} pattern task: "{{question}}"
- Reference {answer_name} Answers: {{standards}}
- Student's {answer_name} Answer: "{{user_answer}}"
"""


def _language_meta(code: str) -> dict[str, str]:
    try:
        return _LANG_META[code]
    except KeyError as exc:
        raise PracticeItemSchemaError(f"No judge prompt language metadata for {code!r}") from exc


def get_eval_prompt(q_type: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """Render a language-agnostic Tier 3 judge prompt from schema-v2 metadata."""
    canonical_type, normalized = canonicalize_practice_item(q_type, metadata)
    prompt_meta = _language_meta(normalized["prompt_language"])
    answer_meta = _language_meta(normalized["answer_language"])
    feedback_meta = _language_meta(normalized["feedback_language"])

    template_by_type = {
        "TRANSLATE": _TRANSLATE_TPL,
        "SPEAK": _SPEAK_TPL,
        "LISTEN_WRITE": _LISTEN_WRITE_TPL,
        "PATTERN_DRILL": _PATTERN_DRILL_TPL,
        "PARTICLE_FILL": _PATTERN_DRILL_TPL,
        "CONJUGATION": _PATTERN_DRILL_TPL,
        "TONE_MARKING": _PATTERN_DRILL_TPL,
        "MEASURE_WORD_FILL": _PATTERN_DRILL_TPL,
        "SENTENCE_SOURCE_TO_TARGET": _TRANSLATE_TPL,
        "SENTENCE_TARGET_TO_SOURCE": _TRANSLATE_TPL,
        "VOCAB_SOURCE_TO_TARGET": _TRANSLATE_TPL,
        "VOCAB_TARGET_TO_SOURCE": _TRANSLATE_TPL,
    }
    if canonical_type in {
        "TRANSLATE",
        "SENTENCE_SOURCE_TO_TARGET",
        "SENTENCE_TARGET_TO_SOURCE",
        "VOCAB_SOURCE_TO_TARGET",
        "VOCAB_TARGET_TO_SOURCE",
    }:
        template = _TRANSLATE_TPL
    else:
        template = template_by_type[canonical_type]
    return template.format(
        prompt_name=prompt_meta["name"],
        answer_name=answer_meta["name"],
        feedback_name=feedback_meta["name"],
        you=feedback_meta["you"],
        correct_answer_lead=feedback_meta["correct_answer_lead"],
        corrected_sentence_lead=feedback_meta["corrected_sentence_lead"],
    )
