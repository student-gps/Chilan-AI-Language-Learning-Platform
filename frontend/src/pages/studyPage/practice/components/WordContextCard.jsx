import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { BookOpen, Volume2 } from 'lucide-react';
import { claimGlobalAudio, releaseGlobalAudio } from '../../../../utils/audioPlayback';
import AnnotatedSentence from '../../components/AnnotatedSentence';

const formatPinyinDisplay = (value = '') =>
    value
        .split(/\s+/)
        .filter(Boolean)
        .map((token) => token.toLowerCase())
        .join(' ');

export default function WordContextCard({ word, pinyin, metadata, knowledgeData }) {
    const { t } = useTranslation();
    const examples = metadata?.context_examples || [];
    const fallbackKnowledge = metadata?.knowledge || {};
    const currentSense = knowledgeData?.current_sense || fallbackKnowledge;
    const history = knowledgeData?.other_senses || fallbackKnowledge?.history || [];
    const displayWord = knowledgeData?.word || currentSense?.word || word;
    const displayPinyin = knowledgeData?.pinyin || currentSense?.pinyin || pinyin;
    const displayDefinition = currentSense?.definition || '';
    const displayPartOfSpeech = currentSense?.part_of_speech || '';
    const primaryExample = currentSense?.example_sentence;
    const combinedExamples = [];
    const [showPinyin, setShowPinyin] = useState({});
    const [showTranslation, setShowTranslation] = useState({});

    if (primaryExample?.cn || primaryExample?.py || primaryExample?.translation) {
        combinedExamples.push(primaryExample);
    }
    examples.forEach((ex) => {
        if (!ex) return;
        const exists = combinedExamples.some((item) =>
            item?.cn === ex?.cn && item?.py === ex?.py && item?.translation === ex?.translation
        );
        if (!exists) combinedExamples.push(ex);
    });

    if (
        combinedExamples.length === 0 &&
        history.length === 0 &&
        !displayDefinition &&
        !displayWord
    ) return null;

    const playAudio = (text) => {
        if (!text) return;
        const API_BASE = import.meta.env.VITE_APP_API_BASE_URL;
        const audio = new Audio(`${API_BASE}/study/tts?text=${encodeURIComponent(text)}`);
        claimGlobalAudio(audio);
        audio.onpause = () => releaseGlobalAudio(audio);
        audio.onended = () => releaseGlobalAudio(audio);
        audio.onerror = () => releaseGlobalAudio(audio);
        audio.play().catch(() => releaseGlobalAudio(audio));
    };

    const togglePinyin = (key) => setShowPinyin((prev) => ({ ...prev, [key]: !prev[key] }));
    const toggleTranslation = (key) => setShowTranslation((prev) => ({ ...prev, [key]: !prev[key] }));

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-5 bg-slate-50/80 rounded-[2rem] border border-slate-200/50 p-7 text-left"
        >
            <div className="flex items-center gap-3 mb-5">
                <div className="p-2 bg-blue-50 rounded-xl">
                    <BookOpen className="text-blue-500" size={20} />
                </div>
                <h4 className="text-xl font-black text-slate-800 tracking-tight">{t('knowledge_title')}</h4>
                <div className="h-px flex-1 bg-slate-200/60" />
            </div>

            {(displayWord || displayDefinition) && (
                <div className="mb-5 bg-white/90 p-5 rounded-[1.75rem] border border-white shadow-sm">
                    <div className="mb-3">
                        <span className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 text-[11px] font-black uppercase tracking-[0.25em] text-blue-500">
                            {t('knowledge_current_sense')}
                        </span>
                    </div>
                    <div className="flex flex-wrap items-start gap-4 justify-between">
                        <div className="min-w-[180px]">
                            <div className="flex items-start gap-4">
                                <p className="text-5xl font-black text-slate-900 leading-none">{displayWord}</p>
                                <button
                                    onClick={() => playAudio(displayWord)}
                                    className="mt-1 p-2.5 bg-slate-50 text-slate-400 hover:bg-blue-600 hover:text-white rounded-2xl transition-all shadow-sm"
                                >
                                    <Volume2 size={18} />
                                </button>
                                <div className="pt-2">
                                    {displayPinyin && (
                                        <p className="text-lg font-black text-orange-500">{formatPinyinDisplay(displayPinyin)}</p>
                                    )}
                                    {displayPartOfSpeech && (
                                        <span className="inline-block mt-3 px-3 py-1 rounded-full bg-slate-100 text-xs font-black uppercase tracking-[0.2em] text-slate-500">
                                            {displayPartOfSpeech}
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>
                        {displayDefinition && (
                            <div className="flex-1 min-w-[220px]">
                                <p className="text-lg font-black text-slate-800 leading-snug">
                                    {displayDefinition}
                                </p>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="space-y-4">
                {combinedExamples.map((ex, idx) => {
                    const key = `current-${idx}`;
                    const pinyinOn = showPinyin[key];
                    const translationOn = showTranslation[key];
                    return (
                        <div key={idx} className="bg-white/80 p-5 rounded-2xl border border-white shadow-sm">
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1">
                                    {pinyinOn && ex.py ? (
                                        <AnnotatedSentence
                                            tokens={ex.tokens}
                                            cn={ex.cn}
                                            py={ex.py}
                                            showPinyin
                                            wrapperClassName="flex flex-wrap items-end gap-x-1 gap-y-3"
                                            tokenClassName="inline-flex flex-col items-center justify-end"
                                            pinyinClassName="mb-1 min-h-[0.9rem] text-xs font-bold text-slate-400 normal-case leading-none"
                                            textClassName="text-2xl font-black text-slate-800 leading-none"
                                        />
                                    ) : (
                                        <p className="text-2xl font-black text-slate-800 leading-tight">
                                            {ex.cn}
                                        </p>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 shrink-0">
                                    <button
                                        onClick={() => playAudio(ex.cn)}
                                        className="p-2 text-slate-300 hover:text-blue-600 transition-colors"
                                    >
                                        <Volume2 size={18} />
                                    </button>
                                    <button
                                        onClick={() => togglePinyin(key)}
                                        className={`px-3 py-2 rounded-xl text-xs font-black uppercase tracking-[0.18em] transition-colors ${pinyinOn ? 'bg-orange-100 text-orange-500' : 'bg-slate-100 text-slate-400 hover:bg-slate-200'}`}
                                    >
                                        {t('word_pinyin_btn')}
                                    </button>
                                    <button
                                        onClick={() => toggleTranslation(key)}
                                        className={`px-3 py-2 rounded-xl text-xs font-black uppercase tracking-[0.18em] transition-colors ${translationOn ? 'bg-blue-100 text-blue-500' : 'bg-slate-100 text-slate-400 hover:bg-slate-200'}`}
                                    >
                                        {t('word_translation_btn')}
                                    </button>
                                </div>
                            </div>
                            <AnimatePresence initial={false}>
                                {translationOn && ex.translation && (
                                    <motion.div
                                        initial={{ opacity: 0, height: 0 }}
                                        animate={{ opacity: 1, height: 'auto' }}
                                        exit={{ opacity: 0, height: 0 }}
                                        className="overflow-hidden"
                                    >
                                        <div className="mt-3 py-2 px-4 bg-blue-50/50 rounded-lg inline-block">
                                            <p className="text-base font-bold text-blue-600 italic leading-snug">
                                                {ex.translation}
                                            </p>
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    );
                })}
            </div>

            {history.length > 0 && (
                <div className="mt-6 pt-5 border-t border-slate-200/60">
                    <p className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] mb-4">
                        {t('knowledge_other_senses')}
                    </p>
                    <div className="space-y-3">
                        {history.map((h, i) => (
                            <div key={i} className="bg-white/80 p-4 rounded-2xl border border-white shadow-sm">
                                <div className="flex flex-wrap items-center gap-2 mb-2">
                                    {h.part_of_speech && (
                                        <span className="px-2.5 py-1 rounded-full bg-slate-100 text-[11px] font-black uppercase tracking-[0.2em] text-slate-500">
                                            {h.part_of_speech}
                                        </span>
                                    )}
                                    {h.pinyin && (
                                        <span className="text-sm font-bold text-orange-500">{h.pinyin}</span>
                                    )}
                                    {typeof h.lesson_id !== 'undefined' && h.lesson_id !== null && (
                                        <span className="text-xs font-black text-slate-400">L{h.lesson_id}</span>
                                    )}
                                </div>
                                <p className="text-base font-black text-slate-800 leading-snug">{h.definition}</p>
                                {h.example?.cn && (
                                    <div className="mt-3">
                                        <div className="flex items-start justify-between gap-4">
                                            <div className="flex-1">
                                                {showPinyin[`history-${i}`] && h.example?.py ? (
                                                    <AnnotatedSentence
                                                        tokens={h.example.tokens}
                                                        cn={h.example.cn}
                                                        py={h.example.py}
                                                        showPinyin
                                                        wrapperClassName="flex flex-wrap items-end gap-x-1 gap-y-2"
                                                        tokenClassName="inline-flex flex-col items-center justify-end"
                                                        pinyinClassName="mb-1 min-h-[0.75rem] text-[10px] font-bold text-slate-400 normal-case leading-none"
                                                        textClassName="text-sm font-bold text-slate-700 leading-none"
                                                    />
                                                ) : (
                                                    <p className="text-sm font-bold text-slate-700">{h.example.cn}</p>
                                                )}
                                            </div>
                                            <div className="flex items-center gap-2 shrink-0">
                                                <button
                                                    onClick={() => playAudio(h.example.cn)}
                                                    className="p-1.5 text-slate-300 hover:text-blue-600 transition-colors"
                                                >
                                                    <Volume2 size={16} />
                                                </button>
                                                <button
                                                    onClick={() => togglePinyin(`history-${i}`)}
                                                    className={`px-2.5 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-[0.16em] transition-colors ${showPinyin[`history-${i}`] ? 'bg-orange-100 text-orange-500' : 'bg-slate-100 text-slate-400 hover:bg-slate-200'}`}
                                                >
                                                    拼音
                                                </button>
                                                <button
                                                    onClick={() => toggleTranslation(`history-${i}`)}
                                                    className={`px-2.5 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-[0.16em] transition-colors ${showTranslation[`history-${i}`] ? 'bg-blue-100 text-blue-500' : 'bg-slate-100 text-slate-400 hover:bg-slate-200'}`}
                                                >
                                                    译
                                                </button>
                                            </div>
                                        </div>
                                        <AnimatePresence initial={false}>
                                            {showTranslation[`history-${i}`] && h.example?.translation && (
                                                <motion.div
                                                    initial={{ opacity: 0, height: 0 }}
                                                    animate={{ opacity: 1, height: 'auto' }}
                                                    exit={{ opacity: 0, height: 0 }}
                                                    className="overflow-hidden mt-2"
                                                >
                                                    <p className="text-sm font-semibold italic text-blue-600">{h.example.translation}</p>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </motion.div>
    );
}
