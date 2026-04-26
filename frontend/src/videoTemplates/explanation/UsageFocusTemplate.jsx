import { blackboard, chalk } from './templateUtils';
import ChalkTexture from './ChalkTexture';
import { RubyWord } from './chalkUtils';
import BlackboardShell from './BlackboardShell';

// Parse "Correct: X Incorrect: Y" from notes field
function parseContrastNotes(notes) {
    if (!notes) return { correct: null, incorrect: null, rule: null };
    const correctMatch = notes.match(/Correct:\s*(.+?)(?:\s+Incorrect:|$)/i);
    const incorrectMatch = notes.match(/Incorrect:\s*(.+?)(?:\s*$)/i);
    const isContrast = correctMatch || incorrectMatch;
    return {
        correct: correctMatch?.[1]?.trim() || null,
        incorrect: incorrectMatch?.[1]?.trim() || null,
        rule: isContrast ? null : notes, // if not contrast format, treat as plain rule
    };
}

export default function UsageFocusTemplate({ segment }) {
    const blocks = segment?.visual_blocks || [];
    const usageBlock = blocks.find((b) => b.block_type === 'usage_context');
    const content = usageBlock?.content || {};

    const highlightWords = segment?.highlight_words || [];
    const focusGloss = content?.focus_gloss_en || '';
    const notes = content?.notes || segment?.visual_notes || '';
    const narrationText = segment?.narration_track?.subtitle_en || '';

    const { correct, incorrect, rule } = parseContrastNotes(notes);
    const colors = [chalk.green, chalk.blue, chalk.yellow, chalk.pink];

    return (
        <BlackboardShell subtitleText={narrationText}>
            <ChalkTexture opacity={0.09} zIndex={0} />
            <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
                boxShadow: 'inset 0 0 0 2px rgba(68,42,24,0.35), inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

            {/* Header */}
            <div style={{ ...blackboard.header, position: 'relative', zIndex: 2 }}>
                <span style={{ fontSize: 26, fontWeight: 800, letterSpacing: '0.04em', color: chalk.dim }}>
                    {segment?.segment_title}
                </span>
            </div>

            {/* Body */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: highlightWords.length > 0 ? '0.9fr 1.1fr' : '1fr',
                gap: 28, padding: '20px 44px 16px',
                position: 'relative', zIndex: 2,
                flex: 1, overflow: 'hidden',
            }}>
                {/* Left — key vocabulary cards */}
                {highlightWords.length > 0 && (
                    <section style={{
                        ...blackboard.panel,
                        display: 'flex', flexDirection: 'column',
                        justifyContent: 'center',
                        gap: highlightWords.length >= 4 ? 14 : 26,
                    }}>
                        {highlightWords.slice(0, 4).map((item, i) => {
                            const color = colors[i % colors.length];
                            const compact = highlightWords.length >= 4;
                            return (
                                <div key={i} style={{
                                    display: 'flex', flexDirection: 'column', alignItems: 'flex-start',
                                    paddingBottom: compact ? 12 : 18,
                                    borderBottom: i < highlightWords.length - 1
                                        ? '1px solid rgba(244,240,230,0.08)' : 'none',
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: compact ? 10 : 14 }}>
                                        <RubyWord
                                            text={item.word}
                                            pinyin={item.pinyin}
                                            charSize={compact ? 58 : 82}
                                            pinyinSize={compact ? 17 : 23}
                                            color={color}
                                        />
                                        {item.translation && (
                                            <span style={{
                                                fontSize: compact ? 20 : 24,
                                                fontWeight: 700,
                                                color: chalk.dim,
                                                paddingBottom: 4,
                                            }}>
                                                {item.translation}
                                            </span>
                                        )}
                                    </div>
                                    {item.explanation_en && (
                                        <span style={{
                                            marginTop: 6, fontSize: compact ? 17 : 20,
                                            fontStyle: 'italic',
                                            color: chalk.white, opacity: 0.45, lineHeight: 1.5,
                                        }}>
                                            {item.explanation_en}
                                        </span>
                                    )}
                                </div>
                            );
                        })}
                    </section>
                )}

                {/* Right — rule + correct/incorrect contrast */}
                <section style={{ display: 'flex', flexDirection: 'column', gap: 18, overflow: 'hidden' }}>
                    {/* Brief rule statement */}
                    {focusGloss && (
                        <div style={{
                            display: 'flex', gap: 12, alignItems: 'flex-start',
                            background: 'rgba(0,0,0,0.22)',
                            borderRadius: 7,
                            border: '1px solid rgba(244,240,230,0.08)',
                            borderLeftWidth: 3, borderLeftColor: chalk.blue,
                            padding: '12px 20px',
                        }}>
                            <span style={{
                                fontSize: 14, fontWeight: 900, letterSpacing: '0.14em',
                                color: chalk.blue, opacity: 0.75, textTransform: 'uppercase',
                                paddingTop: 3, flexShrink: 0,
                            }}>
                                Rule
                            </span>
                            <p style={{
                                margin: 0, fontSize: 24, lineHeight: 1.6,
                                color: chalk.white, opacity: 0.6, fontStyle: 'italic',
                            }}>
                                {focusGloss}
                            </p>
                        </div>
                    )}

                    {/* Correct example */}
                    {correct && (
                        <div style={{
                            ...blackboard.panel,
                            display: 'flex', alignItems: 'flex-start', gap: 16,
                            borderLeft: `3px solid ${chalk.green}`,
                        }}>
                            <span style={{
                                fontSize: 32, fontWeight: 900, color: chalk.green,
                                flexShrink: 0, lineHeight: 1,
                            }}>✓</span>
                            <div>
                                <p style={{ margin: 0, fontSize: 34, fontWeight: 800, color: chalk.white, lineHeight: 1.4 }}>
                                    {correct}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Incorrect example */}
                    {incorrect && (
                        <div style={{
                            ...blackboard.panel,
                            display: 'flex', alignItems: 'flex-start', gap: 16,
                            borderLeft: `3px solid ${chalk.pink}`,
                        }}>
                            <span style={{
                                fontSize: 32, fontWeight: 900, color: chalk.pink,
                                flexShrink: 0, lineHeight: 1,
                            }}>✗</span>
                            <div>
                                <p style={{
                                    margin: 0, fontSize: 34, fontWeight: 800,
                                    color: chalk.white, opacity: 0.55,
                                    lineHeight: 1.4, textDecoration: 'line-through',
                                    textDecorationColor: `${chalk.pink}88`,
                                }}>
                                    {incorrect}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Plain rule fallback (if notes isn't Correct/Incorrect format) */}
                    {rule && (
                        <div style={{ ...blackboard.panelLight, padding: '14px 20px' }}>
                            <p style={{ margin: 0, fontSize: 24, lineHeight: 1.7, color: chalk.dim, fontStyle: 'italic' }}>
                                {rule}
                            </p>
                        </div>
                    )}
                </section>
            </div>

        </BlackboardShell>
    );
}
