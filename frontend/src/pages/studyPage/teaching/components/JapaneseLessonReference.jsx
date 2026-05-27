import React, { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Eye, EyeOff, Languages, Loader2, MessageSquareText, Volume2, WalletCards } from 'lucide-react';

const KANJI_RE = /[\u3400-\u9fff]/;
const PUNCT_RE = /^[：。，！？、；,.!?…·—～]$/;
const PARTICLE_READINGS = {
    は: 'わ',
    へ: 'え',
};

const PART_OF_SPEECH_LABELS = {
    代: '代词',
    名: '名词',
    動: '动词',
    动: '动词',
    形: '形容词',
    い形: 'い形容词',
    な形: 'な形容词',
    副: '副词',
    助: '助词',
    接: '接续词',
    接尾: '接尾词',
    感: '感叹词',
    连语: '惯用表达',
    連語: '惯用表达',
    表現: '表达',
    表现: '表达',
    助数: '助数词',
    固有名詞: '专有名词',
    固有名词: '专有名词',
};

const asArray = (value) => (Array.isArray(value) ? value : []);

const normalizeLineRef = (value) => {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
};

const textOf = (...values) => {
    for (const value of values) {
        const text = String(value || '').trim();
        if (text) return text;
    }
    return '';
};

const formatPartOfSpeech = (value) => {
    const text = textOf(value);
    return PART_OF_SPEECH_LABELS[text] || text;
};

const normalizeJapanese = (value) => textOf(value)
    .replace(/[。、！？!?・]/g, '')
    .replace(/\s+/g, '');

const compactJapaneseText = (value) => textOf(value)
    .replace(/[\s[\]「」『』（）()]/g, '')
    .replace(/[。！？!?、，,.・]/g, '');

const tokensMatchText = (tokens = [], text = '') => {
    const expected = compactJapaneseText(text);
    if (!expected) return true;
    const actual = compactJapaneseText(asArray(tokens).map((token) => textOf(token.surface, token.cn, token.text, token.word)).join(''));
    return !actual || actual === expected;
};

const hasKanji = (value) => KANJI_RE.test(value || '');

const isKanaLike = (char) => /[\u3040-\u30ffー・\s。、！？!?〜~]/.test(char || '');

const splitRubyToken = (surface, reading) => {
    const surfaceChars = Array.from(textOf(surface));
    const readingChars = Array.from(textOf(reading));
    if (!surfaceChars.length || !readingChars.length) {
        return { prefix: '', core: textOf(surface), ruby: textOf(reading), suffix: '' };
    }

    let prefixLength = 0;
    while (
        prefixLength < surfaceChars.length &&
        prefixLength < readingChars.length &&
        surfaceChars[prefixLength] === readingChars[prefixLength] &&
        isKanaLike(surfaceChars[prefixLength])
    ) {
        prefixLength += 1;
    }

    let suffixLength = 0;
    while (
        suffixLength < surfaceChars.length - prefixLength &&
        suffixLength < readingChars.length - prefixLength &&
        surfaceChars[surfaceChars.length - 1 - suffixLength] === readingChars[readingChars.length - 1 - suffixLength] &&
        isKanaLike(surfaceChars[surfaceChars.length - 1 - suffixLength])
    ) {
        suffixLength += 1;
    }

    return {
        prefix: surfaceChars.slice(0, prefixLength).join(''),
        core: surfaceChars.slice(prefixLength, suffixLength ? surfaceChars.length - suffixLength : surfaceChars.length).join(''),
        ruby: readingChars.slice(prefixLength, suffixLength ? readingChars.length - suffixLength : readingChars.length).join(''),
        suffix: suffixLength ? surfaceChars.slice(surfaceChars.length - suffixLength).join('') : '',
    };
};

const normalizeToken = (token = {}) => ({
    surface: textOf(token.surface, token.cn, token.text, token.word),
    reading: textOf(token.reading, token.py, token.pinyin, token.kana),
    highlight: Boolean(token.highlight),
});

const shouldShowReading = (surface, reading) => {
    if (!surface || !reading || surface === reading) return false;
    if (PARTICLE_READINGS[surface] && PARTICLE_READINGS[surface] === reading) return true;
    if (!hasKanji(surface)) return false;
    return normalizeJapanese(surface) !== normalizeJapanese(reading);
};

