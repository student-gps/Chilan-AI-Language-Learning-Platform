import React from 'react';
import { blackboard, chalk, fontStack } from './templateUtils';
import ChalkTexture from './ChalkTexture';
import { RubyWord } from './chalkUtils';
import BlackboardShell from './BlackboardShell';

export default function VocabSpotlightTemplate({ segment }) {
    const blocks = segment?.visual_blocks || [];
    const vocabGrid = blocks.find((b) => b.block_type === 'vocab_grid');
    const microNote = blocks.find((b) => b.block_type === 'micro_note');
    const gridContent = vocabGrid?.content || {};
    const noteContent = microNote?.content || {};
    const highlightWords = gridContent?.highlight_words || segment?.highlight_words || [];
    const narrationText = segment?.narration_track?.subtitle_en || '';
    const teachingNote = noteContent?.notes || segment?.visual_notes;

    return (
        <BlackboardShell subtitleText={narrationText}>
            <ChalkTexture opacity={0.09} zIndex={0} />

            {/* Inner vignette */}
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
                display: 'grid', gridTemplateColumns: '1.15fr 0.85fr',
                gap: 28, padding: '20px 44px 16px',
                position: 'relative', zIndex: 2,
                flex: 1, overflow: 'hidden',
            }}>
                {/* Left — vocab grid */}
                <section style={{ ...blackboard.panel, display: 'flex', flexDirection: 'column', gap: 16, overflow: 'hidden' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
                        {highlightWords.slice(0, 6).map((item, index) => {
                            const wordColor = index % 2 === 0 ? chalk.yellow : chalk.green;
                            return (
                            <div key={`${item?.word || 'word'}-${index}`} style={{
                                borderRadius: 8,
                                background: 'rgba(0,0,0,0.28)',
                                border: '1px solid rgba(244,240,230,0.10)',
                                borderTop: `2px solid ${wordColor}44`,
                                padding: '18px 20px',
                                display: 'flex', flexDirection: 'column', gap: 8,
                            }}>
                                <RubyWord
                                    text={item?.word}
                                    pinyin={item?.pinyin}
                                    charSize={58}
                                    pinyinSize={18}
                                    color={wordColor}
                                />
                                <div style={{
                                    fontSize: 18, fontStyle: 'italic', fontWeight: 500,
                                    color: chalk.white, opacity: 0.7, letterSpacing: '0.01em',
                                }}>
                                    {item?.translation}
                                </div>
                                {item?.character_insight_en && (
                                    <p style={{
                                        margin: 0, fontSize: 17, lineHeight: 1.7,
                                        color: chalk.white, opacity: 0.5,
                                        fontStyle: 'italic',
                                        borderLeft: `2px solid ${wordColor}44`,
                                        paddingLeft: 10,
                                    }}>
                                        {item.character_insight_en}
                                    </p>
                                )}
                            </div>
                            );
                        })}
                    </div>
                </section>

                {/* Right — teaching note only (narration moves to subtitle bar) */}
                <section style={{ display: 'flex', flexDirection: 'column', gap: 20, overflow: 'hidden' }}>
                    {teachingNote && (
                        <div style={{ ...blackboard.panel, flex: 1, display: 'flex', flexDirection: 'column', gap: 18 }}>
                            {/* Note label */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                <span style={{
                                    width: 3, height: 22, borderRadius: 2,
                                    background: chalk.blue, flexShrink: 0,
                                }} />
                                <span style={{
                                    fontSize: 14, fontWeight: 800, letterSpacing: '0.12em',
                                    color: chalk.blue, opacity: 0.7, textTransform: 'uppercase',
                                }}>
                                    Note
                                </span>
                            </div>
                            <p style={{
                                margin: 0, fontSize: 20, lineHeight: 1.9,
                                color: chalk.white, opacity: 0.6,
                                fontStyle: 'italic', fontWeight: 400,
                                letterSpacing: '0.01em',
                            }}>
                                {teachingNote}
                            </p>
                        </div>
                    )}
                </section>
            </div>

        </BlackboardShell>
    );
}
