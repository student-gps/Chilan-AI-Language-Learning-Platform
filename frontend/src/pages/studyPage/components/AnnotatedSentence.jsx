import React from 'react';

const isChineseChar = (char = '') => /[\u3400-\u9fff]/.test(char);

const buildFallbackTokens = (cn = '', py = '') => {
    const chars = Array.from(cn || '');
    const pinyinTokens = (py || '').toLowerCase().split(/\s+/).filter(Boolean);
    let pinyinIndex = 0;
    return chars.map((char) => ({
        surface: char,
        annotation: isChineseChar(char) ? (pinyinTokens[pinyinIndex++] || null) : null,
    }));
};

const normalizeTokens = (tokens = [], cn = '', py = '') => {
    const normalized = (tokens || [])
        .filter((t) => t && typeof t === 'object')
        .map((t) => ({
            surface: (t.cn ?? t.surface ?? '').trim(),
            annotation: (t.py ?? t.annotation ?? null),
        }))
        .filter((t) => t.surface);
    return normalized.length > 0 ? normalized : buildFallbackTokens(cn, py);
};

export default function AnnotatedSentence({
    tokens = [],
    cn = '',
    py = '',
    showPinyin = true,
    pinyinClassName = '',
    textClassName = '',
    // legacy layout props \u2014 no longer used, kept for call-site compat
    wrapperClassName,
    tokenClassName,
}) {
    const items = normalizeTokens(tokens, cn, py);

    if (!showPinyin) {
        return (
            <div>
                {items.map((t, i) => (
                    <span key={i} className={textClassName}>{t.surface}</span>
                ))}
            </div>
        );
    }

    return (
        <div className="leading-[2.5]">
            {items.map((t, i) => {
                if (!t.annotation) {
                    return <span key={i} className={textClassName}>{t.surface}</span>;
                }
                return (
                    <ruby key={i} className={textClassName}>
                        {t.surface}
                        <rt className={pinyinClassName}>{t.annotation}</rt>
                    </ruby>
                );
            })}
        </div>
    );
}
