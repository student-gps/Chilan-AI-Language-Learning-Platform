import React from 'react';
import GrammarPatternTemplate from './GrammarPatternTemplate';
import GrammarTableTemplate from './GrammarTableTemplate';
import LineFocusTemplate from './LineFocusTemplate';
import LessonRecapTemplate from './LessonRecapTemplate';
import UsageFocusTemplate from './UsageFocusTemplate';
import { blackboard, chalk } from './templateUtils';
import ChalkTexture from './ChalkTexture';
import VocabSpotlightTemplate from './VocabSpotlightTemplate';

const FallbackTemplate = ({ segment }) => (
    <div style={{ ...blackboard.shell, justifyContent: 'center', padding: 48 }}>
        <ChalkTexture opacity={0.09} zIndex={1} />
        <div style={{ position: 'relative', zIndex: 2 }}>
            <div style={{
                fontSize: 11, fontWeight: 900, letterSpacing: '0.24em',
                textTransform: 'uppercase', color: chalk.faint,
            }}>
                {segment?.template_name || 'template'}
            </div>
            <h3 style={{ marginTop: 14, fontSize: 34, fontWeight: 900, color: chalk.white }}>
                {segment?.segment_title}
            </h3>
            <p style={{ marginTop: 18, fontSize: 20, lineHeight: 1.85, color: chalk.dim }}>
                {segment?.narration_track?.subtitle_en}
            </p>
        </div>
    </div>
);

export default function ExplanationSegmentTemplate({ segment }) {
    switch (segment?.template_name) {
        case 'line_focus':
            return <LineFocusTemplate segment={segment} />;
        case 'grammar_pattern':
            return <GrammarPatternTemplate segment={segment} />;
        case 'grammar_table':
            return <GrammarTableTemplate segment={segment} />;
        case 'vocab_spotlight':
            return <VocabSpotlightTemplate segment={segment} />;
        case 'lesson_recap':
            return <LessonRecapTemplate segment={segment} />;
        case 'usage_note':
            return <UsageFocusTemplate segment={segment} />;
        default:
            return <FallbackTemplate segment={segment} />;
    }
}
