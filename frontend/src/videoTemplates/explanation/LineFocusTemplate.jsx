import { blackboard, chalk, fontStack } from './templateUtils';
import ChalkTexture from './ChalkTexture';
import { extractPinyinSyllables, RubyWord } from './chalkUtils';
import BlackboardShell from './BlackboardShell';

// ── Ruby-style pinyin-above-character renderer ────────────────────────────────
function RubyLine({ text, pinyin, charSize = 88, pinyinSize = 22 }) {
    if (!text) return null;
    const syllables = extractPinyinSyllables(pinyin);
    const chars = [...text];
    let pi = 0;
    const cellHeight = charSize + pinyinSize + 10;

    return (
        <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', lineHeight: 1 }}>
            {chars.map((char, i) => {
                const isChinese = /[\u4e00-\u9fff]/.test(char);
                const py = isChinese ? (syllables[pi++] || '') : null;
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
                padding: '26px 56px 22px 56px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                position: 'relative', zIndex: 2,
                overflow: 'hidden',
            }}>
                {/* Top: Ruby line + gloss */}
                <div>
                    <RubyLine text={focusText} pinyin={pinyin} charSize={116} pinyinSize={28} />
                    {gloss && (
                        <div style={{
                            marginTop: 22, marginLeft: 4,
                            display: 'inline-flex', alignItems: 'center',
                            fontSize: 42, fontWeight: 700,
                            color: chalk.yellow,
                            borderBottom: '2px solid rgba(245,215,110,0.45)',
                            paddingBottom: 2,
                        }}>
                            {gloss}
                        </div>
                    )}
                </div>

                {/* Bottom: highlight words + quick note */}
                <div>
                    {highlightWords.length > 0 && (
                        <div style={{ display: 'flex', gap: 56, marginBottom: 24, flexWrap: 'wrap' }}>
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
                                            charSize={74}
                                            pinyinSize={21}
                                            color={color}
                                        />
                                        {item?.english && (
                                            <span style={{ marginTop: 7, fontSize: 24, fontWeight: 700, color: chalk.dim }}>
                                                {item.english}
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
                            padding: '14px 22px',
                        }}>
                            <span style={{
                                fontSize: 18, fontWeight: 900, letterSpacing: '0.14em',
                                color: chalk.blue, opacity: 0.75, textTransform: 'uppercase',
                                paddingTop: 4, flexShrink: 0,
                            }}>
                                Note
                            </span>
                            <p style={{
                                margin: 0, fontSize: 30, lineHeight: 1.7,
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
