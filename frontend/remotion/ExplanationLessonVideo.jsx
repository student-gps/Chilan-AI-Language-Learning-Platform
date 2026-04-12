import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import ExplanationSegmentTemplate from '../src/videoTemplates/explanation/ExplanationSegmentTemplate';
import { splitSentences } from '../src/videoTemplates/explanation/SubtitleBar';
import { SubtitleContext } from '../src/videoTemplates/explanation/SubtitleContext';

const FPS = 30;

function SegmentScene({ segment }) {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const enter = spring({
        fps,
        frame,
        config: {
            damping: 18,
            stiffness: 140,
            mass: 0.9,
        },
    });

    const opacity = interpolate(frame, [0, 8], [0, 1], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
    });

    const translateY = interpolate(enter, [0, 1], [32, 0]);
    const scale = interpolate(enter, [0, 1], [0.98, 1]);

    // Compute which subtitle sentence to show based on current frame
    const narrationText = segment?.narration_track?.subtitle_en || '';
    const sentences = splitSentences(narrationText);
    const durationInSeconds = segment?.duration_seconds || segment?.estimated_duration_seconds || 12;
    const currentTimeSec = frame / fps;
    const timings = segment?.sentence_timings_seconds;

    let sentenceIndex;
    if (timings && timings.length > 0) {
        // Use actual TTS sentence timestamps for precise sync
        sentenceIndex = timings.filter((t) => t <= currentTimeSec).length - 1;
        sentenceIndex = Math.max(0, Math.min(sentenceIndex, sentences.length - 1));
    } else {
        // Fallback: equal distribution
        const totalFrames = Math.max(1, durationInSeconds * fps);
        const framesPerSentence = totalFrames / Math.max(1, sentences.length);
        sentenceIndex = Math.min(
            Math.floor(frame / framesPerSentence),
            Math.max(0, sentences.length - 1),
        );
    }

    return (
        <SubtitleContext.Provider value={{ sentenceIndex }}>
            <AbsoluteFill
                style={{
                    background: 'linear-gradient(180deg, #f8fafc 0%, #eef2ff 48%, #f8fafc 100%)',
                    opacity,
                }}
            >
                <div className="flex h-full w-full items-center justify-center px-16 py-16">
                    <div
                        style={{
                            width: '100%',
                            transform: `translateY(${translateY}px) scale(${scale})`,
                        }}
                    >
                        <ExplanationSegmentTemplate segment={segment} />
                    </div>
                </div>
            </AbsoluteFill>
        </SubtitleContext.Provider>
    );
}

export default function ExplanationLessonVideo({ renderPlan }) {
    const segments = renderPlan?.segments || [];

    return (
        <AbsoluteFill style={{ backgroundColor: '#eef2ff' }}>
            {segments.map((segment) => {
                const from = Math.round((Number(segment?.start_time_seconds) || 0) * FPS);
                const durationInFrames = Math.max(1, Math.round((Number(segment?.duration_seconds) || 1) * FPS));
                return (
                    <Sequence
                        key={`${segment?.segment_id}-${segment?.template_name}`}
                        from={from}
                        durationInFrames={durationInFrames}
                    >
                        <SegmentScene segment={segment} />
                    </Sequence>
                );
            })}
        </AbsoluteFill>
    );
}
