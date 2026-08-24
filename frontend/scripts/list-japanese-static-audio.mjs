import {
    CONTRACTED_SOUNDS,
    FOUNDATION_COPY,
    KANA_QUIZ,
    KANA_ROWS,
    KANJI_QUIZ,
    MORA_QUIZ,
    VOICED_KANA,
} from '../src/pages/japaneseFoundation/foundationContent.js';
import {
    JAPANESE_COURSE_INTRO_COPY,
    JAPANESE_COURSE_INTRO_SLIDES,
} from '../src/videoTemplates/courseIntro/japaneseCourseIntroContent.js';
import {
    japaneseCourseIntroAudioFilename,
    japaneseFoundationAudioFilename,
} from '../src/utils/japaneseStaticAudioNaming.js';

const foundationTexts = new Set();
const add = (value) => {
    const text = String(value || '').trim();
    if (text) foundationTexts.add(text);
};
const exampleText = (value) => String(value || '').split(' · ')[0].trim();
const firstKanjiExample = (value) => String(value || '').split('・')[0].split('（')[0].trim();
const toKatakana = (value) => String(value || '').replace(
    /[ぁ-ゖ]/g,
    (char) => String.fromCharCode(char.charCodeAt(0) + 0x60),
);

for (const row of KANA_ROWS) {
    for (const cell of row.cells) {
        if (!cell) continue;
        add(cell[0]);
        add(cell[1]);
    }
}
for (const row of VOICED_KANA) {
    for (const [, voiced] of row.pairs) {
        add(voiced);
        add(toKatakana(voiced));
    }
}
for (const [hiragana, katakana] of CONTRACTED_SOUNDS) {
    add(hiragana);
    add(katakana);
}
for (const item of KANA_QUIZ) add(item.kana);
for (const item of MORA_QUIZ) add(item.text);
for (const item of KANJI_QUIZ) add(item.word);

for (const copy of Object.values(FOUNDATION_COPY)) {
    for (const mark of copy.kana.marks) add(exampleText(mark[3]));
    for (const vowel of copy.pronunciation.vowels) add(exampleText(vowel[4]));
    for (const example of copy.pronunciation.moraExamples) add(example[0]);
    for (const contrast of copy.pronunciation.contrasts) {
        add(contrast.left[0]);
        add(contrast.right[0]);
    }
    for (const systemItem of copy.kanji.system) add(firstKanjiExample(systemItem.examples));
    for (const row of copy.kanji.contextRows) add(row[1]);
    for (const pair of copy.kanji.chinesePairs) add(pair[0]);
}

const manifest = [];
for (const language of ['zh', 'en']) {
    const copy = JAPANESE_COURSE_INTRO_COPY[language];
    for (const slide of JAPANESE_COURSE_INTRO_SLIDES) {
        manifest.push({
            kind: 'course_intro',
            language,
            slide_id: slide.id,
            text: copy[slide.id].narration,
            filename: japaneseCourseIntroAudioFilename(language, slide.id),
        });
    }
}
for (const text of [...foundationTexts].sort((left, right) => left.localeCompare(right, 'ja'))) {
    manifest.push({
        kind: 'foundation',
        language: 'ja',
        text,
        filename: japaneseFoundationAudioFilename(text),
    });
}

const filenames = new Map();
for (const item of manifest) {
    const existing = filenames.get(item.filename);
    if (existing && existing !== item.text) {
        throw new Error(`Static audio filename collision: ${item.filename}`);
    }
    filenames.set(item.filename, item.text);
}

process.stdout.write(JSON.stringify(manifest));
