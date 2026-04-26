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
    """,

    "CN_TO_FR": """
        # Rôle : Coach linguistique expert pour les francophones
        # Tâche : Évaluer une traduction du chinois vers le français par équivalence de SENS, pas de formulation exacte.

        # Contexte :
        - Source chinoise : "{question}"
        - Réponses françaises de référence (exemples, non exhaustifs) : {standards}
        - Réponse française de l'étudiant : "{user_answer}"

        # Politique principale :
        1. Traiter les réponses de référence comme des exemples seulement. Accepter les paraphrases sémantiquement équivalentes.
        2. Ne PAS pénaliser les variations de formulation ou d'ordre des mots si le sens est préservé.
        3. Pénaliser uniquement les vraies erreurs de sens (sujet/objet incorrect, polarité incorrecte, information clé manquante).

        # Étapes d'évaluation :
        A. Déterminer l'intention de la source.
        B. Comparer les éléments sémantiques clés (acteur, action, objet, contrainte).
        C. Évaluer la naturalité séparément de la correction.

        # Échelle de notation :
        - 4 : Sens entièrement correct et naturel.
        - 3 : Sens correct avec des problèmes mineurs de grammaire ou de style.
        - 2 : Partiellement correct ; information clé manquante ou formulation maladroite.
        - 1 : Sens incorrect ou mauvaise langue utilisée.

        # Règle de décision :
        - Si le sens est préservé, is_correct DOIT être true (niveau 3 ou 4).
        - Ne jamais mettre is_correct=false uniquement parce que l'expression diffère des références.

        # Exigences :
        - L'"explanation" DOIT être en français.
        - Utilisez "Vous" pour vous adresser directement à l'étudiant (ex. : "Vous avez dit...", "Vous avez utilisé...").
        - Exactement 2 courtes phrases séparées par un caractère de nouvelle ligne (\\n).
        - Phrase 1 : résumez ce que signifie la réponse de l'étudiant.
        - Phrase 2 : expliquez si le sens est correct et ce qu'il faut améliorer.

        # Format de sortie :
        JSON uniquement : {{"level": int, "is_correct": bool, "explanation": string}}
    """,

    "FR_TO_CN": """
        # Rôle : Professeur de chinois expert pour les francophones
        # Tâche : Évaluer une traduction du français vers le chinois par équivalence de SENS, pas de formulation exacte.

        # Contexte :
        - Source française : "{question}"
        - Réponses chinoises de référence (exemples, non exhaustifs) : {standards}
        - Réponse chinoise de l'étudiant : "{user_answer}"

        # Politique principale :
        1. Traiter les réponses de référence comme des exemples seulement. Accepter les paraphrases sémantiquement équivalentes.
        2. Ne PAS pénaliser les variations de formulation si le sens est préservé.
        3. Exemples équivalents qui doivent être acceptés :
           - 你叫什么？
           - 你叫什么名字？
           - 你的名字是什么？
        4. Pénaliser uniquement les vraies erreurs de sens (sujet/objet incorrect, polarité incorrecte, information clé manquante).

        # Étapes d'évaluation :
        A. Déterminer l'intention de la source.
        B. Comparer les éléments sémantiques clés (acteur, action, objet, contrainte).
        C. Évaluer la naturalité séparément de la correction.

        # Échelle de notation :
        - 4 : Sens entièrement correct et naturel.
        - 3 : Sens correct avec des problèmes mineurs de grammaire ou de style.
        - 2 : Partiellement correct ; information clé manquante ou formulation maladroite.
        - 1 : Sens incorrect ou mauvaise langue utilisée.

        # Règle de décision :
        - Si le sens est préservé, is_correct DOIT être true (niveau 3 ou 4).
        - Ne jamais mettre is_correct=false uniquement parce que l'expression diffère des références.

        # Exigences :
        - L'"explanation" DOIT être en français.
        - Utilisez "Vous" pour vous adresser directement à l'étudiant (ex. : "Vous avez écrit...", "Vous avez utilisé...").
        - Exactement 2 courtes phrases séparées par un caractère de nouvelle ligne (\\n).
        - Phrase 1 : résumez ce que signifie la réponse de l'étudiant.
        - Phrase 2 : expliquez si le sens est correct et ce qu'il faut améliorer.

        # Format de sortie :
        JSON uniquement : {{"level": int, "is_correct": bool, "explanation": string}}
    """,
}

# Fallback: map language-specific types to their base template when no dedicated prompt exists
_TYPE_FALLBACK = {
    "FR_TO_CN_SPEAK": "FR_TO_CN",
    "CN_LISTEN_WRITE": "EN_TO_CN",
}

def get_eval_prompt(q_type: str) -> str:
    """Return the evaluation prompt for a given question type, with fallback."""
    if q_type in EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH:
        return EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH[q_type]
    resolved = _TYPE_FALLBACK.get(q_type)
    if resolved:
        return EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH[resolved]
    # Generic fallback: infer from suffix
    if q_type.endswith("_TO_CN") or q_type.endswith("_TO_CN_SPEAK"):
        return EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH["EN_TO_CN"]
    if q_type.startswith("CN_TO_"):
        return EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH["CN_TO_EN"]
    return EVALUATE_PROMPT_TEMPLATE_LEARN_CHINESE_BY_ENGLISH["EN_TO_CN"]
