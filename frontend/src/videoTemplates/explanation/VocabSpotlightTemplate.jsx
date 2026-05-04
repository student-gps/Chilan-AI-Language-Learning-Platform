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
    const visibleWords = highlightWords.slice(0, 6);
    const wordCount = visibleWords.length;
    const longestWord = visibleWords.reduce((max, item) => Math.max(max, [...String(item?.word || '')].length), 0);
    const longestTranslation = visibleWords.reduce((max, item) => Math.max(max, String(item?.translation || '').length), 0);
    const longestInsight = visibleWords.reduce((max, item) => Math.max(max, String(item?.character_insight_en || '').length), 0);
    const noteLength = String(teachingNote || '').length;
    const roomy = wordCount <= 2;
    const medium = wordCount <= 4;
    const longRoomyCards = roomy && (longestWord >= 4 || longestTranslation > 24 || longestInsight > 70);
    const cardGap = roomy ? (longRoomyCards ? 22 : 30) : medium ? 20 : 14;
    const cardPadding = roomy ? (longRoomyCards ? '30px 32px' : '42px 44px') : medium ? '28px 30px' : '18px 20px';
    const cardMinHeight = roomy ? (longRoomyCards ? 248 : 268) : medium ? 176 : 0;
    const charSize = roomy
        ? (longestWord <= 2 ? 128 : longestWord <= 4 ? (longRoomyCards ? 86 : 104) : 70)
        : medium
            ? (longestWord <= 3 ? 82 : 68)
            : 56;
    const pinyinSize = roomy ? (longRoomyCards ? 27 : 32) : medium ? 23 : 18;
    const translationSize = roomy
        ? (longestTranslation > 30 ? 22 : longestTranslation > 20 ? 24 : longRoomyCards ? 28 : 34)
        : medium
            ? (longestTranslation > 22 ? 19 : 22)
            : 18;
    const insightSize = roomy ? (longestInsight > 95 ? 18 : longestInsight > 65 ? 20 : longRoomyCards ? 21 : 24) : medium ? 20 : 17;
    const noteFontSize = noteLength > 110 ? 27 : noteLength > 70 ? 32 : 38;
    const noteLineHeight = noteLength > 110 ? 1.55 : 1.65;
    const gridColumns = roomy ? '1fr 1fr' : medium ? '1fr 1fr' : '1fr 1fr';

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
                gap: 32, padding: '22px 46px 20px',
                position: 'relative', zIndex: 2,
                flex: 1, overflow: 'hidden',
            }}>
                {/* Left — vocab grid */}
                <section style={{
                    ...blackboard.panel,
                    padding: roomy ? (longRoomyCards ? 34 : 44) : medium ? 34 : 28,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: roomy ? 'flex-start' : 'center',
                    gap: 18,
                    overflow: 'hidden',
                }}>
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: gridColumns,
                        gap: cardGap,
                        alignContent: 'start',
                    }}>
                        {visibleWords.map((item, index) => {
                            const wordColor = index % 2 === 0 ? chalk.yellow : chalk.green;
                            return (
                            <div key={`${item?.word || 'word'}-${index}`} style={{
                                borderRadius: 8,
                                background: 'rgba(0,0,0,0.28)',
                                border: '1px solid rgba(244,240,230,0.10)',
                                borderTop: `2px solid ${wordColor}44`,
                                padding: cardPadding,
                                minHeight: cardMinHeight,
                                display: 'flex', flexDirection: 'column', gap: 8,
                                justifyContent: 'center',
                            }}>
                                <RubyWord
                                    text={item?.word}
                                    pinyin={item?.pinyin}
                                    charSize={charSize}
                                    pinyinSize={pinyinSize}
                                    color={wordColor}
                                />
                                <div style={{
                                    fontSize: translationSize, fontStyle: 'italic', fontWeight: 600,
                                    color: chalk.white, opacity: 0.7, letterSpacing: '0.01em',
                                    lineHeight: 1.35,
                                }}>
                                    {item?.translation}
                                </div>
                                {item?.character_insight_en && (
                                    <p style={{
                                        margin: 0, fontSize: insightSize, lineHeight: 1.55,
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
                        <div style={{
                            ...blackboard.panel,
                            padding: roomy ? 44 : 30,
                            flex: 1,
                            display: 'flex',
                            flexDirection: 'column',
                            gap: roomy ? 34 : 20,
                            overflow: 'hidden',
                        }}>
                            {/* Note label */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                                <span style={{
                                    width: 5, height: roomy ? 38 : 24, borderRadius: 2,
                                    background: chalk.blue, flexShrink: 0,
                                }} />
                                <span style={{
                                    fontSize: roomy ? 22 : 15, fontWeight: 900, letterSpacing: '0.14em',
                                    color: chalk.blue, opacity: 0.7, textTransform: 'uppercase',
                                }}>
                                    Note
                                </span>
                            </div>
                            <p style={{
                                margin: 0,
                                fontSize: noteFontSize,
                                lineHeight: noteLineHeight,
                                color: chalk.white, opacity: 0.6,
                                fontStyle: 'italic', fontWeight: 400,
                                letterSpacing: '0.01em',
                                maxWidth: '100%',
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
