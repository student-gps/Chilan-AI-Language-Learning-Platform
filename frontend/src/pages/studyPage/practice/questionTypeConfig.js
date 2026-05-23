import i18n from '../../../i18n';

// Short abbreviations for badge display (e.g. "翻译 · 中→日")
const LANG_ABBREV = {
    CN: { zh: '中', jp: '中', default: 'ZH' },
    EN: { zh: '英', jp: '英', default: 'EN' },
    JA: { zh: '日', jp: '日', default: 'JA' },
    FR: { zh: '法', jp: '仏', default: 'FR' },
    DE: { zh: '德', jp: '独', default: 'DE' },
    KO: { zh: '韩', jp: '韓', default: 'KO' },
    RU: { zh: '俄', jp: '露', default: 'RU' },
    ES: { zh: '西', jp: '西', default: 'ES' },
    PT: { zh: '葡', jp: '葡', default: 'PT' },
    VI: { zh: '越', jp: '越', default: 'VI' },
    TH: { zh: '泰', jp: '泰', default: 'TH' },
    AR: { zh: '阿', jp: 'ア', default: 'AR' },
    IT: { zh: '意', jp: '伊', default: 'IT' },
    ID: { zh: '印', jp: 'イ', default: 'ID' },
    MS: { zh: '马', jp: 'マ', default: 'MS' },
};

// Full language names for prompt label (e.g. "翻译成日文")
const LANG_NAME = {
    CN: { zh: '中文', jp: '中国語', fr: 'chinois', de: 'Chinesisch', en: 'Chinese' },
    EN: { zh: '英文', jp: '英語', fr: 'anglais', de: 'Englisch', en: 'English' },
    JA: { zh: '日文', jp: '日本語', fr: 'japonais', de: 'Japanisch', en: 'Japanese' },
    FR: { zh: '法文', jp: 'フランス語', fr: 'français', de: 'Französisch', en: 'French' },
    DE: { zh: '德文', jp: 'ドイツ語', fr: 'allemand', de: 'Deutsch', en: 'German' },
    KO: { zh: '韩文', jp: '韓国語', fr: 'coréen', de: 'Koreanisch', en: 'Korean' },
    RU: { zh: '俄文', jp: 'ロシア語', fr: 'russe', de: 'Russisch', en: 'Russian' },
    ES: { zh: '西班牙文', jp: 'スペイン語', fr: 'espagnol', de: 'Spanisch', en: 'Spanish' },
    PT: { zh: '葡萄牙文', jp: 'ポルトガル語', fr: 'portugais', de: 'Portugiesisch', en: 'Portuguese' },
    VI: { zh: '越南文', jp: 'ベトナム語', fr: 'vietnamien', de: 'Vietnamesisch', en: 'Vietnamese' },
    TH: { zh: '泰文', jp: 'タイ語', fr: 'thaïlandais', de: 'Thaïlandais', en: 'Thai' },
    AR: { zh: '阿拉伯文', jp: 'アラビア語', fr: 'arabe', de: 'Arabisch', en: 'Arabic' },
    IT: { zh: '意大利文', jp: 'イタリア語', fr: 'italien', de: 'Italienisch', en: 'Italian' },
    ID: { zh: '印尼文', jp: 'インドネシア語', fr: 'indonésien', de: 'Indonesisch', en: 'Indonesian' },
    MS: { zh: '马来文', jp: 'マレー語', fr: 'malais', de: 'Malaiisch', en: 'Malay' },
};

