EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH = {
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
    """
}
