import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import { COURSE_INTRO_PAGE_TRANSLATIONS } from './courseIntroPageTranslations';
import { INTRO_VIDEO_TRANSLATIONS } from './introVideoTranslations';

const HANZI_RADICAL_BASE = [
  { no: 1, radical: "人/亻", pinyin: "rén", examples: "今 · 他" },
  { no: 2, radical: "刀/刂", pinyin: "dāo", examples: "分 · 到" },
  { no: 3, radical: "力", pinyin: "lì", examples: "加 · 助" },
  { no: 4, radical: "又", pinyin: "yòu", examples: "友 · 取" },
  { no: 5, radical: "口", pinyin: "kǒu", examples: "叫 · 可" },
  { no: 6, radical: "囗", pinyin: "wéi", examples: "回 · 因" },
  { no: 7, radical: "土", pinyin: "tǔ", examples: "在 · 坐" },
  { no: 8, radical: "夕", pinyin: "xī", examples: "外 · 多" },
  { no: 9, radical: "大", pinyin: "dà", examples: "天 · 太" },
  { no: 10, radical: "女", pinyin: "nǚ", examples: "婆 · 好" },
  { no: 11, radical: "子", pinyin: "zǐ", examples: "字 · 孩" },
  { no: 12, radical: "寸", pinyin: "cùn", examples: "寺 · 封" },
  { no: 13, radical: "小", pinyin: "xiǎo", examples: "少 · 尖" },
  { no: 14, radical: "工", pinyin: "gōng", examples: "左 · 差" },
  { no: 15, radical: "幺", pinyin: "yāo", examples: "幻 · 幼" },
  { no: 16, radical: "弓", pinyin: "gōng", examples: "引 · 弟" },
  { no: 17, radical: "心/忄", pinyin: "xīn", examples: "想 · 忙" },
  { no: 18, radical: "戈", pinyin: "gē", examples: "我 · 或" },
  { no: 19, radical: "手/扌", pinyin: "shǒu", examples: "拿 · 打" },
  { no: 20, radical: "日", pinyin: "rì", examples: "早 · 明" },
  { no: 21, radical: "月", pinyin: "yuè", examples: "期 · 朗" },
  { no: 22, radical: "木", pinyin: "mù", examples: "李 · 杯" },
  { no: 23, radical: "水/氵", pinyin: "shuǐ", examples: "河 · 洗" },
  { no: 24, radical: "火/灬", pinyin: "huǒ", examples: "烧 · 热" },
  { no: 25, radical: "田", pinyin: "tián", examples: "男 · 留" },
  { no: 26, radical: "目", pinyin: "mù", examples: "看 · 睡" },
  { no: 27, radical: "示/礻", pinyin: "shì", examples: "票 · 社" },
  { no: 28, radical: "糸/纟", pinyin: "mì", examples: "素 · 红" },
  { no: 29, radical: "耳", pinyin: "ěr", examples: "聋 · 聊" },
  { no: 30, radical: "衣/衤", pinyin: "yī", examples: "袋 · 衫" },
  { no: 31, radical: "言/讠", pinyin: "yán", examples: "誓 · 话" },
  { no: 32, radical: "贝", pinyin: "bèi", examples: "贵 · 财" },
  { no: 33, radical: "走", pinyin: "zǒu", examples: "趣 · 起" },
  { no: 34, radical: "足", pinyin: "zú", examples: "跳 · 跑" },
  { no: 35, radical: "金/钅", pinyin: "jīn", examples: "鉴 · 银" },
  { no: 36, radical: "门", pinyin: "mén", examples: "间 · 闷" },
  { no: 37, radical: "隹", pinyin: "zhuī", examples: "难 · 集" },
  { no: 38, radical: "雨", pinyin: "yǔ", examples: "雪 · 雷" },
  { no: 39, radical: "食/饣", pinyin: "shí", examples: "餐 · 饭" },
  { no: 40, radical: "马", pinyin: "mǎ", examples: "骑 · 驾" }
];

const HANZI_RADICAL_COPY = {
  zh: [
    ["人", "人、身份、动作主体"], ["刀", "切割或工具"], ["力量", "动作、力量"], ["又", "手、动作或重复"], ["口", "说话、入口、口形"], ["围", "包围起来的外框"], ["土", "土地、位置"], ["夕", "夜晚、时间"], ["大", "大小、人体姿态"], ["女", "人物或身份"], ["孩子", "孩子或下部件"], ["寸", "手寸、尺度"], ["小", "小或细小形态"], ["工", "工作、工具、形状"], ["细小", "细小、丝线相关"], ["弓", "弓形或拉开"], ["心", "心理、情感"], ["戈", "古兵器或动作"], ["手", "手部动作"], ["日", "太阳、时间、明亮"], ["月", "月亮、身体也常见"], ["木", "树木、木制物"], ["水", "水、液体"], ["火", "火、热"], ["田", "田地、区域"], ["目", "眼睛、观看"], ["示", "祭祀、礼仪、显示"], ["丝", "丝线、纤维"], ["耳", "耳朵、听觉"], ["衣", "衣服、布料"], ["言语", "说话、语言"], ["贝", "钱财、价值"], ["走", "行走、移动"], ["足", "脚、动作"], ["金", "金属、钱"], ["门", "门、空间入口"], ["隹", "鸟类相关"], ["雨", "雨、天气"], ["食", "吃、食物"], ["马", "马或骑乘"]
  ],
  en: [
    ["person", "people, roles, actions"], ["knife", "cutting or tools"], ["power", "action or strength"], ["right hand / again", "hand action or repetition"], ["mouth", "speech, opening, mouth shape"], ["enclosure", "outer box around a character"], ["earth", "place or ground"], ["sunset", "evening or time"], ["big", "size or body posture"], ["woman", "people or identity"], ["child", "child or lower component"], ["inch", "measure or hand span"], ["small", "small or fine forms"], ["work", "work, tools, shape"], ["tiny", "smallness or silk-like forms"], ["bow", "bow shape or pulling"], ["heart", "mind, feeling"], ["dagger-axe", "old weapon or action"], ["hand", "hand actions"], ["sun", "time or brightness"], ["moon / flesh", "moon, time, or body"], ["wood", "trees or wooden things"], ["water", "water or liquid"], ["fire", "fire or heat"], ["field", "field or area"], ["eye", "eyes or seeing"], ["show", "ritual, sign, display"], ["fine silk", "thread or fiber"], ["ear", "ear or hearing"], ["clothing", "clothes or fabric"], ["speech", "speech and language"], ["cowrie shell", "money or value"], ["walk", "walking or movement"], ["foot", "feet and movement"], ["gold", "metal or money"], ["door", "door or entrance"], ["short-tailed bird", "bird-related forms"], ["rain", "rain or weather"], ["food", "eating or food"], ["horse", "horse or riding"]
  ],
  de: [
    ["Person", "Menschen, Rollen, Handlungen"], ["Messer", "Schneiden oder Werkzeuge"], ["Kraft", "Handlung oder Stärke"], ["rechte Hand / wieder", "Handlung oder Wiederholung"], ["Mund", "Sprechen, Öffnung, Mundform"], ["Einfassung", "äußerer Rahmen"], ["Erde", "Ort oder Boden"], ["Abend", "Abend oder Zeit"], ["groß", "Größe oder Körperhaltung"], ["Frau", "Personen oder Identität"], ["Kind", "Kind oder unterer Bestandteil"], ["Zoll", "Maß oder Handspanne"], ["klein", "kleine oder feine Formen"], ["Arbeit", "Arbeit, Werkzeug, Form"], ["winzig", "klein oder fadenartig"], ["Bogen", "Bogenform oder Ziehen"], ["Herz", "Geist, Gefühl"], ["Hellebarde", "alte Waffe oder Handlung"], ["Hand", "Handlungen mit der Hand"], ["Sonne", "Zeit oder Helligkeit"], ["Mond / Fleisch", "Mond, Zeit oder Körper"], ["Holz", "Bäume oder Holzobjekte"], ["Wasser", "Wasser oder Flüssigkeit"], ["Feuer", "Feuer oder Hitze"], ["Feld", "Feld oder Bereich"], ["Auge", "Augen oder Sehen"], ["zeigen", "Ritual, Zeichen, Anzeige"], ["feine Seide", "Faden oder Faser"], ["Ohr", "Ohr oder Hören"], ["Kleidung", "Kleidung oder Stoff"], ["Sprache", "Sprechen und Sprache"], ["Muschel", "Geld oder Wert"], ["gehen", "Gehen oder Bewegung"], ["Fuß", "Fuß und Bewegung"], ["Gold", "Metall oder Geld"], ["Tür", "Tür oder Eingang"], ["Kurzschwanzvogel", "vogelbezogene Formen"], ["Regen", "Regen oder Wetter"], ["Essen", "Essen oder Nahrung"], ["Pferd", "Pferd oder Reiten"]
  ],
  fr: [
    ["personne", "personnes, rôles, actions"], ["couteau", "couper ou outils"], ["force", "action ou puissance"], ["main droite / encore", "action de la main ou répétition"], ["bouche", "parole, ouverture, forme de bouche"], ["enceinte", "cadre extérieur"], ["terre", "lieu ou sol"], ["soir", "soir ou temps"], ["grand", "taille ou posture"], ["femme", "personnes ou identité"], ["enfant", "enfant ou composant bas"], ["pouce", "mesure ou empan"], ["petit", "formes petites ou fines"], ["travail", "travail, outil, forme"], ["minuscule", "petit ou filiforme"], ["arc", "forme d'arc ou traction"], ["coeur", "esprit, émotion"], ["hallebarde", "ancienne arme ou action"], ["main", "actions de la main"], ["soleil", "temps ou lumière"], ["lune / chair", "lune, temps ou corps"], ["bois", "arbres ou objets en bois"], ["eau", "eau ou liquide"], ["feu", "feu ou chaleur"], ["champ", "champ ou zone"], ["oeil", "yeux ou vision"], ["montrer", "rite, signe, affichage"], ["soie fine", "fil ou fibre"], ["oreille", "oreille ou audition"], ["vêtement", "vêtements ou tissu"], ["parole", "parole et langage"], ["coquillage", "argent ou valeur"], ["marcher", "marche ou mouvement"], ["pied", "pied et mouvement"], ["or", "métal ou argent"], ["porte", "porte ou entrée"], ["oiseau à queue courte", "formes liées aux oiseaux"], ["pluie", "pluie ou météo"], ["nourriture", "manger ou aliment"], ["cheval", "cheval ou équitation"]
  ]
};

function buildHanziRadicals(locale) {
  const copy = HANZI_RADICAL_COPY[locale] || HANZI_RADICAL_COPY.en;
  return HANZI_RADICAL_BASE.map((item, index) => ({
    ...item,
    meaning: copy[index][0],
    hint: copy[index][1]
  }));
}

const HANZI_FORMATION_BLUEPRINT = [
  { key: "pictograph", pinyin: "xiàngxíng", glyph: "山", exampleKeys: ["person", "mountain", "sun", "moon", "tree"] },
  { key: "ideogram", pinyin: "zhǐshì", glyph: "上", exampleKeys: ["above", "below"] },
  { key: "compound", pinyin: "huìyì", glyph: "明", exampleKeys: ["bright", "rest"] },
  { key: "semanticPhonetic", pinyin: "xíngshēng", glyph: "河", exampleKeys: ["riverJiang", "riverHe", "meal", "aunt"] },
  { key: "mutual", pinyin: "zhuǎnzhù", glyph: "老", exampleKeys: ["old", "test"] },
  { key: "loan", pinyin: "jiǎjiè", glyph: "来", exampleKeys: ["come", "me"] }
];

const HANZI_FORMATION_EXAMPLES = {
  person: { char: "人", pinyin: "rén" },
  mountain: { char: "山", pinyin: "shān" },
  sun: { char: "日", pinyin: "rì" },
  moon: { char: "月", pinyin: "yuè" },
  tree: { char: "木", pinyin: "mù" },
  above: { char: "上", pinyin: "shàng" },
  below: { char: "下", pinyin: "xià" },
  bright: { char: "明", pinyin: "míng" },
  rest: { char: "休", pinyin: "xiū" },
  riverJiang: { char: "江", pinyin: "jiāng" },
  riverHe: { char: "河", pinyin: "hé" },
  meal: { char: "饭", pinyin: "fàn" },
  aunt: { char: "姑", pinyin: "gū" },
  old: { char: "老", pinyin: "lǎo" },
  test: { char: "考", pinyin: "kǎo" },
  come: { char: "来", pinyin: "lái" },
  me: { char: "我", pinyin: "wǒ" }
};

function buildHanziFormationTypes(copy) {
  return HANZI_FORMATION_BLUEPRINT.map((item) => ({
    ...item,
    title: copy.formationTypes[item.key].title,
    description: copy.formationTypes[item.key].description,
    glyphMeaning: copy.formationTypes[item.key].glyphMeaning,
    examples: item.exampleKeys.map((key) => ({
      ...HANZI_FORMATION_EXAMPLES[key],
      meaning: copy.exampleMeanings[key],
    })),
    breakdowns: item.key === "compound" ? [
      {
        parts: [
          { ...HANZI_FORMATION_EXAMPLES.sun, meaning: copy.exampleMeanings.sun },
          { ...HANZI_FORMATION_EXAMPLES.moon, meaning: copy.exampleMeanings.moon },
        ],
        result: { ...HANZI_FORMATION_EXAMPLES.bright, meaning: copy.exampleMeanings.bright },
      },
      {
        parts: [
          { ...HANZI_FORMATION_EXAMPLES.person, meaning: copy.exampleMeanings.person },
          { ...HANZI_FORMATION_EXAMPLES.tree, meaning: copy.exampleMeanings.tree },
        ],
        result: { ...HANZI_FORMATION_EXAMPLES.rest, meaning: copy.exampleMeanings.rest },
      },
    ] : [],
  }));
}

const HANZI_INTRO_TRANSLATIONS = {
  zh: {
    badge: "基础 · 汉字",
    title: "汉字如何组成",
    subtitle: "这页把教材 Basic 13-17 页整理成一个更适合外语学习者浏览的汉字地图：先学会看结构，再认识部首、笔画和笔顺。",
    readingOnly: "先建立识别模型 - 不要求一次背完",
    studyModel: {
      eyebrow: "How to look",
      title: "遇到新字，先问三个问题",
      body: "外语学习者最容易被笔画数量吓到。这里把观察顺序固定下来：先看整体，再看部件，最后再处理读音。",
      steps: [
        { title: "看外形", body: "这个字是左右、上下、包围，还是独体？先把大块切出来。" },
        { title: "找部首", body: "哪个部件最像意义提示？水、口、手、言这类部首特别常见。" },
        { title: "听读音", body: "很多字有声音线索，但现代读音不一定完全相同；最后交给拼音确认。" }
      ]
    },
    formation: {
      eyebrow: "Writing system",
      title: "先理解：汉字不是一张张小画",
      body: "汉字以方块为单位。一个字通常对应一个音节，也承载一个意义单位。少数汉字来自图像，更多汉字则由表示意义和提示读音的部件组合而成。",
      note: "关键模型：看到新字时，先找它的部件、部首和空间结构，再把读音交给拼音和输入法。",
      priority: {
        title: "最值得优先理解：形声字",
        body: "教材特别提醒：只有少量汉字真正来自图画，绝大多数常用字更像“意义部件 + 声音线索”。所以不要把六类平均背诵，先学会看形声结构更有用。",
        examples: [
          { char: "河", parts: ["氵 = 水/液体", "可 = 历史读音线索"], note: "意义和水有关，读音靠拼音确认 hé" },
          { char: "饭", parts: ["饣 = 食物", "反 = 历史读音线索"], note: "意义和吃有关，读音是 fàn" },
          { char: "妈", parts: ["女 = 人物/身份", "马 = 历史读音线索"], note: "声音线索接近，但声调会变" }
        ]
      },
      types: [
        { title: "象形", pinyin: "xiàngxíng", glyph: "山", glyphMeaning: "山", description: "从具体物体的轮廓演变而来，是最直观的一类。", examples: [{ char: "人", pinyin: "rén", meaning: "人" }, { char: "山", pinyin: "shān", meaning: "山" }, { char: "日", pinyin: "rì", meaning: "太阳/日" }, { char: "月", pinyin: "yuè", meaning: "月亮/月" }, { char: "木", pinyin: "mù", meaning: "树木" }] },
        { title: "指事", pinyin: "zhǐshì", glyph: "上", glyphMeaning: "上方", description: "用简单符号标出抽象关系或位置。", examples: [{ char: "上", pinyin: "shàng", meaning: "上方" }, { char: "下", pinyin: "xià", meaning: "下方" }] },
        { title: "会意", pinyin: "huìyì", glyph: "明", glyphMeaning: "明亮", description: "把两个意义部件放在一起，让合成意义显现出来。", examples: [{ char: "明", pinyin: "míng", meaning: "明亮" }, { char: "休", pinyin: "xiū", meaning: "休息" }], breakdowns: [{ parts: [{ char: "日", pinyin: "rì", meaning: "太阳/日" }, { char: "月", pinyin: "yuè", meaning: "月亮/月" }], result: { char: "明", pinyin: "míng", meaning: "明亮" } }, { parts: [{ char: "人", pinyin: "rén", meaning: "人" }, { char: "木", pinyin: "mù", meaning: "树木" }], result: { char: "休", pinyin: "xiū", meaning: "休息" } }] },
        { title: "形声", pinyin: "xíngshēng", glyph: "河", glyphMeaning: "河流", description: "一个部件提示意义类别，另一个部件提示读音来源；现代汉字中非常常见。", examples: [{ char: "江", pinyin: "jiāng", meaning: "江河" }, { char: "河", pinyin: "hé", meaning: "河流" }, { char: "饭", pinyin: "fàn", meaning: "饭/餐" }, { char: "姑", pinyin: "gū", meaning: "姑母" }] },
        { title: "转注", pinyin: "zhuǎnzhù", glyph: "老", glyphMeaning: "年老", description: "意义相近的字彼此解释或延伸，学习时只需要知道它存在。", examples: [{ char: "老", pinyin: "lǎo", meaning: "年老" }, { char: "考", pinyin: "kǎo", meaning: "考试/考察" }] },
        { title: "假借", pinyin: "jiǎjiè", glyph: "来", glyphMeaning: "来", description: "借用已有字来记录相同或相近的读音。", examples: [{ char: "来", pinyin: "lái", meaning: "来" }, { char: "我", pinyin: "wǒ", meaning: "我" }] }
      ]
    },
    radicals: {
      eyebrow: "Radicals",
      title: "部首是查字和记字的抓手",
      body: "传统字典按部首组织汉字。教材列出四十个入门部首；这里完整保留，但改成可快速扫读的小卡片。",
      tip: "先认“意义范围”，不要把每个英文/中文释义当作唯一答案。部首常常只是方向提示。",
      items: buildHanziRadicals('zh')
    },
    structures: {
      eyebrow: "Character structures",
      title: "汉字像积木：先看空间结构",
      body: "教材把常见结构整理成九类。结构不是为了背术语，而是帮助你快速看出一个字由几块组成。",
      items: [
        { type: "独体", label: "Unitary", sketch: "unitary", examples: "上 · 水 · 人 · 女 · 山" },
        { type: "左右", label: "Left-right", sketch: "leftRight", examples: "忙 · 唱 · 便 · 汉 · 都" },
        { type: "上下", label: "Top-bottom", sketch: "topBottom", examples: "李 · 字 · 念 · 想 · 笔" },
        { type: "半包围", label: "Semi-enclosing", sketch: "semiEnclosing", examples: "同 · 周 · 问 · 间 · 风" },
        { type: "全包围", label: "Enclosing", sketch: "enclosing", examples: "回 · 因 · 国 · 图 · 圆" },
        { type: "左中右", label: "Horizontal trisection", sketch: "horizontalTrisection", examples: "班 · 街 · 辩 · 粥" },
        { type: "上中下", label: "Vertical trisection", sketch: "verticalTrisection", examples: "鼻 · 幕 · 曼" },
        { type: "左下包围", label: "Left-bottom enclosing", sketch: "leftBottomEnclosing", examples: "这 · 起 · 过 · 道 · 造" },
        { type: "左上包围", label: "Left-top enclosing", sketch: "leftTopEnclosing", examples: "床 · 麻 · 病 · 历 · 屋" }
      ]
    },
    strokes: {
      eyebrow: "Basic strokes",
      title: "基本笔画：写字的最小动作",
      body: "笔画从上到下、从左到右居多。这里按教材列出常见基本笔画，作为识字和查字的准备。",
      note: "例外需要特别记：提通常向右上，撇通常向左下。",
      items: [
        { mark: "丶", name: "点 diǎn", description: "点", examples: "小 · 六" },
        { mark: "一", name: "横 héng", description: "从左到右", examples: "一 · 六" },
        { mark: "丨", name: "竖 shù", description: "从上到下", examples: "十 · 中" },
        { mark: "丿", name: "撇 piě", description: "向左下", examples: "人 · 大" },
        { mark: "㇏", name: "捺 nà", description: "向右下", examples: "八 · 人" },
        { mark: "㇀", name: "提 tí", description: "向右上", examples: "我 · 江" },
        { mark: "乛", name: "横钩 hénggōu", description: "横后带钩", examples: "你 · 字" },
        { mark: "亅", name: "竖钩 shùgōu", description: "竖后带钩", examples: "小 · 你" },
        { mark: "㇂", name: "斜钩 xiégōu", description: "斜向带钩", examples: "我 · 戈" },
        { mark: "𠃍", name: "横折 héngzhé", description: "横后转折", examples: "五 · 口" },
        { mark: "㇄", name: "竖折 shùzhé", description: "竖后转折", examples: "七 · 亡" }
      ]
    },
    strokeOrder: {
      eyebrow: "Stroke order",
      title: "笔顺规则：让字形稳定下来",
      body: "这不是手写训练课，但理解笔顺会帮你数笔画、查字典，也能让汉字看起来更像汉字。",
      note: "课程仍然优先训练阅读、听说和拼音输入；笔顺在这里作为识字背景知识出现。",
      rules: [
        { title: "从左到右", example: "例：川、人", steps: ["左", "中", "右"] },
        { title: "从上到下", example: "例：三", steps: ["一", "二", "三"] },
        { title: "先横后竖", example: "例：十", steps: ["一", "十"] },
        { title: "先外后内", example: "例：月", steps: ["外框", "里面"] },
        { title: "先中间后两边", example: "例：小", steps: ["亅", "丿", "丶"] },
        { title: "先里后封口", example: "例：日、回", steps: ["冂", "里面", "封口"] }
      ]
    },
    typing: {
      title: "最后连接到本课程的目标：会认、会读、会打",
      p1: "手写和笔顺很重要，但本课程的主要路径是<strong>阅读、听力、口语和拼音输入法打字</strong>。",
      p2: "你先用这些结构建立汉字的视觉模型，再用拼音页面掌握读音，最后用输入法把声音转成汉字。"
    }
  },
  en: {
    badge: "Foundation · Characters",
    title: "How Chinese characters are built",
    subtitle: "This page turns the textbook's Basic pages 13-17 into a learner-friendly map: structure first, then radicals, strokes, and stroke order.",
    readingOnly: "Build a recognition model first - no need to memorize it all",
    studyModel: {
      eyebrow: "How to look",
      title: "When you meet a character, ask three questions",
      body: "New learners often see only a dense pile of strokes. Use the same viewing order every time: whole shape, components, then pronunciation.",
      steps: [
        { title: "Read the shape", body: "Is it left-right, top-bottom, enclosing, or unitary? Split the large blocks first." },
        { title: "Find the radical", body: "Which part may hint at meaning? Water, mouth, hand, and speech are especially common." },
        { title: "Check the sound", body: "Many characters contain a sound clue, but modern pronunciation may have shifted. Confirm with pinyin." }
      ]
    },
    formation: {
      eyebrow: "Writing system",
      title: "Start here: characters are not just little pictures",
      body: "Chinese is written in square characters. A character usually maps to one syllable and carries a unit of meaning. A few characters began as pictures; many more combine meaning components with sound clues.",
      note: "Working model: when you meet a new character, first look for its components, radical, and spatial structure. Let pinyin and the IME handle pronunciation and typing.",
      priority: {
        title: "Most useful first: semantic-phonetic characters",
        body: "The textbook points out a common myth: only a small share of characters are pictographs. Most useful beginner characters are better understood as meaning part + sound clue, so do not give the six historical categories equal study time.",
        examples: [
          { char: "河", parts: ["氵 = water/liquid", "可 = historical sound clue"], note: "Meaning relates to water; pinyin confirms hé." },
          { char: "饭", parts: ["饣 = food", "反 = historical sound clue"], note: "Meaning relates to eating; pronunciation is fàn." },
          { char: "妈", parts: ["女 = person/identity", "马 = historical sound clue"], note: "The sound clue is close, but the tone changes." }
        ]
      },
      types: [
        { title: "Pictographs", pinyin: "xiàngxíng", glyph: "山", glyphMeaning: "mountain", description: "Characters that developed from the outline of concrete things.", examples: [{ char: "人", pinyin: "rén", meaning: "person" }, { char: "山", pinyin: "shān", meaning: "mountain" }, { char: "日", pinyin: "rì", meaning: "sun" }, { char: "月", pinyin: "yuè", meaning: "moon" }, { char: "木", pinyin: "mù", meaning: "tree" }] },
        { title: "Simple ideograms", pinyin: "zhǐshì", glyph: "上", glyphMeaning: "above", description: "Simple marks that point to an abstract relation or position.", examples: [{ char: "上", pinyin: "shàng", meaning: "above" }, { char: "下", pinyin: "xià", meaning: "below" }] },
        { title: "Compound ideograms", pinyin: "huìyì", glyph: "明", glyphMeaning: "bright", description: "Meaning components placed together so the combined meaning becomes visible.", examples: [{ char: "明", pinyin: "míng", meaning: "bright" }, { char: "休", pinyin: "xiū", meaning: "rest" }], breakdowns: [{ parts: [{ char: "日", pinyin: "rì", meaning: "sun" }, { char: "月", pinyin: "yuè", meaning: "moon" }], result: { char: "明", pinyin: "míng", meaning: "bright" } }, { parts: [{ char: "人", pinyin: "rén", meaning: "person" }, { char: "木", pinyin: "mù", meaning: "tree" }], result: { char: "休", pinyin: "xiū", meaning: "rest" } }] },
        { title: "Semantic-phonetic", pinyin: "xíngshēng", glyph: "河", glyphMeaning: "river", description: "One part hints at meaning, another at historical sound. This is the most useful pattern for beginners.", examples: [{ char: "江", pinyin: "jiāng", meaning: "river" }, { char: "河", pinyin: "hé", meaning: "river" }, { char: "饭", pinyin: "fàn", meaning: "meal" }, { char: "姑", pinyin: "gū", meaning: "aunt" }] },
        { title: "Mutual explanation", pinyin: "zhuǎnzhù", glyph: "老", glyphMeaning: "old", description: "A historical category where related characters explain or extend each other.", examples: [{ char: "老", pinyin: "lǎo", meaning: "old" }, { char: "考", pinyin: "kǎo", meaning: "test" }] },
        { title: "Phonetic loans", pinyin: "jiǎjiè", glyph: "来", glyphMeaning: "come", description: "Existing characters borrowed to write a same or similar sound.", examples: [{ char: "来", pinyin: "lái", meaning: "come" }, { char: "我", pinyin: "wǒ", meaning: "I / me" }] }
      ]
    },
    radicals: {
      eyebrow: "Radicals",
      title: "Radicals are handles for lookup and memory",
      body: "Traditional dictionaries organize characters by radicals. The textbook gives forty starter radicals; this version keeps all forty in a compact scan-friendly grid.",
      tip: "Learn the meaning range first. A radical is usually a clue, not a strict definition.",
      items: buildHanziRadicals('en')
    },
    structures: {
      eyebrow: "Character structures",
      title: "Characters are blocks: read the layout first",
      body: "The textbook presents nine common layouts. The goal is not terminology; it is learning to see how a character is assembled.",
      items: [
        { type: "Unitary", label: "独体", sketch: "unitary", examples: "上 · 水 · 人 · 女 · 山" },
        { type: "Left-right", label: "左右", sketch: "leftRight", examples: "忙 · 唱 · 便 · 汉 · 都" },
        { type: "Top-bottom", label: "上下", sketch: "topBottom", examples: "李 · 字 · 念 · 想 · 笔" },
        { type: "Semi-enclosing", label: "半包围", sketch: "semiEnclosing", examples: "同 · 周 · 问 · 间 · 风" },
        { type: "Enclosing", label: "全包围", sketch: "enclosing", examples: "回 · 因 · 国 · 图 · 圆" },
        { type: "Horizontal trisection", label: "左中右", sketch: "horizontalTrisection", examples: "班 · 街 · 辩 · 粥" },
        { type: "Vertical trisection", label: "上中下", sketch: "verticalTrisection", examples: "鼻 · 幕 · 曼" },
        { type: "Left-bottom enclosing", label: "左下包围", sketch: "leftBottomEnclosing", examples: "这 · 起 · 过 · 道 · 造" },
        { type: "Left-top enclosing", label: "左上包围", sketch: "leftTopEnclosing", examples: "床 · 麻 · 病 · 历 · 屋" }
      ]
    },
    strokes: {
      eyebrow: "Basic strokes",
      title: "Basic strokes: the smallest writing moves",
      body: "Most strokes move top-to-bottom or left-to-right. This chart gives you the main names used for recognizing and looking up characters.",
      note: "Two exceptions are worth noticing: tí moves up to the right, and piě falls down to the left.",
      items: [
        { mark: "丶", name: "点 diǎn", description: "dot", examples: "小 · 六" },
        { mark: "一", name: "横 héng", description: "horizontal", examples: "一 · 六" },
        { mark: "丨", name: "竖 shù", description: "vertical", examples: "十 · 中" },
        { mark: "丿", name: "撇 piě", description: "downward left", examples: "人 · 大" },
        { mark: "㇏", name: "捺 nà", description: "downward right", examples: "八 · 人" },
        { mark: "㇀", name: "提 tí", description: "upward", examples: "我 · 江" },
        { mark: "乛", name: "横钩 hénggōu", description: "horizontal hook", examples: "你 · 字" },
        { mark: "亅", name: "竖钩 shùgōu", description: "vertical hook", examples: "小 · 你" },
        { mark: "㇂", name: "斜钩 xiégōu", description: "slanted hook", examples: "我 · 戈" },
        { mark: "𠃍", name: "横折 héngzhé", description: "horizontal bend", examples: "五 · 口" },
        { mark: "㇄", name: "竖折 shùzhé", description: "vertical bend", examples: "七 · 亡" }
      ]
    },
    strokeOrder: {
      eyebrow: "Stroke order",
      title: "Stroke order keeps the shape stable",
      body: "This is not a handwriting course, but stroke order helps you count strokes, use radical dictionaries, and understand why characters look balanced.",
      note: "The course still prioritizes reading, listening, speaking, and pinyin typing. Stroke order appears here as background knowledge for recognizing characters.",
      rules: [
        { title: "Left to right", example: "Examples: 川, 人", steps: ["left", "middle", "right"] },
        { title: "Top to bottom", example: "Example: 三", steps: ["一", "二", "三"] },
        { title: "Horizontal before vertical", example: "Example: 十", steps: ["一", "十"] },
        { title: "Outside before inside", example: "Example: 月", steps: ["outside", "inside"] },
        { title: "Middle before two sides", example: "Example: 小", steps: ["亅", "丿", "丶"] },
        { title: "Inside before closing", example: "Examples: 日, 回", steps: ["frame", "inside", "close"] }
      ]
    },
    typing: {
      title: "The course goal: recognize, read, and type",
      p1: "Handwriting and stroke order matter, but this course focuses on <strong>reading, listening, speaking, and typing with a pinyin IME</strong>.",
      p2: "Use this page to build a visual model, use the pinyin page for pronunciation, then let your input method turn sounds into characters."
    }
  },
  de: {
    badge: "Grundlagen · Zeichen",
    title: "Wie chinesische Zeichen aufgebaut sind",
    subtitle: "Diese Seite macht aus den Basic-Seiten 13-17 des Lehrbuchs eine lernfreundliche Karte: zuerst Struktur, dann Radikale, Striche und Strichfolge.",
    readingOnly: "Zuerst ein Erkennungsmodell aufbauen - nicht alles sofort auswendig lernen",
    studyModel: {
      eyebrow: "Blickfolge",
      title: "Bei einem neuen Zeichen drei Fragen stellen",
      body: "Am Anfang sieht man oft nur viele Striche. Nutze immer dieselbe Reihenfolge: Gesamtform, Bestandteile, dann Aussprache.",
      steps: [
        { title: "Form lesen", body: "Ist es links-rechts, oben-unten, umschließend oder einteilig? Zuerst die großen Blöcke trennen." },
        { title: "Radikal finden", body: "Welcher Teil kann Bedeutung anzeigen? Wasser, Mund, Hand und Sprache kommen besonders oft vor." },
        { title: "Laut prüfen", body: "Viele Zeichen enthalten einen Laut-Hinweis, aber die heutige Aussprache kann abweichen. Mit Pinyin bestätigen." }
      ]
    },
    formation: {
      eyebrow: "Schriftsystem",
      title: "Zuerst verstehen: Zeichen sind nicht einfach kleine Bilder",
      body: "Chinesisch wird in quadratischen Zeichen geschrieben. Ein Zeichen entspricht meist einer Silbe und trägt zugleich eine Bedeutungseinheit. Einige Zeichen entstanden aus Bildern; viele kombinieren Bedeutungsteile mit Laut-Hinweisen.",
      note: "Arbeitsmodell: Suche bei einem neuen Zeichen zuerst Komponenten, Radikal und räumliche Struktur. Aussprache und Tippen laufen dann über Pinyin und die Eingabemethode.",
      priority: {
        title: "Am wichtigsten zuerst: Bedeutung + Laut",
        body: "Das Lehrbuch korrigiert einen verbreiteten Mythos: Nur wenige Zeichen sind echte Bilder. Für Lernende ist meist das Muster Bedeutungsteil + Laut-Hinweis wichtiger als die gleichmäßige Einprägung aller sechs historischen Kategorien.",
        examples: [
          { char: "河", parts: ["氵 = Wasser/Flüssigkeit", "可 = historischer Laut-Hinweis"], note: "Die Bedeutung hat mit Wasser zu tun; Pinyin bestätigt hé." },
          { char: "饭", parts: ["饣 = Essen", "反 = historischer Laut-Hinweis"], note: "Die Bedeutung hat mit Essen zu tun; die Aussprache ist fàn." },
          { char: "妈", parts: ["女 = Person/Identität", "马 = historischer Laut-Hinweis"], note: "Der Laut ist ähnlich, aber der Ton ändert sich." }
        ]
      },
      types: [
        { title: "Piktogramme", pinyin: "xiàngxíng", glyph: "山", glyphMeaning: "Berg", description: "Zeichen, die aus Umrissen konkreter Dinge entstanden sind.", examples: [{ char: "人", pinyin: "rén", meaning: "Person" }, { char: "山", pinyin: "shān", meaning: "Berg" }, { char: "日", pinyin: "rì", meaning: "Sonne" }, { char: "月", pinyin: "yuè", meaning: "Mond" }, { char: "木", pinyin: "mù", meaning: "Baum" }] },
        { title: "Einfache Ideogramme", pinyin: "zhǐshì", glyph: "上", glyphMeaning: "oben", description: "Einfache Zeichen, die abstrakte Beziehungen oder Positionen markieren.", examples: [{ char: "上", pinyin: "shàng", meaning: "oben" }, { char: "下", pinyin: "xià", meaning: "unten" }] },
        { title: "Zusammengesetzte Ideogramme", pinyin: "huìyì", glyph: "明", glyphMeaning: "hell", description: "Bedeutungsteile werden kombiniert, sodass eine neue Bedeutung sichtbar wird.", examples: [{ char: "明", pinyin: "míng", meaning: "hell" }, { char: "休", pinyin: "xiū", meaning: "ruhen" }], breakdowns: [{ parts: [{ char: "日", pinyin: "rì", meaning: "Sonne" }, { char: "月", pinyin: "yuè", meaning: "Mond" }], result: { char: "明", pinyin: "míng", meaning: "hell" } }, { parts: [{ char: "人", pinyin: "rén", meaning: "Person" }, { char: "木", pinyin: "mù", meaning: "Baum" }], result: { char: "休", pinyin: "xiū", meaning: "ruhen" } }] },
        { title: "Bedeutung + Laut", pinyin: "xíngshēng", glyph: "河", glyphMeaning: "Fluss", description: "Ein Teil deutet die Bedeutung an, ein anderer den historischen Klang. Für Lernende ist das besonders nützlich.", examples: [{ char: "江", pinyin: "jiāng", meaning: "Fluss" }, { char: "河", pinyin: "hé", meaning: "Fluss" }, { char: "饭", pinyin: "fàn", meaning: "Mahlzeit" }, { char: "姑", pinyin: "gū", meaning: "Tante" }] },
        { title: "Gegenseitige Erklärung", pinyin: "zhuǎnzhù", glyph: "老", glyphMeaning: "alt", description: "Eine historische Kategorie verwandter Zeichen, die einander erklären oder erweitern.", examples: [{ char: "老", pinyin: "lǎo", meaning: "alt" }, { char: "考", pinyin: "kǎo", meaning: "Prüfung" }] },
        { title: "Lautentlehnung", pinyin: "jiǎjiè", glyph: "来", glyphMeaning: "kommen", description: "Vorhandene Zeichen wurden für gleiche oder ähnliche Laute ausgeliehen.", examples: [{ char: "来", pinyin: "lái", meaning: "kommen" }, { char: "我", pinyin: "wǒ", meaning: "ich" }] }
      ]
    },
    radicals: {
      eyebrow: "Radikale",
      title: "Radikale helfen beim Nachschlagen und Merken",
      body: "Traditionelle Wörterbücher ordnen Zeichen nach Radikalen. Das Lehrbuch zeigt vierzig Starter-Radikale; hier bleiben alle vierzig erhalten, aber als kompakte Übersicht.",
      tip: "Lerne zuerst den Bedeutungsbereich. Ein Radikal ist meist ein Hinweis, keine strenge Definition.",
      items: buildHanziRadicals('de')
    },
    structures: {
      eyebrow: "Zeichenstrukturen",
      title: "Zeichen sind Bausteine: zuerst das Layout lesen",
      body: "Das Lehrbuch zeigt neun häufige Layouts. Wichtig ist nicht der Fachbegriff, sondern zu sehen, wie ein Zeichen zusammengesetzt ist.",
      items: [
        { type: "Einheitlich", label: "独体", sketch: "unitary", examples: "上 · 水 · 人 · 女 · 山" },
        { type: "Links-rechts", label: "左右", sketch: "leftRight", examples: "忙 · 唱 · 便 · 汉 · 都" },
        { type: "Oben-unten", label: "上下", sketch: "topBottom", examples: "李 · 字 · 念 · 想 · 笔" },
        { type: "Teilweise umschlossen", label: "半包围", sketch: "semiEnclosing", examples: "同 · 周 · 问 · 间 · 风" },
        { type: "Umschlossen", label: "全包围", sketch: "enclosing", examples: "回 · 因 · 国 · 图 · 圆" },
        { type: "Links-mitte-rechts", label: "左中右", sketch: "horizontalTrisection", examples: "班 · 街 · 辩 · 粥" },
        { type: "Oben-mitte-unten", label: "上中下", sketch: "verticalTrisection", examples: "鼻 · 幕 · 曼" },
        { type: "Links-unten umschlossen", label: "左下包围", sketch: "leftBottomEnclosing", examples: "这 · 起 · 过 · 道 · 造" },
        { type: "Links-oben umschlossen", label: "左上包围", sketch: "leftTopEnclosing", examples: "床 · 麻 · 病 · 历 · 屋" }
      ]
    },
    strokes: {
      eyebrow: "Grundstriche",
      title: "Grundstriche: die kleinsten Schreibbewegungen",
      body: "Die meisten Striche laufen von oben nach unten oder von links nach rechts. Diese Liste hilft beim Erkennen und Nachschlagen.",
      note: "Zwei Ausnahmen fallen auf: tí steigt nach rechts oben, piě fällt nach links unten.",
      items: [
        { mark: "丶", name: "点 diǎn", description: "Punkt", examples: "小 · 六" },
        { mark: "一", name: "横 héng", description: "horizontal", examples: "一 · 六" },
        { mark: "丨", name: "竖 shù", description: "vertikal", examples: "十 · 中" },
        { mark: "丿", name: "撇 piě", description: "fallend nach links", examples: "人 · 大" },
        { mark: "㇏", name: "捺 nà", description: "fallend nach rechts", examples: "八 · 人" },
        { mark: "㇀", name: "提 tí", description: "steigend", examples: "我 · 江" },
        { mark: "乛", name: "横钩 hénggōu", description: "Horizontalhaken", examples: "你 · 字" },
        { mark: "亅", name: "竖钩 shùgōu", description: "Vertikalhaken", examples: "小 · 你" },
        { mark: "㇂", name: "斜钩 xiégōu", description: "Schräghaken", examples: "我 · 戈" },
        { mark: "𠃍", name: "横折 héngzhé", description: "horizontaler Knick", examples: "五 · 口" },
        { mark: "㇄", name: "竖折 shùzhé", description: "vertikaler Knick", examples: "七 · 亡" }
      ]
    },
    strokeOrder: {
      eyebrow: "Strichfolge",
      title: "Strichfolge stabilisiert die Form",
      body: "Dies ist kein Handschriftkurs, aber Strichfolge hilft beim Zählen, Nachschlagen und beim Verständnis der Balance eines Zeichens.",
      note: "Der Kurs priorisiert weiterhin Lesen, Hören, Sprechen und Pinyin-Tippen. Strichfolge bleibt hier Hintergrundwissen.",
      rules: [
        { title: "Von links nach rechts", example: "Beispiele: 川, 人", steps: ["links", "mitte", "rechts"] },
        { title: "Von oben nach unten", example: "Beispiel: 三", steps: ["一", "二", "三"] },
        { title: "Horizontal vor vertikal", example: "Beispiel: 十", steps: ["一", "十"] },
        { title: "Außen vor innen", example: "Beispiel: 月", steps: ["außen", "innen"] },
        { title: "Mitte vor beiden Seiten", example: "Beispiel: 小", steps: ["亅", "丿", "丶"] },
        { title: "Innen vor Schließen", example: "Beispiele: 日, 回", steps: ["Rahmen", "innen", "schließen"] }
      ]
    },
    typing: {
      title: "Kursziel: erkennen, lesen und tippen",
      p1: "Handschrift und Strichfolge sind wichtig, aber dieser Kurs konzentriert sich auf <strong>Lesen, Hören, Sprechen und Tippen mit einer Pinyin-Eingabemethode</strong>.",
      p2: "Nutze diese Seite für das visuelle Modell, die Pinyin-Seite für Aussprache, und dann wandelt die Eingabemethode Laute in Zeichen um."
    }
  },
  fr: {
    badge: "Fondations · Caractères",
    title: "Comment les caractères chinois sont construits",
    subtitle: "Cette page transforme les pages Basic 13-17 du manuel en carte plus lisible : structure d'abord, puis radicaux, traits et ordre des traits.",
    readingOnly: "Construire d'abord un modèle de reconnaissance - pas besoin de tout mémoriser",
    studyModel: {
      eyebrow: "Comment regarder",
      title: "Devant un nouveau caractère, posez trois questions",
      body: "Au début, on voit surtout beaucoup de traits. Gardez toujours le même ordre : forme globale, composants, puis prononciation.",
      steps: [
        { title: "Lire la forme", body: "Est-il gauche-droite, haut-bas, encerclant ou unitaire ? Séparez d'abord les grands blocs." },
        { title: "Trouver le radical", body: "Quelle partie peut donner le sens ? Eau, bouche, main et parole sont très fréquents." },
        { title: "Vérifier le son", body: "Beaucoup de caractères ont un indice sonore, mais la prononciation moderne peut avoir changé. Confirmez avec le pinyin." }
      ]
    },
    formation: {
      eyebrow: "Système d'écriture",
      title: "Commencer ici : les caractères ne sont pas seulement de petites images",
      body: "Le chinois s'écrit en caractères carrés. Un caractère correspond souvent à une syllabe et porte une unité de sens. Quelques caractères viennent d'images ; beaucoup combinent des indices de sens et de son.",
      note: "Modèle pratique : devant un nouveau caractère, repérez ses composants, son radical et sa structure spatiale. Le pinyin et l'IME aideront pour la prononciation et la saisie.",
      priority: {
        title: "Priorité utile : sens + indice sonore",
        body: "Le manuel corrige un mythe courant : peu de caractères sont de vrais pictogrammes. Pour apprendre, le modèle composant de sens + indice sonore est souvent plus utile que mémoriser également les six catégories historiques.",
        examples: [
          { char: "河", parts: ["氵 = eau/liquide", "可 = indice sonore historique"], note: "Le sens est lié à l'eau ; le pinyin confirme hé." },
          { char: "饭", parts: ["饣 = nourriture", "反 = indice sonore historique"], note: "Le sens est lié à manger ; la prononciation est fàn." },
          { char: "妈", parts: ["女 = personne/identité", "马 = indice sonore historique"], note: "L'indice sonore est proche, mais le ton change." }
        ]
      },
      types: [
        { title: "Pictogrammes", pinyin: "xiàngxíng", glyph: "山", glyphMeaning: "montagne", description: "Caractères issus du contour de choses concrètes.", examples: [{ char: "人", pinyin: "rén", meaning: "personne" }, { char: "山", pinyin: "shān", meaning: "montagne" }, { char: "日", pinyin: "rì", meaning: "soleil" }, { char: "月", pinyin: "yuè", meaning: "lune" }, { char: "木", pinyin: "mù", meaning: "arbre" }] },
        { title: "Idéogrammes simples", pinyin: "zhǐshì", glyph: "上", glyphMeaning: "au-dessus", description: "Marques simples indiquant une relation ou une position abstraite.", examples: [{ char: "上", pinyin: "shàng", meaning: "au-dessus" }, { char: "下", pinyin: "xià", meaning: "au-dessous" }] },
        { title: "Idéogrammes composés", pinyin: "huìyì", glyph: "明", glyphMeaning: "clair", description: "Des composants de sens sont réunis pour faire apparaître un sens combiné.", examples: [{ char: "明", pinyin: "míng", meaning: "clair" }, { char: "休", pinyin: "xiū", meaning: "se reposer" }], breakdowns: [{ parts: [{ char: "日", pinyin: "rì", meaning: "soleil" }, { char: "月", pinyin: "yuè", meaning: "lune" }], result: { char: "明", pinyin: "míng", meaning: "clair" } }, { parts: [{ char: "人", pinyin: "rén", meaning: "personne" }, { char: "木", pinyin: "mù", meaning: "arbre" }], result: { char: "休", pinyin: "xiū", meaning: "se reposer" } }] },
        { title: "Sémantico-phonétiques", pinyin: "xíngshēng", glyph: "河", glyphMeaning: "rivière", description: "Une partie indique le sens, l'autre donne un indice sonore historique.", examples: [{ char: "江", pinyin: "jiāng", meaning: "fleuve" }, { char: "河", pinyin: "hé", meaning: "rivière" }, { char: "饭", pinyin: "fàn", meaning: "repas" }, { char: "姑", pinyin: "gū", meaning: "tante" }] },
        { title: "Explication mutuelle", pinyin: "zhuǎnzhù", glyph: "老", glyphMeaning: "vieux", description: "Catégorie historique où des caractères apparentés s'expliquent ou s'étendent.", examples: [{ char: "老", pinyin: "lǎo", meaning: "vieux" }, { char: "考", pinyin: "kǎo", meaning: "examen" }] },
        { title: "Emprunts phonétiques", pinyin: "jiǎjiè", glyph: "来", glyphMeaning: "venir", description: "Des caractères existants sont empruntés pour noter un son identique ou proche.", examples: [{ char: "来", pinyin: "lái", meaning: "venir" }, { char: "我", pinyin: "wǒ", meaning: "je / moi" }] }
      ]
    },
    radicals: {
      eyebrow: "Radicaux",
      title: "Les radicaux servent à chercher et mémoriser",
      body: "Les dictionnaires traditionnels organisent les caractères par radicaux. Le manuel en présente quarante ; cette version les garde tous dans une grille compacte.",
      tip: "Apprenez d'abord la zone de sens. Un radical est souvent un indice, pas une définition stricte.",
      items: buildHanziRadicals('fr')
    },
    structures: {
      eyebrow: "Structures",
      title: "Les caractères sont des blocs : lire d'abord la disposition",
      body: "Le manuel présente neuf dispositions fréquentes. Le but n'est pas le vocabulaire technique, mais de voir comment le caractère est assemblé.",
      items: [
        { type: "Unitaire", label: "独体", sketch: "unitary", examples: "上 · 水 · 人 · 女 · 山" },
        { type: "Gauche-droite", label: "左右", sketch: "leftRight", examples: "忙 · 唱 · 便 · 汉 · 都" },
        { type: "Haut-bas", label: "上下", sketch: "topBottom", examples: "李 · 字 · 念 · 想 · 笔" },
        { type: "Semi-encerclant", label: "半包围", sketch: "semiEnclosing", examples: "同 · 周 · 问 · 间 · 风" },
        { type: "Encerclant", label: "全包围", sketch: "enclosing", examples: "回 · 因 · 国 · 图 · 圆" },
        { type: "Gauche-centre-droite", label: "左中右", sketch: "horizontalTrisection", examples: "班 · 街 · 辩 · 粥" },
        { type: "Haut-centre-bas", label: "上中下", sketch: "verticalTrisection", examples: "鼻 · 幕 · 曼" },
        { type: "Encerclant gauche-bas", label: "左下包围", sketch: "leftBottomEnclosing", examples: "这 · 起 · 过 · 道 · 造" },
        { type: "Encerclant gauche-haut", label: "左上包围", sketch: "leftTopEnclosing", examples: "床 · 麻 · 病 · 历 · 屋" }
      ]
    },
    strokes: {
      eyebrow: "Traits de base",
      title: "Traits de base : les plus petits gestes d'écriture",
      body: "La plupart des traits vont de haut en bas ou de gauche à droite. Cette liste aide à reconnaître et chercher les caractères.",
      note: "Deux exceptions utiles : tí monte vers la droite, piě descend vers la gauche.",
      items: [
        { mark: "丶", name: "点 diǎn", description: "point", examples: "小 · 六" },
        { mark: "一", name: "横 héng", description: "horizontal", examples: "一 · 六" },
        { mark: "丨", name: "竖 shù", description: "vertical", examples: "十 · 中" },
        { mark: "丿", name: "撇 piě", description: "descendant gauche", examples: "人 · 大" },
        { mark: "㇏", name: "捺 nà", description: "descendant droit", examples: "八 · 人" },
        { mark: "㇀", name: "提 tí", description: "montant", examples: "我 · 江" },
        { mark: "乛", name: "横钩 hénggōu", description: "crochet horizontal", examples: "你 · 字" },
        { mark: "亅", name: "竖钩 shùgōu", description: "crochet vertical", examples: "小 · 你" },
        { mark: "㇂", name: "斜钩 xiégōu", description: "crochet oblique", examples: "我 · 戈" },
        { mark: "𠃍", name: "横折 héngzhé", description: "pli horizontal", examples: "五 · 口" },
        { mark: "㇄", name: "竖折 shùzhé", description: "pli vertical", examples: "七 · 亡" }
      ]
    },
    strokeOrder: {
      eyebrow: "Ordre des traits",
      title: "L'ordre des traits stabilise la forme",
      body: "Ce n'est pas un cours d'écriture manuscrite, mais l'ordre des traits aide à compter, chercher et comprendre l'équilibre des caractères.",
      note: "Le cours reste centré sur lecture, écoute, parole et saisie pinyin. L'ordre des traits sert ici de contexte pour reconnaître les caractères.",
      rules: [
        { title: "De gauche à droite", example: "Exemples : 川, 人", steps: ["gauche", "centre", "droite"] },
        { title: "De haut en bas", example: "Exemple : 三", steps: ["一", "二", "三"] },
        { title: "Horizontal avant vertical", example: "Exemple : 十", steps: ["一", "十"] },
        { title: "Extérieur avant intérieur", example: "Exemple : 月", steps: ["extérieur", "intérieur"] },
        { title: "Milieu avant les côtés", example: "Exemple : 小", steps: ["亅", "丿", "丶"] },
        { title: "Intérieur avant fermeture", example: "Exemples : 日, 回", steps: ["cadre", "intérieur", "fermer"] }
      ]
    },
    typing: {
      title: "Objectif du cours : reconnaître, lire et saisir",
      p1: "L'écriture manuscrite et l'ordre des traits comptent, mais ce cours se concentre sur <strong>la lecture, l'écoute, l'oral et la saisie avec un IME pinyin</strong>.",
      p2: "Utilisez cette page pour construire le modèle visuel, la page pinyin pour la prononciation, puis l'IME transforme les sons en caractères."
    }
  }
};

const HANZI_STRUCTURE_BLUEPRINT = HANZI_INTRO_TRANSLATIONS.en.structures.items.map(({ label, sketch, examples }) => ({
  label,
  sketch,
  examples,
}));

const HANZI_STROKE_BLUEPRINT = HANZI_INTRO_TRANSLATIONS.en.strokes.items.map(({ mark, name, examples }) => ({
  mark,
  name,
  examples,
}));

const HANZI_STRUCTURE_TYPES = {
  ru: ["Цельный", "Слева-справа", "Сверху-снизу", "Полуокружение", "Полное окружение", "Лево-центр-право", "Верх-середина-низ", "Окружение слева снизу", "Окружение слева сверху"],
  es: ["Unitario", "Izquierda-derecha", "Arriba-abajo", "Semienvolvente", "Envolvente", "Izquierda-centro-derecha", "Arriba-centro-abajo", "Envolvente izquierda-abajo", "Envolvente izquierda-arriba"],
  jp: ["独体", "左右", "上下", "半包囲", "全包囲", "左中右", "上中下", "左下包囲", "左上包囲"],
  ko: ["단일 구조", "좌우 구조", "상하 구조", "반포위 구조", "완전 포위 구조", "좌중우 구조", "상중하 구조", "왼쪽-아래 포위", "왼쪽-위 포위"],
  vi: ["Độc thể", "Trái-phải", "Trên-dưới", "Nửa bao quanh", "Bao quanh", "Trái-giữa-phải", "Trên-giữa-dưới", "Bao trái-dưới", "Bao trái-trên"],
  pt: ["Unitário", "Esquerda-direita", "Cima-baixo", "Semienvolvente", "Envolvente", "Esquerda-centro-direita", "Cima-centro-baixo", "Envolvente esquerda-baixo", "Envolvente esquerda-cima"],
  it: ["Unitario", "Sinistra-destra", "Alto-basso", "Semiavvolgente", "Avvolgente", "Sinistra-centro-destra", "Alto-centro-basso", "Avvolgente sinistra-basso", "Avvolgente sinistra-alto"],
  id: ["Tunggal", "Kiri-kanan", "Atas-bawah", "Setengah mengurung", "Mengurung penuh", "Kiri-tengah-kanan", "Atas-tengah-bawah", "Mengurung kiri-bawah", "Mengurung kiri-atas"],
  ms: ["Tunggal", "Kiri-kanan", "Atas-bawah", "Separuh mengepung", "Mengepung penuh", "Kiri-tengah-kanan", "Atas-tengah-bawah", "Mengepung kiri-bawah", "Mengepung kiri-atas"],
  ar: ["مفرد", "يسار-يمين", "أعلى-أسفل", "شبه محيط", "محيط كامل", "يسار-وسط-يمين", "أعلى-وسط-أسفل", "إحاطة يسار-أسفل", "إحاطة يسار-أعلى"],
  th: ["เดี่ยว", "ซ้าย-ขวา", "บน-ล่าง", "ล้อมบางส่วน", "ล้อมรอบ", "ซ้าย-กลาง-ขวา", "บน-กลาง-ล่าง", "ล้อมซ้ายล่าง", "ล้อมซ้ายบน"],
};

const HANZI_STROKE_DESCRIPTIONS = {
  ru: ["точка", "горизонтальная", "вертикальная", "вниз влево", "вниз вправо", "вверх вправо", "горизонтальный крюк", "вертикальный крюк", "наклонный крюк", "горизонтальный излом", "вертикальный излом"],
  es: ["punto", "horizontal", "vertical", "baja a la izquierda", "baja a la derecha", "sube a la derecha", "gancho horizontal", "gancho vertical", "gancho oblicuo", "giro horizontal", "giro vertical"],
  jp: ["点", "横", "縦", "左下へ払う", "右下へ払う", "右上へ上げる", "横のあと鉤", "縦のあと鉤", "斜めの鉤", "横のあと折れる", "縦のあと折れる"],
  ko: ["점", "가로", "세로", "왼쪽 아래로", "오른쪽 아래로", "오른쪽 위로", "가로 갈고리", "세로 갈고리", "비스듬한 갈고리", "가로 꺾임", "세로 꺾임"],
  vi: ["chấm", "ngang", "dọc", "xuống trái", "xuống phải", "hất lên phải", "móc ngang", "móc dọc", "móc xiên", "ngang rồi gập", "dọc rồi gập"],
  pt: ["ponto", "horizontal", "vertical", "desce à esquerda", "desce à direita", "sobe à direita", "gancho horizontal", "gancho vertical", "gancho inclinado", "dobra horizontal", "dobra vertical"],
  it: ["punto", "orizzontale", "verticale", "scende a sinistra", "scende a destra", "sale a destra", "gancio orizzontale", "gancio verticale", "gancio obliquo", "piega orizzontale", "piega verticale"],
  id: ["titik", "horizontal", "vertikal", "turun ke kiri", "turun ke kanan", "naik ke kanan", "kait horizontal", "kait vertikal", "kait miring", "belok horizontal", "belok vertikal"],
  ms: ["titik", "melintang", "menegak", "turun ke kiri", "turun ke kanan", "naik ke kanan", "cangkuk melintang", "cangkuk menegak", "cangkuk serong", "lipatan melintang", "lipatan menegak"],
  ar: ["نقطة", "أفقي", "عمودي", "نزول إلى اليسار", "نزول إلى اليمين", "صعود إلى اليمين", "خط أفقي بخطاف", "خط عمودي بخطاف", "خطاف مائل", "انثناء أفقي", "انثناء عمودي"],
  th: ["จุด", "แนวนอน", "แนวตั้ง", "ลงซ้าย", "ลงขวา", "ยกขึ้นขวา", "ขีดนอนมีตะขอ", "ขีดตั้งมีตะขอ", "ตะขอเฉียง", "ขีดนอนแล้วหัก", "ขีดตั้งแล้วหัก"],
};

const HANZI_STROKE_ORDER_RULES = {
  ru: ["Слева направо", "Сверху вниз", "Горизонталь перед вертикалью", "Снаружи перед внутренним", "Середина перед сторонами", "Внутреннее перед закрытием"],
  es: ["De izquierda a derecha", "De arriba abajo", "Horizontal antes que vertical", "Exterior antes que interior", "Centro antes que lados", "Interior antes de cerrar"],
  jp: ["左から右へ", "上から下へ", "横画を先に、縦画を後に", "外側を先に、内側を後に", "中央を先に、両側を後に", "内側を先に、最後に閉じる"],
  ko: ["왼쪽에서 오른쪽으로", "위에서 아래로", "가로획 먼저, 세로획 나중", "바깥쪽 먼저, 안쪽 나중", "가운데 먼저, 양쪽 나중", "안쪽 먼저, 닫기는 마지막"],
  vi: ["Từ trái sang phải", "Từ trên xuống dưới", "Ngang trước dọc", "Ngoài trước trong", "Giữa trước hai bên", "Trong trước khi đóng"],
  pt: ["Da esquerda para a direita", "De cima para baixo", "Horizontal antes do vertical", "Fora antes de dentro", "Meio antes dos lados", "Dentro antes de fechar"],
  it: ["Da sinistra a destra", "Dall'alto in basso", "Orizzontale prima del verticale", "Esterno prima dell'interno", "Centro prima dei lati", "Interno prima della chiusura"],
  id: ["Kiri ke kanan", "Atas ke bawah", "Horizontal sebelum vertikal", "Luar sebelum dalam", "Tengah sebelum dua sisi", "Dalam sebelum menutup"],
  ms: ["Kiri ke kanan", "Atas ke bawah", "Melintang sebelum menegak", "Luar sebelum dalam", "Tengah sebelum dua sisi", "Dalam sebelum menutup"],
  ar: ["من اليسار إلى اليمين", "من الأعلى إلى الأسفل", "الأفقي قبل العمودي", "الخارج قبل الداخل", "الوسط قبل الجانبين", "الداخل قبل الإغلاق"],
  th: ["ซ้ายไปขวา", "บนลงล่าง", "แนวนอนก่อนแนวตั้ง", "ด้านนอกก่อนด้านใน", "กลางก่อนสองข้าง", "ด้านในก่อนปิด"],
};

function buildLocalizedStructures(locale) {
  const types = HANZI_STRUCTURE_TYPES[locale] || HANZI_INTRO_TRANSLATIONS.en.structures.items.map(({ type }) => type);
  return HANZI_STRUCTURE_BLUEPRINT.map((item, index) => ({
    ...item,
    type: types[index] || HANZI_INTRO_TRANSLATIONS.en.structures.items[index].type,
  }));
}

function buildLocalizedStrokes(locale) {
  const descriptions = HANZI_STROKE_DESCRIPTIONS[locale] || HANZI_INTRO_TRANSLATIONS.en.strokes.items.map(({ description }) => description);
  return HANZI_STROKE_BLUEPRINT.map((item, index) => ({
    ...item,
    description: descriptions[index] || HANZI_INTRO_TRANSLATIONS.en.strokes.items[index].description,
  }));
}

function buildLocalizedStrokeOrderRules(locale) {
  const titles = HANZI_STROKE_ORDER_RULES[locale] || HANZI_INTRO_TRANSLATIONS.en.strokeOrder.rules.map(({ title }) => title);
  return HANZI_INTRO_TRANSLATIONS.en.strokeOrder.rules.map((item, index) => ({
    ...item,
    title: titles[index] || item.title,
  }));
}

function buildHanziIntroFromCopy(copy, locale = 'en') {
  const radicalItems = buildHanziRadicals(copy.radicalLocale || 'en').map((item, index) => ({
    ...item,
    meaning: copy.radicalMeanings?.[index] || item.meaning,
    hint: "",
  }));
  const formationPriority = copy.formation?.priority
    ? { ...copy.formation.priority, examples: copy.formation.priority.examples || [] }
    : HANZI_INTRO_TRANSLATIONS.en.formation.priority;
  const structures = {
    ...HANZI_INTRO_TRANSLATIONS.en.structures,
    ...copy.structures,
    items: copy.structures?.items || buildLocalizedStructures(locale),
  };
  const strokes = {
    ...HANZI_INTRO_TRANSLATIONS.en.strokes,
    ...copy.strokes,
    items: copy.strokes?.items || buildLocalizedStrokes(locale),
  };
  const strokeOrder = {
    ...HANZI_INTRO_TRANSLATIONS.en.strokeOrder,
    ...copy.strokeOrder,
    rules: copy.strokeOrder?.rules || buildLocalizedStrokeOrderRules(locale),
  };

  return {
    ...HANZI_INTRO_TRANSLATIONS.en,
    badge: copy.badge,
    title: copy.title,
    subtitle: copy.subtitle,
    readingOnly: copy.readingOnly,
    studyModel: copy.studyModel,
    formation: {
      ...HANZI_INTRO_TRANSLATIONS.en.formation,
      ...copy.formation,
      priority: formationPriority,
      types: buildHanziFormationTypes(copy),
    },
    radicals: {
      ...HANZI_INTRO_TRANSLATIONS.en.radicals,
      ...copy.radicals,
      items: radicalItems,
    },
    structures,
    strokes,
    strokeOrder,
    typing: copy.typing,
  };
}

const HANZI_EXTRA_LOCALE_COPY = {
  ru: {
    badge: "Основа · Иероглифы",
    title: "Как устроены китайские иероглифы",
    subtitle: "Карта по страницам Basic 13-17: сначала форма, затем ключи, черты и порядок письма.",
    readingOnly: "Сначала узнавание формы - не нужно сразу все запоминать",
    studyModel: { eyebrow: "Как смотреть", title: "У нового иероглифа задайте три вопроса", body: "Сначала иероглифы выглядят как набор черт. Смотрите в одном порядке: форма, части, произношение.", steps: [{ title: "Форма", body: "Это слева-направо, сверху-вниз, окружение или цельный знак?" }, { title: "Ключ", body: "Какая часть может намекать на смысл? Вода, рот, рука и речь встречаются часто." }, { title: "Звук", body: "Звуковая часть помогает не всегда точно. Проверьте чтение по пиньиню." }] },
    formation: { eyebrow: "Система письма", title: "Иероглифы - не просто маленькие картинки", body: "Один иероглиф обычно соответствует одному слогу и несет единицу смысла. Немногие знаки произошли от рисунков; многие состоят из смысловой части и звуковой подсказки.", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "Самое полезное: смысл + звук", body: "Для начинающих важнее всего видеть модель: одна часть подсказывает область значения, другая - историческое звучание." } },
    radicals: { eyebrow: "Ключи", title: "Ключи помогают искать и запоминать", body: "В учебнике дано сорок базовых ключей. Здесь они собраны в компактную сетку.", tip: "" },
    structures: { eyebrow: "Структуры", title: "Сначала читайте расположение частей", body: "Цель не в терминах, а в умении видеть, из каких блоков собран знак." },
    strokes: { eyebrow: "Базовые черты", title: "Черты: минимальные движения письма", body: "Эти названия помогают распознавать и искать иероглифы.", note: "" },
    strokeOrder: { eyebrow: "Порядок черт", title: "Порядок черт стабилизирует форму", body: "Он помогает считать черты, искать в словаре и понимать баланс знака.", note: "" },
    typing: { title: "Цель курса: узнавать, читать и печатать", p1: "Письмо от руки важно, но курс делает упор на <strong>чтение, аудирование, говорение и ввод через пиньинь</strong>.", p2: "Сначала постройте визуальную модель, затем используйте пиньинь для произношения и ввода." },
    formationTypes: {
      pictograph: { title: "Пиктограммы", glyphMeaning: "гора", description: "Знаки, возникшие из очертаний конкретных предметов." },
      ideogram: { title: "Простые идеограммы", glyphMeaning: "сверху", description: "Простые отметки для отношения или положения." },
      compound: { title: "Составные идеограммы", glyphMeaning: "яркий", description: "Части со значением соединяются и дают новый смысл." },
      semanticPhonetic: { title: "Смысл + звук", glyphMeaning: "река", description: "Одна часть намекает на смысл, другая на историческое звучание." },
      mutual: { title: "Взаимное объяснение", glyphMeaning: "старый", description: "Историческая категория родственных знаков." },
      loan: { title: "Фонетические заимствования", glyphMeaning: "приходить", description: "Существующие знаки использовались для похожего звучания." }
    },
    exampleMeanings: { person: "человек", mountain: "гора", sun: "солнце", moon: "луна", tree: "дерево", above: "сверху", below: "снизу", bright: "яркий", rest: "отдых", riverJiang: "река", riverHe: "река", meal: "еда", aunt: "тетя", old: "старый", test: "экзамен", come: "приходить", me: "я" }
  },
  es: {
    badge: "Base · Caracteres", title: "Cómo se construyen los caracteres chinos", subtitle: "Una guía de las páginas Basic 13-17: primero la forma, luego radicales, trazos y orden.", readingOnly: "Primero reconoce patrones - no memorices todo de golpe",
    studyModel: { eyebrow: "Cómo mirar", title: "Ante un carácter nuevo, haz tres preguntas", body: "Usa siempre el mismo orden: forma completa, componentes y pronunciación.", steps: [{ title: "Forma", body: "¿Es izquierda-derecha, arriba-abajo, envolvente o unitario?" }, { title: "Radical", body: "¿Qué parte puede indicar el campo de significado?" }, { title: "Sonido", body: "La pista sonora puede haber cambiado; confirma con pinyin." }] },
    formation: { eyebrow: "Sistema de escritura", title: "Los caracteres no son solo dibujos pequeños", body: "Un carácter suele representar una sílaba y una unidad de significado. Muchos combinan una parte semántica con una pista sonora.", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "Lo más útil: significado + sonido", body: "Para principiantes, este patrón es más útil que memorizar por igual las seis categorías históricas." } },
    radicals: { eyebrow: "Radicales", title: "Los radicales ayudan a buscar y recordar", body: "El libro presenta cuarenta radicales básicos; aquí están en una cuadrícula compacta.", tip: "" },
    structures: { eyebrow: "Estructuras", title: "Lee primero la disposición", body: "La meta es ver cómo se arma el carácter, no memorizar términos." },
    strokes: { eyebrow: "Trazos básicos", title: "Trazos: los movimientos mínimos", body: "Estos nombres ayudan a reconocer y buscar caracteres.", note: "" },
    strokeOrder: { eyebrow: "Orden de trazos", title: "El orden estabiliza la forma", body: "Ayuda a contar trazos, usar diccionarios y escribir con mejor equilibrio.", note: "" },
    typing: { title: "Meta del curso: reconocer, leer y escribir con teclado", p1: "La escritura a mano importa, pero el curso prioriza <strong>lectura, escucha, habla y entrada con pinyin</strong>.", p2: "Construye el modelo visual y luego usa pinyin para pronunciación y escritura." },
    formationTypes: { pictograph: { title: "Pictogramas", glyphMeaning: "montaña", description: "Caracteres que vienen del contorno de cosas concretas." }, ideogram: { title: "Ideogramas simples", glyphMeaning: "arriba", description: "Marcas simples para relación o posición." }, compound: { title: "Ideogramas compuestos", glyphMeaning: "brillante", description: "Componentes de significado se combinan." }, semanticPhonetic: { title: "Semántico-fonético", glyphMeaning: "río", description: "Una parte sugiere significado y otra sonido histórico." }, mutual: { title: "Explicación mutua", glyphMeaning: "viejo", description: "Categoría histórica de caracteres relacionados." }, loan: { title: "Préstamos fonéticos", glyphMeaning: "venir", description: "Caracteres usados por sonido parecido." } },
    exampleMeanings: { person: "persona", mountain: "montaña", sun: "sol", moon: "luna", tree: "árbol", above: "arriba", below: "abajo", bright: "brillante", rest: "descansar", riverJiang: "río", riverHe: "río", meal: "comida", aunt: "tía", old: "viejo", test: "examen", come: "venir", me: "yo" }
  },
  jp: {
    badge: "基礎 · 漢字", title: "漢字はどう組み立てられるか", subtitle: "Basic 13-17ページを、形・部首・筆画・筆順の順で見やすく整理しました。", readingOnly: "まず認識モデルを作る - 一度に暗記しなくて大丈夫",
    studyModel: { eyebrow: "見方", title: "新しい字では三つ質問する", body: "全体の形、部品、発音の順で見ます。", steps: [{ title: "形を見る", body: "左右、上下、囲み、独体のどれかを見ます。" }, { title: "部首を探す", body: "意味のヒントになりそうな部分を探します。" }, { title: "音を確認", body: "音のヒントはずれることもあるので、ピンインで確認します。" }] },
    formation: { eyebrow: "文字体系", title: "漢字はただの小さな絵ではない", body: "漢字は多くの場合、一つの音節と意味単位を表します。絵から来た字は一部で、多くは意味部品と音の手がかりから成ります。", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "まず大事なのは意味 + 音", body: "初心者には、意味部品と歴史的な音の手がかりを見ることが特に役立ちます。" } },
    radicals: { eyebrow: "部首", title: "部首は検索と記憶の手がかり", body: "教材の40個の入門部首をコンパクトに表示します。", tip: "" },
    structures: { eyebrow: "構造", title: "まず配置を見る", body: "用語よりも、字がどのブロックでできているかを見ることが大切です。" },
    strokes: { eyebrow: "基本筆画", title: "筆画は最小の書く動き", body: "名前を知ると字を認識しやすくなります。", note: "" },
    strokeOrder: { eyebrow: "筆順", title: "筆順は形を安定させる", body: "筆画数、辞書検索、字形のバランスに役立ちます。", note: "" },
    typing: { title: "目標：認識・読解・入力", p1: "手書きも大切ですが、このコースは<strong>読む・聞く・話す・ピンイン入力</strong>を中心にします。", p2: "まず視覚モデルを作り、ピンインで発音と入力につなげます。" },
    formationTypes: { pictograph: { title: "象形", glyphMeaning: "山", description: "具体物の輪郭から発展した字。" }, ideogram: { title: "指事", glyphMeaning: "上", description: "位置や関係を示す簡単な記号。" }, compound: { title: "会意", glyphMeaning: "明るい", description: "意味部品を合わせて新しい意味を表します。" }, semanticPhonetic: { title: "形声", glyphMeaning: "川/河", description: "一部が意味、一部が歴史的な音を示します。" }, mutual: { title: "転注", glyphMeaning: "老い", description: "関連する字が互いに説明する歴史的分類。" }, loan: { title: "仮借", glyphMeaning: "来る", description: "似た音を書くために既存の字を借ります。" } },
    exampleMeanings: { person: "人", mountain: "山", sun: "太陽", moon: "月", tree: "木", above: "上", below: "下", bright: "明るい", rest: "休む", riverJiang: "川", riverHe: "河", meal: "ご飯", aunt: "おば", old: "古い/老い", test: "試験", come: "来る", me: "私" }
  },
  ko: {
    badge: "기초 · 한자", title: "한자는 어떻게 구성될까", subtitle: "Basic 13-17쪽 내용을 구조, 부수, 획, 필순 순서로 정리했습니다.", readingOnly: "먼저 인식 모델 만들기 - 한 번에 외울 필요 없음",
    studyModel: { eyebrow: "보는 순서", title: "새 글자를 보면 세 가지를 묻기", body: "전체 모양, 구성 요소, 발음 순서로 봅니다.", steps: [{ title: "모양", body: "좌우, 상하, 둘러쌈, 독체인지 봅니다." }, { title: "부수", body: "의미를 암시하는 부분을 찾습니다." }, { title: "소리", body: "소리 힌트는 달라졌을 수 있으니 병음으로 확인합니다." }] },
    formation: { eyebrow: "문자 체계", title: "한자는 작은 그림만이 아닙니다", body: "한 글자는 보통 한 음절과 의미 단위를 나타냅니다. 많은 글자는 의미 부분과 소리 힌트가 결합됩니다.", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "가장 유용한 것: 의미 + 소리", body: "초보자에게는 여섯 분류를 똑같이 외우기보다 이 구조를 보는 것이 더 유용합니다." } },
    radicals: { eyebrow: "부수", title: "부수는 검색과 기억의 손잡이", body: "교재의 40개 입문 부수를 작은 카드로 정리했습니다.", tip: "" },
    structures: { eyebrow: "구조", title: "먼저 배치를 읽기", body: "용어보다 글자가 어떤 블록으로 이루어졌는지 보는 것이 중요합니다." },
    strokes: { eyebrow: "기본 획", title: "획은 가장 작은 쓰기 동작", body: "이 이름들은 글자 인식과 검색에 도움이 됩니다.", note: "" },
    strokeOrder: { eyebrow: "필순", title: "필순은 모양을 안정시킵니다", body: "획수 세기, 사전 검색, 균형 이해에 도움이 됩니다.", note: "" },
    typing: { title: "목표: 알아보기, 읽기, 입력하기", p1: "손글씨도 중요하지만 이 과정은 <strong>읽기, 듣기, 말하기, 병음 입력</strong>에 중점을 둡니다.", p2: "시각 모델을 만들고 병음으로 발음과 입력을 연결하세요." },
    formationTypes: { pictograph: { title: "상형", glyphMeaning: "산", description: "구체적인 사물의 윤곽에서 온 글자." }, ideogram: { title: "지사", glyphMeaning: "위", description: "관계나 위치를 표시하는 간단한 기호." }, compound: { title: "회의", glyphMeaning: "밝음", description: "의미 요소가 결합되어 새 의미를 만듭니다." }, semanticPhonetic: { title: "형성", glyphMeaning: "강", description: "한 부분은 의미, 다른 부분은 역사적 소리를 암시합니다." }, mutual: { title: "전주", glyphMeaning: "늙음", description: "관련 글자가 서로 설명하는 역사적 분류." }, loan: { title: "가차", glyphMeaning: "오다", description: "비슷한 소리를 적기 위해 글자를 빌립니다." } },
    exampleMeanings: { person: "사람", mountain: "산", sun: "해", moon: "달", tree: "나무", above: "위", below: "아래", bright: "밝다", rest: "쉬다", riverJiang: "강", riverHe: "강", meal: "밥", aunt: "고모/이모", old: "늙다", test: "시험", come: "오다", me: "나" }
  }
};

Object.assign(HANZI_EXTRA_LOCALE_COPY, {
  vi: {
    badge: "Nền tảng · Chữ Hán", title: "Chữ Hán được cấu tạo như thế nào", subtitle: "Bản đồ từ Basic trang 13-17: xem cấu trúc trước, rồi bộ thủ, nét và thứ tự nét.", readingOnly: "Xây mô hình nhận diện trước - không cần nhớ hết ngay",
    studyModel: { eyebrow: "Cách nhìn", title: "Gặp chữ mới, hỏi ba câu", body: "Nhìn theo thứ tự cố định: hình tổng thể, bộ phận, rồi phát âm.", steps: [{ title: "Hình dạng", body: "Chữ thuộc kiểu trái-phải, trên-dưới, bao quanh hay độc thể?" }, { title: "Bộ thủ", body: "Phần nào có thể gợi nghĩa?" }, { title: "Âm đọc", body: "Gợi ý âm có thể lệch; hãy xác nhận bằng pinyin." }] },
    formation: { eyebrow: "Hệ chữ viết", title: "Chữ Hán không chỉ là những hình vẽ nhỏ", body: "Một chữ thường tương ứng một âm tiết và một đơn vị nghĩa. Nhiều chữ kết hợp phần gợi nghĩa với gợi ý âm lịch sử.", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "Hữu ích nhất: nghĩa + âm", body: "Với người mới học, nhận ra mô hình này quan trọng hơn học đều cả sáu loại lịch sử." } },
    radicals: { eyebrow: "Bộ thủ", title: "Bộ thủ giúp tra cứu và ghi nhớ", body: "Bốn mươi bộ thủ nhập môn của sách được trình bày thành lưới nhỏ gọn.", tip: "" },
    structures: { eyebrow: "Cấu trúc", title: "Đọc bố cục trước", body: "Mục tiêu là thấy chữ được ghép từ các khối nào." },
    strokes: { eyebrow: "Nét cơ bản", title: "Nét là động tác viết nhỏ nhất", body: "Tên nét giúp nhận diện và tra chữ.", note: "" },
    strokeOrder: { eyebrow: "Thứ tự nét", title: "Thứ tự nét giữ hình chữ ổn định", body: "Nó giúp đếm nét, tra từ điển và hiểu cân bằng chữ.", note: "" },
    typing: { title: "Mục tiêu: nhận ra, đọc và gõ", p1: "Viết tay quan trọng, nhưng khóa học ưu tiên <strong>đọc, nghe, nói và gõ bằng pinyin</strong>.", p2: "Xây mô hình thị giác trước, rồi dùng pinyin cho phát âm và nhập liệu." },
    formationTypes: { pictograph: { title: "Tượng hình", glyphMeaning: "núi", description: "Chữ phát triển từ đường nét của vật cụ thể." }, ideogram: { title: "Chỉ sự", glyphMeaning: "trên", description: "Dấu đơn giản chỉ quan hệ hoặc vị trí." }, compound: { title: "Hội ý", glyphMeaning: "sáng", description: "Các phần nghĩa kết hợp để tạo nghĩa mới." }, semanticPhonetic: { title: "Hình thanh", glyphMeaning: "sông", description: "Một phần gợi nghĩa, phần kia gợi âm lịch sử." }, mutual: { title: "Chuyển chú", glyphMeaning: "già", description: "Nhóm lịch sử của các chữ liên quan." }, loan: { title: "Giả tá", glyphMeaning: "đến", description: "Mượn chữ có âm gần giống." } },
    exampleMeanings: { person: "người", mountain: "núi", sun: "mặt trời", moon: "mặt trăng", tree: "cây", above: "trên", below: "dưới", bright: "sáng", rest: "nghỉ", riverJiang: "sông", riverHe: "sông", meal: "cơm", aunt: "cô/dì", old: "già", test: "thi", come: "đến", me: "tôi" }
  },
  pt: {
    badge: "Base · Caracteres", title: "Como os caracteres chineses são formados", subtitle: "Um mapa das páginas Basic 13-17: forma primeiro, depois radicais, traços e ordem.", readingOnly: "Construa o reconhecimento primeiro - não memorize tudo agora",
    studyModel: { eyebrow: "Como olhar", title: "Ao ver um caractere novo, faça três perguntas", body: "Use sempre a mesma ordem: forma geral, partes e pronúncia.", steps: [{ title: "Forma", body: "É esquerda-direita, cima-baixo, envolvente ou unitário?" }, { title: "Radical", body: "Que parte pode sugerir significado?" }, { title: "Som", body: "A pista sonora pode ter mudado; confirme com pinyin." }] },
    formation: { eyebrow: "Sistema de escrita", title: "Caracteres não são só pequenos desenhos", body: "Um caractere geralmente representa uma sílaba e uma unidade de significado. Muitos combinam parte semântica e pista sonora.", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "Mais útil: significado + som", body: "Para iniciantes, reconhecer esse padrão é mais útil do que memorizar igualmente as seis categorias históricas." } },
    radicals: { eyebrow: "Radicais", title: "Radicais ajudam a procurar e lembrar", body: "Os quarenta radicais iniciais do livro aparecem aqui em cartões compactos.", tip: "" },
    structures: { eyebrow: "Estruturas", title: "Leia primeiro o layout", body: "O objetivo é ver de quais blocos o caractere é feito." },
    strokes: { eyebrow: "Traços básicos", title: "Traços são os menores movimentos", body: "Esses nomes ajudam a reconhecer e procurar caracteres.", note: "" },
    strokeOrder: { eyebrow: "Ordem dos traços", title: "A ordem estabiliza a forma", body: "Ajuda a contar traços, usar dicionários e entender o equilíbrio.", note: "" },
    typing: { title: "Meta: reconhecer, ler e digitar", p1: "A escrita à mão importa, mas o curso prioriza <strong>leitura, escuta, fala e digitação com pinyin</strong>.", p2: "Crie o modelo visual e use pinyin para pronúncia e entrada." },
    formationTypes: { pictograph: { title: "Pictogramas", glyphMeaning: "montanha", description: "Caracteres derivados do contorno de coisas concretas." }, ideogram: { title: "Ideogramas simples", glyphMeaning: "acima", description: "Marcas simples para relação ou posição." }, compound: { title: "Ideogramas compostos", glyphMeaning: "brilhante", description: "Partes de significado se combinam." }, semanticPhonetic: { title: "Semântico-fonético", glyphMeaning: "rio", description: "Uma parte sugere significado e outra som histórico." }, mutual: { title: "Explicação mútua", glyphMeaning: "velho", description: "Categoria histórica de caracteres relacionados." }, loan: { title: "Empréstimos fonéticos", glyphMeaning: "vir", description: "Caracteres usados por som parecido." } },
    exampleMeanings: { person: "pessoa", mountain: "montanha", sun: "sol", moon: "lua", tree: "árvore", above: "acima", below: "abaixo", bright: "brilhante", rest: "descansar", riverJiang: "rio", riverHe: "rio", meal: "refeição", aunt: "tia", old: "velho", test: "prova", come: "vir", me: "eu" }
  },
  it: {
    badge: "Base · Caratteri", title: "Come sono costruiti i caratteri cinesi", subtitle: "Una mappa delle pagine Basic 13-17: prima forma, poi radicali, tratti e ordine.", readingOnly: "Prima costruisci il riconoscimento - non memorizzare tutto subito",
    studyModel: { eyebrow: "Come guardare", title: "Con un carattere nuovo, fai tre domande", body: "Osserva sempre: forma generale, componenti, pronuncia.", steps: [{ title: "Forma", body: "È sinistra-destra, alto-basso, racchiuso o unitario?" }, { title: "Radicale", body: "Quale parte può suggerire il significato?" }, { title: "Suono", body: "L'indizio sonoro può essere cambiato; conferma col pinyin." }] },
    formation: { eyebrow: "Sistema di scrittura", title: "I caratteri non sono solo piccoli disegni", body: "Un carattere di solito rappresenta una sillaba e un'unità di significato. Molti combinano parte semantica e indizio sonoro.", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "Più utile: significato + suono", body: "Per chi inizia, questo modello conta più che memorizzare allo stesso modo le sei categorie storiche." } },
    radicals: { eyebrow: "Radicali", title: "I radicali aiutano ricerca e memoria", body: "I quaranta radicali iniziali del libro sono mostrati in schede compatte.", tip: "" },
    structures: { eyebrow: "Strutture", title: "Leggi prima il layout", body: "L'obiettivo è vedere da quali blocchi è composto il carattere." },
    strokes: { eyebrow: "Tratti di base", title: "I tratti sono i movimenti minimi", body: "Questi nomi aiutano a riconoscere e cercare i caratteri.", note: "" },
    strokeOrder: { eyebrow: "Ordine dei tratti", title: "L'ordine stabilizza la forma", body: "Aiuta a contare i tratti e capire l'equilibrio.", note: "" },
    typing: { title: "Obiettivo: riconoscere, leggere e digitare", p1: "La scrittura a mano conta, ma il corso privilegia <strong>lettura, ascolto, parlato e input pinyin</strong>.", p2: "Costruisci il modello visivo e usa il pinyin per pronuncia e input." },
    formationTypes: { pictograph: { title: "Pittogrammi", glyphMeaning: "montagna", description: "Caratteri derivati dal contorno di oggetti concreti." }, ideogram: { title: "Ideogrammi semplici", glyphMeaning: "sopra", description: "Segni semplici per relazione o posizione." }, compound: { title: "Ideogrammi composti", glyphMeaning: "luminoso", description: "Componenti di significato si combinano." }, semanticPhonetic: { title: "Semantico-fonetici", glyphMeaning: "fiume", description: "Una parte suggerisce il significato, l'altra il suono storico." }, mutual: { title: "Spiegazione reciproca", glyphMeaning: "vecchio", description: "Categoria storica di caratteri collegati." }, loan: { title: "Prestiti fonetici", glyphMeaning: "venire", description: "Caratteri usati per suoni simili." } },
    exampleMeanings: { person: "persona", mountain: "montagna", sun: "sole", moon: "luna", tree: "albero", above: "sopra", below: "sotto", bright: "luminoso", rest: "riposare", riverJiang: "fiume", riverHe: "fiume", meal: "pasto", aunt: "zia", old: "vecchio", test: "esame", come: "venire", me: "io" }
  },
  id: {
    badge: "Dasar · Karakter", title: "Bagaimana aksara Tionghoa dibentuk", subtitle: "Peta Basic halaman 13-17: bentuk dulu, lalu radikal, goresan, dan urutan.", readingOnly: "Bangun pola pengenalan dulu - tidak perlu hafal semua",
    studyModel: { eyebrow: "Cara melihat", title: "Saat melihat karakter baru, ajukan tiga pertanyaan", body: "Lihat bentuk utuh, bagian-bagian, lalu bunyi.", steps: [{ title: "Bentuk", body: "Kiri-kanan, atas-bawah, mengurung, atau tunggal?" }, { title: "Radikal", body: "Bagian mana yang memberi petunjuk makna?" }, { title: "Bunyi", body: "Petunjuk bunyi bisa berubah; cek dengan pinyin." }] },
    formation: { eyebrow: "Sistem tulisan", title: "Karakter bukan sekadar gambar kecil", body: "Satu karakter biasanya mewakili satu suku kata dan satu unit makna. Banyak karakter menggabungkan bagian makna dan petunjuk bunyi.", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "Paling berguna: makna + bunyi", body: "Untuk pemula, pola ini lebih berguna daripada menghafal enam kategori sejarah secara merata." } },
    radicals: { eyebrow: "Radikal", title: "Radikal membantu mencari dan mengingat", body: "Empat puluh radikal dasar dari buku disusun sebagai kartu ringkas.", tip: "" },
    structures: { eyebrow: "Struktur", title: "Baca tata letaknya dulu", body: "Tujuannya melihat karakter tersusun dari blok apa saja." },
    strokes: { eyebrow: "Goresan dasar", title: "Goresan adalah gerakan terkecil", body: "Nama-nama ini membantu mengenali dan mencari karakter.", note: "" },
    strokeOrder: { eyebrow: "Urutan goresan", title: "Urutan menstabilkan bentuk", body: "Membantu menghitung goresan, kamus, dan keseimbangan bentuk.", note: "" },
    typing: { title: "Tujuan: mengenali, membaca, mengetik", p1: "Tulisan tangan penting, tetapi kursus ini fokus pada <strong>membaca, mendengar, berbicara, dan mengetik pinyin</strong>.", p2: "Bangun model visual, lalu gunakan pinyin untuk bunyi dan input." },
    formationTypes: { pictograph: { title: "Piktograf", glyphMeaning: "gunung", description: "Karakter dari garis bentuk benda nyata." }, ideogram: { title: "Ideogram sederhana", glyphMeaning: "atas", description: "Tanda sederhana untuk relasi atau posisi." }, compound: { title: "Ideogram gabungan", glyphMeaning: "terang", description: "Komponen makna digabungkan." }, semanticPhonetic: { title: "Semantik-fonetik", glyphMeaning: "sungai", description: "Satu bagian makna, satu bagian bunyi historis." }, mutual: { title: "Penjelasan timbal balik", glyphMeaning: "tua", description: "Kategori historis karakter terkait." }, loan: { title: "Pinjaman fonetik", glyphMeaning: "datang", description: "Karakter dipakai karena bunyi mirip." } },
    exampleMeanings: { person: "orang", mountain: "gunung", sun: "matahari", moon: "bulan", tree: "pohon", above: "atas", below: "bawah", bright: "terang", rest: "istirahat", riverJiang: "sungai", riverHe: "sungai", meal: "makanan", aunt: "bibi", old: "tua", test: "ujian", come: "datang", me: "saya" }
  },
  ms: {
    badge: "Asas · Aksara", title: "Bagaimana aksara Cina dibina", subtitle: "Peta Basic halaman 13-17: bentuk dahulu, kemudian radikal, strok dan urutan.", readingOnly: "Bina pengecaman dahulu - tidak perlu hafal semuanya",
    studyModel: { eyebrow: "Cara melihat", title: "Apabila melihat aksara baharu, tanya tiga soalan", body: "Lihat bentuk keseluruhan, komponen, kemudian bunyi.", steps: [{ title: "Bentuk", body: "Kiri-kanan, atas-bawah, mengepung atau tunggal?" }, { title: "Radikal", body: "Bahagian mana memberi petunjuk makna?" }, { title: "Bunyi", body: "Petunjuk bunyi boleh berubah; sahkan dengan pinyin." }] },
    formation: { eyebrow: "Sistem tulisan", title: "Aksara bukan sekadar gambar kecil", body: "Satu aksara biasanya mewakili satu suku kata dan satu unit makna. Banyak aksara menggabungkan bahagian makna dan petunjuk bunyi.", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "Paling berguna: makna + bunyi", body: "Untuk pemula, corak ini lebih berguna daripada menghafal semua kategori sejarah secara sama rata." } },
    radicals: { eyebrow: "Radikal", title: "Radikal membantu mencari dan mengingat", body: "Empat puluh radikal asas buku dipaparkan sebagai kad ringkas.", tip: "" },
    structures: { eyebrow: "Struktur", title: "Baca susun atur dahulu", body: "Matlamatnya melihat aksara dibina daripada blok apa." },
    strokes: { eyebrow: "Strok asas", title: "Strok ialah gerakan terkecil", body: "Nama ini membantu mengenali dan mencari aksara.", note: "" },
    strokeOrder: { eyebrow: "Urutan strok", title: "Urutan menstabilkan bentuk", body: "Membantu mengira strok, menggunakan kamus dan memahami imbangan.", note: "" },
    typing: { title: "Matlamat: kenal, baca dan taip", p1: "Tulisan tangan penting, tetapi kursus ini fokus pada <strong>membaca, mendengar, bertutur dan menaip pinyin</strong>.", p2: "Bina model visual dahulu, kemudian gunakan pinyin untuk bunyi dan input." },
    formationTypes: { pictograph: { title: "Piktograf", glyphMeaning: "gunung", description: "Aksara daripada garis bentuk benda nyata." }, ideogram: { title: "Ideogram mudah", glyphMeaning: "atas", description: "Tanda mudah untuk hubungan atau kedudukan." }, compound: { title: "Ideogram gabungan", glyphMeaning: "terang", description: "Komponen makna digabungkan." }, semanticPhonetic: { title: "Semantik-fonetik", glyphMeaning: "sungai", description: "Satu bahagian makna, satu bahagian bunyi sejarah." }, mutual: { title: "Penjelasan bersama", glyphMeaning: "tua", description: "Kategori sejarah aksara berkaitan." }, loan: { title: "Pinjaman fonetik", glyphMeaning: "datang", description: "Aksara digunakan kerana bunyi serupa." } },
    exampleMeanings: { person: "orang", mountain: "gunung", sun: "matahari", moon: "bulan", tree: "pokok", above: "atas", below: "bawah", bright: "terang", rest: "rehat", riverJiang: "sungai", riverHe: "sungai", meal: "makanan", aunt: "mak cik", old: "tua", test: "ujian", come: "datang", me: "saya" }
  },
  ar: {
    badge: "أساس · الأحرف", title: "كيف تُبنى الأحرف الصينية", subtitle: "خريطة لصفحات Basic 13-17: الشكل أولاً، ثم الجذور، فالخطوط وترتيبها.", readingOnly: "ابنِ نموذج التعرّف أولاً - لا تحفظ كل شيء الآن",
    studyModel: { eyebrow: "طريقة النظر", title: "عند رؤية حرف جديد اسأل ثلاثة أسئلة", body: "انظر إلى الشكل العام، ثم الأجزاء، ثم النطق.", steps: [{ title: "الشكل", body: "هل هو يسار-يمين، أعلى-أسفل، محيط، أم مفرد؟" }, { title: "الجذر", body: "أي جزء قد يلمّح إلى المعنى؟" }, { title: "الصوت", body: "قد يتغير الدليل الصوتي؛ تأكد بالبينيين." }] },
    formation: { eyebrow: "نظام الكتابة", title: "الأحرف ليست مجرد صور صغيرة", body: "يمثل الحرف غالباً مقطعاً صوتياً ووحدة معنى. كثير من الأحرف تجمع جزءاً دلالياً ودليلاً صوتياً تاريخياً.", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "الأهم: المعنى + الصوت", body: "للمبتدئين، هذا النمط أنفع من حفظ الفئات التاريخية الست بالتساوي." } },
    radicals: { eyebrow: "الجذور", title: "الجذور تساعد في البحث والتذكر", body: "أربعون جذراً أساسياً من الكتاب معروضة كبطاقات مختصرة.", tip: "" },
    structures: { eyebrow: "البنية", title: "اقرأ الترتيب أولاً", body: "المهم أن ترى من أي كتل يتكوّن الحرف." },
    strokes: { eyebrow: "الخطوط الأساسية", title: "الخط هو أصغر حركة كتابة", body: "هذه الأسماء تساعد على التعرف والبحث.", note: "" },
    strokeOrder: { eyebrow: "ترتيب الخطوط", title: "الترتيب يثبت الشكل", body: "يساعد على عدّ الخطوط واستخدام القاموس وفهم التوازن.", note: "" },
    typing: { title: "الهدف: التعرّف والقراءة والكتابة بلوحة المفاتيح", p1: "الكتابة اليدوية مهمة، لكن الدورة تركز على <strong>القراءة والاستماع والكلام والإدخال بالبينيين</strong>.", p2: "ابنِ النموذج البصري أولاً، ثم استخدم البينيين للنطق والإدخال." },
    formationTypes: { pictograph: { title: "تصويرية", glyphMeaning: "جبل", description: "أحرف تطورت من ملامح أشياء ملموسة." }, ideogram: { title: "رمزية بسيطة", glyphMeaning: "فوق", description: "علامات بسيطة للعلاقة أو الموضع." }, compound: { title: "رمزية مركبة", glyphMeaning: "مشرق", description: "تتحد أجزاء المعنى لتكوين معنى جديد." }, semanticPhonetic: { title: "دلالية-صوتية", glyphMeaning: "نهر", description: "جزء للمعنى وجزء للصوت التاريخي." }, mutual: { title: "شرح متبادل", glyphMeaning: "قديم", description: "فئة تاريخية لأحرف مرتبطة." }, loan: { title: "استعارة صوتية", glyphMeaning: "يأتي", description: "استعمال حرف لصوت مشابه." } },
    exampleMeanings: { person: "شخص", mountain: "جبل", sun: "شمس", moon: "قمر", tree: "شجرة", above: "فوق", below: "تحت", bright: "مشرق", rest: "راحة", riverJiang: "نهر", riverHe: "نهر", meal: "وجبة", aunt: "عمة/خالة", old: "قديم", test: "اختبار", come: "يأتي", me: "أنا" }
  },
  th: {
    badge: "พื้นฐาน · ตัวอักษร", title: "อักษรจีนประกอบขึ้นอย่างไร", subtitle: "แผนที่จาก Basic หน้า 13-17: ดูรูปก่อน แล้วค่อยดูหมวดนำ นับเส้น และลำดับเส้น", readingOnly: "สร้างแบบจำการจำก่อน - ยังไม่ต้องท่องทั้งหมด",
    studyModel: { eyebrow: "วิธีมอง", title: "เจอตัวใหม่ ให้ถามสามข้อ", body: "มองตามลำดับ: รูปรวม ส่วนประกอบ แล้วเสียงอ่าน", steps: [{ title: "รูปร่าง", body: "ซ้าย-ขวา บน-ล่าง ล้อมรอบ หรือเดี่ยว?" }, { title: "หมวดนำ", body: "ส่วนไหนอาจบอกความหมาย?" }, { title: "เสียง", body: "เบาะแสเสียงอาจเปลี่ยนไป ตรวจด้วยพินอิน" }] },
    formation: { eyebrow: "ระบบตัวเขียน", title: "อักษรจีนไม่ใช่แค่รูปภาพเล็กๆ", body: "ตัวอักษรมักแทนหนึ่งพยางค์และหนึ่งหน่วยความหมาย หลายตัวรวมส่วนบอกความหมายกับเบาะแสเสียง", note: "", priority: { ...HANZI_INTRO_TRANSLATIONS.en.formation.priority, title: "สำคัญที่สุด: ความหมาย + เสียง", body: "สำหรับผู้เริ่มต้น แบบนี้มีประโยชน์กว่าการท่องหกหมวดเท่าๆ กัน" } },
    radicals: { eyebrow: "หมวดนำ", title: "หมวดนำช่วยค้นและจำ", body: "หมวดนำพื้นฐาน 40 ตัวจากหนังสือจัดเป็นการ์ดสั้นๆ", tip: "" },
    structures: { eyebrow: "โครงสร้าง", title: "อ่านผังตัวก่อน", body: "เป้าหมายคือเห็นว่าตัวอักษรมาจากบล็อกใดบ้าง" },
    strokes: { eyebrow: "เส้นพื้นฐาน", title: "เส้นคือการเคลื่อนไหวเล็กที่สุด", body: "ชื่อเส้นช่วยจำแนกและค้นตัวอักษร", note: "" },
    strokeOrder: { eyebrow: "ลำดับเส้น", title: "ลำดับเส้นทำให้รูปมั่นคง", body: "ช่วยนับเส้น ค้นพจนานุกรม และเข้าใจสมดุล", note: "" },
    typing: { title: "เป้าหมาย: จำ อ่าน และพิมพ์", p1: "การเขียนมือสำคัญ แต่คอร์สนี้เน้น <strong>อ่าน ฟัง พูด และพิมพ์ด้วยพินอิน</strong>", p2: "สร้างภาพจำก่อน แล้วใช้พินอินกับเสียงอ่านและการพิมพ์" },
    formationTypes: { pictograph: { title: "รูปภาพ", glyphMeaning: "ภูเขา", description: "ตัวที่พัฒนาจากรูปสิ่งของจริง" }, ideogram: { title: "สัญลักษณ์ง่าย", glyphMeaning: "บน", description: "เครื่องหมายง่ายๆ บอกตำแหน่งหรือความสัมพันธ์" }, compound: { title: "รวมความหมาย", glyphMeaning: "สว่าง", description: "ส่วนที่มีความหมายรวมกันเป็นความหมายใหม่" }, semanticPhonetic: { title: "ความหมาย-เสียง", glyphMeaning: "แม่น้ำ", description: "ส่วนหนึ่งบอกความหมาย อีกส่วนบอกเสียงเก่า" }, mutual: { title: "อธิบายร่วม", glyphMeaning: "แก่", description: "หมวดประวัติศาสตร์ของตัวที่เกี่ยวข้องกัน" }, loan: { title: "ยืมเสียง", glyphMeaning: "มา", description: "ยืมตัวที่เสียงคล้ายกันมาใช้" } },
    exampleMeanings: { person: "คน", mountain: "ภูเขา", sun: "ดวงอาทิตย์", moon: "ดวงจันทร์", tree: "ต้นไม้", above: "บน", below: "ล่าง", bright: "สว่าง", rest: "พัก", riverJiang: "แม่น้ำ", riverHe: "แม่น้ำ", meal: "อาหาร", aunt: "ป้า/น้า", old: "แก่", test: "สอบ", come: "มา", me: "ฉัน" }
  }
});

const HANZI_EXTRA_RADICAL_MEANINGS = {
  ru: ["человек", "нож", "сила", "рука/снова", "рот", "ограда", "земля", "закат", "большой", "женщина", "ребенок", "мера", "маленький", "работа", "крошечный", "лук", "сердце", "оружие", "рука", "солнце", "луна/тело", "дерево", "вода", "огонь", "поле", "глаз", "знак", "шелк", "ухо", "одежда", "речь", "ценность", "идти", "стопа", "металл", "дверь", "птица", "дождь", "еда", "лошадь"],
  es: ["persona", "cuchillo", "fuerza", "mano/otra vez", "boca", "recinto", "tierra", "atardecer", "grande", "mujer", "niño", "medida", "pequeño", "trabajo", "diminuto", "arco", "corazón", "arma antigua", "mano", "sol", "luna/cuerpo", "madera", "agua", "fuego", "campo", "ojo", "mostrar", "seda", "oreja", "ropa", "habla", "valor", "caminar", "pie", "metal", "puerta", "ave", "lluvia", "comida", "caballo"],
  jp: ["人", "刀", "力", "手/また", "口", "囲み", "土", "夕方", "大きい", "女", "子ども", "寸法", "小さい", "仕事", "小さい", "弓", "心", "武器", "手", "太陽", "月/体", "木", "水", "火", "田", "目", "示す", "糸", "耳", "衣服", "言葉", "価値", "歩く", "足", "金属", "門", "鳥", "雨", "食べ物", "馬"],
  ko: ["사람", "칼", "힘", "손/다시", "입", "둘러쌈", "흙", "저녁", "크다", "여자", "아이", "치수", "작다", "일", "작음", "활", "마음", "무기", "손", "해", "달/몸", "나무", "물", "불", "밭", "눈", "보이다", "실", "귀", "옷", "말", "가치", "걷다", "발", "금속", "문", "새", "비", "음식", "말"],
  vi: ["người", "dao", "sức mạnh", "tay/lại", "miệng", "bao quanh", "đất", "hoàng hôn", "lớn", "phụ nữ", "trẻ em", "tấc", "nhỏ", "công việc", "nhỏ xíu", "cung", "tim", "vũ khí", "tay", "mặt trời", "trăng/thân thể", "gỗ", "nước", "lửa", "ruộng", "mắt", "chỉ ra", "tơ", "tai", "áo", "lời nói", "giá trị", "đi", "chân", "kim loại", "cửa", "chim", "mưa", "thức ăn", "ngựa"],
  pt: ["pessoa", "faca", "força", "mão/de novo", "boca", "cercado", "terra", "pôr do sol", "grande", "mulher", "criança", "medida", "pequeno", "trabalho", "minúsculo", "arco", "coração", "arma antiga", "mão", "sol", "lua/corpo", "madeira", "água", "fogo", "campo", "olho", "mostrar", "seda", "orelha", "roupa", "fala", "valor", "andar", "pé", "metal", "porta", "ave", "chuva", "comida", "cavalo"],
  it: ["persona", "coltello", "forza", "mano/di nuovo", "bocca", "recinto", "terra", "tramonto", "grande", "donna", "bambino", "misura", "piccolo", "lavoro", "minuscolo", "arco", "cuore", "arma antica", "mano", "sole", "luna/corpo", "legno", "acqua", "fuoco", "campo", "occhio", "mostrare", "seta", "orecchio", "vestito", "parola", "valore", "camminare", "piede", "metallo", "porta", "uccello", "pioggia", "cibo", "cavallo"],
  id: ["orang", "pisau", "kekuatan", "tangan/lagi", "mulut", "kurungan", "tanah", "senja", "besar", "perempuan", "anak", "ukuran", "kecil", "kerja", "mungil", "busur", "hati", "senjata", "tangan", "matahari", "bulan/tubuh", "kayu", "air", "api", "ladang", "mata", "menunjukkan", "sutra", "telinga", "pakaian", "ucapan", "nilai", "berjalan", "kaki", "logam", "pintu", "burung", "hujan", "makanan", "kuda"],
  ms: ["orang", "pisau", "kuasa", "tangan/lagi", "mulut", "kepungan", "tanah", "senja", "besar", "wanita", "kanak-kanak", "ukuran", "kecil", "kerja", "halus", "busur", "hati", "senjata", "tangan", "matahari", "bulan/tubuh", "kayu", "air", "api", "sawah", "mata", "menunjukkan", "sutera", "telinga", "pakaian", "pertuturan", "nilai", "berjalan", "kaki", "logam", "pintu", "burung", "hujan", "makanan", "kuda"],
  ar: ["شخص", "سكين", "قوة", "يد/مرة أخرى", "فم", "إحاطة", "أرض", "غروب", "كبير", "امرأة", "طفل", "مقياس", "صغير", "عمل", "دقيق", "قوس", "قلب", "سلاح", "يد", "شمس", "قمر/جسم", "خشب", "ماء", "نار", "حقل", "عين", "إظهار", "حرير", "أذن", "ملابس", "كلام", "قيمة", "مشي", "قدم", "معدن", "باب", "طائر", "مطر", "طعام", "حصان"],
  th: ["คน", "มีด", "แรง", "มือ/อีกครั้ง", "ปาก", "ล้อม", "ดิน", "ยามเย็น", "ใหญ่", "ผู้หญิง", "เด็ก", "หน่วยวัด", "เล็ก", "งาน", "เล็กมาก", "ธนู", "ใจ", "อาวุธ", "มือ", "ดวงอาทิตย์", "ดวงจันทร์/ร่างกาย", "ไม้", "น้ำ", "ไฟ", "นา", "ตา", "แสดง", "ไหม", "หู", "เสื้อผ้า", "คำพูด", "มูลค่า", "เดิน", "เท้า", "โลหะ", "ประตู", "นก", "ฝน", "อาหาร", "ม้า"]
};

Object.entries(HANZI_EXTRA_RADICAL_MEANINGS).forEach(([locale, meanings]) => {
  HANZI_EXTRA_LOCALE_COPY[locale].radicalMeanings = meanings;
});

["ru", "es", "jp", "ko", "vi", "pt", "it", "id", "ms", "ar", "th"].forEach((locale) => {
  HANZI_INTRO_TRANSLATIONS[locale] = buildHanziIntroFromCopy(HANZI_EXTRA_LOCALE_COPY[locale], locale);
});

const TYPING_INTRO_TRANSLATIONS = {
  "en": {
    "back": "Back",
    "finish": "Finish",
    "badge": "Foundation · Typing",
    "title": "Typing Chinese with pinyin",
    "subtitle": "Set up an input method, type pronunciation, choose the right characters, and handle the small traps that beginners meet first.",
    "setupTitle": "Set up the Chinese keyboard once",
    "setupLead": "You do not need a special physical keyboard. Add a Simplified Chinese Pinyin input method to your operating system, then switch to it when you want to type Chinese.",
    "platforms": [
      [
        "Windows",
        [
          "Open Settings.",
          "Go to Time & language.",
          "Open Language & region.",
          "Add Chinese (Simplified).",
          "In keyboard options, choose Microsoft Pinyin.",
          "Switch to the Chinese keyboard from the taskbar language button.",
          "Inside Microsoft Pinyin, press Shift to switch Chinese/English mode."
        ]
      ],
      [
        "macOS",
        [
          "Open System Settings.",
          "Go to Keyboard.",
          "Open Input Sources.",
          "Click + and add Chinese, Simplified Pinyin.",
          "Use the menu-bar input icon or Control + Space to switch input sources.",
          "Type pinyin in any text field; the candidate window appears automatically."
        ]
      ],
      [
        "Phones",
        [
          "Open your system keyboard settings.",
          "Add a Chinese keyboard.",
          "Choose Pinyin or Simplified Chinese Pinyin.",
          "Open any app with a text box.",
          "Long-press the globe key or keyboard switch key.",
          "Select the Chinese Pinyin keyboard and start typing."
        ]
      ]
    ],
    "flowTitle": "The everyday typing flow",
    "flow": [
      [
        "Type pinyin",
        "Type the sound without tone marks: nihao, xiexie, zhongwen. Modern IMEs understand full syllables and whole phrases."
      ],
      [
        "Read candidates",
        "A candidate window appears. The first option is often right, but always check similar words."
      ],
      [
        "Choose",
        "Press Space for the highlighted candidate, press a number for a specific candidate, or use arrow keys to move."
      ],
      [
        "Confirm or keep English",
        "Enter usually keeps the raw letters instead of converting them, which is useful for names, URLs, and English words."
      ]
    ],
    "demoTitle": "Try these keystrokes",
    "demos": [
      [
        "nihao",
        "你好",
        "Type the whole greeting, then Space."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "Whole-sentence input is usually easier than one character at a time."
      ],
      [
        "nv",
        "女",
        "Use v when pinyin needs ü."
      ],
      [
        "lü / lv",
        "绿",
        "In most IMEs, lv gives lü. After j/q/x, type u: ju, qu, xu."
      ]
    ],
    "specialTitle": "The v = ü rule",
    "specialBody": "Standard keyboards do not have a convenient ü key, and Mandarin pinyin does not use the letter v. That is why most pinyin input methods use v as the typing code for ü.",
    "specialExamples": [
      "nǚ → nv → 女",
      "lǜ → lv → 绿",
      "lüè → lve → 略"
    ],
    "skillsTitle": "Important habits",
    "skills": [
      [
        "Type phrases, not isolated characters",
        "“wo yao he shui” gives the IME more context than “wo / yao / he / shui”."
      ],
      [
        "Ignore tones while typing",
        "For normal Chinese IME input, type pinyin letters without tone marks. Use candidates and context to choose the word."
      ],
      [
        "Use apostrophes for ambiguity",
        "If syllables can be split wrongly, add an apostrophe: xi'an for 西安."
      ],
      [
        "Learn punctuation switching",
        "Chinese mode usually gives Chinese punctuation. Windows also supports Ctrl + . for Chinese/English punctuation."
      ],
      [
        "Watch full-width mode",
        "If letters or punctuation suddenly look too wide, switch back to half-width mode."
      ],
      [
        "Let the IME learn",
        "Frequently used words move upward over time, so your candidate list becomes more personal."
      ]
    ],
    "pitfallsTitle": "When something feels wrong",
    "pitfalls": [
      [
        "You type letters only",
        "You may be in English mode. Switch to Chinese mode or change the active keyboard."
      ],
      [
        "The wrong character appears",
        "Use the number keys or arrows to choose a different candidate. Type a longer phrase for more context."
      ],
      [
        "ü words fail",
        "Use v: nv, lv, lve. For j/q/x, type u: ju, qu, xu."
      ],
      [
        "Punctuation looks strange",
        "You may be using Chinese punctuation or full-width mode. Toggle punctuation or width settings."
      ]
    ]
  },
  "zh": {
    "back": "返回",
    "finish": "完成",
    "badge": "基础 · 打字",
    "title": "用拼音输入中文",
    "subtitle": "先设置输入法，再用拼音打出读音、选择正确汉字，并处理初学者最容易卡住的几个小问题。",
    "setupTitle": "先把中文键盘设置好",
    "setupLead": "不需要特殊键盘。只要在系统里添加“简体中文拼音输入法”，需要打中文时切换过去就可以。",
    "platforms": [
      [
        "Windows",
        [
          "打开系统“设置”。",
          "进入“时间和语言”。",
          "进入“语言和区域”。",
          "添加“中文（简体）”。",
          "在键盘选项里选择 Microsoft Pinyin。",
          "从任务栏语言按钮切换到中文键盘。",
          "在 Microsoft Pinyin 内部，可以按 Shift 切换中英文模式。"
        ]
      ],
      [
        "macOS",
        [
          "打开“系统设置”。",
          "进入“键盘”。",
          "打开“输入法 / Input Sources”。",
          "点击 +，添加中文“简体拼音”。",
          "用菜单栏输入法图标或 Control + Space 切换输入法。",
          "在任意文本框输入拼音，候选窗口会自动出现。"
        ]
      ],
      [
        "手机",
        [
          "打开系统键盘设置。",
          "添加中文键盘。",
          "选择“拼音”或“简体中文拼音”。",
          "打开任意可以输入文字的 App。",
          "长按地球键或输入法切换键。",
          "选择中文拼音键盘，然后开始输入。"
        ]
      ]
    ],
    "flowTitle": "日常输入流程",
    "flow": [
      [
        "输入拼音",
        "不输入声调，直接打 nihao、xiexie、zhongwen。现代输入法可以理解完整音节和整句。"
      ],
      [
        "查看候选",
        "候选窗口会显示可能的汉字。第一个常常是对的，但相近词一定要看清。"
      ],
      [
        "选择汉字",
        "空格选择当前高亮候选，数字键选择指定候选，方向键移动候选。"
      ],
      [
        "确认或保留英文",
        "Enter 通常会保留你输入的英文字母，适合人名、网址和英文词。"
      ]
    ],
    "demoTitle": "可以先练这几组",
    "demos": [
      [
        "nihao",
        "你好",
        "整句打完再按空格。"
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "整句输入通常比一个字一个字选更容易。"
      ],
      [
        "nv",
        "女",
        "拼音里需要 ü 时，用 v 来输入。"
      ],
      [
        "lv",
        "绿",
        "多数输入法里 lv 就是 lü。j/q/x 后面写 u：ju、qu、xu。"
      ]
    ],
    "specialTitle": "v = ü 这条规则",
    "specialBody": "普通键盘没有方便的 ü 键，而且汉语拼音不用字母 v，所以大多数拼音输入法都用 v 代表 ü。",
    "specialExamples": [
      "nǚ → nv → 女",
      "lǜ → lv → 绿",
      "lüè → lve → 略"
    ],
    "skillsTitle": "重要习惯",
    "skills": [
      [
        "尽量输入词组/整句",
        "“wo yao he shui” 比 “wo / yao / he / shui” 给输入法更多上下文。"
      ],
      [
        "打字时不用输声调",
        "正常中文输入法里只打拼音字母，不打声调；靠候选词和上下文选字。"
      ],
      [
        "歧义处用 apostrophe",
        "音节容易切错时加 apostrophe，比如 xi'an 表示 西安。"
      ],
      [
        "熟悉标点切换",
        "中文模式常会输出中文标点。Windows 还可以用 Ctrl + . 切换中英文标点。"
      ],
      [
        "注意全角/半角",
        "如果字母或标点突然变宽，可能进入了全角模式，要切回半角。"
      ],
      [
        "让输入法学习你",
        "常用词会逐渐排到前面，候选列表会越来越符合你的习惯。"
      ]
    ],
    "pitfallsTitle": "常见问题",
    "pitfalls": [
      [
        "只出现英文字母",
        "可能还在英文模式，切换到中文模式或切换当前键盘。"
      ],
      [
        "出来的字不对",
        "用数字键或方向键选其他候选；输入更长词组会更准。"
      ],
      [
        "ü 相关词打不出来",
        "用 v：nv、lv、lve。j/q/x 后面直接用 u：ju、qu、xu。"
      ],
      [
        "标点看起来不对",
        "可能是中文标点或全角模式，切换标点/宽度设置。"
      ]
    ]
  },
  "fr": {
    "platforms": [
      [
        "Windows",
        [
          "Ouvrez Paramètres.",
          "Allez dans Heure et langue.",
          "Ouvrez Langue et région.",
          "Ajoutez Chinois (simplifié).",
          "Dans les options du clavier, choisissez Microsoft Pinyin.",
          "Basculez vers le clavier chinois depuis la barre des tâches.",
          "Dans Microsoft Pinyin, appuyez sur Shift pour passer entre chinois et anglais."
        ]
      ],
      [
        "macOS",
        [
          "Ouvrez Réglages Système.",
          "Allez dans Clavier.",
          "Ouvrez Sources d’entrée.",
          "Cliquez sur + et ajoutez Chinois, Pinyin simplifié.",
          "Utilisez l’icône de saisie dans la barre de menu ou Control + Espace.",
          "Tapez du pinyin dans un champ de texte ; la fenêtre de candidats apparaît."
        ]
      ],
      [
        "Téléphones",
        [
          "Ouvrez les réglages du clavier.",
          "Ajoutez un clavier chinois.",
          "Choisissez Pinyin ou Chinois simplifié Pinyin.",
          "Ouvrez une app avec un champ de texte.",
          "Maintenez la touche globe ou changement de clavier.",
          "Sélectionnez le clavier pinyin chinois et commencez à taper."
        ]
      ]
    ],
    "flow": [
      [
        "Taper le pinyin",
        "Tapez le son sans tons : nihao, xiexie, zhongwen. Les IME modernes comprennent les syllabes et les phrases entières."
      ],
      [
        "Lire les candidats",
        "Une fenêtre propose des caractères. Le premier est souvent correct, mais vérifiez les mots similaires."
      ],
      [
        "Choisir",
        "Appuyez sur Espace pour le candidat surligné, sur un chiffre pour un candidat précis, ou utilisez les flèches."
      ],
      [
        "Confirmer ou garder l’anglais",
        "Entrée garde souvent les lettres brutes, utile pour les noms, URL et mots anglais."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "Tapez toute la salutation, puis Espace."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "La phrase entière est souvent plus facile que caractère par caractère."
      ],
      [
        "nv",
        "女",
        "Utilisez v quand le pinyin demande ü."
      ],
      [
        "lü / lv",
        "绿",
        "Dans la plupart des IME, lv donne lü. Après j/q/x, tapez u : ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "Tapez des groupes de mots",
        "“wo yao he shui” donne plus de contexte que “wo / yao / he / shui”."
      ],
      [
        "Ignorez les tons",
        "Dans un IME chinois normal, tapez les lettres du pinyin sans marques de ton."
      ],
      [
        "Utilisez l’apostrophe en cas d’ambiguïté",
        "Si les syllabes peuvent être mal coupées, ajoutez une apostrophe : xi'an pour 西安."
      ],
      [
        "Apprenez les signes de ponctuation",
        "Le mode chinois produit souvent une ponctuation chinoise. Windows prend aussi Ctrl + . en charge."
      ],
      [
        "Surveillez le mode pleine largeur",
        "Si les lettres deviennent trop larges, repassez en demi-largeur."
      ],
      [
        "Laissez l’IME apprendre",
        "Les mots fréquents montent dans la liste avec le temps."
      ]
    ],
    "pitfalls": [
      [
        "Vous ne tapez que des lettres",
        "Vous êtes peut-être en mode anglais. Passez en mode chinois ou changez de clavier actif."
      ],
      [
        "Le mauvais caractère apparaît",
        "Utilisez les chiffres ou les flèches pour choisir un autre candidat. Tapez une phrase plus longue."
      ],
      [
        "Les mots avec ü échouent",
        "Utilisez v : nv, lv, lve. Après j/q/x, tapez u : ju, qu, xu."
      ],
      [
        "La ponctuation semble étrange",
        "Vous utilisez peut-être la ponctuation chinoise ou le mode pleine largeur."
      ]
    ]
  },
  "de": {
    "platforms": [
      [
        "Windows",
        [
          "Öffne die Einstellungen.",
          "Gehe zu Zeit und Sprache.",
          "Öffne Sprache und Region.",
          "Füge Chinesisch (vereinfacht) hinzu.",
          "Wähle in den Tastaturoptionen Microsoft Pinyin.",
          "Wechsle über die Sprachschaltfläche in der Taskleiste.",
          "In Microsoft Pinyin schaltet Shift zwischen Chinesisch und Englisch um."
        ]
      ],
      [
        "macOS",
        [
          "Öffne Systemeinstellungen.",
          "Gehe zu Tastatur.",
          "Öffne Eingabequellen.",
          "Klicke auf + und füge Chinesisch, vereinfachtes Pinyin hinzu.",
          "Wechsle über das Eingabesymbol oder Control + Leertaste.",
          "Tippe Pinyin in ein Textfeld; das Kandidatenfenster erscheint automatisch."
        ]
      ],
      [
        "Telefone",
        [
          "Öffne die Tastatureinstellungen.",
          "Füge eine chinesische Tastatur hinzu.",
          "Wähle Pinyin oder vereinfachtes Chinesisch Pinyin.",
          "Öffne eine App mit Textfeld.",
          "Halte die Globus- oder Tastaturwechseltaste gedrückt.",
          "Wähle die chinesische Pinyin-Tastatur und tippe los."
        ]
      ]
    ],
    "flow": [
      [
        "Pinyin tippen",
        "Tippe ohne Tonzeichen: nihao, xiexie, zhongwen. Moderne IMEs verstehen Silben und ganze Phrasen."
      ],
      [
        "Kandidaten lesen",
        "Ein Kandidatenfenster erscheint. Der erste Vorschlag ist oft richtig, aber prüfe ähnliche Wörter."
      ],
      [
        "Auswählen",
        "Leertaste übernimmt den markierten Kandidaten, Zahlen wählen gezielt, Pfeiltasten bewegen die Auswahl."
      ],
      [
        "Bestätigen oder Englisch behalten",
        "Enter behält oft die Rohbuchstaben, praktisch für Namen, URLs und englische Wörter."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "Tippe die ganze Begrüßung und dann Leertaste."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "Ganze Sätze sind meist leichter als einzelne Zeichen."
      ],
      [
        "nv",
        "女",
        "Nutze v, wenn Pinyin ü braucht."
      ],
      [
        "lü / lv",
        "绿",
        "In den meisten IMEs ergibt lv lü. Nach j/q/x tippst du u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "Phrasen statt Einzelzeichen tippen",
        "“wo yao he shui” gibt dem IME mehr Kontext."
      ],
      [
        "Töne beim Tippen ignorieren",
        "Für normale IME-Eingabe tippst du Pinyin ohne Tonzeichen."
      ],
      [
        "Apostroph bei Mehrdeutigkeit nutzen",
        "Wenn Silben falsch getrennt werden könnten: xi'an für 西安."
      ],
      [
        "Interpunktion kennen",
        "Der chinesische Modus nutzt oft chinesische Satzzeichen. Windows unterstützt auch Ctrl + ."
      ],
      [
        "Vollbreite beachten",
        "Wenn Zeichen plötzlich breit wirken, zurück in den Halbbreitenmodus wechseln."
      ],
      [
        "Das IME lernen lassen",
        "Häufige Wörter wandern mit der Zeit nach oben."
      ]
    ],
    "pitfalls": [
      [
        "Es erscheinen nur Buchstaben",
        "Du bist vielleicht im Englischmodus. Wechsle in den Chinesischmodus oder zur aktiven Tastatur."
      ],
      [
        "Das falsche Zeichen erscheint",
        "Wähle mit Zahlen oder Pfeilen einen anderen Kandidaten. Mehr Kontext hilft."
      ],
      [
        "ü-Wörter funktionieren nicht",
        "Nutze v: nv, lv, lve. Nach j/q/x: ju, qu, xu."
      ],
      [
        "Satzzeichen sehen seltsam aus",
        "Vielleicht ist chinesische Interpunktion oder Vollbreite aktiv."
      ]
    ]
  },
  "jp": {
    "platforms": [
      [
        "Windows",
        [
          "設定を開きます。",
          "時刻と言語へ進みます。",
          "言語と地域を開きます。",
          "中国語（簡体字）を追加します。",
          "キーボード オプションで Microsoft Pinyin を選びます。",
          "タスクバーの言語ボタンから中国語キーボードに切り替えます。",
          "Microsoft Pinyin 内では Shift で中国語/英語モードを切り替えます。"
        ]
      ],
      [
        "macOS",
        [
          "システム設定を開きます。",
          "キーボードへ進みます。",
          "入力ソースを開きます。",
          "+ をクリックして中国語・簡体字 Pinyin を追加します。",
          "メニューバーの入力アイコン、または Control + Space で切り替えます。",
          "テキスト欄にピンインを入力すると候補ウィンドウが出ます。"
        ]
      ],
      [
        "スマホ",
        [
          "キーボード設定を開きます。",
          "中国語キーボードを追加します。",
          "Pinyin または簡体字中国語 Pinyin を選びます。",
          "テキスト入力できるアプリを開きます。",
          "地球キーまたはキーボード切替キーを長押しします。",
          "中国語 Pinyin キーボードを選んで入力します。"
        ]
      ]
    ],
    "flow": [
      [
        "ピンインを入力",
        "声調記号なしで nihao, xiexie, zhongwen と入力します。最近の IME は音節や文全体を理解します。"
      ],
      [
        "候補を見る",
        "候補ウィンドウが出ます。最初の候補が正しいことも多いですが、似た語は確認します。"
      ],
      [
        "選ぶ",
        "Space で選択中の候補、数字で特定候補、矢印キーで移動します。"
      ],
      [
        "確定または英字のまま",
        "Enter は変換せず英字を残すことが多く、名前や URL に便利です。"
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "あいさつ全体を打ってから Space。"
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "一文字ずつより文全体で打つ方が簡単です。"
      ],
      [
        "nv",
        "女",
        "ü が必要な時は v を使います。"
      ],
      [
        "lü / lv",
        "绿",
        "多くの IME では lv が lü になります。j/q/x の後は u: ju, qu, xu。"
      ]
    ],
    "skills": [
      [
        "単字ではなく語句で入力",
        "“wo yao he shui” は “wo / yao / he / shui” より文脈が多いです。"
      ],
      [
        "声調は入力しない",
        "通常の中国語 IME では声調記号なしでピンイン文字だけ入力します。"
      ],
      [
        "曖昧な所はアポストロフィ",
        "音節の切れ目が曖昧なら xi'an のようにします。"
      ],
      [
        "句読点切替に慣れる",
        "中国語モードでは中国語の句読点になります。Windows では Ctrl + . も使えます。"
      ],
      [
        "全角モードに注意",
        "文字が急に広く見えたら半角に戻します。"
      ],
      [
        "IME に学習させる",
        "よく使う語は徐々に上位に出ます。"
      ]
    ],
    "pitfalls": [
      [
        "英字だけ出る",
        "英語モードかもしれません。中国語モードまたは入力ソースを切り替えます。"
      ],
      [
        "違う漢字が出る",
        "数字や矢印で別候補を選び、長めの語句で入力します。"
      ],
      [
        "ü の語が出ない",
        "v を使います: nv, lv, lve。j/q/x の後は u。"
      ],
      [
        "句読点が変に見える",
        "中国語句読点または全角モードかもしれません。"
      ]
    ]
  },
  "ko": {
    "platforms": [
      [
        "Windows",
        [
          "설정을 엽니다.",
          "시간 및 언어로 이동합니다.",
          "언어 및 지역을 엽니다.",
          "중국어(간체)를 추가합니다.",
          "키보드 옵션에서 Microsoft Pinyin을 선택합니다.",
          "작업 표시줄의 언어 버튼으로 중국어 키보드로 전환합니다.",
          "Microsoft Pinyin 안에서는 Shift로 중국어/영어 모드를 바꿉니다."
        ]
      ],
      [
        "macOS",
        [
          "시스템 설정을 엽니다.",
          "키보드로 이동합니다.",
          "입력 소스를 엽니다.",
          "+를 눌러 중국어 간체 Pinyin을 추가합니다.",
          "메뉴 막대 입력 아이콘이나 Control + Space로 전환합니다.",
          "텍스트 칸에 병음을 입력하면 후보 창이 나타납니다."
        ]
      ],
      [
        "휴대폰",
        [
          "키보드 설정을 엽니다.",
          "중국어 키보드를 추가합니다.",
          "Pinyin 또는 중국어 간체 Pinyin을 선택합니다.",
          "텍스트 입력 앱을 엽니다.",
          "지구본 키나 키보드 전환 키를 길게 누릅니다.",
          "중국어 Pinyin 키보드를 선택하고 입력합니다."
        ]
      ]
    ],
    "flow": [
      [
        "병음 입력",
        "성조 표시 없이 nihao, xiexie, zhongwen처럼 입력합니다. 최신 IME는 음절과 문장을 이해합니다."
      ],
      [
        "후보 확인",
        "후보 창이 나타납니다. 첫 후보가 맞을 때가 많지만 비슷한 단어는 확인하세요."
      ],
      [
        "선택",
        "스페이스는 강조된 후보, 숫자는 특정 후보, 화살표는 이동입니다."
      ],
      [
        "확정 또는 영어 유지",
        "Enter는 보통 원래 알파벳을 유지하므로 이름, URL, 영어 단어에 유용합니다."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "인사말 전체를 입력한 뒤 Space."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "한 글자씩보다 문장 전체 입력이 보통 쉽습니다."
      ],
      [
        "nv",
        "女",
        "ü가 필요할 때 v를 씁니다."
      ],
      [
        "lü / lv",
        "绿",
        "대부분 IME에서 lv는 lü입니다. j/q/x 뒤에는 u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "낱글자보다 구절 입력",
        "“wo yao he shui”가 더 많은 문맥을 줍니다."
      ],
      [
        "입력할 때 성조는 무시",
        "일반 중국어 IME에서는 성조 없이 병음 글자만 입력합니다."
      ],
      [
        "모호하면 apostrophe 사용",
        "음절이 잘못 나뉠 수 있으면 xi'an처럼 씁니다."
      ],
      [
        "문장부호 전환 익히기",
        "중국어 모드는 보통 중국어 문장부호를 냅니다. Windows는 Ctrl + . 도 지원합니다."
      ],
      [
        "전각 모드 주의",
        "글자나 문장부호가 갑자기 넓으면 반각으로 전환하세요."
      ],
      [
        "IME가 배우게 두기",
        "자주 쓰는 단어는 시간이 지나며 위로 올라갑니다."
      ]
    ],
    "pitfalls": [
      [
        "알파벳만 입력됨",
        "영어 모드일 수 있습니다. 중국어 모드나 활성 키보드를 바꾸세요."
      ],
      [
        "틀린 한자가 나옴",
        "숫자나 화살표로 다른 후보를 고르고 더 긴 구절을 입력하세요."
      ],
      [
        "ü 단어가 안 됨",
        "v를 쓰세요: nv, lv, lve. j/q/x 뒤에는 u."
      ],
      [
        "문장부호가 이상함",
        "중국어 문장부호나 전각 모드일 수 있습니다."
      ]
    ]
  },
  "es": {
    "platforms": [
      [
        "Windows",
        [
          "Abre Configuración.",
          "Ve a Hora e idioma.",
          "Abre Idioma y región.",
          "Añade Chino (simplificado).",
          "En opciones de teclado, elige Microsoft Pinyin.",
          "Cambia al teclado chino desde la barra de tareas.",
          "Dentro de Microsoft Pinyin, pulsa Shift para alternar chino/inglés."
        ]
      ],
      [
        "macOS",
        [
          "Abre Ajustes del Sistema.",
          "Ve a Teclado.",
          "Abre Fuentes de entrada.",
          "Pulsa + y añade Chino, Pinyin simplificado.",
          "Usa el icono de entrada o Control + Espacio.",
          "Escribe pinyin en un campo de texto; aparecerán candidatos."
        ]
      ],
      [
        "Teléfonos",
        [
          "Abre los ajustes del teclado.",
          "Añade un teclado chino.",
          "Elige Pinyin o Chino simplificado Pinyin.",
          "Abre una app con campo de texto.",
          "Mantén pulsada la tecla globo o cambio de teclado.",
          "Selecciona el teclado chino Pinyin y empieza."
        ]
      ]
    ],
    "flow": [
      [
        "Escribe pinyin",
        "Escribe el sonido sin tonos: nihao, xiexie, zhongwen. Los IME modernos entienden sílabas y frases."
      ],
      [
        "Lee candidatos",
        "Aparece una ventana de candidatos. El primero suele ser correcto, pero revisa palabras similares."
      ],
      [
        "Elige",
        "Espacio acepta el candidato resaltado, un número elige uno específico y las flechas mueven la selección."
      ],
      [
        "Confirma o conserva inglés",
        "Enter suele mantener las letras sin convertir, útil para nombres, URL y palabras inglesas."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "Escribe todo el saludo y luego Espacio."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "Escribir la frase completa suele ser más fácil que carácter por carácter."
      ],
      [
        "nv",
        "女",
        "Usa v cuando el pinyin necesita ü."
      ],
      [
        "lü / lv",
        "绿",
        "En la mayoría de IME, lv produce lü. Después de j/q/x, escribe u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "Escribe frases, no caracteres aislados",
        "“wo yao he shui” da más contexto al IME."
      ],
      [
        "Ignora los tonos al escribir",
        "En un IME normal se escribe pinyin sin marcas de tono."
      ],
      [
        "Usa apóstrofos si hay ambigüedad",
        "Si las sílabas pueden dividirse mal, usa xi'an para 西安."
      ],
      [
        "Aprende el cambio de puntuación",
        "El modo chino suele producir puntuación china. Windows también tiene Ctrl + ."
      ],
      [
        "Vigila el modo ancho completo",
        "Si letras o signos se ven demasiado anchos, vuelve a medio ancho."
      ],
      [
        "Deja que el IME aprenda",
        "Las palabras frecuentes suben con el tiempo."
      ]
    ],
    "pitfalls": [
      [
        "Solo salen letras",
        "Quizá estás en modo inglés. Cambia al modo chino o al teclado activo correcto."
      ],
      [
        "Aparece el carácter equivocado",
        "Usa números o flechas para elegir otro candidato. Una frase más larga ayuda."
      ],
      [
        "Fallan palabras con ü",
        "Usa v: nv, lv, lve. Después de j/q/x, usa u."
      ],
      [
        "La puntuación se ve rara",
        "Puede ser puntuación china o modo ancho completo."
      ]
    ]
  },
  "vi": {
    "platforms": [
      [
        "Windows",
        [
          "Mở Settings.",
          "Vào Time & language.",
          "Mở Language & region.",
          "Thêm Chinese (Simplified).",
          "Trong tùy chọn bàn phím, chọn Microsoft Pinyin.",
          "Chuyển sang bàn phím tiếng Trung từ nút ngôn ngữ trên thanh tác vụ.",
          "Trong Microsoft Pinyin, nhấn Shift để đổi chế độ Trung/Anh."
        ]
      ],
      [
        "macOS",
        [
          "Mở System Settings.",
          "Vào Keyboard.",
          "Mở Input Sources.",
          "Bấm + và thêm Chinese, Simplified Pinyin.",
          "Dùng biểu tượng bộ gõ trên thanh menu hoặc Control + Space.",
          "Gõ pinyin trong ô văn bản; cửa sổ ứng viên sẽ hiện ra."
        ]
      ],
      [
        "Điện thoại",
        [
          "Mở cài đặt bàn phím.",
          "Thêm bàn phím tiếng Trung.",
          "Chọn Pinyin hoặc Chinese Simplified Pinyin.",
          "Mở app có ô nhập chữ.",
          "Nhấn giữ phím quả địa cầu hoặc phím đổi bàn phím.",
          "Chọn bàn phím Chinese Pinyin và bắt đầu gõ."
        ]
      ]
    ],
    "flow": [
      [
        "Gõ pinyin",
        "Gõ âm không dấu thanh: nihao, xiexie, zhongwen. Bộ gõ hiện đại hiểu âm tiết và cả cụm câu."
      ],
      [
        "Đọc ứng viên",
        "Cửa sổ ứng viên xuất hiện. Mục đầu thường đúng, nhưng hãy kiểm tra từ gần giống."
      ],
      [
        "Chọn",
        "Space chọn ứng viên đang tô sáng, số chọn mục cụ thể, phím mũi tên để di chuyển."
      ],
      [
        "Xác nhận hoặc giữ tiếng Anh",
        "Enter thường giữ nguyên chữ cái, hữu ích cho tên, URL và từ tiếng Anh."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "Gõ cả lời chào rồi nhấn Space."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "Gõ cả câu thường dễ hơn chọn từng chữ."
      ],
      [
        "nv",
        "女",
        "Dùng v khi pinyin cần ü."
      ],
      [
        "lü / lv",
        "绿",
        "Hầu hết bộ gõ hiểu lv là lü. Sau j/q/x, gõ u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "Gõ cụm từ, không gõ từng chữ rời",
        "“wo yao he shui” cho bộ gõ nhiều ngữ cảnh hơn."
      ],
      [
        "Bỏ qua dấu thanh khi gõ",
        "Bộ gõ tiếng Trung bình thường chỉ cần chữ pinyin không dấu thanh."
      ],
      [
        "Dùng apostrophe khi mơ hồ",
        "Nếu âm tiết dễ bị tách sai, thêm apostrophe: xi'an cho 西安."
      ],
      [
        "Học cách đổi dấu câu",
        "Chế độ tiếng Trung thường tạo dấu câu tiếng Trung. Windows hỗ trợ Ctrl + ."
      ],
      [
        "Chú ý chế độ full-width",
        "Nếu chữ hoặc dấu câu bỗng rộng hơn, đổi về half-width."
      ],
      [
        "Để bộ gõ học thói quen",
        "Từ hay dùng sẽ dần lên cao trong danh sách."
      ]
    ],
    "pitfalls": [
      [
        "Chỉ ra chữ cái",
        "Có thể bạn đang ở chế độ tiếng Anh. Hãy đổi sang chế độ tiếng Trung hoặc bàn phím đang dùng."
      ],
      [
        "Ra sai chữ Hán",
        "Dùng số hoặc mũi tên để chọn ứng viên khác. Gõ cụm dài hơn sẽ chính xác hơn."
      ],
      [
        "Từ có ü không ra",
        "Dùng v: nv, lv, lve. Sau j/q/x, gõ u."
      ],
      [
        "Dấu câu trông lạ",
        "Có thể đang dùng dấu câu tiếng Trung hoặc chế độ full-width."
      ]
    ]
  },
  "pt": {
    "platforms": [
      [
        "Windows",
        [
          "Abra as Configurações.",
          "Vá para Hora e idioma.",
          "Abra Idioma e região.",
          "Adicione Chinês (simplificado).",
          "Nas opções de teclado, escolha Microsoft Pinyin.",
          "Troque para o teclado chinês pelo botão de idioma da barra de tarefas.",
          "No Microsoft Pinyin, pressione Shift para alternar chinês/inglês."
        ]
      ],
      [
        "macOS",
        [
          "Abra Ajustes do Sistema.",
          "Vá para Teclado.",
          "Abra Fontes de entrada.",
          "Clique em + e adicione Chinês, Pinyin simplificado.",
          "Use o ícone de entrada na barra de menu ou Control + Espaço.",
          "Digite pinyin em qualquer campo; a janela de candidatos aparece."
        ]
      ],
      [
        "Telefones",
        [
          "Abra as configurações do teclado.",
          "Adicione um teclado chinês.",
          "Escolha Pinyin ou Chinês simplificado Pinyin.",
          "Abra um app com caixa de texto.",
          "Mantenha pressionada a tecla globo ou troca de teclado.",
          "Selecione o teclado chinês Pinyin e comece."
        ]
      ]
    ],
    "flow": [
      [
        "Digite pinyin",
        "Digite o som sem tons: nihao, xiexie, zhongwen. IMEs modernos entendem sílabas e frases inteiras."
      ],
      [
        "Leia candidatos",
        "Uma janela de candidatos aparece. A primeira opção costuma estar certa, mas confira palavras parecidas."
      ],
      [
        "Escolha",
        "Espaço aceita o candidato destacado, números escolhem candidatos específicos e setas movem a seleção."
      ],
      [
        "Confirme ou mantenha inglês",
        "Enter geralmente mantém as letras cruas, útil para nomes, URLs e palavras em inglês."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "Digite a saudação inteira e depois Espaço."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "Digitar a frase inteira costuma ser mais fácil que caractere por caractere."
      ],
      [
        "nv",
        "女",
        "Use v quando o pinyin precisa de ü."
      ],
      [
        "lü / lv",
        "绿",
        "Na maioria dos IMEs, lv gera lü. Depois de j/q/x, digite u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "Digite frases, não caracteres isolados",
        "“wo yao he shui” dá mais contexto ao IME."
      ],
      [
        "Ignore tons ao digitar",
        "No IME chinês normal, digite pinyin sem marcas de tom."
      ],
      [
        "Use apóstrofo para ambiguidade",
        "Se as sílabas podem ser separadas errado, use xi'an para 西安."
      ],
      [
        "Aprenda a alternar pontuação",
        "O modo chinês geralmente produz pontuação chinesa. Windows também aceita Ctrl + ."
      ],
      [
        "Observe o modo largura total",
        "Se letras ou pontuação ficarem largas, volte para meia largura."
      ],
      [
        "Deixe o IME aprender",
        "Palavras frequentes sobem na lista com o tempo."
      ]
    ],
    "pitfalls": [
      [
        "Só aparecem letras",
        "Talvez você esteja no modo inglês. Troque para chinês ou para o teclado ativo correto."
      ],
      [
        "Aparece o caractere errado",
        "Use números ou setas para outro candidato. Digite uma frase mais longa."
      ],
      [
        "Palavras com ü falham",
        "Use v: nv, lv, lve. Depois de j/q/x, use u."
      ],
      [
        "A pontuação parece estranha",
        "Pode ser pontuação chinesa ou modo largura total."
      ]
    ]
  },
  "ru": {
    "platforms": [
      [
        "Windows",
        [
          "Откройте Параметры.",
          "Перейдите в Время и язык.",
          "Откройте Язык и регион.",
          "Добавьте Китайский (упрощённый).",
          "В параметрах клавиатуры выберите Microsoft Pinyin.",
          "Переключитесь на китайскую клавиатуру через кнопку языка на панели задач.",
          "В Microsoft Pinyin нажмите Shift для режима китайский/английский."
        ]
      ],
      [
        "macOS",
        [
          "Откройте Системные настройки.",
          "Перейдите в Клавиатура.",
          "Откройте Источники ввода.",
          "Нажмите + и добавьте Китайский, упрощённый Pinyin.",
          "Используйте значок ввода в меню или Control + Space.",
          "Введите пиньинь в поле текста; появится окно кандидатов."
        ]
      ],
      [
        "Телефоны",
        [
          "Откройте настройки клавиатуры.",
          "Добавьте китайскую клавиатуру.",
          "Выберите Pinyin или Chinese Simplified Pinyin.",
          "Откройте приложение с полем ввода.",
          "Удерживайте клавишу глобуса или смены клавиатуры.",
          "Выберите китайскую Pinyin-клавиатуру и начните ввод."
        ]
      ]
    ],
    "flow": [
      [
        "Введите пиньинь",
        "Пишите звук без тонов: nihao, xiexie, zhongwen. Современные IME понимают слоги и целые фразы."
      ],
      [
        "Читайте кандидаты",
        "Появится окно вариантов. Первый часто верный, но похожие слова нужно проверять."
      ],
      [
        "Выберите",
        "Пробел выбирает выделенный вариант, цифра — конкретный вариант, стрелки двигают выбор."
      ],
      [
        "Подтвердите или оставьте английский",
        "Enter часто оставляет исходные буквы, что удобно для имён, URL и английских слов."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "Введите всё приветствие, затем Пробел."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "Целую фразу обычно вводить легче, чем по одному иероглифу."
      ],
      [
        "nv",
        "女",
        "Используйте v, когда нужен ü."
      ],
      [
        "lü / lv",
        "绿",
        "В большинстве IME lv даёт lü. После j/q/x вводите u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "Вводите фразы, а не отдельные знаки",
        "“wo yao he shui” даёт IME больше контекста."
      ],
      [
        "Игнорируйте тоны при вводе",
        "В обычном китайском IME вводят пиньинь без тоновых знаков."
      ],
      [
        "Используйте апостроф при неоднозначности",
        "Если слоги могут разделиться неверно, пишите xi'an для 西安."
      ],
      [
        "Освойте переключение пунктуации",
        "Китайский режим часто даёт китайскую пунктуацию. В Windows есть Ctrl + ."
      ],
      [
        "Следите за полноширинным режимом",
        "Если буквы или знаки стали широкими, вернитесь в полуширинный режим."
      ],
      [
        "Дайте IME учиться",
        "Частые слова со временем поднимаются выше."
      ]
    ],
    "pitfalls": [
      [
        "Появляются только буквы",
        "Возможно, включён английский режим. Переключитесь на китайский или нужную клавиатуру."
      ],
      [
        "Появился неправильный иероглиф",
        "Выберите другой вариант цифрами или стрелками. Более длинная фраза поможет."
      ],
      [
        "Не работают слова с ü",
        "Используйте v: nv, lv, lve. После j/q/x — u."
      ],
      [
        "Пунктуация выглядит странно",
        "Возможно, включена китайская пунктуация или полноширинный режим."
      ]
    ]
  },
  "id": {
    "platforms": [
      [
        "Windows",
        [
          "Buka Settings.",
          "Masuk ke Time & language.",
          "Buka Language & region.",
          "Tambahkan Chinese (Simplified).",
          "Di opsi keyboard, pilih Microsoft Pinyin.",
          "Pindah ke keyboard Mandarin dari tombol bahasa di taskbar.",
          "Di Microsoft Pinyin, tekan Shift untuk berganti mode Mandarin/Inggris."
        ]
      ],
      [
        "macOS",
        [
          "Buka System Settings.",
          "Masuk ke Keyboard.",
          "Buka Input Sources.",
          "Klik + dan tambahkan Chinese, Simplified Pinyin.",
          "Gunakan ikon input di menu bar atau Control + Space.",
          "Ketik pinyin di kotak teks; jendela kandidat muncul otomatis."
        ]
      ],
      [
        "Ponsel",
        [
          "Buka pengaturan keyboard.",
          "Tambahkan keyboard Mandarin.",
          "Pilih Pinyin atau Chinese Simplified Pinyin.",
          "Buka app dengan kotak teks.",
          "Tekan lama tombol globe atau tombol ganti keyboard.",
          "Pilih keyboard Chinese Pinyin dan mulai mengetik."
        ]
      ]
    ],
    "flow": [
      [
        "Ketik pinyin",
        "Ketik bunyi tanpa tanda nada: nihao, xiexie, zhongwen. IME modern memahami suku kata dan frasa penuh."
      ],
      [
        "Baca kandidat",
        "Jendela kandidat muncul. Opsi pertama sering benar, tetapi periksa kata yang mirip."
      ],
      [
        "Pilih",
        "Space memilih kandidat yang disorot, angka memilih kandidat tertentu, panah memindahkan pilihan."
      ],
      [
        "Konfirmasi atau biarkan Inggris",
        "Enter biasanya mempertahankan huruf mentah, berguna untuk nama, URL, dan kata Inggris."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "Ketik seluruh sapaan, lalu Space."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "Mengetik kalimat penuh biasanya lebih mudah daripada satu karakter."
      ],
      [
        "nv",
        "女",
        "Gunakan v saat pinyin membutuhkan ü."
      ],
      [
        "lü / lv",
        "绿",
        "Di kebanyakan IME, lv menghasilkan lü. Setelah j/q/x, ketik u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "Ketik frasa, bukan karakter terpisah",
        "“wo yao he shui” memberi IME lebih banyak konteks."
      ],
      [
        "Abaikan nada saat mengetik",
        "Untuk IME Mandarin biasa, ketik huruf pinyin tanpa tanda nada."
      ],
      [
        "Gunakan apostrof untuk ambiguitas",
        "Jika suku kata bisa terpisah salah, gunakan xi'an untuk 西安."
      ],
      [
        "Pelajari pengalihan tanda baca",
        "Mode Mandarin biasanya menghasilkan tanda baca Mandarin. Windows juga mendukung Ctrl + ."
      ],
      [
        "Perhatikan mode full-width",
        "Jika huruf atau tanda baca tiba-tiba lebar, kembali ke half-width."
      ],
      [
        "Biarkan IME belajar",
        "Kata yang sering dipakai akan naik dari waktu ke waktu."
      ]
    ],
    "pitfalls": [
      [
        "Hanya huruf yang muncul",
        "Anda mungkin berada di mode Inggris. Pindah ke mode Mandarin atau keyboard aktif yang benar."
      ],
      [
        "Karakter salah muncul",
        "Gunakan angka atau panah untuk kandidat lain. Ketik frasa lebih panjang."
      ],
      [
        "Kata ü gagal",
        "Gunakan v: nv, lv, lve. Setelah j/q/x, gunakan u."
      ],
      [
        "Tanda baca terlihat aneh",
        "Mungkin tanda baca Mandarin atau mode full-width sedang aktif."
      ]
    ]
  },
  "ms": {
    "platforms": [
      [
        "Windows",
        [
          "Buka Settings.",
          "Pergi ke Time & language.",
          "Buka Language & region.",
          "Tambah Chinese (Simplified).",
          "Dalam pilihan papan kekunci, pilih Microsoft Pinyin.",
          "Tukar ke papan kekunci Cina melalui butang bahasa di taskbar.",
          "Dalam Microsoft Pinyin, tekan Shift untuk tukar mod Cina/Inggeris."
        ]
      ],
      [
        "macOS",
        [
          "Buka System Settings.",
          "Pergi ke Keyboard.",
          "Buka Input Sources.",
          "Klik + dan tambah Chinese, Simplified Pinyin.",
          "Guna ikon input pada menu bar atau Control + Space.",
          "Taip pinyin dalam kotak teks; tetingkap calon akan muncul."
        ]
      ],
      [
        "Telefon",
        [
          "Buka tetapan papan kekunci.",
          "Tambah papan kekunci Cina.",
          "Pilih Pinyin atau Chinese Simplified Pinyin.",
          "Buka app yang ada kotak teks.",
          "Tekan lama kekunci globe atau tukar papan kekunci.",
          "Pilih papan kekunci Chinese Pinyin dan mula menaip."
        ]
      ]
    ],
    "flow": [
      [
        "Taip pinyin",
        "Taip bunyi tanpa tanda nada: nihao, xiexie, zhongwen. IME moden faham suku kata dan frasa penuh."
      ],
      [
        "Baca calon",
        "Tetingkap calon muncul. Pilihan pertama kerap betul, tetapi semak perkataan yang hampir sama."
      ],
      [
        "Pilih",
        "Space memilih calon yang disorot, nombor memilih calon tertentu, anak panah menggerakkan pilihan."
      ],
      [
        "Sahkan atau kekalkan Inggeris",
        "Enter biasanya mengekalkan huruf asal, berguna untuk nama, URL dan perkataan Inggeris."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "Taip seluruh sapaan, kemudian Space."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "Menaip ayat penuh biasanya lebih mudah daripada satu aksara."
      ],
      [
        "nv",
        "女",
        "Guna v apabila pinyin memerlukan ü."
      ],
      [
        "lü / lv",
        "绿",
        "Dalam kebanyakan IME, lv menjadi lü. Selepas j/q/x, taip u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "Taip frasa, bukan aksara terpencil",
        "“wo yao he shui” memberi IME lebih banyak konteks."
      ],
      [
        "Abaikan nada semasa menaip",
        "Untuk IME Cina biasa, taip huruf pinyin tanpa tanda nada."
      ],
      [
        "Guna apostrophe untuk kekaburan",
        "Jika suku kata boleh dipisah salah, guna xi'an untuk 西安."
      ],
      [
        "Belajar tukar tanda baca",
        "Mod Cina biasanya menghasilkan tanda baca Cina. Windows juga menyokong Ctrl + ."
      ],
      [
        "Perhatikan mod lebar penuh",
        "Jika huruf atau tanda baca tiba-tiba lebar, tukar semula ke separuh lebar."
      ],
      [
        "Biarkan IME belajar",
        "Perkataan yang kerap digunakan akan naik dalam senarai."
      ]
    ],
    "pitfalls": [
      [
        "Hanya huruf muncul",
        "Anda mungkin dalam mod Inggeris. Tukar ke mod Cina atau papan kekunci aktif yang betul."
      ],
      [
        "Aksara salah muncul",
        "Guna nombor atau anak panah untuk calon lain. Taip frasa lebih panjang."
      ],
      [
        "Perkataan ü gagal",
        "Guna v: nv, lv, lve. Selepas j/q/x, guna u."
      ],
      [
        "Tanda baca kelihatan pelik",
        "Mungkin tanda baca Cina atau mod lebar penuh sedang aktif."
      ]
    ]
  },
  "it": {
    "platforms": [
      [
        "Windows",
        [
          "Apri Impostazioni.",
          "Vai a Ora e lingua.",
          "Apri Lingua e area geografica.",
          "Aggiungi Cinese (semplificato).",
          "Nelle opzioni tastiera scegli Microsoft Pinyin.",
          "Passa alla tastiera cinese dal pulsante lingua nella barra delle applicazioni.",
          "In Microsoft Pinyin, premi Shift per alternare cinese/inglese."
        ]
      ],
      [
        "macOS",
        [
          "Apri Impostazioni di Sistema.",
          "Vai a Tastiera.",
          "Apri Sorgenti di input.",
          "Clicca + e aggiungi Cinese, Pinyin semplificato.",
          "Usa l’icona input nella barra menu o Control + Spazio.",
          "Digita pinyin in un campo di testo; appare la finestra dei candidati."
        ]
      ],
      [
        "Telefoni",
        [
          "Apri le impostazioni della tastiera.",
          "Aggiungi una tastiera cinese.",
          "Scegli Pinyin o Cinese semplificato Pinyin.",
          "Apri un’app con campo di testo.",
          "Tieni premuto il tasto globo o cambio tastiera.",
          "Seleziona la tastiera cinese Pinyin e inizia."
        ]
      ]
    ],
    "flow": [
      [
        "Digita pinyin",
        "Digita il suono senza toni: nihao, xiexie, zhongwen. Gli IME moderni capiscono sillabe e frasi intere."
      ],
      [
        "Leggi i candidati",
        "Compare una finestra di candidati. Il primo è spesso giusto, ma controlla parole simili."
      ],
      [
        "Scegli",
        "Spazio accetta il candidato evidenziato, un numero sceglie un candidato specifico, le frecce spostano la selezione."
      ],
      [
        "Conferma o lascia inglese",
        "Invio spesso mantiene le lettere grezze, utile per nomi, URL e parole inglesi."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "Digita tutto il saluto, poi Spazio."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "Digitare una frase intera è spesso più facile che un carattere alla volta."
      ],
      [
        "nv",
        "女",
        "Usa v quando il pinyin richiede ü."
      ],
      [
        "lü / lv",
        "绿",
        "Nella maggior parte degli IME, lv dà lü. Dopo j/q/x, digita u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "Digita frasi, non caratteri isolati",
        "“wo yao he shui” dà più contesto all’IME."
      ],
      [
        "Ignora i toni mentre digiti",
        "Nel normale IME cinese si digitano lettere pinyin senza segni di tono."
      ],
      [
        "Usa apostrofi per ambiguità",
        "Se le sillabe possono essere divise male, usa xi'an per 西安."
      ],
      [
        "Impara la punteggiatura",
        "Il modo cinese spesso produce punteggiatura cinese. Windows supporta anche Ctrl + ."
      ],
      [
        "Controlla il modo full-width",
        "Se lettere o segni diventano larghi, torna a half-width."
      ],
      [
        "Lascia che l’IME impari",
        "Le parole frequenti salgono nella lista nel tempo."
      ]
    ],
    "pitfalls": [
      [
        "Compaiono solo lettere",
        "Potresti essere in modo inglese. Passa al modo cinese o alla tastiera corretta."
      ],
      [
        "Compare il carattere sbagliato",
        "Usa numeri o frecce per un altro candidato. Una frase più lunga aiuta."
      ],
      [
        "Le parole con ü falliscono",
        "Usa v: nv, lv, lve. Dopo j/q/x, usa u."
      ],
      [
        "La punteggiatura sembra strana",
        "Potrebbe essere punteggiatura cinese o modo full-width."
      ]
    ]
  },
  "ar": {
    "platforms": [
      [
        "Windows",
        [
          "افتح الإعدادات.",
          "انتقل إلى الوقت واللغة.",
          "افتح اللغة والمنطقة.",
          "أضف الصينية (المبسطة).",
          "في خيارات لوحة المفاتيح اختر Microsoft Pinyin.",
          "بدّل إلى لوحة المفاتيح الصينية من زر اللغة في شريط المهام.",
          "داخل Microsoft Pinyin اضغط Shift للتبديل بين الصينية والإنجليزية."
        ]
      ],
      [
        "macOS",
        [
          "افتح إعدادات النظام.",
          "انتقل إلى لوحة المفاتيح.",
          "افتح مصادر الإدخال.",
          "اضغط + وأضف الصينية، Pinyin مبسط.",
          "استخدم أيقونة الإدخال في شريط القائمة أو Control + Space.",
          "اكتب pinyin في أي حقل نص؛ ستظهر نافذة المرشحات."
        ]
      ],
      [
        "الهواتف",
        [
          "افتح إعدادات لوحة المفاتيح.",
          "أضف لوحة مفاتيح صينية.",
          "اختر Pinyin أو Chinese Simplified Pinyin.",
          "افتح تطبيقًا يحتوي على مربع نص.",
          "اضغط مطولًا على زر الكرة الأرضية أو زر تبديل اللوحة.",
          "اختر لوحة Chinese Pinyin وابدأ الكتابة."
        ]
      ]
    ],
    "flow": [
      [
        "اكتب pinyin",
        "اكتب الصوت دون علامات النغمة: nihao, xiexie, zhongwen. طرق الإدخال الحديثة تفهم المقاطع والعبارات الكاملة."
      ],
      [
        "اقرأ المرشحات",
        "تظهر نافذة مرشحات. الخيار الأول غالبًا صحيح، لكن تحقق من الكلمات المتشابهة."
      ],
      [
        "اختر",
        "المسافة تختار المرشح المحدد، والأرقام تختار مرشحًا معينًا، والأسهم تنقل الاختيار."
      ],
      [
        "أكد أو أبقِ الإنجليزية",
        "Enter غالبًا يبقي الحروف كما هي، وهذا مفيد للأسماء والروابط والكلمات الإنجليزية."
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "اكتب التحية كاملة ثم اضغط Space."
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "كتابة الجملة كاملة أسهل غالبًا من اختيار كل حرف وحده."
      ],
      [
        "nv",
        "女",
        "استخدم v عندما يحتاج pinyin إلى ü."
      ],
      [
        "lü / lv",
        "绿",
        "في معظم طرق الإدخال، lv يعطي lü. بعد j/q/x اكتب u: ju, qu, xu."
      ]
    ],
    "skills": [
      [
        "اكتب عبارات لا حروفًا منفردة",
        "“wo yao he shui” يعطي طريقة الإدخال سياقًا أكثر."
      ],
      [
        "تجاهل النغمات أثناء الكتابة",
        "في الإدخال الصيني العادي تكتب حروف pinyin دون علامات نغمة."
      ],
      [
        "استخدم الفاصلة العليا عند الالتباس",
        "إذا قد تُقسّم المقاطع خطأ، اكتب xi'an من أجل 西安."
      ],
      [
        "تعلّم تبديل علامات الترقيم",
        "الوضع الصيني ينتج غالبًا ترقيمًا صينيًا. Windows يدعم Ctrl + . أيضًا."
      ],
      [
        "انتبه لوضع العرض الكامل",
        "إذا بدت الحروف أو العلامات عريضة جدًا، عد إلى الوضع نصف العرض."
      ],
      [
        "دع طريقة الإدخال تتعلم",
        "الكلمات المتكررة ترتفع في القائمة مع الوقت."
      ]
    ],
    "pitfalls": [
      [
        "تظهر حروف فقط",
        "قد تكون في الوضع الإنجليزي. بدّل إلى الوضع الصيني أو لوحة المفاتيح الصحيحة."
      ],
      [
        "ظهر الحرف الخطأ",
        "استخدم الأرقام أو الأسهم لاختيار مرشح آخر. العبارة الأطول تساعد."
      ],
      [
        "كلمات ü لا تعمل",
        "استخدم v: nv, lv, lve. بعد j/q/x استخدم u."
      ],
      [
        "الترقيم يبدو غريبًا",
        "قد يكون ترقيمًا صينيًا أو وضع العرض الكامل."
      ]
    ]
  },
  "th": {
    "platforms": [
      [
        "Windows",
        [
          "เปิด Settings",
          "ไปที่ Time & language",
          "เปิด Language & region",
          "เพิ่ม Chinese (Simplified)",
          "ในตัวเลือกคีย์บอร์ด เลือก Microsoft Pinyin",
          "สลับไปคีย์บอร์ดจีนจากปุ่มภาษาบนแถบงาน",
          "ใน Microsoft Pinyin กด Shift เพื่อสลับโหมดจีน/อังกฤษ"
        ]
      ],
      [
        "macOS",
        [
          "เปิด System Settings",
          "ไปที่ Keyboard",
          "เปิด Input Sources",
          "กด + แล้วเพิ่ม Chinese, Simplified Pinyin",
          "ใช้ไอคอน input บนแถบเมนูหรือ Control + Space",
          "พิมพ์ pinyin ในช่องข้อความ แล้วหน้าต่างคำ候補จะปรากฏ"
        ]
      ],
      [
        "โทรศัพท์",
        [
          "เปิดการตั้งค่าแป้นพิมพ์",
          "เพิ่มแป้นพิมพ์ภาษาจีน",
          "เลือก Pinyin หรือ Chinese Simplified Pinyin",
          "เปิดแอปที่มีช่องพิมพ์ข้อความ",
          "กดค้างปุ่มรูปโลกหรือปุ่มสลับแป้นพิมพ์",
          "เลือกแป้นพิมพ์ Chinese Pinyin แล้วเริ่มพิมพ์"
        ]
      ]
    ],
    "flow": [
      [
        "พิมพ์ pinyin",
        "พิมพ์เสียงโดยไม่ใส่วรรณยุกต์: nihao, xiexie, zhongwen. IME สมัยใหม่เข้าใจพยางค์และวลีทั้งชุด"
      ],
      [
        "อ่านตัวเลือก",
        "หน้าต่างตัวเลือกจะปรากฏ ตัวแรกมักถูก แต่ควรตรวจคำที่คล้ายกัน"
      ],
      [
        "เลือก",
        "Space เลือกตัวที่ไฮไลต์ ตัวเลขเลือกตัวเฉพาะ ปุ่มลูกศรเลื่อนตัวเลือก"
      ],
      [
        "ยืนยันหรือเก็บอังกฤษไว้",
        "Enter มักเก็บตัวอักษรเดิม เหมาะกับชื่อ URL และคำอังกฤษ"
      ]
    ],
    "demos": [
      [
        "nihao",
        "你好",
        "พิมพ์คำทักทายทั้งหมด แล้วกด Space"
      ],
      [
        "wo xiang xue zhongwen",
        "我想学中文",
        "พิมพ์ทั้งประโยคมักง่ายกว่าทีละตัวอักษรจีน"
      ],
      [
        "nv",
        "女",
        "ใช้ v เมื่อ pinyin ต้องใช้ ü"
      ],
      [
        "lü / lv",
        "绿",
        "ใน IME ส่วนใหญ่ lv จะได้ lü หลัง j/q/x ให้พิมพ์ u: ju, qu, xu"
      ]
    ],
    "skills": [
      [
        "พิมพ์เป็นวลี ไม่ใช่ตัวเดี่ยว",
        "“wo yao he shui” ให้บริบทมากกว่า “wo / yao / he / shui”"
      ],
      [
        "ไม่ต้องใส่วรรณยุกต์ตอนพิมพ์",
        "IME จีนทั่วไปใช้ตัวอักษร pinyin โดยไม่มีเครื่องหมายวรรณยุกต์"
      ],
      [
        "ใช้อะพอสทรอฟีเมื่อกำกวม",
        "ถ้าแบ่งพยางค์ผิดได้ ให้ใช้ xi'an สำหรับ 西安"
      ],
      [
        "เรียนรู้การสลับเครื่องหมายวรรคตอน",
        "โหมดจีนมักให้วรรคตอนจีน Windows ยังใช้ Ctrl + . ได้"
      ],
      [
        "ระวังโหมด full-width",
        "ถ้าตัวอักษรหรือวรรคตอนกว้างผิดปกติ ให้กลับเป็น half-width"
      ],
      [
        "ให้ IME เรียนรู้",
        "คำที่ใช้บ่อยจะค่อย ๆ ขยับขึ้นในรายการ"
      ]
    ],
    "pitfalls": [
      [
        "ขึ้นแต่ตัวอักษร",
        "อาจอยู่ในโหมดอังกฤษ ให้สลับเป็นโหมดจีนหรือคีย์บอร์ดที่ถูกต้อง"
      ],
      [
        "ตัวอักษรจีนไม่ถูก",
        "ใช้ตัวเลขหรือลูกศรเลือก候補อื่น พิมพ์วลียาวขึ้นจะช่วยได้"
      ],
      [
        "คำที่มี ü ใช้ไม่ได้",
        "ใช้ v: nv, lv, lve หลัง j/q/x ใช้ u"
      ],
      [
        "วรรคตอนดูแปลก",
        "อาจเป็นวรรคตอนจีนหรือโหมด full-width"
      ]
    ]
  }
};

const PINYIN_INTRO_TRANSLATIONS = {
  "en": {
    "overview": "Overview",
    "nativeHint": "Native-language hint",
    "articulation": "How to make the sound",
    "introTitle": "Introduction",
    "introDesc": "Chinese syllables have three parts: an initial, a final, and a tone.",
    "initial": "Initial",
    "final": "Final",
    "tone": "Tone",
    "syllable": "Syllable",
    "initials": "Initials",
    "finals": "Finals",
    "exploreHint": "Tap to listen · click group to explore",
    "detail": "Detail",
    "tonesTitle": "Tones",
    "tonesDesc": "Chinese is a tonal language: the same syllable in different tones means completely different things.",
    "toneNames": [
      "high & level",
      "rising",
      "falling-rising",
      "falling",
      "neutral"
    ],
    "toneMeanings": [
      "mom",
      "hemp",
      "horse",
      "to scold",
      "question particle"
    ],
    "neutralNote": "The neutral tone (5) is short and unstressed; the tone mark is usually omitted in writing."
  },
  "zh": {
    "overview": "概览",
    "nativeHint": "母语提示",
    "articulation": "发音动作",
    "introTitle": "拼音介绍",
    "introDesc": "中文音节由三个部分组成：声母、韵母和声调。",
    "initial": "声母",
    "final": "韵母",
    "tone": "声调",
    "syllable": "音节",
    "initials": "声母",
    "finals": "韵母",
    "exploreHint": "点击试听 · 点击分组查看细节",
    "detail": "详情",
    "tonesTitle": "声调",
    "tonesDesc": "中文是声调语言：同一个音节，声调不同，意思可能完全不同。",
    "toneNames": [
      "第一声：高平",
      "第二声：上扬",
      "第三声：先降后升",
      "第四声：下降",
      "轻声"
    ],
    "toneMeanings": [
      "妈妈",
      "麻",
      "马",
      "骂",
      "疑问助词"
    ],
    "neutralNote": "轻声（第 5 声）短而轻，书写时通常不标声调。"
  },
  "jp": {
    "overview": "概要",
    "nativeHint": "母語ヒント",
    "articulation": "発音の作り方",
    "introTitle": "ピンイン入門",
    "introDesc": "中国語の音節は、声母・韻母・声調の3つでできています。",
    "initial": "声母",
    "final": "韻母",
    "tone": "声調",
    "syllable": "音節",
    "initials": "声母",
    "finals": "韻母",
    "exploreHint": "タップして聞く · グループを開く",
    "detail": "詳細",
    "tonesTitle": "声調",
    "tonesDesc": "中国語は声調言語です。同じ音節でも声調が違うと意味が大きく変わります。",
    "toneNames": [
      "高く平ら",
      "上昇",
      "下降して上昇",
      "下降",
      "軽声"
    ],
    "toneMeanings": [
      "お母さん",
      "麻",
      "馬",
      "叱る",
      "疑問助詞"
    ],
    "neutralNote": "軽声（5）は短く弱く発音され、通常は声調記号を書きません。"
  },
  "fr": {
    "overview": "Aperçu",
    "nativeHint": "Indice en langue maternelle",
    "articulation": "Comment produire le son",
    "introTitle": "Introduction",
    "introDesc": "Les syllabes chinoises ont trois parties : une initiale, une finale et un ton.",
    "initial": "Initiale",
    "final": "Finale",
    "tone": "Ton",
    "syllable": "Syllabe",
    "initials": "Initiales",
    "finals": "Finales",
    "exploreHint": "Touchez pour écouter · ouvrez un groupe",
    "detail": "Détail",
    "tonesTitle": "Tons",
    "tonesDesc": "Le chinois est une langue tonale : la même syllabe peut changer complètement de sens selon le ton.",
    "toneNames": [
      "haut et plat",
      "montant",
      "descendant-montant",
      "descendant",
      "neutre"
    ],
    "toneMeanings": [
      "maman",
      "chanvre",
      "cheval",
      "gronder",
      "particule interrogative"
    ],
    "neutralNote": "Le ton neutre (5) est court et non accentué ; on omet généralement la marque de ton à l’écrit."
  },
  "de": {
    "overview": "Übersicht",
    "nativeHint": "Hinweis in deiner Sprache",
    "articulation": "So bildest du den Laut",
    "introTitle": "Einführung",
    "introDesc": "Chinesische Silben bestehen aus drei Teilen: Anlaut, Auslaut und Ton.",
    "initial": "Anlaut",
    "final": "Auslaut",
    "tone": "Ton",
    "syllable": "Silbe",
    "initials": "Anlaute",
    "finals": "Auslaute",
    "exploreHint": "Antippen zum Hören · Gruppe öffnen",
    "detail": "Details",
    "tonesTitle": "Töne",
    "tonesDesc": "Chinesisch ist eine Tonsprache: dieselbe Silbe kann mit anderem Ton eine völlig andere Bedeutung haben.",
    "toneNames": [
      "hoch und eben",
      "steigend",
      "fallend-steigend",
      "fallend",
      "neutral"
    ],
    "toneMeanings": [
      "Mama",
      "Hanf",
      "Pferd",
      "schimpfen",
      "Fragepartikel"
    ],
    "neutralNote": "Der neutrale Ton (5) ist kurz und unbetont; das Tonzeichen wird beim Schreiben meist weggelassen."
  },
  "ko": {
    "overview": "개요",
    "nativeHint": "모국어 힌트",
    "articulation": "발음 방법",
    "introTitle": "병음 소개",
    "introDesc": "중국어 음절은 성모, 운모, 성조 세 부분으로 이루어집니다.",
    "initial": "성모",
    "final": "운모",
    "tone": "성조",
    "syllable": "음절",
    "initials": "성모",
    "finals": "운모",
    "exploreHint": "눌러 듣기 · 그룹 살펴보기",
    "detail": "자세히",
    "tonesTitle": "성조",
    "tonesDesc": "중국어는 성조 언어입니다. 같은 음절도 성조가 다르면 뜻이 완전히 달라질 수 있습니다.",
    "toneNames": [
      "높고 평평함",
      "올라감",
      "내려갔다 올라감",
      "내려감",
      "경성"
    ],
    "toneMeanings": [
      "엄마",
      "삼",
      "말",
      "꾸짖다",
      "의문 조사"
    ],
    "neutralNote": "경성(5성)은 짧고 약하게 발음되며, 보통 성조 표시를 쓰지 않습니다."
  },
  "es": {
    "overview": "Resumen",
    "nativeHint": "Pista en tu idioma",
    "articulation": "Cómo producir el sonido",
    "introTitle": "Introducción",
    "introDesc": "Las sílabas chinas tienen tres partes: inicial, final y tono.",
    "initial": "Inicial",
    "final": "Final",
    "tone": "Tono",
    "syllable": "Sílaba",
    "initials": "Iniciales",
    "finals": "Finales",
    "exploreHint": "Toca para escuchar · explora el grupo",
    "detail": "Detalle",
    "tonesTitle": "Tonos",
    "tonesDesc": "El chino es una lengua tonal: la misma sílaba puede cambiar por completo de significado según el tono.",
    "toneNames": [
      "alto y plano",
      "ascendente",
      "baja y sube",
      "descendente",
      "neutro"
    ],
    "toneMeanings": [
      "mamá",
      "cáñamo",
      "caballo",
      "regañar",
      "partícula interrogativa"
    ],
    "neutralNote": "El tono neutro (5) es corto y átono; normalmente se omite la marca de tono al escribir."
  },
  "vi": {
    "overview": "Tổng quan",
    "nativeHint": "Gợi ý theo tiếng mẹ đẻ",
    "articulation": "Cách tạo âm",
    "introTitle": "Giới thiệu",
    "introDesc": "Một âm tiết tiếng Trung có ba phần: thanh mẫu, vận mẫu và thanh điệu.",
    "initial": "Thanh mẫu",
    "final": "Vận mẫu",
    "tone": "Thanh điệu",
    "syllable": "Âm tiết",
    "initials": "Thanh mẫu",
    "finals": "Vận mẫu",
    "exploreHint": "Chạm để nghe · mở nhóm để xem",
    "detail": "Chi tiết",
    "tonesTitle": "Thanh điệu",
    "tonesDesc": "Tiếng Trung là ngôn ngữ thanh điệu: cùng một âm tiết nhưng đổi thanh có thể đổi hẳn nghĩa.",
    "toneNames": [
      "cao và ngang",
      "đi lên",
      "xuống rồi lên",
      "đi xuống",
      "nhẹ"
    ],
    "toneMeanings": [
      "mẹ",
      "cây gai",
      "ngựa",
      "mắng",
      "trợ từ nghi vấn"
    ],
    "neutralNote": "Thanh nhẹ (5) ngắn và không nhấn; khi viết thường không ghi dấu thanh."
  },
  "pt": {
    "overview": "Visão geral",
    "nativeHint": "Dica no seu idioma",
    "articulation": "Como produzir o som",
    "introTitle": "Introdução",
    "introDesc": "As sílabas chinesas têm três partes: inicial, final e tom.",
    "initial": "Inicial",
    "final": "Final",
    "tone": "Tom",
    "syllable": "Sílaba",
    "initials": "Iniciais",
    "finals": "Finais",
    "exploreHint": "Toque para ouvir · abra o grupo",
    "detail": "Detalhe",
    "tonesTitle": "Tons",
    "tonesDesc": "O chinês é uma língua tonal: a mesma sílaba pode mudar completamente de sentido conforme o tom.",
    "toneNames": [
      "alto e plano",
      "ascendente",
      "desce e sobe",
      "descendente",
      "neutro"
    ],
    "toneMeanings": [
      "mãe",
      "cânhamo",
      "cavalo",
      "repreender",
      "partícula interrogativa"
    ],
    "neutralNote": "O tom neutro (5) é curto e sem ênfase; normalmente a marca de tom é omitida na escrita."
  },
  "ar": {
    "overview": "نظرة عامة",
    "nativeHint": "تلميح بلغتك",
    "articulation": "طريقة نطق الصوت",
    "introTitle": "مقدمة",
    "introDesc": "يتكوّن المقطع الصيني من ثلاثة أجزاء: صوت ابتدائي، صوت نهائي، ونغمة.",
    "initial": "ابتدائي",
    "final": "نهائي",
    "tone": "النغمة",
    "syllable": "المقطع",
    "initials": "الأصوات الابتدائية",
    "finals": "الأصوات النهائية",
    "exploreHint": "اضغط للاستماع · افتح المجموعة",
    "detail": "تفاصيل",
    "tonesTitle": "النغمات",
    "tonesDesc": "الصينية لغة نغمية: المقطع نفسه قد يحمل معنى مختلفًا تمامًا عند تغيير النغمة.",
    "toneNames": [
      "عالٍ ومستوى",
      "صاعد",
      "هابط ثم صاعد",
      "هابط",
      "محايد"
    ],
    "toneMeanings": [
      "أم",
      "قنب",
      "حصان",
      "يوبّخ",
      "أداة سؤال"
    ],
    "neutralNote": "النغمة المحايدة (5) قصيرة وغير مشددة؛ وغالبًا لا تُكتب علامتها."
  },
  "th": {
    "overview": "ภาพรวม",
    "nativeHint": "คำแนะนำภาษาแม่",
    "articulation": "วิธีออกเสียง",
    "introTitle": "บทนำ",
    "introDesc": "พยางค์ภาษาจีนมี 3 ส่วน: พยัญชนะต้น สระท้าย และวรรณยุกต์",
    "initial": "พยัญชนะต้น",
    "final": "สระท้าย",
    "tone": "วรรณยุกต์",
    "syllable": "พยางค์",
    "initials": "พยัญชนะต้น",
    "finals": "สระท้าย",
    "exploreHint": "แตะเพื่อฟัง · เปิดกลุ่มเพื่อดู",
    "detail": "รายละเอียด",
    "tonesTitle": "วรรณยุกต์",
    "tonesDesc": "ภาษาจีนเป็นภาษาวรรณยุกต์: พยางค์เดียวกันเมื่อเสียงต่างกัน ความหมายอาจต่างกันโดยสิ้นเชิง",
    "toneNames": [
      "สูงและเรียบ",
      "เสียงขึ้น",
      "ลงแล้วขึ้น",
      "เสียงลง",
      "เสียงเบา"
    ],
    "toneMeanings": [
      "แม่",
      "ป่าน",
      "ม้า",
      "ด่า",
      "คำช่วยคำถาม"
    ],
    "neutralNote": "เสียงเบา (5) สั้นและไม่เน้น ปกติไม่เขียนเครื่องหมายวรรณยุกต์"
  },
  "ru": {
    "overview": "Обзор",
    "nativeHint": "Подсказка на родном языке",
    "articulation": "Как произнести звук",
    "introTitle": "Введение",
    "introDesc": "Китайский слог состоит из трёх частей: инициали, финали и тона.",
    "initial": "Инициаль",
    "final": "Финаль",
    "tone": "Тон",
    "syllable": "Слог",
    "initials": "Инициали",
    "finals": "Финали",
    "exploreHint": "Нажмите, чтобы слушать · откройте группу",
    "detail": "Подробнее",
    "tonesTitle": "Тоны",
    "tonesDesc": "Китайский — тональный язык: один и тот же слог с разным тоном может означать совсем разные вещи.",
    "toneNames": [
      "высокий ровный",
      "восходящий",
      "нисходяще-восходящий",
      "нисходящий",
      "нейтральный"
    ],
    "toneMeanings": [
      "мама",
      "конопля",
      "лошадь",
      "ругать",
      "вопросительная частица"
    ],
    "neutralNote": "Нейтральный тон (5) короткий и без ударения; при письме знак тона обычно не ставится."
  },
  "id": {
    "overview": "Ikhtisar",
    "nativeHint": "Petunjuk bahasa ibu",
    "articulation": "Cara membuat bunyi",
    "introTitle": "Pengantar",
    "introDesc": "Suku kata Mandarin memiliki tiga bagian: initial, final, dan nada.",
    "initial": "Initial",
    "final": "Final",
    "tone": "Nada",
    "syllable": "Suku kata",
    "initials": "Initial",
    "finals": "Final",
    "exploreHint": "Ketuk untuk dengar · buka grup",
    "detail": "Detail",
    "tonesTitle": "Nada",
    "tonesDesc": "Mandarin adalah bahasa bernada: suku kata yang sama bisa berarti sangat berbeda jika nadanya berubah.",
    "toneNames": [
      "tinggi dan datar",
      "naik",
      "turun-naik",
      "turun",
      "netral"
    ],
    "toneMeanings": [
      "ibu",
      "rami",
      "kuda",
      "memarahi",
      "partikel tanya"
    ],
    "neutralNote": "Nada netral (5) pendek dan tidak ditekankan; tanda nada biasanya tidak ditulis."
  },
  "ms": {
    "overview": "Gambaran",
    "nativeHint": "Petunjuk bahasa ibunda",
    "articulation": "Cara menghasilkan bunyi",
    "introTitle": "Pengenalan",
    "introDesc": "Suku kata Cina mempunyai tiga bahagian: initial, final dan nada.",
    "initial": "Initial",
    "final": "Final",
    "tone": "Nada",
    "syllable": "Suku kata",
    "initials": "Initial",
    "finals": "Final",
    "exploreHint": "Ketik untuk dengar · buka kumpulan",
    "detail": "Butiran",
    "tonesTitle": "Nada",
    "tonesDesc": "Bahasa Cina ialah bahasa bernada: suku kata yang sama boleh membawa maksud berbeza apabila nadanya berubah.",
    "toneNames": [
      "tinggi dan rata",
      "menaik",
      "turun lalu naik",
      "menurun",
      "neutral"
    ],
    "toneMeanings": [
      "ibu",
      "rami",
      "kuda",
      "memarahi",
      "partikel tanya"
    ],
    "neutralNote": "Nada neutral (5) pendek dan tidak ditekankan; tanda nada biasanya tidak ditulis."
  },
  "it": {
    "overview": "Panoramica",
    "nativeHint": "Suggerimento nella tua lingua",
    "articulation": "Come produrre il suono",
    "introTitle": "Introduzione",
    "introDesc": "Le sillabe cinesi hanno tre parti: iniziale, finale e tono.",
    "initial": "Iniziale",
    "final": "Finale",
    "tone": "Tono",
    "syllable": "Sillaba",
    "initials": "Iniziali",
    "finals": "Finali",
    "exploreHint": "Tocca per ascoltare · apri il gruppo",
    "detail": "Dettaglio",
    "tonesTitle": "Toni",
    "tonesDesc": "Il cinese è una lingua tonale: la stessa sillaba può cambiare completamente significato con un tono diverso.",
    "toneNames": [
      "alto e piano",
      "ascendente",
      "discendente-ascendente",
      "discendente",
      "neutro"
    ],
    "toneMeanings": [
      "mamma",
      "canapa",
      "cavallo",
      "rimproverare",
      "particella interrogativa"
    ],
    "neutralNote": "Il tono neutro (5) è breve e non accentato; di solito il segno tonale non si scrive."
  }
};

const resources = {
  zh: {
    translation: {
      // 导航与基础
      "nav_auth": "登录/注册",
      "auth_login": "登录",
      "auth_register": "注册",
      "auth_email": "电子邮箱",
      "auth_password": "密码",
      "auth_confirm_password": "确认密码",
      "auth_submit_reg": "注册",
      "auth_submit_login": "登录",
      "auth_submit_continue": "继续",
      "auth_submit_verify": "验证激活",
      "auth_welcome": "欢迎回来",
      "auth_create": "创建新账号",
      "auth_back_home": "返回首页",
      "auth_login_subtitle": "请使用邮箱登录您的账号",
      "auth_register_subtitle": "开启您的智能外语学习之旅",
      "auth_register_tip": "请按照下方安全标准设置密码",
      "auth_verify_title": "验证您的邮箱",
      "auth_verify_subtitle": "验证码已发送至 {{email}}",
      "auth_success_title": "验证成功！",
      "auth_success_subtitle": "您的账号已激活，正在前往登录界面...",
      "auth_change_email": "返回修改邮箱",
      "auth_or_use": "或者使用",
      "auth_login_success_title": "登录成功！",
      "auth_login_success_subtitle": "正在返回首页...",

      // 密码强度要求
      "auth_pw_req_length": "8-32 个字符",
      "auth_pw_req_letter": "包含字母",
      "auth_pw_req_number": "包含数字",
      "auth_pw_req_special": "包含任意特殊字符",
      "auth_pw_req_no_space": "不能包含空格",
      "auth_pw_match": "两次密码一致",

      // 忘记密码
      "auth_forgot_password": "忘记密码？",
      "auth_forgot_title": "重置密码",
      "auth_forgot_subtitle": "请输入您的邮箱以获取验证码",
      "auth_reset_title": "设置新密码",
      "auth_reset_subtitle": "请输入验证码并设置您的新密码",
      "auth_submit_send_code": "发送验证码",
      "auth_submit_reset": "重置密码",
      "auth_back_to_login": "返回登录",

      // 首页 Hero
      "hero_badge": "✨ 你的首个 LLM 驱动的 AI 外教系统",
      "hero_title_1": "像母语者一样思考与表达",
      "hero_title_2": "AI 智能外语学习",
      "hero_desc": "告别机械记忆。Chilan 利用 LLM 深度分析你的遣词造句，结合科学的 FSRS 算法，助你高效掌握地道外语。",
      "hero_btn_classroom": "进入教室",
      "hero_btn_more": "查看功能特性",

      // 特性展示
      "feat_1_title": "语义化评测",
      "feat_1_desc": "利用向量检索与 LLM，Chilan 能像真人老师一样理解你的回答逻辑。",
      "feat_2_title": "FSRS 动态调度",
      "feat_2_desc": "基于现代统计学的 FSRS 算法，实时计算记忆稳定性，让记忆效率实现质的飞跃。",
      "feat_3_title": "AI 智能周报",
      "feat_3_desc": "内置智能 Agent 定期汇总复习历史，自动生成深度周报，精准定位薄弱环节。",
      "feat_4_title": "经典教材集成",
      "feat_4_desc": "支持全球多种主流语言及经典教材体系，让你在系统的框架下享受 AI 的辅助。",
      "feat_5_title": "极致性价比",
      "feat_5_desc": "仅需 3 欧元/月。我们不以盈利为目的，仅收基础成本费以维持服务器运行。",
      "feat_6_title": "全球学习社区",
      "feat_6_desc": "加入专属语言群聊，与全球学习者及 AI 共同探讨，构建真实的语言实践环境。",

      // 用户菜单与布局
      "nav_profile": "个人账户",
      "nav_overview": "学习概览",
      "nav_settings": "个人设置",
      "nav_account_title": "账户信息",
      "nav_logout": "退出登录",
      "settings_title": "个人设置",
      "overview_title": "学习概览",

      // 教室与课程管理
      "classroom_title": "学习教室",
      "classroom_subtitle": "挑选一个课程，开始今天的沉浸式学习。",
      "classroom_remaining_today": "今日待复习",
      "classroom_reviewed_today": "今日已复习",
      "classroom_new_learned_today": "今日新学习",
      "classroom_my_courses": "我的课程",
      "classroom_all_courses": "全部课程",
      "classroom_mastered": "已掌握",
      "classroom_start": "开始学习",
      "classroom_add_course": "添加新课程",
      "classroom_filter_learning": "学习语言",
      "classroom_filter_native": "母语",
      "classroom_filter_all": "全部",
      "classroom_join_course": "加入课程",
      "classroom_in_learning": "已在学习",
      "classroom_added": "已添加",
      "classroom_active_limit": "进行中 {{count}}/{{max}} 门，最多同时学习 {{max}} 门",
      "classroom_no_courses": "暂无符合筛选条件的课程",
      "classroom_course_lessons": "{{count}} 课时",
      "classroom_course_items": "{{count}} 个词汇",
      "btn_add": "添加",
      "course_en_zh": "中文学英文",
      "course_fr_zh": "法文学中文",
      "course_jp_zh": "日文学中文",
      "practice_title_lesson": "随堂强化练习",
      "practice_title_review": "智能巩固复习",
      "practice_prompt_cn_to_en": "翻译成英文",
      "practice_prompt_en_to_cn": "请翻译成中文",
      "practice_prompt_cn_listen_write": "听音写汉字",
      "practice_input_placeholder": "在这里输入你的答案...",
      "practice_submit": "提交答案",
      "practice_evaluating": "AI 导师正在阅卷...",
      "practice_retry": "重新提交",
      "practice_skip": "跳过此题，继续前进",
      "practice_next": "进入下一题",
      "practice_finish": "完成所有练习",
      "practice_feedback_excellent": "优秀！",
      "practice_feedback_good": "不错，但还有提升空间！",
      "practice_feedback_retry": "需要继续努力！",
      "practice_eval_failed": "判题服务连接失败，请重试。",
      "practice_ai_feedback_title": "AI 反馈",
      "practice_ai_analyzing": "AI 导师正在分析你的回答...",
      "word_pinyin_btn": "拼音",
      "word_translation_btn": "译",
      "practice_badge_cn_to_en": "翻译 · 中→英",
      "practice_badge_en_to_cn": "翻译 · 英→中",
      "practice_badge_speak": "口语 · 说中文",
      "practice_badge_dictation": "听写 · Dictation",
      "practice_audio_play": "播放",
      "practice_audio_replay": "重播",
      "practice_audio_played_times": "已播放 {{count}} 次 · 可重复播放",
      "practice_dictation_instruction": "听后用汉字写出你听到的句子",
      "practice_replay_hint": "按 ↑ 键重播",
      "practice_forfeit": "不会，查看答案",
      "practice_retry_show_answer": "重新查看答案",
      "practice_std_answer": "标准答案",
      "practice_ai_thinking": "AI 导师正在生成反馈",
      "practice_asr_recognized": "本次识别文本",
      "practice_retry_text": "重新作答",
      "practice_retry_speech": "重新录音",
      "practice_skip_question": "跳过本题",
      "practice_next_question": "下一题",
      "practice_finish_round": "完成本轮练习",
      "knowledge_title": "知识点详情",
      "knowledge_current_sense": "当前义项",
      "knowledge_other_senses": "更多义项",
      "knowledge_show": "显示",
      "knowledge_hide": "收起",
      "study_error_load": "无法获取课程数据，请确认后端已同步课程内容",
      "study_not_enrolled_title": "这门课不在你的学习列表中",
      "study_not_enrolled_desc": "你可以先浏览课程内容；需要继续学习、练习和记录进度时，请先加入课程。",
      "study_not_enrolled_action": "查看课程详情",
      "study_retry": "重试",
      "teaching_new_unit": "新单元",
      "teaching_video_label": "视觉语境引擎",
      "teaching_diary_original": "日记原文",
      "teaching_reading": "课文阅读",
      "teaching_content": "课文内容",
      "teaching_dialogue": "课文对话",
      "teaching_pinyin_on": "拼音开",
      "teaching_pinyin_off": "拼音关",
      "teaching_translation_on": "翻译开",
      "teaching_translation_off": "翻译关",
      "teaching_vocab_title": "本课生词",
      "teaching_example": "例句",
      "teaching_generating_quiz": "正在生成测验...",
      "teaching_start_quiz": "完成学习，进入测验",

      // 课程页
      "course_back": "返回课程选择",
      "course_foundations": "入门基础",
      "course_all_lessons": "全部课时",
      "course_no_lessons": "暂无课时数据",
      "course_start_learning": "开始学习",
      "course_progress_label": "课程进度",
      "course_progress_completed_count": "已完成 {{completed}} / {{total}} 课",
      "course_progress_next_lesson": "下一课",
      "course_progress_start_practice": "已看讲解，进入练习",
      "course_progress_resume_practice": "继续练习第 {{number}} 题",
      "course_progress_completed": "课程已完成",
      "course_progress_all_done": "全部课时已完成",
      "course_untitled_lesson": "未命名课时",
      "course_lesson_completed": "已完成",
      "course_lesson_current": "当前课时",
      "course_lesson_not_started": "未开始",
      "course_adding_learning": "正在添加...",
      "course_remove_learning": "暂停学习",
      "course_remove_failed": "暂停课程失败，请稍后重试。",
      "course_pause_confirm_eyebrow": "暂停确认",
      "course_pause_confirm_title": "确定暂停这门课吗？",
      "course_pause_confirm_desc": "暂停后，{{course}} 会从“我的课程”中移除，已有学习进度会保留，之后可以从全部课程重新添加。",
      "course_pause_confirm_action": "确认暂停",
      "course_remove_confirm_eyebrow": "课程管理",
      "course_remove_confirm_title": "要暂停还是清除这门课？",
      "course_remove_confirm_desc": "暂停会保留 {{course}} 的学习进度；清除会移除这门课的学习记录、复习记录和课时进度，之后重新添加会从头开始。",
      "course_clear_confirm_action": "清除记录",
      "course_limit_reached": "你当前最多可学习 2 门课程，请先完成或暂停一门。",
      "course_enroll_failed": "添加课程失败，请稍后重试。",
      "course_preview_before_join": "你可以先浏览课程结构和课时内容。添加到学习后会记录练习与学习进度。",
      "course_intro_card_title": "课程介绍",
      "course_intro_card_sub": "理念 · 学习方式 · 路径",
      "course_hanzi_card_title": "汉字入门",
      "course_hanzi_card_sub": "笔画 · 部首 · 结构",
      "course_pinyin_card_title": "拼音入门",
      "course_pinyin_card_sub": "声母 · 韵母 · 声调",
      "course_typing_card_title": "电脑打字",
      "course_typing_card_sub": "输入法 · 拼音打字 · 练习",
      "teaching_back_to_course": "返回教室",

      "ci_back": "返回",
      "ci_badge": "Chilan · 中文",
      "ci_h1_line1": "学习汉语",
      "ci_h1_line2": "像真实使用那样去学",
      "ci_subtitle": "一门由 AI 驱动的课程，从基础出发培养真正的沟通能力——听、说、打字，全面发展。",
      "ci_diff_heading": "与众不同之处",
      "ci_feat0_title": "AI 智能反馈",
      "ci_feat0_desc": "三层评估体系——即时正则匹配、语义相似度，再到深度 LLM 分析。对每一个答案都给出真实、细致的反馈。",
      "ci_feat1_title": "听力优先",
      "ci_feat1_desc": "每个单词和句子都有音频。听写练习训练你感知声调和发音的耳朵。",
      "ci_feat2_title": "口语练习",
      "ci_feat2_desc": "大声说出你的答案。语音识别 + AI 检验你的语义，而不仅仅是发音。",
      "ci_feat3_title": "键盘输入为主",
      "ci_feat3_desc": "用标准拼音输入法学习打字——母语者日常书写的方式。无需手写。",
      "ci_feat4_title": "间隔重复（FSRS）",
      "ci_feat4_desc": "每道题都由 FSRS 调度安排。掌握好的内容复现间隔更长；难点则更早重现。",
      "ci_feat5_title": "看得见的进步",
      "ci_feat5_desc": "教室追踪已复习、待复习和已掌握的内容。每次学习都有实质性收获。",
      "ci_no_hw_title": "我们不教写字",
      "ci_no_hw_body": "笔顺和手写确实很重要，但这是需要多年专项练习的独立技能。本课程专注于<strong>阅读、听力、口语和拼音输入法打字</strong>——大多数学习者最先需要的技能。",
      "ci_how_heading": "每节课如何进行",
      "ci_step0_title": "教学阶段",
      "ci_step0_desc": "新词配拼音、翻译、音频和可选视频讲解。没有计时——慢慢来。",
      "ci_step1_title": "练习阶段",
      "ci_step1_desc": "四种题型：译成英文、译成中文、大声朗读、听音写字。",
      "ci_step2_title": "AI 评测",
      "ci_step2_desc": "三层检验——精确匹配、语义相似，再到完整 LLM 判断并对边界情况给出解释。",
      "ci_step3_title": "FSRS 调度",
      "ci_step3_desc": "根据你的结果，FSRS 精确计算下次复习时间——几小时、几天或几周。",
      "ci_cta_text": "准备好了吗？从基础模块开始。",
      "ci_cta_hanzi": "汉字介绍 →",
      "ci_cta_pinyin": "拼音",

      "hi_back": "返回",
      "hi_badge": "入门基础",
      "hi_h1": "汉字",
      "hi_subtitle": "在学习词汇之前，了解汉字是什么以及它们如何构成会很有帮助。这是一个概念性概览——不需要死记硬背。",
      "hi_reading_only": "仅供阅读——这里没有练习题",
      "hi_what_h2": "什么是汉字？",
      "hi_what_p1": "每个汉字都是一个<strong>语素文字</strong>——一个代表语素（意义和声音的单位）的书写符号，而不仅仅是声音。字符 山 表示<em>山</em>，读作 <em>shān</em>。意义和声音都与这个单一符号绑定在一起。",
      "hi_what_p2": "现代普通话的日常读写大约需要<strong>3000–4000个汉字</strong>。HSK 6（高级）涵盖约 5000 个。好消息：大多数汉字由小的重复部件构成，规律很快就能显现。",
      "hi_what_p3": "与字母文字不同，中文没有大小写之分，词语之间没有空格，字符也不直接告诉你发音——这正是<strong>拼音</strong>的作用。",
      "hi_strokes_h2": "基本笔画",
      "hi_strokes_intro": "每个汉字都由少量基本笔画构成。大约有 6–8 种基本类型，其余都是变体或组合。",
      "hi_strokes_note": "本课程不教笔顺，但了解这些名称有助于在字典中查字。",
      "hi_stroke0_desc": "横 — 从左到右",
      "hi_stroke1_desc": "竖 — 从上到下",
      "hi_stroke2_desc": "撇 — 向左下弧",
      "hi_stroke3_desc": "捺 — 向右下按",
      "hi_stroke4_desc": "点",
      "hi_stroke5_desc": "折 — 转折（含钩）",
      "hi_radicals_h2": "偏旁部首（部首 bùshǒu）",
      "hi_radicals_intro": "部首是反复出现的构件，通常暗示字的<strong>义类</strong>。字典传统上按部首编排。认识部首能让猜测和记忆新字更容易。",
      "hi_rad0_meaning": "水", "hi_rad0_hint": "左侧三点水", "hi_rad0_ex": "河 · 海 · 洗",
      "hi_rad1_meaning": "木", "hi_rad1_hint": "独立或作左旁", "hi_rad1_ex": "树 · 林 · 桌",
      "hi_rad2_meaning": "口", "hi_rad2_hint": "小方框形状", "hi_rad2_ex": "吃 · 喝 · 说",
      "hi_rad3_meaning": "人", "hi_rad3_hint": "站立形或单人旁", "hi_rad3_ex": "他 · 你 · 做",
      "hi_rad4_meaning": "心", "hi_rad4_hint": "独立或作左旁三点", "hi_rad4_ex": "想 · 忘 · 情",
      "hi_rad5_meaning": "言", "hi_rad5_hint": "简化为左侧两点一横", "hi_rad5_ex": "说 · 话 · 读",
      "hi_radicals_tip": "<strong>提示：</strong>部首并不总能预测发音，一个字也可以有多个部件。把它们看作大致的语义提示，而非严格规则。",
      "hi_struct_h2": "汉字的结构",
      "hi_struct_intro": "汉字将部件按照可预测的空间排列组合。一旦掌握规律，你就能一眼「读出」新字的形状。",
      "hi_struct0_type": "左右结构", "hi_struct0_desc": "两个或多个部件并排排列。中文最常见的结构。",
      "hi_struct0_ex0_m": "好", "hi_struct0_ex0_b": "女 + 子",
      "hi_struct0_ex1_m": "明亮", "hi_struct0_ex1_b": "日 + 月",
      "hi_struct0_ex2_m": "请", "hi_struct0_ex2_b": "讠 + 青",
      "hi_struct1_type": "上下结构", "hi_struct1_desc": "一个部件叠在另一个上面。",
      "hi_struct1_ex0_m": "字", "hi_struct1_ex0_b": "宀 + 子",
      "hi_struct1_ex1_m": "思考", "hi_struct1_ex1_b": "田 + 心",
      "hi_struct1_ex2_m": "男性", "hi_struct1_ex2_b": "田 + 力",
      "hi_struct2_type": "包围结构", "hi_struct2_desc": "一个部件包围另一个——全包或三面包。",
      "hi_struct2_ex0_m": "国家", "hi_struct2_ex0_b": "囗 + 玉",
      "hi_struct2_ex1_m": "问", "hi_struct2_ex1_b": "门 + 口",
      "hi_struct2_ex2_m": "花园", "hi_struct2_ex2_b": "囗 + 元",
      "hi_struct3_type": "独体字", "hi_struct3_desc": "一个单一、不可分割的字——通常是古代汉语的象形字。",
      "hi_struct3_ex0_m": "山", "hi_struct3_ex0_b": "三个山峰形状",
      "hi_struct3_ex1_m": "太阳 / 日", "hi_struct3_ex1_b": "带一横的圆——太阳",
      "hi_struct3_ex2_m": "木", "hi_struct3_ex2_b": "带根和枝的树",
      "hi_typing_h2": "打出汉字",
      "hi_typing_p1": "在本课程中，你使用<strong>拼音输入法</strong>（IME）输入中文——这与几乎所有母语者在手机和电脑上使用的方法相同。你输入罗马化发音，IME 提供匹配的字供选择。",
      "hi_typing_p2": "例如，输入 <code>hao</code> 并选择正确的字，就能得到 好。你不需要知道如何书写这个字才能在数字设备上输入它。",
      "hi_typing_p3": "这就是为什么<strong>拼音掌握放在首位</strong>：准确打字依赖于知道每个字的发音。",
      "hi_cta_text": "现在你已经建立了汉字的心理模型，准备好学习声音系统了。",
      "hi_cta_btn": "继续学习拼音",

      "civ_welcome_h1": "学习中文",
      "civ_welcome_accent": "像它真正被使用的那样",
      "civ_welcome_sub": "AI 驱动 · 交际优先 · 为数字时代而生",
      "civ_sounds_label": "基础 — 第一步",
      "civ_sounds_h2_pre": "先从",
      "civ_sounds_h2_accent": "声音开始",
      "civ_sounds_sub": "在词汇和语法之前——掌握改变一切的 4 个声调。",
      "civ_sounds_tone0_label": "第一声", "civ_sounds_tone0_name": "高平",
      "civ_sounds_tone1_label": "第二声", "civ_sounds_tone1_name": "上升",
      "civ_sounds_tone2_label": "第三声", "civ_sounds_tone2_name": "降升",
      "civ_sounds_tone3_label": "第四声", "civ_sounds_tone3_name": "下降",
      "civ_sounds_example": "妈（妈妈）· 麻（麻布）· 马（马匹）· 骂（骂人）— 同一音节，四种不同含义",
      "civ_skills_label": "你将练习的内容",
      "civ_skills_h2_pre": "三项技能，",
      "civ_skills_h2_accent": "一门课",
      "civ_skills_sk0_label": "听", "civ_skills_sk0_sub": "每个词和句子都有音频。听写练习训练你的耳朵。",
      "civ_skills_sk1_label": "说", "civ_skills_sk1_sub": "录制你的声音。AI 检查你的意思，而不仅仅是发音。",
      "civ_skills_sk2_label": "打字", "civ_skills_sk2_sub": "拼音输入法——母语者每天在手机和电脑上的书写方式。",
      "civ_skills_no_hw": "书写是一项单独的技能——本课程完全专注于阅读、听力、口语和打字。",
      "civ_ai_label": "答案如何被评判",
      "civ_ai_h2_pre": "AI 评判",
      "civ_ai_h2_accent": "每一个答案",
      "civ_ai_sub": "三层系统：即时模式匹配 → 语义相似度 → 完整 LLM 分析。含义比精确措辞更重要。",
      "civ_ai_example_label": "示例",
      "civ_ai_example_ans1": "「你平时都做什么？」",
      "civ_ai_example_ans2": "「你通常都做什么？」",
      "civ_ai_example_note": "两者均被接受——相同含义，不同措辞",
      "civ_ai_tier0_label": "精确匹配", "civ_ai_tier0_desc": "正则/模式检查——即时",
      "civ_ai_tier1_label": "语义", "civ_ai_tier1_desc": "嵌入相似度分数",
      "civ_ai_tier2_label": "AI 分析", "civ_ai_tier2_desc": "LLM 判断 + 解释",
      "civ_fsrs_label": "记忆科学",
      "civ_fsrs_h2_pre": "没有任何内容会",
      "civ_fsrs_h2_accent": "被遗漏",
      "civ_fsrs_sub": "FSRS——免费间隔重复调度器——精确计算每个单词的复习时间。",
      "civ_fsrs_chart_label": "单词复习计划示例",
      "civ_fsrs_leg0": "早期频繁复习", "civ_fsrs_leg1": "间隔增加", "civ_fsrs_leg2": "长期记忆保留",
      "civ_start_label": "你的学习路径",
      "civ_start_h2_pre": "准备好",
      "civ_start_h2_accent": "开始了吗？",
      "civ_start_sub": "从基础开始——其余一切都建立在这之上。",
      "civ_start_step0_label": "拼音", "civ_start_step0_sub": "声音与声调",
      "civ_start_step1_label": "汉字", "civ_start_step1_sub": "结构与偏旁部首",
      "civ_start_step2_label": "词汇", "civ_start_step2_sub": "语境中的词汇",
      "civ_start_step3_label": "句子", "civ_start_step3_sub": "语法模式",
      "civ_start_note": "在教室中使用基础模块开始学习。",
      "civ_narration_welcome": "欢迎来到 Chilan——一个 AI 驱动的中文学习平台。本课程培养真实的交流技能：听力、口语和打字。我们从第一原理出发，从发音系统开始。",
      "civ_narration_sounds": "每个汉语音节都有声调，改变声调会完全改变含义。四个声调是高平调、上升调、降升调和下降调。掌握声调是学汉语最重要的基础。",
      "civ_narration_skills": "本课程培养三项核心技能：听力、口语和使用拼音输入法打字。我们专注于中文在日常数字生活中的实际使用方式——而非手写。你很快就能阅读、听、说和打字。",
      "civ_narration_ai": "你提交的每个答案都由三层系统评估。即时模式匹配处理明显的情况。语义比较捕获措辞不同但含义相同的答案。大型语言模型则处理真正的边缘情况并提供详细解释。",
      "civ_narration_fsrs": "你的复习计划由 FSRS 驱动——免费间隔重复调度器。你掌握较好的内容复现频率较低。较难的内容会更快再次出现。这确保你将学习时间花在最需要的地方。",
      "civ_narration_start": "你已经准备好开始了。从基础模块开始：拼音用于发音系统，然后是汉字用于结构。课程中的每节课都建立在这些基础之上。"
    }
  },
  en: {
    translation: {
      "nav_auth": "Login/Register",
      "auth_login": "Login",
      "auth_register": "Register",
      "auth_email": "Email Address",
      "auth_password": "Password",
      "auth_confirm_password": "Confirm Password",
      "auth_submit_reg": "Register",
      "auth_submit_login": "Login",
      "auth_submit_continue": "Continue",
      "auth_submit_verify": "Verify & Activate",
      "auth_welcome": "Welcome Back",
      "auth_create": "Create Account",
      "auth_back_home": "Back to Home",
      "auth_login_subtitle": "Login with your email address",
      "auth_register_subtitle": "Start your AI learning journey",
      "auth_register_tip": "Set a password meeting the safety standards",
      "auth_verify_title": "Verify Your Email",
      "auth_verify_subtitle": "A code has been sent to {{email}}",
      "auth_success_title": "Success!",
      "auth_success_subtitle": "Account activated. Redirecting to login...",
      "auth_change_email": "Change Email",
      "auth_or_use": "Or use",
      "auth_login_success_title": "Login Success!",
      "auth_login_success_subtitle": "Returning to home page...",
      "auth_pw_req_length": "8-32 characters",
      "auth_pw_req_letter": "Contains letters",
      "auth_pw_req_number": "Numbers",
      "auth_pw_req_special": "Any special character",
      "auth_pw_req_no_space": "No spaces",
      "auth_pw_match": "Passwords match",
      "hero_badge": "✨ Your First LLM-Powered AI Tutor",
      "hero_title_1": "Think and Speak Like a Native",
      "hero_title_2": "AI Language Learning",
      "hero_desc": "Beyond rote memorization. Chilan uses LLM for deep analysis and FSRS algorithm for efficient mastery.",
      "hero_btn_classroom": "Enter Classroom",
      "hero_btn_more": "Explore Features",
      "feat_1_title": "Semantic Grading",
      "feat_1_desc": "Advanced LLM understanding allows for flexible expression instead of rigid matching.",
      "feat_2_title": "FSRS Scheduling",
      "feat_2_desc": "FSRS algorithm calculates memory stability to optimize your review intervals.",
      "feat_3_title": "AI Progress Report",
      "feat_3_desc": "Built-in AI Agents analyze history to generate deep insights and targeted advice.",
      "feat_4_title": "Classic Textbooks",
      "feat_4_desc": "Support for multiple languages and world-class textbooks for structured learning.",
      "feat_5_title": "Unbeatable Value",
      "feat_5_desc": "Only €3/month. Non-profit pricing designed to cover server costs.",
      "feat_6_title": "Global Community",
      "feat_6_desc": "Join language-specific groups and practice with global learners and AI.",
      "nav_profile": "Profile",
      "nav_overview": "Overview",
      "nav_settings": "Settings",
      "nav_account_title": "Account",
      "nav_logout": "Logout",
      "settings_title": "Personal Settings",
      "overview_title": "Learning Overview",
      "classroom_title": "Classroom",
      "classroom_subtitle": "Pick a course to start today's immersion.",
      "classroom_remaining_today": "To Review",
      "classroom_reviewed_today": "Reviewed",
      "classroom_new_learned_today": "New Learned",
      "classroom_my_courses": "My Courses",
      "classroom_all_courses": "All Courses",
      "classroom_mastered": "Mastered",
      "classroom_start": "Start Learning",
      "classroom_add_course": "Add New Course",
      "classroom_filter_learning": "Learning Language",
      "classroom_filter_native": "Native Language",
      "classroom_filter_all": "All",
      "classroom_join_course": "Join Course",
      "classroom_in_learning": "In Progress",
      "classroom_added": "Added",
      "classroom_active_limit": "In progress {{count}}/{{max}}. You can study up to {{max}} courses at once.",
      "classroom_no_courses": "No courses match the current filters",
      "classroom_course_lessons": "{{count}} lessons",
      "classroom_course_items": "{{count}} vocab items",
      "btn_add": "Add",
      "course_en_zh": "English (CN)",
      "course_fr_zh": "French (CN)",
      "course_jp_zh": "Japanese (CN)",
      "practice_title_lesson": "In-Class Intensive Practice",
      "practice_title_review": "Smart Review Practice",
      "practice_prompt_cn_to_en": "Translate into English",
      "practice_prompt_en_to_cn": "Translate into Chinese",
      "practice_prompt_cn_listen_write": "Listen & Write Chinese",
      "practice_input_placeholder": "Type your answer here...",
      "practice_submit": "Submit Answer",
      "practice_evaluating": "AI tutor is evaluating...",
      "practice_retry": "Submit Again",
      "practice_skip": "Skip this question",
      "practice_next": "Next Question",
      "practice_finish": "Finish Practice",
      "practice_feedback_excellent": "Excellent!",
      "practice_feedback_good": "Good job, but there is room to improve!",
      "practice_feedback_retry": "Keep trying!",
      "practice_eval_failed": "Evaluation service is unavailable. Please try again.",
      "practice_ai_feedback_title": "AI Feedback",
      "practice_ai_analyzing": "AI tutor is analyzing your answer...",
      "word_pinyin_btn": "Pinyin",
      "word_translation_btn": "Trans",
      "practice_badge_cn_to_en": "Translate · CN→EN",
      "practice_badge_en_to_cn": "Translate · EN→CN",
      "practice_badge_speak": "Speaking · in Chinese",
      "practice_badge_dictation": "Dictation · 听写",
      "practice_audio_play": "Play",
      "practice_audio_replay": "Replay",
      "practice_audio_played_times": "Played {{count}} time(s) · Replay anytime",
      "practice_dictation_instruction": "Write the Chinese characters you hear",
      "practice_replay_hint": "Press ↑ to replay",
      "practice_forfeit": "Show answer",
      "practice_retry_show_answer": "Try showing answer again",
      "practice_std_answer": "Answer",
      "practice_ai_thinking": "AI tutor is generating feedback",
      "practice_asr_recognized": "Recognized text",
      "practice_retry_text": "Try again",
      "practice_retry_speech": "Record again",
      "practice_skip_question": "Skip",
      "practice_next_question": "Next",
      "practice_finish_round": "Finish round",
      "knowledge_title": "Knowledge Details",
      "knowledge_current_sense": "Current Sense",
      "knowledge_other_senses": "Other Meanings",
      "knowledge_show": "Show",
      "knowledge_hide": "Hide",
      "study_error_load": "Unable to load course data. Please make sure the backend has synced the lesson.",
      "study_not_enrolled_title": "This course is not in your learning list",
      "study_not_enrolled_desc": "You can still preview the course. Join it first when you want learning, practice, and progress tracking.",
      "study_not_enrolled_action": "View Course",
      "study_retry": "Retry",
      "teaching_new_unit": "New Unit",
      "teaching_video_label": "Visual Context Engine",
      "teaching_diary_original": "Diary Entry",
      "teaching_reading": "Reading Passage",
      "teaching_content": "Lesson Content",
      "teaching_dialogue": "Dialogue",
      "teaching_pinyin_on": "Pinyin On",
      "teaching_pinyin_off": "Pinyin Off",
      "teaching_translation_on": "Translation On",
      "teaching_translation_off": "Translation Off",
      "teaching_vocab_title": "Vocabulary",
      "teaching_example": "Example",
      "teaching_generating_quiz": "Generating quiz...",
      "teaching_start_quiz": "Finish Lesson & Start Quiz",

      // Auth - password reset (missing keys)
      "auth_forgot_password": "Forgot Password?",
      "auth_forgot_title": "Reset Password",
      "auth_forgot_subtitle": "Enter your email to receive a verification code",
      "auth_reset_title": "Set New Password",
      "auth_reset_subtitle": "Enter the code and set your new password",
      "auth_submit_send_code": "Send Code",
      "auth_submit_reset": "Reset Password",
      "auth_back_to_login": "Back to Login",

      // Course page
      "course_back": "Back to Course Selection",
      "course_foundations": "Foundations",
      "course_all_lessons": "All Lessons",
      "course_no_lessons": "No lessons available",
      "course_start_learning": "Start Learning",
      "course_progress_label": "Course Progress",
      "course_progress_completed_count": "{{completed}} / {{total}} lessons completed",
      "course_progress_next_lesson": "Next lesson",
      "course_progress_start_practice": "Teaching viewed. Start practice",
      "course_progress_resume_practice": "Resume practice question {{number}}",
      "course_progress_completed": "Course completed",
      "course_progress_all_done": "All lessons completed",
      "course_untitled_lesson": "Untitled lesson",
      "course_lesson_completed": "Completed",
      "course_lesson_current": "Current",
      "course_lesson_not_started": "Not started",
      "course_adding_learning": "Adding...",
      "course_remove_learning": "Pause",
      "course_remove_failed": "Failed to pause the course. Please try again.",
      "course_pause_confirm_eyebrow": "Pause confirmation",
      "course_pause_confirm_title": "Pause this course?",
      "course_pause_confirm_desc": "After pausing, {{course}} will be removed from My Courses. Your progress will be kept, and you can add it again from All Courses later.",
      "course_pause_confirm_action": "Confirm pause",
      "course_remove_confirm_eyebrow": "Course management",
      "course_remove_confirm_title": "Pause or clear this course?",
      "course_remove_confirm_desc": "Pause keeps your progress for {{course}}. Clear removes learning records, review logs, and lesson progress, so adding it again starts from the beginning.",
      "course_clear_confirm_action": "Clear records",
      "course_limit_reached": "You can study up to 2 courses at once. Please complete or pause one first.",
      "course_enroll_failed": "Failed to add the course. Please try again.",
      "course_preview_before_join": "You can preview the course structure and lessons first. Add it to your learning list when you want practice and progress tracking.",
      "course_intro_card_title": "Course Intro",
      "course_intro_card_sub": "Concepts · workflow · path",
      "course_hanzi_card_title": "Hanzi Basics",
      "course_hanzi_card_sub": "Strokes · radicals · structure",
      "course_pinyin_card_title": "Pinyin Basics",
      "course_pinyin_card_sub": "Initials · finals · tones",
      "course_typing_card_title": "Typing",
      "course_typing_card_sub": "IME · pinyin typing · practice",
      "teaching_back_to_course": "Back to Course",

      "ci_back": "Back",
      "ci_badge": "Chilan · Chinese",
      "ci_h1_line1": "Learn Chinese",
      "ci_h1_line2": "the way it's actually used",
      "ci_subtitle": "An AI-powered course that builds real communication skills — listening, speaking, and typing — starting from first principles.",
      "ci_diff_heading": "What makes this different",
      "ci_feat0_title": "AI-powered feedback",
      "ci_feat0_desc": "Three-tier evaluation — instant regex check, semantic similarity, then deep LLM analysis. Honest, nuanced feedback on every answer.",
      "ci_feat1_title": "Listening first",
      "ci_feat1_desc": "Audio for every word and sentence. Dictation exercises train your ear to hear tones and sounds.",
      "ci_feat2_title": "Speaking practice",
      "ci_feat2_desc": "Speak your answers aloud. Speech recognition + AI checks your meaning — not just pronunciation.",
      "ci_feat3_title": "Keyboard input focus",
      "ci_feat3_desc": "Learn to type Chinese with a standard pinyin IME — the way native speakers write every day. No handwriting required.",
      "ci_feat4_title": "Spaced repetition (FSRS)",
      "ci_feat4_desc": "Every question is scheduled by FSRS. Items you know well come back less often; tricky ones reappear sooner.",
      "ci_feat5_title": "Progress you can see",
      "ci_feat5_desc": "Your classroom tracks reviewed, remaining, and mastered items. Every session moves the needle.",
      "ci_no_hw_title": "We don't teach handwriting",
      "ci_no_hw_body": "Stroke order and handwriting are genuinely important, but they're a separate skill that takes years of dedicated practice. This course focuses entirely on <strong>reading, listening, speaking, and typing with a pinyin IME</strong> — the skills most learners need first.",
      "ci_how_heading": "How each lesson works",
      "ci_step0_title": "Teaching phase",
      "ci_step0_desc": "New words with pinyin, translation, audio, and an optional video explanation. No timer — take your time.",
      "ci_step1_title": "Practice phase",
      "ci_step1_desc": "Four question types: translate to English, translate to Chinese, speak aloud, or write from audio dictation.",
      "ci_step2_title": "AI evaluation",
      "ci_step2_desc": "Three-tier check — exact match, semantic similarity, then full LLM judgment with explanation for edge cases.",
      "ci_step3_title": "FSRS scheduling",
      "ci_step3_desc": "Based on your result, FSRS calculates exactly when to show this item again — hours, days, or weeks.",
      "ci_cta_text": "Ready to start? Begin with the foundation modules.",
      "ci_cta_hanzi": "Chinese Characters →",
      "ci_cta_pinyin": "Pinyin",

      "hi_back": "Back",
      "hi_badge": "Foundation · 基础",
      "hi_h1": "Chinese Characters",
      "hi_subtitle": "Before diving into vocabulary, it helps to understand what Chinese characters are and how they're built. This is a conceptual overview — no memorisation required.",
      "hi_reading_only": "Reading only — no practice questions here",
      "hi_what_h2": "What is a Chinese character?",
      "hi_what_p1": "Each Chinese character is a <strong>logogram</strong> — a written symbol that represents a morpheme (a unit of meaning and sound), not just a sound. The character 山 means <em>mountain</em> and is pronounced <em>shān</em>. Both the meaning and the sound are tied to that single symbol.",
      "hi_what_p2": "Modern Mandarin uses roughly <strong>3,000–4,000 characters</strong> for everyday literacy. HSK 6 (advanced) covers around 5,000. The good news: most characters are made of smaller recurring pieces, so patterns emerge quickly.",
      "hi_what_p3": "Unlike alphabetic scripts, Chinese has no uppercase or lowercase, no spaces between words, and characters don't tell you their pronunciation directly — that's what <strong>pinyin</strong> is for.",
      "hi_strokes_h2": "Basic strokes",
      "hi_strokes_intro": "Every character is built from a small set of fundamental brush strokes. There are about 6–8 basic types; everything else is a variant or combination.",
      "hi_strokes_note": "We don't teach stroke order in this course, but knowing these names helps when you look characters up in a dictionary.",
      "hi_stroke0_desc": "Horizontal — left to right",
      "hi_stroke1_desc": "Vertical — top to bottom",
      "hi_stroke2_desc": "Left-falling sweep",
      "hi_stroke3_desc": "Right-falling press",
      "hi_stroke4_desc": "Dot",
      "hi_stroke5_desc": "Turn / bend (includes hooks)",
      "hi_radicals_h2": "Radicals (部首 bùshǒu)",
      "hi_radicals_intro": "Radicals are recurring components that often hint at a character's <strong>category of meaning</strong>. Dictionaries are traditionally organized by radical. Recognizing them makes new characters easier to guess and remember.",
      "hi_rad0_meaning": "water", "hi_rad0_hint": "three dots on the left", "hi_rad0_ex": "河 river · 海 sea · 洗 wash",
      "hi_rad1_meaning": "wood / tree", "hi_rad1_hint": "standalone or as 木 on left", "hi_rad1_ex": "树 tree · 林 forest · 桌 table",
      "hi_rad2_meaning": "mouth", "hi_rad2_hint": "small box shape", "hi_rad2_ex": "吃 eat · 喝 drink · 说 speak",
      "hi_rad3_meaning": "person", "hi_rad3_hint": "standing figure or side radical", "hi_rad3_ex": "他 he · 你 you · 做 do",
      "hi_rad4_meaning": "heart / mind", "hi_rad4_hint": "standalone or three dots on left", "hi_rad4_ex": "想 think · 忘 forget · 情 emotion",
      "hi_rad5_meaning": "speech / words", "hi_rad5_hint": "simplified to two dots + stroke on left", "hi_rad5_ex": "说 speak · 话 words · 读 read",
      "hi_radicals_tip": "<strong>Tip:</strong> Radicals don't always predict pronunciation, and one character can have multiple components. Think of them as rough semantic hints, not strict rules.",
      "hi_struct_h2": "How characters are structured",
      "hi_struct_intro": "Characters combine components in predictable spatial arrangements. Once you see the pattern, you start to \"read\" the shape of new characters at a glance.",
      "hi_struct0_type": "Left–right  左右", "hi_struct0_desc": "Two or more components placed side by side. The most common structure in Chinese.",
      "hi_struct0_ex0_m": "good", "hi_struct0_ex0_b": "女 (woman) + 子 (child)",
      "hi_struct0_ex1_m": "bright", "hi_struct0_ex1_b": "日 (sun) + 月 (moon)",
      "hi_struct0_ex2_m": "please / invite", "hi_struct0_ex2_b": "讠(speech) + 青 (blue/clear)",
      "hi_struct1_type": "Top–bottom  上下", "hi_struct1_desc": "One component stacked on top of another.",
      "hi_struct1_ex0_m": "character / word", "hi_struct1_ex0_b": "宀 (roof) + 子 (child)",
      "hi_struct1_ex1_m": "to think", "hi_struct1_ex1_b": "田 (field) + 心 (heart)",
      "hi_struct1_ex2_m": "male", "hi_struct1_ex2_b": "田 (field) + 力 (strength)",
      "hi_struct2_type": "Enclosure  包围", "hi_struct2_desc": "One component wraps around another — fully or on three sides.",
      "hi_struct2_ex0_m": "country", "hi_struct2_ex0_b": "囗 (border) + 玉 (jade)",
      "hi_struct2_ex1_m": "to ask", "hi_struct2_ex1_b": "门 (door) + 口 (mouth)",
      "hi_struct2_ex2_m": "garden", "hi_struct2_ex2_b": "囗 (border) + 元",
      "hi_struct3_type": "Single unit  独体", "hi_struct3_desc": "A single, indivisible character — often a pictograph from ancient Chinese.",
      "hi_struct3_ex0_m": "mountain", "hi_struct3_ex0_b": "Three peaks — mountain shape",
      "hi_struct3_ex1_m": "sun / day", "hi_struct3_ex1_b": "Circle with a line — the sun",
      "hi_struct3_ex2_m": "wood / tree", "hi_struct3_ex2_b": "Tree with roots and branches",
      "hi_typing_h2": "Typing Chinese characters",
      "hi_typing_p1": "In this course, you type Chinese using a <strong>pinyin IME</strong> (Input Method Editor) — the same method virtually all native speakers use on phones and computers. You type the romanised pronunciation, and the IME offers matching characters to pick from.",
      "hi_typing_p2": "For example, typing <code>hao</code> and selecting the right character gives you 好. You don't need to know how to draw the character to produce it digitally.",
      "hi_typing_p3": "This is why <strong>pinyin mastery comes first</strong>: accurate typing depends on knowing how each character is pronounced.",
      "hi_cta_text": "Now that you have a mental model of Chinese characters, you're ready for the sound system.",
      "hi_cta_btn": "Continue to Pinyin",

      "civ_welcome_h1": "Learn Chinese",
      "civ_welcome_accent": "the way it's actually used",
      "civ_welcome_sub": "AI-powered · communication-first · built for the digital age",
      "civ_sounds_label": "Foundation — Step 1",
      "civ_sounds_h2_pre": "We start with ",
      "civ_sounds_h2_accent": "sounds",
      "civ_sounds_sub": "Before words, before grammar — master the 4 tones that change everything.",
      "civ_sounds_tone0_label": "1st tone", "civ_sounds_tone0_name": "high level",
      "civ_sounds_tone1_label": "2nd tone", "civ_sounds_tone1_name": "rising",
      "civ_sounds_tone2_label": "3rd tone", "civ_sounds_tone2_name": "falling-rising",
      "civ_sounds_tone3_label": "4th tone", "civ_sounds_tone3_name": "falling",
      "civ_sounds_example": "妈 (mom) · 麻 (hemp) · 马 (horse) · 骂 (scold) — same syllable, four different meanings",
      "civ_skills_label": "What you'll practise",
      "civ_skills_h2_pre": "Three skills, ",
      "civ_skills_h2_accent": "one course",
      "civ_skills_sk0_label": "Listen", "civ_skills_sk0_sub": "Audio for every word and sentence. Dictation exercises train your ear.",
      "civ_skills_sk1_label": "Speak", "civ_skills_sk1_sub": "Record your voice. AI checks your meaning, not just pronunciation.",
      "civ_skills_sk2_label": "Type", "civ_skills_sk2_sub": "Pinyin IME — how native speakers write every day on phones and computers.",
      "civ_skills_no_hw": "Handwriting is a separate skill — this course focuses entirely on reading, listening, speaking, and typing.",
      "civ_ai_label": "How answers are judged",
      "civ_ai_h2_pre": "AI evaluates",
      "civ_ai_h2_accent": "every answer",
      "civ_ai_sub": "A three-tier system: instant pattern match → semantic similarity → full LLM analysis. Meaning matters more than exact wording.",
      "civ_ai_example_label": "example",
      "civ_ai_example_ans1": "\"What do you usually do?\"",
      "civ_ai_example_ans2": "\"What do you normally do?\"",
      "civ_ai_example_note": "Both accepted — same meaning, different words",
      "civ_ai_tier0_label": "Exact match", "civ_ai_tier0_desc": "Regex / pattern check — instant",
      "civ_ai_tier1_label": "Semantic", "civ_ai_tier1_desc": "Embedding similarity score",
      "civ_ai_tier2_label": "AI analysis", "civ_ai_tier2_desc": "LLM judgment + explanation",
      "civ_fsrs_label": "Memory science",
      "civ_fsrs_h2_pre": "Nothing falls through ",
      "civ_fsrs_h2_accent": "the cracks",
      "civ_fsrs_sub": "FSRS — the Free Spaced Repetition Scheduler — calculates exactly when to review each word.",
      "civ_fsrs_chart_label": "example review schedule for one word",
      "civ_fsrs_leg0": "frequent early reviews", "civ_fsrs_leg1": "spacing increases", "civ_fsrs_leg2": "long-term retention",
      "civ_start_label": "Your path",
      "civ_start_h2_pre": "Ready to ",
      "civ_start_h2_accent": "start?",
      "civ_start_sub": "Begin with the foundation — everything else builds on top.",
      "civ_start_step0_label": "Pinyin", "civ_start_step0_sub": "Sounds & tones",
      "civ_start_step1_label": "Characters", "civ_start_step1_sub": "Structure & radicals",
      "civ_start_step2_label": "Vocabulary", "civ_start_step2_sub": "Words in context",
      "civ_start_step3_label": "Sentences", "civ_start_step3_sub": "Grammar patterns",
      "civ_start_note": "Use the foundation modules in the classroom to get started.",
      "civ_narration_welcome": "Welcome to Chilan — an AI-powered Chinese language learning platform. This course builds real communication skills: listening, speaking, and typing. We start from first principles, beginning with the sound system.",
      "civ_narration_sounds": "Every Chinese syllable has a tone, and changing the tone completely changes the meaning. The four tones are high and level, rising, falling-rising, and falling. Mastering tones is the single most important foundation in Chinese.",
      "civ_narration_skills": "This course trains three core skills: listening, speaking, and typing with a pinyin input method. We focus on how Chinese is actually used in daily digital life — not handwriting. You'll be able to read, listen, speak, and type before long.",
      "civ_narration_ai": "Every answer you submit is evaluated by a three-tier system. Instant pattern matching handles obvious cases. Semantic comparison catches answers that mean the same thing in different words. And a large language model handles genuine edge cases with a detailed explanation.",
      "civ_narration_fsrs": "Your review schedule is powered by FSRS — the Free Spaced Repetition Scheduler. Items you know well come back less often. Tricky items reappear sooner. This ensures you spend your study time exactly where it's needed.",
      "civ_narration_start": "You're ready to begin. Start with the foundation modules: pinyin for the sound system, then Chinese characters for structure. Every lesson in the course builds on these foundations."
    }
  },
  jp: {
    translation: {
      "nav_auth": "ログイン/登録",
      "auth_login": "ログイン",
      "auth_register": "新規登録",
      "auth_email": "メールアドレス",
      "auth_password": "パスワード",
      "auth_confirm_password": "パスワード再確認",
      "auth_submit_reg": "登録",
      "auth_submit_login": "ログイン",
      "auth_submit_continue": "次へ",
      "auth_submit_verify": "認証して有効化",
      "auth_welcome": "おかえりなさい",
      "auth_create": "アカウント作成",
      "auth_back_home": "ホームに戻る",
      "auth_login_subtitle": "メールアドレスでログインしてください",
      "auth_register_subtitle": "AI言語学習の旅を始めましょう",
      "auth_register_tip": "以下の基準に従って設定してください",
      "auth_verify_title": "メールアドレスの確認",
      "auth_verify_subtitle": "確認コードを {{email}} に送信しました",
      "auth_success_title": "認証成功！",
      "auth_success_subtitle": "有効化されました。ログイン画面に移動します...",
      "auth_change_email": "メールアドレスを変更する",
      "auth_or_use": "または",
      "auth_login_success_title": "ログイン成功！",
      "auth_login_success_subtitle": "ホームに戻ります...",
      "auth_pw_req_length": "8〜32文字",
      "auth_pw_req_letter": "文字を含む",
      "auth_pw_req_number": "数字を含む",
      "auth_pw_req_special": "任意の記号を含む",
      "auth_pw_req_no_space": "スペースを含まない",
      "auth_pw_match": "パスワードが一致",
      "hero_badge": "✨ LLM搭載のAI言語コーチ",
      "hero_title_1": "ネイティブのように考え、話す",
      "hero_title_2": "AI 智能外語学習",
      "hero_desc": "暗記を捨てて、会話を始めましょう。LLMとFSRSを搭載したChilanは、あなたの語学力を高めます。",
      "hero_btn_classroom": "教室に入る",
      "hero_btn_more": "機能を見る",
      "feat_1_title": "意味論的評価",
      "feat_1_desc": "LLMによる高度な理解で、キーワード一致ではなく柔軟な表現を評価します。",
      "feat_2_title": "FSRSスケジューリング",
      "feat_2_desc": "FSRSアルゴリズムが記憶の安定性を計算し、復習間隔を最適化します。",
      "feat_3_title": "AI進捗レポート",
      "feat_3_desc": "AIエージェントが履歴を分析し、深い洞察とアドバイスを生成します。",
      "feat_4_title": "教材統合",
      "feat_4_desc": "多言語対応と定評ある教材体系をサポートし、学習を支援します。",
      "feat_5_title": "圧倒的なコスパ",
      "feat_5_desc": "月額わずか3ユーロ。サーバー維持費のみを頂戴する非営利価格です。",
      "feat_6_title": "学習コミュニティ",
      "feat_6_desc": "グループチャットに参加し、世界中の学習者やAIと交流しましょう。",
      "nav_profile": "プロフィール",
      "nav_overview": "学習概況",
      "nav_settings": "設定",
      "nav_account_title": "アカウント",
      "nav_logout": "ログアウト",
      "settings_title": "個人設定",
      "overview_title": "学習概況",
      "classroom_title": "学習室",
      "classroom_subtitle": "コースを選択して学習を開始しましょう。",
      "classroom_remaining_today": "未復習",
      "classroom_reviewed_today": "復習済み",
      "classroom_new_learned_today": "新規学習",
      "classroom_my_courses": "マイコース",
      "classroom_all_courses": "すべてのコース",
      "classroom_mastered": "習得済み",
      "classroom_start": "学習開始",
      "classroom_add_course": "コースを追加",
      "classroom_filter_learning": "学習言語",
      "classroom_filter_native": "母語",
      "classroom_filter_all": "すべて",
      "classroom_join_course": "コースに参加",
      "classroom_in_learning": "学習中",
      "classroom_added": "追加済み",
      "classroom_active_limit": "学習中 {{count}}/{{max}}。同時に学習できるコースは最大 {{max}} 件です。",
      "classroom_no_courses": "条件に合うコースはありません",
      "classroom_course_lessons": "{{count}} レッスン",
      "classroom_course_items": "{{count}} 単語",
      "btn_add": "追加",
      "course_en_zh": "英語 (中国語経由)",
      "course_fr_zh": "フランス語 (中国語経由)",
      "course_jp_zh": "日本語 (中国語経由)",
      "practice_title_lesson": "授業内強化練習",
      "practice_title_review": "スマート復習練習",
      "practice_prompt_cn_to_en": "英語に翻訳してください",
      "practice_prompt_en_to_cn": "中国語に翻訳してください",
      "practice_prompt_cn_listen_write": "聴いて中国語で書いてください",
      "practice_input_placeholder": "ここに答えを入力してください...",
      "practice_submit": "回答を提出",
      "practice_evaluating": "AI講師が採点中...",
      "practice_retry": "再提出",
      "practice_skip": "この問題をスキップ",
      "practice_next": "次の問題へ",
      "practice_finish": "すべて完了",
      "practice_feedback_excellent": "素晴らしい！",
      "practice_feedback_good": "よくできました。さらに伸ばせます！",
      "practice_feedback_retry": "もう少し頑張りましょう！",
      "practice_eval_failed": "採点サービスに接続できません。再試行してください。",
      "practice_ai_feedback_title": "AIフィードバック",
      "practice_ai_analyzing": "AI講師があなたの回答を分析中...",
      "word_pinyin_btn": "ピンイン",
      "word_translation_btn": "訳",
      "practice_badge_cn_to_en": "翻訳 · 中→英",
      "practice_badge_en_to_cn": "翻訳 · 英→中",
      "practice_badge_speak": "スピーキング · 中国語",
      "practice_badge_dictation": "書き取り · 听写",
      "practice_audio_play": "再生",
      "practice_audio_replay": "再生",
      "practice_audio_played_times": "{{count}} 回再生済み · 繰り返し可",
      "practice_dictation_instruction": "聴いた文を漢字で書いてください",
      "practice_replay_hint": "↑ キーで再生",
      "practice_forfeit": "答えを見る",
      "practice_retry_show_answer": "もう一度答えを見る",
      "practice_std_answer": "模範解答",
      "practice_ai_thinking": "AI講師がフィードバックを生成中",
      "practice_asr_recognized": "認識テキスト",
      "practice_retry_text": "再挑戦",
      "practice_retry_speech": "再録音",
      "practice_skip_question": "スキップ",
      "practice_next_question": "次の問題",
      "practice_finish_round": "今回のラウンド終了",
      "knowledge_title": "知識ポイント",
      "knowledge_current_sense": "現在の意味",
      "knowledge_other_senses": "その他の意味",
      "knowledge_show": "表示",
      "knowledge_hide": "非表示",
      "study_error_load": "コースデータを取得できません。バックエンドがレッスンを同期しているか確認してください。",
      "study_not_enrolled_title": "このコースは学習リストにありません",
      "study_not_enrolled_desc": "コース内容のプレビューは可能です。学習・練習・進捗記録を使うには、先にコースを追加してください。",
      "study_not_enrolled_action": "コース詳細を見る",
      "study_retry": "再試行",
      "teaching_new_unit": "新しいユニット",
      "teaching_video_label": "ビジュアルコンテキストエンジン",
      "teaching_diary_original": "日記原文",
      "teaching_reading": "本文閲読",
      "teaching_content": "本文内容",
      "teaching_dialogue": "会話本文",
      "teaching_pinyin_on": "ピンイン表示",
      "teaching_pinyin_off": "ピンイン非表示",
      "teaching_translation_on": "翻訳表示",
      "teaching_translation_off": "翻訳非表示",
      "teaching_vocab_title": "本課の単語",
      "teaching_example": "例文",
      "teaching_generating_quiz": "クイズを生成中...",
      "teaching_start_quiz": "学習完了、クイズへ",

      // Auth - password reset
      "auth_forgot_password": "パスワードをお忘れですか？",
      "auth_forgot_title": "パスワードをリセット",
      "auth_forgot_subtitle": "メールアドレスを入力して確認コードを受け取ってください",
      "auth_reset_title": "新しいパスワードを設定",
      "auth_reset_subtitle": "確認コードを入力し、新しいパスワードを設定してください",
      "auth_submit_send_code": "コードを送信",
      "auth_submit_reset": "パスワードをリセット",
      "auth_back_to_login": "ログインに戻る",

      // Course page
      "course_back": "コース選択に戻る",
      "course_foundations": "入門基礎",
      "course_all_lessons": "全レッスン",
      "course_no_lessons": "レッスンがありません",
      "course_start_learning": "学習開始",
      "course_progress_label": "コース進捗",
      "course_progress_completed_count": "{{completed}} / {{total}} レッスン完了",
      "course_progress_next_lesson": "次のレッスン",
      "course_progress_start_practice": "解説を見ました。練習へ",
      "course_progress_resume_practice": "練習 {{number}} 問目から再開",
      "course_progress_completed": "コース完了",
      "course_progress_all_done": "すべてのレッスン完了",
      "course_untitled_lesson": "無題のレッスン",
      "course_lesson_completed": "完了",
      "course_lesson_current": "現在のレッスン",
      "course_lesson_not_started": "未開始",
      "course_adding_learning": "追加中...",
      "course_remove_learning": "学習を一時停止",
      "course_remove_failed": "コースを一時停止できませんでした。もう一度お試しください。",
      "course_pause_confirm_eyebrow": "一時停止の確認",
      "course_pause_confirm_title": "このコースを一時停止しますか？",
      "course_pause_confirm_desc": "一時停止すると、{{course}} は「マイコース」から外れます。進捗は保持され、あとで全コースから再追加できます。",
      "course_pause_confirm_action": "一時停止する",
      "course_remove_confirm_eyebrow": "コース管理",
      "course_remove_confirm_title": "一時停止しますか、それとも記録を削除しますか？",
      "course_remove_confirm_desc": "一時停止すると {{course}} の進捗は保持されます。削除すると学習記録、復習記録、レッスン進捗が消え、再追加時は最初から始まります。",
      "course_clear_confirm_action": "記録を削除",
      "course_limit_reached": "同時に学習できるコースは最大2件です。先に1件を完了するか一時停止してください。",
      "course_enroll_failed": "コースを追加できませんでした。もう一度お試しください。",
      "course_preview_before_join": "先にコース構成とレッスン内容を確認できます。学習に追加すると練習と進捗が記録されます。",
      "course_intro_card_title": "コース紹介",
      "course_intro_card_sub": "理念 · 学習方法 · 道筋",
      "course_hanzi_card_title": "漢字入門",
      "course_hanzi_card_sub": "筆画 · 部首 · 構造",
      "course_pinyin_card_title": "ピンイン入門",
      "course_pinyin_card_sub": "声母 · 韻母 · 声調",
      "course_typing_card_title": "タイピング",
      "course_typing_card_sub": "入力法 · ピンイン入力 · 練習",
      "teaching_back_to_course": "コースに戻る"
    }
  },
  fr: {
    translation: {
      "nav_auth": "Connexion/S'inscrire",
      "auth_login": "Connexion",
      "auth_register": "S'inscrire",
      "auth_email": "Adresse E-mail",
      "auth_password": "Mot de passe",
      "auth_confirm_password": "Confirmer le mot de passe",
      "auth_submit_reg": "S'inscrire",
      "auth_submit_login": "Connexion",
      "auth_submit_continue": "Continuer",
      "auth_submit_verify": "Vérifier & Activer",
      "auth_welcome": "Bon retour",
      "auth_create": "Créer un compte",
      "auth_back_home": "Retour à l'accueil",
      "auth_login_subtitle": "Connectez-vous avec votre e-mail",
      "auth_register_subtitle": "Commencez votre voyage d'apprentissage IA",
      "auth_register_tip": "Définissez un mot de passe sécurisé",
      "auth_verify_title": "Vérifiez votre e-mail",
      "auth_verify_subtitle": "Un code a été envoyé à {{email}}",
      "auth_success_title": "Succès !",
      "auth_success_subtitle": "Compte activé. Redirection...",
      "auth_change_email": "Modifier l'e-mail",
      "auth_or_use": "Ou utiliser",
      "auth_login_success_title": "Connexion réussie !",
      "auth_login_success_subtitle": "Retour à l'accueil...",
      "auth_pw_req_length": "8-32 caractères",
      "auth_pw_req_letter": "Contient des lettres",
      "auth_pw_req_number": "Chiffre",
      "auth_pw_req_special": "N'importe quel caractère spécial",
      "auth_pw_req_no_space": "Sans espaces",
      "auth_pw_match": "Mots de passe identiques",
      "hero_badge": "✨ Votre coach linguistique IA propulsé par LLM",
      "hero_title_1": "Pensez et parlez comme un natif",
      "hero_title_2": "Apprentissage IA des langues",
      "hero_desc": "Arrêtez d'apprendre par cœur. Chilan utilise le LLM et l'algorithme FSRS pour une maîtrise efficace.",
      "hero_btn_classroom": "Entrer en classe",
      "hero_btn_more": "Explorer les fonctions",
      "feat_1_title": "Évaluation sémantique",
      "feat_1_desc": "La compréhension LLM permet une expression flexible au lieu d'une correspondance rigide.",
      "feat_2_title": "Planification FSRS",
      "feat_2_desc": "L'algorithme FSRS moderne calcule la stabilité de la mémoire pour optimiser vos intervalles.",
      "feat_3_title": "Rapport de progrès IA",
      "feat_3_desc": "Les agents IA analysent votre historique pour générer des conseils ciblés.",
      "feat_4_title": "Manuels Classiques",
      "feat_4_desc": "Support multi-langues et intégration de manuels réputés pour un apprentissage structuré.",
      "feat_5_title": "Valeur Inégalée",
      "feat_5_desc": "Seulement 3 €/mois. Un prix conçu uniquement pour couvrir les coûts des serveurs.",
      "feat_6_title": "Communauté Mondiale",
      "feat_6_desc": "Rejoignez des groupes et pratiquez avec des apprenants du monde entier et l'IA.",
      "nav_profile": "Profil",
      "nav_overview": "Aperçu",
      "nav_settings": "Paramètres",
      "nav_account_title": "Compte",
      "nav_logout": "Déconnexion",
      "settings_title": "Paramètres personnels",
      "overview_title": "Aperçu de l'apprentissage",
      "classroom_title": "Salle de classe",
      "classroom_subtitle": "Choisissez un cours pour commencer aujourd'hui.",
      "classroom_remaining_today": "À réviser",
      "classroom_reviewed_today": "Révisés",
      "classroom_new_learned_today": "Nouveaux appris",
      "classroom_my_courses": "Mes cours",
      "classroom_all_courses": "Tous les cours",
      "classroom_mastered": "Maîtrisés",
      "classroom_start": "Démarrer",
      "classroom_add_course": "Ajouter un cours",
      "classroom_filter_learning": "Langue cible",
      "classroom_filter_native": "Langue maternelle",
      "classroom_filter_all": "Tout",
      "classroom_join_course": "Rejoindre",
      "classroom_in_learning": "En cours",
      "classroom_added": "Ajouté",
      "classroom_active_limit": "En cours {{count}}/{{max}}. Vous pouvez suivre jusqu'à {{max}} cours à la fois.",
      "classroom_no_courses": "Aucun cours ne correspond aux filtres",
      "classroom_course_lessons": "{{count}} leçons",
      "classroom_course_items": "{{count}} mots",
      "btn_add": "Ajouter",
      "course_en_zh": "Anglais (via CN)",
      "course_fr_zh": "Français (via CN)",
      "course_jp_zh": "Japonais (via CN)",
      "practice_title_lesson": "Exercice intensif en classe",
      "practice_title_review": "Révision intelligente",
      "practice_prompt_cn_to_en": "Traduisez en anglais",
      "practice_prompt_en_to_cn": "Traduisez en chinois",
      "practice_prompt_cn_listen_write": "Écouter et écrire en chinois",
      "practice_input_placeholder": "Saisissez votre réponse ici...",
      "practice_submit": "Soumettre",
      "practice_evaluating": "Le tuteur IA corrige...",
      "practice_retry": "Soumettre à nouveau",
      "practice_skip": "Passer cette question",
      "practice_next": "Question suivante",
      "practice_finish": "Terminer",
      "practice_feedback_excellent": "Excellent !",
      "practice_feedback_good": "Bien, mais il reste une marge de progression !",
      "practice_feedback_retry": "Continuez vos efforts !",
      "practice_eval_failed": "Le service d'évaluation est indisponible. Veuillez réessayer.",
      "practice_ai_feedback_title": "Retour IA",
      "practice_ai_analyzing": "Le tuteur IA analyse votre réponse...",
      "word_pinyin_btn": "Pinyin",
      "word_translation_btn": "Trad",
      "practice_badge_cn_to_en": "Traduire · ZH→EN",
      "practice_badge_en_to_cn": "Traduire · EN→ZH",
      "practice_badge_speak": "Expression orale · en chinois",
      "practice_badge_dictation": "Dictée · 听写",
      "practice_audio_play": "Lire",
      "practice_audio_replay": "Rejouer",
      "practice_audio_played_times": "Lu {{count}} fois · Rejouer à tout moment",
      "practice_dictation_instruction": "Écrivez en chinois la phrase que vous entendez",
      "practice_replay_hint": "Appuyer sur ↑ pour rejouer",
      "practice_forfeit": "Voir la réponse",
      "practice_retry_show_answer": "Réessayer d’afficher la réponse",
      "practice_std_answer": "Réponse correcte",
      "practice_ai_thinking": "Le tuteur IA génère des retours...",
      "practice_asr_recognized": "Texte reconnu",
      "practice_retry_text": "Réessayer",
      "practice_retry_speech": "Réenregistrer",
      "practice_skip_question": "Passer",
      "practice_next_question": "Suivant",
      "practice_finish_round": "Terminer ce tour",
      "knowledge_title": "Détails du point clé",
      "knowledge_current_sense": "Sens actuel",
      "knowledge_other_senses": "Autres sens",
      "knowledge_show": "Afficher",
      "knowledge_hide": "Masquer",
      "study_error_load": "Impossible de charger le cours. Veuillez vérifier que le backend a bien synchronisé la leçon.",
      "study_not_enrolled_title": "Ce cours n'est pas dans votre liste",
      "study_not_enrolled_desc": "Vous pouvez toujours le prévisualiser. Rejoignez-le d'abord pour apprendre, vous entraîner et enregistrer la progression.",
      "study_not_enrolled_action": "Voir le cours",
      "study_retry": "Réessayer",
      "teaching_new_unit": "Nouvelle unité",
      "teaching_video_label": "Moteur de contexte visuel",
      "teaching_diary_original": "Texte du journal",
      "teaching_reading": "Lecture",
      "teaching_content": "Contenu du cours",
      "teaching_dialogue": "Dialogue",
      "teaching_pinyin_on": "Pinyin affiché",
      "teaching_pinyin_off": "Pinyin masqué",
      "teaching_translation_on": "Traduction affichée",
      "teaching_translation_off": "Traduction masquée",
      "teaching_vocab_title": "Vocabulaire",
      "teaching_example": "Exemple",
      "teaching_generating_quiz": "Génération du quiz...",
      "teaching_start_quiz": "Terminer et commencer le quiz",

      // Auth - password reset
      "auth_forgot_password": "Mot de passe oublié ?",
      "auth_forgot_title": "Réinitialiser le mot de passe",
      "auth_forgot_subtitle": "Entrez votre e-mail pour recevoir un code de vérification",
      "auth_reset_title": "Définir un nouveau mot de passe",
      "auth_reset_subtitle": "Entrez le code et définissez votre nouveau mot de passe",
      "auth_submit_send_code": "Envoyer le code",
      "auth_submit_reset": "Réinitialiser",
      "auth_back_to_login": "Retour à la connexion",

      // Course page
      "course_back": "Retour au choix des cours",
      "course_foundations": "Bases",
      "course_all_lessons": "Tous les cours",
      "course_no_lessons": "Aucun cours disponible",
      "course_start_learning": "Commencer",
      "course_progress_label": "Progression du cours",
      "course_progress_completed_count": "{{completed}} / {{total}} leçons terminées",
      "course_progress_next_lesson": "Prochaine leçon",
      "course_progress_start_practice": "Leçon vue. Commencer l'exercice",
      "course_progress_resume_practice": "Reprendre à la question {{number}}",
      "course_progress_completed": "Cours terminé",
      "course_progress_all_done": "Toutes les leçons sont terminées",
      "course_untitled_lesson": "Leçon sans titre",
      "course_lesson_completed": "Terminée",
      "course_lesson_current": "En cours",
      "course_lesson_not_started": "Non commencée",
      "course_adding_learning": "Ajout en cours...",
      "course_remove_learning": "Mettre en pause",
      "course_remove_failed": "Impossible de mettre ce cours en pause. Veuillez réessayer.",
      "course_pause_confirm_eyebrow": "Confirmation",
      "course_pause_confirm_title": "Mettre ce cours en pause ?",
      "course_pause_confirm_desc": "Après la pause, {{course}} sera retiré de Mes cours. Votre progression sera conservée et vous pourrez le rajouter depuis Tous les cours.",
      "course_pause_confirm_action": "Confirmer la pause",
      "course_remove_confirm_eyebrow": "Gestion du cours",
      "course_remove_confirm_title": "Mettre en pause ou effacer ce cours ?",
      "course_remove_confirm_desc": "La pause conserve votre progression pour {{course}}. Effacer supprime les données d'apprentissage, les révisions et la progression de leçon.",
      "course_clear_confirm_action": "Effacer les données",
      "course_limit_reached": "Vous pouvez suivre jusqu'à 2 cours à la fois. Veuillez d'abord en terminer ou en mettre un en pause.",
      "course_enroll_failed": "Impossible d'ajouter ce cours. Veuillez réessayer.",
      "course_preview_before_join": "Vous pouvez d'abord parcourir la structure du cours et les leçons. Ajoutez-le à votre apprentissage pour enregistrer la pratique et la progression.",
      "course_intro_card_title": "Présentation du cours",
      "course_intro_card_sub": "Concepts · méthode · parcours",
      "course_hanzi_card_title": "Bases des caractères",
      "course_hanzi_card_sub": "Traits · radicaux · structure",
      "course_pinyin_card_title": "Bases du pinyin",
      "course_pinyin_card_sub": "Initiales · finales · tons",
      "course_typing_card_title": "Saisie au clavier",
      "course_typing_card_sub": "IME · saisie pinyin · pratique",
      "teaching_back_to_course": "Retour au cours",

      "ci_back": "Retour",
      "ci_badge": "Chilan · Chinois",
      "ci_h1_line1": "Apprendre le chinois",
      "ci_h1_line2": "tel qu'il est vraiment parlé",
      "ci_subtitle": "Un cours propulsé par l'IA qui développe de vraies compétences — écoute, expression orale et saisie — depuis les fondements.",
      "ci_diff_heading": "Ce qui rend ce cours différent",
      "ci_feat0_title": "Retours propulsés par l'IA",
      "ci_feat0_desc": "Évaluation en trois niveaux — vérification regex instantanée, similarité sémantique, puis analyse LLM approfondie. Des retours honnêtes et nuancés à chaque réponse.",
      "ci_feat1_title": "L'écoute en priorité",
      "ci_feat1_desc": "Audio pour chaque mot et phrase. Les exercices de dictée entraînent votre oreille à percevoir les tons et les sons.",
      "ci_feat2_title": "Pratique orale",
      "ci_feat2_desc": "Répondez à voix haute. La reconnaissance vocale et l'IA vérifient votre sens — pas seulement votre prononciation.",
      "ci_feat3_title": "Priorité à la saisie clavier",
      "ci_feat3_desc": "Apprenez à saisir le chinois avec un IME pinyin standard — la méthode utilisée quotidiennement par les locuteurs natifs. Aucune écriture manuelle requise.",
      "ci_feat4_title": "Répétition espacée (FSRS)",
      "ci_feat4_desc": "Chaque question est planifiée par FSRS. Les éléments bien maîtrisés reviennent moins souvent ; les difficiles réapparaissent plus tôt.",
      "ci_feat5_title": "Un progrès visible",
      "ci_feat5_desc": "Votre salle de classe suit les éléments révisés, restants et maîtrisés. Chaque session fait avancer les choses.",
      "ci_no_hw_title": "Nous n'enseignons pas l'écriture manuelle",
      "ci_no_hw_body": "L'ordre des traits et l'écriture sont vraiment importants, mais il s'agit d'une compétence à part qui demande des années de pratique. Ce cours se concentre entièrement sur <strong>la lecture, l'écoute, l'expression orale et la saisie avec un IME pinyin</strong> — les compétences dont la plupart des apprenants ont d'abord besoin.",
      "ci_how_heading": "Comment fonctionne chaque leçon",
      "ci_step0_title": "Phase d'enseignement",
      "ci_step0_desc": "Nouveaux mots avec pinyin, traduction, audio et une explication vidéo optionnelle. Pas de minuterie — prenez votre temps.",
      "ci_step1_title": "Phase de pratique",
      "ci_step1_desc": "Quatre types de questions : traduire en anglais, traduire en chinois, parler à voix haute ou écrire à partir d'une dictée audio.",
      "ci_step2_title": "Évaluation IA",
      "ci_step2_desc": "Vérification en trois niveaux — correspondance exacte, similarité sémantique, puis jugement LLM complet avec explication pour les cas limites.",
      "ci_step3_title": "Planification FSRS",
      "ci_step3_desc": "En fonction de votre résultat, FSRS calcule exactement quand vous montrer cet élément à nouveau — heures, jours ou semaines.",
      "ci_cta_text": "Prêt à commencer ? Débutez par les modules fondamentaux.",
      "ci_cta_hanzi": "Caractères chinois →",
      "ci_cta_pinyin": "Pinyin",

      "hi_back": "Retour",
      "hi_badge": "Fondations · 基础",
      "hi_h1": "Les caractères chinois",
      "hi_subtitle": "Avant de plonger dans le vocabulaire, il est utile de comprendre ce que sont les caractères chinois et comment ils sont construits. Il s'agit d'un aperçu conceptuel — aucune mémorisation requise.",
      "hi_reading_only": "Lecture seule — pas de questions de pratique ici",
      "hi_what_h2": "Qu'est-ce qu'un caractère chinois ?",
      "hi_what_p1": "Chaque caractère chinois est un <strong>logogramme</strong> — un symbole écrit qui représente un morphème (une unité de sens et de son), pas seulement un son. Le caractère 山 signifie <em>montagne</em> et se prononce <em>shān</em>. Le sens et le son sont tous deux liés à ce symbole unique.",
      "hi_what_p2": "Le mandarin moderne utilise environ <strong>3 000 à 4 000 caractères</strong> pour la lecture courante. Le HSK 6 (avancé) en couvre environ 5 000. La bonne nouvelle : la plupart des caractères sont composés de petits éléments récurrents, ce qui fait émerger des structures rapidement.",
      "hi_what_p3": "Contrairement aux écritures alphabétiques, le chinois n'a pas de majuscules ni de minuscules, pas d'espaces entre les mots, et les caractères n'indiquent pas directement leur prononciation — c'est à cela que sert le <strong>pinyin</strong>.",
      "hi_strokes_h2": "Les traits de base",
      "hi_strokes_intro": "Chaque caractère est construit à partir d'un petit ensemble de traits de pinceau fondamentaux. Il existe environ 6 à 8 types de base ; tout le reste est une variante ou une combinaison.",
      "hi_strokes_note": "Nous n'enseignons pas l'ordre des traits dans ce cours, mais connaître ces noms aide à chercher des caractères dans un dictionnaire.",
      "hi_stroke0_desc": "Horizontal — de gauche à droite",
      "hi_stroke1_desc": "Vertical — de haut en bas",
      "hi_stroke2_desc": "Balayage tombant à gauche",
      "hi_stroke3_desc": "Pression tombant à droite",
      "hi_stroke4_desc": "Point",
      "hi_stroke5_desc": "Virage / coude (y compris les crochets)",
      "hi_radicals_h2": "Les radicaux (部首 bùshǒu)",
      "hi_radicals_intro": "Les radicaux sont des composants récurrents qui donnent souvent un indice sur la <strong>catégorie de sens</strong> d'un caractère. Les dictionnaires sont traditionnellement organisés par radical. Les reconnaître rend les nouveaux caractères plus faciles à deviner et à mémoriser.",
      "hi_rad0_meaning": "eau", "hi_rad0_hint": "trois points à gauche", "hi_rad0_ex": "河 rivière · 海 mer · 洗 laver",
      "hi_rad1_meaning": "bois / arbre", "hi_rad1_hint": "seul ou comme 木 à gauche", "hi_rad1_ex": "树 arbre · 林 forêt · 桌 table",
      "hi_rad2_meaning": "bouche", "hi_rad2_hint": "forme de petite boîte", "hi_rad2_ex": "吃 manger · 喝 boire · 说 parler",
      "hi_rad3_meaning": "personne", "hi_rad3_hint": "silhouette debout ou radical latéral", "hi_rad3_ex": "他 il · 你 tu · 做 faire",
      "hi_rad4_meaning": "cœur / esprit", "hi_rad4_hint": "seul ou trois points à gauche", "hi_rad4_ex": "想 penser · 忘 oublier · 情 émotion",
      "hi_rad5_meaning": "parole / mots", "hi_rad5_hint": "simplifié en deux points + trait à gauche", "hi_rad5_ex": "说 parler · 话 mots · 读 lire",
      "hi_radicals_tip": "<strong>Conseil :</strong> Les radicaux ne permettent pas toujours de prédire la prononciation, et un caractère peut avoir plusieurs composants. Considérez-les comme des indices sémantiques approximatifs, pas comme des règles strictes.",
      "hi_struct_h2": "Comment les caractères sont structurés",
      "hi_struct_intro": "Les caractères combinent des composants selon des arrangements spatiaux prévisibles. Une fois le schéma compris, on commence à « lire » la forme des nouveaux caractères d'un coup d'œil.",
      "hi_struct0_type": "Gauche–droite  左右", "hi_struct0_desc": "Deux composants ou plus placés côte à côte. La structure la plus courante en chinois.",
      "hi_struct0_ex0_m": "bien", "hi_struct0_ex0_b": "女 (femme) + 子 (enfant)",
      "hi_struct0_ex1_m": "brillant", "hi_struct0_ex1_b": "日 (soleil) + 月 (lune)",
      "hi_struct0_ex2_m": "s'il vous plaît / inviter", "hi_struct0_ex2_b": "讠(parole) + 青 (bleu/clair)",
      "hi_struct1_type": "Haut–bas  上下", "hi_struct1_desc": "Un composant empilé sur un autre.",
      "hi_struct1_ex0_m": "caractère / mot", "hi_struct1_ex0_b": "宀 (toit) + 子 (enfant)",
      "hi_struct1_ex1_m": "penser", "hi_struct1_ex1_b": "田 (champ) + 心 (cœur)",
      "hi_struct1_ex2_m": "masculin", "hi_struct1_ex2_b": "田 (champ) + 力 (force)",
      "hi_struct2_type": "Encadrement  包围", "hi_struct2_desc": "Un composant entoure un autre — totalement ou sur trois côtés.",
      "hi_struct2_ex0_m": "pays", "hi_struct2_ex0_b": "囗 (frontière) + 玉 (jade)",
      "hi_struct2_ex1_m": "demander", "hi_struct2_ex1_b": "门 (porte) + 口 (bouche)",
      "hi_struct2_ex2_m": "jardin", "hi_struct2_ex2_b": "囗 (frontière) + 元",
      "hi_struct3_type": "Unité simple  独体", "hi_struct3_desc": "Un caractère unique et indivisible — souvent un pictogramme du chinois ancien.",
      "hi_struct3_ex0_m": "montagne", "hi_struct3_ex0_b": "Trois pics — forme de montagne",
      "hi_struct3_ex1_m": "soleil / jour", "hi_struct3_ex1_b": "Cercle avec une ligne — le soleil",
      "hi_struct3_ex2_m": "bois / arbre", "hi_struct3_ex2_b": "Arbre avec racines et branches",
      "hi_typing_h2": "Saisir les caractères chinois",
      "hi_typing_p1": "Dans ce cours, vous saisissez le chinois avec un <strong>IME pinyin</strong> (éditeur de méthode de saisie) — la même méthode utilisée par pratiquement tous les locuteurs natifs sur téléphone et ordinateur. Vous tapez la prononciation romanisée, et l'IME propose les caractères correspondants.",
      "hi_typing_p2": "Par exemple, taper <code>hao</code> et sélectionner le bon caractère donne 好. Vous n'avez pas besoin de savoir tracer le caractère pour le produire numériquement.",
      "hi_typing_p3": "C'est pourquoi <strong>la maîtrise du pinyin passe en premier</strong> : une saisie précise dépend de la connaissance de la prononciation de chaque caractère.",
      "hi_cta_text": "Maintenant que vous avez un modèle mental des caractères chinois, vous êtes prêt pour le système phonétique.",
      "hi_cta_btn": "Continuer vers le Pinyin",

      "civ_welcome_h1": "Apprendre le Chinois",
      "civ_welcome_accent": "tel qu'on l'utilise vraiment",
      "civ_welcome_sub": "Propulsé par IA · communication d'abord · conçu pour l'ère numérique",
      "civ_sounds_label": "Fondation — Étape 1",
      "civ_sounds_h2_pre": "On commence par les ",
      "civ_sounds_h2_accent": "sons",
      "civ_sounds_sub": "Avant les mots, avant la grammaire — maîtrisez les 4 tons qui changent tout.",
      "civ_sounds_tone0_label": "1er ton", "civ_sounds_tone0_name": "haut et égal",
      "civ_sounds_tone1_label": "2e ton", "civ_sounds_tone1_name": "montant",
      "civ_sounds_tone2_label": "3e ton", "civ_sounds_tone2_name": "descendant-montant",
      "civ_sounds_tone3_label": "4e ton", "civ_sounds_tone3_name": "descendant",
      "civ_sounds_example": "妈 (maman) · 麻 (chanvre) · 马 (cheval) · 骂 (gronder) — même syllabe, quatre sens différents",
      "civ_skills_label": "Ce que vous pratiquerez",
      "civ_skills_h2_pre": "Trois compétences, ",
      "civ_skills_h2_accent": "un seul cours",
      "civ_skills_sk0_label": "Écouter", "civ_skills_sk0_sub": "Audio pour chaque mot et phrase. Les exercices de dictée entraînent votre oreille.",
      "civ_skills_sk1_label": "Parler", "civ_skills_sk1_sub": "Enregistrez votre voix. L'IA vérifie votre sens, pas seulement la prononciation.",
      "civ_skills_sk2_label": "Taper", "civ_skills_sk2_sub": "IME Pinyin — comment les locuteurs natifs écrivent chaque jour sur téléphone et ordinateur.",
      "civ_skills_no_hw": "L'écriture manuscrite est une compétence distincte — ce cours se concentre entièrement sur la lecture, l'écoute, la parole et la saisie.",
      "civ_ai_label": "Comment les réponses sont évaluées",
      "civ_ai_h2_pre": "L'IA évalue",
      "civ_ai_h2_accent": "chaque réponse",
      "civ_ai_sub": "Un système à trois niveaux : correspondance instantanée → similarité sémantique → analyse LLM complète. Le sens compte plus que le libellé exact.",
      "civ_ai_example_label": "exemple",
      "civ_ai_example_ans1": "« Qu'est-ce que vous faites habituellement ? »",
      "civ_ai_example_ans2": "« Qu'est-ce que vous faites normalement ? »",
      "civ_ai_example_note": "Les deux acceptées — même sens, mots différents",
      "civ_ai_tier0_label": "Correspondance exacte", "civ_ai_tier0_desc": "Vérification regex / motif — instantanée",
      "civ_ai_tier1_label": "Sémantique", "civ_ai_tier1_desc": "Score de similarité d'embedding",
      "civ_ai_tier2_label": "Analyse IA", "civ_ai_tier2_desc": "Jugement LLM + explication",
      "civ_fsrs_label": "Science de la mémoire",
      "civ_fsrs_h2_pre": "Rien ne passe à travers ",
      "civ_fsrs_h2_accent": "les mailles",
      "civ_fsrs_sub": "FSRS — le Planificateur de Répétition Espacée Gratuit — calcule exactement quand réviser chaque mot.",
      "civ_fsrs_chart_label": "exemple de calendrier de révision pour un mot",
      "civ_fsrs_leg0": "révisions fréquentes au début", "civ_fsrs_leg1": "l'espacement augmente", "civ_fsrs_leg2": "rétention à long terme",
      "civ_start_label": "Votre parcours",
      "civ_start_h2_pre": "Prêt à ",
      "civ_start_h2_accent": "commencer ?",
      "civ_start_sub": "Commencez par les fondations — tout le reste se construit dessus.",
      "civ_start_step0_label": "Pinyin", "civ_start_step0_sub": "Sons et tons",
      "civ_start_step1_label": "Caractères", "civ_start_step1_sub": "Structure et radicaux",
      "civ_start_step2_label": "Vocabulaire", "civ_start_step2_sub": "Mots en contexte",
      "civ_start_step3_label": "Phrases", "civ_start_step3_sub": "Structures grammaticales",
      "civ_start_note": "Utilisez les modules de base dans la salle de classe pour commencer.",
      "civ_narration_welcome": "Bienvenue sur Chilan — une plateforme d'apprentissage du chinois propulsée par l'IA. Ce cours développe de vraies compétences de communication : écoute, expression orale et saisie au clavier. Nous partons des principes de base, en commençant par le système phonétique.",
      "civ_narration_sounds": "Chaque syllabe chinoise a un ton, et changer le ton change complètement le sens. Les quatre tons sont haut et égal, montant, descendant-montant et descendant. Maîtriser les tons est la base la plus importante du chinois.",
      "civ_narration_skills": "Ce cours entraîne trois compétences clés : l'écoute, l'expression orale et la saisie avec une méthode de saisie pinyin. Nous nous concentrons sur l'utilisation réelle du chinois dans la vie numérique quotidienne — pas l'écriture manuscrite. Vous pourrez bientôt lire, écouter, parler et taper.",
      "civ_narration_ai": "Chaque réponse que vous soumettez est évaluée par un système à trois niveaux. La correspondance de motif instantanée gère les cas évidents. La comparaison sémantique détecte les réponses qui ont le même sens avec des mots différents. Et un grand modèle de langage gère les vrais cas limites avec une explication détaillée.",
      "civ_narration_fsrs": "Votre calendrier de révision est alimenté par FSRS — le Planificateur de Répétition Espacée Gratuit. Les éléments que vous connaissez bien reviennent moins souvent. Les éléments difficiles réapparaissent plus tôt. Cela garantit que vous consacrez votre temps d'étude exactement là où c'est nécessaire.",
      "civ_narration_start": "Vous êtes prêt à commencer. Démarrez avec les modules de base : le pinyin pour le système phonétique, puis les caractères chinois pour la structure. Chaque leçon du cours s'appuie sur ces fondations."
    }
  },
  de: {
    translation: {
      "nav_auth": "Anmelden/Registrieren",
      "auth_login": "Anmelden",
      "auth_register": "Registrieren",
      "auth_email": "E-Mail-Adresse",
      "auth_password": "Passwort",
      "auth_confirm_password": "Passwort bestätigen",
      "auth_submit_reg": "Registrieren",
      "auth_submit_login": "Anmelden",
      "auth_submit_continue": "Weiter",
      "auth_submit_verify": "Verifizieren",
      "auth_welcome": "Willkommen zurück",
      "auth_create": "Konto erstellen",
      "auth_back_home": "Zur Startseite",
      "auth_login_subtitle": "Anmeldung mit Ihrer E-Mail",
      "auth_register_subtitle": "Starte deine KI-Lernreise",
      "auth_register_tip": "Lege ein sicheres Passwort fest",
      "auth_verify_title": "E-Mail verifizieren",
      "auth_verify_subtitle": "Code wurde an {{email}} gesendet",
      "auth_success_title": "Erfolg!",
      "auth_success_subtitle": "Konto aktiviert. Weiterleitung...",
      "auth_change_email": "E-Mail ändern",
      "auth_or_use": "Oder verwenden",
      "auth_login_success_title": "Anmeldung erfolgreich!",
      "auth_login_success_subtitle": "Zurück zur Startseite...",
      "auth_pw_req_length": "8-32 Zeichen",
      "auth_pw_req_letter": "Buchstaben enthalten",
      "auth_pw_req_number": "Zahlen",
      "auth_pw_req_special": "Beliebiges Sonderzeichen",
      "auth_pw_req_no_space": "Keine Leerzeichen",
      "auth_pw_match": "Passwörter stimmen überein",
      "hero_badge": "✨ Dein KI-Sprachcoach mit LLM",
      "hero_title_1": "Denken und sprechen wie ein Native",
      "hero_title_2": "KI-Sprachlernen",
      "hero_desc": "Kein stures Auswendiglernen mehr. Chilan nutzt LLM und FSRS für effizientes Sprachenlernen.",
      "hero_btn_classroom": "Klassenzimmer",
      "hero_btn_more": "Funktionen",
      "feat_1_title": "Semantische Bewertung",
      "feat_1_desc": "KI versteht flexible Ausdrücke statt nur starrer Keyword-Abgleiche.",
      "feat_2_title": "FSRS-Planung",
      "feat_2_desc": "Der FSRS-Algorithmus optimiert Ihre Wiederholungsintervalle wissenschaftlich.",
      "feat_3_title": "KI-Fortschrittsbericht",
      "feat_3_desc": "KI-Agenten analysieren Ihren Verlauf für gezielte Ratschläge.",
      "feat_4_title": "Klassische Lehrbücher",
      "feat_4_desc": "Unterstützung für mehrere Sprachen und erstklassige Lehrwerke.",
      "feat_5_title": "Top Preis-Leistung",
      "feat_5_desc": "Nur 3 €/Monat. Non-Profit-Preis zur Deckung der Serverkosten.",
      "feat_6_title": "Globale Community",
      "feat_6_desc": "Tritt Gruppen bei und übe mit Lernenden weltweit und der KI.",
      "nav_profile": "Profil",
      "nav_overview": "Übersicht",
      "nav_settings": "Einstellungen",
      "nav_account_title": "Konto",
      "nav_logout": "Abmelden",
      "settings_title": "Einstellungen",
      "overview_title": "Lernübersicht",
      "classroom_title": "Klassenzimmer",
      "classroom_subtitle": "Wähle einen Kurs und starte heute.",
      "classroom_remaining_today": "Wiederholen",
      "classroom_reviewed_today": "Gelernt",
      "classroom_new_learned_today": "Neu gelernt",
      "classroom_my_courses": "Meine Kurse",
      "classroom_all_courses": "Alle Kurse",
      "classroom_mastered": "Gelernt",
      "classroom_start": "Starten",
      "classroom_add_course": "Kurs hinzufügen",
      "classroom_filter_learning": "Lernsprache",
      "classroom_filter_native": "Muttersprache",
      "classroom_filter_all": "Alle",
      "classroom_join_course": "Kurs beitreten",
      "classroom_in_learning": "Im Lernen",
      "classroom_added": "Hinzugefügt",
      "classroom_active_limit": "Aktiv {{count}}/{{max}}. Du kannst höchstens {{max}} Kurse gleichzeitig lernen.",
      "classroom_course_lessons": "{{count}} Lektionen",
      "classroom_course_items": "{{count}} Vokabeln",
      "classroom_no_courses": "Keine Kurse passen zu den Filtern",
      "btn_add": "Hinzufügen",
      "course_en_zh": "Englisch (via CN)",
      "course_fr_zh": "Französisch (via CN)",
      "course_jp_zh": "Japanisch (via CN)",
      "practice_title_lesson": "Intensives Üben im Unterricht",
      "practice_title_review": "Intelligente Wiederholung",
      "practice_prompt_cn_to_en": "Ins Englische übersetzen",
      "practice_prompt_en_to_cn": "Ins Chinesische übersetzen",
      "practice_prompt_cn_listen_write": "Hören und auf Chinesisch schreiben",
      "practice_input_placeholder": "Gib hier deine Antwort ein...",
      "practice_submit": "Antwort absenden",
      "practice_evaluating": "KI-Lehrer bewertet...",
      "practice_retry": "Erneut absenden",
      "practice_skip": "Diese Frage überspringen",
      "practice_next": "Nächste Frage",
      "practice_finish": "Alles abschließen",
      "practice_feedback_excellent": "Ausgezeichnet!",
      "practice_feedback_good": "Gut, aber es gibt noch Luft nach oben!",
      "practice_feedback_retry": "Weiter üben!",
      "practice_eval_failed": "Bewertungsdienst nicht verfügbar. Bitte erneut versuchen.",
      "practice_ai_feedback_title": "KI-Feedback",
      "practice_ai_analyzing": "KI-Lehrer analysiert deine Antwort...",
      "word_pinyin_btn": "Pinyin",
      "word_translation_btn": "Übers",
      "practice_badge_cn_to_en": "Übersetzen · ZH→EN",
      "practice_badge_en_to_cn": "Übersetzen · EN→ZH",
      "practice_badge_speak": "Sprechen · auf Chinesisch",
      "practice_badge_dictation": "Diktat · 听写",
      "practice_audio_play": "Abspielen",
      "practice_audio_replay": "Wiederholen",
      "practice_audio_played_times": "{{count}} Mal abgespielt · Beliebig wiederholbar",
      "practice_dictation_instruction": "Schreibe den gehörten Satz auf Chinesisch",
      "practice_replay_hint": "↑ drücken zum Wiederholen",
      "practice_forfeit": "Antwort anzeigen",
      "practice_retry_show_answer": "Antwort erneut anzeigen",
      "practice_std_answer": "Musterlösung",
      "practice_ai_thinking": "KI-Lehrer erstellt Feedback...",
      "practice_asr_recognized": "Erkannter Text",
      "practice_retry_text": "Nochmals versuchen",
      "practice_retry_speech": "Neu aufnehmen",
      "practice_skip_question": "Überspringen",
      "practice_next_question": "Nächste",
      "practice_finish_round": "Runde beenden",
      "knowledge_title": "Wissensdetails",
      "knowledge_current_sense": "Aktuelle Bedeutung",
      "knowledge_other_senses": "Weitere Bedeutungen",
      "knowledge_show": "Anzeigen",
      "knowledge_hide": "Ausblenden",
      "study_error_load": "Kursdaten konnten nicht geladen werden. Bitte prüfe, ob das Backend die Lektion synchronisiert hat.",
      "study_not_enrolled_title": "Dieser Kurs ist nicht in deiner Lernliste",
      "study_not_enrolled_desc": "Du kannst den Kurs weiterhin ansehen. Füge ihn zuerst hinzu, wenn du lernen, üben und Fortschritt speichern möchtest.",
      "study_not_enrolled_action": "Kurs ansehen",
      "study_retry": "Erneut versuchen",
      "teaching_new_unit": "Neue Einheit",
      "teaching_video_label": "Visuelle Kontext-Engine",
      "teaching_diary_original": "Tagebuchtext",
      "teaching_reading": "Lesetext",
      "teaching_content": "Lektionsinhalt",
      "teaching_dialogue": "Dialog",
      "teaching_pinyin_on": "Pinyin an",
      "teaching_pinyin_off": "Pinyin aus",
      "teaching_translation_on": "Übersetzung an",
      "teaching_translation_off": "Übersetzung aus",
      "teaching_vocab_title": "Vokabeln",
      "teaching_example": "Beispiel",
      "teaching_generating_quiz": "Quiz wird erstellt...",
      "teaching_start_quiz": "Lektion beenden & Quiz starten",

      // Auth - password reset
      "auth_forgot_password": "Passwort vergessen?",
      "auth_forgot_title": "Passwort zurücksetzen",
      "auth_forgot_subtitle": "Gib deine E-Mail ein, um einen Verifizierungscode zu erhalten",
      "auth_reset_title": "Neues Passwort setzen",
      "auth_reset_subtitle": "Gib den Code ein und setze dein neues Passwort",
      "auth_submit_send_code": "Code senden",
      "auth_submit_reset": "Passwort zurücksetzen",
      "auth_back_to_login": "Zurück zur Anmeldung",

      // Course page
      "course_back": "Zurück zur Kursauswahl",
      "course_foundations": "Grundlagen",
      "course_all_lessons": "Alle Lektionen",
      "course_no_lessons": "Keine Lektionen verfügbar",
      "course_start_learning": "Starten",
      "course_progress_label": "Kursfortschritt",
      "course_progress_completed_count": "{{completed}} / {{total}} Lektionen abgeschlossen",
      "course_progress_next_lesson": "Nächste Lektion",
      "course_progress_start_practice": "Erklärung gesehen. Übung starten",
      "course_progress_resume_practice": "Bei Frage {{number}} fortfahren",
      "course_progress_completed": "Kurs abgeschlossen",
      "course_progress_all_done": "Alle Lektionen abgeschlossen",
      "course_untitled_lesson": "Unbenannte Lektion",
      "course_lesson_completed": "Abgeschlossen",
      "course_lesson_current": "Aktuell",
      "course_lesson_not_started": "Nicht begonnen",
      "course_adding_learning": "Wird hinzugefügt...",
      "course_remove_learning": "Pausieren",
      "course_remove_failed": "Der Kurs konnte nicht pausiert werden. Bitte versuche es erneut.",
      "course_pause_confirm_eyebrow": "Pause bestätigen",
      "course_pause_confirm_title": "Diesen Kurs pausieren?",
      "course_pause_confirm_desc": "{{course}} wird aus „Meine Kurse“ entfernt. Dein Fortschritt bleibt erhalten und du kannst den Kurs später wieder hinzufügen.",
      "course_pause_confirm_action": "Pause bestätigen",
      "course_remove_confirm_eyebrow": "Kursverwaltung",
      "course_remove_confirm_title": "Diesen Kurs pausieren oder löschen?",
      "course_remove_confirm_desc": "Pausieren behält deinen Fortschritt für {{course}}. Löschen entfernt Lernstand, Wiederholungsprotokolle und Lektionsfortschritt.",
      "course_clear_confirm_action": "Daten löschen",
      "course_limit_reached": "Du kannst höchstens 2 Kurse gleichzeitig lernen. Bitte schließe zuerst einen Kurs ab oder pausiere ihn.",
      "course_enroll_failed": "Der Kurs konnte nicht hinzugefügt werden. Bitte versuche es erneut.",
      "course_preview_before_join": "Sie können zuerst Kursstruktur und Lektionen ansehen. Fügen Sie den Kurs hinzu, wenn Übungen und Fortschritt gespeichert werden sollen.",
      "course_intro_card_title": "Kurseinführung",
      "course_intro_card_sub": "Konzept · Lernweise · Pfad",
      "course_hanzi_card_title": "Hanzi-Grundlagen",
      "course_hanzi_card_sub": "Striche · Radikale · Struktur",
      "course_pinyin_card_title": "Pinyin-Grundlagen",
      "course_pinyin_card_sub": "Initialen · Finale · Töne",
      "course_typing_card_title": "Tippen",
      "course_typing_card_sub": "IME · Pinyin-Eingabe · Übung",
      "teaching_back_to_course": "Zurück zum Kurs"
    }
  }
};

const NEW_LOCALE_OVERRIDES = {
  ko: {
    "nav_auth": "로그인/가입", "nav_profile": "프로필", "nav_overview": "학습 개요", "nav_settings": "설정", "nav_account_title": "계정", "nav_logout": "로그아웃",
    "auth_login": "로그인", "auth_register": "가입", "auth_email": "이메일", "auth_password": "비밀번호", "auth_confirm_password": "비밀번호 확인", "auth_submit_login": "로그인", "auth_submit_reg": "가입", "auth_welcome": "다시 오신 것을 환영합니다", "auth_create": "새 계정 만들기", "auth_back_home": "홈으로 돌아가기", "auth_login_subtitle": "이메일로 계정에 로그인하세요", "auth_register_subtitle": "AI 언어 학습 여정을 시작하세요", "auth_or_use": "또는 다음으로 계속",
    "hero_badge": "✨ LLM 기반 AI 언어 튜터", "hero_title_1": "원어민처럼 생각하고 말하기", "hero_title_2": "AI 언어 학습", "hero_desc": "기계적인 암기에서 벗어나세요. Chilan은 LLM과 FSRS로 더 효율적인 언어 학습을 돕습니다.", "hero_btn_classroom": "교실로 이동", "hero_btn_more": "기능 보기",
    "feat_1_title": "의미 기반 평가", "feat_1_desc": "AI가 단순 키워드가 아니라 답변의 의미를 이해합니다.", "feat_2_title": "FSRS 복습 일정", "feat_2_desc": "과학적인 간격 반복으로 복습 시점을 최적화합니다.", "feat_3_title": "AI 주간 리포트", "feat_3_desc": "학습 기록을 분석해 약점을 찾아줍니다.", "feat_4_title": "검증된 교재", "feat_4_desc": "여러 언어와 고전 교재 체계를 지원합니다.", "feat_5_title": "높은 가성비", "feat_5_desc": "서버 비용을 위한 낮은 월 구독료.", "feat_6_title": "글로벌 커뮤니티", "feat_6_desc": "전 세계 학습자와 AI와 함께 연습하세요.",
    "settings_title": "설정", "overview_title": "학습 개요", "classroom_title": "학습 교실", "classroom_subtitle": "오늘 학습할 코스를 선택하세요.", "classroom_remaining_today": "오늘 복습", "classroom_reviewed_today": "오늘 완료", "classroom_new_learned_today": "오늘 새 학습", "classroom_my_courses": "내 코스", "classroom_all_courses": "전체 코스", "classroom_mastered": "숙달", "classroom_start": "시작", "classroom_filter_learning": "학습 언어", "classroom_filter_native": "모국어", "classroom_filter_all": "전체", "classroom_join_course": "코스 참여", "classroom_in_learning": "학습 중", "classroom_added": "추가됨", "classroom_no_courses": "조건에 맞는 코스가 없습니다", "classroom_course_lessons": "{{count}}개 레슨", "classroom_course_items": "{{count}}개 단어", "btn_add": "추가",
    "course_back": "코스 선택으로 돌아가기", "course_foundations": "기초", "course_all_lessons": "전체 레슨", "course_no_lessons": "레슨이 없습니다", "course_start_learning": "학습 시작", "course_intro_card_title": "코스 소개", "course_intro_card_sub": "개념 · 학습 방식 · 경로", "course_hanzi_card_title": "한자 기초", "course_hanzi_card_sub": "획 · 부수 · 구조", "course_pinyin_card_title": "병음 기초", "course_pinyin_card_sub": "성모 · 운모 · 성조", "course_typing_card_title": "타이핑", "course_typing_card_sub": "입력기 · 병음 입력 · 연습", "teaching_back_to_course": "코스로 돌아가기",
    "practice_submit": "답안 제출", "practice_evaluating": "AI 튜터가 채점 중...", "practice_retry": "다시 제출", "practice_skip": "건너뛰기", "practice_next": "다음 문제", "practice_finish": "완료", "practice_ai_feedback_title": "AI 피드백", "practice_audio_play": "재생", "practice_audio_replay": "다시 재생", "practice_std_answer": "정답", "practice_next_question": "다음 문제", "practice_finish_round": "이번 연습 완료", "teaching_new_unit": "새 단원", "teaching_vocab_title": "이번 레슨 단어", "teaching_example": "예문", "teaching_start_quiz": "학습 완료, 퀴즈 시작"
  },
  es: {
    "nav_auth": "Iniciar sesión/Registrarse", "nav_profile": "Perfil", "nav_overview": "Resumen", "nav_settings": "Ajustes", "nav_account_title": "Cuenta", "nav_logout": "Cerrar sesión",
    "auth_login": "Iniciar sesión", "auth_register": "Registrarse", "auth_email": "Correo electrónico", "auth_password": "Contraseña", "auth_confirm_password": "Confirmar contraseña", "auth_submit_login": "Iniciar sesión", "auth_submit_reg": "Registrarse", "auth_welcome": "Bienvenido de nuevo", "auth_create": "Crear cuenta", "auth_back_home": "Volver al inicio", "auth_login_subtitle": "Inicia sesión con tu correo", "auth_register_subtitle": "Empieza tu aprendizaje con IA", "auth_or_use": "O usar",
    "hero_badge": "✨ Tu tutor de idiomas con LLM", "hero_title_1": "Piensa y habla como un nativo", "hero_title_2": "Aprendizaje de idiomas con IA", "hero_desc": "Deja atrás la memorización mecánica. Chilan usa LLM y FSRS para ayudarte a aprender mejor.", "hero_btn_classroom": "Entrar al aula", "hero_btn_more": "Ver funciones",
    "feat_1_title": "Evaluación semántica", "feat_1_desc": "La IA entiende el sentido de tus respuestas.", "feat_2_title": "Planificación FSRS", "feat_2_desc": "Optimiza tus repasos con repetición espaciada.", "feat_3_title": "Informe con IA", "feat_3_desc": "Analiza tu progreso y detecta puntos débiles.", "feat_4_title": "Materiales clásicos", "feat_4_desc": "Soporta varios idiomas y cursos estructurados.", "feat_5_title": "Precio justo", "feat_5_desc": "Una cuota baja para cubrir costes de servidor.", "feat_6_title": "Comunidad global", "feat_6_desc": "Practica con estudiantes de todo el mundo y con la IA.",
    "settings_title": "Ajustes", "overview_title": "Resumen de aprendizaje", "classroom_title": "Aula", "classroom_subtitle": "Elige un curso y empieza hoy.", "classroom_remaining_today": "Por repasar", "classroom_reviewed_today": "Repasado hoy", "classroom_new_learned_today": "Nuevo hoy", "classroom_my_courses": "Mis cursos", "classroom_all_courses": "Todos los cursos", "classroom_mastered": "Dominado", "classroom_start": "Empezar", "classroom_filter_learning": "Idioma de estudio", "classroom_filter_native": "Idioma nativo", "classroom_filter_all": "Todos", "classroom_join_course": "Unirse", "classroom_in_learning": "En curso", "classroom_added": "Añadido", "classroom_no_courses": "No hay cursos con esos filtros", "classroom_course_lessons": "{{count}} lecciones", "classroom_course_items": "{{count}} palabras", "btn_add": "Añadir",
    "course_back": "Volver a cursos", "course_foundations": "Fundamentos", "course_all_lessons": "Todas las lecciones", "course_no_lessons": "No hay lecciones", "course_start_learning": "Empezar", "course_intro_card_title": "Introducción", "course_intro_card_sub": "Conceptos · método · ruta", "course_hanzi_card_title": "Bases de Hanzi", "course_hanzi_card_sub": "Trazos · radicales · estructura", "course_pinyin_card_title": "Bases de Pinyin", "course_pinyin_card_sub": "Iniciales · finales · tonos", "course_typing_card_title": "Tecleo", "course_typing_card_sub": "IME · pinyin · práctica", "teaching_back_to_course": "Volver al curso",
    "practice_submit": "Enviar respuesta", "practice_evaluating": "El tutor IA está evaluando...", "practice_retry": "Reintentar", "practice_skip": "Saltar", "practice_next": "Siguiente", "practice_finish": "Finalizar", "practice_ai_feedback_title": "Comentarios de IA", "practice_audio_play": "Reproducir", "practice_audio_replay": "Repetir", "practice_std_answer": "Respuesta modelo", "practice_next_question": "Siguiente pregunta", "practice_finish_round": "Terminar ronda", "teaching_new_unit": "Nueva unidad", "teaching_vocab_title": "Vocabulario", "teaching_example": "Ejemplo", "teaching_start_quiz": "Terminar y empezar prueba"
  },
  vi: {
    "nav_auth": "Đăng nhập/Đăng ký", "nav_profile": "Hồ sơ", "nav_overview": "Tổng quan", "nav_settings": "Cài đặt", "nav_account_title": "Tài khoản", "nav_logout": "Đăng xuất",
    "auth_login": "Đăng nhập", "auth_register": "Đăng ký", "auth_email": "Email", "auth_password": "Mật khẩu", "auth_confirm_password": "Xác nhận mật khẩu", "auth_submit_login": "Đăng nhập", "auth_submit_reg": "Đăng ký", "auth_welcome": "Chào mừng trở lại", "auth_create": "Tạo tài khoản", "auth_back_home": "Về trang chủ", "auth_login_subtitle": "Đăng nhập bằng email của bạn", "auth_register_subtitle": "Bắt đầu hành trình học ngôn ngữ với AI", "auth_or_use": "Hoặc dùng",
    "hero_badge": "✨ Gia sư ngôn ngữ AI dùng LLM", "hero_title_1": "Suy nghĩ và nói như người bản xứ", "hero_title_2": "Học ngôn ngữ với AI", "hero_desc": "Tạm biệt học vẹt. Chilan dùng LLM và FSRS để giúp bạn học hiệu quả hơn.", "hero_btn_classroom": "Vào lớp học", "hero_btn_more": "Xem tính năng",
    "feat_1_title": "Đánh giá ngữ nghĩa", "feat_1_desc": "AI hiểu ý nghĩa câu trả lời của bạn.", "feat_2_title": "Lịch ôn FSRS", "feat_2_desc": "Tối ưu thời điểm ôn tập bằng lặp lại ngắt quãng.", "feat_3_title": "Báo cáo AI", "feat_3_desc": "Phân tích tiến độ và điểm yếu.", "feat_4_title": "Giáo trình kinh điển", "feat_4_desc": "Hỗ trợ nhiều ngôn ngữ và lộ trình có cấu trúc.", "feat_5_title": "Chi phí hợp lý", "feat_5_desc": "Phí thấp để duy trì máy chủ.", "feat_6_title": "Cộng đồng toàn cầu", "feat_6_desc": "Luyện tập cùng người học khắp thế giới và AI.",
    "settings_title": "Cài đặt", "overview_title": "Tổng quan học tập", "classroom_title": "Lớp học", "classroom_subtitle": "Chọn một khóa học và bắt đầu hôm nay.", "classroom_remaining_today": "Cần ôn hôm nay", "classroom_reviewed_today": "Đã ôn hôm nay", "classroom_new_learned_today": "Mới học hôm nay", "classroom_my_courses": "Khóa học của tôi", "classroom_all_courses": "Tất cả khóa học", "classroom_mastered": "Đã nắm", "classroom_start": "Bắt đầu", "classroom_filter_learning": "Ngôn ngữ học", "classroom_filter_native": "Tiếng mẹ đẻ", "classroom_filter_all": "Tất cả", "classroom_join_course": "Tham gia", "classroom_in_learning": "Đang học", "classroom_added": "Đã thêm", "classroom_no_courses": "Không có khóa học phù hợp", "classroom_course_lessons": "{{count}} bài", "classroom_course_items": "{{count}} từ vựng", "btn_add": "Thêm",
    "course_back": "Quay lại chọn khóa", "course_foundations": "Nền tảng", "course_all_lessons": "Tất cả bài học", "course_no_lessons": "Chưa có bài học", "course_start_learning": "Bắt đầu học", "course_intro_card_title": "Giới thiệu khóa học", "course_intro_card_sub": "Ý tưởng · cách học · lộ trình", "course_hanzi_card_title": "Cơ bản Hán tự", "course_hanzi_card_sub": "Nét · bộ thủ · cấu trúc", "course_pinyin_card_title": "Cơ bản Pinyin", "course_pinyin_card_sub": "Thanh mẫu · vận mẫu · thanh điệu", "course_typing_card_title": "Gõ máy", "course_typing_card_sub": "IME · gõ pinyin · luyện tập", "teaching_back_to_course": "Quay lại khóa học",
    "practice_submit": "Nộp câu trả lời", "practice_evaluating": "Gia sư AI đang chấm...", "practice_retry": "Thử lại", "practice_skip": "Bỏ qua", "practice_next": "Tiếp theo", "practice_finish": "Hoàn thành", "practice_ai_feedback_title": "Phản hồi AI", "practice_audio_play": "Phát", "practice_audio_replay": "Phát lại", "practice_std_answer": "Đáp án mẫu", "practice_next_question": "Câu tiếp theo", "practice_finish_round": "Kết thúc lượt luyện", "teaching_new_unit": "Bài mới", "teaching_vocab_title": "Từ vựng bài này", "teaching_example": "Ví dụ", "teaching_start_quiz": "Hoàn thành học và làm bài kiểm tra"
  },
  pt: {
    "nav_auth": "Entrar/Registrar", "nav_profile": "Perfil", "nav_overview": "Visão geral", "nav_settings": "Configurações", "nav_account_title": "Conta", "nav_logout": "Sair",
    "auth_login": "Entrar", "auth_register": "Registrar", "auth_email": "E-mail", "auth_password": "Senha", "auth_confirm_password": "Confirmar senha", "auth_submit_login": "Entrar", "auth_submit_reg": "Registrar", "auth_welcome": "Bem-vindo de volta", "auth_create": "Criar conta", "auth_back_home": "Voltar ao início", "auth_login_subtitle": "Entre com seu e-mail", "auth_register_subtitle": "Comece sua jornada com IA", "auth_or_use": "Ou usar",
    "hero_badge": "✨ Seu tutor de idiomas com LLM", "hero_title_1": "Pense e fale como um nativo", "hero_title_2": "Aprendizado de idiomas com IA", "hero_desc": "Deixe a memorização mecânica para trás. Chilan usa LLM e FSRS para ajudar você a aprender melhor.", "hero_btn_classroom": "Entrar na sala", "hero_btn_more": "Ver recursos",
    "settings_title": "Configurações", "overview_title": "Visão geral de aprendizagem", "classroom_title": "Sala de aula", "classroom_subtitle": "Escolha um curso e comece hoje.", "classroom_remaining_today": "Para revisar", "classroom_reviewed_today": "Revisado hoje", "classroom_new_learned_today": "Novo hoje", "classroom_my_courses": "Meus cursos", "classroom_all_courses": "Todos os cursos", "classroom_mastered": "Dominado", "classroom_start": "Começar", "classroom_filter_learning": "Idioma de estudo", "classroom_filter_native": "Idioma nativo", "classroom_filter_all": "Todos", "classroom_join_course": "Entrar no curso", "classroom_in_learning": "Em estudo", "classroom_added": "Adicionado", "classroom_no_courses": "Nenhum curso encontrado", "classroom_course_lessons": "{{count}} aulas", "classroom_course_items": "{{count}} palavras", "btn_add": "Adicionar",
    "course_back": "Voltar aos cursos", "course_foundations": "Fundamentos", "course_all_lessons": "Todas as aulas", "course_no_lessons": "Nenhuma aula disponível", "course_start_learning": "Começar", "course_intro_card_title": "Introdução", "course_intro_card_sub": "Conceitos · método · caminho", "course_hanzi_card_title": "Bases de Hanzi", "course_hanzi_card_sub": "Traços · radicais · estrutura", "course_pinyin_card_title": "Bases de Pinyin", "course_pinyin_card_sub": "Iniciais · finais · tons", "course_typing_card_title": "Digitação", "course_typing_card_sub": "IME · pinyin · prática", "teaching_back_to_course": "Voltar ao curso",
    "practice_submit": "Enviar resposta", "practice_evaluating": "Tutor IA avaliando...", "practice_retry": "Tentar novamente", "practice_skip": "Pular", "practice_next": "Próximo", "practice_finish": "Concluir", "practice_ai_feedback_title": "Feedback da IA", "practice_audio_play": "Tocar", "practice_audio_replay": "Repetir", "practice_std_answer": "Resposta modelo", "practice_next_question": "Próxima pergunta", "practice_finish_round": "Concluir rodada", "teaching_new_unit": "Nova unidade", "teaching_vocab_title": "Vocabulário", "teaching_example": "Exemplo", "teaching_start_quiz": "Concluir e iniciar quiz"
  },
  ar: {
    "nav_auth": "تسجيل الدخول/إنشاء حساب", "nav_profile": "الملف الشخصي", "nav_overview": "نظرة عامة", "nav_settings": "الإعدادات", "nav_account_title": "الحساب", "nav_logout": "تسجيل الخروج",
    "auth_login": "تسجيل الدخول", "auth_register": "إنشاء حساب", "auth_email": "البريد الإلكتروني", "auth_password": "كلمة المرور", "auth_confirm_password": "تأكيد كلمة المرور", "auth_submit_login": "تسجيل الدخول", "auth_submit_reg": "إنشاء حساب", "auth_welcome": "مرحباً بعودتك", "auth_create": "إنشاء حساب جديد", "auth_back_home": "العودة للرئيسية", "auth_login_subtitle": "سجّل الدخول باستخدام بريدك", "auth_register_subtitle": "ابدأ رحلة تعلم اللغة بالذكاء الاصطناعي", "auth_or_use": "أو استخدم",
    "hero_badge": "✨ مدرس لغة بالذكاء الاصطناعي مدعوم بـ LLM", "hero_title_1": "فكّر وتحدث كمتحدث أصلي", "hero_title_2": "تعلم اللغات بالذكاء الاصطناعي", "hero_desc": "تجاوز الحفظ الآلي. يستخدم Chilan نماذج LLM وFSRS لمساعدتك على التعلم بكفاءة.", "hero_btn_classroom": "ادخل الصف", "hero_btn_more": "عرض الميزات",
    "settings_title": "الإعدادات", "overview_title": "نظرة عامة على التعلم", "classroom_title": "صف التعلم", "classroom_subtitle": "اختر دورة وابدأ اليوم.", "classroom_remaining_today": "للمراجعة اليوم", "classroom_reviewed_today": "تمت مراجعته اليوم", "classroom_new_learned_today": "جديد اليوم", "classroom_my_courses": "دوراتي", "classroom_all_courses": "كل الدورات", "classroom_mastered": "متقن", "classroom_start": "ابدأ", "classroom_filter_learning": "لغة التعلم", "classroom_filter_native": "اللغة الأم", "classroom_filter_all": "الكل", "classroom_join_course": "انضم للدورة", "classroom_in_learning": "قيد التعلم", "classroom_added": "تمت الإضافة", "classroom_no_courses": "لا توجد دورات مطابقة", "classroom_course_lessons": "{{count}} درس", "classroom_course_items": "{{count}} مفردة", "btn_add": "إضافة",
    "course_back": "العودة لاختيار الدورة", "course_foundations": "الأساسيات", "course_all_lessons": "كل الدروس", "course_no_lessons": "لا توجد دروس", "course_start_learning": "ابدأ التعلم", "course_intro_card_title": "مقدمة الدورة", "course_intro_card_sub": "الفكرة · طريقة التعلم · المسار", "course_hanzi_card_title": "أساسيات هانزي", "course_hanzi_card_sub": "الخطوط · الجذور · البنية", "course_pinyin_card_title": "أساسيات بينيين", "course_pinyin_card_sub": "الأوائل · النهايات · النغمات", "course_typing_card_title": "الكتابة", "course_typing_card_sub": "IME · كتابة بينيين · تدريب", "teaching_back_to_course": "العودة للدورة",
    "practice_submit": "إرسال الإجابة", "practice_evaluating": "المعلم الذكي يقيّم...", "practice_retry": "إعادة المحاولة", "practice_skip": "تخطي", "practice_next": "التالي", "practice_finish": "إنهاء", "practice_ai_feedback_title": "ملاحظات الذكاء الاصطناعي", "practice_audio_play": "تشغيل", "practice_audio_replay": "إعادة", "practice_std_answer": "الإجابة النموذجية", "practice_next_question": "السؤال التالي", "practice_finish_round": "إنهاء الجولة", "teaching_new_unit": "وحدة جديدة", "teaching_vocab_title": "مفردات الدرس", "teaching_example": "مثال", "teaching_start_quiz": "إنهاء التعلم وبدء الاختبار"
  },
  th: {
    "nav_auth": "เข้าสู่ระบบ/สมัคร", "nav_profile": "โปรไฟล์", "nav_overview": "ภาพรวม", "nav_settings": "ตั้งค่า", "nav_account_title": "บัญชี", "nav_logout": "ออกจากระบบ",
    "auth_login": "เข้าสู่ระบบ", "auth_register": "สมัคร", "auth_email": "อีเมล", "auth_password": "รหัสผ่าน", "auth_confirm_password": "ยืนยันรหัสผ่าน", "auth_submit_login": "เข้าสู่ระบบ", "auth_submit_reg": "สมัคร", "auth_welcome": "ยินดีต้อนรับกลับ", "auth_create": "สร้างบัญชี", "auth_back_home": "กลับหน้าแรก", "auth_login_subtitle": "เข้าสู่ระบบด้วยอีเมล", "auth_register_subtitle": "เริ่มเรียนภาษาด้วย AI", "auth_or_use": "หรือใช้",
    "hero_badge": "✨ ติวเตอร์ภาษา AI ที่ใช้ LLM", "hero_title_1": "คิดและพูดเหมือนเจ้าของภาษา", "hero_title_2": "เรียนภาษาด้วย AI", "hero_desc": "เลิกท่องจำแบบเดิม Chilan ใช้ LLM และ FSRS เพื่อช่วยให้คุณเรียนได้มีประสิทธิภาพขึ้น", "hero_btn_classroom": "เข้าห้องเรียน", "hero_btn_more": "ดูฟีเจอร์",
    "settings_title": "ตั้งค่า", "overview_title": "ภาพรวมการเรียน", "classroom_title": "ห้องเรียน", "classroom_subtitle": "เลือกคอร์สและเริ่มวันนี้", "classroom_remaining_today": "ต้องทบทวนวันนี้", "classroom_reviewed_today": "ทบทวนแล้ววันนี้", "classroom_new_learned_today": "เรียนใหม่วันนี้", "classroom_my_courses": "คอร์สของฉัน", "classroom_all_courses": "ทุกคอร์ส", "classroom_mastered": "เชี่ยวชาญ", "classroom_start": "เริ่ม", "classroom_filter_learning": "ภาษาที่เรียน", "classroom_filter_native": "ภาษาแม่", "classroom_filter_all": "ทั้งหมด", "classroom_join_course": "เข้าร่วมคอร์ส", "classroom_in_learning": "กำลังเรียน", "classroom_added": "เพิ่มแล้ว", "classroom_no_courses": "ไม่พบคอร์สที่ตรงเงื่อนไข", "classroom_course_lessons": "{{count}} บทเรียน", "classroom_course_items": "{{count}} คำศัพท์", "btn_add": "เพิ่ม",
    "course_back": "กลับไปเลือกคอร์ส", "course_foundations": "พื้นฐาน", "course_all_lessons": "บทเรียนทั้งหมด", "course_no_lessons": "ยังไม่มีบทเรียน", "course_start_learning": "เริ่มเรียน", "course_intro_card_title": "แนะนำคอร์ส", "course_intro_card_sub": "แนวคิด · วิธีเรียน · เส้นทาง", "course_hanzi_card_title": "พื้นฐานฮั่นจื้อ", "course_hanzi_card_sub": "เส้นขีด · หมวดนำ · โครงสร้าง", "course_pinyin_card_title": "พื้นฐานพินอิน", "course_pinyin_card_sub": "พยัญชนะต้น · สระ · วรรณยุกต์", "course_typing_card_title": "การพิมพ์", "course_typing_card_sub": "IME · พิมพ์พินอิน · ฝึก", "teaching_back_to_course": "กลับไปคอร์ส",
    "practice_submit": "ส่งคำตอบ", "practice_evaluating": "ติวเตอร์ AI กำลังตรวจ...", "practice_retry": "ลองอีกครั้ง", "practice_skip": "ข้าม", "practice_next": "ถัดไป", "practice_finish": "เสร็จสิ้น", "practice_ai_feedback_title": "ข้อเสนอแนะจาก AI", "practice_audio_play": "เล่น", "practice_audio_replay": "เล่นซ้ำ", "practice_std_answer": "คำตอบมาตรฐาน", "practice_next_question": "คำถามถัดไป", "practice_finish_round": "จบรอบฝึก", "teaching_new_unit": "หน่วยใหม่", "teaching_vocab_title": "คำศัพท์บทนี้", "teaching_example": "ตัวอย่าง", "teaching_start_quiz": "เรียนจบแล้ว เริ่มแบบทดสอบ"
  },
  ru: {
    "nav_auth": "Войти/Регистрация", "nav_profile": "Профиль", "nav_overview": "Обзор", "nav_settings": "Настройки", "nav_account_title": "Аккаунт", "nav_logout": "Выйти",
    "auth_login": "Войти", "auth_register": "Регистрация", "auth_email": "Эл. почта", "auth_password": "Пароль", "auth_confirm_password": "Подтвердите пароль", "auth_submit_login": "Войти", "auth_submit_reg": "Зарегистрироваться", "auth_welcome": "С возвращением", "auth_create": "Создать аккаунт", "auth_back_home": "На главную", "auth_login_subtitle": "Войдите по электронной почте", "auth_register_subtitle": "Начните обучение с ИИ", "auth_or_use": "Или используйте",
    "hero_badge": "✨ ИИ-репетитор языка на базе LLM", "hero_title_1": "Думайте и говорите как носитель", "hero_title_2": "Изучение языков с ИИ", "hero_desc": "Забудьте о механическом заучивании. Chilan использует LLM и FSRS для более эффективного обучения.", "hero_btn_classroom": "Войти в класс", "hero_btn_more": "Функции",
    "settings_title": "Настройки", "overview_title": "Обзор обучения", "classroom_title": "Учебный класс", "classroom_subtitle": "Выберите курс и начните сегодня.", "classroom_remaining_today": "Повторить сегодня", "classroom_reviewed_today": "Повторено сегодня", "classroom_new_learned_today": "Новое сегодня", "classroom_my_courses": "Мои курсы", "classroom_all_courses": "Все курсы", "classroom_mastered": "Освоено", "classroom_start": "Начать", "classroom_filter_learning": "Изучаемый язык", "classroom_filter_native": "Родной язык", "classroom_filter_all": "Все", "classroom_join_course": "Присоединиться", "classroom_in_learning": "В процессе", "classroom_added": "Добавлено", "classroom_no_courses": "Курсы не найдены", "classroom_course_lessons": "{{count}} уроков", "classroom_course_items": "{{count}} слов", "btn_add": "Добавить",
    "course_back": "Назад к выбору курса", "course_foundations": "Основы", "course_all_lessons": "Все уроки", "course_no_lessons": "Уроков пока нет", "course_start_learning": "Начать обучение", "course_intro_card_title": "Введение в курс", "course_intro_card_sub": "Идея · метод · путь", "course_hanzi_card_title": "Основы иероглифов", "course_hanzi_card_sub": "Черты · ключи · структура", "course_pinyin_card_title": "Основы пиньиня", "course_pinyin_card_sub": "Инициали · финали · тоны", "course_typing_card_title": "Набор текста", "course_typing_card_sub": "IME · пиньинь · практика", "teaching_back_to_course": "Назад к курсу",
    "practice_submit": "Отправить ответ", "practice_evaluating": "ИИ-преподаватель проверяет...", "practice_retry": "Повторить", "practice_skip": "Пропустить", "practice_next": "Далее", "practice_finish": "Завершить", "practice_ai_feedback_title": "Отзыв ИИ", "practice_audio_play": "Воспроизвести", "practice_audio_replay": "Повторить", "practice_std_answer": "Образцовый ответ", "practice_next_question": "Следующий вопрос", "practice_finish_round": "Завершить раунд", "teaching_new_unit": "Новый раздел", "teaching_vocab_title": "Слова урока", "teaching_example": "Пример", "teaching_start_quiz": "Завершить и начать тест"
  },
  id: {
    "nav_auth": "Masuk/Daftar", "nav_profile": "Profil", "nav_overview": "Ringkasan", "nav_settings": "Pengaturan", "nav_account_title": "Akun", "nav_logout": "Keluar",
    "auth_login": "Masuk", "auth_register": "Daftar", "auth_email": "Email", "auth_password": "Kata sandi", "auth_confirm_password": "Konfirmasi kata sandi", "auth_submit_login": "Masuk", "auth_submit_reg": "Daftar", "auth_welcome": "Selamat datang kembali", "auth_create": "Buat akun", "auth_back_home": "Kembali ke beranda", "auth_login_subtitle": "Masuk dengan email Anda", "auth_register_subtitle": "Mulai belajar bahasa dengan AI", "auth_or_use": "Atau gunakan",
    "hero_badge": "✨ Tutor bahasa AI berbasis LLM", "hero_title_1": "Berpikir dan berbicara seperti penutur asli", "hero_title_2": "Belajar bahasa dengan AI", "hero_desc": "Tinggalkan hafalan mekanis. Chilan memakai LLM dan FSRS agar belajar lebih efektif.", "hero_btn_classroom": "Masuk kelas", "hero_btn_more": "Lihat fitur",
    "settings_title": "Pengaturan", "overview_title": "Ringkasan belajar", "classroom_title": "Kelas belajar", "classroom_subtitle": "Pilih kursus dan mulai hari ini.", "classroom_remaining_today": "Perlu diulas", "classroom_reviewed_today": "Diulas hari ini", "classroom_new_learned_today": "Baru hari ini", "classroom_my_courses": "Kursus saya", "classroom_all_courses": "Semua kursus", "classroom_mastered": "Dikuasai", "classroom_start": "Mulai", "classroom_filter_learning": "Bahasa belajar", "classroom_filter_native": "Bahasa ibu", "classroom_filter_all": "Semua", "classroom_join_course": "Ikut kursus", "classroom_in_learning": "Sedang belajar", "classroom_added": "Ditambahkan", "classroom_no_courses": "Tidak ada kursus yang cocok", "classroom_course_lessons": "{{count}} pelajaran", "classroom_course_items": "{{count}} kosakata", "btn_add": "Tambah",
    "course_back": "Kembali ke pilihan kursus", "course_foundations": "Dasar", "course_all_lessons": "Semua pelajaran", "course_no_lessons": "Belum ada pelajaran", "course_start_learning": "Mulai belajar", "course_intro_card_title": "Intro kursus", "course_intro_card_sub": "Konsep · cara belajar · jalur", "course_hanzi_card_title": "Dasar Hanzi", "course_hanzi_card_sub": "Goresan · radikal · struktur", "course_pinyin_card_title": "Dasar Pinyin", "course_pinyin_card_sub": "Inisial · final · nada", "course_typing_card_title": "Mengetik", "course_typing_card_sub": "IME · pinyin · latihan", "teaching_back_to_course": "Kembali ke kursus",
    "practice_submit": "Kirim jawaban", "practice_evaluating": "Tutor AI sedang menilai...", "practice_retry": "Coba lagi", "practice_skip": "Lewati", "practice_next": "Berikutnya", "practice_finish": "Selesai", "practice_ai_feedback_title": "Umpan balik AI", "practice_audio_play": "Putar", "practice_audio_replay": "Putar ulang", "practice_std_answer": "Jawaban standar", "practice_next_question": "Pertanyaan berikutnya", "practice_finish_round": "Selesaikan ronde", "teaching_new_unit": "Unit baru", "teaching_vocab_title": "Kosakata pelajaran", "teaching_example": "Contoh", "teaching_start_quiz": "Selesai belajar, mulai kuis"
  },
  ms: {
    "nav_auth": "Log masuk/Daftar", "nav_profile": "Profil", "nav_overview": "Gambaran", "nav_settings": "Tetapan", "nav_account_title": "Akaun", "nav_logout": "Log keluar",
    "auth_login": "Log masuk", "auth_register": "Daftar", "auth_email": "E-mel", "auth_password": "Kata laluan", "auth_confirm_password": "Sahkan kata laluan", "auth_submit_login": "Log masuk", "auth_submit_reg": "Daftar", "auth_welcome": "Selamat kembali", "auth_create": "Cipta akaun", "auth_back_home": "Kembali ke laman utama", "auth_login_subtitle": "Log masuk dengan e-mel anda", "auth_register_subtitle": "Mulakan pembelajaran bahasa dengan AI", "auth_or_use": "Atau gunakan",
    "hero_badge": "✨ Tutor bahasa AI berasaskan LLM", "hero_title_1": "Berfikir dan bercakap seperti penutur asli", "hero_title_2": "Pembelajaran bahasa dengan AI", "hero_desc": "Tinggalkan hafalan mekanikal. Chilan menggunakan LLM dan FSRS untuk pembelajaran lebih berkesan.", "hero_btn_classroom": "Masuk kelas", "hero_btn_more": "Lihat ciri",
    "settings_title": "Tetapan", "overview_title": "Gambaran pembelajaran", "classroom_title": "Kelas pembelajaran", "classroom_subtitle": "Pilih kursus dan mula hari ini.", "classroom_remaining_today": "Perlu ulang kaji", "classroom_reviewed_today": "Diulang kaji hari ini", "classroom_new_learned_today": "Baharu hari ini", "classroom_my_courses": "Kursus saya", "classroom_all_courses": "Semua kursus", "classroom_mastered": "Dikuasai", "classroom_start": "Mula", "classroom_filter_learning": "Bahasa dipelajari", "classroom_filter_native": "Bahasa ibunda", "classroom_filter_all": "Semua", "classroom_join_course": "Sertai kursus", "classroom_in_learning": "Sedang belajar", "classroom_added": "Ditambah", "classroom_no_courses": "Tiada kursus sepadan", "classroom_course_lessons": "{{count}} pelajaran", "classroom_course_items": "{{count}} kosakata", "btn_add": "Tambah",
    "course_back": "Kembali ke pilihan kursus", "course_foundations": "Asas", "course_all_lessons": "Semua pelajaran", "course_no_lessons": "Tiada pelajaran", "course_start_learning": "Mula belajar", "course_intro_card_title": "Pengenalan kursus", "course_intro_card_sub": "Konsep · cara belajar · laluan", "course_hanzi_card_title": "Asas Hanzi", "course_hanzi_card_sub": "Goresan · radikal · struktur", "course_pinyin_card_title": "Asas Pinyin", "course_pinyin_card_sub": "Awalan · akhiran · nada", "course_typing_card_title": "Menaip", "course_typing_card_sub": "IME · pinyin · latihan", "teaching_back_to_course": "Kembali ke kursus",
    "practice_submit": "Hantar jawapan", "practice_evaluating": "Tutor AI sedang menilai...", "practice_retry": "Cuba lagi", "practice_skip": "Langkau", "practice_next": "Seterusnya", "practice_finish": "Selesai", "practice_ai_feedback_title": "Maklum balas AI", "practice_audio_play": "Main", "practice_audio_replay": "Main semula", "practice_std_answer": "Jawapan standard", "practice_next_question": "Soalan seterusnya", "practice_finish_round": "Tamatkan pusingan", "teaching_new_unit": "Unit baharu", "teaching_vocab_title": "Kosa kata pelajaran", "teaching_example": "Contoh", "teaching_start_quiz": "Selesai belajar, mula kuiz"
  },
  it: {
    "nav_auth": "Accedi/Registrati", "nav_profile": "Profilo", "nav_overview": "Panoramica", "nav_settings": "Impostazioni", "nav_account_title": "Account", "nav_logout": "Esci",
    "auth_login": "Accedi", "auth_register": "Registrati", "auth_email": "Email", "auth_password": "Password", "auth_confirm_password": "Conferma password", "auth_submit_login": "Accedi", "auth_submit_reg": "Registrati", "auth_welcome": "Bentornato", "auth_create": "Crea account", "auth_back_home": "Torna alla home", "auth_login_subtitle": "Accedi con la tua email", "auth_register_subtitle": "Inizia a imparare con l'IA", "auth_or_use": "Oppure usa",
    "hero_badge": "✨ Tutor linguistico IA basato su LLM", "hero_title_1": "Pensa e parla come un madrelingua", "hero_title_2": "Apprendimento linguistico con IA", "hero_desc": "Supera la memorizzazione meccanica. Chilan usa LLM e FSRS per aiutarti a imparare meglio.", "hero_btn_classroom": "Entra in aula", "hero_btn_more": "Vedi funzionalità",
    "settings_title": "Impostazioni", "overview_title": "Panoramica apprendimento", "classroom_title": "Aula", "classroom_subtitle": "Scegli un corso e inizia oggi.", "classroom_remaining_today": "Da ripassare", "classroom_reviewed_today": "Ripassato oggi", "classroom_new_learned_today": "Nuovo oggi", "classroom_my_courses": "I miei corsi", "classroom_all_courses": "Tutti i corsi", "classroom_mastered": "Padroneggiato", "classroom_start": "Inizia", "classroom_filter_learning": "Lingua di studio", "classroom_filter_native": "Lingua madre", "classroom_filter_all": "Tutti", "classroom_join_course": "Unisciti", "classroom_in_learning": "In apprendimento", "classroom_added": "Aggiunto", "classroom_no_courses": "Nessun corso trovato", "classroom_course_lessons": "{{count}} lezioni", "classroom_course_items": "{{count}} vocaboli", "btn_add": "Aggiungi",
    "course_back": "Torna ai corsi", "course_foundations": "Fondamenti", "course_all_lessons": "Tutte le lezioni", "course_no_lessons": "Nessuna lezione", "course_start_learning": "Inizia", "course_intro_card_title": "Introduzione", "course_intro_card_sub": "Concetti · metodo · percorso", "course_hanzi_card_title": "Basi Hanzi", "course_hanzi_card_sub": "Tratti · radicali · struttura", "course_pinyin_card_title": "Basi Pinyin", "course_pinyin_card_sub": "Iniziali · finali · toni", "course_typing_card_title": "Digitazione", "course_typing_card_sub": "IME · pinyin · pratica", "teaching_back_to_course": "Torna al corso",
    "practice_submit": "Invia risposta", "practice_evaluating": "Il tutor IA sta valutando...", "practice_retry": "Riprova", "practice_skip": "Salta", "practice_next": "Avanti", "practice_finish": "Fine", "practice_ai_feedback_title": "Feedback IA", "practice_audio_play": "Riproduci", "practice_audio_replay": "Ripeti", "practice_std_answer": "Risposta modello", "practice_next_question": "Domanda successiva", "practice_finish_round": "Concludi sessione", "teaching_new_unit": "Nuova unità", "teaching_vocab_title": "Vocabolario", "teaching_example": "Esempio", "teaching_start_quiz": "Finisci e inizia il quiz"
  }
};

const NEW_LOCALE_EXTRA_OVERRIDES = {
  ko: {
    "auth_submit_continue": "계속", "auth_submit_verify": "인증", "auth_verify_title": "이메일 인증", "auth_verify_subtitle": "인증 코드가 {{email}}로 전송되었습니다", "auth_success_title": "인증 완료!", "auth_success_subtitle": "계정이 활성화되었습니다. 로그인 화면으로 이동합니다...", "auth_change_email": "이메일 변경", "auth_login_success_title": "로그인 성공!", "auth_login_success_subtitle": "홈으로 돌아가는 중...", "auth_forgot_password": "비밀번호를 잊으셨나요?", "auth_forgot_title": "비밀번호 재설정", "auth_forgot_subtitle": "인증 코드를 받을 이메일을 입력하세요", "auth_reset_title": "새 비밀번호 설정", "auth_reset_subtitle": "인증 코드를 입력하고 새 비밀번호를 설정하세요", "auth_submit_send_code": "코드 보내기", "auth_submit_reset": "비밀번호 재설정", "auth_back_to_login": "로그인으로 돌아가기", "auth_register_tip": "아래 보안 기준에 맞춰 비밀번호를 설정하세요", "auth_pw_req_length": "8-32자", "auth_pw_req_letter": "문자 포함", "auth_pw_req_number": "숫자 포함", "auth_pw_req_special": "특수 문자 포함", "auth_pw_req_no_space": "공백 없음", "auth_pw_match": "비밀번호 일치",
    "practice_title_lesson": "수업 강화 연습", "practice_title_review": "스마트 복습", "practice_prompt_cn_to_en": "영어로 번역", "practice_prompt_en_to_cn": "중국어로 번역", "practice_prompt_cn_listen_write": "듣고 한자로 쓰기", "practice_input_placeholder": "여기에 답을 입력하세요...", "practice_feedback_excellent": "훌륭해요!", "practice_feedback_good": "좋아요, 더 나아질 수 있어요!", "practice_feedback_retry": "조금 더 연습해요!", "practice_eval_failed": "채점 서비스 연결 실패. 다시 시도하세요.", "practice_ai_analyzing": "AI 튜터가 답변을 분석 중...", "practice_ai_thinking": "AI 튜터가 피드백을 생성 중", "word_pinyin_btn": "병음", "word_translation_btn": "번역", "practice_badge_cn_to_en": "번역 · 중→영", "practice_badge_en_to_cn": "번역 · 영→중", "practice_badge_speak": "말하기 · 중국어", "practice_badge_dictation": "받아쓰기", "practice_audio_played_times": "{{count}}회 재생 · 반복 가능", "practice_dictation_instruction": "들은 문장을 한자로 쓰세요", "practice_replay_hint": "↑ 키로 다시 재생", "practice_forfeit": "답 보기", "practice_retry_show_answer": "답을 다시 보기", "practice_asr_recognized": "인식된 텍스트", "practice_retry_text": "다시 답하기", "practice_retry_speech": "다시 녹음", "practice_skip_question": "문제 건너뛰기",
    "knowledge_title": "지식 포인트", "knowledge_current_sense": "현재 의미", "knowledge_other_senses": "다른 의미", "knowledge_show": "보기", "knowledge_hide": "접기", "study_error_load": "코스 데이터를 불러올 수 없습니다. 백엔드 동기화를 확인하세요.", "study_retry": "다시 시도", "teaching_video_label": "시각 컨텍스트 엔진", "teaching_diary_original": "일기 원문", "teaching_reading": "본문 읽기", "teaching_content": "수업 내용", "teaching_dialogue": "대화", "teaching_pinyin_on": "병음 켜짐", "teaching_pinyin_off": "병음 꺼짐", "teaching_translation_on": "번역 켜짐", "teaching_translation_off": "번역 꺼짐", "teaching_generating_quiz": "퀴즈 생성 중..."
  },
  es: {
    "auth_submit_continue": "Continuar", "auth_submit_verify": "Verificar", "auth_verify_title": "Verifica tu correo", "auth_verify_subtitle": "El código fue enviado a {{email}}", "auth_success_title": "¡Verificación correcta!", "auth_success_subtitle": "Tu cuenta está activa. Redirigiendo...", "auth_change_email": "Cambiar correo", "auth_login_success_title": "¡Inicio de sesión correcto!", "auth_login_success_subtitle": "Volviendo al inicio...", "auth_forgot_password": "¿Olvidaste la contraseña?", "auth_forgot_title": "Restablecer contraseña", "auth_forgot_subtitle": "Introduce tu correo para recibir un código", "auth_reset_title": "Nueva contraseña", "auth_reset_subtitle": "Introduce el código y define tu nueva contraseña", "auth_submit_send_code": "Enviar código", "auth_submit_reset": "Restablecer", "auth_back_to_login": "Volver al inicio de sesión", "auth_register_tip": "Configura una contraseña segura", "auth_pw_req_length": "8-32 caracteres", "auth_pw_req_letter": "Incluye letras", "auth_pw_req_number": "Incluye números", "auth_pw_req_special": "Incluye un carácter especial", "auth_pw_req_no_space": "Sin espacios", "auth_pw_match": "Las contraseñas coinciden",
    "practice_title_lesson": "Práctica intensiva", "practice_title_review": "Repaso inteligente", "practice_prompt_cn_to_en": "Traducir al inglés", "practice_prompt_en_to_cn": "Traducir al chino", "practice_prompt_cn_listen_write": "Escucha y escribe en chino", "practice_input_placeholder": "Escribe tu respuesta aquí...", "practice_feedback_excellent": "¡Excelente!", "practice_feedback_good": "Bien, pero aún puede mejorar.", "practice_feedback_retry": "¡Sigue practicando!", "practice_eval_failed": "Error al conectar con la evaluación. Inténtalo de nuevo.", "practice_ai_analyzing": "El tutor IA analiza tu respuesta...", "practice_ai_thinking": "El tutor IA genera comentarios", "word_pinyin_btn": "Pinyin", "word_translation_btn": "Trad.", "practice_badge_cn_to_en": "Traducción · ZH→EN", "practice_badge_en_to_cn": "Traducción · EN→ZH", "practice_badge_speak": "Hablar · chino", "practice_badge_dictation": "Dictado", "practice_audio_played_times": "Reproducido {{count}} veces · puedes repetirlo", "practice_dictation_instruction": "Escribe en caracteres chinos lo que escuches", "practice_replay_hint": "Pulsa ↑ para repetir", "practice_forfeit": "Ver respuesta", "practice_retry_show_answer": "Volver a mostrar la respuesta", "practice_asr_recognized": "Texto reconocido", "practice_retry_text": "Responder de nuevo", "practice_retry_speech": "Grabar de nuevo", "practice_skip_question": "Saltar pregunta",
    "knowledge_title": "Detalle del punto", "knowledge_current_sense": "Sentido actual", "knowledge_other_senses": "Otros sentidos", "knowledge_show": "Mostrar", "knowledge_hide": "Ocultar", "study_error_load": "No se pudieron cargar los datos del curso. Comprueba la sincronización del backend.", "study_retry": "Reintentar", "teaching_video_label": "Motor de contexto visual", "teaching_diary_original": "Texto original", "teaching_reading": "Lectura", "teaching_content": "Contenido", "teaching_dialogue": "Diálogo", "teaching_pinyin_on": "Pinyin activado", "teaching_pinyin_off": "Pinyin desactivado", "teaching_translation_on": "Traducción activada", "teaching_translation_off": "Traducción desactivada", "teaching_generating_quiz": "Generando prueba..."
  },
  vi: {
    "auth_submit_continue": "Tiếp tục", "auth_submit_verify": "Xác minh", "auth_verify_title": "Xác minh email", "auth_verify_subtitle": "Mã đã được gửi đến {{email}}", "auth_success_title": "Xác minh thành công!", "auth_success_subtitle": "Tài khoản đã kích hoạt. Đang chuyển hướng...", "auth_change_email": "Đổi email", "auth_login_success_title": "Đăng nhập thành công!", "auth_login_success_subtitle": "Đang quay về trang chủ...", "auth_forgot_password": "Quên mật khẩu?", "auth_forgot_title": "Đặt lại mật khẩu", "auth_forgot_subtitle": "Nhập email để nhận mã xác minh", "auth_reset_title": "Đặt mật khẩu mới", "auth_reset_subtitle": "Nhập mã và đặt mật khẩu mới", "auth_submit_send_code": "Gửi mã", "auth_submit_reset": "Đặt lại", "auth_back_to_login": "Quay lại đăng nhập", "auth_register_tip": "Thiết lập mật khẩu an toàn", "auth_pw_req_length": "8-32 ký tự", "auth_pw_req_letter": "Có chữ cái", "auth_pw_req_number": "Có số", "auth_pw_req_special": "Có ký tự đặc biệt", "auth_pw_req_no_space": "Không có khoảng trắng", "auth_pw_match": "Mật khẩu khớp",
    "practice_title_lesson": "Luyện tập tăng cường", "practice_title_review": "Ôn tập thông minh", "practice_prompt_cn_to_en": "Dịch sang tiếng Anh", "practice_prompt_en_to_cn": "Dịch sang tiếng Trung", "practice_prompt_cn_listen_write": "Nghe và viết chữ Hán", "practice_input_placeholder": "Nhập câu trả lời ở đây...", "practice_feedback_excellent": "Xuất sắc!", "practice_feedback_good": "Tốt, nhưng vẫn có thể cải thiện.", "practice_feedback_retry": "Cần luyện thêm!", "practice_eval_failed": "Không kết nối được dịch vụ chấm. Vui lòng thử lại.", "practice_ai_analyzing": "Gia sư AI đang phân tích câu trả lời...", "practice_ai_thinking": "Gia sư AI đang tạo phản hồi", "word_pinyin_btn": "Pinyin", "word_translation_btn": "Dịch", "practice_badge_cn_to_en": "Dịch · Trung→Anh", "practice_badge_en_to_cn": "Dịch · Anh→Trung", "practice_badge_speak": "Nói · tiếng Trung", "practice_badge_dictation": "Chính tả", "practice_audio_played_times": "Đã phát {{count}} lần · có thể phát lại", "practice_dictation_instruction": "Viết bằng chữ Hán câu bạn nghe được", "practice_replay_hint": "Nhấn ↑ để phát lại", "practice_forfeit": "Xem đáp án", "practice_retry_show_answer": "Xem lại đáp án", "practice_asr_recognized": "Văn bản nhận dạng", "practice_retry_text": "Làm lại", "practice_retry_speech": "Ghi âm lại", "practice_skip_question": "Bỏ qua câu này",
    "knowledge_title": "Chi tiết kiến thức", "knowledge_current_sense": "Nghĩa hiện tại", "knowledge_other_senses": "Nghĩa khác", "knowledge_show": "Hiện", "knowledge_hide": "Ẩn", "study_error_load": "Không tải được dữ liệu khóa học. Hãy kiểm tra đồng bộ backend.", "study_retry": "Thử lại", "teaching_video_label": "Công cụ ngữ cảnh trực quan", "teaching_diary_original": "Nguyên văn", "teaching_reading": "Đọc bài", "teaching_content": "Nội dung bài", "teaching_dialogue": "Hội thoại", "teaching_pinyin_on": "Bật pinyin", "teaching_pinyin_off": "Tắt pinyin", "teaching_translation_on": "Bật dịch", "teaching_translation_off": "Tắt dịch", "teaching_generating_quiz": "Đang tạo bài kiểm tra..."
  },
  pt: {
    "auth_submit_continue": "Continuar", "auth_submit_verify": "Verificar", "auth_verify_title": "Verifique seu e-mail", "auth_verify_subtitle": "O código foi enviado para {{email}}", "auth_success_title": "Verificação concluída!", "auth_success_subtitle": "Sua conta foi ativada. Redirecionando...", "auth_change_email": "Alterar e-mail", "auth_login_success_title": "Login concluído!", "auth_login_success_subtitle": "Voltando ao início...", "auth_forgot_password": "Esqueceu a senha?", "auth_forgot_title": "Redefinir senha", "auth_forgot_subtitle": "Digite seu e-mail para receber um código", "auth_reset_title": "Definir nova senha", "auth_reset_subtitle": "Digite o código e defina sua nova senha", "auth_submit_send_code": "Enviar código", "auth_submit_reset": "Redefinir", "auth_back_to_login": "Voltar ao login", "auth_register_tip": "Defina uma senha segura", "auth_pw_req_length": "8-32 caracteres", "auth_pw_req_letter": "Inclui letras", "auth_pw_req_number": "Inclui números", "auth_pw_req_special": "Inclui caractere especial", "auth_pw_req_no_space": "Sem espaços", "auth_pw_match": "Senhas coincidem",
    "practice_title_lesson": "Prática intensiva", "practice_title_review": "Revisão inteligente", "practice_prompt_cn_to_en": "Traduzir para inglês", "practice_prompt_en_to_cn": "Traduzir para chinês", "practice_prompt_cn_listen_write": "Ouça e escreva em chinês", "practice_input_placeholder": "Digite sua resposta aqui...", "practice_feedback_excellent": "Excelente!", "practice_feedback_good": "Bom, mas ainda pode melhorar.", "practice_feedback_retry": "Continue praticando!", "practice_eval_failed": "Falha ao conectar ao serviço de avaliação. Tente novamente.", "practice_ai_analyzing": "Tutor IA analisando sua resposta...", "practice_ai_thinking": "Tutor IA gerando feedback", "word_pinyin_btn": "Pinyin", "word_translation_btn": "Trad.", "practice_badge_cn_to_en": "Tradução · ZH→EN", "practice_badge_en_to_cn": "Tradução · EN→ZH", "practice_badge_speak": "Fala · chinês", "practice_badge_dictation": "Ditado", "practice_audio_played_times": "Reproduzido {{count}} vezes · pode repetir", "practice_dictation_instruction": "Escreva em caracteres chineses o que ouviu", "practice_replay_hint": "Pressione ↑ para repetir", "practice_forfeit": "Ver resposta", "practice_retry_show_answer": "Mostrar resposta novamente", "practice_asr_recognized": "Texto reconhecido", "practice_retry_text": "Responder de novo", "practice_retry_speech": "Gravar de novo", "practice_skip_question": "Pular pergunta",
    "knowledge_title": "Detalhes do ponto", "knowledge_current_sense": "Sentido atual", "knowledge_other_senses": "Outros sentidos", "knowledge_show": "Mostrar", "knowledge_hide": "Ocultar", "study_error_load": "Não foi possível carregar os dados do curso. Verifique a sincronização do backend.", "study_retry": "Tentar novamente", "teaching_video_label": "Motor de contexto visual", "teaching_diary_original": "Texto original", "teaching_reading": "Leitura", "teaching_content": "Conteúdo", "teaching_dialogue": "Diálogo", "teaching_pinyin_on": "Pinyin ligado", "teaching_pinyin_off": "Pinyin desligado", "teaching_translation_on": "Tradução ligada", "teaching_translation_off": "Tradução desligada", "teaching_generating_quiz": "Gerando quiz..."
  },
  ar: {
    "auth_submit_continue": "متابعة", "auth_submit_verify": "تحقق", "auth_verify_title": "تحقق من بريدك", "auth_verify_subtitle": "تم إرسال الرمز إلى {{email}}", "auth_success_title": "تم التحقق!", "auth_success_subtitle": "تم تفعيل الحساب. جارٍ التحويل...", "auth_change_email": "تغيير البريد", "auth_login_success_title": "تم تسجيل الدخول!", "auth_login_success_subtitle": "العودة للرئيسية...", "auth_forgot_password": "هل نسيت كلمة المرور؟", "auth_forgot_title": "إعادة تعيين كلمة المرور", "auth_forgot_subtitle": "أدخل بريدك للحصول على رمز", "auth_reset_title": "تعيين كلمة مرور جديدة", "auth_reset_subtitle": "أدخل الرمز وكلمة المرور الجديدة", "auth_submit_send_code": "إرسال الرمز", "auth_submit_reset": "إعادة التعيين", "auth_back_to_login": "العودة لتسجيل الدخول", "auth_register_tip": "عيّن كلمة مرور آمنة", "auth_pw_req_length": "8-32 حرفاً", "auth_pw_req_letter": "تحتوي على حروف", "auth_pw_req_number": "تحتوي على أرقام", "auth_pw_req_special": "تحتوي على رمز خاص", "auth_pw_req_no_space": "بدون مسافات", "auth_pw_match": "كلمتا المرور متطابقتان",
    "practice_title_lesson": "تدريب مكثف", "practice_title_review": "مراجعة ذكية", "practice_prompt_cn_to_en": "ترجم إلى الإنجليزية", "practice_prompt_en_to_cn": "ترجم إلى الصينية", "practice_prompt_cn_listen_write": "استمع واكتب بالصينية", "practice_input_placeholder": "اكتب إجابتك هنا...", "practice_feedback_excellent": "ممتاز!", "practice_feedback_good": "جيد، ويمكن تحسينه.", "practice_feedback_retry": "تابع التدريب!", "practice_eval_failed": "فشل الاتصال بخدمة التقييم. حاول مرة أخرى.", "practice_ai_analyzing": "المعلم الذكي يحلل إجابتك...", "practice_ai_thinking": "المعلم الذكي ينشئ الملاحظات", "word_pinyin_btn": "بينيين", "word_translation_btn": "ترجمة", "practice_badge_cn_to_en": "ترجمة · صيني→إنجليزي", "practice_badge_en_to_cn": "ترجمة · إنجليزي→صيني", "practice_badge_speak": "تحدث · الصينية", "practice_badge_dictation": "إملاء", "practice_audio_played_times": "تم التشغيل {{count}} مرة · يمكن الإعادة", "practice_dictation_instruction": "اكتب الجملة التي سمعتها بالأحرف الصينية", "practice_replay_hint": "اضغط ↑ للإعادة", "practice_forfeit": "عرض الإجابة", "practice_retry_show_answer": "عرض الإجابة مرة أخرى", "practice_asr_recognized": "النص المتعرف عليه", "practice_retry_text": "أجب مرة أخرى", "practice_retry_speech": "سجل مرة أخرى", "practice_skip_question": "تخطي السؤال",
    "knowledge_title": "تفاصيل المعرفة", "knowledge_current_sense": "المعنى الحالي", "knowledge_other_senses": "معانٍ أخرى", "knowledge_show": "إظهار", "knowledge_hide": "إخفاء", "study_error_load": "تعذر تحميل بيانات الدورة. تحقق من مزامنة الخلفية.", "study_retry": "حاول مرة أخرى", "teaching_video_label": "محرك السياق البصري", "teaching_diary_original": "النص الأصلي", "teaching_reading": "القراءة", "teaching_content": "محتوى الدرس", "teaching_dialogue": "الحوار", "teaching_pinyin_on": "بينيين مفعّل", "teaching_pinyin_off": "بينيين متوقف", "teaching_translation_on": "الترجمة مفعلة", "teaching_translation_off": "الترجمة متوقفة", "teaching_generating_quiz": "جارٍ إنشاء الاختبار..."
  },
  th: {
    "auth_submit_continue": "ต่อไป", "auth_submit_verify": "ยืนยัน", "auth_verify_title": "ยืนยันอีเมล", "auth_verify_subtitle": "ส่งรหัสไปที่ {{email}} แล้ว", "auth_success_title": "ยืนยันสำเร็จ!", "auth_success_subtitle": "เปิดใช้งานบัญชีแล้ว กำลังเปลี่ยนหน้า...", "auth_change_email": "เปลี่ยนอีเมล", "auth_login_success_title": "เข้าสู่ระบบสำเร็จ!", "auth_login_success_subtitle": "กำลังกลับหน้าแรก...", "auth_forgot_password": "ลืมรหัสผ่าน?", "auth_forgot_title": "รีเซ็ตรหัสผ่าน", "auth_forgot_subtitle": "กรอกอีเมลเพื่อรับรหัส", "auth_reset_title": "ตั้งรหัสผ่านใหม่", "auth_reset_subtitle": "กรอกรหัสและตั้งรหัสผ่านใหม่", "auth_submit_send_code": "ส่งรหัส", "auth_submit_reset": "รีเซ็ต", "auth_back_to_login": "กลับไปเข้าสู่ระบบ", "auth_register_tip": "ตั้งรหัสผ่านให้ปลอดภัย", "auth_pw_req_length": "8-32 ตัวอักษร", "auth_pw_req_letter": "มีตัวอักษร", "auth_pw_req_number": "มีตัวเลข", "auth_pw_req_special": "มีอักขระพิเศษ", "auth_pw_req_no_space": "ไม่มีช่องว่าง", "auth_pw_match": "รหัสผ่านตรงกัน",
    "practice_title_lesson": "ฝึกเข้ม", "practice_title_review": "ทบทวนอัจฉริยะ", "practice_prompt_cn_to_en": "แปลเป็นอังกฤษ", "practice_prompt_en_to_cn": "แปลเป็นจีน", "practice_prompt_cn_listen_write": "ฟังแล้วเขียนจีน", "practice_input_placeholder": "พิมพ์คำตอบที่นี่...", "practice_feedback_excellent": "ยอดเยี่ยม!", "practice_feedback_good": "ดีแล้ว แต่ยังพัฒนาได้", "practice_feedback_retry": "ฝึกต่ออีกนิด!", "practice_eval_failed": "เชื่อมต่อบริการตรวจไม่ได้ ลองอีกครั้ง", "practice_ai_analyzing": "ติวเตอร์ AI กำลังวิเคราะห์คำตอบ...", "practice_ai_thinking": "ติวเตอร์ AI กำลังสร้างข้อเสนอแนะ", "word_pinyin_btn": "พินอิน", "word_translation_btn": "แปล", "practice_badge_cn_to_en": "แปล · จีน→อังกฤษ", "practice_badge_en_to_cn": "แปล · อังกฤษ→จีน", "practice_badge_speak": "พูด · จีน", "practice_badge_dictation": "เขียนตามคำบอก", "practice_audio_played_times": "เล่นแล้ว {{count}} ครั้ง · เล่นซ้ำได้", "practice_dictation_instruction": "เขียนประโยคที่ได้ยินเป็นอักษรจีน", "practice_replay_hint": "กด ↑ เพื่อเล่นซ้ำ", "practice_forfeit": "ดูคำตอบ", "practice_retry_show_answer": "ดูคำตอบอีกครั้ง", "practice_asr_recognized": "ข้อความที่จำได้", "practice_retry_text": "ตอบใหม่", "practice_retry_speech": "อัดเสียงใหม่", "practice_skip_question": "ข้ามข้อนี้",
    "knowledge_title": "รายละเอียดความรู้", "knowledge_current_sense": "ความหมายปัจจุบัน", "knowledge_other_senses": "ความหมายอื่น", "knowledge_show": "แสดง", "knowledge_hide": "ซ่อน", "study_error_load": "โหลดข้อมูลคอร์สไม่ได้ โปรดตรวจสอบการซิงก์ backend", "study_retry": "ลองอีกครั้ง", "teaching_video_label": "เครื่องมือบริบทภาพ", "teaching_diary_original": "ต้นฉบับ", "teaching_reading": "อ่านบทเรียน", "teaching_content": "เนื้อหา", "teaching_dialogue": "บทสนทนา", "teaching_pinyin_on": "เปิดพินอิน", "teaching_pinyin_off": "ปิดพินอิน", "teaching_translation_on": "เปิดคำแปล", "teaching_translation_off": "ปิดคำแปล", "teaching_generating_quiz": "กำลังสร้างแบบทดสอบ..."
  },
  ru: {
    "auth_submit_continue": "Продолжить", "auth_submit_verify": "Подтвердить", "auth_verify_title": "Подтвердите почту", "auth_verify_subtitle": "Код отправлен на {{email}}", "auth_success_title": "Подтверждено!", "auth_success_subtitle": "Аккаунт активирован. Перенаправление...", "auth_change_email": "Изменить почту", "auth_login_success_title": "Вход выполнен!", "auth_login_success_subtitle": "Возврат на главную...", "auth_forgot_password": "Забыли пароль?", "auth_forgot_title": "Сброс пароля", "auth_forgot_subtitle": "Введите почту, чтобы получить код", "auth_reset_title": "Новый пароль", "auth_reset_subtitle": "Введите код и новый пароль", "auth_submit_send_code": "Отправить код", "auth_submit_reset": "Сбросить", "auth_back_to_login": "Назад ко входу", "auth_register_tip": "Задайте надежный пароль", "auth_pw_req_length": "8-32 символа", "auth_pw_req_letter": "Есть буквы", "auth_pw_req_number": "Есть цифры", "auth_pw_req_special": "Есть спецсимвол", "auth_pw_req_no_space": "Без пробелов", "auth_pw_match": "Пароли совпадают",
    "practice_title_lesson": "Интенсивная практика", "practice_title_review": "Умное повторение", "practice_prompt_cn_to_en": "Перевести на английский", "practice_prompt_en_to_cn": "Перевести на китайский", "practice_prompt_cn_listen_write": "Слушайте и пишите по-китайски", "practice_input_placeholder": "Введите ответ здесь...", "practice_feedback_excellent": "Отлично!", "practice_feedback_good": "Хорошо, но можно лучше.", "practice_feedback_retry": "Нужно еще потренироваться!", "practice_eval_failed": "Не удалось подключиться к оценке. Повторите попытку.", "practice_ai_analyzing": "ИИ-преподаватель анализирует ответ...", "practice_ai_thinking": "ИИ-преподаватель готовит отзыв", "word_pinyin_btn": "Пиньинь", "word_translation_btn": "Пер.", "practice_badge_cn_to_en": "Перевод · ZH→EN", "practice_badge_en_to_cn": "Перевод · EN→ZH", "practice_badge_speak": "Речь · китайский", "practice_badge_dictation": "Диктант", "practice_audio_played_times": "Воспроизведено {{count}} раз · можно повторять", "practice_dictation_instruction": "Запишите услышанное китайскими иероглифами", "practice_replay_hint": "Нажмите ↑ для повтора", "practice_forfeit": "Показать ответ", "practice_retry_show_answer": "Показать ответ снова", "practice_asr_recognized": "Распознанный текст", "practice_retry_text": "Ответить снова", "practice_retry_speech": "Записать снова", "practice_skip_question": "Пропустить вопрос",
    "knowledge_title": "Детали знания", "knowledge_current_sense": "Текущее значение", "knowledge_other_senses": "Другие значения", "knowledge_show": "Показать", "knowledge_hide": "Скрыть", "study_error_load": "Не удалось загрузить данные курса. Проверьте синхронизацию backend.", "study_retry": "Повторить", "teaching_video_label": "Визуальный контекст", "teaching_diary_original": "Исходный текст", "teaching_reading": "Чтение", "teaching_content": "Содержание", "teaching_dialogue": "Диалог", "teaching_pinyin_on": "Пиньинь вкл.", "teaching_pinyin_off": "Пиньинь выкл.", "teaching_translation_on": "Перевод вкл.", "teaching_translation_off": "Перевод выкл.", "teaching_generating_quiz": "Создание теста..."
  },
  id: {
    "auth_submit_continue": "Lanjut", "auth_submit_verify": "Verifikasi", "auth_verify_title": "Verifikasi email", "auth_verify_subtitle": "Kode dikirim ke {{email}}", "auth_success_title": "Verifikasi berhasil!", "auth_success_subtitle": "Akun aktif. Mengalihkan...", "auth_change_email": "Ubah email", "auth_login_success_title": "Login berhasil!", "auth_login_success_subtitle": "Kembali ke beranda...", "auth_forgot_password": "Lupa kata sandi?", "auth_forgot_title": "Reset kata sandi", "auth_forgot_subtitle": "Masukkan email untuk menerima kode", "auth_reset_title": "Atur kata sandi baru", "auth_reset_subtitle": "Masukkan kode dan kata sandi baru", "auth_submit_send_code": "Kirim kode", "auth_submit_reset": "Reset", "auth_back_to_login": "Kembali ke login", "auth_register_tip": "Buat kata sandi yang aman", "auth_pw_req_length": "8-32 karakter", "auth_pw_req_letter": "Berisi huruf", "auth_pw_req_number": "Berisi angka", "auth_pw_req_special": "Berisi karakter khusus", "auth_pw_req_no_space": "Tanpa spasi", "auth_pw_match": "Kata sandi cocok",
    "practice_title_lesson": "Latihan intensif", "practice_title_review": "Ulasan cerdas", "practice_prompt_cn_to_en": "Terjemahkan ke Inggris", "practice_prompt_en_to_cn": "Terjemahkan ke Tionghoa", "practice_prompt_cn_listen_write": "Dengar lalu tulis aksara Tionghoa", "practice_input_placeholder": "Masukkan jawaban di sini...", "practice_feedback_excellent": "Luar biasa!", "practice_feedback_good": "Bagus, masih bisa ditingkatkan.", "practice_feedback_retry": "Terus berlatih!", "practice_eval_failed": "Gagal terhubung ke layanan penilaian. Coba lagi.", "practice_ai_analyzing": "Tutor AI menganalisis jawaban...", "practice_ai_thinking": "Tutor AI membuat umpan balik", "word_pinyin_btn": "Pinyin", "word_translation_btn": "Terj.", "practice_badge_cn_to_en": "Terjemahan · ZH→EN", "practice_badge_en_to_cn": "Terjemahan · EN→ZH", "practice_badge_speak": "Bicara · Tionghoa", "practice_badge_dictation": "Dikte", "practice_audio_played_times": "Diputar {{count}} kali · bisa diulang", "practice_dictation_instruction": "Tulis kalimat yang Anda dengar dengan aksara Tionghoa", "practice_replay_hint": "Tekan ↑ untuk mengulang", "practice_forfeit": "Lihat jawaban", "practice_retry_show_answer": "Tampilkan jawaban lagi", "practice_asr_recognized": "Teks dikenali", "practice_retry_text": "Jawab ulang", "practice_retry_speech": "Rekam ulang", "practice_skip_question": "Lewati pertanyaan",
    "knowledge_title": "Detail pengetahuan", "knowledge_current_sense": "Makna saat ini", "knowledge_other_senses": "Makna lain", "knowledge_show": "Tampilkan", "knowledge_hide": "Sembunyikan", "study_error_load": "Gagal memuat data kursus. Periksa sinkronisasi backend.", "study_retry": "Coba lagi", "teaching_video_label": "Mesin konteks visual", "teaching_diary_original": "Teks asli", "teaching_reading": "Bacaan", "teaching_content": "Konten", "teaching_dialogue": "Dialog", "teaching_pinyin_on": "Pinyin aktif", "teaching_pinyin_off": "Pinyin nonaktif", "teaching_translation_on": "Terjemahan aktif", "teaching_translation_off": "Terjemahan nonaktif", "teaching_generating_quiz": "Membuat kuis..."
  },
  ms: {
    "auth_submit_continue": "Teruskan", "auth_submit_verify": "Sahkan", "auth_verify_title": "Sahkan e-mel", "auth_verify_subtitle": "Kod dihantar ke {{email}}", "auth_success_title": "Pengesahan berjaya!", "auth_success_subtitle": "Akaun diaktifkan. Mengalihkan...", "auth_change_email": "Tukar e-mel", "auth_login_success_title": "Log masuk berjaya!", "auth_login_success_subtitle": "Kembali ke laman utama...", "auth_forgot_password": "Lupa kata laluan?", "auth_forgot_title": "Tetapkan semula kata laluan", "auth_forgot_subtitle": "Masukkan e-mel untuk menerima kod", "auth_reset_title": "Tetapkan kata laluan baharu", "auth_reset_subtitle": "Masukkan kod dan kata laluan baharu", "auth_submit_send_code": "Hantar kod", "auth_submit_reset": "Tetapkan semula", "auth_back_to_login": "Kembali ke log masuk", "auth_register_tip": "Tetapkan kata laluan yang selamat", "auth_pw_req_length": "8-32 aksara", "auth_pw_req_letter": "Mengandungi huruf", "auth_pw_req_number": "Mengandungi nombor", "auth_pw_req_special": "Mengandungi aksara khas", "auth_pw_req_no_space": "Tiada ruang", "auth_pw_match": "Kata laluan sepadan",
    "practice_title_lesson": "Latihan intensif", "practice_title_review": "Ulang kaji pintar", "practice_prompt_cn_to_en": "Terjemah ke bahasa Inggeris", "practice_prompt_en_to_cn": "Terjemah ke bahasa Cina", "practice_prompt_cn_listen_write": "Dengar dan tulis aksara Cina", "practice_input_placeholder": "Masukkan jawapan di sini...", "practice_feedback_excellent": "Cemerlang!", "practice_feedback_good": "Bagus, masih boleh diperbaiki.", "practice_feedback_retry": "Teruskan berlatih!", "practice_eval_failed": "Gagal menyambung ke perkhidmatan penilaian. Cuba lagi.", "practice_ai_analyzing": "Tutor AI sedang menganalisis jawapan...", "practice_ai_thinking": "Tutor AI sedang menjana maklum balas", "word_pinyin_btn": "Pinyin", "word_translation_btn": "Terj.", "practice_badge_cn_to_en": "Terjemahan · ZH→EN", "practice_badge_en_to_cn": "Terjemahan · EN→ZH", "practice_badge_speak": "Pertuturan · Cina", "practice_badge_dictation": "Dikte", "practice_audio_played_times": "Dimainkan {{count}} kali · boleh diulang", "practice_dictation_instruction": "Tulis ayat yang didengar dalam aksara Cina", "practice_replay_hint": "Tekan ↑ untuk ulang", "practice_forfeit": "Lihat jawapan", "practice_retry_show_answer": "Lihat jawapan sekali lagi", "practice_asr_recognized": "Teks dikenali", "practice_retry_text": "Jawab semula", "practice_retry_speech": "Rakam semula", "practice_skip_question": "Langkau soalan",
    "knowledge_title": "Butiran pengetahuan", "knowledge_current_sense": "Maksud semasa", "knowledge_other_senses": "Maksud lain", "knowledge_show": "Papar", "knowledge_hide": "Sembunyi", "study_error_load": "Gagal memuatkan data kursus. Semak penyelarasan backend.", "study_retry": "Cuba lagi", "teaching_video_label": "Enjin konteks visual", "teaching_diary_original": "Teks asal", "teaching_reading": "Bacaan", "teaching_content": "Kandungan", "teaching_dialogue": "Dialog", "teaching_pinyin_on": "Pinyin hidup", "teaching_pinyin_off": "Pinyin mati", "teaching_translation_on": "Terjemahan hidup", "teaching_translation_off": "Terjemahan mati", "teaching_generating_quiz": "Menjana kuiz..."
  },
  it: {
    "auth_submit_continue": "Continua", "auth_submit_verify": "Verifica", "auth_verify_title": "Verifica la tua email", "auth_verify_subtitle": "Il codice è stato inviato a {{email}}", "auth_success_title": "Verifica riuscita!", "auth_success_subtitle": "Account attivato. Reindirizzamento...", "auth_change_email": "Cambia email", "auth_login_success_title": "Accesso riuscito!", "auth_login_success_subtitle": "Ritorno alla home...", "auth_forgot_password": "Password dimenticata?", "auth_forgot_title": "Reimposta password", "auth_forgot_subtitle": "Inserisci la tua email per ricevere un codice", "auth_reset_title": "Imposta nuova password", "auth_reset_subtitle": "Inserisci il codice e la nuova password", "auth_submit_send_code": "Invia codice", "auth_submit_reset": "Reimposta", "auth_back_to_login": "Torna all'accesso", "auth_register_tip": "Imposta una password sicura", "auth_pw_req_length": "8-32 caratteri", "auth_pw_req_letter": "Include lettere", "auth_pw_req_number": "Include numeri", "auth_pw_req_special": "Include carattere speciale", "auth_pw_req_no_space": "Nessuno spazio", "auth_pw_match": "Le password coincidono",
    "practice_title_lesson": "Pratica intensiva", "practice_title_review": "Ripasso intelligente", "practice_prompt_cn_to_en": "Traduci in inglese", "practice_prompt_en_to_cn": "Traduci in cinese", "practice_prompt_cn_listen_write": "Ascolta e scrivi in cinese", "practice_input_placeholder": "Inserisci la risposta qui...", "practice_feedback_excellent": "Eccellente!", "practice_feedback_good": "Bene, ma puoi migliorare.", "practice_feedback_retry": "Continua a esercitarti!", "practice_eval_failed": "Connessione al servizio di valutazione fallita. Riprova.", "practice_ai_analyzing": "Il tutor IA analizza la risposta...", "practice_ai_thinking": "Il tutor IA genera feedback", "word_pinyin_btn": "Pinyin", "word_translation_btn": "Trad.", "practice_badge_cn_to_en": "Traduzione · ZH→EN", "practice_badge_en_to_cn": "Traduzione · EN→ZH", "practice_badge_speak": "Parlato · cinese", "practice_badge_dictation": "Dettato", "practice_audio_played_times": "Riprodotto {{count}} volte · puoi ripetere", "practice_dictation_instruction": "Scrivi in caratteri cinesi ciò che senti", "practice_replay_hint": "Premi ↑ per ripetere", "practice_forfeit": "Mostra risposta", "practice_retry_show_answer": "Mostra di nuovo la risposta", "practice_asr_recognized": "Testo riconosciuto", "practice_retry_text": "Rispondi di nuovo", "practice_retry_speech": "Registra di nuovo", "practice_skip_question": "Salta domanda",
    "knowledge_title": "Dettagli conoscenza", "knowledge_current_sense": "Significato attuale", "knowledge_other_senses": "Altri significati", "knowledge_show": "Mostra", "knowledge_hide": "Nascondi", "study_error_load": "Impossibile caricare i dati del corso. Controlla la sincronizzazione backend.", "study_retry": "Riprova", "teaching_video_label": "Motore di contesto visivo", "teaching_diary_original": "Testo originale", "teaching_reading": "Lettura", "teaching_content": "Contenuto", "teaching_dialogue": "Dialogo", "teaching_pinyin_on": "Pinyin attivo", "teaching_pinyin_off": "Pinyin disattivo", "teaching_translation_on": "Traduzione attiva", "teaching_translation_off": "Traduzione disattiva", "teaching_generating_quiz": "Generazione quiz..."
  }
};

const PAGE_TRANSLATIONS = {
  zh: {
    common_back: "返回", common_cancel: "取消", common_save: "保存", common_edit: "修改",
    typing_intro_title: "电脑打字教程", typing_intro_subtitle: "输入法 · 拼音打字 · 练习", typing_intro_coming_soon: "内容即将上线", typing_intro_body: "这里将包含中文输入法安装、拼音打字方法和打字练习等内容。",
    overview_subtitle: "基于 FSRS 算法为您定制的今日学习计划", overview_due_review: "待复习", overview_tasks_unit: "任务", overview_stability: "稳定性", overview_stability_unit: "稳定度", overview_learning_stage: "学习阶段", overview_level_unit: "等级", overview_today_list: "今日清单", overview_all_done: "今日任务已全部完成！",
    finish_all_title: "全部通关！", finish_lesson_title: "干得漂亮！", finish_all_desc: "你已经扫清了所有到期的复习题，并且完成了所有的课程。给自己鼓个掌吧！", finish_lesson_desc: "你已成功完成当前学习任务！要一鼓作气继续挑战下一关吗？", finish_back_classroom: "回到教室", finish_continue_next: "继续下一课",
    speech_panel_label: "语音练习", speech_panel_title: "先录音，再确认后提交", speech_panel_attempts: "已录 {{count}} 次", speech_panel_max_seconds: "最长 {{count}} 秒", speech_status_recording: "录音中", speech_status_transcribing: "转写中", speech_status_idle: "待开始", speech_submit_answer: "提交本次回答", speech_preview_recording: "正在聆听，请开始说话。", speech_preview_transcribing: "录音已结束，正在生成识别结果。", speech_preview_idle: "还没有识别结果，点击下方按钮开始录音。", speech_hint_transcribing: "已经收到录音，正在转换成文字。", speech_start_recording: "开始录音", speech_stop_recording: "结束录音", practice_answer_language_warning: "请用{{language}}回答", speech_error_no_valid_input: "未检测到有效语音输入，请重新录音。", speech_error_low_confidence: "语音识别置信度较低（{{confidence}}），建议重新录音。", speech_error_transcribe_failed: "语音转写失败，请重试。", speech_error_unsupported_browser: "当前浏览器不支持录音，请更换现代浏览器后再试。", speech_error_no_audio: "没有录到有效音频，请重新录音。", speech_error_max_duration: "已达到最长录音时长，系统已自动停止并开始转写。", speech_error_mic_unavailable: "麦克风权限不可用，或当前设备无法录音。", speech_error_unstable_result: "语音识别结果不够稳定，请重新录音后再提交。", practice_prompt_pattern_replace: "句型替换", practice_prompt_understand_english: "理解英文", practice_prompt_en_listen_write: "听写英文", practice_prompt_speak_english: "开口说英语", practice_badge_pattern_drill: "句型替换", practice_badge_english_dictation: "英文听写", practice_badge_speak_english: "口语 · 英文", practice_pattern_label: "句型", practice_play_prompt_audio: "播放题目音频",
    teaching_full_lesson_audio: "本课完整对话音频", teaching_play_lesson_audio: "播放整课音频", teaching_pause_lesson_audio: "暂停播放整课音频", teaching_adjust_volume: "调节音量", teaching_set_playback_speed: "设置播放倍速", teaching_lesson_audio: "课文音频", teaching_set_floating_speed: "设置悬浮课文音频倍速", teaching_speed_value: "倍速 {{rate}}x", teaching_collapse_audio_bar: "收起悬浮课文音频条", teaching_expand_audio_bar: "展开悬浮课文音频条", teaching_play_line_audio: "播放音频",
    settings_loading: "加载中...", settings_loading_profile: "正在读取资料...", settings_no_email: "暂无邮箱", settings_change_avatar: "修改头像", settings_nickname_hint: "2-24 个字符，支持中英文、数字、空格和 `_ - .`，且昵称不能重复。", settings_password_title: "修改密码", settings_password_desc: "使用当前密码验证身份，再设置一个新的登录密码。", settings_current_password: "当前密码", settings_new_password: "新密码", settings_confirm_new_password: "确认新密码", settings_pw_req_length: "8 到 32 位", settings_pw_req_letter: "至少一个字母", settings_pw_req_number: "至少一个数字", settings_pw_req_special: "至少一个特殊字符", settings_pw_req_no_space: "不能有空格", settings_pw_req_match: "确认密码一致", settings_pw_req_different: "新旧密码不能相同", settings_save_new_password: "保存新密码", settings_provider_password_desc: "当前账号通过 {{provider}} 登录，密码由 {{provider}} 账户管理。", settings_provider_password: "邮箱密码", settings_unknown_time: "未知时间", settings_status_success: "成功", settings_device_label: "设备", settings_unknown_device: "未知设备", settings_unknown_ip: "未知 IP", settings_security_log_title: "账号安全记录", settings_view: "查看", settings_refresh_logs: "刷新记录", settings_no_login_logs: "暂无登录记录", settings_delete_account_title: "注销账号", settings_delete: "删除", settings_delete_confirm_desc_prefix: "请输入", settings_delete_confirm_desc_suffix: "确认注销账号。账号删除后，当前学习数据和登录记录将无法恢复。", settings_confirm_text: "确认文本", settings_confirm_delete: "确认注销",
    settings_user_missing: "未找到当前用户", settings_password_requirements_first: "请先满足全部密码要求", settings_password_updated: "密码已更新", settings_password_update_failed: "密码修改失败", settings_nickname_length_error: "昵称需为 2 到 24 个字符", settings_nickname_format_error: "昵称仅支持中英文、数字、空格和 _-.", settings_nickname_save_failed: "昵称保存失败", settings_login_history_failed: "登录记录加载失败", settings_delete_success: "账号已注销，正在返回首页", settings_delete_failed: "账号注销失败",
    settings_account_security: "账户与安全", settings_nickname: "昵称", settings_email: "邮箱", settings_language_eyebrow: "语言", settings_language_title: "界面语言 / 母语", settings_language_desc: "统一管理界面显示语言和学习母语。", settings_interface_language: "界面语言", settings_native_language: "母语", settings_feedback_eyebrow: "答题反馈", settings_feedback_title: "答题与反馈设置", settings_feedback_desc: "控制判题标准、提示信息和语音播放方式。", settings_strictness_label: "判题严格度偏好", settings_strictness_strict: "严格", settings_strictness_balanced: "平衡", settings_strictness_friendly: "宽松", settings_default_hints: "默认提示", settings_show_pinyin: "默认显示拼音", settings_show_meaning: "默认显示释义", settings_show_grammar: "默认显示语法提示", settings_ai_explanation: "答错后立即显示 AI 解释", settings_ai_explanation_desc: "在用户答错后马上给出解释、错误分析和更自然的替代表达。", settings_auto_play_audio: "音频自动播放", settings_auto_play_audio_desc: "进入题目或讲解内容时自动播报音频。", settings_playback_speed: "发音语速", settings_speed_slow: "0.8x 慢速", settings_speed_normal: "1.0x 标准", settings_speed_fast: "1.2x 稍快", settings_notifications_eyebrow: "通知提醒", settings_notifications_title: "通知与提醒", settings_notifications_desc: "统一管理学习提醒、课程更新和账号通知。", settings_email_notifications: "邮件通知开关", settings_email_notifications_desc: "统一控制所有邮件类通知。", settings_daily_reminder: "每日学习提醒", settings_daily_reminder_desc: "在每天固定时间提醒用户开始学习。", settings_review_time: "复习提醒时间", settings_course_updates: "课程更新提醒", settings_course_updates_desc: "新课上线、课程内容变更时发送提醒。", settings_security_alerts: "账号安全通知", settings_security_alerts_desc: "密码更新、异常登录等安全事件即时提醒。", settings_support_eyebrow: "帮助支持", settings_support_title: "帮助与支持", settings_support_desc: "查看帮助入口、反馈渠道和版本信息。", settings_faq: "常见问题", settings_faq_desc: "账号、学习流、AI 判题和提醒相关说明。", settings_feedback_link: "问题反馈", settings_feedback_link_desc: "提交 bug、体验建议和课程内容修正意见。", settings_contact: "联系方式", settings_contact_desc: "支持邮箱、合作联系和课程沟通入口。", settings_version: "版本号与更新说明", settings_version_desc: "展示当前版本和最近更新内容。"
  },
  en: {
    common_back: "Back", common_cancel: "Cancel", common_save: "Save", common_edit: "Edit",
    typing_intro_title: "Typing Tutorial", typing_intro_subtitle: "Input methods · pinyin typing · practice", typing_intro_coming_soon: "Coming soon", typing_intro_body: "This section will cover Chinese input method setup, pinyin typing, and typing drills.",
    overview_subtitle: "Your FSRS-powered learning plan for today", overview_due_review: "Due Review", overview_tasks_unit: "Tasks", overview_stability: "Stability", overview_stability_unit: "Stability", overview_learning_stage: "Learning Stage", overview_level_unit: "Level", overview_today_list: "Today's List", overview_all_done: "All tasks are done for today!",
    finish_all_title: "All Clear!", finish_lesson_title: "Nice work!", finish_all_desc: "You cleared every due review and completed all course content. Take a well-earned moment.", finish_lesson_desc: "You finished the current learning task. Ready to keep the momentum going?", finish_back_classroom: "Back to Classroom", finish_continue_next: "Continue",
    speech_panel_label: "Speech Practice", speech_panel_title: "Record first, then confirm and submit", speech_panel_attempts: "{{count}} recording(s)", speech_panel_max_seconds: "Up to {{count}} seconds", speech_status_recording: "Recording", speech_status_transcribing: "Transcribing", speech_status_idle: "Ready", speech_submit_answer: "Submit answer", speech_preview_recording: "Listening. Start speaking when ready.", speech_preview_transcribing: "Recording ended. Generating the transcript.", speech_preview_idle: "No transcript yet. Start recording below.", speech_hint_transcribing: "Audio received. Converting it to text.", speech_start_recording: "Start recording", speech_stop_recording: "Stop recording", practice_answer_language_warning: "Please answer in {{language}}", speech_error_no_valid_input: "No valid speech was detected. Please record again.", speech_error_low_confidence: "Speech recognition confidence is low ({{confidence}}). Recording again is recommended.", speech_error_transcribe_failed: "Speech transcription failed. Please try again.", speech_error_unsupported_browser: "This browser does not support recording. Please try a modern browser.", speech_error_no_audio: "No usable audio was recorded. Please record again.", speech_error_max_duration: "Maximum recording time reached. Recording stopped and transcription has started.", speech_error_mic_unavailable: "Microphone permission is unavailable, or this device cannot record audio.", speech_error_unstable_result: "The speech recognition result is not stable enough. Please record again before submitting.", practice_prompt_pattern_replace: "Pattern replacement", practice_prompt_understand_english: "Understand English", practice_prompt_en_listen_write: "English dictation", practice_prompt_speak_english: "Speak English", practice_badge_pattern_drill: "Pattern Drill", practice_badge_english_dictation: "English Dictation", practice_badge_speak_english: "Speak English", practice_pattern_label: "Pattern", practice_play_prompt_audio: "Play prompt audio",
    teaching_full_lesson_audio: "Full lesson audio", teaching_play_lesson_audio: "Play lesson audio", teaching_pause_lesson_audio: "Pause lesson audio", teaching_adjust_volume: "Adjust volume", teaching_set_playback_speed: "Set playback speed", teaching_lesson_audio: "Lesson audio", teaching_set_floating_speed: "Set floating audio speed", teaching_speed_value: "Speed {{rate}}x", teaching_collapse_audio_bar: "Collapse audio bar", teaching_expand_audio_bar: "Expand audio bar", teaching_play_line_audio: "Play audio",
    settings_loading: "Loading...", settings_loading_profile: "Reading profile...", settings_no_email: "No email", settings_change_avatar: "Change Avatar", settings_nickname_hint: "2-24 characters. Letters, numbers, spaces, and `_ - .` are supported. Nicknames must be unique.", settings_password_title: "Change Password", settings_password_desc: "Verify with your current password, then set a new login password.", settings_current_password: "Current Password", settings_new_password: "New Password", settings_confirm_new_password: "Confirm New Password", settings_pw_req_length: "8 to 32 characters", settings_pw_req_letter: "At least one letter", settings_pw_req_number: "At least one number", settings_pw_req_special: "At least one special character", settings_pw_req_no_space: "No spaces", settings_pw_req_match: "Passwords match", settings_pw_req_different: "New password differs from current", settings_save_new_password: "Save New Password", settings_provider_password_desc: "This account signs in with {{provider}}. Passwords are managed by {{provider}}.", settings_provider_password: "Email password", settings_unknown_time: "Unknown time", settings_status_success: "Success", settings_device_label: "Device", settings_unknown_device: "Unknown device", settings_unknown_ip: "Unknown IP", settings_security_log_title: "Account Security Log", settings_view: "View", settings_refresh_logs: "Refresh", settings_no_login_logs: "No login records yet", settings_delete_account_title: "Delete Account", settings_delete: "Delete", settings_delete_confirm_desc_prefix: "Type", settings_delete_confirm_desc_suffix: "to confirm deletion. Your learning data and login history cannot be recovered.", settings_confirm_text: "Confirmation Text", settings_confirm_delete: "Confirm Delete",
    settings_user_missing: "Current user not found", settings_password_requirements_first: "Please satisfy all password requirements first", settings_password_updated: "Password updated", settings_password_update_failed: "Password update failed", settings_nickname_length_error: "Nickname must be 2 to 24 characters", settings_nickname_format_error: "Nickname only supports letters, numbers, spaces, and _-.", settings_nickname_save_failed: "Failed to save nickname", settings_login_history_failed: "Failed to load login history", settings_delete_success: "Account deleted. Returning home...", settings_delete_failed: "Account deletion failed",
    settings_account_security: "Account & Security", settings_nickname: "Nickname", settings_email: "Email", settings_language_eyebrow: "Language", settings_language_title: "Interface Language / Native Language", settings_language_desc: "Manage the app language and your learning native language.", settings_interface_language: "Interface Language", settings_native_language: "Native Language", settings_feedback_eyebrow: "Feedback", settings_feedback_title: "Answer & Feedback Settings", settings_feedback_desc: "Control grading strictness, hints, and audio behavior.", settings_strictness_label: "Grading strictness", settings_strictness_strict: "Strict", settings_strictness_balanced: "Balanced", settings_strictness_friendly: "Friendly", settings_default_hints: "Default Hints", settings_show_pinyin: "Show pinyin by default", settings_show_meaning: "Show meanings by default", settings_show_grammar: "Show grammar hints by default", settings_ai_explanation: "Show AI explanation after mistakes", settings_ai_explanation_desc: "When an answer is wrong, immediately show explanation, error analysis, and more natural alternatives.", settings_auto_play_audio: "Auto-play audio", settings_auto_play_audio_desc: "Automatically play audio when entering questions or lesson content.", settings_playback_speed: "Pronunciation Speed", settings_speed_slow: "0.8x Slow", settings_speed_normal: "1.0x Standard", settings_speed_fast: "1.2x Faster", settings_notifications_eyebrow: "Notifications", settings_notifications_title: "Notifications & Reminders", settings_notifications_desc: "Manage study reminders, course updates, and account notifications.", settings_email_notifications: "Email notifications", settings_email_notifications_desc: "Control all email notifications.", settings_daily_reminder: "Daily study reminder", settings_daily_reminder_desc: "Remind you to study at a fixed time each day.", settings_review_time: "Review Reminder Time", settings_course_updates: "Course update reminders", settings_course_updates_desc: "Send reminders when new lessons or course changes are available.", settings_security_alerts: "Account security alerts", settings_security_alerts_desc: "Notify you about password changes, unusual logins, and security events.", settings_support_eyebrow: "Support", settings_support_title: "Help & Support", settings_support_desc: "Find help, feedback channels, and version information.", settings_faq: "FAQ", settings_faq_desc: "Help for accounts, learning flow, AI grading, and reminders.", settings_feedback_link: "Feedback", settings_feedback_link_desc: "Submit bugs, experience suggestions, and course content corrections.", settings_contact: "Contact", settings_contact_desc: "Support email, collaboration, and course communication.", settings_version: "Version & Release Notes", settings_version_desc: "View the current version and recent updates."
  }
};

PAGE_TRANSLATIONS.jp = { ...PAGE_TRANSLATIONS.en, common_back: "戻る", common_cancel: "キャンセル", common_save: "保存", common_edit: "編集", typing_intro_title: "タイピング教程", overview_today_list: "今日のリスト", overview_all_done: "今日のタスクはすべて完了しました！", finish_lesson_title: "よくできました！", finish_back_classroom: "教室に戻る", finish_continue_next: "次へ進む", speech_panel_label: "音声練習", speech_status_recording: "録音中", speech_status_transcribing: "文字起こし中", speech_status_idle: "待機中", speech_start_recording: "録音開始", speech_stop_recording: "録音終了", speech_submit_answer: "回答を送信", settings_account_security: "アカウントとセキュリティ", settings_nickname: "ニックネーム", settings_email: "メール", settings_password_title: "パスワード変更", settings_language_title: "表示言語 / 母語", settings_interface_language: "表示言語", settings_native_language: "母語", settings_notifications_title: "通知とリマインダー", settings_support_title: "ヘルプとサポート" };
PAGE_TRANSLATIONS.fr = { ...PAGE_TRANSLATIONS.en, common_back: "Retour", common_cancel: "Annuler", common_save: "Enregistrer", common_edit: "Modifier", typing_intro_title: "Tutoriel de saisie", overview_today_list: "Liste du jour", overview_all_done: "Toutes les tâches du jour sont terminées !", finish_lesson_title: "Beau travail !", finish_back_classroom: "Retour à la classe", finish_continue_next: "Continuer", speech_panel_label: "Pratique orale", speech_status_recording: "Enregistrement", speech_status_transcribing: "Transcription", speech_status_idle: "Prêt", speech_start_recording: "Commencer l'enregistrement", speech_stop_recording: "Arrêter l'enregistrement", speech_submit_answer: "Envoyer la réponse", settings_account_security: "Compte et sécurité", settings_nickname: "Pseudo", settings_email: "E-mail", settings_password_title: "Changer le mot de passe", settings_language_title: "Langue de l'interface / langue maternelle", settings_interface_language: "Langue de l'interface", settings_native_language: "Langue maternelle", settings_notifications_title: "Notifications et rappels", settings_support_title: "Aide et support" };
PAGE_TRANSLATIONS.de = { ...PAGE_TRANSLATIONS.en, common_back: "Zurück", common_cancel: "Abbrechen", common_save: "Speichern", common_edit: "Bearbeiten", typing_intro_title: "Tippkurs", overview_today_list: "Heutige Liste", overview_all_done: "Alle Aufgaben für heute sind erledigt!", finish_lesson_title: "Gut gemacht!", finish_back_classroom: "Zurück zum Klassenzimmer", finish_continue_next: "Weiter", speech_panel_label: "Sprechübung", speech_status_recording: "Aufnahme", speech_status_transcribing: "Transkription", speech_status_idle: "Bereit", speech_start_recording: "Aufnahme starten", speech_stop_recording: "Aufnahme beenden", speech_submit_answer: "Antwort senden", settings_account_security: "Konto und Sicherheit", settings_nickname: "Nickname", settings_email: "E-Mail", settings_password_title: "Passwort ändern", settings_language_title: "Oberflächensprache / Muttersprache", settings_interface_language: "Oberflächensprache", settings_native_language: "Muttersprache", settings_notifications_title: "Benachrichtigungen und Erinnerungen", settings_support_title: "Hilfe und Support" };
["ko", "es", "vi", "pt", "ar", "th", "ru", "id", "ms", "it"].forEach((locale) => {
  PAGE_TRANSLATIONS[locale] = {
    ...PAGE_TRANSLATIONS.en,
    ...(NEW_LOCALE_EXTRA_OVERRIDES[locale] || {}),
  };
});

const PAGE_TRANSLATION_PATCHES = {
  jp: {
    typing_intro_subtitle: "入力方式・ピンイン入力・練習", typing_intro_coming_soon: "近日公開", typing_intro_body: "中国語入力方式の設定、ピンイン入力、タイピング練習を扱います。",
    overview_subtitle: "FSRS に基づく今日の学習プラン", overview_due_review: "復習待ち", overview_tasks_unit: "タスク", overview_stability: "安定度", overview_learning_stage: "学習段階", overview_level_unit: "レベル",
    speech_panel_title: "録音してから確認し、送信します", speech_panel_attempts: "{{count}} 回録音", speech_panel_max_seconds: "最大 {{count}} 秒", speech_preview_recording: "聞き取り中です。話し始めてください。", speech_preview_transcribing: "録音が終了しました。文字起こし中です。", speech_preview_idle: "まだ認識結果がありません。下のボタンで録音を開始してください。", speech_hint_transcribing: "音声を受信しました。テキストに変換中です。", speech_error_no_valid_input: "有効な音声が検出されませんでした。録音し直してください。", speech_error_low_confidence: "音声認識の信頼度が低いです（{{confidence}}）。録音し直すことをおすすめします。", speech_error_transcribe_failed: "文字起こしに失敗しました。もう一度お試しください。", speech_error_unsupported_browser: "このブラウザーは録音に対応していません。新しいブラウザーでお試しください。", speech_error_no_audio: "有効な音声が録音されませんでした。録音し直してください。", speech_error_max_duration: "録音上限に達したため、自動停止して文字起こしを開始しました。", speech_error_mic_unavailable: "マイク権限がないか、この端末では録音できません。", speech_error_unstable_result: "音声認識結果が十分安定していません。送信前に録音し直してください。",
    practice_prompt_pattern_replace: "文型置換", practice_prompt_understand_english: "英語を理解", practice_prompt_en_listen_write: "英語ディクテーション", practice_prompt_speak_english: "英語を話す", practice_badge_pattern_drill: "文型練習", practice_badge_english_dictation: "英語ディクテーション", practice_badge_speak_english: "英語を話す", practice_pattern_label: "文型", practice_play_prompt_audio: "問題音声を再生",
    teaching_full_lesson_audio: "レッスン全体の音声", teaching_play_lesson_audio: "レッスン音声を再生", teaching_pause_lesson_audio: "レッスン音声を一時停止", teaching_adjust_volume: "音量を調整", teaching_set_playback_speed: "再生速度を設定", teaching_lesson_audio: "本文音声", teaching_set_floating_speed: "フローティング音声の速度を設定", teaching_speed_value: "速度 {{rate}}x", teaching_collapse_audio_bar: "音声バーを折りたたむ", teaching_expand_audio_bar: "音声バーを展開", teaching_play_line_audio: "音声を再生"
  },
  fr: {
    typing_intro_subtitle: "Méthodes de saisie · pinyin · pratique", typing_intro_coming_soon: "Bientôt disponible", typing_intro_body: "Cette section couvrira l'installation des méthodes de saisie chinoises, la frappe en pinyin et les exercices.",
    overview_subtitle: "Votre plan d'apprentissage du jour avec FSRS", overview_due_review: "Révisions dues", overview_tasks_unit: "Tâches", overview_stability: "Stabilité", overview_learning_stage: "Étape", overview_level_unit: "Niveau",
    speech_panel_title: "Enregistrez, vérifiez, puis envoyez", speech_panel_attempts: "{{count}} enregistrement(s)", speech_panel_max_seconds: "Jusqu'à {{count}} s", speech_error_no_valid_input: "Aucune voix valide détectée. Réenregistrez.", speech_error_low_confidence: "La confiance de reconnaissance est faible ({{confidence}}). Réenregistrer est conseillé.", speech_error_transcribe_failed: "Échec de la transcription. Réessayez.", speech_error_unsupported_browser: "Ce navigateur ne prend pas en charge l'enregistrement.", speech_error_no_audio: "Aucun audio exploitable enregistré. Réenregistrez.", speech_error_max_duration: "Durée maximale atteinte. L'enregistrement est arrêté et la transcription commence.", speech_error_mic_unavailable: "Micro indisponible ou permission refusée.", speech_error_unstable_result: "Le résultat vocal n'est pas assez stable. Réenregistrez avant d'envoyer.",
    practice_prompt_pattern_replace: "Substitution de modèle", practice_prompt_understand_english: "Comprendre l'anglais", practice_prompt_en_listen_write: "Dictée anglaise", practice_prompt_speak_english: "Parler anglais", practice_badge_pattern_drill: "Exercice de modèle", practice_badge_english_dictation: "Dictée anglaise", practice_badge_speak_english: "Parler anglais", practice_pattern_label: "Modèle", practice_play_prompt_audio: "Lire l'audio de la question",
    teaching_full_lesson_audio: "Audio complet de la leçon", teaching_play_lesson_audio: "Lire l'audio", teaching_pause_lesson_audio: "Mettre l'audio en pause", teaching_adjust_volume: "Régler le volume", teaching_set_playback_speed: "Régler la vitesse", teaching_lesson_audio: "Audio du texte", teaching_set_floating_speed: "Régler la vitesse flottante", teaching_speed_value: "Vitesse {{rate}}x", teaching_collapse_audio_bar: "Réduire la barre audio", teaching_expand_audio_bar: "Déployer la barre audio", teaching_play_line_audio: "Lire l'audio"
  },
  de: {
    typing_intro_subtitle: "Eingabemethoden · Pinyin-Tippen · Übung", typing_intro_coming_soon: "Bald verfügbar", typing_intro_body: "Dieser Bereich behandelt chinesische Eingabemethoden, Pinyin-Tippen und Tippübungen.",
    overview_subtitle: "Dein heutiger FSRS-Lernplan", overview_due_review: "Fällige Wiederholungen", overview_tasks_unit: "Aufgaben", overview_stability: "Stabilität", overview_learning_stage: "Lernphase", overview_level_unit: "Stufe",
    speech_panel_title: "Erst aufnehmen, dann prüfen und senden", speech_panel_attempts: "{{count}} Aufnahme(n)", speech_panel_max_seconds: "Bis zu {{count}} s", speech_error_no_valid_input: "Keine gültige Sprache erkannt. Bitte erneut aufnehmen.", speech_error_low_confidence: "Die Erkennungssicherheit ist niedrig ({{confidence}}). Eine neue Aufnahme wird empfohlen.", speech_error_transcribe_failed: "Transkription fehlgeschlagen. Bitte erneut versuchen.", speech_error_unsupported_browser: "Dieser Browser unterstützt keine Aufnahme.", speech_error_no_audio: "Keine nutzbare Audiodatei aufgenommen. Bitte erneut aufnehmen.", speech_error_max_duration: "Maximale Aufnahmedauer erreicht. Die Transkription wurde gestartet.", speech_error_mic_unavailable: "Mikrofonberechtigung fehlt oder das Gerät kann nicht aufnehmen.", speech_error_unstable_result: "Das Sprachergebnis ist nicht stabil genug. Bitte vor dem Senden neu aufnehmen.",
    practice_prompt_pattern_replace: "Satzmuster ersetzen", practice_prompt_understand_english: "Englisch verstehen", practice_prompt_en_listen_write: "Englisches Diktat", practice_prompt_speak_english: "Englisch sprechen", practice_badge_pattern_drill: "Satzmusterübung", practice_badge_english_dictation: "Englisches Diktat", practice_badge_speak_english: "Englisch sprechen", practice_pattern_label: "Muster", practice_play_prompt_audio: "Aufgabenaudio abspielen",
    teaching_full_lesson_audio: "Gesamte Lektionsaudio", teaching_play_lesson_audio: "Lektionsaudio abspielen", teaching_pause_lesson_audio: "Lektionsaudio pausieren", teaching_adjust_volume: "Lautstärke anpassen", teaching_set_playback_speed: "Wiedergabegeschwindigkeit einstellen", teaching_lesson_audio: "Textaudio", teaching_set_floating_speed: "Schwebende Audiogeschwindigkeit einstellen", teaching_speed_value: "Tempo {{rate}}x", teaching_collapse_audio_bar: "Audioleiste einklappen", teaching_expand_audio_bar: "Audioleiste ausklappen", teaching_play_line_audio: "Audio abspielen"
  },
  ko: { typing_intro_title: "타이핑 튜토리얼", typing_intro_subtitle: "입력기 · 병음 타이핑 · 연습", overview_subtitle: "FSRS 기반 오늘 학습 계획", finish_lesson_title: "잘했어요!", speech_panel_title: "먼저 녹음하고 확인 후 제출하세요", speech_error_no_valid_input: "유효한 음성이 감지되지 않았습니다. 다시 녹음하세요.", speech_error_transcribe_failed: "음성 전사에 실패했습니다. 다시 시도하세요.", speech_error_unstable_result: "음성 인식 결과가 충분히 안정적이지 않습니다. 다시 녹음하세요.", practice_prompt_pattern_replace: "문형 바꾸기", practice_prompt_understand_english: "영어 이해", practice_prompt_en_listen_write: "영어 받아쓰기", practice_prompt_speak_english: "영어 말하기", practice_badge_pattern_drill: "문형 연습", practice_badge_english_dictation: "영어 받아쓰기", practice_badge_speak_english: "영어 말하기", teaching_full_lesson_audio: "전체 수업 오디오", teaching_lesson_audio: "본문 오디오", teaching_speed_value: "속도 {{rate}}x", teaching_play_line_audio: "오디오 재생" },
  es: { typing_intro_title: "Tutorial de escritura", typing_intro_subtitle: "IME · pinyin · práctica", overview_subtitle: "Tu plan de hoy con FSRS", finish_lesson_title: "¡Buen trabajo!", speech_panel_title: "Graba, confirma y envía", speech_error_no_valid_input: "No se detectó voz válida. Graba de nuevo.", speech_error_transcribe_failed: "Falló la transcripción. Inténtalo de nuevo.", speech_error_unstable_result: "El reconocimiento no es lo bastante estable. Graba de nuevo.", practice_prompt_pattern_replace: "Sustitución de patrón", practice_prompt_understand_english: "Comprender inglés", practice_prompt_en_listen_write: "Dictado en inglés", practice_prompt_speak_english: "Hablar inglés", practice_badge_pattern_drill: "Práctica de patrón", practice_badge_english_dictation: "Dictado inglés", practice_badge_speak_english: "Hablar inglés", teaching_full_lesson_audio: "Audio completo de la lección", teaching_lesson_audio: "Audio del texto", teaching_speed_value: "Velocidad {{rate}}x", teaching_play_line_audio: "Reproducir audio" },
  vi: { typing_intro_title: "Hướng dẫn gõ", typing_intro_subtitle: "Bộ gõ · gõ pinyin · luyện tập", overview_subtitle: "Kế hoạch học hôm nay theo FSRS", finish_lesson_title: "Làm tốt lắm!", speech_panel_title: "Ghi âm, kiểm tra rồi gửi", speech_error_no_valid_input: "Không phát hiện giọng nói hợp lệ. Hãy ghi âm lại.", speech_error_transcribe_failed: "Không chuyển giọng nói thành văn bản được. Thử lại nhé.", speech_error_unstable_result: "Kết quả nhận dạng chưa đủ ổn định. Hãy ghi âm lại.", practice_prompt_pattern_replace: "Thay mẫu câu", practice_prompt_understand_english: "Hiểu tiếng Anh", practice_prompt_en_listen_write: "Chính tả tiếng Anh", practice_prompt_speak_english: "Nói tiếng Anh", practice_badge_pattern_drill: "Luyện mẫu câu", practice_badge_english_dictation: "Chính tả tiếng Anh", practice_badge_speak_english: "Nói tiếng Anh", teaching_full_lesson_audio: "Âm thanh toàn bài", teaching_lesson_audio: "Âm thanh bài đọc", teaching_speed_value: "Tốc độ {{rate}}x", teaching_play_line_audio: "Phát âm thanh" },
  pt: { typing_intro_title: "Tutorial de digitação", typing_intro_subtitle: "IME · pinyin · prática", overview_subtitle: "Seu plano de hoje com FSRS", finish_lesson_title: "Bom trabalho!", speech_panel_title: "Grave, confirme e envie", speech_error_no_valid_input: "Nenhuma fala válida detectada. Grave novamente.", speech_error_transcribe_failed: "Falha na transcrição. Tente novamente.", speech_error_unstable_result: "O reconhecimento ainda não está estável. Grave novamente.", practice_prompt_pattern_replace: "Substituição de padrão", practice_prompt_understand_english: "Entender inglês", practice_prompt_en_listen_write: "Ditado em inglês", practice_prompt_speak_english: "Falar inglês", practice_badge_pattern_drill: "Prática de padrão", practice_badge_english_dictation: "Ditado em inglês", practice_badge_speak_english: "Falar inglês", teaching_full_lesson_audio: "Áudio completo da aula", teaching_lesson_audio: "Áudio do texto", teaching_speed_value: "Velocidade {{rate}}x", teaching_play_line_audio: "Tocar áudio" },
  ar: { typing_intro_title: "درس الكتابة", typing_intro_subtitle: "طرق الإدخال · بينيين · تدريب", overview_subtitle: "خطة اليوم وفق FSRS", finish_lesson_title: "عمل رائع!", speech_panel_title: "سجّل أولاً ثم راجع وأرسل", speech_error_no_valid_input: "لم يتم اكتشاف صوت صالح. سجّل مرة أخرى.", speech_error_transcribe_failed: "فشل تحويل الصوت إلى نص. حاول مرة أخرى.", speech_error_unstable_result: "نتيجة التعرف الصوتي غير مستقرة بما يكفي. سجّل مرة أخرى.", practice_prompt_pattern_replace: "استبدال النمط", practice_prompt_understand_english: "فهم الإنجليزية", practice_prompt_en_listen_write: "إملاء إنجليزي", practice_prompt_speak_english: "تحدث الإنجليزية", practice_badge_pattern_drill: "تدريب النمط", practice_badge_english_dictation: "إملاء إنجليزي", practice_badge_speak_english: "تحدث الإنجليزية", teaching_full_lesson_audio: "صوت الدرس الكامل", teaching_lesson_audio: "صوت النص", teaching_speed_value: "السرعة {{rate}}x", teaching_play_line_audio: "تشغيل الصوت" },
  th: { typing_intro_title: "บทเรียนพิมพ์", typing_intro_subtitle: "IME · พิมพ์พินอิน · ฝึก", overview_subtitle: "แผนเรียนวันนี้ด้วย FSRS", finish_lesson_title: "ทำได้ดีมาก!", speech_panel_title: "อัดเสียง ตรวจสอบ แล้วส่ง", speech_error_no_valid_input: "ไม่พบเสียงที่ใช้ได้ กรุณาอัดใหม่", speech_error_transcribe_failed: "ถอดเสียงไม่สำเร็จ ลองอีกครั้ง", speech_error_unstable_result: "ผลรู้จำเสียงยังไม่เสถียรพอ กรุณาอัดใหม่", practice_prompt_pattern_replace: "แทนรูปประโยค", practice_prompt_understand_english: "เข้าใจอังกฤษ", practice_prompt_en_listen_write: "เขียนตามคำบอกอังกฤษ", practice_prompt_speak_english: "พูดอังกฤษ", practice_badge_pattern_drill: "ฝึกรูปประโยค", practice_badge_english_dictation: "เขียนตามคำบอกอังกฤษ", practice_badge_speak_english: "พูดอังกฤษ", teaching_full_lesson_audio: "เสียงทั้งบทเรียน", teaching_lesson_audio: "เสียงบทอ่าน", teaching_speed_value: "ความเร็ว {{rate}}x", teaching_play_line_audio: "เล่นเสียง" },
  ru: { typing_intro_title: "Урок набора", typing_intro_subtitle: "IME · пиньинь · практика", overview_subtitle: "Ваш план на сегодня по FSRS", finish_lesson_title: "Отличная работа!", speech_panel_title: "Запишите, проверьте и отправьте", speech_error_no_valid_input: "Речь не распознана. Запишите снова.", speech_error_transcribe_failed: "Не удалось расшифровать речь. Повторите попытку.", speech_error_unstable_result: "Результат распознавания недостаточно стабилен. Запишите снова.", practice_prompt_pattern_replace: "Замена шаблона", practice_prompt_understand_english: "Понять английский", practice_prompt_en_listen_write: "Английский диктант", practice_prompt_speak_english: "Говорить по-английски", practice_badge_pattern_drill: "Тренировка шаблона", practice_badge_english_dictation: "Английский диктант", practice_badge_speak_english: "Говорить по-английски", teaching_full_lesson_audio: "Аудио всего урока", teaching_lesson_audio: "Аудио текста", teaching_speed_value: "Скорость {{rate}}x", teaching_play_line_audio: "Воспроизвести аудио" },
  id: { typing_intro_title: "Tutorial mengetik", typing_intro_subtitle: "IME · pinyin · latihan", overview_subtitle: "Rencana belajar hari ini dengan FSRS", finish_lesson_title: "Kerja bagus!", speech_panel_title: "Rekam, periksa, lalu kirim", speech_error_no_valid_input: "Tidak ada suara valid terdeteksi. Rekam lagi.", speech_error_transcribe_failed: "Transkripsi gagal. Coba lagi.", speech_error_unstable_result: "Hasil pengenalan suara belum stabil. Rekam lagi.", practice_prompt_pattern_replace: "Ganti pola kalimat", practice_prompt_understand_english: "Pahami bahasa Inggris", practice_prompt_en_listen_write: "Dikte bahasa Inggris", practice_prompt_speak_english: "Bicara bahasa Inggris", practice_badge_pattern_drill: "Latihan pola", practice_badge_english_dictation: "Dikte Inggris", practice_badge_speak_english: "Bicara Inggris", teaching_full_lesson_audio: "Audio pelajaran penuh", teaching_lesson_audio: "Audio teks", teaching_speed_value: "Kecepatan {{rate}}x", teaching_play_line_audio: "Putar audio" },
  ms: { typing_intro_title: "Tutorial menaip", typing_intro_subtitle: "IME · pinyin · latihan", overview_subtitle: "Pelan belajar hari ini dengan FSRS", finish_lesson_title: "Bagus!", speech_panel_title: "Rakam, semak, kemudian hantar", speech_error_no_valid_input: "Tiada suara sah dikesan. Rakam semula.", speech_error_transcribe_failed: "Transkripsi gagal. Cuba lagi.", speech_error_unstable_result: "Keputusan pengecaman suara belum cukup stabil. Rakam semula.", practice_prompt_pattern_replace: "Ganti pola ayat", practice_prompt_understand_english: "Fahami bahasa Inggeris", practice_prompt_en_listen_write: "Dikte Inggeris", practice_prompt_speak_english: "Bertutur Inggeris", practice_badge_pattern_drill: "Latihan pola", practice_badge_english_dictation: "Dikte Inggeris", practice_badge_speak_english: "Bertutur Inggeris", teaching_full_lesson_audio: "Audio penuh pelajaran", teaching_lesson_audio: "Audio teks", teaching_speed_value: "Kelajuan {{rate}}x", teaching_play_line_audio: "Main audio" },
  it: { typing_intro_title: "Tutorial di digitazione", typing_intro_subtitle: "IME · pinyin · pratica", overview_subtitle: "Il tuo piano di oggi con FSRS", finish_lesson_title: "Ottimo lavoro!", speech_panel_title: "Registra, controlla e invia", speech_error_no_valid_input: "Nessuna voce valida rilevata. Registra di nuovo.", speech_error_transcribe_failed: "Trascrizione fallita. Riprova.", speech_error_unstable_result: "Il riconoscimento non è abbastanza stabile. Registra di nuovo.", practice_prompt_pattern_replace: "Sostituzione del modello", practice_prompt_understand_english: "Comprendere l'inglese", practice_prompt_en_listen_write: "Dettato inglese", practice_prompt_speak_english: "Parlare inglese", practice_badge_pattern_drill: "Esercizio modello", practice_badge_english_dictation: "Dettato inglese", practice_badge_speak_english: "Parlare inglese", teaching_full_lesson_audio: "Audio completo della lezione", teaching_lesson_audio: "Audio del testo", teaching_speed_value: "Velocità {{rate}}x", teaching_play_line_audio: "Riproduci audio" }
};

Object.entries(PAGE_TRANSLATION_PATCHES).forEach(([locale, overrides]) => {
  PAGE_TRANSLATIONS[locale] = {
    ...(PAGE_TRANSLATIONS[locale] || PAGE_TRANSLATIONS.en),
    ...overrides,
  };
});

Object.entries(NEW_LOCALE_OVERRIDES).forEach(([locale, overrides]) => {
  resources[locale] = {
    translation: {
      ...resources.en.translation,
      ...(PAGE_TRANSLATIONS.en || {}),
      ...overrides,
      ...(NEW_LOCALE_EXTRA_OVERRIDES[locale] || {}),
      ...(PAGE_TRANSLATIONS[locale] || {}),
    },
  };
});
resources.ja = resources.jp;

Object.entries(PAGE_TRANSLATIONS).forEach(([locale, overrides]) => {
  if (!resources[locale]) return;
  resources[locale].translation = {
    ...resources[locale].translation,
    ...overrides,
  };
});

Object.entries(INTRO_VIDEO_TRANSLATIONS).forEach(([locale, overrides]) => {
  if (!resources[locale]) return;
  resources[locale].translation = {
    ...resources[locale].translation,
    ...overrides,
  };
});

Object.entries(COURSE_INTRO_PAGE_TRANSLATIONS).forEach(([locale, overrides]) => {
  if (!resources[locale]) return;
  resources[locale].translation = {
    ...resources[locale].translation,
    ...overrides,
  };
});

Object.entries(TYPING_INTRO_TRANSLATIONS).forEach(([locale, overrides]) => {
  if (!resources[locale]) return;
  resources[locale].translation.typing_intro = overrides;
});

Object.entries(PINYIN_INTRO_TRANSLATIONS).forEach(([locale, overrides]) => {
  if (!resources[locale]) return;
  resources[locale].translation.pinyin_intro = overrides;
});

const COURSE_PROGRESS_TRANSLATIONS = {
  zh: {
    course_progress_label: "课程进度",
    course_progress_completed_count: "已完成 {{completed}} / {{total}} 课",
    course_progress_next_lesson: "下一课",
    course_progress_start_practice: "已看讲解，进入练习",
    course_progress_resume_practice: "继续练习第 {{number}} 题",
    course_progress_completed: "课程已完成",
    course_progress_all_done: "全部课时已完成",
    course_untitled_lesson: "未命名课时",
    course_lesson_completed: "已完成",
    course_lesson_current: "当前课时",
    course_lesson_not_started: "未开始",
  },
  en: {
    course_progress_label: "Course Progress",
    course_progress_completed_count: "{{completed}} / {{total}} lessons completed",
    course_progress_next_lesson: "Next lesson",
    course_progress_start_practice: "Teaching viewed. Start practice",
    course_progress_resume_practice: "Resume practice question {{number}}",
    course_progress_completed: "Course completed",
    course_progress_all_done: "All lessons completed",
    course_untitled_lesson: "Untitled lesson",
    course_lesson_completed: "Completed",
    course_lesson_current: "Current",
    course_lesson_not_started: "Not started",
  },
  jp: {
    course_progress_label: "コース進捗",
    course_progress_completed_count: "{{completed}} / {{total}} レッスン完了",
    course_progress_next_lesson: "次のレッスン",
    course_progress_start_practice: "解説を見ました。練習へ",
    course_progress_resume_practice: "練習 {{number}} 問目から再開",
    course_progress_completed: "コース完了",
    course_progress_all_done: "すべてのレッスン完了",
    course_untitled_lesson: "無題のレッスン",
    course_lesson_completed: "完了",
    course_lesson_current: "現在のレッスン",
    course_lesson_not_started: "未開始",
  },
  fr: {
    course_progress_label: "Progression du cours",
    course_progress_completed_count: "{{completed}} / {{total}} leçons terminées",
    course_progress_next_lesson: "Prochaine leçon",
    course_progress_start_practice: "Leçon vue. Commencer l'exercice",
    course_progress_resume_practice: "Reprendre à la question {{number}}",
    course_progress_completed: "Cours terminé",
    course_progress_all_done: "Toutes les leçons sont terminées",
    course_untitled_lesson: "Leçon sans titre",
    course_lesson_completed: "Terminée",
    course_lesson_current: "En cours",
    course_lesson_not_started: "Non commencée",
  },
  de: {
    course_progress_label: "Kursfortschritt",
    course_progress_completed_count: "{{completed}} / {{total}} Lektionen abgeschlossen",
    course_progress_next_lesson: "Nächste Lektion",
    course_progress_start_practice: "Erklärung gesehen. Übung starten",
    course_progress_resume_practice: "Bei Frage {{number}} fortfahren",
    course_progress_completed: "Kurs abgeschlossen",
    course_progress_all_done: "Alle Lektionen abgeschlossen",
    course_untitled_lesson: "Unbenannte Lektion",
    course_lesson_completed: "Abgeschlossen",
    course_lesson_current: "Aktuell",
    course_lesson_not_started: "Nicht begonnen",
  },
  ko: {
    course_progress_label: "코스 진행률",
    course_progress_completed_count: "{{completed}} / {{total}} 레슨 완료",
    course_progress_next_lesson: "다음 레슨",
    course_progress_start_practice: "강의를 봤습니다. 연습 시작",
    course_progress_resume_practice: "{{number}}번 문제부터 계속",
    course_progress_completed: "코스 완료",
    course_progress_all_done: "모든 레슨 완료",
    course_untitled_lesson: "제목 없는 레슨",
    course_lesson_completed: "완료",
    course_lesson_current: "현재 레슨",
    course_lesson_not_started: "시작 전",
  },
  es: {
    course_progress_label: "Progreso del curso",
    course_progress_completed_count: "{{completed}} / {{total}} lecciones completadas",
    course_progress_next_lesson: "Siguiente lección",
    course_progress_start_practice: "Lección vista. Empezar práctica",
    course_progress_resume_practice: "Continuar en la pregunta {{number}}",
    course_progress_completed: "Curso completado",
    course_progress_all_done: "Todas las lecciones completadas",
    course_untitled_lesson: "Lección sin título",
    course_lesson_completed: "Completada",
    course_lesson_current: "Actual",
    course_lesson_not_started: "No iniciada",
  },
  vi: {
    course_progress_label: "Tiến độ khóa học",
    course_progress_completed_count: "Đã hoàn thành {{completed}} / {{total}} bài",
    course_progress_next_lesson: "Bài tiếp theo",
    course_progress_start_practice: "Đã xem bài giảng. Bắt đầu luyện tập",
    course_progress_resume_practice: "Tiếp tục câu {{number}}",
    course_progress_completed: "Đã hoàn thành khóa học",
    course_progress_all_done: "Đã hoàn thành tất cả bài học",
    course_untitled_lesson: "Bài học chưa đặt tên",
    course_lesson_completed: "Đã xong",
    course_lesson_current: "Bài hiện tại",
    course_lesson_not_started: "Chưa bắt đầu",
  },
  pt: {
    course_progress_label: "Progresso do curso",
    course_progress_completed_count: "{{completed}} / {{total}} aulas concluídas",
    course_progress_next_lesson: "Próxima aula",
    course_progress_start_practice: "Aula vista. Começar prática",
    course_progress_resume_practice: "Continuar na pergunta {{number}}",
    course_progress_completed: "Curso concluído",
    course_progress_all_done: "Todas as aulas concluídas",
    course_untitled_lesson: "Aula sem título",
    course_lesson_completed: "Concluída",
    course_lesson_current: "Atual",
    course_lesson_not_started: "Não iniciada",
  },
  ar: {
    course_progress_label: "تقدم الدورة",
    course_progress_completed_count: "أكملت {{completed}} / {{total}} درسًا",
    course_progress_next_lesson: "الدرس التالي",
    course_progress_start_practice: "تمت مشاهدة الشرح. ابدأ التدريب",
    course_progress_resume_practice: "تابع من السؤال {{number}}",
    course_progress_completed: "اكتملت الدورة",
    course_progress_all_done: "اكتملت كل الدروس",
    course_untitled_lesson: "درس بلا عنوان",
    course_lesson_completed: "مكتمل",
    course_lesson_current: "الحالي",
    course_lesson_not_started: "لم يبدأ",
  },
  th: {
    course_progress_label: "ความคืบหน้าคอร์ส",
    course_progress_completed_count: "เรียนจบแล้ว {{completed}} / {{total}} บท",
    course_progress_next_lesson: "บทเรียนถัดไป",
    course_progress_start_practice: "ดูคำอธิบายแล้ว เริ่มฝึก",
    course_progress_resume_practice: "ทำต่อที่ข้อ {{number}}",
    course_progress_completed: "จบคอร์สแล้ว",
    course_progress_all_done: "จบบทเรียนทั้งหมดแล้ว",
    course_untitled_lesson: "บทเรียนไม่มีชื่อ",
    course_lesson_completed: "เสร็จแล้ว",
    course_lesson_current: "บทปัจจุบัน",
    course_lesson_not_started: "ยังไม่เริ่ม",
  },
  ru: {
    course_progress_label: "Прогресс курса",
    course_progress_completed_count: "Завершено {{completed}} / {{total}} уроков",
    course_progress_next_lesson: "Следующий урок",
    course_progress_start_practice: "Объяснение просмотрено. Начать практику",
    course_progress_resume_practice: "Продолжить с вопроса {{number}}",
    course_progress_completed: "Курс завершен",
    course_progress_all_done: "Все уроки завершены",
    course_untitled_lesson: "Урок без названия",
    course_lesson_completed: "Завершено",
    course_lesson_current: "Текущий урок",
    course_lesson_not_started: "Не начато",
  },
  id: {
    course_progress_label: "Progres kursus",
    course_progress_completed_count: "{{completed}} / {{total}} pelajaran selesai",
    course_progress_next_lesson: "Pelajaran berikutnya",
    course_progress_start_practice: "Materi sudah dilihat. Mulai latihan",
    course_progress_resume_practice: "Lanjutkan pertanyaan {{number}}",
    course_progress_completed: "Kursus selesai",
    course_progress_all_done: "Semua pelajaran selesai",
    course_untitled_lesson: "Pelajaran tanpa judul",
    course_lesson_completed: "Selesai",
    course_lesson_current: "Saat ini",
    course_lesson_not_started: "Belum mulai",
  },
  ms: {
    course_progress_label: "Kemajuan kursus",
    course_progress_completed_count: "{{completed}} / {{total}} pelajaran selesai",
    course_progress_next_lesson: "Pelajaran seterusnya",
    course_progress_start_practice: "Penerangan telah dilihat. Mula latihan",
    course_progress_resume_practice: "Sambung soalan {{number}}",
    course_progress_completed: "Kursus selesai",
    course_progress_all_done: "Semua pelajaran selesai",
    course_untitled_lesson: "Pelajaran tanpa tajuk",
    course_lesson_completed: "Selesai",
    course_lesson_current: "Semasa",
    course_lesson_not_started: "Belum mula",
  },
  it: {
    course_progress_label: "Avanzamento corso",
    course_progress_completed_count: "{{completed}} / {{total}} lezioni completate",
    course_progress_next_lesson: "Prossima lezione",
    course_progress_start_practice: "Lezione vista. Inizia la pratica",
    course_progress_resume_practice: "Riprendi dalla domanda {{number}}",
    course_progress_completed: "Corso completato",
    course_progress_all_done: "Tutte le lezioni completate",
    course_untitled_lesson: "Lezione senza titolo",
    course_lesson_completed: "Completata",
    course_lesson_current: "Attuale",
    course_lesson_not_started: "Non iniziata",
  },
};

Object.entries(COURSE_PROGRESS_TRANSLATIONS).forEach(([locale, overrides]) => {
  if (!resources[locale]) return;
  resources[locale].translation = {
    ...resources[locale].translation,
    ...overrides,
  };
});

Object.keys(resources).forEach((locale) => {
  resources[locale].translation.hanzi_intro = HANZI_INTRO_TRANSLATIONS[locale] || HANZI_INTRO_TRANSLATIONS.en;
});
resources.ja = resources.jp;

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: localStorage.getItem('chilan_interface_language') || "zh",
    fallbackLng: "en",
    interpolation: { escapeValue: false }
  });

i18n.on('languageChanged', (lng) => {
  localStorage.setItem('chilan_interface_language', lng);
});

export default i18n;
