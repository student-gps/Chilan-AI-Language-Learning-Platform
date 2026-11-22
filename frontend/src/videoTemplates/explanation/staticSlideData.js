export const STATIC_SLIDE_VERSION = '3';
export const SUPPORTED_TEMPLATES = new Set([
    'line_focus', 'grammar_pattern', 'grammar_table', 'vocab_spotlight',
    'lesson_recap', 'usage_note', 'pinyin_tones', 'pinyin_grid',
    'ja_line_focus', 'ja_sentence_stack', 'ja_grammar_board', 'ja_vocab_board',
]);

export function staticSegment(segment) {
    if (!SUPPORTED_TEMPLATES.has(segment?.template_name)) {
        throw new Error(`Unsupported slide template: ${segment?.template_name} (segment ${segment?.segment_id})`);
    }
    const speechFields = new Set(['narration_track', 'sentence_texts', 'sentence_timings_seconds', 'visual_notes']);
    return Object.fromEntries(Object.entries(segment).filter(([key]) => !speechFields.has(key)));
}
