import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, BookOpen, Volume2, ArrowRight } from 'lucide-react';

const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 120, damping: 20 } }
};

const formatLessonId = (id) => {
    const numId = parseInt(id, 10);
    return numId < 100 ? id : `${Math.floor(numId / 100)}.${numId % 100}`;
};

export default function TeachingSection({ data, onStartPractice }) {
    const [showPinyin, setShowPinyin] = useState(true);
    const [showTrans, setShowTrans] = useState(true);

    if (!data) return null;
    const { lesson_metadata, course_content, aigc_visual_prompt } = data;

    const playAudio = (text) => {
        const audio = new Audio(`http://127.0.0.1:8000/study/tts?text=${encodeURIComponent(text)}`);
        audio.play().catch(e => console.error(e));
    };

    return (
        <div className="max-w-4xl mx-auto px-6">
            {/* 顶部标题与标签 */}
            <motion.div variants={fadeInUp} className="flex items-center gap-3 mb-4">
                <span className="px-3 py-1 bg-blue-600 text-white text-xs font-bold rounded-full uppercase tracking-widest">New Lesson</span>
                <span className="text-slate-400 font-mono font-bold">L{formatLessonId(lesson_metadata.lesson_id)}</span>
            </motion.div>
            <motion.h1 variants={fadeInUp} className="text-4xl font-black text-slate-800 mb-8">{lesson_metadata.title}</motion.h1>

            {/* 视频位 */}
            <motion.div variants={fadeInUp} className="w-full aspect-video bg-slate-900 rounded-3xl flex flex-col items-center justify-center mb-12 shadow-2xl relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10"></div>
                <p className="text-white z-20 font-bold tracking-widest opacity-50 mb-2">🎬 VIDEO GENERATION (VEO)</p>
                <p className="text-slate-400 z-20 text-sm max-w-lg text-center px-4 italic line-clamp-2">Prompt: "{aigc_visual_prompt}"</p>
            </motion.div>

            {/* 课文对话 */}
            <motion.section variants={fadeInUp} className="mb-12">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-2xl font-black">💬 课文对话</h2>
                    <div className="flex gap-2">
                        <button onClick={() => setShowPinyin(!showPinyin)} className={`p-2 rounded-lg transition ${showPinyin ? 'bg-blue-100 text-blue-600' : 'bg-white border border-slate-200 text-slate-400'}`}><Eye size={20} /></button>
                        <button onClick={() => setShowTrans(!showTrans)} className={`p-2 rounded-lg transition ${showTrans ? 'bg-indigo-100 text-indigo-600' : 'bg-white border border-slate-200 text-slate-400'}`}><BookOpen size={20} /></button>
                    </div>
                </div>
                <div className="flex flex-col gap-6 bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
                    {course_content.dialogues?.flatMap(t => t.lines || []).map((line, idx) => (
                        <div key={idx} className={`flex flex-col ${idx % 2 === 0 ? 'items-start' : 'items-end'}`}>
                            <div className={`px-5 py-4 rounded-3xl max-w-[85%] group ${idx % 2 === 0 ? 'bg-slate-50 border border-slate-100' : 'bg-blue-50/80 border border-blue-100'}`}>
                                <div className="flex items-end flex-wrap gap-x-1 gap-y-2">
                                    {line.words?.map((w, wIdx) => (
                                        <ruby key={wIdx} className="flex flex-col items-center">
                                            <rt className={`text-xs font-mono text-slate-400 mb-1 transition-opacity ${showPinyin ? 'opacity-100' : 'opacity-0'}`}>{w.py}</rt>
                                            <span className={`text-xl ${w.highlight ? 'text-blue-600 font-black' : 'text-slate-800'}`}>{w.cn}</span>
                                        </ruby>
                                    ))}
                                    <button onClick={() => playAudio(line.words.map(w=>w.cn).join(''))} className="p-1 text-slate-300 hover:text-blue-500"><Volume2 size={18} /></button>
                                </div>
                                {showTrans && <p className="text-sm text-slate-500 italic mt-2 border-t border-slate-200/50 pt-2">{line.english}</p>}
                            </div>
                        </div>
                    ))}
                </div>
            </motion.section>

            <motion.div variants={fadeInUp} className="flex justify-end pb-12">
                <button onClick={onStartPractice} className="px-8 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-700 transition shadow-lg flex items-center gap-2">
                    学完了，去练一练 <ArrowRight size={20} />
                </button>
            </motion.div>
        </div>
    );
}