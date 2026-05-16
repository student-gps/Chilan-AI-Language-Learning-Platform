const buildIntroVideoTranslations = ({
  title,
  accent,
  sub,
  sounds,
  skills,
  ai,
  fsrs,
  start,
  narration,
}) => ({
  civ_welcome_h1: title,
  civ_welcome_accent: accent,
  civ_welcome_sub: sub,
  civ_sounds_label: sounds.label,
  civ_sounds_h2_pre: sounds.h2Pre,
  civ_sounds_h2_accent: sounds.h2Accent,
  civ_sounds_sub: sounds.sub,
  civ_sounds_tone0_label: sounds.toneLabels[0],
  civ_sounds_tone0_name: sounds.toneNames[0],
  civ_sounds_tone1_label: sounds.toneLabels[1],
  civ_sounds_tone1_name: sounds.toneNames[1],
  civ_sounds_tone2_label: sounds.toneLabels[2],
  civ_sounds_tone2_name: sounds.toneNames[2],
  civ_sounds_tone3_label: sounds.toneLabels[3],
  civ_sounds_tone3_name: sounds.toneNames[3],
  civ_sounds_example: sounds.example,
  civ_skills_label: skills.label,
  civ_skills_h2_pre: skills.h2Pre,
  civ_skills_h2_accent: skills.h2Accent,
  civ_skills_sk0_label: skills.items[0].label,
  civ_skills_sk0_sub: skills.items[0].sub,
  civ_skills_sk1_label: skills.items[1].label,
  civ_skills_sk1_sub: skills.items[1].sub,
  civ_skills_sk2_label: skills.items[2].label,
  civ_skills_sk2_sub: skills.items[2].sub,
  civ_skills_no_hw: skills.noHw,
  civ_ai_label: ai.label,
  civ_ai_h2_pre: ai.h2Pre,
  civ_ai_h2_accent: ai.h2Accent,
  civ_ai_sub: ai.sub,
  civ_ai_example_label: ai.exampleLabel,
  civ_ai_example_ans1: ai.answers[0],
  civ_ai_example_ans2: ai.answers[1],
  civ_ai_example_note: ai.note,
  civ_ai_tier0_label: ai.tiers[0].label,
  civ_ai_tier0_desc: ai.tiers[0].desc,
  civ_ai_tier1_label: ai.tiers[1].label,
  civ_ai_tier1_desc: ai.tiers[1].desc,
  civ_ai_tier2_label: ai.tiers[2].label,
  civ_ai_tier2_desc: ai.tiers[2].desc,
  civ_fsrs_label: fsrs.label,
  civ_fsrs_h2_pre: fsrs.h2Pre,
  civ_fsrs_h2_accent: fsrs.h2Accent,
  civ_fsrs_sub: fsrs.sub,
  civ_fsrs_chart_label: fsrs.chartLabel,
  civ_fsrs_leg0: fsrs.legend[0],
  civ_fsrs_leg1: fsrs.legend[1],
  civ_fsrs_leg2: fsrs.legend[2],
  civ_start_label: start.label,
  civ_start_h2_pre: start.h2Pre,
  civ_start_h2_accent: start.h2Accent,
  civ_start_sub: start.sub,
  civ_start_step0_label: start.steps[0].label,
  civ_start_step0_sub: start.steps[0].sub,
  civ_start_step1_label: start.steps[1].label,
  civ_start_step1_sub: start.steps[1].sub,
  civ_start_step2_label: start.steps[2].label,
  civ_start_step2_sub: start.steps[2].sub,
  civ_start_step3_label: start.steps[3].label,
  civ_start_step3_sub: start.steps[3].sub,
  civ_start_note: start.note,
  civ_narration_welcome: narration.welcome,
  civ_narration_sounds: narration.sounds,
  civ_narration_skills: narration.skills,
  civ_narration_ai: narration.ai,
  civ_narration_fsrs: narration.fsrs,
  civ_narration_start: narration.start,
});

const common = {
  zhTerms: {
    pinyin: "Pinyin",
    hanzi: "Hanzi",
    vocabulary: "Vocabulary",
    sentences: "Sentences",
    soundsTones: "Sounds & tones",
    structure: "Structure",
    wordsInContext: "Words in context",
    grammarPatterns: "Grammar patterns",
  },
};

