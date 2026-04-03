import React from 'react';
import { motion } from 'framer-motion';

export default function PracticePromptCard({ fadeInUp, speechMode, promptLabel, originalText }) {
    return (
        <motion.div variants={fadeInUp} initial="hidden" animate="show" className="text-center mb-8">
            <span className="text-xl font-bold text-blue-500 uppercase tracking-[0.3em] block mb-1">
                {speechMode ? '请用中文作答' : promptLabel}
            </span>
            <p className="text-4xl md:text-5xl font-black text-slate-900 leading-tight px-4">
                “{originalText}”
            </p>
        </motion.div>
    );
}