const buildTokenGroups = (tokens = [], fallbackText = '') => {
    const safeTokens = tokensMatchText(tokens, fallbackText) ? tokens : [];
    const normalized = asArray(safeTokens)
        .map(normalizeToken)
        .filter((token) => token.surface);

    const source = normalized.length > 0
        ? normalized
        : Array.from(fallbackText || '').map((char) => ({ surface: char, reading: '', highlight: false }));

    const groups = [];
    for (const token of source) {
        if (PUNCT_RE.test(token.surface) && groups.length > 0) {
            groups[groups.length - 1] = {
                ...groups[groups.length - 1],
                suffix: `${groups[groups.length - 1].suffix || ''}${token.surface}`,
            };
        } else {
            groups.push({ ...token, suffix: '' });
        }
    }
    return groups;
};

function JapaneseText({ item = {}, showReading = true, size = 'base', muted = false }) {
    const text = textOf(item.text, item.term, item.word);
    const groups = buildTokenGroups(item.tokens, text);
    const sizeClass = size === 'large'
        ? 'text-3xl md:text-4xl'
        : size === 'small'
            ? 'text-lg md:text-xl'
            : 'text-2xl md:text-3xl';
    const colorClass = muted ? 'text-slate-500' : 'text-slate-900';
    const baseTextClass = `${sizeClass} ${colorClass} font-black leading-[2.2] tracking-normal`;
    const rtClass = "text-sm font-black leading-none text-rose-500";

    return (
        <span className={baseTextClass}>
            {groups.map((token, idx) => {
                const showRuby = showReading && shouldShowReading(token.surface, token.reading);
                const textClass = token.highlight ? 'text-blue-600' : '';
                if (!showRuby) {
                    return (
                        <span key={`${token.surface}-${idx}`} className={textClass}>
                            {token.surface}{token.suffix}
                        </span>
                    );
                }

                const parts = splitRubyToken(token.surface, token.reading);
                const shouldSplitKanji = parts.core && hasKanji(parts.core);
                if (shouldSplitKanji) {
                    return (
                        <React.Fragment key={`${token.surface}-${idx}`}>
                            {parts.prefix && <span className={textClass}>{parts.prefix}</span>}
                            <ruby className={`ruby align-baseline ${textClass}`}>
                                {parts.core}
                                <rt className={rtClass}>{parts.ruby || token.reading}</rt>
                            </ruby>
                            {parts.suffix && <span className={textClass}>{parts.suffix}</span>}
                            {token.suffix && <span className={textClass}>{token.suffix}</span>}
                        </React.Fragment>
                    );
                }

                return (
                    <React.Fragment key={`${token.surface}-${idx}`}>
                        <ruby className={`ruby align-baseline ${textClass}`}>
                            {token.surface}
                            <rt className={rtClass}>{token.reading}</rt>
                        </ruby>
                        {token.suffix && <span className={textClass}>{token.suffix}</span>}
                    </React.Fragment>
                );
            })}
        </span>
    );
}

function TermWithReading({ term, reading, showReading }) {
    const cleanTerm = textOf(term);
    const cleanReading = textOf(reading);
    const showRuby = showReading && shouldShowReading(cleanTerm, cleanReading);
    const termClassName = "max-w-full whitespace-nowrap text-center text-3xl font-black leading-none text-slate-900";
    if (!showRuby) {
        return <span className={termClassName}>{cleanTerm}</span>;
    }
    const parts = splitRubyToken(cleanTerm, cleanReading);
    const rubyCore = parts.core && hasKanji(parts.core) ? parts.core : cleanTerm;
    const rubyText = parts.core && hasKanji(parts.core) ? parts.ruby : cleanReading;
    const sideClassName = "whitespace-nowrap text-center text-3xl font-black leading-none text-slate-900";
    return (
        <span className="inline-flex max-w-full items-end align-bottom leading-none">
            {parts.core && hasKanji(parts.core) && parts.prefix && (
                <span className={sideClassName}>{parts.prefix}</span>
            )}
            <span className="inline-flex min-w-0 flex-col items-center justify-end">
                <span className="mb-1 min-h-[1rem] max-w-full whitespace-nowrap text-center text-sm font-black leading-none text-rose-500">
                    {rubyText}
                </span>
                <span className={termClassName}>{rubyCore}</span>
            </span>
            {parts.core && hasKanji(parts.core) && parts.suffix && (
                <span className={sideClassName}>{parts.suffix}</span>
            )}
        </span>
    );
}

