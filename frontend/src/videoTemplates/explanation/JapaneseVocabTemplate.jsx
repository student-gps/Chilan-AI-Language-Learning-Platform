import React from 'react';
import BlackboardShell from './BlackboardShell';
import ChalkTexture from './ChalkTexture';
import { blackboard, chalk } from './templateUtils';

const GROUP_META = {
    core: {
        heading: '主线词汇',
        accent: chalk.green,
        soft: 'rgba(141,232,184,0.12)',
        note: '会进入正常学习和复习。',
        footer: '先读假名，再把词义和课文场景连起来。',
    },
    supplementary: {
        heading: '补充词汇',
        accent: chalk.blue,
        soft: 'rgba(124,211,252,0.12)',
        note: '常出现在练习和替换表达里。',
        footer: '重点是见到能懂，之后会在练习里反复遇到。',
    },
    display_only: {
        heading: '专名识别',
        accent: chalk.pink,
        soft: 'rgba(244,114,182,0.12)',
        note: '只需要在课文里认得，不进入复习。',
        footer: '知道它是人名、地名或机构名即可。',
    },
};
const MIN_FONT_SIZE = 26;
const japaneseFontStack = '"Yu Gothic", "YuGothic", "Hiragino Sans", "Meiryo", "Noto Sans JP", "Inter", sans-serif';

function narrationFor(segment) {
    return (
        segment?.narration_track?.script ||
        segment?.narration_track?.subtitle_en ||
        segment?.narration_track?.subtitle_zh ||
        ''
    );
}