export const INTRO_VIDEO_TRANSLATIONS = {
  jp: buildIntroVideoTranslations({
    title: "中国語を学ぶ",
    accent: "実際に使われる形で",
    sub: "AI搭載 · コミュニケーション重視 · デジタル時代のために",
    sounds: { label: "基礎 — ステップ1", h2Pre: "まずは", h2Accent: "音", sub: "単語や文法の前に、意味を変える4つの声調を身につけます。", toneLabels: ["第1声", "第2声", "第3声", "第4声"], toneNames: ["高く平ら", "上昇", "下降上昇", "下降"], example: "妈 · 麻 · 马 · 骂 — 同じ音節でも4つの意味" },
    skills: { label: "練習すること", h2Pre: "三つの力を", h2Accent: "一つのコースで", items: [{ label: "聞く", sub: "単語と文に音声。ディクテーションで耳を鍛えます。" }, { label: "話す", sub: "声を録音。AIが発音だけでなく意味を確認します。" }, { label: "入力", sub: "ピンインIMEで、日常的な中国語入力を学びます。" }], noHw: "手書きは別の技能です。このコースは読む、聞く、話す、入力に集中します。" },
    ai: { label: "回答の判定方法", h2Pre: "AIが", h2Accent: "すべての回答を評価", sub: "即時パターン照合 → 意味類似度 → LLM分析。正確な言い回しより意味を重視します。", exampleLabel: "例", answers: ["「普段は何をしますか？」", "「いつも何をしますか？」"], note: "どちらも正解。同じ意味、違う表現です。", tiers: [{ label: "完全一致", desc: "正規表現 / パターン" }, { label: "意味", desc: "埋め込み類似度" }, { label: "AI分析", desc: "LLM判定 + 解説" }] },
    fsrs: { label: "記憶科学", h2Pre: "抜け落ちる内容は", h2Accent: "ありません", sub: "FSRSが各単語をいつ復習すべきか計算します。", chartLabel: "1語の復習スケジュール例", legend: ["初期は頻繁に復習", "間隔が広がる", "長期記憶"] },
    start: { label: "学習ルート", h2Pre: "始める", h2Accent: "準備はできましたか？", sub: "基礎から始めましょう。すべてはその上に積み重なります。", steps: [{ label: common.zhTerms.pinyin, sub: "音と声調" }, { label: common.zhTerms.hanzi, sub: "構造と部首" }, { label: "語彙", sub: "文脈の中の単語" }, { label: "文", sub: "文法パターン" }], note: "教室の基礎モジュールから始めましょう。" },
    narration: { welcome: "Chilanへようこそ。AIを活用した中国語学習プラットフォームです。このコースでは、聞く、話す、入力するという実用的なコミュニケーション能力を育てます。まずは原理から、音の体系から始めます。", sounds: "中国語のすべての音節には声調があり、声調が変わると意味も大きく変わります。四つの声調は、高く平らな音、上がる音、下がって上がる音、そして下がる音です。声調を身につけることは、中国語学習でもっとも重要な基礎です。", skills: "このコースでは、聞く力、話す力、そしてピンイン入力で文字を打つ力という三つの中心スキルを鍛えます。手書きではなく、日常のデジタル生活で中国語が実際に使われる方法に集中します。まもなく、読んで、聞いて、話して、入力できるようになります。", ai: "あなたが送信するすべての回答は、三段階のシステムで評価されます。明らかなケースは即時のパターン照合で処理します。意味の比較は、言い方が違っても同じ意味の回答を捉えます。そして大規模言語モデルが、本当に微妙なケースを判断し、詳しい説明を返します。", fsrs: "復習スケジュールはFSRS、つまり自由間隔反復スケジューラーによって管理されます。よく覚えている項目は少ない頻度で戻ってきます。難しい項目はより早く再登場します。これにより、学習時間を本当に必要なところに使えます。", start: "準備はできました。まずは基礎モジュールから始めましょう。ピンインで音の体系を学び、次に漢字で構造を理解します。コース内のすべてのレッスンは、この基礎の上に積み重なります。" },
  }),
  de: buildIntroVideoTranslations({
    title: "Chinesisch lernen", accent: "so, wie es wirklich verwendet wird", sub: "KI-gestützt · Kommunikation zuerst · für das digitale Zeitalter",
    sounds: { label: "Grundlage — Schritt 1", h2Pre: "Wir beginnen mit ", h2Accent: "Lauten", sub: "Vor Wörtern und Grammatik: die 4 Töne, die alles verändern.", toneLabels: ["1. Ton", "2. Ton", "3. Ton", "4. Ton"], toneNames: ["hoch eben", "steigend", "fallend-steigend", "fallend"], example: "妈 · 麻 · 马 · 骂 — gleiche Silbe, vier Bedeutungen" },
    skills: { label: "Was du übst", h2Pre: "Drei Fähigkeiten, ", h2Accent: "ein Kurs", items: [{ label: "Hören", sub: "Audio für jedes Wort und jeden Satz. Diktate trainieren dein Ohr." }, { label: "Sprechen", sub: "Nimm deine Stimme auf. KI prüft Bedeutung, nicht nur Aussprache." }, { label: "Tippen", sub: "Pinyin-IME, wie Muttersprachler täglich schreiben." }], noHw: "Handschrift ist eine eigene Fähigkeit. Dieser Kurs konzentriert sich auf Lesen, Hören, Sprechen und Tippen." },
    ai: { label: "Wie Antworten bewertet werden", h2Pre: "KI bewertet", h2Accent: "jede Antwort", sub: "Drei Stufen: Musterabgleich → semantische Ähnlichkeit → LLM-Analyse. Bedeutung zählt mehr als exakte Formulierung.", exampleLabel: "Beispiel", answers: ["„Was machst du normalerweise?“", "„Was tust du gewöhnlich?“"], note: "Beides akzeptiert: gleiche Bedeutung, andere Wörter.", tiers: [{ label: "Exakt", desc: "Regex / Muster" }, { label: "Semantik", desc: "Ähnlichkeitsscore" }, { label: "KI-Analyse", desc: "LLM-Urteil + Erklärung" }] },
    fsrs: { label: "Gedächtniswissenschaft", h2Pre: "Nichts fällt ", h2Accent: "durchs Raster", sub: "FSRS berechnet genau, wann jedes Wort wiederholt werden soll.", chartLabel: "Beispiel-Wiederholungsplan für ein Wort", legend: ["frühe häufige Wiederholung", "Abstände wachsen", "langfristiges Behalten"] },
    start: { label: "Dein Weg", h2Pre: "Bereit zu ", h2Accent: "starten?", sub: "Beginne mit den Grundlagen. Alles Weitere baut darauf auf.", steps: [{ label: "Pinyin", sub: "Laute & Töne" }, { label: "Zeichen", sub: "Struktur & Radikale" }, { label: "Wortschatz", sub: "Wörter im Kontext" }, { label: "Sätze", sub: "Grammatikmuster" }], note: "Nutze die Grundlagenmodule im Klassenzimmer, um zu beginnen." },
    narration: { welcome: "Willkommen bei Chilan, einer KI-gestützten Plattform zum Chinesischlernen. Dieser Kurs baut echte Kommunikationsfähigkeiten auf: Hören, Sprechen und Tippen. Wir beginnen bei den Grundlagen, zuerst mit dem Lautsystem.", sounds: "Jede chinesische Silbe hat einen Ton, und ein anderer Ton kann die Bedeutung völlig verändern. Die vier Töne sind hoch und eben, steigend, fallend-steigend und fallend. Die Töne zu beherrschen ist die wichtigste Grundlage im Chinesischen.", skills: "Dieser Kurs trainiert drei Kernfähigkeiten: Hören, Sprechen und Tippen mit einer Pinyin-Eingabemethode. Wir konzentrieren uns darauf, wie Chinesisch im digitalen Alltag wirklich verwendet wird, nicht auf Handschrift. Schon bald kannst du lesen, hören, sprechen und tippen.", ai: "Jede Antwort, die du eingibst, wird von einem dreistufigen System bewertet. Ein sofortiger Musterabgleich behandelt klare Fälle. Der semantische Vergleich erkennt Antworten mit gleicher Bedeutung, auch wenn sie anders formuliert sind. Und ein großes Sprachmodell behandelt echte Grenzfälle mit einer ausführlichen Erklärung.", fsrs: "Dein Wiederholungsplan wird von FSRS gesteuert, dem Free Spaced Repetition Scheduler. Inhalte, die du gut kannst, kommen seltener zurück. Schwierige Inhalte erscheinen früher wieder. So nutzt du deine Lernzeit genau dort, wo sie am meisten gebraucht wird.", start: "Du bist bereit zu beginnen. Starte mit den Grundlagenmodulen: Pinyin für das Lautsystem und danach chinesische Schriftzeichen für die Struktur. Jede Lektion in diesem Kurs baut auf diesen Grundlagen auf." },
  }),
};

