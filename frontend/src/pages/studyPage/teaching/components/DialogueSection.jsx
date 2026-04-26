import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen, Eye, EyeOff, Languages, Volume2 } from 'lucide-react';

const normalizeLineRef = (value) => {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
};

// Punctuation that should be attached to the preceding word, never orphaned
const PUNCT_RE = /^[：。，！？、；,.!?…·—～]$/;

const InlineAnnotatedText = ({ words = [], showPinyin, pinyinClassName = '', textClassName = '' }) => {
    if (!showPinyin) {
        return (
            <div className={`leading-[1.95] ${textClassName}`}>
                {words.map((w, idx) => (
                    <span key={idx} className={w.highlight ? 'text-blue-600 font-black' : ''}>
                        {w.cn}
                    </span>
                ))}
            </div>
        );
    }

    // Attach trailing punctuation to the preceding word to prevent line-break orphans
    const groups = [];
    for (const w of words) {
        if (PUNCT_RE.test(w.cn) && groups.length > 0) {
            const last = groups[groups.length - 1];
            groups[groups.length - 1] = { ...last, suffix: (last.suffix || '') + w.cn };
        } else {
            groups.push({ ...w, suffix: '' });
        }
    }

    return (
        <div className="flex flex-wrap items-end gap-x-2 gap-y-4 leading-relaxed">
            {groups.map((w, idx) => (
                <ruby key={idx} className="flex flex-col items-center">
                    <rt className={pinyinClassName}>{w.py}</rt>
                    <span className={`${textClassName} ${w.highlight ? 'text-blue-600 font-black' : ''}`}>
                        {w.cn}{w.suffix}
                    </span>
                </ruby>
            ))}
        </div>
    );
};

function ControlCapsule({ pinyin, setPinyin, trans, setTrans, t }) {
    return (
        <div className="flex items-center gap-2 rounded-2xl border border-slate-200/50 bg-slate-100 p-1 shadow-inner">
            <button
                onClick={() => setPinyin(!pinyin)}
                className={`flex items-center gap-2 rounded-xl px-4 py-1.5 text-xs font-black transition-all duration-300 ${
                    pinyin ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400'
                }`}
            >
                {pinyin ? <Eye size={14} /> : <EyeOff size={14} />}
                {pinyin ? t('teaching_pinyin_on') : t('teaching_pinyin_off')}
            </button>
            <button
                onClick={() => setTrans(!trans)}
                className={`flex items-center gap-2 rounded-xl px-4 py-1.5 text-xs font-black transition-all duration-300 ${
                    trans ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400'
                }`}
            >
                {trans ? <Languages size={14} /> : <BookOpen size={14} />}
                {trans ? t('teaching_translation_on') : t('teaching_translation_off')}
            </button>
        </div>
    );
}

const renderAudioButton = ({ onClick, active, accent = 'slate', size = 20 }) => {
    const baseClass = active
        ? 'bg-blue-600 text-white shadow-lg'
        : accent === 'blue'
            ? 'text-blue-400 hover:text-blue-600'
            : 'text-slate-400 hover:text-blue-500';

    return (
        <button onClick={onClick} className={`rounded-2xl p-2 transition-all ${baseClass}`} title="播放音频">
            <Volume2 size={size} />
        </button>
    );
};

