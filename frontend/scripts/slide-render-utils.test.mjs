import assert from 'node:assert/strict';
import path from 'node:path';
import test from 'node:test';
import { artifactRootFor, renderPropsForSegment, staticSegment } from './slide-render-utils.mjs';

test('each still receives its own resolved props as well as input props', () => {
    const first = { segment_id: 1, segment_title: 'First' };
    const second = { segment_id: 2, segment_title: 'Second' };
    const composition = { id: 'TeachingSlide', props: { segment: first }, width: 1920 };
    const options = renderPropsForSegment(composition, second);
    assert.deepEqual(options.inputProps, options.composition.props);
    assert.equal(options.composition.props.segment.segment_title, 'Second');
    assert.equal(composition.props.segment.segment_title, 'First');
    assert.equal(options.composition.width, 1920);
});

test('static export cannot receive narration, captions or production directions', () => {
    const segment = { template_name: 'line_focus', narration_track: { subtitle_en: 'First caption' },
        sentence_texts: ['First caption'], sentence_timings_seconds: [0], visual_notes: 'Animate the characters',
        visual_blocks: [{ block_type: 'hero_line', content: { focus_text: '你好' } }] };
    const board = staticSegment(segment);
    assert.equal(JSON.stringify(board).includes('First caption'), false);
    assert.equal(JSON.stringify(board).includes('Animate'), false);
    assert.equal(board.visual_blocks[0].content.focus_text, '你好');
    assert.equal(segment.narration_track.subtitle_en, 'First caption');
});

test('unknown templates fail instead of rendering a narration fallback', () => {
    assert.throws(() => staticSegment({ template_name: 'unknown' }), /Unsupported slide template/);
});

test('all pipelines resolve to their canonical language folders', () => {
    assert.equal(artifactRootFor('/repo', 'integrated_chinese'), path.join('/repo', 'backend/content_builder/zh/integrated_chinese/artifacts'));
    assert.equal(artifactRootFor('/repo', 'nce'), path.join('/repo', 'backend/content_builder/en/new_concept_english/artifacts'));
    assert.equal(artifactRootFor('/repo', 'mnn'), path.join('/repo', 'backend/content_builder/ja/minna_no_nihongo/artifacts'));
    assert.throws(() => artifactRootFor('/repo', '../other'), /Unknown content pipeline/);
});
