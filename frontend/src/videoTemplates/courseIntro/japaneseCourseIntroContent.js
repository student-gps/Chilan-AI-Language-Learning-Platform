import { chalk } from '../explanation/templateUtils.js';
import { JAPANESE_COURSE_INTRO_TRANSLATIONS } from '../../japaneseFoundationTranslations.generated.js';

export const JAPANESE_COURSE_INTRO_SLIDES = [
    { id: 'welcome', duration: 14000 },
    { id: 'sounds', duration: 15000 },
    { id: 'skills', duration: 14000 },
    { id: 'ai', duration: 16000 },
    { id: 'fsrs', duration: 14000 },
    { id: 'start', duration: 14000 },
];

export const JAPANESE_COURSE_INTRO_COPY = {
    zh: {
        common: {
            course: 'CHILAN · 日语',
            day: '天',
            month: '月',
            ariaLabel: '日语课程介绍幻灯片',
            previousSlide: '上一页',
            nextSlide: '下一页',
            playNarration: '播放旁白',
            pauseNarration: '暂停旁白',
        },
        welcome: {
            pill: '从真实沟通出发',
            title: '学习日语',
            accent: '像真实使用那样去学',
            subtitle: '听懂、开口、读懂三套文字，并用日语输入法表达。',
            narration: '欢迎来到 Chilan 日语课程。这是一套由人工智能辅助的系统课程，目标不是只记住课文，而是逐步建立真实的听力、口语、阅读和输入能力。',
        },
        sounds: {
            label: '文字与声音',
            title: '三套文字，',
            accent: '共用一套声音系统',
            subtitle: '平假名、片假名和汉字各有分工；所有读音都落在清晰的拍节奏中。',
            cards: [
                ['あ', '平假名', '语法、词尾和常用词', chalk.pink],
                ['ア', '片假名', '外来语、名称和强调', chalk.blue],
                ['漢', '汉字', '词义、词干和信息压缩', chalk.yellow],
            ],
            example: 'きょう ＝ きょ・う ＝ 2 拍　　きって ＝ き・っ・て ＝ 3 拍',
            narration: '日语同时使用平假名、片假名和汉字。它们不是三套发音，而是三种分工不同的写法。学习声音时要以拍为单位，长音、促音和拨音都要占据准确的时间。',
        },
        skills: {
            label: '核心能力',
            title: '每一课都在训练',
            accent: '真实输出',
            cards: [
                ['👂', '听懂', '先听完整表达，再用假名和翻译核对。', chalk.green],
                ['🎤', '开口', '按拍跟读整句，练习停顿、长短音和语气。', chalk.blue],
                ['読', '阅读与输入', '在词语中识读汉字，并用输入法完成表达。', chalk.yellow],
            ],
            note: '罗马字只用于理解键盘规则，阅读时会尽早过渡到假名。',
            narration: '课程持续训练三组核心能力。先通过原声建立听力，再按拍模仿整句并开口表达，同时在词语中学习假名和汉字，最后使用日语输入法完成书面输出。',
        },
        ai: {
            label: '人工智能反馈',
            title: '理解你的意思，',
            accent: '也指出真正的问题',
            subtitle: '等义表达可以通过；助词、活用和用词问题会得到具体说明。',
            exampleLabel: '同一意思，不同表达',
            answers: ['毎朝コーヒーを飲みます。', '朝はいつもコーヒーを飲んでいます。'],
            exampleNote: '语境一致时均可接受，并继续检查自然度',
            tiers: [
                ['1', '快速匹配', '明确答案即时判断', chalk.blue],
                ['2', '语义比较', '识别不同措辞的同义表达', chalk.green],
                ['3', 'AI 分析', '解释助词、活用与自然度', chalk.pink],
            ],
            narration: '你提交的答案会经过三层评估。快速匹配处理明确情况，语义比较识别不同措辞表达的相同意思，大语言模型则分析助词、词形变化和表达自然度，并给出具体反馈。',
        },
        fsrs: {
            label: '记忆科学', title: '该复习的时候，', accent: '它会回来',
            subtitle: 'FSRS 根据每次作答更新记忆状态，而不是让所有内容机械重复。',
            chartLabel: '一个词语的复习间隔示例', legends: ['早期密集巩固', '间隔逐步增加', '进入长期记忆'],
            narration: '复习计划由 FSRS 间隔重复算法管理。掌握稳定的内容会逐渐延长复习间隔，容易混淆的假名、读音或句型会更快回来，让时间集中在真正薄弱的地方。',
        },
        start: {
            label: '你的学习路径', title: '基础打稳，', accent: '再进入课文',
            subtitle: '四个入门模块解决日语课文开始前最常见的障碍。',
            steps: [['假名', '字符与声音', chalk.blue], ['发音', '拍与特殊音', '#a78bfa'], ['汉字', '读音与语境', chalk.yellow], ['输入', '假名转汉字', chalk.green]],
            note: '完成导览后，从假名模块开始；语法会在每一课的真实语境中展开。',
            narration: '现在可以开始了。先掌握假名，再理解日语的拍节奏，然后学习汉字在具体词语中的读音，最后熟悉日语输入法。语法和表达会在后续每一课的真实语境中逐步建立。',
        },
    },
    en: {
        common: {
            course: 'CHILAN · Japanese',
            day: 'd',
            month: 'mo',
            ariaLabel: 'Japanese course introduction slides',
            previousSlide: 'Previous slide',
            nextSlide: 'Next slide',
            playNarration: 'Play narration',
            pauseNarration: 'Pause narration',
        },
        welcome: {
            pill: 'Built for real communication', title: 'Learn Japanese', accent: 'the way it is actually used', subtitle: 'Listen, speak, read three scripts, and express yourself with a Japanese IME.',
            narration: 'Welcome to Chilan Japanese. This AI-assisted course goes beyond memorizing a textbook. It progressively builds practical listening, speaking, reading, and digital writing skills.',
        },
        sounds: {
            label: 'Writing and sound', title: 'Three scripts,', accent: 'one sound system', subtitle: 'Hiragana, katakana, and kanji have different jobs; every reading fits a clear mora rhythm.',
            cards: [['あ', 'Hiragana', 'Grammar, endings, and common words', chalk.pink], ['ア', 'Katakana', 'Loanwords, names, and emphasis', chalk.blue], ['漢', 'Kanji', 'Meaning, word stems, and compact information', chalk.yellow]],
            example: 'きょう = きょ・う = 2 morae　　きって = き・っ・て = 3 morae',
            narration: 'Japanese uses hiragana, katakana, and kanji together. These are not three pronunciation systems, but three writing systems with different roles. Sound is organized in morae, and length, small tsu, and moraic n all occupy precise timing.',
        },
        skills: {
            label: 'Core abilities', title: 'Every lesson trains', accent: 'real output',
            cards: [['👂', 'Listen', 'Hear the full expression before checking kana and meaning.', chalk.green], ['🎤', 'Speak', 'Shadow whole sentences with clear morae, length, and pauses.', chalk.blue], ['読', 'Read and type', 'Learn kanji in words and produce text with an IME.', chalk.yellow]],
            note: 'Romaji explains keyboard rules; reading moves to kana as early as possible.',
            narration: 'The course develops three connected abilities. Native audio builds listening, mora-timed shadowing builds speech, and word-based kana and kanji study leads into practical digital writing with a Japanese input method.',
        },
        ai: {
            label: 'AI feedback', title: 'It understands your meaning', accent: 'and identifies the real issue', subtitle: 'Equivalent answers can pass while particles, inflection, and natural wording receive precise feedback.',
            exampleLabel: 'Same meaning, different wording', answers: ['毎朝コーヒーを飲みます。', '朝はいつもコーヒーを飲んでいます。'], exampleNote: 'Both can be accepted in the same context, with naturalness still checked.',
            tiers: [['1', 'Fast match', 'Immediate clear-case judgment', chalk.blue], ['2', 'Semantic check', 'Recognizes equivalent wording', chalk.green], ['3', 'AI analysis', 'Explains particles, inflection, and naturalness', chalk.pink]],
            narration: 'Each answer passes through three evaluation layers. Fast matching handles clear cases, semantic comparison recognizes equivalent wording, and a language model analyzes particles, inflection, and naturalness with concrete feedback.',
        },
        fsrs: {
            label: 'Memory science', title: 'It comes back', accent: 'when review helps', subtitle: 'FSRS updates memory state after every answer instead of repeating everything mechanically.', chartLabel: 'Example review spacing for one word', legends: ['Dense early practice', 'Growing intervals', 'Long-term retention'],
            narration: 'FSRS schedules every review. Stable items gradually move farther apart, while uncertain kana, readings, and patterns return sooner. This keeps study time focused on the weakest points.',
        },
        start: {
            label: 'Your path', title: 'Build the foundation,', accent: 'then enter the lessons', subtitle: 'Four short modules remove the most common obstacles before the first text.',
            steps: [['Kana', 'Characters and sounds', chalk.blue], ['Sound', 'Morae and contrasts', '#a78bfa'], ['Kanji', 'Readings in context', chalk.yellow], ['Typing', 'Kana-to-kanji', chalk.green]],
            note: 'Start with Kana after this guide; grammar unfolds inside real lesson contexts.',
            narration: 'You are ready to begin. Learn kana first, then Japanese mora timing, kanji readings inside real words, and finally Japanese input. Grammar and expression will grow through the context of each lesson.',
        },
    },
    ...JAPANESE_COURSE_INTRO_TRANSLATIONS,
};
