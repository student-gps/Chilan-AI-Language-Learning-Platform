import React from 'react';
import BlackboardShell from './BlackboardShell';
import ChalkTexture from './ChalkTexture';
import { JapaneseRubySentence } from './JapaneseSentenceTemplate';
import { blackboard, chalk } from './templateUtils';

const ACCENTS = [chalk.yellow, chalk.green, chalk.blue, chalk.pink];
const MIN_FONT_SIZE = 26;

function narrationFor(segment) {
    return (
        segment?.narration_track?.script ||
        segment?.narration_track?.subtitle_en ||
        segment?.narration_track?.subtitle_zh ||
        ''
    );
}

function firstBlockContent(segment) {
    const blocks = segment?.visual_blocks || [];
    return blocks.find((block) => block.block_type === 'ja_grammar_board')?.content || {};
}

function textLength(value) {
    return [...String(value || '')].length;
}

function cleanText(value) {
    return String(value || '').replace(/`+/g, '').replace(/\s+/g, ' ').trim();
}

function PatternCard({ item, index, compact }) {
    const accent = ACCENTS[index % ACCENTS.length];
    const text = cleanText(item?.text || item?.pattern || '');
    const translation = cleanText(item?.translation || '');
    const size = compact || textLength(text) > 26 ? 28 : 40;
    return (
        <div style={{
            borderRadius: 9,
            background: 'rgba(0,0,0,0.30)',
            border: '1px solid rgba(244,240,230,0.10)',
            borderLeft: `4px solid ${accent}`,
            padding: compact ? '16px 20px' : '20px 24px',
        }}>
            <div style={{
                fontSize: size,
                lineHeight: 1.18,
                fontWeight: 900,
                color: accent,
                letterSpacing: '0',
                overflowWrap: 'anywhere',
            }}>
                {text}
            </div>
            {translation && (
                <div style={{
                    marginTop: 8,
                    fontSize: 26,
                    lineHeight: 1.35,
                    color: chalk.white,
                    opacity: 0.62,
                    fontStyle: 'italic',
                    fontWeight: 700,
                }}>
                    {translation}
                </div>
            )}
        </div>
    );
}

function ExampleCard({ item, index, compact }) {
    const accent = ACCENTS[(index + 2) % ACCENTS.length];
    const text = cleanText(item?.text || '');
    const reading = cleanText(item?.reading || '');
    const translation = cleanText(item?.translation || '');
    const jpSize = compact || textLength(text) > 24 ? 28 : 36;
    const rubySize = compact ? 18 : 21;
    return (
        <div style={{
            borderRadius: 8,
            background: 'rgba(255,255,255,0.045)',
            border: '1px solid rgba(244,240,230,0.08)',
            padding: compact ? '12px 16px' : '14px 18px',
        }}>
            <JapaneseRubySentence
                text={text}
                reading={reading}
                tokens={item?.tokens}
                color={accent}
                charSize={jpSize}
                rubySize={rubySize}
            />
            {translation && (
                <div style={{
                    marginTop: 5,
                    fontSize: 25,
                    lineHeight: 1.32,
                    color: chalk.white,
                    opacity: 0.58,
                    fontStyle: 'italic',
                    fontWeight: 700,
                }}>
                    {translation}
                </div>
            )}
        </div>
    );
}

export default function JapaneseGrammarTemplate({ segment }) {
    const content = firstBlockContent(segment);
    const title = cleanText(content.title || segment?.segment_title || '');
    const explanation = cleanText(content.explanation || segment?.teaching_goal || '');
    const patterns = Array.isArray(content.patterns) ? content.patterns.slice(0, 2) : [];
    const examples = Array.isArray(content.examples) ? content.examples.slice(0, 2) : [];
    const usageNotes = Array.isArray(content.usage_notes) ? content.usage_notes.map(cleanText).filter(Boolean).slice(0, 2) : [];
    const narrationText = narrationFor(segment);
    const compact = explanation.length > 95 || patterns.length + examples.length >= 5;

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
                gridTemplateColumns: '0.95fr 1.05fr',
                gap: 28,
                overflow: 'hidden',
            }}>
                <section style={{
                    ...blackboard.panel,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    gap: compact ? 14 : 18,
                    padding: compact ? 28 : 34,
                    minHeight: 0,
                    overflow: 'hidden',
                }}>
                    <h2 style={{
                        margin: 0,
                        fontSize: textLength(title) > 24 ? 42 : 54,
                        lineHeight: 1.06,
                        color: chalk.green,
                        fontWeight: 900,
                        letterSpacing: '0',
                        overflowWrap: 'anywhere',
                    }}>
                        {title}
                    </h2>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: compact ? 10 : 14 }}>
                        {patterns.map((item, index) => (
                            <PatternCard key={`${item?.text || index}`} item={item} index={index} compact={compact} />
                        ))}
                    </div>
                </section>

                <section style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: compact ? 12 : 16,
                    minHeight: 0,
                    overflow: 'hidden',
                }}>
                    <div style={{
                        borderRadius: 8,
                        background: 'rgba(0,0,0,0.22)',
                        border: '1px solid rgba(244,240,230,0.10)',
                        borderLeft: `4px solid ${chalk.blue}`,
                        padding: compact ? '13px 18px' : '17px 22px',
                    }}>
                        <p style={{
                            margin: 0,
                            fontSize: 27,
                            lineHeight: compact ? 1.45 : 1.55,
                            color: chalk.white,
                            opacity: 0.66,
                            fontStyle: 'italic',
                            fontWeight: 500,
                        }}>
                            {explanation}
                        </p>
                    </div>

                    {usageNotes.length > 0 && (
                        <div style={{
                            display: 'flex',
                            gap: 10,
                            flexWrap: 'wrap',
                        }}>
                            {usageNotes.map((note, index) => (
                                <div key={`${note}-${index}`} style={{
                                    borderRadius: 999,
                                    padding: '8px 13px',
                                    background: 'rgba(245,215,110,0.10)',
                                    border: '1px solid rgba(245,215,110,0.18)',
                                    color: chalk.yellow,
                                    fontSize: 25,
                                    fontWeight: 800,
                                    lineHeight: 1.25,
                                }}>
                                    {note}
                                </div>
                            ))}
                        </div>
                    )}

                    <div style={{
                        ...blackboard.panel,
                        flex: 1,
                        minHeight: 0,
                        padding: compact ? 18 : 22,
                        display: 'flex',
                        flexDirection: 'column',
                        gap: compact ? 10 : 12,
                        overflow: 'hidden',
                    }}>
                        {examples.map((item, index) => (
                            <ExampleCard key={`${item?.text || index}`} item={item} index={index} compact={compact} />
                        ))}
                    </div>
                </section>
            </div>
        </BlackboardShell>
    );
}