const TRANSLATE_VERB = { zh: '翻译', en: 'Translate', jp: '翻訳', fr: 'Traduire', de: 'Übersetzen' };
const SPEAK_VERB = { zh: '口语', en: 'Speak', jp: 'スピーキング', fr: 'Expression orale', de: 'Sprechen' };
const DICTATION_VERB = { zh: '听写', en: 'Dictation', jp: 'ディクテーション', fr: 'Dictée', de: 'Diktat' };
const TRANSLATE_INTO_FN = {
    zh: (tgt) => `翻译成${LANG_NAME[tgt]?.zh || tgt}`,
    en: (tgt) => `Translate into ${LANG_NAME[tgt]?.en || tgt}`,
    jp: (tgt) => `${LANG_NAME[tgt]?.jp || tgt}に翻訳してください`,
    fr: (tgt) => `Traduire en ${LANG_NAME[tgt]?.fr || tgt}`,
    de: (tgt) => `Ins ${LANG_NAME[tgt]?.de || tgt}ische übersetzen`,
};
const SPEAK_INTO_FN = {
    zh: (tgt) => `说出${LANG_NAME[tgt]?.zh || tgt}`,
    en: (tgt) => `Speak ${LANG_NAME[tgt]?.en || tgt}`,
    jp: (tgt) => `${LANG_NAME[tgt]?.jp || tgt}で話してください`,
    fr: (tgt) => `Parler en ${LANG_NAME[tgt]?.fr || tgt}`,
    de: (tgt) => `${LANG_NAME[tgt]?.de || tgt} sprechen`,
};
const DICTATION_INTO_FN = {
    zh: (tgt) => `${LANG_NAME[tgt]?.zh || tgt}听写`,
    en: (tgt) => `${LANG_NAME[tgt]?.en || tgt} dictation`,
    jp: (tgt) => `${LANG_NAME[tgt]?.jp || tgt}ディクテーション`,
    fr: (tgt) => `Dictée en ${LANG_NAME[tgt]?.fr || tgt}`,
    de: (tgt) => `${LANG_NAME[tgt]?.de || tgt}-Diktat`,
};

const _uiLang = () => (i18n.language || 'en').split('-')[0].toLowerCase();
const _abbrev = (code, lang) => { const e = LANG_ABBREV[code?.toUpperCase()] || {}; return e[lang] || e.default || code?.toUpperCase() || '?'; };
const _buildTranslateBadge = (src, tgt) => { const l = _uiLang(); return `${TRANSLATE_VERB[l] || TRANSLATE_VERB.en} · ${_abbrev(src, l)}→${_abbrev(tgt, l)}`; };
const _buildSpeakBadge = (tgt) => { const l = _uiLang(); return `${SPEAK_VERB[l] || SPEAK_VERB.en} · ${LANG_NAME[tgt?.toUpperCase()]?.[l] || tgt}`; };
const _buildDictationBadge = (tgt) => { const l = _uiLang(); return `${DICTATION_VERB[l] || DICTATION_VERB.en} · ${LANG_NAME[tgt?.toUpperCase()]?.[l] || tgt}`; };
const _buildPromptLabel = (tgt) => { const l = _uiLang(); return (TRANSLATE_INTO_FN[l] || TRANSLATE_INTO_FN.en)(tgt?.toUpperCase()); };
const _buildSpeakPromptLabel = (tgt) => { const l = _uiLang(); return (SPEAK_INTO_FN[l] || SPEAK_INTO_FN.en)(tgt?.toUpperCase()); };
const _buildDictationPromptLabel = (tgt) => { const l = _uiLang(); return (DICTATION_INTO_FN[l] || DICTATION_INTO_FN.en)(tgt?.toUpperCase()); };

const THEMES = {
    blue: {
        sparkle: 'text-blue-500',
        card: 'bg-blue-50/40 border-blue-100 shadow-blue-100/30',
        btn: 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-100',
        badgeBg: 'bg-blue-100',
        badgeText: 'text-blue-700',
    },
    emerald: {
        sparkle: 'text-emerald-500',
        card: 'bg-emerald-50/40 border-emerald-100 shadow-emerald-100/30',
        btn: 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-emerald-100',
        badgeBg: 'bg-emerald-100',
        badgeText: 'text-emerald-700',
    },
    rose: {
        sparkle: 'text-rose-500',
        card: 'bg-rose-50/40 border-rose-100 shadow-rose-100/30',
        btn: 'bg-rose-600 text-white hover:bg-rose-700 shadow-rose-100',
        badgeBg: 'bg-rose-100',
        badgeText: 'text-rose-700',
    },
    indigo: {
        sparkle: 'text-indigo-500',
        card: 'bg-indigo-50/60 border-indigo-100 shadow-indigo-100/40',
        btn: 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-indigo-100',
        badgeBg: 'bg-indigo-100',
        badgeText: 'text-indigo-700',
        btnActive: 'bg-indigo-700 shadow-indigo-300 scale-105',
        btnIdle: 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-200',
        ping: 'bg-indigo-400',
    },
    amber: {
        sparkle: 'text-amber-500',
        card: 'bg-amber-50/50 border-amber-100 shadow-amber-100/30',
        btn: 'bg-amber-600 text-white hover:bg-amber-700 shadow-amber-100',
        badgeBg: 'bg-amber-100',
        badgeText: 'text-amber-800',
    },
    teal: {
        sparkle: 'text-teal-500',
        card: 'bg-teal-50/50 border-teal-100 shadow-teal-100/30',
        btn: 'bg-teal-600 text-white hover:bg-teal-700 shadow-teal-100',
        badgeBg: 'bg-teal-100',
        badgeText: 'text-teal-800',
    },
};

