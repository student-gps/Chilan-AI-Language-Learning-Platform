import React from 'react';
import { blackboard, chalk, fontStack } from './templateUtils';
import ChalkTexture from './ChalkTexture';
import BlackboardShell from './BlackboardShell';
import { PatternFormula } from './chalkUtils';

// ── char_grid sub-layout ────────────────────────────────────────────────────
// Renders a vocabulary grid: large char + pinyin above + English below
// Used for enumerable sets like numbers 0-10, months, measure words, etc.
function CharGrid({ content }) {
    if (!content) return null;
    const items = content.items || [];
    const accentColors = [chalk.yellow, chalk.green, chalk.blue, chalk.pink];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
            {content.title && (
                <span style={{
                    fontSize: 12, fontWeight: 900, letterSpacing: '0.16em',
                    color: chalk.blue, opacity: 0.7, textTransform: 'uppercase',
                }}>
                    {content.title}
                </span>
            )}
            <div style={{
                display: 'flex', flexWrap: 'wrap', gap: 10,
                alignContent: 'flex-start',
            }}>
                {items.map((item, i) => {
                    const color = accentColors[i % accentColors.length];
                    return (
                        <div key={i} style={{
                            display: 'flex', flexDirection: 'column', alignItems: 'center',
                            background: 'rgba(0,0,0,0.22)',
                            border: `1px solid ${color}30`,
                            borderTop: `2px solid ${color}55`,
                            borderRadius: 8,
                            padding: '10px 14px',
                            minWidth: 68,
                        }}>
                            <span style={{
                                fontSize: 12, lineHeight: 1,
                                color: 'rgba(244,240,230,0.50)',
                                marginBottom: 4,
                                letterSpacing: '0.01em',
                            }}>
                                {item.pinyin}
                            </span>
                            <span style={{
                                fontFamily: fontStack,
                                fontSize: 38, fontWeight: 900,
                                color, lineHeight: 1,
                                textShadow: '0 0 2px rgba(255,255,255,0.12)',
                            }}>
                                {item.char}
                            </span>
                            <span style={{
                                fontSize: 13, fontWeight: 700,
                                color: chalk.dim, marginTop: 5,
                                letterSpacing: '0.01em',
                            }}>
                                {item.english}
                            </span>
                        </div>
                    );
                })}
            </div>
            {content.note && (
                <p style={{
                    margin: '6px 0 0', fontSize: 14, lineHeight: 1.6,
                    color: chalk.faint, fontStyle: 'italic',
                }}>
                    {content.note}
                </p>
            )}
        </div>
    );
}

// ── pattern_table sub-layout ────────────────────────────────────────────────
// Renders a 3-column table: Pattern | Range | Example
// Used for systematic grammar rules like number formation, date patterns, etc.
function PatternTable({ content }) {
    if (!content) return null;
    const rows = content.rows || [];
    const accentColors = [chalk.yellow, chalk.blue, chalk.green, chalk.pink];

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, flex: 1 }}>
            {content.title && (
                <span style={{
                    fontSize: 12, fontWeight: 900, letterSpacing: '0.16em',
                    color: chalk.blue, opacity: 0.7, textTransform: 'uppercase',
                }}>
                    {content.title}
                </span>
            )}
            {/* Column headers */}
            <div style={{
                display: 'grid', gridTemplateColumns: '1.8fr 0.85fr 1.1fr',
                gap: 12, padding: '4px 16px',
            }}>
                {['Pattern', 'Range', 'Example'].map((h) => (
                    <span key={h} style={{
                        fontSize: 11, fontWeight: 900, letterSpacing: '0.18em',
                        color: 'rgba(244,240,230,0.30)', textTransform: 'uppercase',
                    }}>
                        {h}
                    </span>
                ))}
            </div>
            {/* Data rows */}
            {rows.map((row, i) => {
                const accent = accentColors[i % accentColors.length];
                return (
                    <div key={i} style={{
                        display: 'grid', gridTemplateColumns: '1.8fr 0.85fr 1.1fr',
                        gap: 12, alignItems: 'center',
                        background: 'rgba(0,0,0,0.22)',
                        borderLeft: `3px solid ${accent}`,
                        border: '1px solid rgba(244,240,230,0.08)',
                        borderLeftWidth: 3, borderLeftColor: accent,
                        borderRadius: 8,
                        padding: '10px 16px',
                    }}>
                        {/* Pattern column */}
                        <PatternFormula
                            text={row.pattern}
                            pinyin={row.pattern_pinyin || undefined}
                            color={accent}
                            size={22}
                        />
                        {/* Range column */}
                        <span style={{
                            fontSize: 15, color: chalk.dim,
                            fontStyle: 'italic', lineHeight: 1.4,
                        }}>
                            {row.range}
                        </span>
                        {/* Example column */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                            <span style={{
                                fontFamily: fontStack, fontSize: 26,
                                fontWeight: 900, color: accent, lineHeight: 1,
                                textShadow: '0 0 2px rgba(255,255,255,0.12)',
                            }}>
                                {row.example}
                            </span>
                            {row.example_pinyin && (
                                <span style={{
                                    fontSize: 13, color: 'rgba(244,240,230,0.45)',
                                    fontStyle: 'italic', lineHeight: 1,
                                }}>
                                    {row.example_pinyin}
                                </span>
                            )}
                            {row.example_english && (
                                <span style={{
                                    fontSize: 13, fontWeight: 700,
                                    color: chalk.dim, marginTop: 1,
                                }}>
                                    {row.example_english}
                                </span>
                            )}
                        </div>
                    </div>
                );
            })}
            {content.note && (
                <p style={{
                    margin: '4px 0 0', fontSize: 14, lineHeight: 1.6,
                    color: chalk.faint, fontStyle: 'italic',
                }}>
                    {content.note}
                </p>
            )}
        </div>
    );
}

// ── Main template ────────────────────────────────────────────────────────────
export default function GrammarTableTemplate({ segment }) {
    const blocks = segment?.visual_blocks || [];
    const charGridBlock = blocks.find((b) => b.block_type === 'char_grid');
    const patternTableBlock = blocks.find((b) => b.block_type === 'pattern_table');
    const narrationText = segment?.narration_track?.subtitle_en || '';

    const hasBoth = charGridBlock && patternTableBlock;

    return (
        <BlackboardShell subtitleText={narrationText}>
            <ChalkTexture opacity={0.09} zIndex={0} />
            <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
                boxShadow: 'inset 0 0 0 2px rgba(68,42,24,0.35), inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

            {/* Header */}
            <div style={{ ...blackboard.header, position: 'relative', zIndex: 2 }}>
                <span style={{ fontSize: 22, fontWeight: 800, letterSpacing: '0.04em', color: chalk.dim }}>
                    {segment?.segment_title}
                </span>
            </div>

            {/* Body — side-by-side if both present, full-width otherwise */}
            <div style={{
                display: hasBoth ? 'grid' : 'flex',
                gridTemplateColumns: hasBoth ? '1fr 1.2fr' : undefined,
                flexDirection: hasBoth ? undefined : 'column',
                gap: 20,
                padding: '14px 34px 12px',
                position: 'relative', zIndex: 2,
                flex: 1, overflow: 'hidden',
            }}>
                {charGridBlock && <CharGrid content={charGridBlock.content} />}
                {patternTableBlock && <PatternTable content={patternTableBlock.content} />}
            </div>
        </BlackboardShell>
    );
}
