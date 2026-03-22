import React, { useState } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Eye, EyeOff, Volume2, ArrowRight, Languages, BookOpen, Loader2 } from 'lucide-react';

const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 120, damping: 20 } }
};

const formatLessonId = (id) => {
    const numId = parseInt(id, 10);
    return numId < 100 ? id : `${Math.floor(numId / 100)}.${numId % 100}`;
};

export default function TeachingSection({ data, courseId, userId, onStartPractice }) {
    // 1. 状态拆分：课文专用
    const [diagPinyin, setDiagPinyin] = useState(true);
    const [diagTrans, setDiagTrans] = useState(true);

    // 2. 状态拆分：生词专用
    const [vocabPinyin, setVocabPinyin] = useState(true);
    const [vocabTrans, setVocabTrans] = useState(true);

    // 新增状态：处理打书签的加载中状态
    const [isSaving, setIsSaving] = useState(false);

    if (!data) return null;
    const { lesson_metadata, course_content, aigc_visual_prompt } = data;
    const { dialogues, vocabulary } = course_content;

    const playAudio = (text) => {
        if (!text) return;
        new Audio(`http://127.0.0.1:8000/study/tts?text=${encodeURIComponent(text)}`).play();
    };

    // 3. 通用控制组件：接收 props 实现局部控制
    const ControlCapsule = ({ pinyin, setPinyin, trans, setTrans }) => (
        <div className="flex items-center gap-2 p-1 bg-slate-100 rounded-2xl border border-slate-200/50 shadow-inner">
            <button 
                onClick={() => setPinyin(!pinyin)} 
                className={`flex items-center gap-2 px-4 py-1.5 rounded-xl text-xs font-black transition-all duration-300 ${
                    pinyin ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400'
                }`}
            >
                {pinyin ? <Eye size={14} /> : <EyeOff size={14} />}
                {pinyin ? '拼音开' : '拼音关'}
            </button>
            <button 
                onClick={() => setTrans(!trans)} 
                className={`flex items-center gap-2 px-4 py-1.5 rounded-xl text-xs font-black transition-all duration-300 ${
                    trans ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400'
                }`}
            >
                {trans ? <Languages size={14} /> : <BookOpen size={14} />}
                {trans ? '翻译开' : '翻译关'}
            </button>
        </div>
    );

    // 打书签逻辑
    const handleStartPracticeClick = async () => {
        if (isSaving) return;
        setIsSaving(true);
        try {
            await axios.post('http://127.0.0.1:8000/study/content_viewed', {
                user_id: userId,
                course_id: courseId,
                lesson_id: lesson_metadata.lesson_id
            });
        } catch (error) {
            console.error("记录阅读进度失败:", error);
        } finally {
            setIsSaving(false);
            onStartPractice(); 
        }
    };

    return (
        <div className="max-w-4xl mx-auto px-6 pt-24">
            {/* 顶部页眉 */}
            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="flex items-center gap-3 mb-4">
                <span className="px-3 py-1 bg-slate-900 text-white text-[10px] font-black rounded-full uppercase tracking-widest">New Unit</span>
                <span className="text-slate-400 font-mono font-bold text-sm">LEVEL {formatLessonId(lesson_metadata.lesson_id)}</span>
            </motion.div>
            
            <h1 className="text-5xl font-black text-slate-900 mb-12 tracking-tight">
                {lesson_metadata.title}
            </h1>

            {/* 视频区 */}
            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="w-full aspect-video bg-slate-900 rounded-[2.5rem] flex flex-col items-center justify-center mb-16 shadow-2xl relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent z-10"></div>
                <div className="z-20 text-center">
                    <div className="w-16 h-16 bg-white/10 backdrop-blur-xl rounded-full flex items-center justify-center mx-auto mb-4 border border-white/20 group-hover:scale-110 transition-transform">
                        <div className="w-0 h-0 border-t-[10px] border-t-transparent border-l-[18px] border-l-white border-b-[10px] border-b-transparent ml-1"></div>
                    </div>
                    <p className="text-white/40 text-[10px] font-black tracking-[0.4em] uppercase">Visual Context Engine</p>
                </div>
                <p className="absolute bottom-6 left-10 right-10 text-white/60 text-sm italic font-light opacity-0 group-hover:opacity-100 transition-all duration-700">
                    "{aigc_visual_prompt}"
                </p>
            </motion.div>

            {/* 4. 课文对话区 (使用全新清爽蓝配色) */}
            <motion.section variants={fadeInUp} initial="hidden" animate="show" className="mb-24">
                <div className="flex justify-between items-end mb-8">
                    <h2 className="text-2xl font-black text-slate-800">💬 课文对话</h2>
                    <ControlCapsule 
                        pinyin={diagPinyin} setPinyin={setDiagPinyin} 
                        trans={diagTrans} setTrans={setDiagTrans} 
                    />
                </div>

                <div className="space-y-10 bg-white p-10 md:p-14 rounded-[3rem] shadow-sm border border-slate-100">
                    {dialogues?.flatMap(t => t.lines || []).map((line, idx) => {
                        const isLeft = idx % 2 === 0;
                        return (
                            <div key={idx} className={`flex flex-col ${isLeft ? 'items-start' : 'items-end'}`}>
                                <span className="text-2xl font-black text-slate-300 mb-2 px-4 uppercase tracking-widest">{line.role}</span>
                                
                                <div className={`px-7 py-5 rounded-[2.2rem] max-w-[85%] group relative transition-all hover:shadow-lg ${
                                    isLeft 
                                        ? 'bg-slate-50 border border-slate-100 rounded-tl-none text-slate-800' 
                                        : 'bg-blue-50 border border-blue-100 rounded-tr-none text-slate-800'
                                }`}>
                                    <div className="flex items-end flex-wrap gap-x-2 gap-y-4">
                                        {line.words?.map((w, wIdx) => (
                                            <ruby key={wIdx} className="flex flex-col items-center">
                                                <rt className={`text-xl font-mono mb-1 transition-all duration-500 ${
                                                    diagPinyin ? 'opacity-100' : 'opacity-0 h-0 overflow-hidden'
                                                } ${isLeft ? 'text-slate-400' : 'text-blue-400'}`}>{w.py}</rt>
                                                
                                                <span className={`text-3xl ${
                                                    w.highlight 
                                                        ? 'text-blue-600 font-black' 
                                                        : 'font-medium'
                                                }`}>{w.cn}</span>
                                            </ruby>
                                        ))}
                                        
                                        <button onClick={() => playAudio(line.words.map(w=>w.cn).join(''))} 
                                            className={`p-2 ml-2 transition-colors ${
                                                isLeft ? 'text-slate-400 hover:text-blue-500' : 'text-blue-400 hover:text-blue-600'
                                            }`}>
                                            <Volume2 size={20} />
                                        </button>
                                    </div>
                                    
                                    {diagTrans && line.english && (
                                        <p className={`text-xl mt-5 pt-4 border-t ${
                                            isLeft 
                                                ? 'text-slate-500 border-slate-200/60' 
                                                : 'text-blue-700/70 border-blue-200/60'
                                        }`}>
                                            {line.english}
                                        </p>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </motion.section>

            {/* 5. 生词区 */}
            <motion.section variants={fadeInUp} initial="hidden" animate="show" className="mb-20">
                <div className="flex justify-between items-end mb-8">
                    <h2 className="text-2xl font-black text-slate-800">🔤 本课生词</h2>
                    <ControlCapsule 
                        pinyin={vocabPinyin} setPinyin={setVocabPinyin} 
                        trans={vocabTrans} setTrans={setVocabTrans} 
                    />
                </div>
                
                <div className="grid grid-cols-1 gap-6">
                    {vocabulary?.map((vocab, idx) => (
                        <div key={idx} className="group p-8 bg-white border border-slate-100 rounded-[2.5rem] shadow-sm hover:shadow-xl transition-all duration-500">
                            <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
                                <div className="flex items-start gap-5">
                                    <span className="text-4xl font-black text-slate-900">{vocab.word}</span>
                                    <button onClick={() => playAudio(vocab.word)} className="p-2.5 bg-slate-50 text-slate-400 hover:bg-blue-600 hover:text-white rounded-2xl transition-all shadow-sm">
                                        <Volume2 size={20} />
                                    </button>
                                    <div className="flex flex-col gap-1">
                                        <span className={`text-orange-600 font-mono font-bold transition-all duration-500 ${vocabPinyin ? 'opacity-100' : 'opacity-0'}`}>
                                            {vocab.pinyin}
                                        </span>
                                        <span className="text-[10px] bg-slate-100 text-slate-400 px-2 py-0.5 rounded-lg uppercase font-black tracking-widest self-start">
                                            {vocab.part_of_speech}
                                        </span>
                                    </div>
                                </div>
                                <div className={`transition-all duration-500 ${vocabTrans ? 'opacity-100' : 'opacity-0 translate-x-4'}`}>
                                    <span className="text-xl text-slate-800 font-black">{vocab.definition}</span>
                                </div>
                            </div>

                            {/* 例句部分 */}
                            {vocab.example_sentence && (
                                <div className="mt-8 pt-6 border-t border-slate-50 flex items-start gap-4">
                                    <div className="w-8 h-8 rounded-xl bg-slate-50 flex items-center justify-center shrink-0">
                                        <span className="text-[10px] font-black text-slate-300">EX</span>
                                    </div>
                                    <div className="flex-1">
                                        <p className={`text-sm text-slate-400 font-mono mb-1 transition-all duration-500 ${vocabPinyin ? 'opacity-100' : 'opacity-0'}`}>
                                            {vocab.example_sentence.py}
                                        </p>
                                        <div className="flex items-center gap-3 mb-2">
                                            <p className="text-xl text-slate-800 font-bold tracking-wide">{vocab.example_sentence.cn}</p>
                                            <button onClick={() => playAudio(vocab.example_sentence.cn)} className="p-1.5 text-slate-300 hover:text-blue-600 transition-colors">
                                                <Volume2 size={18} />
                                            </button>
                                        </div>
                                        <p className={`text-sm text-slate-400 italic font-medium transition-all duration-500 ${vocabTrans ? 'opacity-100' : 'opacity-0'}`}>
                                            {vocab.example_sentence.en}
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </motion.section>

            {/* 6. 底部按钮 */}
            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="flex justify-center pt-8 pb-24">
                <button 
                    onClick={handleStartPracticeClick} 
                    disabled={isSaving}
                    className="px-14 py-5 bg-slate-900 text-white font-black text-lg rounded-[2rem] hover:bg-blue-600 disabled:bg-slate-400 disabled:hover:translate-y-0 transition-all shadow-xl hover:-translate-y-1 flex items-center gap-4"
                >
                    {isSaving ? (
                        <>正在生成测验... <Loader2 className="animate-spin" size={22} /></>
                    ) : (
                        <>完成学习，进入测验 <ArrowRight size={22} /></>
                    )}
                </button>
            </motion.div>
        </div>
    );
}