function ToggleBar({ showReading, setShowReading, showTranslation, setShowTranslation }) {
    return (
        <div className="flex items-center gap-2 rounded-2xl border border-slate-200/70 bg-slate-100 p-1 shadow-inner">
            <button
                type="button"
                onClick={() => setShowReading((value) => !value)}
                className={`flex items-center gap-2 rounded-xl px-4 py-1.5 text-xs font-black transition-all ${
                    showReading ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400'
                }`}
            >
                {showReading ? <Eye size={14} /> : <EyeOff size={14} />}
                {showReading ? 'かな ON' : 'かな OFF'}
            </button>
            <button
                type="button"
                onClick={() => setShowTranslation((value) => !value)}
                className={`flex items-center gap-2 rounded-xl px-4 py-1.5 text-xs font-black transition-all ${
                    showTranslation ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400'
                }`}
            >
                {showTranslation ? <Languages size={14} /> : <BookOpen size={14} />}
                {showTranslation ? '翻译 ON' : '翻译 OFF'}
            </button>
        </div>
    );
}

const AudioIcon = ({ loading }) => (
    loading ? <Loader2 size={18} className="animate-spin" /> : <Volume2 size={18} />
);

function TextSection({
    title,
    eyebrow,
    icon: Icon,
    items,
    showReading,
    showTranslation,
    playTextAudio,
    playingKey,
    audioLoadingKey,
    activeLessonLineRef,
    dialogue = false,
}) {
    if (!items.length) return null;

    return (
        <section className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm md:p-8">
            <div className="mb-6 flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                    <Icon size={20} />
                </span>
                <div>
                    <h3 className="text-2xl font-black text-slate-900">{title}</h3>
                    <p className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-400">{eyebrow}</p>
                </div>
            </div>

            <div className="space-y-4">
                {items.map((item, idx) => {
                    const text = textOf(item.text);
                    const audioKey = `ja-reference-${title}-${idx}`;
                    const lineRef = normalizeLineRef(item.line_ref) || idx + 1;
                    const isLoading = audioLoadingKey === audioKey;
                    const isPlaying = playingKey === audioKey && !isLoading;
                    const isLessonActive = dialogue && activeLessonLineRef === normalizeLineRef(lineRef);
                    return (
                        <article
                            key={`${title}-${idx}`}
                            className={`rounded-[1.5rem] border p-5 transition-all ${
                                isLessonActive
                                    ? 'border-sky-200 bg-sky-50 shadow-sm shadow-sky-100'
                                    : 'border-slate-100 bg-slate-50/70'
                            }`}
                        >
                            <div className="flex items-start gap-4">
                                {dialogue && (
                                    <span className={`mt-8 min-w-16 text-sm font-black transition-colors ${
                                        isLessonActive ? 'text-sky-600' : 'text-slate-400'
                                    }`}>
                                        {textOf(item.speaker, item.role) || idx + 1}
                                    </span>
                                )}
                                <div className={`min-w-0 flex-1 ${isLessonActive ? 'border-l-4 border-sky-300 pl-4' : ''}`}>
                                    <JapaneseText item={item} showReading={showReading} size={dialogue ? 'base' : 'small'} />
                                    {showTranslation && item.translation && (
                                        <p className={`mt-2 text-lg font-bold ${isLessonActive ? 'text-sky-700/80' : 'text-slate-500'}`}>
                                            {item.translation}
                                        </p>
                                    )}
                                </div>
                                {playTextAudio && text && (
                                    <button
                                        type="button"
                                        onClick={() => playTextAudio(text, audioKey)}
                                        className={`mt-7 rounded-2xl p-2.5 shadow-sm transition hover:bg-slate-900 hover:text-white ${isPlaying ? 'bg-slate-900 text-white' : 'bg-white text-slate-400'}`}
                                        aria-label={isLoading ? '正在加载音频' : '播放'}
                                    >
                                        <AudioIcon loading={isLoading} />
                                    </button>
                                )}
                            </div>
                        </article>
                    );
                })}
            </div>
        </section>
    );
}

