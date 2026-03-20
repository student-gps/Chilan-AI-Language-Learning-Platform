import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';
import { Loader2, Send, CheckCircle2, XCircle } from 'lucide-react';

const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0 }
};

export default function PracticeSection({ questions, isReview, onAllDone }) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [feedback, setFeedback] = useState(null);

    const currentQuestion = questions[currentIndex];

    // 监听键盘 Enter
    useEffect(() => {
        const handleEnter = (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (feedback) handleNext();
                else if (userAnswer.trim() && !isEvaluating) handleSubmit();
            }
        };
        window.addEventListener('keydown', handleEnter);
        return () => window.removeEventListener('keydown', handleEnter);
    }, [userAnswer, feedback, isEvaluating]);

    const handleSubmit = async () => {
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
        } catch (e) {
            setFeedback({ isCorrect: false, message: "判题服务连接失败" });
        } finally {
            setIsEvaluating(false);
        }
    };

    const handleNext = () => {
        if (currentIndex < questions.length - 1) {
            setCurrentIndex(prev => prev + 1);
            setUserAnswer('');
            setFeedback(null);
        } else {
            onAllDone();
        }
    };

    if (!currentQuestion) return null;

    return (
        <div className="max-w-3xl mx-auto px-6">
            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="text-center mb-10">
                <h1 className="text-4xl font-black text-slate-800 mb-2">{isReview ? "智能巩固复习" : "随堂强化练习"}</h1>
                <div className="mt-4 inline-block px-4 py-1 bg-slate-200 rounded-full text-xs font-bold text-slate-500">
                    题目 {currentIndex + 1} / {questions.length}
                </div>
            </motion.div>

            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="text-center mb-10">
                <span className="text-sm font-bold text-blue-500 uppercase tracking-widest block mb-2">
                    {currentQuestion.question_type === 'CN_TO_EN' ? 'Translate to English' : '翻译成中文'}
                </span>
                <p className="text-3xl font-extrabold text-slate-900">“{currentQuestion.original_text}”</p>
            </motion.div>

            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100">
                <textarea 
                    autoFocus
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    disabled={isEvaluating || feedback}
                    placeholder="在这里输入你的翻译..."
                    className="w-full h-32 p-4 bg-slate-50 border border-slate-200 rounded-2xl text-xl focus:ring-2 focus:ring-blue-500 outline-none mb-6 resize-none"
                />

                {!feedback ? (
                    <button 
                        onClick={handleSubmit}
                        disabled={!userAnswer.trim() || isEvaluating}
                        className="w-full py-4 bg-blue-600 text-white rounded-xl font-bold text-lg hover:bg-blue-700 disabled:bg-slate-300 transition flex items-center justify-center gap-2"
                    >
                        {isEvaluating ? <Loader2 className="animate-spin" /> : <Send size={20} />}
                        {isEvaluating ? 'AI 导师正在阅卷...' : '提交答案'}
                    </button>
                ) : (
                    <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                        <div className={`p-6 rounded-2xl mb-6 border ${feedback.isCorrect ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                            <div className="flex gap-3">
                                {feedback.isCorrect ? <CheckCircle2 className="text-green-500" /> : <XCircle className="text-red-500" />}
                                <div>
                                    <h4 className={`font-bold ${feedback.isCorrect ? 'text-green-800' : 'text-red-800'}`}>{feedback.isCorrect ? '太棒了！' : 'AI 导师点评'}</h4>
                                    <p className="text-slate-700 text-sm mt-1">{feedback.message}</p>
                                </div>
                            </div>
                        </div>
                        <button onClick={handleNext} className="w-full py-4 bg-slate-900 text-white rounded-xl font-bold text-lg flex items-center justify-center">
                            {currentIndex === questions.length - 1 ? '完成练习' : '下一题'} <span className="ml-2 text-slate-400 font-normal text-sm">(Enter)</span>
                        </button>
                    </div>
                )}
            </motion.div>
        </div>
    );
}