const copyIntroLocale = (locale, patch) => {
  const narrationOverrides = patch.narration
    ? {
        civ_narration_welcome: patch.narration.welcome,
        civ_narration_sounds: patch.narration.sounds,
        civ_narration_skills: patch.narration.skills,
        civ_narration_ai: patch.narration.ai,
        civ_narration_fsrs: patch.narration.fsrs,
        civ_narration_start: patch.narration.start,
      }
    : {};
  const { narration, ...flatPatch } = patch;
  INTRO_VIDEO_TRANSLATIONS[locale] = {
    ...INTRO_VIDEO_TRANSLATIONS.de,
    ...flatPatch,
    ...narrationOverrides,
  };
};

copyIntroLocale("ko", {
  title: "중국어 배우기", accent: "실제로 쓰이는 방식으로", sub: "AI 기반 · 의사소통 중심 · 디지털 시대를 위해",
  narration: { welcome: "Chilan에 오신 것을 환영합니다. Chilan은 AI 기반 중국어 학습 플랫폼입니다. 이 과정은 듣기, 말하기, 타이핑이라는 실제 의사소통 능력을 길러 줍니다. 우리는 가장 기본 원리부터, 먼저 소리 체계부터 시작합니다.", sounds: "중국어의 모든 음절에는 성조가 있고, 성조가 바뀌면 의미도 완전히 달라질 수 있습니다. 네 가지 성조는 높고 평평한 소리, 올라가는 소리, 내려갔다 올라가는 소리, 내려가는 소리입니다. 성조를 익히는 것은 중국어 학습의 가장 중요한 기초입니다.", skills: "이 과정은 세 가지 핵심 능력을 훈련합니다. 듣기, 말하기, 그리고 병음 입력기로 타이핑하기입니다. 손글씨가 아니라, 디지털 일상에서 중국어가 실제로 쓰이는 방식에 집중합니다. 곧 읽고, 듣고, 말하고, 입력할 수 있게 됩니다.", ai: "여러분이 제출하는 모든 답변은 세 단계 시스템으로 평가됩니다. 즉시 패턴 매칭은 명확한 경우를 처리합니다. 의미 비교는 표현이 달라도 뜻이 같은 답변을 찾아냅니다. 그리고 대형 언어 모델은 정말 애매한 경우를 자세한 설명과 함께 판단합니다.", fsrs: "복습 일정은 FSRS, 즉 자유 간격 반복 스케줄러가 관리합니다. 잘 아는 항목은 덜 자주 돌아오고, 어려운 항목은 더 빨리 다시 나타납니다. 그래서 학습 시간을 가장 필요한 곳에 쓸 수 있습니다.", start: "이제 시작할 준비가 되었습니다. 먼저 기초 모듈부터 시작하세요. 병음은 소리 체계를 배우기 위한 것이고, 한자는 구조를 이해하기 위한 것입니다. 이 과정의 모든 수업은 이 기초 위에 쌓입니다." },
});

copyIntroLocale("es", { title: "Aprender chino", accent: "como se usa de verdad", sub: "Con IA · comunicación primero · para la era digital" });
copyIntroLocale("vi", { title: "Học tiếng Trung", accent: "như cách nó thật sự được dùng", sub: "AI hỗ trợ · ưu tiên giao tiếp · dành cho thời đại số" });
copyIntroLocale("pt", { title: "Aprender chinês", accent: "como ele é realmente usado", sub: "Com IA · foco em comunicação · feito para a era digital" });
copyIntroLocale("ar", { title: "تعلّم الصينية", accent: "كما تُستخدم فعلًا", sub: "مدعوم بالذكاء الاصطناعي · التواصل أولًا · للعصر الرقمي" });
copyIntroLocale("th", { title: "เรียนภาษาจีน", accent: "แบบที่ใช้จริง", sub: "ขับเคลื่อนด้วย AI · เน้นการสื่อสาร · สำหรับยุคดิจิทัล" });
copyIntroLocale("ru", { title: "Изучайте китайский", accent: "так, как он реально используется", sub: "С ИИ · сначала общение · для цифровой эпохи" });
copyIntroLocale("id", { title: "Belajar Mandarin", accent: "seperti benar-benar digunakan", sub: "Didukung AI · komunikasi dulu · untuk era digital" });
copyIntroLocale("ms", { title: "Belajar bahasa Cina", accent: "seperti yang benar-benar digunakan", sub: "Dikuasakan AI · komunikasi dahulu · untuk era digital" });
copyIntroLocale("it", { title: "Imparare il cinese", accent: "come viene usato davvero", sub: "Con IA · prima la comunicazione · per l'era digitale" });

const makeCompactIntro = (x) => buildIntroVideoTranslations({
  title: x.title,
  accent: x.accent,
  sub: x.sub,
  sounds: { label: x.foundation, h2Pre: x.startWith, h2Accent: x.soundsWord, sub: x.soundsSub, toneLabels: x.toneLabels, toneNames: x.toneNames, example: x.example },
  skills: { label: x.practiceLabel, h2Pre: x.skillsPre, h2Accent: x.skillsAccent, items: x.skills, noHw: x.noHw },
  ai: { label: x.aiLabel, h2Pre: x.aiPre, h2Accent: x.aiAccent, sub: x.aiSub, exampleLabel: x.exampleLabel, answers: x.answers, note: x.note, tiers: x.tiers },
  fsrs: { label: x.fsrsLabel, h2Pre: x.fsrsPre, h2Accent: x.fsrsAccent, sub: x.fsrsSub, chartLabel: x.chartLabel, legend: x.legend },
  start: { label: x.pathLabel, h2Pre: x.readyPre, h2Accent: x.readyAccent, sub: x.readySub, steps: x.steps, note: x.startNote },
  narration: x.narration,
});

const commonSteps = (labels) => [
  { label: "Pinyin", sub: labels[0] },
  { label: labels[1], sub: labels[2] },
  { label: labels[3], sub: labels[4] },
  { label: labels[5], sub: labels[6] },
];

