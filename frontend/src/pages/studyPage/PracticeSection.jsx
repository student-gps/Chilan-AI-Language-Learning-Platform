import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { 
    Loader2, Send, CheckCircle2, XCircle, 
    Sparkles, RefreshCcw, ArrowRight, AlertCircle 
} from 'lucide-react';

const fadeInUp = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 20 } }
};

export default function PracticeSection({ questions, isReview, onAllDone }) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState('');
    const [lastSubmittedAnswer, setLastSubmittedAnswer] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [isFocused, setIsFocused] = useState(false);
    
    const inputRef = useRef(null);
    const currentQuestion = questions[currentIndex];

    // 辅助函数：根据 Level 获取样式配置
    const getFeedbackConfig = (level) => {
        if (level === 4) {
            return {
                card: 'bg-green-50/50 border-green-100',
                titleColor: 'text-green-800',
                msgColor: 'text-green-700/90',
                icon: <CheckCircle2 className="text-green-500 shrink-0" size={32} />,
                title: '优秀！'
            };
        }
        if (level === 2 || level === 3) {
            return {
                card: 'bg-amber-50/50 border-amber-100',
                titleColor: 'text-amber-800',
                msgColor: 'text-amber-700',
                icon: <AlertCircle className="text-amber-500 shrink-0" size={32} />,
                title: '不错，但还有提升空间！'
            };
        }
        return {
            card: 'bg-red-50/50 border-red-100',
            titleColor: 'text-red-800',
            msgColor: 'text-red-700',
            icon: <XCircle className="text-red-500 shrink-0" size={32} />,
            title: '需要继续努力！'
        };
    };

    const focusAndMoveCursorToEnd = () => {
        if (inputRef.current) {
            const len = userAnswer.length;
            inputRef.current.focus();
            inputRef.current.setSelectionRange(len, len);
        }
    };

    useEffect(() => {
        if (!feedback && !isEvaluating && inputRef.current) {
            const timer = setTimeout(() => { focusAndMoveCursorToEnd(); }, 100);
            return () => clearTimeout(timer);
        }
        if (feedback && feedback.level === 1 && !isEvaluating) {
            focusAndMoveCursorToEnd();
        }
    }, [currentIndex, feedback, isEvaluating]);

    // 键盘逻辑：Level 2, 3, 4 均视为“过关”，按 Enter 进入下一题
    useEffect(() => {
        const handleEnter = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                if (feedback && feedback.level >= 2) {
                    e.preventDefault();
                    handleNext();
                    return;
                }
                if (document.activeElement === inputRef.current) {
                    e.preventDefault();
                    if (feedback && feedback.level === 1) {
                        if (userAnswer.trim() !== lastSubmittedAnswer) handleSubmit();
                    } else if (userAnswer.trim() && !isEvaluating) {
                        handleSubmit();
                    }
                }
            }
        };
        window.addEventListener('keydown', handleEnter);
        return () => window.removeEventListener('keydown', handleEnter);
    }, [userAnswer, feedback, isEvaluating, lastSubmittedAnswer]);

    const handleSubmit = async () => {
        if (isEvaluating) return;
        setIsEvaluating(true);
        try {
            const res = await axios.post(`http://127.0.0.1:8000/study/evaluate`, {
                user_id: localStorage.getItem('chilan_user_id') || 'test-user-id',
                lesson_id: currentQuestion.lesson_id || 101,
                question_id: currentQuestion.question_id,
                question_type: currentQuestion.question_type,
                original_text: currentQuestion.original_text,
                standard_answers: Array.isArray(currentQuestion.standard_answers) ? currentQuestion.standard_answers : [currentQuestion.standard_answers],
                user_answer: userAnswer
            });
            setFeedback(res.data.data);
            setLastSubmittedAnswer(userAnswer);
        } catch (e) {
            setFeedback({ level: 1, isCorrect: false, message: "判题服务连接失败，请重试。" });
        } finally {
            setIsEvaluating(false);
        }
    };

    const handleNext = () => {
        if (currentIndex < questions.length - 1) {
            setCurrentIndex(prev => prev + 1);
            setUserAnswer('');
            setLastSubmittedAnswer('');
            setFeedback(null);
        } else {
            onAllDone();
        }
    };

    if (!currentQuestion) return null;

    const isResubmitDisabled = isEvaluating || !userAnswer.trim() || (feedback && feedback.level === 1 && userAnswer === lastSubmittedAnswer);
    const config = feedback ? getFeedbackConfig(feedback.level) : null;

    return (
        <div className="max-w-4xl mx-auto px-6 pt-20 pb-0">
            
            {/* 顶部标题与进度 - 保持 font-black */}
            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="flex items-center justify-center gap-5 mb-8">
                <div className="flex items-center gap-3">
                    <Sparkles className="text-blue-500" size={28} />
                    <h1 className="text-5xl font-black text-slate-900 tracking-tight">
                        {isReview ? "智能巩固复习" : "随堂强化练习"}
                    </h1>
                </div>
                <div className="px-5 py-1.5 bg-slate-200/50 rounded-full text-xl font-black text-slate-500 tracking-tighter">
                    {currentIndex + 1} / {questions.length}
                </div>
            </motion.div>

            {/* 题目展示区 - 保持 font-black */}
            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="text-center mb-8">
                <span className="text-xl font-bold text-blue-500 uppercase tracking-[0.3em] block mb-1">
                    {currentQuestion.question_type === 'CN_TO_EN' ? 'Translate into English' : '请翻译成中文'}
                </span>
                <p className="text-4xl md:text-5xl font-black text-slate-900 leading-tight px-4">
                    “{currentQuestion.original_text}”
                </p>
            </motion.div>

            {/* 输入交互区 */}
            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="bg-white p-8 md:p-10 rounded-[2.5rem] shadow-xl shadow-slate-200/40 border border-slate-100">
                
                <div className={`
                    w-full h-20 px-8 flex items-center justify-center transition-all duration-300
                    bg-slate-50 border-2 rounded-[2rem]
                    ${isFocused ? 'border-blue-500 bg-white shadow-md' : 'border-slate-100'}
                    ${(feedback && feedback.level >= 2) ? 'opacity-60' : 'opacity-100'}
                    mb-6
                `}>
                    <textarea 
                        ref={inputRef}
                        value={userAnswer}
                        onChange={(e) => setUserAnswer(e.target.value)}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        placeholder={isFocused ? "" : "在这里输入你的答案..."}
                        disabled={isEvaluating || (feedback && feedback.level >= 2)}
                        className="w-full h-auto max-h-full bg-transparent text-center focus:outline-none resize-none leading-relaxed text-slate-800 placeholder:text-slate-400 text-3xl font-bold"
                        rows={1}
                    />
                </div>

                <AnimatePresence mode="wait">
                    {!feedback ? (
                        <motion.button 
                            key="submit-btn"
                            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleSubmit}
                            disabled={!userAnswer.trim() || isEvaluating}
                            className="w-full py-5 bg-slate-900 text-white rounded-[1.2rem] font-black text-xl hover:bg-blue-600 disabled:bg-slate-200 transition-all flex items-center justify-center gap-3 shadow-lg"
                        >
                            {isEvaluating ? <Loader2 className="animate-spin" /> : <Send size={22} />}
                            {isEvaluating ? 'AI 导师正在阅卷...' : '提交答案'}
                        </motion.button>
                    ) : (
                        <motion.div key="feedback-area" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-5">
                            
                            {/* 🌟 核心修改：根据 config 动态渲染颜色 */}
                            <div className={`p-6 rounded-[2rem] border-2 transition-colors duration-500 ${config.card}`}>
                                <div className="flex gap-4">
                                    {config.icon}
                                    <div className="flex-1">
                                        <h4 className={`text-xl font-black mb-1 ${config.titleColor}`}>
                                            {config.title}
                                        </h4>
                                        <p style={{ fontFamily: '"Times New Roman", Times, serif' }}
                                           className={`mt-3 text-xl md:text-2xl font-bold whitespace-pre-line leading-snug ${config.msgColor}`}>
                                            {feedback.message}
                                        </p>
                                    </div>
                                </div>
                            </div>

                            <div className="flex flex-col gap-3">
                                {feedback.level === 1 ? (
                                    <>
                                        <button 
                                            onClick={handleSubmit} 
                                            disabled={isResubmitDisabled}
                                            className="w-full py-5 bg-slate-900 text-white rounded-[1.2rem] font-black text-xl hover:bg-slate-800 transition-all flex items-center justify-center gap-3 shadow-lg disabled:bg-slate-200 disabled:text-slate-400"
                                        >
                                            {isEvaluating ? <Loader2 className="animate-spin" /> : <RefreshCcw size={22} />}
                                            重新提交
                                            <span className="ml-2 font-normal text-xs uppercase tracking-widest opacity-60">Enter</span>
                                        </button>
                                        <button onClick={handleNext} className="w-full py-5 bg-blue-600 text-white rounded-[1.2rem] font-black text-xl hover:bg-blue-700 transition-all flex items-center justify-center gap-3 shadow-lg">
                                            跳过此题，继续前进
                                            <ArrowRight size={22} />
                                        </button>
                                    </>
                                ) : (
                                    <button 
                                        onClick={handleNext} 
                                        className="w-full py-5 bg-blue-600 text-white rounded-[1.2rem] font-black text-xl hover:bg-blue-700 transition-all flex items-center justify-center shadow-lg shadow-blue-100"
                                    >
                                        {currentIndex === questions.length - 1 ? '完成所有练习' : '进入下一题'} 
                                        <span className="ml-3 text-blue-200 font-normal text-xs uppercase tracking-widest">Enter</span>
                                    </button>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}