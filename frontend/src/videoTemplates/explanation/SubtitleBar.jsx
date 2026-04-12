import React from 'react';
import { chalk } from './templateUtils';
import { useSubtitleIndex } from './SubtitleContext';

/**
 * Strip [zh:汉字] markers, replacing them with just the Chinese text.
 * Used for subtitle display so learners see 请问 instead of [zh:请问].
 */
export function stripZhMarkers(text) {
    if (!text) return text;
    return text.replace(/\[zh:([^\]]+)\]/g, '$1');
}

const _ABBREV_RE = /\b(Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|e\.g|i\.e|approx|dept|fig|govt|ca|cf|vol|no)\./gi;
const _PLACEHOLDER = '\x00';

/**
 * Sentence splitter — handles both ASCII (.!?) and Chinese (。！？) endings,
 * plus optional trailing quote/bracket before the whitespace.
 * Preserves common abbreviations (Mr. Dr. etc.) from being split mid-sentence.
 */
export function splitSentences(text) {
    if (!text) return [];
    const protected_ = text.replace(_ABBREV_RE, (m) => m.slice(0, -1) + _PLACEHOLDER);
    return protected_
        .split(/(?<=[.!?。！？]['"]?)\s+/)
        .map((s) => s.replace(/\x00/g, '.').trim())
        .filter(Boolean);
}

/**
 * Subtitle bar shown at the bottom of every explanation template.
 *
 * Gets the current sentence index from SubtitleContext:
 *   - Inside a Remotion Sequence: SegmentScene provides the index via context,
 *     driven by useCurrentFrame(), so sentences cycle automatically.
 *   - In the preview page (no provider): defaults to sentenceIndex = 0,
 *     always showing the first sentence statically.
 */
export default function SubtitleBar({ text }) {
    const sentenceIndex = useSubtitleIndex();
    const sentences = splitSentences(text);
    if (!sentences.length) return null;

    const current = stripZhMarkers(sentences[Math.min(sentenceIndex, sentences.length - 1)]);

    return (
        <div style={{
            position: 'relative', zIndex: 2,
            background: 'rgba(0,0,0,0.68)',
            borderTop: '1px solid rgba(244,240,230,0.08)',
            padding: '14px 48px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            minHeight: 74,
        }}>
            <p style={{
                margin: 0,
                fontSize: 32,
                lineHeight: 1.55,
                color: chalk.white,
                textAlign: 'center',
            }}>
                {current}
            </p>
        </div>
    );
}
