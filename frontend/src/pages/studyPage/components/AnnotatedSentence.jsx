import React from 'react';

const formatPinyinDisplay = (value = '') => {
    return value
        .split(/\s+/)
        .filter(Boolean)
        .map((token) => token.toLowerCase())
        .join(' ');
};

const isChineseChar = (char = '') => /[\u3400-\u9fff]/.test(char);

const buildFallbackTokens = (cn = '', py = '') => {
    const chars = Array.from(cn || '');
    const pinyinTokens = formatPinyinDisplay(py).split(/\s+/).filter(Boolean);
    let pinyinIndex = 0;

    return chars.map((char) => {
        if (isChineseChar(char)) {
            const token = pinyinTokens[pinyinIndex] || '';
            pinyinIndex += 1;
            return { cn: char, py: token };
        }
        return { cn: char, py: '' };
    });
};

const normalizeTokens = (tokens = [], cn = '', py = '') => {
    const normalized = (tokens || [])
        .filter((token) => token && typeof token === 'object')
        .map((token) => ({
            // v1: {cn, py}  |  v2: {surface, annotation}
            cn: (token.cn ?? token.surface ?? '').trim(),
            // annotation may be explicitly null (punctuation) or absent; treat both as ''
            py: (token.py ?? token.annotation ?? '').trim(),
        }))
        .filter((token) => token.cn);

    if (normalized.length > 0) {
        return normalized;
    }

    return buildFallbackTokens(cn, py);
};

export default function AnnotatedSentence({
    tokens = [],
    cn = '',
    py = '',
    showPinyin = true,
    wrapperClassName = '',
    tokenClassName = '',
    pinyinClassName = '',
    textClassName = '',
}) {
    const annotatedTokens = normalizeTokens(tokens, cn, py);

    if (!showPinyin) {
        return (
            <div className={wrapperClassName}>
                {annotatedTokens.map((token, idx) => (
                    <span key={`${token.cn}-${idx}`} className={textClassName}>
                        {token.cn}
                    </span>
                ))}
            </div>
        );
    }

    return (
        <div className={wrapperClassName}>
            {annotatedTokens.map((token, idx) => (
                <span key={`${token.cn}-${idx}`} className={tokenClassName}>
                    <span className={pinyinClassName}>{token.py || '\u00A0'}</span>
                    <span className={textClassName}>{token.cn}</span>
                </span>
            ))}
        </div>
    );
}
