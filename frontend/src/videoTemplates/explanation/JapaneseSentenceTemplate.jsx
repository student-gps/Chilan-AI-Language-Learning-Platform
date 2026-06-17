import React from 'react';
import BlackboardShell from './BlackboardShell';
import ChalkTexture from './ChalkTexture';
import { blackboard, chalk } from './templateUtils';

const COLORS = [chalk.yellow, chalk.green, chalk.blue, chalk.pink];
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

function splitSpeaker(text = '') {
    const match = String(text).match(/^([^：:]{1,18})[：:](.+)$/);
    if (!match) return { speaker: '', text: String(text || '').trim() };
    return { speaker: match[1].trim(), text: match[2].trim() };
}

function cleanText(value) {
    return String(value || '').replace(/`+/g, '').replace(/\s+/g, ' ').trim();
}

function normalizeJapanese(value) {
    return cleanText(value)
        .replace(/[。、！？!?・]/g, '')
        .replace(/\s+/g, '');
}

function hasMeaningfulReading(text, reading) {
    if (!reading) return false;
    return normalizeJapanese(text) !== normalizeJapanese(reading);
}

function tokenHasRuby(token) {
    const surface = cleanText(token?.surface);
    const reading = cleanText(token?.annotation ?? token?.reading);
    if (!surface || !reading) return false;
    if (/^[。、！？!?・\s]+$/.test(surface)) return false;
    if (surface === 'は' && reading === 'わ') return true;
    if (surface === 'へ' && reading === 'え') return true;
    return normalizeJapanese(surface) !== normalizeJapanese(reading);
}

function isKanaLike(char) {
    return /[\u3040-\u30ffー・\s。、！？!?]/.test(char);
}

function splitRubyToken(surface, reading) {
    let surfaceText = cleanText(surface);
    const readingText = cleanText(reading);
    let trailingPunctuation = '';
    while (surfaceText && /^[。、！？!?]$/.test([...surfaceText].at(-1)) && !readingText.endsWith([...surfaceText].at(-1))) {
        const chars = [...surfaceText];
        trailingPunctuation = chars.at(-1) + trailingPunctuation;
        surfaceText = chars.slice(0, -1).join('');
    }

    const surfaceChars = [...surfaceText];
    const readingChars = [...readingText];
    if (!surfaceChars.length || !readingChars.length) {
        return { prefix: '', core: surface, ruby: reading, suffix: '' };
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
    const suffix = `${suffixLength ? surfaceChars.slice(surfaceChars.length - suffixLength).join('') : ''}${trailingPunctuation}`;
    const core = surfaceChars.slice(prefixLength, suffixLength ? surfaceChars.length - suffixLength : surfaceChars.length).join('');
    const ruby = readingChars.slice(prefixLength, suffixLength ? readingChars.length - suffixLength : readingChars.length).join('');

    if (!core || !ruby || !/[\u3400-\u9fff々]/.test(core)) {
        return { prefix: '', core: surface, ruby: reading, suffix: '' };
    }
    return { prefix, core, ruby, suffix };
}

function TokenWithRuby({ token, charSize, rubySize, color }) {
    const rubyParts = splitRubyToken(token.surface, token.annotation ?? token.reading);
    const plainStyle = {
        fontFamily: japaneseFontStack,
        fontSize: charSize,
        lineHeight: 1,
        fontWeight: 900,
        color,
        whiteSpace: 'nowrap',
        letterSpacing: '0',
    };
    if (!rubyParts.prefix && rubyParts.core === token.surface && rubyParts.ruby === (token.annotation ?? token.reading) && !rubyParts.suffix) {
        return (
            <span style={{
                display: 'inline-flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
            }}>
                <span style={{
                    minHeight: rubySize + 3,
                    marginBottom: 5,
                    fontFamily: japaneseFontStack,
                    fontSize: rubySize,
                    lineHeight: 1,
                    fontWeight: 800,
                    color: 'rgba(244,240,230,0.50)',
                    whiteSpace: 'nowrap',
                    letterSpacing: '0',
                }}>
                    {token.annotation ?? token.reading}
                </span>
                <span style={plainStyle}>{token.surface}</span>
            </span>
        );
    }

    return (
        <span style={{ display: 'inline-flex', alignItems: 'flex-end', lineHeight: 1 }}>
            {rubyParts.prefix && <span style={plainStyle}>{rubyParts.prefix}</span>}
            <span style={{
                display: 'inline-flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-end',
            }}>
                <span style={{
                    minHeight: rubySize + 3,
                    marginBottom: 5,
                    fontFamily: japaneseFontStack,
                    fontSize: rubySize,
                    lineHeight: 1,
                    fontWeight: 800,
                    color: 'rgba(244,240,230,0.50)',
                    whiteSpace: 'nowrap',
                    letterSpacing: '0',
                }}>
                    {rubyParts.ruby}
                </span>
                <span style={plainStyle}>{rubyParts.core}</span>
            </span>
            {rubyParts.suffix && <span style={plainStyle}>{rubyParts.suffix}</span>}
        </span>
    );
}

function canUseSyntheticRuby(surface, reading) {
    if (!hasMeaningfulReading(surface, reading) || !/[\u3400-\u9fff々]/.test(surface)) {
        return false;
    }
    const parts = splitRubyToken(surface, reading);
    const fellBackToWholeText = (
        !parts.prefix &&
        parts.core === surface &&
        parts.ruby === reading &&
        !parts.suffix
    );
    if (fellBackToWholeText) {
        return false;
    }
    return /^[\u3400-\u9fff々]+$/.test(parts.core);
}

function lineLength(line) {
    return Math.max(
        [...String(line?.text || '')].length,
        [...String(line?.translation || '')].length,
    );
}

export function JapaneseRubySentence({ text, reading, tokens, color, charSize, rubySize }) {
    const validTokens = Array.isArray(tokens)
        ? tokens.map((token) => ({
            surface: cleanText(token?.surface),
            reading: cleanText(token?.annotation ?? token?.reading),
        })).filter((token) => token.surface)
        : [];

    if (validTokens.length === 0) {
        const cleanSurface = cleanText(text);
        const cleanReading = cleanText(reading);
        const isSpecialParticleReading = (
            (cleanSurface === 'は' && cleanReading === 'わ') ||
            (cleanSurface === 'へ' && cleanReading === 'え')
        );
        const syntheticRuby = (isSpecialParticleReading || canUseSyntheticRuby(cleanSurface, cleanReading))
            ? { surface: cleanSurface, reading: cleanReading }
            : null;
        if (syntheticRuby) {
            return (
                <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    alignItems: 'flex-end',
                    columnGap: Math.max(3, Math.round(charSize * 0.07)),
                    rowGap: 7,
                    lineHeight: 1,
                    maxWidth: '100%',
                }}>
                    <TokenWithRuby token={syntheticRuby} charSize={charSize} rubySize={rubySize} color={color} />
                </div>
            );
        }
        return (
            <div style={{
                fontFamily: japaneseFontStack,
                fontSize: charSize,
                color,
                fontWeight: 900,
                lineHeight: 1.16,
                letterSpacing: '0',
                wordBreak: 'keep-all',
                overflowWrap: 'anywhere',
            }}>
                {text}
            </div>
        );
    }

    const tokenGap = Math.max(3, Math.round(charSize * 0.07));
    const tokenHeight = charSize + rubySize + 9;
    return (
        <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'flex-end',
            columnGap: tokenGap,
            rowGap: 7,
            lineHeight: 1,
            maxWidth: '100%',
        }}>
            {validTokens.map((token, tokenIndex) => {
                const ruby = tokenHasRuby(token) ? (token.annotation ?? token.reading) : '';
                const isPunctuation = /^[。、！？!?・]+$/.test(token.surface);
                return (
                    <span key={`${token.surface}-${tokenIndex}`} style={{
                        display: 'inline-flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        minHeight: isPunctuation ? charSize : tokenHeight,
                        marginLeft: isPunctuation ? -tokenGap : 0,
                    }}>
                        {!isPunctuation && !ruby && (
                            <span style={{
                                minHeight: rubySize + 3,
                                marginBottom: 5,
                                fontFamily: japaneseFontStack,
                                fontSize: rubySize,
                                lineHeight: 1,
                                fontWeight: 800,
                                color: 'transparent',
                                whiteSpace: 'nowrap',
                                letterSpacing: '0',
                            }}>
                                {' '}
                            </span>
                        )}
                        {ruby && !isPunctuation ? (
                            <TokenWithRuby token={token} charSize={charSize} rubySize={rubySize} color={color} />
                        ) : (
                            <span style={{
                                fontFamily: japaneseFontStack,
                                fontSize: isPunctuation ? charSize * 0.68 : charSize,
                                lineHeight: 1,
                                fontWeight: 900,
                                color,
                                whiteSpace: 'nowrap',
                                letterSpacing: '0',
                            }}>
                                {token.surface}
                            </span>
                        )}
                    </span>
                );
            })}
        </div>
    );
}

export default function JapaneseSentenceTemplate({ segment }) {
    const blocks = segment?.visual_blocks || [];
    const stackBlock = blocks.find((block) => block.block_type === 'ja_sentence_stack');
    const content = stackBlock?.content || {};
    const mode = content.mode || 'examples';
    const isDialogue = mode === 'dialogue';
    const lines = Array.isArray(content.lines) ? content.lines.slice(0, 4) : [];
    const note = content.note || segment?.teaching_goal || '';
    const narrationText = narrationFor(segment);

    const count = Math.max(lines.length, 1);
    const longest = lines.reduce((max, item) => Math.max(max, lineLength(item)), 0);
    const dense = count >= 4;
    const jpSize = dense
        ? (longest > 36 ? 28 : longest > 28 ? 31 : longest > 20 ? 35 : 40)
        : (longest > 36 ? 32 : longest > 28 ? 36 : longest > 20 ? 42 : 50);
    const readingSize = dense ? 20 : 25;
    const translationSize = dense ? 22 : 26;
    const cardPadding = dense ? '12px 20px' : '17px 24px';
    const cardGap = dense ? 12 : 16;

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
                display: 'flex',
                flexDirection: 'column',
                gap: 18,
                overflow: 'hidden',
            }}>
                {note && (
                    <div style={{
                        borderRadius: 8,
                        background: 'rgba(0,0,0,0.22)',
                        border: '1px solid rgba(244,240,230,0.10)',
                        borderLeft: `4px solid ${isDialogue ? chalk.blue : chalk.green}`,
                        padding: '13px 18px',
                    }}>
                        <span style={{
                            fontSize: 27,
                            lineHeight: 1.38,
                            color: chalk.white,
                            opacity: 0.62,
                            fontStyle: 'italic',
                            fontWeight: 500,
                        }}>
                            {note}
                        </span>
                    </div>
                )}

                <section style={{
                    ...blackboard.panel,
                    flex: 1,
                    minHeight: 0,
                    padding: 28,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: count <= 2 ? 'center' : 'flex-start',
                    gap: cardGap,
                    overflow: 'hidden',
                }}>
                    {lines.map((rawLine, index) => {
                        const accent = COLORS[index % COLORS.length];
                        const parsed = splitSpeaker(rawLine.text);
                        const speaker = rawLine.speaker || parsed.speaker;
                        const text = rawLine.text_clean || parsed.text || rawLine.text;
                        return (
                            <div key={`${text}-${index}`} style={{
                                borderRadius: 9,
                                background: 'rgba(0,0,0,0.28)',
                                border: '1px solid rgba(244,240,230,0.10)',
                                borderLeft: `4px solid ${accent}`,
                                padding: cardPadding,
                                display: 'grid',
                                gridTemplateColumns: isDialogue ? '180px 1fr' : '74px 1fr',
                                gap: 24,
                                alignItems: 'center',
                                minHeight: dense ? 132 : count >= 3 ? 158 : 188,
                            }}>
                                <div style={{
                                    alignSelf: 'stretch',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    borderRadius: 7,
                                    background: 'rgba(255,255,255,0.055)',
                                    color: accent,
                                    fontSize: MIN_FONT_SIZE,
                                    fontWeight: 900,
                                    lineHeight: 1.25,
                                    textAlign: 'center',
                                    padding: isDialogue ? '0 12px' : 0,
                                    wordBreak: 'keep-all',
                                }}>
                                    {isDialogue ? (speaker || '話者') : index + 1}
                                </div>
                                <div style={{ minWidth: 0, display: 'flex', flexDirection: 'column', gap: 7 }}>
                                    <JapaneseRubySentence
                                        text={text}
                                        reading={rawLine.reading}
                                        tokens={rawLine.tokens}
                                        color={accent}
                                        charSize={jpSize}
                                        rubySize={readingSize}
                                    />
                                    {rawLine.translation && (
                                        <div style={{
                                            fontSize: translationSize,
                                            color: chalk.white,
                                            opacity: 0.62,
                                            fontStyle: 'italic',
                                            fontWeight: 700,
                                            lineHeight: 1.32,
                                            whiteSpace: 'normal',
                                        }}>
                                            {rawLine.translation}
                                        </div>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </section>
            </div>
        </BlackboardShell>
    );
}
