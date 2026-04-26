import React from 'react';
import { blackboard, chalk } from './templateUtils';
import ChalkTexture from './ChalkTexture';
import { RubyWord } from './chalkUtils';
import BlackboardShell from './BlackboardShell';

function splitQA(text) {
    if (!text) return [{ text: '', color: chalk.green }];
    const qaMatch = text.match(/^Q[:：]\s*(.+?)\s+A[:：]\s*(.+)$/is);
    if (qaMatch) {
        return [
            { icon: '?', text: qaMatch[1].trim(), color: chalk.blue },
            { icon: '›', text: qaMatch[2].trim(), color: chalk.green },
        ];
    }
    return [{ icon: null, text, color: chalk.yellow }];
}

const PHRASE_COLORS = [chalk.yellow, chalk.blue, chalk.green, chalk.pink, chalk.yellow, chalk.blue];

export default function LessonRecapTemplate({ segment }) {
    const blocks = segment?.visual_blocks || [];
    const recap = blocks.find((b) => b.block_type === 'recap_summary');
    const content = recap?.content || {};
    const highlightWords = content.highlight_words || segment?.highlight_words || [];
    const grammarPoints = content.grammar_points || segment?.grammar_points || [];
    const narrationText = segment?.narration_track?.subtitle_en || '';

    const hasKeyPhrases = highlightWords.length > 0;

    return (
        <BlackboardShell subtitleText={narrationText}>
            <ChalkTexture opacity={0.09} zIndex={0} />
            <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
                boxShadow: 'inset 0 0 0 2px rgba(68,42,24,0.35), inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

            {/* Header */}
            <div style={{ ...blackboard.header, position: 'relative', zIndex: 2 }}>
                <span style={{ fontSize: 30, fontWeight: 800, letterSpacing: '0.04em', color: chalk.dim }}>
                    {segment?.segment_title || 'Lesson Recap'}
                </span>
            </div>

            {/* Body */}
            <div style={{
                flex: 1, overflow: 'hidden',
                padding: '20px 48px 16px',
                position: 'relative', zIndex: 2,
                display: 'grid',
                gridTemplateColumns: hasKeyPhrases && grammarPoints.length > 0 ? '1.1fr 0.9fr' : '1fr',
                gap: 32,
            }}>

                {/* Left — key phrases as big chalk writing */}
                {hasKeyPhrases && (
                    <section style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                        {highlightWords.slice(0, 6).map((item, i) => {
                            const color = PHRASE_COLORS[i];
                            return (
                                <div key={i} style={{
                                    display: 'flex', alignItems: 'center', gap: 22,
                                    padding: '10px 0',
                                    borderBottom: i < highlightWords.length - 1
                                        ? '1px solid rgba(244,240,230,0.07)' : 'none',
                                }}>
                                    <RubyWord
                                        text={item?.word}
                                        pinyin={item?.pinyin}
                                        charSize={52}
                                        pinyinSize={17}
                                        color={color}
                                    />
                                    {item?.translation && (
                                        <span style={{
                                            fontSize: 24, fontStyle: 'italic',
                                            color: chalk.white, opacity: 0.45,
                                            flexShrink: 0,
                                        }}>
                                            {item.translation}
                                        </span>
                                    )}
                                </div>
                            );
                        })}
                    </section>
                )}

                {/* Right — grammar summary cards */}
                {grammarPoints.length > 0 && (
                    <section style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                        {grammarPoints.slice(0, 4).map((item, i) => {
                            const accent = PHRASE_COLORS[i];
                            const lines = splitQA(item?.pattern);
                            return (
                                <div key={i} style={{
                                    borderRadius: 7,
                                    background: 'rgba(0,0,0,0.20)',
                                    borderLeft: `3px solid ${accent}`,
                                    border: `1px solid rgba(244,240,230,0.07)`,
                                    borderLeftWidth: 3,
                                    borderLeftColor: accent,
                                    padding: '12px 18px',
                                    display: 'flex', flexDirection: 'column', gap: 6,
                                }}>
                                    {lines.map(({ icon, text, color }, li) => (
                                        <div key={li} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                            {icon && (
                                                <span style={{
                                                    fontSize: 15, color, opacity: 0.5, flexShrink: 0,
                                                    fontStyle: icon === '?' ? 'italic' : 'normal',
                                                }}>
                                                    {icon}
                                                </span>
                                            )}
                                            <RubyWord text={text} charSize={32} pinyinSize={14} color={color} />
                                        </div>
                                    ))}
                                    {item?.explanation_en && (
                                        <p style={{
                                            margin: '5px 0 0', fontSize: 20, lineHeight: 1.5,
                                            color: chalk.white, opacity: 0.38, fontStyle: 'italic',
                                            borderTop: '1px solid rgba(244,240,230,0.06)',
                                            paddingTop: 6,
                                        }}>
                                            {item.explanation_en}
                                        </p>
                                    )}
                                </div>
                            );
                        })}
                    </section>
                )}
            </div>

        </BlackboardShell>
    );
}
