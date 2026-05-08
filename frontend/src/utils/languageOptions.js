export const UI_LANGUAGE_OPTIONS = [
    { code: 'zh', name: '简体中文', nativeName: '简体中文', flag: '🇨🇳' },
    { code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
    { code: 'jp', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' },
    { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
    { code: 'de', name: 'German', nativeName: 'Deutsch', flag: '🇩🇪' },
    { code: 'ko', name: 'Korean', nativeName: '한국어', flag: '🇰🇷' },
    { code: 'es', name: 'Spanish', nativeName: 'Español', flag: '🇪🇸' },
    { code: 'vi', name: 'Vietnamese', nativeName: 'Tiếng Việt', flag: '🇻🇳' },
    { code: 'pt', name: 'Portuguese', nativeName: 'Português', flag: '🇵🇹' },
    { code: 'ar', name: 'Arabic', nativeName: 'العربية', flag: '🇸🇦' },
    { code: 'th', name: 'Thai', nativeName: 'ไทย', flag: '🇹🇭' },
    { code: 'ru', name: 'Russian', nativeName: 'Русский', flag: '🇷🇺' },
    { code: 'id', name: 'Indonesian', nativeName: 'Bahasa Indonesia', flag: '🇮🇩' },
    { code: 'ms', name: 'Malay', nativeName: 'Bahasa Melayu', flag: '🇲🇾' },
    { code: 'it', name: 'Italian', nativeName: 'Italiano', flag: '🇮🇹' },
];

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

export const getUiLanguageOption = (language) => {
    const normalized = (language || 'zh').split('-')[0].toLowerCase();
    const appCode = normalized === 'ja' ? 'jp' : normalized;
    return UI_LANGUAGE_OPTIONS.find((item) => item.code === appCode) || UI_LANGUAGE_OPTIONS[0];
};