Object.assign(INTRO_VIDEO_TRANSLATIONS, {
  fr: makeCompactIntro({
    title: "Apprendre le chinois", accent: "tel qu'on l'utilise vraiment", sub: "Propulsé par IA · communication d'abord · conçu pour l'ère numérique",
    foundation: "Fondation — étape 1", startWith: "On commence par les ", soundsWord: "sons", soundsSub: "Avant les mots et la grammaire : les 4 tons qui changent tout.",
    toneLabels: ["1er ton", "2e ton", "3e ton", "4e ton"], toneNames: ["haut plat", "montant", "descendant-montant", "descendant"], example: "妈 · 麻 · 马 · 骂 — même syllabe, quatre sens",
    practiceLabel: "Ce que vous pratiquez", skillsPre: "Trois compétences, ", skillsAccent: "un seul cours", skills: [{ label: "Écouter", sub: "Audio pour chaque mot et phrase. Les dictées entraînent l'oreille." }, { label: "Parler", sub: "Enregistrez votre voix. L'IA vérifie le sens, pas seulement la prononciation." }, { label: "Taper", sub: "IME pinyin, comme les locuteurs natifs écrivent au quotidien." }], noHw: "L'écriture manuscrite est une compétence séparée. Ce cours vise lecture, écoute, parole et saisie.",
    aiLabel: "Comment les réponses sont évaluées", aiPre: "L'IA évalue ", aiAccent: "chaque réponse", aiSub: "Correspondance instantanée → similarité sémantique → analyse LLM. Le sens compte plus que les mots exacts.", exampleLabel: "exemple", answers: ["« Que faites-vous d'habitude ? »", "« Que faites-vous normalement ? »"], note: "Les deux sont acceptées : même sens, mots différents.", tiers: [{ label: "Exact", desc: "Regex / motif" }, { label: "Sémantique", desc: "Score de similarité" }, { label: "Analyse IA", desc: "Jugement LLM + explication" }],
    fsrsLabel: "Science de la mémoire", fsrsPre: "Rien ne passe ", fsrsAccent: "à travers les mailles", fsrsSub: "FSRS calcule quand réviser chaque mot.", chartLabel: "exemple de planning pour un mot", legend: ["révisions fréquentes au début", "espacement croissant", "mémoire long terme"],
    pathLabel: "Votre parcours", readyPre: "Prêt à ", readyAccent: "commencer ?", readySub: "Commencez par les bases. Tout le reste se construit dessus.", steps: commonSteps(["sons et tons", "Caractères", "structure et radicaux", "Vocabulaire", "mots en contexte", "Phrases", "modèles grammaticaux"]), startNote: "Utilisez les modules de base dans la salle de classe.",
    narration: { welcome: "Bienvenue sur Chilan, une plateforme d'apprentissage du chinois propulsée par l'IA. Ce cours développe de vraies compétences de communication : écouter, parler et taper. Nous partons des principes de base, en commençant par le système phonétique.", sounds: "Chaque syllabe chinoise a un ton, et changer le ton change complètement le sens. Les quatre tons sont haut et plat, montant, descendant puis montant, et descendant. Maîtriser les tons est la base la plus importante du chinois.", skills: "Ce cours entraîne trois compétences essentielles : écouter, parler et taper avec une méthode de saisie pinyin. Nous nous concentrons sur l'utilisation réelle du chinois dans la vie numérique quotidienne, pas sur l'écriture manuscrite. Vous pourrez bientôt lire, écouter, parler et taper.", ai: "Chaque réponse que vous envoyez est évaluée par un système à trois niveaux. La correspondance instantanée gère les cas évidents. La comparaison sémantique repère les réponses qui ont le même sens avec des mots différents. Et un grand modèle de langage traite les vrais cas limites avec une explication détaillée.", fsrs: "Votre calendrier de révision est alimenté par FSRS, le Free Spaced Repetition Scheduler. Les éléments que vous connaissez bien reviennent moins souvent. Les éléments difficiles réapparaissent plus vite. Cela garantit que votre temps d'étude va exactement là où il est nécessaire.", start: "Vous êtes prêt à commencer. Démarrez avec les modules de base : le pinyin pour le système sonore, puis les caractères chinois pour la structure. Chaque leçon du cours s'appuie sur ces fondations." },
  }),
  es: makeCompactIntro({
    title: "Aprender chino", accent: "como se usa de verdad", sub: "Con IA · comunicación primero · para la era digital",
    foundation: "Base — paso 1", startWith: "Empezamos con los ", soundsWord: "sonidos", soundsSub: "Antes de palabras y gramática: los 4 tonos que lo cambian todo.", toneLabels: ["1.er tono", "2.º tono", "3.er tono", "4.º tono"], toneNames: ["alto plano", "ascendente", "baja y sube", "descendente"], example: "妈 · 麻 · 马 · 骂 — misma sílaba, cuatro significados",
    practiceLabel: "Lo que practicarás", skillsPre: "Tres habilidades, ", skillsAccent: "un curso", skills: [{ label: "Escuchar", sub: "Audio para cada palabra y frase. Los dictados entrenan el oído." }, { label: "Hablar", sub: "Graba tu voz. La IA revisa el significado, no solo la pronunciación." }, { label: "Teclear", sub: "IME pinyin, como se escribe a diario." }], noHw: "La escritura a mano es otra habilidad. Este curso se centra en leer, escuchar, hablar y teclear.",
    aiLabel: "Cómo se evalúan las respuestas", aiPre: "La IA evalúa ", aiAccent: "cada respuesta", aiSub: "Patrón instantáneo → similitud semántica → análisis LLM. Importa más el sentido que la forma exacta.", exampleLabel: "ejemplo", answers: ["«¿Qué haces normalmente?»", "«¿Qué sueles hacer?»"], note: "Ambas son válidas: mismo sentido, palabras distintas.", tiers: [{ label: "Exacta", desc: "Regex / patrón" }, { label: "Semántica", desc: "Similitud" }, { label: "Análisis IA", desc: "LLM + explicación" }],
    fsrsLabel: "Ciencia de la memoria", fsrsPre: "Nada queda ", fsrsAccent: "olvidado", fsrsSub: "FSRS calcula cuándo repasar cada palabra.", chartLabel: "ejemplo de repaso para una palabra", legend: ["repasos frecuentes al inicio", "intervalos mayores", "retención a largo plazo"],
    pathLabel: "Tu ruta", readyPre: "¿Listo para ", readyAccent: "empezar?", readySub: "Empieza por la base. Todo lo demás se construye encima.", steps: commonSteps(["sonidos y tonos", "Caracteres", "estructura y radicales", "Vocabulario", "palabras en contexto", "Frases", "patrones gramaticales"]), startNote: "Usa los módulos base en el aula para comenzar.",
    narration: { welcome: "Bienvenido a Chilan, una plataforma para aprender chino impulsada por IA. Este curso desarrolla habilidades reales de comunicación: escuchar, hablar y escribir con el teclado. Empezamos desde los principios básicos, comenzando por el sistema de sonidos.", sounds: "Cada sílaba china tiene un tono, y cambiar el tono puede cambiar completamente el significado. Los cuatro tonos son alto y plano, ascendente, descendente-ascendente y descendente. Dominar los tonos es la base más importante del chino.", skills: "Este curso entrena tres habilidades centrales: escuchar, hablar y escribir con un método de entrada pinyin. Nos centramos en cómo se usa realmente el chino en la vida digital diaria, no en la escritura a mano. Pronto podrás leer, escuchar, hablar y escribir.", ai: "Cada respuesta que envías se evalúa con un sistema de tres niveles. La coincidencia instantánea de patrones maneja los casos obvios. La comparación semántica detecta respuestas que significan lo mismo con palabras diferentes. Y un modelo de lenguaje grande resuelve los casos realmente ambiguos con una explicación detallada.", fsrs: "Tu calendario de repaso funciona con FSRS, el programador gratuito de repetición espaciada. Los elementos que conoces bien vuelven con menos frecuencia. Los difíciles reaparecen antes. Así dedicas tu tiempo de estudio exactamente donde hace falta.", start: "Ya estás listo para empezar. Comienza con los módulos de base: pinyin para el sistema de sonidos y luego caracteres chinos para la estructura. Cada lección del curso se construye sobre estos fundamentos." },
  }),
});

