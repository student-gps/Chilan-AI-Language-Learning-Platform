"""
一次性脚本：为课程介绍幻灯片生成 TTS 旁白音频。

输出目录：frontend/public/audio/intro/
  EN:  slide_{id}.mp3
  FR:  slide_{id}_fr.mp3  (uses TTS_EXPLANATION_PROVIDER_FR / TTS_EXPLANATION_VOICE_FR from .env)

用法：
    cd backend
    python generate_intro_narration.py           # English (default)
    python generate_intro_narration.py --lang fr  # French
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from content_builder.tasks.narration_audio import Task4DExplanationNarrator

# ── Narration texts per language ──────────────────────────────────────────────

SLIDES_EN = [
    {
        "id": "welcome",
        "narration": (
            "Welcome to Chilan — an AI-powered Chinese language learning platform. "
            "This course builds real communication skills: listening, speaking, and typing. "
            "We start from first principles, beginning with the sound system."
        ),
    },
    {
        "id": "sounds",
        "narration": (
            "Every Chinese syllable has a tone, and changing the tone completely changes the meaning. "
            "The four tones are high and level, rising, falling-rising, and falling. "
            "Mastering tones is the single most important foundation in Chinese."
        ),
    },
    {
        "id": "skills",
        "narration": (
            "This course trains three core skills: listening, speaking, and typing with a pinyin input method. "
            "We focus on how Chinese is actually used in daily digital life — not handwriting. "
            "You'll be able to read, listen, speak, and type before long."
        ),
    },
    {
        "id": "ai",
        "narration": (
            "Every answer you submit is evaluated by a three-tier system. "
            "Instant pattern matching handles obvious cases. "
            "Semantic comparison catches answers that mean the same thing in different words. "
            "And a large language model handles genuine edge cases with a detailed explanation."
        ),
    },
    {
        "id": "fsrs",
        "narration": (
            "Your review schedule is powered by FSRS — the Free Spaced Repetition Scheduler. "
            "Items you know well come back less often. Tricky items reappear sooner. "
            "This ensures you spend your study time exactly where it's needed."
        ),
    },
    {
        "id": "start",
        "narration": (
            "You're ready to begin. "
            "Start with the foundation modules: pinyin for the sound system, "
            "then Chinese characters for structure. "
            "Every lesson in the course builds on these foundations."
        ),
    },
]

SLIDES_FR = [
    {
        "id": "welcome",
        "narration": (
            "Bienvenue sur Chilan — une plateforme d'apprentissage du chinois propulsée par l'IA. "
            "Ce cours développe de vraies compétences de communication : écoute, expression orale et saisie au clavier. "
            "Nous partons des principes de base, en commençant par le système phonétique."
        ),
    },
    {
        "id": "sounds",
        "narration": (
            "Chaque syllabe chinoise a un ton, et changer le ton change complètement le sens. "
            "Les quatre tons sont haut et égal, montant, descendant-montant et descendant. "
            "Maîtriser les tons est la base la plus importante du chinois."
        ),
    },
    {
        "id": "skills",
        "narration": (
            "Ce cours entraîne trois compétences clés : l'écoute, l'expression orale et la saisie avec une méthode de saisie pinyin. "
            "Nous nous concentrons sur l'utilisation réelle du chinois dans la vie numérique quotidienne — pas l'écriture manuscrite. "
            "Vous pourrez bientôt lire, écouter, parler et taper."
        ),
    },
    {
        "id": "ai",
        "narration": (
            "Chaque réponse que vous soumettez est évaluée par un système à trois niveaux. "
            "La correspondance de motif instantanée gère les cas évidents. "
            "La comparaison sémantique détecte les réponses qui ont le même sens avec des mots différents. "
            "Et un grand modèle de langage gère les vrais cas limites avec une explication détaillée."
        ),
    },
    {
        "id": "fsrs",
        "narration": (
            "Votre calendrier de révision est alimenté par FSRS — le Planificateur de Répétition Espacée Gratuit. "
            "Les éléments que vous connaissez bien reviennent moins souvent. Les éléments difficiles réapparaissent plus tôt. "
            "Cela garantit que vous consacrez votre temps d'étude exactement là où c'est nécessaire."
        ),
    },
    {
        "id": "start",
        "narration": (
            "Vous êtes prêt à commencer. "
            "Démarrez avec les modules de base : le pinyin pour le système phonétique, "
            "puis les caractères chinois pour la structure. "
            "Chaque leçon du cours s'appuie sur ces fondations."
        ),
    },
]

SLIDES_BY_LANG = {
    "en": SLIDES_EN,
    "fr": SLIDES_FR,
}

BACKEND_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BACKEND_DIR.parent / "frontend" / "public" / "audio" / "intro"


def main():
    parser = argparse.ArgumentParser(description="Generate intro narration audio")
    parser.add_argument("--lang", default="en", choices=list(SLIDES_BY_LANG.keys()),
                        help="Language code (default: en)")
    args = parser.parse_args()
    lang = args.lang

    slides = SLIDES_BY_LANG[lang]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    tts = Task4DExplanationNarrator()
    tts._configure_for_lang(lang)
    print(f"Language:     {lang}")
    print(f"TTS provider: {tts.provider}  voice: {tts.voice}")
    print(f"Output dir:   {OUTPUT_DIR}\n")

    suffix = f"_{lang}" if lang != "en" else ""
    ok, fail = 0, 0
    for slide in slides:
        slide_id = slide["id"]
        text = slide["narration"]
        out_path = OUTPUT_DIR / f"slide_{slide_id}{suffix}.mp3"

        print(f"🔊  [{slide_id}]  {text[:60]}…")
        try:
            tts._synthesize(text, out_path)
            size_kb = out_path.stat().st_size // 1024
            print(f"  ✅  saved → {out_path.name}  ({size_kb} KB)\n")
            ok += 1
        except Exception as e:
            print(f"  ❌  failed: {e}\n")
            fail += 1

    print(f"完成：{ok} 成功，{fail} 失败。")
    suffix_display = suffix or ""
    print(f"\n前端引用路径：/audio/intro/slide_{{id}}{suffix_display}.mp3")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
