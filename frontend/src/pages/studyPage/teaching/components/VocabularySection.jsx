import React from 'react';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Languages, Volume2, BookOpen } from 'lucide-react';
import AnnotatedSentence from '../../components/AnnotatedSentence';

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

export default function VocabularySection({
    fadeInUp,
    vocabulary,
    vocabPinyin,
    setVocabPinyin,
    vocabTrans,
    setVocabTrans,
    playTtsFallback,
    t,
}) {
    return (
        <motion.section variants={fadeInUp} initial="hidden" animate="show" className="mb-20">
            <div className="mb-8 flex items-end justify-between">
                <h2 className="text-2xl font-black text-slate-800">🔤 {t('teaching_vocab_title')}</h2>
                <ControlCapsule
                    pinyin={vocabPinyin}
                    setPinyin={setVocabPinyin}
                    trans={vocabTrans}
                    setTrans={setVocabTrans}
                    t={t}
                />
            </div>

            <div className="grid grid-cols-1 gap-6">
                {vocabulary?.map((vocab, idx) => (
                    <div
                        key={idx}
                        className="group rounded-[2.5rem] border border-slate-100 bg-white p-8 shadow-sm transition-all duration-500 hover:shadow-xl"
                    >
                        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-start">
                            <div className="flex items-start gap-5">
                                <span className="text-4xl font-black text-slate-900">{vocab.word}</span>
                                <button
                                    onClick={() => playTtsFallback(vocab.word, `vocab-${idx}`)}
                                    className="rounded-2xl bg-slate-50 p-2.5 text-slate-400 shadow-sm transition-all hover:bg-blue-600 hover:text-white"
                                >
                                    <Volume2 size={20} />
                                </button>
                                <div className="flex flex-col gap-1">
                                    <span className={`font-mono font-bold text-orange-600 transition-all duration-500 ${vocabPinyin ? 'opacity-100' : 'opacity-0'}`}>
                                        {vocab.pinyin}
                                    </span>
                                    <span className="self-start rounded-lg bg-slate-100 px-2 py-0.5 text-[10px] font-black uppercase tracking-widest text-slate-400">
                                        {vocab.part_of_speech}
                                    </span>
                                </div>
                            </div>
                            <div className={`transition-all duration-500 ${vocabTrans ? 'translate-x-0 opacity-100' : 'translate-x-4 opacity-0'}`}>
                                <span className="text-xl font-black text-slate-800">{vocab.definition}</span>
                            </div>
                        </div>

                        {vocab.example_sentence && (
                            <div className="mt-8 flex items-start gap-4 border-t border-slate-50 pt-6">
                                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-50">
                                    <span className="text-[10px] font-black text-slate-300">{t('teaching_example')}</span>
                                </div>
                                <div className="flex-1">
                                    <div className="mb-2 flex items-center gap-3">
                                        <AnnotatedSentence
                                            tokens={vocab.example_sentence.tokens}
                                            cn={vocab.example_sentence.cn}
                                            py={vocab.example_sentence.py}
                                            showPinyin={vocabPinyin}
                                            wrapperClassName="flex flex-wrap items-end gap-x-2 gap-y-3"
                                            tokenClassName="inline-flex flex-col items-center justify-end"
                                            pinyinClassName="mb-1 min-h-[1.1rem] text-sm font-mono font-bold text-slate-400 normal-case leading-none"
                                            textClassName="text-xl font-bold text-slate-800 leading-none"
                                        />
                                        <button
                                            onClick={() => playTtsFallback(vocab.example_sentence.cn, `example-${idx}`)}
                                            className="p-1.5 text-slate-300 transition-colors hover:text-blue-600"
                                        >
                                            <Volume2 size={18} />
                                        </button>
                                    </div>
                                    <p className={`text-sm font-medium italic text-slate-400 transition-all duration-500 ${vocabTrans ? 'opacity-100' : 'opacity-0'}`}>
                                        {vocab.example_sentence.translation}
                                    </p>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </motion.section>
    );
}
