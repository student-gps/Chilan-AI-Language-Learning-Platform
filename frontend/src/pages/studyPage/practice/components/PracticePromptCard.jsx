import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Volume2, Headphones, RotateCcw, Languages, Mic } from 'lucide-react';

const THEMES = {
    CN_TO_EN: {
        badgeBg: 'bg-blue-100', badgeText: 'text-blue-700',
        label: 'Translate · 中→英', Icon: Languages, promptColor: 'text-blue-500',
    },
    EN_TO_CN: {
        badgeBg: 'bg-emerald-100', badgeText: 'text-emerald-700',
        label: 'Translate · 英→中', Icon: Languages, promptColor: 'text-emerald-500',
    },
    EN_TO_CN_SPEAK: {
        badgeBg: 'bg-rose-100', badgeText: 'text-rose-700',
        label: 'Speaking · 口语', Icon: Mic, promptColor: 'text-rose-500',
    },
    CN_LISTEN_WRITE: {
        badgeBg: 'bg-indigo-100', badgeText: 'text-indigo-700',
        label: 'Dictation · 听写', Icon: Headphones, promptColor: 'text-indigo-500',
        btnActive: 'bg-indigo-700 shadow-indigo-300 scale-105',
        btnIdle: 'bg-indigo-600 hover:bg-indigo-700 shadow-indigo-200',
        ping: 'bg-indigo-400',
    },
};

export default function PracticePromptCard({ fadeInUp, promptLabel, originalText, questionType, onPlayAudio }) {
    const [playCount, setPlayCount] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);

    const theme = THEMES[questionType] ?? THEMES.CN_TO_EN;
    const isListenWrite = questionType === 'CN_LISTEN_WRITE';

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
                {/* Badge */}
                <div className={`inline-flex items-center gap-2 px-4 py-1.5 ${theme.badgeBg} rounded-full mb-6`}>
                    <theme.Icon size={15} className={theme.badgeText} />
                    <span className={`text-xs font-black ${theme.badgeText} uppercase tracking-widest`}>{theme.label}</span>
                </div>

                {/* Big circular play button */}
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
                            {playCount === 0 ? '播放' : '重播'}
                        </span>
                    </button>

                    {playCount > 0 && (
                        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-medium">
                            <RotateCcw size={11} />
                            已播放 {playCount} 次 · 可重复播放
                        </div>
                    )}

                    <div className="flex items-center gap-1.5">
                        <kbd className="px-1.5 py-0.5 rounded border border-slate-200 bg-white text-[10px] font-mono text-slate-400 shadow-sm">↑</kbd>
                        <span className="text-xs text-slate-400">重播</span>
                    </div>

                    <p className="text-base text-slate-500 font-medium">
                        听后用<strong className="text-slate-700">汉字</strong>写出你听到的句子
                    </p>
                </div>
            </motion.div>
        );
    }

    return (
        <motion.div variants={fadeInUp} initial="hidden" animate="show" className="text-center mb-8">
            {/* Badge */}
            <div className={`inline-flex items-center gap-2 px-4 py-1.5 ${theme.badgeBg} rounded-full mb-4`}>
                <theme.Icon size={15} className={theme.badgeText} />
                <span className={`text-xs font-black ${theme.badgeText} uppercase tracking-widest`}>{theme.label}</span>
            </div>

            <p className="text-4xl md:text-5xl font-black text-slate-900 leading-tight px-4">
                "{originalText}"
            </p>
            {onPlayAudio && (
                <p className="mt-3 text-sm text-slate-400">按 <kbd className="px-1.5 py-0.5 rounded border border-slate-300 bg-slate-100 text-xs font-mono text-slate-500">↑</kbd> 键重播</p>
            )}
        </motion.div>
    );
}
