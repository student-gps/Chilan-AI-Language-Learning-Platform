import React, { useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Eye, EyeOff, Languages, MessageSquareText, Volume2, WalletCards } from 'lucide-react';

const KANJI_RE = /[\u3400-\u9fff]/;
const PUNCT_RE = /^[：。，！？、；,.!?…·—～]$/;
const PARTICLE_READINGS = {
    は: 'わ',
    へ: 'え',
};

const asArray = (value) => (Array.isArray(value) ? value : []);

const textOf = (...values) => {
    for (const value of values) {
        const text = String(value || '').trim();
        if (text) return text;
    }
    return '';
};

const normalizeJapanese = (value) => textOf(value)
    .replace(/[。、！？!?・]/g, '')
    .replace(/\s+/g, '');

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
    const normalized = asArray(tokens)
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

    return (
        <div className="flex flex-wrap items-end gap-x-2 gap-y-3 leading-relaxed">
            {groups.map((token, idx) => {
                const showRuby = showReading && shouldShowReading(token.surface, token.reading);
                return (
                    <span key={`${token.surface}-${idx}`} className="inline-flex flex-col items-center justify-end">
                        <span className={`mb-1 min-h-[1rem] whitespace-nowrap text-center text-sm font-black leading-none text-rose-500 ${showRuby ? 'opacity-100' : 'opacity-0'}`}>
                            {showRuby ? token.reading : '\u00A0'}
                        </span>
                        <span className={`${sizeClass} ${colorClass} whitespace-nowrap font-black leading-none tracking-normal ${token.highlight ? 'text-blue-600' : ''}`}>
                            {token.surface}{token.suffix}
                        </span>
                    </span>
                );
            })}
        </div>
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

function TextSection({ title, eyebrow, icon: Icon, items, showReading, showTranslation, playTextAudio, dialogue = false }) {
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
                    return (
                        <article key={`${title}-${idx}`} className="rounded-[1.5rem] border border-slate-100 bg-slate-50/70 p-5">
                            <div className="flex items-start gap-4">
                                {dialogue && (
                                    <span className="mt-8 min-w-16 text-sm font-black text-slate-400">
                                        {textOf(item.speaker, item.role) || idx + 1}
                                    </span>
                                )}
                                <div className="min-w-0 flex-1">
                                    <JapaneseText item={item} showReading={showReading} size={dialogue ? 'base' : 'small'} />
                                    {showTranslation && item.translation && (
                                        <p className="mt-2 text-lg font-bold text-slate-500">{item.translation}</p>
                                    )}
                                </div>
                                {playTextAudio && text && (
                                    <button
                                        type="button"
                                        onClick={() => playTextAudio(text, `ja-reference-${title}-${idx}`)}
                                        className="mt-7 rounded-2xl bg-white p-2.5 text-slate-400 shadow-sm transition hover:bg-slate-900 hover:text-white"
                                        aria-label="播放"
                                    >
                                        <Volume2 size={18} />
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

function VocabularyGroup({ title, eyebrow, items, showReading, showTranslation, playTextAudio }) {
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

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {items.map((item, idx) => {
                    const term = textOf(item.term, item.word);
                    const reading = textOf(item.reading, item.romaji);
                    const translation = textOf(item.translation, item.definition);
                    return (
                        <article key={`${title}-${term}-${idx}`} className="rounded-[1.5rem] border border-slate-100 bg-slate-50/70 p-5">
                            <div className="flex items-start justify-between gap-4">
                                <div className="min-w-0">
                                    <TermWithReading term={term} reading={reading} showReading={showReading} />
                                    {item.part_of_speech && (
                                        <p className="mt-1 text-xs font-black uppercase tracking-widest text-slate-400">
                                            {item.part_of_speech}
                                        </p>
                                    )}
                                    {showTranslation && translation && (
                                        <p className="mt-2 text-lg font-bold text-slate-600">{translation}</p>
                                    )}
                                </div>
                                {playTextAudio && term && (
                                    <button
                                        type="button"
                                        onClick={() => playTextAudio(term, `ja-vocab-${title}-${idx}`)}
                                        className="rounded-2xl bg-white p-2.5 text-slate-400 shadow-sm transition hover:bg-slate-900 hover:text-white"
                                        aria-label="播放"
                                    >
                                        <Volume2 size={18} />
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

export default function JapaneseLessonReference({
    courseContent = {},
    lessonMetadata = {},
    fadeInUp,
    playTextAudio,
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
                />
                <TextSection
                    title="例文"
                    eyebrow="Example Sentences"
                    icon={BookOpen}
                    items={examples}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                />
                <TextSection
                    title={dialogueTitle}
                    eyebrow="Dialogue"
                    icon={MessageSquareText}
                    items={dialogueLines}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                    dialogue
                />
                <VocabularyGroup
                    title="主线词汇"
                    eyebrow="Core Vocabulary"
                    items={coreVocab}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                />
                <VocabularyGroup
                    title="补充词汇"
                    eyebrow="Supplementary Vocabulary"
                    items={supplementaryVocab}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                />
                <VocabularyGroup
                    title="课文识别词"
                    eyebrow="Reference Names"
                    items={displayOnlyVocab}
                    showReading={showReading}
                    showTranslation={showTranslation}
                    playTextAudio={playTextAudio}
                />
            </div>
        </Wrapper>
    );
}