function VocabularyGroup({ title, eyebrow, items, showReading, showTranslation, playTextAudio, playingKey, audioLoadingKey }) {
    if (!items.length) return null;

    return (
        <section className="rounded-[2rem] border border-slate-100 bg-white p-6 shadow-sm md:p-8">
            <div className="mb-6 flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-100 text-slate-700">
                    <WalletCards size={20} />
                </span>
                <div>
                    <h3 className="text-2xl font-black text-slate-900">{title}</h3>
                    <p className="text-[10px] font-black uppercase tracking-[0.28em] text-slate-400">{eyebrow}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 items-start gap-4 md:grid-cols-2">
                {items.map((item, idx) => {
                    const term = textOf(item.term, item.word);
                    const reading = textOf(item.reading, item.romaji);
                    const translation = textOf(item.translation, item.definition);
                    const partOfSpeech = formatPartOfSpeech(item.part_of_speech);
                    const example = item.example_sentence && typeof item.example_sentence === 'object'
                        ? item.example_sentence
                        : null;
                    const exampleText = textOf(example?.text, example?.sentence);
                    const exampleTranslation = textOf(example?.translation, example?.definition);
                    const termAudioKey = `ja-vocab-${title}-${idx}`;
                    const exampleAudioKey = `ja-vocab-example-${title}-${idx}`;
                    const isTermLoading = audioLoadingKey === termAudioKey;
                    const isTermPlaying = playingKey === termAudioKey && !isTermLoading;
                    const isExampleLoading = audioLoadingKey === exampleAudioKey;
                    const isExamplePlaying = playingKey === exampleAudioKey && !isExampleLoading;
                    return (
                        <article key={`${title}-${term}-${idx}`} className="rounded-[1.5rem] border border-slate-100 bg-slate-50/70 p-5">
                            <div className="flex items-start justify-between gap-4">
                                <div className="min-w-0">
                                    <TermWithReading term={term} reading={reading} showReading={showReading} />
                                    {partOfSpeech && (
                                        <p className="mt-1 text-xs font-black uppercase tracking-widest text-slate-400">
                                            {partOfSpeech}
                                        </p>
                                    )}
                                    {showTranslation && translation && (
                                        <p className="mt-2 text-lg font-bold text-slate-600">{translation}</p>
                                    )}
                                </div>
                                {playTextAudio && term && (
                                    <button
                                        type="button"
                                        onClick={() => playTextAudio(term, termAudioKey)}
                                        className={`rounded-2xl p-2.5 shadow-sm transition hover:bg-slate-900 hover:text-white ${isTermPlaying ? 'bg-slate-900 text-white' : 'bg-white text-slate-400'}`}
                                        aria-label={isTermLoading ? '正在加载音频' : '播放'}
                                    >
                                        <AudioIcon loading={isTermLoading} />
                                    </button>
                                )}
                            </div>
                            {exampleText && (
                                <div className="mt-5 border-t border-slate-200/70 pt-4">
                                    <div className="mb-2 flex items-center justify-between gap-3">
                                        <span className="rounded-full bg-white px-2.5 py-1 text-[10px] font-black text-slate-400 shadow-sm">
                                            例句
                                        </span>
                                        {playTextAudio && (
                                            <button
                                                type="button"
                                                onClick={() => playTextAudio(exampleText, exampleAudioKey)}
                                                className={`rounded-xl p-2 shadow-sm transition hover:bg-slate-900 hover:text-white ${isExamplePlaying ? 'bg-slate-900 text-white' : 'bg-white text-slate-400'}`}
                                                aria-label={isExampleLoading ? '正在加载例句音频' : '播放例句'}
                                            >
                                                {isExampleLoading ? <Loader2 size={15} className="animate-spin" /> : <Volume2 size={15} />}
                                            </button>
                                        )}
                                    </div>
                                    <JapaneseText item={example} showReading={showReading} size="small" />
                                    {showTranslation && exampleTranslation && (
                                        <p className="mt-2 text-sm font-bold leading-relaxed text-slate-500">
                                            {exampleTranslation}
                                        </p>
                                    )}
                                </div>
                            )}
                        </article>
                    );
                })}
            </div>
        </section>
    );
}

