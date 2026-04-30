import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Volume2, Headphones, RotateCcw, Languages, Mic } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { getQuestionContext, getQuestionTypeConfig } from '../questionTypeConfig';

const ICONS_BY_MODE = {
    listen_write: Headphones,
    pattern: Languages,
    speech: Mic,
    text: Languages,
};

export default function PracticePromptCard({
    fadeInUp,
    originalText,
    questionType,
    currentQuestion,
    promptLabel,
    onPlayAudio,
}) {
    const { t } = useTranslation();
    const [playCount, setPlayCount] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);

    const config = getQuestionTypeConfig(currentQuestion || { question_type: questionType });
    const theme = config.theme;
    const context = getQuestionContext(currentQuestion);
    const isListenWrite = config.promptMode === 'listen_write';
    const Icon = config.answerMode === 'speech'
        ? Mic
        : ICONS_BY_MODE[config.promptMode] || ICONS_BY_MODE[config.answerMode] || Languages;
    const badgeLabel = config.badgeLabel || t(config.badgeKey);

    const handlePlay = () => {
        if (!onPlayAudio) return;
        onPlayAudio();
        setPlayCount(c => c + 1);
        setIsPlaying(true);
        setTimeout(() => setIsPlaying(false), 2200);
    };

    if (isListenWrite) {
        return (
            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="text-center mb-8">
                <div className={`inline-flex items-center gap-2 px-4 py-1.5 ${theme.badgeBg} rounded-full mb-6`}>
                    <Icon size={15} className={theme.badgeText} />
                    <span className={`text-xs font-black ${theme.badgeText} uppercase tracking-widest`}>{badgeLabel}</span>
                </div>

                <div className="flex flex-col items-center gap-5">
                    <button
                        onClick={handlePlay}
                        className={`relative w-28 h-28 rounded-full flex flex-col items-center justify-center gap-1.5 shadow-2xl transition-all active:scale-95 ${
                            isPlaying ? theme.btnActive : theme.btnIdle
                        }`}
                    >
                        {isPlaying && (
                            <span className={`absolute inset-0 rounded-full animate-ping ${theme.ping} opacity-30`} />
                        )}
                        <Volume2 size={36} className="text-white relative z-10" />
                        <span className="text-xs font-black text-indigo-200 relative z-10 tracking-wide">
                            {playCount === 0 ? t('practice_audio_play') : t('practice_audio_replay')}
                        </span>
                    </button>

                    {playCount > 0 && (
                        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
                            <RotateCcw size={11} />
                            {t('practice_audio_played_times', { count: playCount })}
                        </div>
                    )}

                    <div className="flex items-center gap-1.5">
                        <kbd className="px-1.5 py-0.5 rounded border border-slate-200 bg-white text-[10px] font-mono text-slate-400 shadow-sm">↑</kbd>
                        <span className="text-xs text-slate-400">{t('practice_audio_replay')}</span>
                    </div>

                    <p className="text-base text-slate-500 font-medium">
                        {promptLabel || t('practice_dictation_instruction')}
                    </p>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div variants={fadeInUp} initial="hidden" animate="show" className="text-center mb-8">
            <div className={`inline-flex items-center gap-2 px-4 py-1.5 ${theme.badgeBg} rounded-full mb-4`}>
                <Icon size={15} className={theme.badgeText} />
                <span className={`text-xs font-black ${theme.badgeText} uppercase tracking-widest`}>{badgeLabel}</span>
            </div>

            {config.promptMode === 'pattern' && context?.pattern && (
                <div className="mx-auto mb-5 max-w-2xl rounded-[1.5rem] border border-amber-100 bg-amber-50 px-5 py-4 text-left">
                    <p className="text-[11px] font-black uppercase tracking-[0.22em] text-amber-700">Pattern</p>
                    <p className="mt-1 text-2xl font-black text-amber-950">
                        {context.pattern.replace('{item}', context.slot || 'item')}
                    </p>
                </div>
            )}

            <div className="flex items-center justify-center gap-3 px-4">
                <p className="text-4xl md:text-5xl font-black text-slate-900 leading-tight">
                    "{originalText}"
                </p>
                {onPlayAudio && (
                    <button
                        type="button"
                        onClick={handlePlay}
                        className="mt-1 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white text-slate-500 shadow-sm ring-1 ring-slate-200 transition hover:bg-slate-900 hover:text-white"
                        aria-label="Play prompt audio"
                    >
                        <Volume2 size={22} />
                    </button>
                )}
            </div>
            {onPlayAudio && (
                <p className="mt-3 text-sm text-slate-400">{t('practice_replay_hint')}</p>
            )}
        </motion.div>
    );
}
