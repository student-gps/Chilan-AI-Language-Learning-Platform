const CJK    = /[一-鿿㐀-䶿]/;
const KANA   = /[぀-ゟ゠-ヿ]/;
const HANGUL = /[가-힯]/;
const ARABIC = /[؀-ۿ]/;
const CYRIL  = /[Ѐ-ӿ]/;
const THAI   = /[฀-๿]/;
const NON_LATIN = /[一-鿿぀-ヿ가-힯؀-ۿЀ-ӿ฀-๿]/;

const SCRIPT_OK = {
    zh: (t) => CJK.test(t) && !KANA.test(t),
    ja: (t) => KANA.test(t) || CJK.test(t),
    ko: (t) => HANGUL.test(t),
    ar: (t) => ARABIC.test(t),
    ru: (t) => CYRIL.test(t),
    th: (t) => THAI.test(t),
};

export function isWrongLanguage(text, answerLanguage) {
    const t = (text || '').trim();
    if (!t) return false;
    const lang = (answerLanguage || '').toLowerCase();
    const ok = SCRIPT_OK[lang];
    if (ok) return !ok(t);
    return NON_LATIN.test(t);
}

const LANG_NAMES = {
    zh: { zh: '中文',       en: 'Chinese',     ja: '中国語',         fr: 'chinois'      },
    ja: { zh: '日文',       en: 'Japanese',    ja: '日本語',         fr: 'japonais'     },
    ko: { zh: '韩文',       en: 'Korean',      ja: '韓国語',         fr: 'coréen'       },
    en: { zh: '英文',       en: 'English',     ja: '英語',           fr: 'anglais'      },
    fr: { zh: '法文',       en: 'French',      ja: 'フランス語',     fr: 'français'     },
    de: { zh: '德文',       en: 'German',      ja: 'ドイツ語',       fr: 'allemand'     },
    ar: { zh: '阿拉伯文',   en: 'Arabic',      ja: 'アラビア語',     fr: 'arabe'        },
    ru: { zh: '俄文',       en: 'Russian',     ja: 'ロシア語',       fr: 'russe'        },
    th: { zh: '泰文',       en: 'Thai',        ja: 'タイ語',         fr: 'thaïlandais'  },
    es: { zh: '西班牙文',   en: 'Spanish',     ja: 'スペイン語',     fr: 'espagnol'     },
    pt: { zh: '葡萄牙文',   en: 'Portuguese',  ja: 'ポルトガル語',   fr: 'portugais'    },
    vi: { zh: '越南文',     en: 'Vietnamese',  ja: 'ベトナム語',     fr: 'vietnamien'   },
    it: { zh: '意大利文',   en: 'Italian',     ja: 'イタリア語',     fr: 'italien'      },
    id: { zh: '印尼文',     en: 'Indonesian',  ja: 'インドネシア語', fr: 'indonésien'   },
    ms: { zh: '马来文',     en: 'Malay',       ja: 'マレー語',       fr: 'malais'       },
};

export function getLangName(answerLanguage, uiLang) {
    const lang = (answerLanguage || '').toLowerCase();
    const ui   = (uiLang || 'zh').split('-')[0].toLowerCase();
    return LANG_NAMES[lang]?.[ui] || LANG_NAMES[lang]?.en || lang.toUpperCase();
}
