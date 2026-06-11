/**
 * lessonNormalizer.js
 *
 * Normalises any lesson JSON (v1 or v2) to the unified Schema v2 shape so
 * the rest of the app only has to deal with one token format:
 *
 *   token = { surface, annotation, romanization, pos, highlight }
 *
 * v2 data passes through unchanged.
 * v1 Chinese data (words[{cn, py, highlight}]) is up-converted in-place.
 * v1 Japanese data (tokens[{surface, reading, romaji, pos, highlight}]) is
 * remapped to the v2 field names (reading → annotation, romaji → romanization).
 */

const SCHEMA_VERSION = '2.0';

/** Map pipeline_id / target_language → annotation_type */
const ANNOTATION_TYPE_MAP = {
  zh: 'pinyin',
  ja: 'furigana',
  ko: 'romanization',
};

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Normalise a raw lesson data object to Schema v2.
 * Returns the same object reference (mutated) for performance.
 *
 * @param {object} data  Raw lesson JSON from API / database
 * @returns {object}     Schema v2 lesson data
 */
export function normalizeLesson(data) {
  if (!data || typeof data !== 'object') return data;
  if (data.schema_version === SCHEMA_VERSION) return data;  // already v2

  // Inject top-level v2 fields if missing
  if (!data.schema_version) {
    const targetLanguage = data.target_language ?? _inferLanguage(data);
    data.schema_version  = SCHEMA_VERSION;
    data.target_language = targetLanguage;
    data.annotation_type = data.annotation_type ?? _inferAnnotationType(targetLanguage);
  }

  const content = data.course_content;
  if (!content || typeof content !== 'object') return data;

  // Normalise dialogue lines
  if (Array.isArray(content.dialogues)) {
    content.dialogues = content.dialogues.map(_normaliseDialogue);
  }

  // Normalise sentence_patterns (Japanese v1)
  if (Array.isArray(content.sentence_patterns)) {
    content.sentence_patterns = content.sentence_patterns.map(pattern => ({
      ...pattern,
      tokens: _normaliseTokenArray(pattern.tokens),
    }));
  }

  // Normalise example_sentences (Japanese v1)
  if (Array.isArray(content.example_sentences)) {
    content.example_sentences = content.example_sentences.map(ex => ({
      ...ex,
      tokens: _normaliseTokenArray(ex.tokens),
    }));
  }

  // Normalise vocabulary example_sentence tokens (Chinese v1)
  if (Array.isArray(content.vocabulary)) {
    content.vocabulary = content.vocabulary.map(vocab => {
      const ex = vocab.example_sentence;
      if (!ex || typeof ex !== 'object') return vocab;
      return {
        ...vocab,
        example_sentence: {
          ...ex,
          tokens: _normaliseTokenArray(ex.tokens || ex.words),
        },
      };
    });
  }

  return data;
}

/**
 * Return annotation_type for a given language code.
 * Returns null for languages that need no phonetic annotation.
 *
 * @param {string|null} lang  ISO 639-1 language code
 * @returns {string|null}
 */
export function annotationTypeForLanguage(lang) {
  return ANNOTATION_TYPE_MAP[String(lang || '').toLowerCase()] ?? null;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function _normaliseDialogue(dialogue) {
  if (!dialogue || typeof dialogue !== 'object') return dialogue;
  if (!Array.isArray(dialogue.lines)) return dialogue;
  return {
    ...dialogue,
    lines: dialogue.lines.map(line => ({
      ...line,
      tokens: _normaliseTokenArray(line.tokens || line.words),
    })),
  };
}

/**
 * Convert an array of raw tokens (any version) to v2 token objects.
 * Handles:
 *   - v2 already: { surface, annotation, ... }         → pass through
 *   - Chinese v1: { cn, py, highlight }                → surface/annotation
 *   - Japanese v1: { surface, reading, romaji, pos }   → annotation/romanization
 */
function _normaliseTokenArray(tokens) {
  if (!Array.isArray(tokens)) return [];
  return tokens.map(_normaliseToken).filter(Boolean);
}

function _normaliseToken(t) {
  if (!t || typeof t !== 'object') return null;

  // Already v2
  if ('surface' in t && 'annotation' in t) {
    return {
      surface:       t.surface       ?? '',
      annotation:    t.annotation    ?? null,
      romanization:  t.romanization  ?? null,
      pos:           t.pos           ?? '',
      highlight:     Boolean(t.highlight),
    };
  }

  // Chinese v1: { cn, py, highlight }
  if ('cn' in t) {
    return {
      surface:      t.cn             ?? '',
      annotation:   t.py             ?? null,
      romanization: null,
      pos:          t.pos            ?? '',
      highlight:    Boolean(t.highlight),
    };
  }

  // Japanese v1: { surface, reading, romaji, pos, highlight }
  if ('surface' in t) {
    return {
      surface:      t.surface        ?? '',
      annotation:   t.reading        ?? null,
      romanization: t.romaji         ?? null,
      pos:          t.pos            ?? '',
      highlight:    Boolean(t.highlight),
    };
  }

  return null;
}

function _inferLanguage(data) {
  const pid = String(data?.pipeline_id || '').toLowerCase();
  if (pid.includes('chinese'))  return 'zh';
  if (pid.includes('nihongo'))  return 'ja';
  if (pid.includes('english'))  return 'en';

  // Fall back to metadata heuristics already in teaching/index.jsx
  const slug = String(data?.lesson_metadata?.course_slug || '').toLowerCase();
  if (slug.includes('integrated_chinese')) return 'zh';
  if (slug.includes('minna'))              return 'ja';

  return null;
}

function _inferAnnotationType(targetLanguage) {
  return annotationTypeForLanguage(targetLanguage);
}
