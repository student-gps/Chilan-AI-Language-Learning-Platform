import React from 'react';
import { Composition } from 'remotion';
import ExplanationLessonVideo from './ExplanationLessonVideo';
import explanationRenderPlan from './generated/explanationRenderPlan';

const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;

export default function RemotionRoot() {
    const totalDurationSeconds = Number(explanationRenderPlan?.timeline?.total_duration_seconds) || 10;
    const durationInFrames = Math.max(30, Math.ceil(totalDurationSeconds * FPS));

    return (
        <Composition
            id="ExplanationLessonVideo"
            component={ExplanationLessonVideo}
            durationInFrames={durationInFrames}
            fps={FPS}
            width={WIDTH}
            height={HEIGHT}
            defaultProps={{
                renderPlan: explanationRenderPlan,
            }}
        />
    );
}