const CONFIGS = {
    CN_TO_EN: {
        promptLabelKey: 'practice_prompt_cn_to_en',
        badgeKey: 'practice_badge_cn_to_en',
        promptMode: 'text',
        answerMode: 'text',
        answerLanguage: 'en',
        ttsLanguage: 'zh',
        autoPlayPrompt: true,
        replayPrompt: true,
        showKnowledgeCard: true,
        theme: THEMES.blue,
    },
    EN_TO_CN: {
        promptLabelKey: 'practice_prompt_en_to_cn',
        badgeKey: 'practice_badge_en_to_cn',
        promptMode: 'text',
        answerMode: 'text',
        answerLanguage: 'zh',
        ttsLanguage: 'en',
        replayPrompt: false,
        showKnowledgeCard: true,
        theme: THEMES.emerald,
    },
    EN_TO_CN_SPEAK: {
        promptLabelKey: 'practice_prompt_en_to_cn',
        badgeKey: 'practice_badge_speak',
        promptMode: 'text',
        answerMode: 'speech',
        answerLanguage: 'zh',
        speechLanguage: 'zh',
        ttsLanguage: 'en',
        replayPrompt: false,
        showKnowledgeCard: true,
        theme: THEMES.rose,
    },
    CN_LISTEN_WRITE: {
        promptLabelKey: 'practice_prompt_cn_listen_write',
        badgeKey: 'practice_badge_dictation',
        promptMode: 'listen_write',
        answerMode: 'text',
        answerLanguage: 'zh',
        audioLanguage: 'zh',
        showKnowledgeCard: true,
        theme: THEMES.indigo,
    },
    PATTERN_DRILL: {
        promptLabelKey: 'practice_prompt_pattern_replace',
        badgeKey: 'practice_badge_pattern_drill',
        promptMode: 'pattern',
        answerMode: 'text',
        answerLanguage: 'en',
        ttsLanguage: 'zh',
        replayPrompt: false,
        showKnowledgeCard: false,
        theme: THEMES.amber,
    },
    SUPPORT_TO_TARGET: {
        promptLabelKey: 'practice_prompt_pattern_replace',
        badgeKey: 'practice_badge_pattern_drill',
        promptMode: 'pattern',
        answerMode: 'text',
        answerLanguage: 'en',
        ttsLanguage: 'zh',
        replayPrompt: false,
        showKnowledgeCard: false,
        theme: THEMES.amber,
    },
    TARGET_TO_SUPPORT: {
        promptLabelKey: 'practice_prompt_understand_english',
        badgeKey: 'practice_badge_en_to_cn',
        promptMode: 'text',
        answerMode: 'text',
        answerLanguage: 'zh',
        ttsLanguage: 'en',
        replayPrompt: true,
        showKnowledgeCard: false,
        theme: THEMES.emerald,
    },
    TARGET_LISTEN_WRITE: {
        promptLabelKey: 'practice_prompt_en_listen_write',
        badgeKey: 'practice_badge_english_dictation',
        promptMode: 'listen_write',
        answerMode: 'text',
        answerLanguage: 'en',
        audioLanguage: 'en',
        showKnowledgeCard: false,
        theme: THEMES.indigo,
    },
    TARGET_SPEAK: {
        promptLabelKey: 'practice_prompt_speak_english',
        badgeKey: 'practice_badge_speak_english',
        promptMode: 'text',
        answerMode: 'speech',
        answerLanguage: 'en',
        speechLanguage: 'en',
        ttsLanguage: 'zh',
        replayPrompt: false,
        showKnowledgeCard: false,
        theme: THEMES.teal,
    },
};

