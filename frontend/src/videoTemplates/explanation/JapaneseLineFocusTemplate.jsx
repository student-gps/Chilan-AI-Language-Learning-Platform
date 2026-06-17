import React from 'react';
import BlackboardShell from './BlackboardShell';
import ChalkTexture from './ChalkTexture';
import { blackboard, chalk } from './templateUtils';
import { JapaneseRubySentence } from './JapaneseSentenceTemplate';

const japaneseFontStack = '"Yu Gothic", "YuGothic", "Hiragino Sans", "Meiryo", "Noto Sans JP", "Inter", sans-serif';
const MIN_FONT_SIZE = 26;

function narrationFor(segment) {
    return (
        segment?.narration_track?.script ||
        segment?.narration_track?.subtitle_en ||
        segment?.narration_track?.subtitle_zh ||
        ''
    );
}

function cleanText(value) {
    return String(value || '').replace(/`+/g, '').replace(/\s+/g, ' ').trim();
}

function firstBlockContent(segment, blockType) {
    const blocks = segment?.visual_blocks || [];
    return blocks.find((block) => block.block_type === blockType)?.content || {};
}

function charLength(value) {
    return [...String(value || '')].length;
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

function JapaneseRubyLine({ text, tokens, reading, charSize }) {
    const validTokens = Array.isArray(tokens)
        ? tokens.map((token) => ({
            surface: cleanText(token?.surface),
            reading: cleanText(token?.annotation ?? token?.reading),
        })).filter((token) => token.surface)
        : [];

    if (validTokens.length === 0) {
        return (
            <JapaneseRubySentence
                text={text}
                reading={reading}
                color={chalk.white}
                charSize={charSize}
                rubySize={Math.max(MIN_FONT_SIZE, Math.round(charSize * 0.42))}
            />
        );
    }

    const rubySize = Math.max(MIN_FONT_SIZE, Math.round(charSize * 0.35));
    const tokenGap = Math.max(4, Math.round(charSize * 0.08));
    const lineHeight = charSize + rubySize + 12;

    return (
        <div style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'flex-end',
            columnGap: tokenGap,
            rowGap: 12,
            lineHeight: 1,
            maxWidth: '100%',
        }}>
            {validTokens.map((token, index) => {
                const ruby = tokenHasRuby(token) ? (token.annotation ?? token.reading) : '';
                const isPunctuation = /^[。、！？!?・]+$/.test(token.surface);
                return (
                    <span key={`${token.surface}-${index}`} style={{
                        display: 'inline-flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'flex-end',
                        minHeight: isPunctuation ? charSize : lineHeight,
                        marginLeft: isPunctuation ? -tokenGap : 0,
                    }}>
                        {!isPunctuation && (
                            <span style={{
                                minHeight: rubySize + 4,
                                marginBottom: 8,
                                fontFamily: japaneseFontStack,
                                fontSize: rubySize,
                                lineHeight: 1,
                                fontWeight: 800,
                                color: ruby ? 'rgba(244,240,230,0.50)' : 'transparent',
                                whiteSpace: 'nowrap',
                                letterSpacing: '0',
                            }}>
                                {ruby || ' '}
                            </span>
                        )}
                        <span style={{
                            fontFamily: japaneseFontStack,
                            fontSize: isPunctuation ? charSize * 0.68 : charSize,
                            lineHeight: 1,
                            fontWeight: 900,
                            color: chalk.white,
                            whiteSpace: 'nowrap',
                            letterSpacing: '0',
                            textShadow: '0 0 2px rgba(255,255,255,0.15), 1px 1px 0 rgba(9,20,16,0.35)',
                        }}>
                            {token.surface}
                        </span>
                    </span>
                );
            })}
        </div>
    );
}

function JapaneseRubyWord({ word, reading, color, charSize = 42, rubySize = MIN_FONT_SIZE }) {
    return (
        <JapaneseRubySentence
            text={word}
            reading={reading}
            color={color}
            charSize={charSize}
            rubySize={rubySize}
        />
    );
}

function focusSize(text) {
    const length = charLength(text);
    if (length <= 18) return 82;
    if (length <= 26) return 70;
    if (length <= 36) return 58;
    return 48;
}

function translationSize(text) {
    const length = charLength(text);
    if (length <= 18) return 34;
    if (length <= 30) return 30;
    return 26;
}

export default function JapaneseLineFocusTemplate({ segment }) {
    const heroContent = firstBlockContent(segment, 'hero_line');
    const teachingContent = firstBlockContent(segment, 'teaching_points');
    const focusText = cleanText(heroContent.focus_text || segment?.on_screen_text?.focus_text);
    const reading = cleanText(heroContent.focus_pinyin || segment?.on_screen_text?.focus_pinyin);
    const gloss = cleanText(heroContent.focus_gloss_en || segment?.on_screen_text?.focus_gloss_en);
    const quickTake = cleanText(teachingContent.notes || segment?.visual_notes);
    const highlightWords = Array.isArray(teachingContent.highlight_words) ? teachingContent.highlight_words : [];
    const tokens = Array.isArray(heroContent.tokens) ? heroContent.tokens : [];
    const mainSize = focusSize(focusText);

    return (
        <BlackboardShell subtitleText={narrationFor(segment)}>
            <ChalkTexture opacity={0.09} zIndex={0} />
            <div style={{
                position: 'absolute',
                inset: 0,
                pointerEvents: 'none',
                zIndex: 0,
                boxShadow: 'inset 0 0 0 2px rgba(68,42,24,0.35), inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

            <div style={{
                ...blackboard.header,
                position: 'relative',
                zIndex: 2,
                padding: '18px 36px 14px 36px',
            }}>
                <span style={{
                    fontSize: MIN_FONT_SIZE,
                    fontWeight: 800,
                    letterSpacing: '0.04em',
                    color: chalk.dim,
                }}>
                    {segment?.segment_title}
                </span>
            </div>

            <main style={{
                flex: 1,
                minHeight: 0,
                padding: '28px 56px 24px 56px',
                display: 'grid',
                gridTemplateRows: '1fr auto',
                gap: 22,
                position: 'relative',
                zIndex: 2,
                overflow: 'hidden',
            }}>
                <section style={{
                    minHeight: 0,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    paddingBottom: 18,
                }}>
                    <JapaneseRubyLine text={focusText} tokens={tokens} reading={reading} charSize={mainSize} />

                    {gloss && (
                        <div style={{
                            marginTop: 22,
                            display: 'inline-flex',
                            alignItems: 'center',
                            alignSelf: 'flex-start',
                            maxWidth: '100%',
                            fontSize: Math.max(MIN_FONT_SIZE, translationSize(gloss)),
                            fontWeight: 850,
                            lineHeight: 1.32,
                            color: chalk.yellow,
                            borderBottom: '2px solid rgba(245,215,110,0.45)',
                            paddingBottom: 4,
                            letterSpacing: '0',
                        }}>
                            {gloss}
                        </div>
                    )}
                </section>

                <section style={{ alignSelf: 'end', width: '100%' }}>
                    {highlightWords.length > 0 && (
                        <div style={{
                            display: 'flex',
                            gap: 22,
                            flexWrap: 'wrap',
                            marginBottom: 20,
                        }}>
                            {highlightWords.slice(0, 4).map((item, index) => {
                                const text = cleanText(item?.word);
                                if (!text) return null;
                                const readingText = cleanText(item?.pinyin || item?.reading);
                                const translation = cleanText(item?.translation);
                                const explanation = cleanText(item?.explanation);
                                const color = [chalk.blue, chalk.pink, chalk.yellow, chalk.green][index % 4];
                                return (
                                    <div key={`${text}-${index}`} style={{
                                        display: 'flex',
                                        flexDirection: 'column',
                                        gap: 8,
                                        minWidth: 190,
                                        maxWidth: 330,
                                        padding: '15px 17px 14px',
                                        borderRadius: 8,
                                        background: 'rgba(255,255,255,0.055)',
                                        border: '1px solid rgba(244,240,230,0.10)',
                                        borderBottom: `2px solid ${color}`,
                                    }}>
                                        <JapaneseRubyWord word={text} reading={readingText} color={color} />
                                        {translation && (
                                            <div style={{
                                                fontSize: MIN_FONT_SIZE,
                                                lineHeight: 1.24,
                                                fontWeight: 800,
                                                color: chalk.white,
                                                opacity: 0.74,
                                            }}>
                                                {translation}
                                            </div>
                                        )}
                                        {explanation && (
                                            <div style={{
                                                fontSize: MIN_FONT_SIZE,
                                                lineHeight: 1.35,
                                                fontWeight: 650,
                                                color: chalk.dim,
                                            }}>
                                                {explanation}
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {quickTake && (
                        <div style={{
                            display: 'flex',
                            gap: 18,
                            alignItems: 'flex-start',
                            background: 'rgba(0,0,0,0.22)',
                            borderRadius: 7,
                            border: '1px solid rgba(244,240,230,0.08)',
                            borderLeft: `3px solid ${chalk.blue}`,
                            padding: '14px 22px',
                        }}>
                            <p style={{
                                margin: 0,
                                fontSize: MIN_FONT_SIZE,
                                lineHeight: 1.5,
                                color: chalk.white,
                                opacity: 0.65,
                                fontStyle: 'italic',
                                fontWeight: 400,
                            }}>
                                {quickTake}
                            </p>
                        </div>
                    )}
                </section>
            </main>
        </BlackboardShell>
    );
}