const emptyNarration = { welcome: "", sounds: "", skills: "", ai: "", fsrs: "", start: "" };
const makeVisualOnlyIntro = (x) => makeCompactIntro({
  ...x,
  foundation: x.foundation || x.base,
  startWith: x.startWith,
  soundsWord: x.soundsWord,
  soundsSub: x.soundsSub,
  toneLabels: x.toneLabels,
  toneNames: x.toneNames,
  example: x.example,
  practiceLabel: x.practiceLabel,
  skillsPre: x.skillsPre,
  skillsAccent: x.skillsAccent,
  skills: x.skills,
  noHw: x.noHw,
  aiLabel: x.aiLabel,
  aiPre: x.aiPre,
  aiAccent: x.aiAccent,
  aiSub: x.aiSub,
  exampleLabel: x.exampleLabel,
  answers: x.answers,
  note: x.note,
  tiers: x.tiers,
  fsrsLabel: x.fsrsLabel,
  fsrsPre: x.fsrsPre,
  fsrsAccent: x.fsrsAccent,
  fsrsSub: x.fsrsSub,
  chartLabel: x.chartLabel,
  legend: x.legend,
  pathLabel: x.pathLabel,
  readyPre: x.readyPre,
  readyAccent: x.readyAccent,
  readySub: x.readySub,
  steps: x.steps,
  startNote: x.startNote,
  narration: x.narration || emptyNarration,
});

