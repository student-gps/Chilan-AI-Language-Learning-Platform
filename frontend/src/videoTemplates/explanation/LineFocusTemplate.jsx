import { blackboard, chalk, fontStack } from './templateUtils';
import ChalkTexture from './ChalkTexture';
import { extractPinyinSyllables, RubyWord } from './chalkUtils';
import BlackboardShell from './BlackboardShell';

// ── Ruby-style pinyin-above-character renderer ────────────────────────────────
function RubyLine({ text, pinyin, charSize = 88, pinyinSize = 22 }) {
    if (!text) return null;
    const syllables = extractPinyinSyllables(pinyin);
    const chars = [...text];
    // Exclude erhua \u513f (retroflexion suffix, not independent syllable) from expected count
    const cnCount = (() => {
        let si = 0;
        return chars.filter((c, i) => {
            if (!/[\u4e00-\u9fff]/.test(c)) return false;
            const erhua = c === '\u513f' && i > 0 && /[\u4e00-\u9fff]/.test(chars[i - 1])
                && !/^[e\u0113\u00e9\u011b\u00e8\u00ea]/i.test(syllables[si] || '');
            if (!erhua) si++;
            return !erhua;
        }).length;
    })();
    const showPinyin = syllables.length === cnCount;
    let pi = 0;
    const cellHeight = charSize + pinyinSize + 10;

    return (
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', lineHeight: 1 }}>
            {chars.map((char, i) => {
                const isChinese = /[\u4e00-\u9fff]/.test(char);
                const isErhua = char === '\u513f' && i > 0 && /[\u4e00-\u9fff]/.test(chars[i - 1])
                    && !/^[e\u0113\u00e9\u011b\u00e8\u00ea]/i.test(syllables[pi] || '');
                const py = isChinese ? (isErhua ? null : (showPinyin ? (syllables[pi++] || '') : '')) : null;
                return (
                    <span
                        key={i}
                        style={{
                            display: 'inline-flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            height: cellHeight,
                            justifyContent: 'flex-end',
                            marginRight: isChinese ? 6 : 0,
                        }}
                    >
                        {py !== null && (
                            <span style={{
                                fontSize: pinyinSize,
                                color: 'rgba(244,240,230,0.50)',
                                letterSpacing: '0.01em',
                                marginBottom: 6,
                                lineHeight: 1,
                            }}>
                                {py}
                            </span>
                        )}
                        <span style={{
                            fontFamily: fontStack,
                            fontSize: isChinese ? charSize : charSize * 0.62,
                            fontWeight: 900,
                            color: chalk.white,
                            textShadow: '0 0 2px rgba(255,255,255,0.15), 1px 1px 0 rgba(9,20,16,0.35)',
                            lineHeight: 1,
                        }}>
                            {char}
                        </span>
                    </span>
                );
            })}
        </div>
    );
}
// ─────────────────────────────────────────────────────────────────────────────