const FALLBACK_CONFIG = {
    promptLabelKey: 'practice_prompt_cn_to_en',
    badgeKey: 'practice_badge_cn_to_en',
    promptMode: 'text',
    answerMode: 'text',
    answerLanguage: 'en',
    ttsLanguage: 'zh',
    showKnowledgeCard: false,
    theme: THEMES.blue,
};

export const getQuestionTypeConfig = (question) => {
    const type = question?.question_type;
    const metadata = question?.metadata || {};

    const exact = CONFIGS[type];
    if (exact) {
        return {
            ...exact,
            speechLanguage: metadata.speech_language || exact.speechLanguage || exact.answerLanguage || 'zh',
            audioLanguage: metadata.audio_language || exact.audioLanguage || exact.ttsLanguage || 'zh',
        };
    }

    // Dynamic resolution for localized variants: CN_TO_JA, FR_TO_CN, JA_TO_CN_SPEAK, etc.
    let m;
    if ((m = type?.match(/^CN_TO_(\w+)$/))) {
        const tgt = m[1];
        return {
            ...CONFIGS.CN_TO_EN,
            badgeLabel: _buildTranslateBadge('CN', tgt),
            badgeKey: null,
            promptLabel: _buildPromptLabel(tgt),
            promptLabelKey: null,
            answerLanguage: tgt.toLowerCase(),
            speechLanguage: metadata.speech_language || tgt.toLowerCase(),
            audioLanguage: metadata.audio_language || 'zh',
        };
    }
    if ((m = type?.match(/^(\w+)_TO_CN_SPEAK$/))) {
        return {
            ...CONFIGS.EN_TO_CN_SPEAK,
            badgeLabel: _buildSpeakBadge('CN'),
            badgeKey: null,
            speechLanguage: metadata.speech_language || CONFIGS.EN_TO_CN_SPEAK.speechLanguage || 'zh',
            audioLanguage: metadata.audio_language || m[1].toLowerCase(),
        };
    }
    if ((m = type?.match(/^(\w+)_TO_CN$/))) {
        const src = m[1];
        const srcLang = src.toLowerCase();
        return {
            ...CONFIGS.EN_TO_CN,
            badgeLabel: _buildTranslateBadge(src, 'CN'),
            badgeKey: null,
            promptLabel: _buildPromptLabel('CN'),
            promptLabelKey: null,
            ttsLanguage: srcLang,
            speechLanguage: metadata.speech_language || 'zh',
            audioLanguage: metadata.audio_language || srcLang,
        };
    }
    if ((m = type?.match(/^(\w+)_LISTEN_WRITE$/))) {
        const tgt = m[1];
        const tgtLang = tgt.toLowerCase();
        return {
            ...CONFIGS.TARGET_LISTEN_WRITE,
            badgeLabel: _buildDictationBadge(tgt),
            badgeKey: null,
            promptLabel: _buildDictationPromptLabel(tgt),
            promptLabelKey: null,
            answerLanguage: tgtLang,
            audioLanguage: metadata.audio_language || tgtLang,
            ttsLanguage: metadata.audio_language || tgtLang,
            showKnowledgeCard: false,
        };
    }
    if ((m = type?.match(/^(\w+)_SPEAK$/))) {
        const tgt = m[1];
        const tgtLang = tgt.toLowerCase();
        return {
            ...CONFIGS.TARGET_SPEAK,
            badgeLabel: _buildSpeakBadge(tgt),
            badgeKey: null,
            promptLabel: _buildSpeakPromptLabel(tgt),
            promptLabelKey: null,
            answerLanguage: tgtLang,
            speechLanguage: metadata.speech_language || tgtLang,
            ttsLanguage: metadata.tts_language || 'zh',
            audioLanguage: metadata.audio_language || 'zh',
            showKnowledgeCard: false,
        };
    }

    const base = FALLBACK_CONFIG;
    return {
        ...base,
        speechLanguage: metadata.speech_language || base.answerLanguage || 'zh',
        audioLanguage: metadata.audio_language || base.ttsLanguage || 'zh',
    };
};

export const isListenWriteQuestion = (question) =>
    getQuestionTypeConfig(question).promptMode === 'listen_write';

export const isSpeechQuestion = (question) =>
    getQuestionTypeConfig(question).answerMode === 'speech' ||
    question?.metadata?.answer_mode === 'speech';

export const getQuestionContext = (question) => {
    const metadata = question?.metadata || {};
    return metadata.context || metadata || {};
};
