import React from 'react';
import { Composition } from 'remotion';
import ExplanationLessonVideo from './ExplanationLessonVideo';
import explanationRenderPlan from './generated/explanationRenderPlan';
import pinyinOverviewRenderPlan from './generated/pinyinOverviewRenderPlan';

const FPS = 30;
const WIDTH = 1920;
const HEIGHT = 1080;

export default function RemotionRoot() {
    const totalDurationSeconds = Number(explanationRenderPlan?.timeline?.total_duration_seconds) || 10;
    const durationInFrames = Math.max(30, Math.ceil(totalDurationSeconds * FPS));

    const pinyinDurationSeconds = Number(pinyinOverviewRenderPlan?.timeline?.total_duration_seconds) || 10;
    const pinyinDurationInFrames = Math.max(30, Math.ceil(pinyinDurationSeconds * FPS));

    return (
        <>
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
            <Composition
                id="PinyinOverviewVideo"
                component={ExplanationLessonVideo}
                durationInFrames={pinyinDurationInFrames}
                fps={FPS}
                width={WIDTH}
                height={HEIGHT}
                defaultProps={{
                    renderPlan: pinyinOverviewRenderPlan,
                }}
            />
        </>
    );
}
