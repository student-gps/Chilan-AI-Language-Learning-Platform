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
        promptLabel: '句型替换',
        badgeLabel: 'Pattern Drill',
        promptMode: 'pattern',
        answerMode: 'text',
        answerLanguage: 'en',
        ttsLanguage: 'zh',
        replayPrompt: false,
        showKnowledgeCard: false,
        theme: THEMES.amber,
    },
    SUPPORT_TO_TARGET: {
        promptLabel: '句型替换',
        badgeLabel: 'Pattern Drill',
        promptMode: 'pattern',
        answerMode: 'text',
        answerLanguage: 'en',
        ttsLanguage: 'zh',
        replayPrompt: false,
        showKnowledgeCard: false,
        theme: THEMES.amber,
    },
    TARGET_TO_SUPPORT: {
        promptLabel: '理解英文',
        badgeLabel: 'English → 中文',
        promptMode: 'text',
        answerMode: 'text',
        answerLanguage: 'zh',
        ttsLanguage: 'en',
        replayPrompt: true,
        showKnowledgeCard: false,
        theme: THEMES.emerald,
    },
    TARGET_LISTEN_WRITE: {
        promptLabel: '听写英文',
        badgeLabel: 'English Dictation',
        promptMode: 'listen_write',
        answerMode: 'text',
        answerLanguage: 'en',
        audioLanguage: 'en',
        showKnowledgeCard: false,
        theme: THEMES.indigo,
    },
    TARGET_SPEAK: {
        promptLabel: '开口说英语',
        badgeLabel: 'Speak English',
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
    const base = CONFIGS[type] || FALLBACK_CONFIG;
    const metadata = question?.metadata || {};
    return {
        ...base,
        speechLanguage: metadata.speech_language || base.speechLanguage || base.answerLanguage || 'zh',
        audioLanguage: metadata.audio_language || base.audioLanguage || base.ttsLanguage || 'zh',
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