export default function LineFocusTemplate({ segment }) {
    const blocks = segment?.visual_blocks || [];
    const hero = blocks.find((b) => b.block_type === 'hero_line');
    const teaching = blocks.find((b) => b.block_type === 'teaching_points');
    const heroContent = hero?.content || {};
    const teachingContent = teaching?.content || {};
    const highlightWords = teachingContent?.highlight_words || segment?.highlight_words || [];
    const quickTake = teachingContent?.notes || segment?.visual_notes;

    const focusText = heroContent?.focus_text  || segment?.on_screen_text?.focus_text;
    const pinyin    = heroContent?.focus_pinyin || segment?.on_screen_text?.focus_pinyin;
    const gloss     = heroContent?.focus_gloss_en || segment?.on_screen_text?.focus_gloss_en;

    // Subtitle: use full narration text, split into sentences for future animation
    const narrationText = segment?.narration_track?.subtitle_en || '';

    // Adaptive font size based on Chinese character count
    const cnCount = [...(focusText || '')].filter(c => /[一-鿿]/.test(c)).length;
    const hasBottom = highlightWords.length > 0 || !!quickTake;
    const glossLength = String(gloss || '').length;
    const quickTakeLength = String(quickTake || '').length;
    const roomyLongLine = cnCount > 25 && cnCount <= 55;
    let charSize, pinyinSize;
    if (cnCount <= 12)       { charSize = 126; pinyinSize = 30; }
    else if (cnCount <= 25)  { charSize = 96;  pinyinSize = 24; }
    else if (cnCount <= 50)  { charSize = 74;  pinyinSize = 20; }
    else                     { charSize = 46;  pinyinSize = 14; }
    if (hasBottom && cnCount > 55) {
        charSize   = Math.max(40, Math.round(charSize   * 0.88));
        pinyinSize = Math.max(12, Math.round(pinyinSize * 0.88));
    }
    const glossSize = glossLength > 130 ? 38 : glossLength > 90 ? 44 : roomyLongLine ? 52 : 46;
    const bottomCharSize = highlightWords.length > 3 ? 74 : roomyLongLine ? 88 : 78;
    const bottomPinyinSize = highlightWords.length > 3 ? 21 : roomyLongLine ? 25 : 22;
    const bottomTranslationSize = highlightWords.length > 3 ? 24 : roomyLongLine ? 29 : 25;
    const noteFontSize = quickTakeLength > 140 ? 29 : quickTakeLength > 90 ? 33 : roomyLongLine ? 36 : 31;
    const noteLineHeight = quickTakeLength > 120 ? 1.45 : 1.55;

    return (
        <BlackboardShell subtitleText={narrationText}>
            <ChalkTexture opacity={0.09} zIndex={0} />

            {/* Inner vignette */}
            <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
                boxShadow: 'inset 0 0 0 2px rgba(68,42,24,0.35), inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

            {/* ── Header ── */}
            <div style={{
                ...blackboard.header,
                position: 'relative', zIndex: 2,
                padding: '18px 36px 14px 36px',
            }}>
                <span style={{
                    fontSize: 30, fontWeight: 800, letterSpacing: '0.04em',
                    color: chalk.dim,
                }}>
                    {segment?.segment_title}
                </span>
            </div>

            {/* ── Blackboard content (full width) ── */}
            <div style={{
                flex: 1,
                padding: '24px 56px 24px 56px',
                display: 'grid',
                gridTemplateRows: roomyLongLine ? '1.35fr 0.85fr' : '1fr auto',
                gap: roomyLongLine ? 30 : 22,
                position: 'relative', zIndex: 2,
                overflow: 'hidden',
            }}>
                {/* Top: Ruby line + gloss */}
                <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'flex-start',
                    minHeight: 0,
                }}>
                    <RubyLine text={focusText} pinyin={pinyin} charSize={charSize} pinyinSize={pinyinSize} />
                    {gloss && (
                        <div style={{
                            marginTop: roomyLongLine ? 28 : 22, marginLeft: 4,
                            display: 'inline-flex', alignItems: 'center',
                            maxWidth: '100%',
                            fontSize: glossSize, fontWeight: 800,
                            lineHeight: 1.35,
                            color: chalk.yellow,
                            borderBottom: '2px solid rgba(245,215,110,0.45)',
                            paddingBottom: 2,
                        }}>
                            {gloss}
                        </div>
                    )}
                </div>

                {/* Bottom: highlight words + quick note */}
                <div style={{ alignSelf: 'end', width: '100%' }}>
                    {highlightWords.length > 0 && (
                        <div style={{
                            display: 'flex',
                            gap: roomyLongLine ? 72 : 56,
                            marginBottom: roomyLongLine ? 28 : 24,
                            flexWrap: 'wrap',
                        }}>
                            {highlightWords.slice(0, 4).map((item, index) => {
                                const color = [chalk.blue, chalk.pink, chalk.yellow, chalk.green][index % 4];
                                return (
                                    <div key={`${item?.word}-${index}`} style={{
                                        display: 'flex', flexDirection: 'column', alignItems: 'center',
                                        paddingBottom: 8,
                                        borderBottom: `2px solid ${color}`,
                                        minWidth: 100,
                                    }}>
                                        <RubyWord
                                            text={item?.word}
                                            pinyin={item?.pinyin}
                                            charSize={bottomCharSize}
                                            pinyinSize={bottomPinyinSize}
                                            color={color}
                                        />
                                        {item?.translation && (
                                            <span style={{ marginTop: 8, fontSize: bottomTranslationSize, fontWeight: 750, color: chalk.dim }}>
                                                {item.translation}
                                            </span>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {quickTake && (
                        <div style={{
                            display: 'flex', gap: 18, alignItems: 'flex-start',
                            background: 'rgba(0,0,0,0.22)',
                            borderRadius: 7,
                            border: '1px solid rgba(244,240,230,0.08)',
                            borderLeft: `3px solid ${chalk.blue}`,
                            padding: roomyLongLine ? '18px 24px' : '14px 22px',
                        }}>
                            <span style={{
                                fontSize: roomyLongLine ? 20 : 18, fontWeight: 900, letterSpacing: '0.14em',
                                color: chalk.blue, opacity: 0.75, textTransform: 'uppercase',
                                paddingTop: 4, flexShrink: 0,
                            }}>
                                Note
                            </span>
                            <p style={{
                                margin: 0, fontSize: noteFontSize, lineHeight: noteLineHeight,
                                color: chalk.white, opacity: 0.65,
                                fontStyle: 'italic', fontWeight: 400,
                            }}>
                                {quickTake}
                            </p>
                        </div>
                    )}
                </div>
            </div>

        </BlackboardShell>
    );
}
