import { createContext, useContext } from 'react';

/**
 * Provides the current subtitle sentence index to SubtitleBar.
 *
 * - In a Remotion composition: SegmentScene computes the index using
 *   useCurrentFrame() and wraps the template in a SubtitleContext.Provider.
 * - In the preview page (no provider): falls back to sentenceIndex = 0,
 *   so the first sentence is always shown statically.
 */
export const SubtitleContext = createContext({
    sentenceIndex: 0,
    sentenceTexts: null,
    showSubtitleBar: true,
});

export function useSubtitleIndex() {
    return useContext(SubtitleContext).sentenceIndex;
}

export function useSubtitle() {
    return useContext(SubtitleContext);
}
