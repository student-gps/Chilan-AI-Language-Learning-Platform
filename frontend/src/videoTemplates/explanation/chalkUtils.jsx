import React from 'react';
import { chalk, fontStack } from './templateUtils';

// ── PatternFormula — renders grammar structural patterns like "[Statement]+呢？"
// Tokenises into: [Placeholder] badges | Chinese chars (with pinyin above) | other chars
export function PatternFormula({ text, color = chalk.yellow, size = 24, pinyin }) {
    if (!text) return null;
    // Split into tokens: [Placeholder], Chinese chars, other chars
    const tokens = [];
    const re = /(\[[^\]]+\])|([^\[]+)/g;
    let m;
    while ((m = re.exec(text)) !== null) {
        if (m[1]) {
            tokens.push({ type: 'placeholder', value: m[1] });
        } else {
            const sub = m[2];
            let i = 0;
            while (i < sub.length) {
                if (/[\u4e00-\u9fff]/.test(sub[i])) {
                    tokens.push({ type: 'chinese', value: sub[i] });
                    i++;
                } else {
                    let j = i;
                    while (j < sub.length && !/[\u4e00-\u9fff]/.test(sub[j])) j++;
                    tokens.push({ type: 'other', value: sub.slice(i, j) });
                    i = j;
                }
            }
        }
    }

    // Pre-assign pinyin syllables to Chinese tokens (ruby above each char)
    const syllables = extractPinyinSyllables(pinyin || '');
    const chineseTokenCount = tokens.filter(t => t.type === 'chinese').length;
    const hasPinyin = syllables.length > 0 && syllables.length === chineseTokenCount;
    let pi = 0;
    const pySize = Math.round(size * 0.42);
    const cellH = size + pySize + 4;

    return (
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', gap: 3, lineHeight: 1.3 }}>
            {tokens.map((tok, i) => {
                if (tok.type === 'placeholder') {
                    return (
                        <span key={i} style={{
                            display: 'inline-block',
                            background: 'rgba(244,240,230,0.12)',
                            border: `1px solid ${color}55`,
                            borderRadius: 5,
                            padding: '2px 7px',
                            fontSize: size * 0.72,
                            fontWeight: 700,
                            color: `${color}CC`,
                            letterSpacing: '0.03em',
                            alignSelf: 'flex-end',
                            marginBottom: hasPinyin ? 2 : 0,
                        }}>
                            {tok.value}
                        </span>
                    );
                }
                if (tok.type === 'chinese') {
                    const py = hasPinyin ? (syllables[pi++] || '') : null;
                    return (
                        <span key={i} style={{
                            display: 'inline-flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            height: py !== null ? cellH : undefined,
                            justifyContent: 'flex-end',
                        }}>
                            {py !== null && (
                                <span style={{
                                    fontSize: pySize,
                                    color: 'rgba(244,240,230,0.50)',
                                    letterSpacing: '0.01em',
                                    marginBottom: 3,
                                    lineHeight: 1,
                                    whiteSpace: 'nowrap',
                                }}>
                                    {py}
                                </span>
                            )}
                            <span style={{
                                fontFamily: fontStack,
                                fontSize: size,
                                fontWeight: 900,
                                color,
                                lineHeight: 1,
                            }}>
                                {tok.value}
                            </span>
                        </span>
                    );
                }
                // punctuation / + / spaces / ASCII
                return (
                    <span key={i} style={{
                        fontSize: size * 0.85,
                        fontWeight: 700,
                        color: `${color}99`,
                        lineHeight: 1,
                        alignSelf: 'flex-end',
                        paddingBottom: hasPinyin ? 2 : 0,
                    }}>
                        {tok.value}
                    </span>
                );
            })}
        </div>
    );
}

// ── Pinyin syllable extractor (shared) ───────────────────────────────────────
const PINYIN_VOWELS = 'aeiouüāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ';
const SYLLABLE_RE = new RegExp(
    `(?:zh|ch|sh|[bpmfdtnlgkhjqxrzcsyw])?[${PINYIN_VOWELS}]+(?:ng|n|r)?`,
    'gi',
);
export function extractPinyinSyllables(str) {
    if (!str) return [];
    return str.match(SYLLABLE_RE) || [];
}

// ── RubyWord — pinyin above each character, for vocab cards & highlight words ─
// Differs from RubyLine (full sentences) in that it's inline and doesn't wrap.
export function RubyWord({ text, pinyin, charSize = 44, pinyinSize = 15, color = chalk.white }) {
    if (!text) return null;
    const syllables = extractPinyinSyllables(pinyin);
    const chars = [...text];
    let pi = 0;
    const cellHeight = charSize + pinyinSize + 4;

    return (
        <div style={{ display: 'inline-flex', alignItems: 'flex-end', lineHeight: 1 }}>
            {chars.map((char, i) => {
                const isChinese = /[\u4e00-\u9fff]/.test(char);
                const py = isChinese ? (syllables[pi++] || '') : null;
                return (
                    <span key={i} style={{
                        display: 'inline-flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        height: cellHeight,
                        justifyContent: 'flex-end',
                        marginRight: isChinese ? 3 : 0,
                    }}>
                        {py !== null && (
                            <span style={{
                                fontSize: pinyinSize,
                                color: 'rgba(244,240,230,0.50)',
                                letterSpacing: '0.01em',
                                marginBottom: 4,
                                lineHeight: 1,
                            }}>
                                {py}
                            </span>
                        )}
                        <span style={{
                            fontFamily: fontStack,
                            fontSize: isChinese ? charSize : charSize * 0.7,
                            fontWeight: 900,
                            color,
                            lineHeight: 1,
                            textShadow: '1px 1px 0 rgba(9,20,16,0.20)',
                        }}>
                            {char}
                        </span>
                    </span>
                );
            })}
        </div>
    );
}