export default function DialogueSection({
    fadeInUp,
    lessonHeading,
    contentType,
    isReadingMode,
    lessonMetadata,
    lineItems,
    diagPinyin,
    setDiagPinyin,
    diagTrans,
    setDiagTrans,
    playingKey,
    activeLessonLineRef,
    playDialogueAudio,
    t,
}) {

    return (
        <motion.section variants={fadeInUp} initial="hidden" animate="show" className="mb-24">
            <div className="mb-8 flex items-end justify-between">
                <div>
                    <h2 className="text-2xl font-black text-slate-800">{lessonHeading}</h2>
                    <p className="mt-1 text-xs font-black uppercase tracking-[0.24em] text-slate-400">
                        {contentType}
                    </p>
                </div>
                <ControlCapsule
                    pinyin={diagPinyin}
                    setPinyin={setDiagPinyin}
                    trans={diagTrans}
                    setTrans={setDiagTrans}
                    t={t}
                />
            </div>

            <div className={`rounded-[3rem] border border-slate-100 bg-white shadow-sm ${isReadingMode ? 'p-3 md:p-4' : 'p-10 md:p-14'}`}>
                {isReadingMode ? (
                    <div className="mx-auto max-w-3xl overflow-hidden rounded-[2.5rem] border border-stone-200/80 bg-gradient-to-b from-stone-50 to-white shadow-[0_24px_60px_rgba(15,23,42,0.06)]">

                        {/* Passage header: title + type badge */}
                        <div className="flex items-start justify-between gap-4 px-6 pb-6 pt-8 md:px-10 md:pt-10">
                            <div>
                                <p className="text-[10px] font-black uppercase tracking-[0.36em] text-stone-400">
                                    {contentType === 'diary' ? t('teaching_diary_original') : t('teaching_reading')}
                                </p>
                                <h3 className="mt-3 text-3xl font-black tracking-tight text-stone-800 md:text-4xl">
                                    {lessonMetadata.title}
                                </h3>
                                {lessonMetadata.title_localized && (
                                    <p className="mt-1 text-base font-medium text-stone-400">
                                        {lessonMetadata.title_localized}
                                    </p>
                                )}
                            </div>
                            <div className="hidden shrink-0 items-center rounded-full border border-stone-200 bg-white/80 px-4 py-2 text-[10px] font-black uppercase tracking-[0.28em] text-stone-400 md:flex">
                                {contentType}
                            </div>
                        </div>

                        {/* Divider between header and body */}
                        <div className="mx-6 border-t border-stone-200/80 md:mx-10" />

                        {/* Letter / passage body — all lines uniform */}
                        <div className="space-y-8 px-6 pb-10 pt-7 md:px-10 md:pb-12">
                            {lineItems.map((line, idx) => {
                                const lineRef = idx + 1;
                                const cnText = (line.words || []).map(w => w.cn).join('');
                                const isActive = playingKey === `line-${lineRef}`;

                                return (
                                    <article key={idx} className="group">
                                        <div className="flex items-end gap-3">
                                            <div className="min-w-0 flex-1">
                                                <InlineAnnotatedText
                                                    words={line.words || []}
                                                    showPinyin={diagPinyin}
                                                    pinyinClassName="mb-1 text-sm font-mono text-stone-400 md:text-base"
                                                    textClassName="text-stone-800 text-3xl font-medium md:text-[2.15rem]"
                                                />
                                            </div>
                                            {renderAudioButton({
                                                onClick: () => playDialogueAudio({ lineRef, text: cnText }),
                                                active: isActive,
                                                accent: 'slate',
                                            })}
                                        </div>

                                        {diagTrans && line.translation && (
                                            <p className="mt-3 text-lg leading-relaxed text-stone-500 md:text-xl">
                                                {line.translation}
                                            </p>
                                        )}
                                    </article>
                                );
                            })}
                        </div>
                    </div>
                ) : (
                    <div className="space-y-7">
                        {lineItems.map((line, idx) => {
                            const isLeft = idx % 2 === 0;
                            const lineRef = idx + 1;
                            const cnText = (line.words || []).map((w) => w.cn).join('');
                            const isActive = playingKey === `line-${lineRef}`;
                            const isLessonActive = activeLessonLineRef === normalizeLineRef(lineRef);

                            return (
                                <div key={idx} className={`flex ${isLeft ? 'justify-start' : 'justify-end'}`}>
                                    <div className={`flex max-w-full items-start gap-3 ${isLeft ? 'flex-row' : 'flex-row-reverse'}`}>
                                        <span className={`pt-4 text-xl font-black uppercase tracking-[0.22em] transition-colors md:text-2xl ${
                                            isLessonActive ? (isLeft ? 'text-slate-500' : 'text-blue-500') : 'text-slate-300'
                                        }`}>
                                            {line.role}
                                        </span>

                                        <div className={`group relative max-w-[88%] rounded-[2.2rem] px-6 py-4 transition-all hover:shadow-lg ${
                                            isLessonActive
                                                ? isLeft
                                                    ? 'rounded-tl-none border border-slate-300 bg-slate-100 text-slate-900 shadow-lg shadow-slate-200/60'
                                                    : 'rounded-tr-none border border-blue-300 bg-blue-100 text-slate-900 shadow-lg shadow-blue-200/60'
                                                : isLeft
                                                    ? 'rounded-tl-none border border-slate-100 bg-slate-50 text-slate-800'
                                                    : 'rounded-tr-none border border-blue-100 bg-blue-50 text-slate-800'
                                        }`}>
                                            <div className="flex items-end gap-3">
                                                <div className="min-w-0 flex-1">
                                                    <InlineAnnotatedText
                                                        words={line.words || []}
                                                        showPinyin={diagPinyin}
                                                        pinyinClassName={`mb-1 text-xl font-mono ${
                                                            isLessonActive
                                                                ? isLeft ? 'text-slate-500' : 'text-blue-500'
                                                                : isLeft ? 'text-slate-400' : 'text-blue-400'
                                                        }`}
                                                        textClassName="text-3xl font-medium"
                                                    />
                                                </div>

                                                {renderAudioButton({
                                                    onClick: () => playDialogueAudio({ lineRef, text: cnText }),
                                                    active: isActive,
                                                    accent: isLeft ? 'slate' : 'blue'
                                                })}
                                            </div>

                                            {diagTrans && line.translation && (
                                                <p className={`mt-4 border-t pt-3 text-xl ${
                                                    isLessonActive
                                                        ? isLeft ? 'border-slate-300/70 text-slate-600' : 'border-blue-300/70 text-blue-800/80'
                                                        : isLeft ? 'border-slate-200/60 text-slate-500' : 'border-blue-200/60 text-blue-700/70'
                                                }`}>
                                                    {line.translation}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </motion.section>
    );
}
