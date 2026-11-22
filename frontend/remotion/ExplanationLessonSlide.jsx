import { AbsoluteFill } from 'remotion';
import ExplanationSegmentTemplate from '../src/videoTemplates/explanation/ExplanationSegmentTemplate';
import { SubtitleContext } from '../src/videoTemplates/explanation/SubtitleContext';
import { staticSegment } from '../src/videoTemplates/explanation/staticSlideData';

// A still is a teaching board, independent of the video's animation and clock.
// Captions remain in the deck JSON and are drawn by LessonSlideDeckPlayer.
export default function ExplanationLessonSlide({ segment }) {
    const board = staticSegment(segment);
    return (
        <SubtitleContext.Provider value={{ sentenceIndex: 0, sentenceTexts: [], showSubtitleBar: false }}>
            <AbsoluteFill style={{ backgroundColor: '#1F3B2D', justifyContent: 'center' }}>
                <ExplanationSegmentTemplate segment={board} />
            </AbsoluteFill>
        </SubtitleContext.Provider>
    );
}