function cleanText(value = '') {
    return String(value || '').replace(/`/g, '').trim();
}

function pickBlock(segment) {
    const blocks = segment?.visual_blocks || [];
    return blocks.find((block) => block.block_type === 'ja_vocab_board') || {};
}

function itemLength(item) {
    return Math.max(
        [...String(item?.term || '')].length,
        [...String(item?.translation || '')].length,
        [...String(item?.note || '')].length,
    );
}

function normalizeJapanese(value) {
    return cleanText(value)
        .replace(/[。、！？!?・]/g, '')
        .replace(/\s+/g, '');
}

function hasKanji(value) {
    return /[\u3400-\u9fff々]/.test(value);
}

function isKanaLike(char) {
    return /[\u3040-\u30ffー・\s。、！？!?]/.test(char);
}

function splitRubyToken(surface, reading) {
    const surfaceChars = [...cleanText(surface)];
    const readingChars = [...cleanText(reading)];
    if (!surfaceChars.length || !readingChars.length) {
        return { prefix: '', core: cleanText(surface), ruby: cleanText(reading), suffix: '' };
    }

    let prefixLength = 0;
    while (
        prefixLength < surfaceChars.length &&
        prefixLength < readingChars.length &&
        surfaceChars[prefixLength] === readingChars[prefixLength] &&
        isKanaLike(surfaceChars[prefixLength])
    ) {
        prefixLength += 1;
    }

    let suffixLength = 0;
    while (
        suffixLength < surfaceChars.length - prefixLength &&
        suffixLength < readingChars.length - prefixLength &&
        surfaceChars[surfaceChars.length - 1 - suffixLength] === readingChars[readingChars.length - 1 - suffixLength] &&
        isKanaLike(surfaceChars[surfaceChars.length - 1 - suffixLength])
    ) {
        suffixLength += 1;
    }

    const prefix = surfaceChars.slice(0, prefixLength).join('');
    const suffix = suffixLength ? surfaceChars.slice(surfaceChars.length - suffixLength).join('') : '';
    const core = surfaceChars.slice(prefixLength, suffixLength ? surfaceChars.length - suffixLength : surfaceChars.length).join('');
    const ruby = readingChars.slice(prefixLength, suffixLength ? readingChars.length - suffixLength : readingChars.length).join('');
    return { prefix, core, ruby, suffix };
}

function shouldShowRuby(term, reading) {
    const cleanTerm = cleanText(term);
    const cleanReading = cleanText(reading);
    if (!cleanTerm || !cleanReading) return false;
    if (cleanTerm === 'は' && cleanReading === 'わ') return true;
    if (cleanTerm === 'へ' && cleanReading === 'え') return true;
    if (!hasKanji(cleanTerm)) return false;
    return normalizeJapanese(cleanTerm) !== normalizeJapanese(cleanReading);
}

function VocabTermWithRuby({ term, reading, color, charSize, rubySize }) {
    const cleanTerm = cleanText(term);
    const cleanReading = cleanText(reading);
    const baseStyle = {
        fontFamily: japaneseFontStack,
        fontSize: charSize,
        lineHeight: 1,
        fontWeight: 900,
        color,
        whiteSpace: 'nowrap',
        letterSpacing: 0,
    };
    if (!shouldShowRuby(cleanTerm, cleanReading)) {
        return (
            <div style={{
                ...baseStyle,
                lineHeight: 1.16,
                wordBreak: 'keep-all',
                overflowWrap: 'anywhere',
            }}>
                {cleanTerm}
            </div>
        );
    }

    const parts = splitRubyToken(cleanTerm, cleanReading);
    const rubyCore = parts.core && hasKanji(parts.core) ? parts.core : cleanTerm;
    const rubyText = parts.core && hasKanji(parts.core) ? parts.ruby : cleanReading;
    return (
        <div style={{
            display: 'inline-flex',
            alignItems: 'flex-end',
            maxWidth: '100%',
            lineHeight: 1,
        }}>
            {parts.core && hasKanji(parts.core) && parts.prefix && <span style={baseStyle}>{parts.prefix}</span>}
            <span style={{
                display: 'inline-flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
                minWidth: 0,
            }}>
                <span style={{
                    minHeight: rubySize + 3,
                    marginBottom: 5,
                    fontFamily: japaneseFontStack,
                    fontSize: rubySize,
                    lineHeight: 1,
                    fontWeight: 800,
                    color: 'rgba(244,240,230,0.52)',
                    whiteSpace: 'nowrap',
                    letterSpacing: 0,
                }}>
                    {rubyText}
                </span>
                <span style={baseStyle}>{rubyCore}</span>
            </span>
            {parts.core && hasKanji(parts.core) && parts.suffix && <span style={baseStyle}>{parts.suffix}</span>}
        </div>
    );
}

export default function JapaneseVocabTemplate({ segment }) {
    const block = pickBlock(segment);
    const content = block?.content || {};
    const group = content.group || 'core';
    const meta = GROUP_META[group] || GROUP_META.core;
    const items = Array.isArray(content.items) ? content.items.slice(0, 4) : [];
    const note = cleanText(content.note || meta.note);
    const narrationText = narrationFor(segment);

    const count = Math.max(items.length, 1);
    const longest = items.reduce((max, item) => Math.max(max, itemLength(item)), 0);
    const columns = '1fr 1fr';
    const termSize = longest > 18 ? 36 : longest > 12 ? 43 : 54;
    const readingSize = 26;
    const translationSize = 27;
    const cardPadding = '20px 24px';
    const cardMinHeight = count > 2 ? 218 : 252;

    return (
        <BlackboardShell subtitleText={narrationText}>
            <ChalkTexture opacity={0.09} zIndex={0} />
            <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
                boxShadow: 'inset 0 0 0 2px rgba(68,42,24,0.35), inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

            <div style={{ ...blackboard.header, position: 'relative', zIndex: 2 }}>
                <span style={{ fontSize: MIN_FONT_SIZE, fontWeight: 800, letterSpacing: '0.04em', color: chalk.dim }}>
                    {segment?.segment_title}
                </span>
            </div>

            <div style={{
                position: 'relative',
                zIndex: 2,
                flex: 1,
                minHeight: 0,
                padding: '22px 46px 22px',
                display: 'grid',
                gridTemplateColumns: '0.7fr 1.7fr',
                gap: 30,
                overflow: 'hidden',
            }}>
                <aside style={{
                    ...blackboard.panel,
                    padding: 32,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    overflow: 'hidden',
                }}>
                    <div>
                        <div style={{
                            width: 58,
                            height: 7,
                            borderRadius: 999,
                            background: meta.accent,
                            marginBottom: 24,
                            boxShadow: `0 0 26px ${meta.accent}44`,
                        }} />
                        <h2 style={{
                            margin: 0,
                            fontSize: 54,
                            lineHeight: 1.12,
                            color: chalk.white,
                            fontWeight: 900,
                            letterSpacing: 0,
                        }}>
                            {content.heading || meta.heading}
                        </h2>
                        <p style={{
                            margin: '24px 0 0',
                            fontSize: 28,
                            lineHeight: 1.48,
                            color: chalk.white,
                            opacity: 0.62,
                            fontStyle: 'italic',
                            fontWeight: 600,
                        }}>
                            {note}
                        </p>
                    </div>

                    <div style={{
                        borderRadius: 8,
                        background: meta.soft,
                        border: `1px solid ${meta.accent}33`,
                        padding: '18px 20px',
                    }}>
                        <div style={{
                            fontSize: 26,
                            lineHeight: 1.45,
                            color: chalk.white,
                            opacity: 0.58,
                            fontWeight: 700,
                        }}>
                            {content.footer || meta.footer}
                        </div>
                    </div>
                </aside>

                <section style={{
                    ...blackboard.panel,
                    padding: 30,
                    display: 'grid',
                    gridTemplateColumns: columns,
                    gap: 16,
                    alignContent: count <= 4 ? 'center' : 'start',
                    overflow: 'hidden',
                }}>
                    {items.map((item, index) => {
                        const term = cleanText(item.term);
                        const reading = cleanText(item.reading);
                        const romaji = cleanText(item.romaji);
                        const translation = cleanText(item.translation);
                        const tag = cleanText(item.part_of_speech || item.category);
                        const isReview = item.memory_status === 'review';
                        return (
                            <article key={`${term}-${index}`} style={{
                                minHeight: cardMinHeight,
                                borderRadius: 9,
                                background: 'rgba(0,0,0,0.28)',
                                border: '1px solid rgba(244,240,230,0.10)',
                                borderTop: `3px solid ${meta.accent}`,
                                padding: cardPadding,
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'center',
                                gap: 8,
                                overflow: 'hidden',
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: 8, minHeight: 22 }}>
                                    {tag && (
                                        <span style={{
                                            borderRadius: 999,
                                            background: 'rgba(255,255,255,0.065)',
                                            color: chalk.white,
                                            opacity: 0.5,
                                            padding: '4px 9px',
                                            fontSize: 24,
                                            fontWeight: 900,
                                            letterSpacing: '0.08em',
                                            textTransform: 'uppercase',
                                            whiteSpace: 'nowrap',
                                        }}>
                                            {tag}
                                        </span>
                                    )}
                                    {isReview && (
                                        <span style={{
                                            borderRadius: 999,
                                            background: 'rgba(250,204,21,0.12)',
                                            color: chalk.yellow,
                                            padding: '4px 9px',
                                            fontSize: MIN_FONT_SIZE,
                                            fontWeight: 900,
                                            letterSpacing: '0.08em',
                                        }}>
                                            复现
                                        </span>
                                    )}
                                </div>

                                <VocabTermWithRuby
                                    term={term}
                                    reading={reading}
                                    color={meta.accent}
                                    charSize={termSize}
                                    rubySize={readingSize}
                                />

                                {translation && (
                                    <div style={{
                                        fontSize: translationSize,
                                        lineHeight: 1.32,
                                        color: chalk.white,
                                        opacity: 0.68,
                                        fontWeight: 800,
                                        fontStyle: 'italic',
                                        overflowWrap: 'anywhere',
                                    }}>
                                        {translation}
                                    </div>
                                )}

                                {romaji && group === 'display_only' && (
                                    <div style={{
                                        fontSize: MIN_FONT_SIZE,
                                        lineHeight: 1.25,
                                        color: chalk.white,
                                        opacity: 0.38,
                                        fontWeight: 700,
                                    }}>
                                        {romaji}
                                    </div>
                                )}
                            </article>
                        );
                    })}
                </section>
            </div>
        </BlackboardShell>
    );
}