export default function JapaneseLessonReference({
    courseContent = {},
    lessonMetadata = {},
    fadeInUp,
    playTextAudio,
    playingKey,
    audioLoadingKey,
    activeLessonLineRef,
    className = '',
}) {
    const [showReading, setShowReading] = useState(true);
    const [showTranslation, setShowTranslation] = useState(true);
    const Wrapper = fadeInUp ? motion.section : 'section';
    const wrapperProps = fadeInUp ? { variants: fadeInUp, initial: 'hidden', animate: 'show' } : {};

    const {
        patterns,
        examples,
        dialogueLines,
        coreVocab,
        supplementaryVocab,
        displayOnlyVocab,
    } = useMemo(() => {
        const vocab = asArray(courseContent.vocabulary);
        return {
            patterns: asArray(courseContent.sentence_patterns),
            examples: asArray(courseContent.example_sentences),
            dialogueLines: asArray(courseContent.dialogue?.lines),
            coreVocab: vocab.filter((item) => textOf(item.lesson_section).toLowerCase() !== 'supplementary'),
            supplementaryVocab: vocab.filter((item) => textOf(item.lesson_section).toLowerCase() === 'supplementary'),
            displayOnlyVocab: asArray(courseContent.display_only_vocabulary),
        };
    }, [courseContent]);

    const hasContent = patterns.length || examples.length || dialogueLines.length || coreVocab.length || supplementaryVocab.length || displayOnlyVocab.length;
    if (!hasContent) return null;

    const dialogueTitle = textOf(courseContent.dialogue?.title_localized, courseContent.dialogue?.title, '会話');

    return (
        <Wrapper {...wrapperProps} className={`mb-20 ${className}`}>
            <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                    <h2 className="text-3xl font-black tracking-tight text-slate-900">课文与词汇</h2>
                    <p className="mt-1 text-sm font-bold text-slate-500">
                        {lessonMetadata.title_localized || lessonMetadata.title || '本课内容'} 的原文、会话和完整词汇。
                    </p>
                </div>
                <ToggleBar
                    showReading={showReading}
                    setShowReading={setShowReading}
                    showTranslation={showTranslation}
                    setShowTranslation={setShowTranslation}
                />
            </div>

            <div className="space-y-6">
                <TextSection
                    title="文型"
                    eyebrow="Sentence Patterns"
                    icon={BookOpen}
                    items={patterns}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                    playingKey={playingKey}
                    audioLoadingKey={audioLoadingKey}
                    activeLessonLineRef={activeLessonLineRef}
                />
                <TextSection
                    title="例文"
                    eyebrow="Example Sentences"
                    icon={BookOpen}
                    items={examples}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                    playingKey={playingKey}
                    audioLoadingKey={audioLoadingKey}
                    activeLessonLineRef={activeLessonLineRef}
                />
                <TextSection
                    title={dialogueTitle}
                    eyebrow="Dialogue"
                    icon={MessageSquareText}
                    items={dialogueLines}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                    playingKey={playingKey}
                    audioLoadingKey={audioLoadingKey}
                    activeLessonLineRef={activeLessonLineRef}
                    dialogue
                />
                <VocabularyGroup
                    title="主线词汇"
                    eyebrow="Core Vocabulary"
                    items={coreVocab}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                    playingKey={playingKey}
                    audioLoadingKey={audioLoadingKey}
                />
                <VocabularyGroup
                    title="补充词汇"
                    eyebrow="Supplementary Vocabulary"
                    items={supplementaryVocab}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                    playingKey={playingKey}
                    audioLoadingKey={audioLoadingKey}
                />
                <VocabularyGroup
                    title="课文识别词"
                    eyebrow="Reference Names"
                    items={displayOnlyVocab}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                    playingKey={playingKey}
                    audioLoadingKey={audioLoadingKey}
                />
            </div>
        </Wrapper>
    );
}
