import React from 'react';
import { chalk } from './templateUtils';
import { useSubtitle } from './SubtitleContext';

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

function restoreProtected(text) {
    return text.replace(/\x00/g, '.').replace(/\x01/g, '...').trim();
}

/**
 * Sentence splitter matching the backend TTS splitter. It protects ellipses,
 * abbreviations, and paired quotation spans so subtitle text and generated
 * sentence timings stay aligned.
 */
export function splitSentences(text) {
    if (!text) return [];
    const protected_ = text
        .trim()
        .replace(/…/g, '\x01')
        .replace(/\.{2,}/g, '\x01')
        .replace(_ABBREV_RE, (m) => m.slice(0, -1) + _PLACEHOLDER);

    const terminators = '.!?。！？';
    const trailingClosers = new Set(['"', '”', "'", ')', ']', '}', '」', '』']);
    const sentences = [];
    let start = 0;
    const quoteStack = [];
    const quotePairs = new Map([
        ['«', '»'],
        ['»', '«'],
        ['„', '“'],
        ['“', '”'],
        ['「', '」'],
        ['『', '』'],
    ]);
    let i = 0;

    const prevNonSpace = (index) => {
        let j = index;
        while (j >= 0 && /\s/.test(protected_[j])) j -= 1;
        return j >= 0 ? protected_[j] : '';
    };
    const isBoundary = (nextIndex, terminator) => (
        nextIndex === protected_.length
        || /\s/.test(protected_[nextIndex])
        || '。！？'.includes(terminator)
    );

    while (i < protected_.length) {
        const ch = protected_[i];

        if (protected_.startsWith('[zh:', i)) {
            const end = protected_.indexOf(']', i + 4);
            if (end !== -1) {
                i = end + 1;
                continue;
            }
        }

        if (quoteStack.length && ch === quoteStack[quoteStack.length - 1]) {
            quoteStack.pop();
            if (!quoteStack.length && terminators.includes(prevNonSpace(i - 1))) {
                let j = i + 1;
                while (j < protected_.length && trailingClosers.has(protected_[j])) j += 1;
                if (j === protected_.length || /\s/.test(protected_[j])) {
                    const sentence = restoreProtected(protected_.slice(start, j));
                    if (sentence) sentences.push(sentence);
                    while (j < protected_.length && /\s/.test(protected_[j])) j += 1;
                    start = j;
                    i = j;
                    continue;
                }
            }
        } else if (quotePairs.has(ch)) {
            quoteStack.push(quotePairs.get(ch));
        } else if (terminators.includes(ch) && !quoteStack.length) {
            let j = i + 1;
            while (j < protected_.length && trailingClosers.has(protected_[j])) j += 1;
            if (isBoundary(j, ch)) {
                const sentence = restoreProtected(protected_.slice(start, j));
                if (sentence) sentences.push(sentence);
                while (j < protected_.length && /\s/.test(protected_[j])) j += 1;
                start = j;
                i = j;
                continue;
            }
        }

        i += 1;
    }

    const tail = restoreProtected(protected_.slice(start));
    if (tail) sentences.push(tail);
    return sentences;
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
    const { sentenceIndex, sentenceTexts, showSubtitleBar = true } = useSubtitle();
    if (!showSubtitleBar) return null;

    const sentences = sentenceTexts?.length ? sentenceTexts : splitSentences(text);
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
