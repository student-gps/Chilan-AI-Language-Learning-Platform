import React from 'react';
import { motion } from 'framer-motion';
import { Loader2, Mic, Send, Square } from 'lucide-react';

export default function SpeechAnswerPanel({
    statusTone,
    isRecording,
    isTranscribing,
    recordAttempts,
    maxDurationSec,
    recordingSeconds,
    liveWaveform,
    speechPreviewText,
    speechInlineHint,
    onPrimaryAction,
    primaryLabel,
    primaryDisabled,
    showSubmit,
    onSubmit,
    submitDisabled,
    isEvaluating,
    primaryButtonRef,
    primaryButtonClass,
    secondaryButtonClass,
}) {
    return (
        <div className={`mb-6 rounded-[2.25rem] border p-5 md:p-6 shadow-inner shadow-white/70 ${statusTone || 'border-slate-200/70 bg-[linear-gradient(135deg,rgba(248,250,252,0.98),rgba(239,246,255,0.9))]'}`}>
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div className="flex items-start gap-4">
                    <div className={`mt-1 flex h-12 w-12 items-center justify-center rounded-2xl shadow-sm ${
                        isRecording
                            ? 'bg-red-100 text-red-600'
                            : isTranscribing
                                ? 'bg-blue-100 text-blue-600'
                                : 'bg-slate-900 text-white'
                    }`}>
                        {isRecording ? <Square size={18} /> : <Mic size={20} />}
                    </div>
                    <div>
                        <p className="text-xs font-black uppercase tracking-[0.24em] text-slate-400">
                            语音练习
                        </p>
                        <h3 className="mt-1 text-[28px] font-black tracking-tight text-slate-900">
                            先录音，再确认后提交
                        </h3>
                        <p className="mt-2 text-sm font-semibold text-slate-400">
                            已录 {recordAttempts} 次
                            <span className="mx-2 text-slate-300">/</span>
                            最长 {maxDurationSec} 秒
                        </p>
                    </div>
                </div>

                <div className="flex flex-wrap gap-2 md:justify-end">
                    <span className={`rounded-full px-3 py-1.5 text-[11px] font-black uppercase tracking-[0.18em] ${
                        isRecording
                            ? 'bg-red-100 text-red-600'
                            : isTranscribing
                                ? 'bg-blue-100 text-blue-600'
                                : 'bg-slate-200/70 text-slate-500'
                    }`}>
                        {isRecording ? '录音中' : isTranscribing ? '转写中' : '待开始'}
                    </span>
                </div>
            </div>

            <div className="mt-4 rounded-[1.9rem] border border-white/80 bg-white/90 px-5 py-4 shadow-sm">
                <div className="mb-4 flex items-center justify-end gap-4">
                    {isRecording && (
                        <p className="text-xs font-black uppercase tracking-[0.18em] text-red-500">
                            {recordingSeconds}s / {maxDurationSec}s
                        </p>
                    )}
                </div>

                <div className="mb-3 flex h-9 items-end justify-center gap-1.5">
                    {Array.from({ length: 18 }).map((_, idx) => {
                        const waveformValue = liveWaveform[idx] || 0;
                        const active = isRecording ? waveformValue > 0.01 : isTranscribing ? idx % 3 === 0 : idx < 4;
                        const height = isRecording
                            ? Math.max(2, Math.round(2 + waveformValue * 68))
                            : isTranscribing
                                ? 16 + ((idx * 5) % 14)
                                : 10;
                        return (
                            <span
                                key={idx}
                                className={`w-2 rounded-full transition-all duration-300 ${
                                    active
                                        ? isRecording
                                            ? 'bg-red-400'
                                            : isTranscribing
                                                ? 'bg-blue-400'
                                                : 'bg-slate-300'
                                        : 'bg-slate-200'
                                }`}
                                style={{ height: `${height}px` }}
                            />
                        );
                    })}
                </div>

                <p className={`min-h-12 text-center text-2xl font-bold leading-snug ${speechPreviewText ? 'text-slate-800' : 'text-slate-400'}`}>
                    {speechPreviewText}
                </p>

                {speechInlineHint && (
                    <div className={`mt-3 rounded-2xl border px-4 py-3 text-base font-bold ${speechInlineHint.tone}`}>
                        <div className="flex items-center justify-center gap-2 text-center">
                            {(isTranscribing || speechInlineHint.emphasis === 'warning') && (
                                <span className={`inline-block h-2.5 w-2.5 rounded-full ${isTranscribing ? 'bg-sky-400 animate-pulse' : 'bg-amber-400'}`} />
                            )}
                            <span>{speechInlineHint.text}</span>
                        </div>
                    </div>
                )}
            </div>

            <div className="mt-4 space-y-3">
                <button
                    ref={primaryButtonRef}
                    onClick={onPrimaryAction}
                    disabled={primaryDisabled}
                    className={`w-full py-5 rounded-[1.3rem] font-black text-xl transition-all flex items-center justify-center gap-3 shadow-lg ${primaryButtonClass} disabled:bg-slate-300`}
                >
                    {isRecording ? <Square size={20} /> : <Mic size={20} />}
                    {primaryLabel}
                </button>

                {showSubmit && (
                    <motion.button
                        whileTap={{ scale: 0.98 }}
                        onClick={onSubmit}
                        disabled={submitDisabled}
                        className={`w-full py-5 rounded-[1.35rem] font-black text-xl disabled:bg-slate-200 transition-all flex items-center justify-center gap-3 shadow-lg ${secondaryButtonClass}`}
                    >
                        {isEvaluating ? <Loader2 className="animate-spin" /> : <Send size={22} />}
                        {isEvaluating ? '正在判题...' : '提交本次回答'}
                    </motion.button>
                )}
            </div>
        </div>
    );
}
