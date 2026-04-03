import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles } from 'lucide-react';

export default function AIThinkingIndicator({ label = 'AI 导师正在分析你的回答...' }) {
    return (
        <div className="rounded-[2rem] border border-slate-200 bg-slate-50/70 px-6 py-5">
            <div className="flex items-center gap-4">
                <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl border border-blue-100 bg-[linear-gradient(135deg,rgba(239,246,255,0.95),rgba(219,234,254,0.95))] shadow-sm shadow-blue-100/80">
                    <motion.div
                        animate={{ scale: [0.92, 1.08, 0.92], rotate: [0, 10, -10, 0] }}
                        transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
                        className="flex items-center justify-center"
                    >
                        <Sparkles size={20} className="text-blue-500" />
                    </motion.div>
                    <motion.span
                        animate={{ scale: [0.8, 1.35, 0.8], opacity: [0.22, 0.55, 0.22] }}
                        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
                        className="absolute inset-0 rounded-2xl border border-blue-200/80"
                    />
                </div>

                <div className="flex-1">
                    <p className="text-sm font-black uppercase tracking-[0.22em] text-slate-400">AI FEEDBACK</p>
                    <div className="mt-2 flex items-center gap-3">
                        <p className="text-lg font-bold text-slate-700">{label}</p>
                        <div className="flex items-center gap-1.5">
                            {[0, 1, 2].map((dot) => (
                                <motion.span
                                    key={dot}
                                    animate={{ y: [0, -4, 0], opacity: [0.35, 1, 0.35] }}
                                    transition={{ duration: 0.9, repeat: Infinity, delay: dot * 0.14, ease: 'easeInOut' }}
                                    className="h-2 w-2 rounded-full bg-blue-400"
                                />
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