Object.assign(INTRO_VIDEO_TRANSLATIONS, {
  ko: makeVisualOnlyIntro({
    title: "중국어 배우기", accent: "실제로 쓰이는 방식으로", sub: "AI 기반 · 의사소통 중심 · 디지털 시대를 위해",
    base: "기초 — 1단계", startWith: "먼저 ", soundsWord: "소리", soundsSub: "단어와 문법 전에, 의미를 바꾸는 4개 성조부터 익힙니다.", toneLabels: ["1성", "2성", "3성", "4성"], toneNames: ["높고 평평", "올라감", "내려갔다 올라감", "내려감"], example: "妈 · 麻 · 马 · 骂 — 같은 음절, 네 가지 뜻",
    practiceLabel: "연습할 것", skillsPre: "세 가지 능력, ", skillsAccent: "하나의 코스", skills: [{ label: "듣기", sub: "모든 단어와 문장에 오디오가 있습니다." }, { label: "말하기", sub: "목소리를 녹음하면 AI가 의미를 확인합니다." }, { label: "타이핑", sub: "병음 IME로 실제 입력 방식을 배웁니다." }], noHw: "손글씨는 별도 기술입니다. 이 코스는 읽기, 듣기, 말하기, 타이핑에 집중합니다.",
    aiLabel: "답변 평가 방식", aiPre: "AI가 ", aiAccent: "모든 답변을 평가", aiSub: "패턴 → 의미 유사도 → LLM 분석. 정확한 표현보다 의미가 중요합니다.", exampleLabel: "예시", answers: ["보통 무엇을 하나요?", "평소 무엇을 하나요?"], note: "둘 다 정답: 같은 의미입니다.", tiers: [{ label: "정확", desc: "패턴" }, { label: "의미", desc: "유사도" }, { label: "AI", desc: "판단+설명" }],
    fsrsLabel: "기억 과학", fsrsPre: "빠지는 내용은 ", fsrsAccent: "없습니다", fsrsSub: "FSRS가 각 단어의 복습 시점을 계산합니다.", chartLabel: "단어 복습 일정 예시", legend: ["초기 빈번한 복습", "간격 증가", "장기 기억"],
    pathLabel: "학습 경로", readyPre: "시작할 ", readyAccent: "준비가 됐나요?", readySub: "기초부터 시작하세요.", steps: commonSteps(["소리와 성조", "한자", "구조와 부수", "어휘", "문맥 속 단어", "문장", "문법 패턴"]), startNote: "교실의 기초 모듈에서 시작하세요.",
  }),
  vi: makeVisualOnlyIntro({
    title: "Học tiếng Trung", accent: "như cách nó thật sự được dùng", sub: "AI hỗ trợ · ưu tiên giao tiếp · dành cho thời đại số",
    base: "Nền tảng — bước 1", startWith: "Bắt đầu với ", soundsWord: "âm thanh", soundsSub: "Trước từ vựng và ngữ pháp: 4 thanh điệu thay đổi mọi thứ.", toneLabels: ["Thanh 1", "Thanh 2", "Thanh 3", "Thanh 4"], toneNames: ["cao ngang", "đi lên", "xuống rồi lên", "đi xuống"], example: "妈 · 麻 · 马 · 骂 — cùng âm tiết, bốn nghĩa",
    practiceLabel: "Bạn sẽ luyện gì", skillsPre: "Ba kỹ năng, ", skillsAccent: "một khóa học", skills: [{ label: "Nghe", sub: "Âm thanh cho từng từ và câu. Chính tả luyện tai nghe." }, { label: "Nói", sub: "Ghi âm giọng nói. AI kiểm tra ý nghĩa, không chỉ phát âm." }, { label: "Gõ", sub: "IME pinyin, cách người bản xứ gõ hằng ngày." }], noHw: "Viết tay là kỹ năng riêng. Khóa này tập trung vào đọc, nghe, nói và gõ.",
    aiLabel: "Cách chấm câu trả lời", aiPre: "AI đánh giá ", aiAccent: "mọi câu trả lời", aiSub: "Mẫu tức thì → ngữ nghĩa → phân tích LLM. Ý nghĩa quan trọng hơn câu chữ.", exampleLabel: "ví dụ", answers: ["Bạn thường làm gì?", "Bình thường bạn làm gì?"], note: "Cả hai đều đúng: cùng nghĩa, khác cách nói.", tiers: [{ label: "Khớp", desc: "mẫu / regex" }, { label: "Ngữ nghĩa", desc: "độ tương đồng" }, { label: "AI", desc: "LLM + giải thích" }],
    fsrsLabel: "Khoa học ghi nhớ", fsrsPre: "Không bỏ sót ", fsrsAccent: "nội dung nào", fsrsSub: "FSRS tính thời điểm ôn từng từ.", chartLabel: "ví dụ lịch ôn một từ", legend: ["ôn sớm thường xuyên", "khoảng cách tăng", "ghi nhớ lâu dài"],
    pathLabel: "Lộ trình", readyPre: "Sẵn sàng ", readyAccent: "bắt đầu?", readySub: "Bắt đầu từ nền tảng. Mọi thứ xây trên đó.", steps: commonSteps(["âm và thanh", "Chữ Hán", "cấu trúc và bộ thủ", "Từ vựng", "từ trong ngữ cảnh", "Câu", "mẫu ngữ pháp"]), startNote: "Bắt đầu bằng các mô-đun nền tảng trong lớp học.",
  }),
  pt: makeVisualOnlyIntro({
    title: "Aprender chinês", accent: "como ele é realmente usado", sub: "Com IA · foco em comunicação · feito para a era digital",
    base: "Base — passo 1", startWith: "Começamos pelos ", soundsWord: "sons", soundsSub: "Antes de palavras e gramática: os 4 tons que mudam tudo.", toneLabels: ["1º tom", "2º tom", "3º tom", "4º tom"], toneNames: ["alto plano", "ascendente", "desce e sobe", "descendente"], example: "妈 · 麻 · 马 · 骂 — mesma sílaba, quatro sentidos",
    practiceLabel: "O que você pratica", skillsPre: "Três habilidades, ", skillsAccent: "um curso", skills: [{ label: "Ouvir", sub: "Áudio para cada palavra e frase." }, { label: "Falar", sub: "Grave sua voz. A IA verifica o sentido." }, { label: "Digitar", sub: "IME pinyin, como se escreve no dia a dia." }], noHw: "Escrita à mão é uma habilidade separada. Aqui focamos em ler, ouvir, falar e digitar.",
    aiLabel: "Como as respostas são avaliadas", aiPre: "A IA avalia ", aiAccent: "cada resposta", aiSub: "Padrão → semântica → LLM. O sentido importa mais.", exampleLabel: "exemplo", answers: ["O que você costuma fazer?", "O que você normalmente faz?"], note: "Ambas aceitas: mesmo sentido.", tiers: [{ label: "Exato", desc: "regex / padrão" }, { label: "Semântico", desc: "similaridade" }, { label: "IA", desc: "LLM + explicação" }],
    fsrsLabel: "Ciência da memória", fsrsPre: "Nada fica ", fsrsAccent: "para trás", fsrsSub: "FSRS calcula quando revisar cada palavra.", chartLabel: "exemplo de revisão", legend: ["revisões iniciais", "intervalos maiores", "retenção longa"],
    pathLabel: "Seu caminho", readyPre: "Pronto para ", readyAccent: "começar?", readySub: "Comece pela base.", steps: commonSteps(["sons e tons", "Caracteres", "estrutura e radicais", "Vocabulário", "palavras em contexto", "Frases", "padrões gramaticais"]), startNote: "Use os módulos básicos na sala de aula.",
  }),
  ar: makeVisualOnlyIntro({
    title: "تعلّم الصينية", accent: "كما تُستخدم فعلًا", sub: "مدعوم بالذكاء الاصطناعي · التواصل أولًا · للعصر الرقمي",
    base: "الأساس — الخطوة 1", startWith: "نبدأ بـ ", soundsWord: "الأصوات", soundsSub: "قبل الكلمات والقواعد: أربع نغمات تغيّر المعنى.", toneLabels: ["النغمة 1", "النغمة 2", "النغمة 3", "النغمة 4"], toneNames: ["عالٍ مستوٍ", "صاعد", "هابط ثم صاعد", "هابط"], example: "妈 · 麻 · 马 · 骂 — مقطع واحد، أربعة معانٍ",
    practiceLabel: "ما ستتدرّب عليه", skillsPre: "ثلاث مهارات، ", skillsAccent: "دورة واحدة", skills: [{ label: "الاستماع", sub: "صوت لكل كلمة وجملة." }, { label: "التحدث", sub: "سجّل صوتك، والذكاء الاصطناعي يراجع المعنى." }, { label: "الكتابة", sub: "إدخال بينيين كما يكتب الناطقون يوميًا." }], noHw: "الكتابة اليدوية مهارة منفصلة. نركّز هنا على القراءة والاستماع والتحدث والكتابة.",
    aiLabel: "كيف تُقيّم الإجابات", aiPre: "الذكاء الاصطناعي يقيّم ", aiAccent: "كل إجابة", aiSub: "نمط فوري → معنى → تحليل LLM. المعنى أهم من اللفظ الحرفي.", exampleLabel: "مثال", answers: ["ماذا تفعل عادة؟", "ماذا تفعل غالبًا؟"], note: "كلاهما مقبول: نفس المعنى.", tiers: [{ label: "مطابقة", desc: "نمط / regex" }, { label: "دلالة", desc: "تشابه المعنى" }, { label: "AI", desc: "حكم وشرح" }],
    fsrsLabel: "علم الذاكرة", fsrsPre: "لا يضيع ", fsrsAccent: "أي شيء", fsrsSub: "FSRS يحسب موعد مراجعة كل كلمة.", chartLabel: "مثال جدول مراجعة", legend: ["مراجعات مبكرة", "تباعد أكبر", "حفظ طويل"],
    pathLabel: "مسارك", readyPre: "هل أنت جاهز ", readyAccent: "للبدء؟", readySub: "ابدأ من الأساس.", steps: commonSteps(["الأصوات والنغمات", "الحروف", "البنية والجذور", "المفردات", "كلمات في سياق", "الجمل", "أنماط نحوية"]), startNote: "ابدأ من وحدات الأساس في الصف.",
  }),
  th: makeVisualOnlyIntro({
    title: "เรียนภาษาจีน", accent: "แบบที่ใช้จริง", sub: "ขับเคลื่อนด้วย AI · เน้นการสื่อสาร · สำหรับยุคดิจิทัล",
    base: "พื้นฐาน — ขั้นที่ 1", startWith: "เริ่มจาก", soundsWord: "เสียง", soundsSub: "ก่อนคำศัพท์และไวยากรณ์: 4 วรรณยุกต์ที่เปลี่ยนความหมาย", toneLabels: ["เสียง 1", "เสียง 2", "เสียง 3", "เสียง 4"], toneNames: ["สูงเรียบ", "ขึ้น", "ตกแล้วขึ้น", "ตก"], example: "妈 · 麻 · 马 · 骂 — พยางค์เดียว สี่ความหมาย",
    practiceLabel: "สิ่งที่จะฝึก", skillsPre: "สามทักษะ ", skillsAccent: "ในคอร์สเดียว", skills: [{ label: "ฟัง", sub: "เสียงทุกคำและประโยค" }, { label: "พูด", sub: "อัดเสียง แล้ว AI ตรวจความหมาย" }, { label: "พิมพ์", sub: "IME พินอินแบบที่ใช้จริงทุกวัน" }], noHw: "การเขียนมือเป็นอีกทักษะหนึ่ง คอร์สนี้เน้นอ่าน ฟัง พูด และพิมพ์",
    aiLabel: "วิธีตรวจคำตอบ", aiPre: "AI ตรวจ", aiAccent: "ทุกคำตอบ", aiSub: "รูปแบบ → ความหมาย → LLM ความหมายสำคัญกว่าคำตรงตัว", exampleLabel: "ตัวอย่าง", answers: ["คุณมักทำอะไร?", "ปกติคุณทำอะไร?"], note: "ยอมรับทั้งคู่: ความหมายเดียวกัน", tiers: [{ label: "ตรง", desc: "รูปแบบ" }, { label: "ความหมาย", desc: "ความคล้าย" }, { label: "AI", desc: "ตัดสิน+อธิบาย" }],
    fsrsLabel: "วิทยาศาสตร์ความจำ", fsrsPre: "ไม่มีสิ่งใด", fsrsAccent: "หล่นหาย", fsrsSub: "FSRS คำนวณเวลาทบทวนแต่ละคำ", chartLabel: "ตัวอย่างตารางทบทวน", legend: ["ทบทวนถี่ช่วงแรก", "ระยะห่างเพิ่ม", "จำระยะยาว"],
    pathLabel: "เส้นทางของคุณ", readyPre: "พร้อม", readyAccent: "เริ่มไหม?", readySub: "เริ่มจากพื้นฐาน", steps: commonSteps(["เสียงและวรรณยุกต์", "ตัวอักษร", "โครงสร้าง", "คำศัพท์", "คำในบริบท", "ประโยค", "รูปแบบไวยากรณ์"]), startNote: "เริ่มจากโมดูลพื้นฐานในห้องเรียน",
  }),
  ru: makeVisualOnlyIntro({
    title: "Изучайте китайский", accent: "так, как он реально используется", sub: "С ИИ · сначала общение · для цифровой эпохи",
    base: "Основа — шаг 1", startWith: "Начинаем со ", soundsWord: "звуков", soundsSub: "До слов и грамматики: 4 тона, меняющие смысл.", toneLabels: ["1-й тон", "2-й тон", "3-й тон", "4-й тон"], toneNames: ["высокий ровный", "восходящий", "нисходяще-восходящий", "нисходящий"], example: "妈 · 麻 · 马 · 骂 — один слог, четыре значения",
    practiceLabel: "Что вы тренируете", skillsPre: "Три навыка, ", skillsAccent: "один курс", skills: [{ label: "Слушать", sub: "Аудио для каждого слова и предложения." }, { label: "Говорить", sub: "Запишите голос, ИИ проверит смысл." }, { label: "Печатать", sub: "Pinyin IME, как пишут каждый день." }], noHw: "Письмо от руки — отдельный навык. Здесь мы учимся читать, слушать, говорить и печатать.",
    aiLabel: "Как оцениваются ответы", aiPre: "ИИ оценивает ", aiAccent: "каждый ответ", aiSub: "Шаблон → смысл → LLM. Смысл важнее точной формулировки.", exampleLabel: "пример", answers: ["Что вы обычно делаете?", "Чем вы обычно занимаетесь?"], note: "Оба ответа принимаются.", tiers: [{ label: "Точно", desc: "шаблон" }, { label: "Смысл", desc: "сходство" }, { label: "ИИ", desc: "решение + объяснение" }],
    fsrsLabel: "Наука памяти", fsrsPre: "Ничего не ", fsrsAccent: "теряется", fsrsSub: "FSRS рассчитывает, когда повторять каждое слово.", chartLabel: "пример графика повторения", legend: ["часто в начале", "интервалы растут", "долгая память"],
    pathLabel: "Ваш путь", readyPre: "Готовы ", readyAccent: "начать?", readySub: "Начните с основы.", steps: commonSteps(["звуки и тоны", "Иероглифы", "структура и радикалы", "Лексика", "слова в контексте", "Предложения", "грамматические модели"]), startNote: "Начните с базовых модулей в классе.",
  }),
  id: makeVisualOnlyIntro({
    title: "Belajar Mandarin", accent: "seperti benar-benar digunakan", sub: "Didukung AI · komunikasi dulu · untuk era digital",
    base: "Dasar — langkah 1", startWith: "Mulai dari ", soundsWord: "bunyi", soundsSub: "Sebelum kata dan tata bahasa: 4 nada yang mengubah makna.", toneLabels: ["Nada 1", "Nada 2", "Nada 3", "Nada 4"], toneNames: ["tinggi datar", "naik", "turun-naik", "turun"], example: "妈 · 麻 · 马 · 骂 — suku kata sama, empat makna",
    practiceLabel: "Yang dilatih", skillsPre: "Tiga keterampilan, ", skillsAccent: "satu kursus", skills: [{ label: "Mendengar", sub: "Audio untuk setiap kata dan kalimat." }, { label: "Berbicara", sub: "Rekam suara, AI memeriksa makna." }, { label: "Mengetik", sub: "IME pinyin untuk penggunaan sehari-hari." }], noHw: "Tulisan tangan adalah keterampilan terpisah. Fokus kursus ini membaca, mendengar, berbicara, dan mengetik.",
    aiLabel: "Cara jawaban dinilai", aiPre: "AI menilai ", aiAccent: "setiap jawaban", aiSub: "Pola → semantik → LLM. Makna lebih penting.", exampleLabel: "contoh", answers: ["Biasanya kamu melakukan apa?", "Kamu biasanya apa?"], note: "Keduanya diterima.", tiers: [{ label: "Cocok", desc: "pola" }, { label: "Semantik", desc: "kemiripan" }, { label: "AI", desc: "penilaian + penjelasan" }],
    fsrsLabel: "Ilmu memori", fsrsPre: "Tidak ada yang ", fsrsAccent: "terlewat", fsrsSub: "FSRS menghitung waktu ulasan tiap kata.", chartLabel: "contoh jadwal ulasan", legend: ["sering di awal", "jarak bertambah", "ingatan jangka panjang"],
    pathLabel: "Jalurmu", readyPre: "Siap ", readyAccent: "mulai?", readySub: "Mulai dari dasar.", steps: commonSteps(["bunyi dan nada", "Karakter", "struktur dan radikal", "Kosakata", "kata dalam konteks", "Kalimat", "pola tata bahasa"]), startNote: "Mulai dari modul dasar di kelas.",
  }),
  ms: makeVisualOnlyIntro({
    title: "Belajar bahasa Cina", accent: "seperti yang benar-benar digunakan", sub: "Dikuasakan AI · komunikasi dahulu · untuk era digital",
    base: "Asas — langkah 1", startWith: "Bermula dengan ", soundsWord: "bunyi", soundsSub: "Sebelum perkataan dan tatabahasa: 4 nada yang mengubah makna.", toneLabels: ["Nada 1", "Nada 2", "Nada 3", "Nada 4"], toneNames: ["tinggi rata", "menaik", "turun-naik", "menurun"], example: "妈 · 麻 · 马 · 骂 — suku kata sama, empat makna",
    practiceLabel: "Apa yang dilatih", skillsPre: "Tiga kemahiran, ", skillsAccent: "satu kursus", skills: [{ label: "Mendengar", sub: "Audio untuk setiap perkataan dan ayat." }, { label: "Bertutur", sub: "Rakam suara, AI menyemak makna." }, { label: "Menaip", sub: "IME pinyin untuk penggunaan harian." }], noHw: "Tulisan tangan ialah kemahiran berasingan. Kursus ini fokus pada membaca, mendengar, bertutur dan menaip.",
    aiLabel: "Cara jawapan dinilai", aiPre: "AI menilai ", aiAccent: "setiap jawapan", aiSub: "Pola → semantik → LLM. Makna lebih penting.", exampleLabel: "contoh", answers: ["Biasanya anda buat apa?", "Anda selalu buat apa?"], note: "Kedua-duanya diterima.", tiers: [{ label: "Padan", desc: "pola" }, { label: "Semantik", desc: "persamaan" }, { label: "AI", desc: "keputusan + penjelasan" }],
    fsrsLabel: "Sains memori", fsrsPre: "Tiada yang ", fsrsAccent: "terlepas", fsrsSub: "FSRS mengira masa ulang kaji setiap perkataan.", chartLabel: "contoh jadual ulang kaji", legend: ["kerap pada awal", "jarak bertambah", "ingatan jangka panjang"],
    pathLabel: "Laluan anda", readyPre: "Sedia untuk ", readyAccent: "bermula?", readySub: "Mulakan dengan asas.", steps: commonSteps(["bunyi dan nada", "Aksara", "struktur dan radikal", "Kosa kata", "perkataan dalam konteks", "Ayat", "pola tatabahasa"]), startNote: "Mulakan dengan modul asas di kelas.",
  }),
  it: makeVisualOnlyIntro({
    title: "Imparare il cinese", accent: "come viene usato davvero", sub: "Con IA · prima la comunicazione · per l'era digitale",
    base: "Fondamenti — passo 1", startWith: "Iniziamo dai ", soundsWord: "suoni", soundsSub: "Prima di parole e grammatica: i 4 toni che cambiano tutto.", toneLabels: ["1º tono", "2º tono", "3º tono", "4º tono"], toneNames: ["alto piano", "ascendente", "discendente-ascendente", "discendente"], example: "妈 · 麻 · 马 · 骂 — stessa sillaba, quattro significati",
    practiceLabel: "Cosa praticherai", skillsPre: "Tre abilità, ", skillsAccent: "un corso", skills: [{ label: "Ascoltare", sub: "Audio per ogni parola e frase." }, { label: "Parlare", sub: "Registra la voce, l'IA verifica il senso." }, { label: "Digitare", sub: "IME pinyin per l'uso quotidiano." }], noHw: "La scrittura a mano è separata. Qui ci concentriamo su lettura, ascolto, parlato e digitazione.",
    aiLabel: "Come vengono valutate le risposte", aiPre: "L'IA valuta ", aiAccent: "ogni risposta", aiSub: "Pattern → semantica → LLM. Il significato conta di più.", exampleLabel: "esempio", answers: ["Cosa fai di solito?", "Normalmente cosa fai?"], note: "Entrambe accettate.", tiers: [{ label: "Esatto", desc: "pattern" }, { label: "Semantico", desc: "similarità" }, { label: "IA", desc: "giudizio + spiegazione" }],
    fsrsLabel: "Scienza della memoria", fsrsPre: "Nulla viene ", fsrsAccent: "perso", fsrsSub: "FSRS calcola quando ripassare ogni parola.", chartLabel: "esempio di programma", legend: ["ripassi frequenti all'inizio", "intervalli crescenti", "memoria a lungo termine"],
    pathLabel: "Il tuo percorso", readyPre: "Pronto a ", readyAccent: "iniziare?", readySub: "Comincia dalle basi.", steps: commonSteps(["suoni e toni", "Caratteri", "struttura e radicali", "Vocabolario", "parole nel contesto", "Frasi", "schemi grammaticali"]), startNote: "Inizia dai moduli base in classe.",
  }),
});
