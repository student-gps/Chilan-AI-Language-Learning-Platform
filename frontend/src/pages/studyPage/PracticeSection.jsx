import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
// 🚀 引入统一的 API 客户端
import apiClient from '../../api/apiClient'; 
import { 
    Loader2, Send, CheckCircle2, XCircle, 
    Sparkles, RefreshCcw, ArrowRight, AlertCircle,
    BookOpen
} from 'lucide-react';

const fadeInUp = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 100, damping: 20 } }
};

// 🌟 单词语境扩展卡片组件
const WordContextCard = ({ word, pinyin, metadata, knowledgeData }) => {
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

    if (primaryExample?.cn || primaryExample?.py || primaryExample?.en) {
        combinedExamples.push(primaryExample);
    }
    examples.forEach((ex) => {
        if (!ex) return;
        const exists = combinedExamples.some((item) =>
            item?.cn === ex?.cn && item?.py === ex?.py && item?.en === ex?.en
        );
        if (!exists) combinedExamples.push(ex);
    });

    if (
        combinedExamples.length === 0 &&
        history.length === 0 &&
        !displayDefinition &&
        !displayWord
    ) return null;

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
                <h4 className="text-xl font-black text-slate-800 tracking-tight">知识点详情</h4>
                <div className="h-px flex-1 bg-slate-200/60" />
            </div>

            {(displayWord || displayDefinition) && (
                <div className="mb-5 bg-white/90 p-5 rounded-[1.75rem] border border-white shadow-sm">
                    <div className="mb-3">
                        <span className="inline-flex items-center px-3 py-1 rounded-full bg-blue-50 text-[11px] font-black uppercase tracking-[0.25em] text-blue-500">
                            Current Sense / 当前义项
                        </span>
                    </div>
                    <div className="flex flex-wrap items-start gap-4 justify-between">
                        <div className="min-w-[180px]">
                            <div className="flex items-end gap-3">
                                <p className="text-5xl font-black text-slate-900 leading-none">{displayWord}</p>
                                {displayPinyin && (
                                    <p className="text-lg font-black text-orange-500">{displayPinyin}</p>
                                )}
                            </div>
                            {displayPartOfSpeech && (
                                <span className="inline-block mt-3 px-3 py-1 rounded-full bg-slate-100 text-xs font-black uppercase tracking-[0.2em] text-slate-500">
                                    {displayPartOfSpeech}
                                </span>
                            )}
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
                {combinedExamples.map((ex, idx) => (
                    <div key={idx} className="bg-white/80 p-5 rounded-2xl border border-white shadow-sm">
                        <p className="text-2xl font-black text-slate-800 mb-1 leading-tight">
                            {ex.cn}
                        </p>
                        <p className="text-sm font-bold text-slate-400 mb-3 tracking-wide uppercase">
                            {ex.py}
                        </p>
                        <div className="py-2 px-4 bg-blue-50/50 rounded-lg inline-block">
                            <p className="text-base font-bold text-blue-600 italic leading-snug">
                                {ex.en}
                            </p>
                        </div>
                    </div>
                ))}
            </div>

            {history.length > 0 && (
                <div className="mt-6 pt-5 border-t border-slate-200/60">
                    <p className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] mb-4">
                        Other Meanings / 更多义项
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
                                {(h.example?.cn || h.example?.en) && (
                                    <div className="mt-3 space-y-1.5">
                                        {h.example?.cn && (
                                            <p className="text-sm font-bold text-slate-700">{h.example.cn}</p>
                                        )}
                                        {h.example?.py && (
                                            <p className="text-xs font-bold text-slate-400 uppercase tracking-wide">{h.example.py}</p>
                                        )}
                                        {h.example?.en && (
                                            <p className="text-sm font-semibold italic text-blue-600">{h.example.en}</p>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </motion.div>
    );
};

export default function PracticeSection({ questions, isReview, onAllDone, userId, courseId, lessonId, initialIndex = 0 }) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState('');
    const [lastSubmittedAnswer, setLastSubmittedAnswer] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [isFocused, setIsFocused] = useState(false);
    const [knowledgeDetails, setKnowledgeDetails] = useState(null);
    
    const inputRef = useRef(null);
    const currentQuestion = questions[currentIndex];

    useEffect(() => {
        const safeIndex = Number.isInteger(initialIndex)
            ? Math.max(0, Math.min(initialIndex, Math.max(questions.length - 1, 0)))
            : 0;
        setCurrentIndex(safeIndex);
        setUserAnswer('');
        setLastSubmittedAnswer('');
        setFeedback(null);
        setKnowledgeDetails(null);
    }, [initialIndex, questions]);

    useEffect(() => {
        if (!questions?.length || !userId || !courseId || !lessonId || isReview) return;
        const syncProgress = async () => {
            try {
                await apiClient.post(`/study/practice_progress`, {
                    user_id: userId,
                    course_id: Number(courseId),
                    lesson_id: lessonId,
                    current_index: currentIndex,
                });
            } catch (e) {
                console.error("同步练习进度失败:", e);
            }
        };
        syncProgress();
    }, [currentIndex, questions, userId, courseId, lessonId, isReview]);

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

    useEffect(() => {
        if (!feedback || !currentQuestion?.item_id) {
            setKnowledgeDetails(null);
            return;
        }

        const fetchKnowledge = async () => {
            try {
                const res = await apiClient.get(`/study/knowledge`, {
                    params: { item_id: currentQuestion.item_id }
                });
                setKnowledgeDetails(res.data?.data || null);
            } catch (e) {
                console.error("加载动态知识点失败:", e);
                setKnowledgeDetails(null);
            }
        };

        fetchKnowledge();
    }, [feedback, currentQuestion]);

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
            // 🚀 使用 apiClient 并简化路径
            const res = await apiClient.post(`/study/evaluate`, {
                user_id: userId || localStorage.getItem('chilan_user_id') || 'test-user-id',
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
            setKnowledgeDetails(null);
        } else {
            onAllDone();
        }
    };

    if (!currentQuestion) return null;

    const isResubmitDisabled = isEvaluating || !userAnswer.trim() || (feedback && feedback.level === 1 && userAnswer === lastSubmittedAnswer);
    const config = feedback ? getFeedbackConfig(feedback.level) : null;

    return (
        <div className="max-w-4xl mx-auto px-6 pt-20 pb-0">
            
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

            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="text-center mb-8">
                <span className="text-xl font-bold text-blue-500 uppercase tracking-[0.3em] block mb-1">
                    {currentQuestion.question_type === 'CN_TO_EN' ? 'Translate into English' : '请翻译成中文'}
                </span>
                <p className="text-4xl md:text-5xl font-black text-slate-900 leading-tight px-4">
                    “{currentQuestion.original_text}”
                </p>
            </motion.div>

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

                            <WordContextCard 
                                word={currentQuestion.original_text}
                                pinyin={currentQuestion.original_pinyin}
                                metadata={currentQuestion.metadata}
                                knowledgeData={knowledgeDetails}
                            />
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}
