export const JAPANESE_FOUNDATION_LANGUAGE_CODES = Object.freeze([
    'zh',
    'en',
    'ja',
    'fr',
    'de',
    'ko',
    'es',
    'vi',
    'pt',
    'ar',
    'th',
    'ru',
    'id',
    'ms',
    'it',
]);

const JAPANESE_FOUNDATION_LANGUAGE_ALIASES = Object.freeze({
    cn: 'zh',
    jp: 'ja',
    kr: 'ko',
    'zh-cn': 'zh',
    'zh-hans': 'zh',
    'zh-hans-cn': 'zh',
});

export function normalizeJapaneseFoundationLanguage(value) {
    const normalized = String(value || '')
        .trim()
        .replace(/_/g, '-')
        .toLowerCase();
    const aliased = JAPANESE_FOUNDATION_LANGUAGE_ALIASES[normalized] || normalized;
    const base = JAPANESE_FOUNDATION_LANGUAGE_ALIASES[aliased.split('-')[0]] || aliased.split('-')[0];
    return JAPANESE_FOUNDATION_LANGUAGE_CODES.includes(base) ? base : 'en';
}
