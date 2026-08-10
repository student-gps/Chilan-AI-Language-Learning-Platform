const UI_LANGUAGE_DEFINITIONS = [
    {
        locale: 'zh-Hans',
        nativeName: '简体中文',
        flag: '🇨🇳',
        searchAliases: ['zh', 'cn', 'zh-cn', 'zh-hans-cn'],
    },
    {
        locale: 'en',
        nativeName: 'English',
        flag: '🇺🇸',
        searchAliases: ['eng', 'en-us', 'en-gb'],
    },
    {
        locale: 'ja',
        nativeName: '日本語',
        flag: '🇯🇵',
        searchAliases: ['jp', 'ja-jp'],
    },
    {
        locale: 'fr',
        nativeName: 'Français',
        flag: '🇫🇷',
        searchAliases: ['fr-fr'],
    },
    {
        locale: 'de',
        nativeName: 'Deutsch',
        flag: '🇩🇪',
        searchAliases: ['de-de'],
    },
    {
        locale: 'ko',
        nativeName: '한국어',
        flag: '🇰🇷',
        searchAliases: ['ko-kr', 'kr'],
    },
    {
        locale: 'es',
        nativeName: 'Español',
        flag: '🇪🇸',
        searchAliases: ['es-es'],
    },
    {
        locale: 'vi',
        nativeName: 'Tiếng Việt',
        flag: '🇻🇳',
        searchAliases: ['vi-vn', 'vn'],
    },
    {
        locale: 'pt',
        nativeName: 'Português',
        flag: '🇵🇹',
        searchAliases: ['pt-pt', 'pt-br'],
    },
    {
        locale: 'ar',
        nativeName: 'العربية',
        flag: '🇸🇦',
        searchAliases: ['ar-sa'],
    },
    {
        locale: 'th',
        nativeName: 'ไทย',
        flag: '🇹🇭',
        searchAliases: ['th-th'],
    },
    {
        locale: 'ru',
        nativeName: 'Русский',
        flag: '🇷🇺',
        searchAliases: ['ru-ru'],
    },
    {
        locale: 'id',
        nativeName: 'Bahasa Indonesia',
        flag: '🇮🇩',
        searchAliases: ['id-id'],
    },
    {
        locale: 'ms',
        nativeName: 'Bahasa Melayu',
        flag: '🇲🇾',
        searchAliases: ['ms-my'],
    },
    {
        locale: 'it',
        nativeName: 'Italiano',
        flag: '🇮🇹',
        searchAliases: ['it-it'],
    },
];

const DEFAULT_UI_LOCALE = 'zh-Hans';
const LEGACY_UI_LOCALE_ALIASES = {
    zh: 'zh-Hans',
    'zh-cn': 'zh-Hans',
    'zh-hans-cn': 'zh-Hans',
    cn: 'zh-Hans',
    jp: 'ja',
};

const normalizeLocaleInput = (value) => String(value || '')
    .trim()
    .replace(/_/g, '-')
    .toLowerCase();

const getLocaleCandidates = (value) => {
    const normalized = normalizeLocaleInput(value);
    if (!normalized) return [];

    const aliased = LEGACY_UI_LOCALE_ALIASES[normalized] || normalized;
    return [aliased, aliased.split('-')[0]];
};

const resolveSupportedLocale = (value) => {
    const candidates = getLocaleCandidates(value);
    if (!candidates.length) return null;

    return UI_LANGUAGE_DEFINITIONS.find((item) => candidates.some((candidate) => (
        item.locale.toLowerCase() === candidate
        || item.searchAliases.includes(candidate)
    )))?.locale || null;
};

export const normalizeUiLocale = (value) => resolveSupportedLocale(value) || DEFAULT_UI_LOCALE;

export const UI_LANGUAGE_OPTIONS = UI_LANGUAGE_DEFINITIONS.map((item) => ({ ...item }));

export const UI_SUPPORTED_LOCALES = UI_LANGUAGE_OPTIONS.map((item) => item.locale);

export const getUiLanguageOption = (language) => {
    const locale = normalizeUiLocale(language);
    return UI_LANGUAGE_OPTIONS.find((item) => item.locale === locale) || UI_LANGUAGE_OPTIONS[0];
};

export const getUiLanguageDisplayName = (language, displayLocale = DEFAULT_UI_LOCALE) => {
    const option = getUiLanguageOption(language);

    try {
        return new Intl.DisplayNames([normalizeUiLocale(displayLocale)], {
            type: 'language',
            languageDisplay: 'standard',
        }).of(option.locale) || option.nativeName;
    } catch {
        return option.nativeName;
    }
};

export const getUiLanguageSearchTerms = (language, displayLocale = DEFAULT_UI_LOCALE) => {
    const option = getUiLanguageOption(language);
    const languageCode = option.locale.split('-')[0];

    return [...new Set([
        option.locale,
        languageCode,
        option.nativeName,
        getUiLanguageDisplayName(option.locale, displayLocale),
        ...option.searchAliases,
    ])];
};

export const getUiLanguageSelectOptions = (displayLocale = DEFAULT_UI_LOCALE) => UI_LANGUAGE_OPTIONS.map((item) => ({
    value: item.locale,
    label: `${item.flag} ${item.nativeName} · ${getUiLanguageDisplayName(item.locale, displayLocale)}`,
}));

export const COURSE_LANGUAGE_OPTIONS = [
    { value: 'zh', label: '中文' },
    { value: 'en', label: 'English' },
    { value: 'jp', label: '日本語' },
    { value: 'fr', label: 'Français' },
    { value: 'de', label: 'Deutsch' },
    { value: 'ko', label: '한국어' },
    { value: 'es', label: 'Español' },
    { value: 'vi', label: 'Tiếng Việt' },
    { value: 'pt', label: 'Português' },
    { value: 'ar', label: 'العربية' },
    { value: 'th', label: 'ไทย' },
    { value: 'ru', label: 'Русский' },
    { value: 'id', label: 'Bahasa Indonesia' },
    { value: 'ms', label: 'Bahasa Melayu' },
    { value: 'it', label: 'Italiano' },
];
