import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Loader2, Eye, EyeOff, Volume2, Send, CheckCircle2, XCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';

// 格式化 Lesson ID (101 -> 1.1)
const formatLessonId = (id) => {
    if (!id) return "";
    const numId = parseInt(id, 10);
    if (numId < 100) return id; 
    const major = Math.floor(numId / 100); 
    const minor = numId % 100;             
    return `${major}.${minor}`;
};

// 🌟 统一的入场动画配置
const staggerContainer = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.15 } } 
};

const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 120, damping: 20 } }
};

export default function StudyPage() {
    const { t, i18n } = useTranslation();
    
    const params = useParams();
    const initialCourseId = params.courseId || 1; 
    const initialLessonId = params.lessonId || 101; 
    
    const navigate = useNavigate();
    const userId = localStorage.getItem('chilan_user_id') || 'test-user-id';

    const [mode, setMode] = useState('loading'); 
    const [studyData, setStudyData] = useState(null);
    const [error, setError] = useState(null);
    
    const [currentLessonId, setCurrentLessonId] = useState(initialLessonId);

    useEffect(() => {
        fetchLessonData(currentLessonId);
    }, [currentLessonId]);

    const fetchLessonData = async (lessonId) => {
        setMode('loading');
        try {
            const response = await axios.get(`http://127.0.0.1:8000/study/init`, {
                params: { course_id: initialCourseId, lesson_id: lessonId, user_id: userId }
            });
            
            setStudyData(response.data.data);
            setMode('teaching'); 
            setError(null);
        } catch (err) {
            console.error("加载学习数据失败", err);
            setError("获取课件或题库失败，可能是这节课还没生成。");
            setMode('error');
        }
    };

    const handleFinishTeaching = () => {
        if (studyData?.pending_items && studyData.pending_items.length > 0) {
            setMode('practice');
        } else {
            handleFinishPractice();
        }
    };

    const handleFinishPractice = () => {
        const nextLessonId = parseInt(currentLessonId) + 1;
        setCurrentLessonId(nextLessonId);
    };

    if (mode === 'loading') {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-500">
                <Loader2 className="animate-spin w-12 h-12 mb-4 text-blue-500" />
                <p>正在为你加载自适应学习内容...</p>
            </div>
        );
    }

    if (mode === 'error') {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-red-500">
                <p className="mb-4 text-lg font-bold">{error}</p>
                <button onClick={() => navigate(-1)} className="px-6 py-2 bg-slate-200 text-slate-700 rounded-lg hover:bg-slate-300">返回主页</button>
            </div>
        );
    }

    return (
        // 🌟 恢复完美的 pt-8，不再用过大的 Padding 补救
        <div className="min-h-screen bg-slate-50 pb-20 pt-8">
            {/* 🌟 核心修复：onExitComplete 钩子，退出动画播完瞬间回顶 */}
            <AnimatePresence 
                mode="wait" 
                onExitComplete={() => window.scrollTo(0, 0)}
            >
                <motion.div 
                    key={i18n.language + mode} 
                    variants={staggerContainer}
                    initial="hidden"
                    animate="show"
                    exit={{ opacity: 0, y: -20, transition: { duration: 0.2 } }}
                    className="w-full"
                >
                    {mode === 'teaching' && (
                        <TeachingMode 
                            lessonData={studyData?.lesson_content} 
                            onNext={() => handleFinishTeaching()} 
                        />
                    )}

                    {mode === 'practice' && (
                        <PracticeMode 
                            questions={studyData?.pending_items || []}
                            onComplete={() => handleFinishPractice()}
                        />
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}

// ==========================================
// 子组件：TeachingMode
// ==========================================
function TeachingMode({ lessonData, onNext }) {
    const [showDialoguePinyin, setShowDialoguePinyin] = useState(true);
    const [showDialogueTranslation, setShowDialogueTranslation] = useState(true);
    
    const [showVocabPinyin, setShowVocabPinyin] = useState(true);
    const [showVocabTranslation, setShowVocabTranslation] = useState(true);

    if (!lessonData) return <div>数据缺失</div>;

    const { lesson_metadata, course_content, aigc_visual_prompt } = lessonData;
    const { dialogues, vocabulary } = course_content;

    const displayTitle = lesson_metadata?.title 
        ? lesson_metadata.title.replace(/Lesson \d+/, `Lesson ${formatLessonId(lesson_metadata.lesson_id)}`)
        : "未命名课程";

    const playAudio = (wordsArray) => {
        if (!wordsArray || wordsArray.length === 0) return;
        const fullText = wordsArray.map(w => w.cn).join('');
        const audioUrl = `http://127.0.0.1:8000/study/tts?text=${encodeURIComponent(fullText)}`;
        const audio = new Audio(audioUrl);
        audio.play().catch(err => console.error("音频播放失败:", err));
    };
    
    const playWordAudio = (text) => {
        if (!text) return;
        const audioUrl = `http://127.0.0.1:8000/study/tts?text=${encodeURIComponent(text)}`;
        const audio = new Audio(audioUrl);
        audio.play().catch(err => console.error("音频播放失败:", err));
    };

    const allLines = dialogues?.flatMap(turn => turn.lines || []) || [];

    return (
        <div className="max-w-4xl mx-auto px-6">
            <motion.h1 variants={fadeInUp} className="text-4xl font-black text-slate-800 mb-8">
                {displayTitle}
            </motion.h1>
            
            <motion.div variants={fadeInUp} className="w-full aspect-video bg-slate-900 rounded-3xl flex flex-col items-center justify-center mb-12 shadow-2xl relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent z-10"></div>
                <p className="text-white z-20 font-bold tracking-widest opacity-50 mb-2">🎬 GOOGLE VEO / AIGC 视频位</p>
                <p className="text-slate-400 z-20 text-sm max-w-lg text-center px-4 italic line-clamp-2">
                    Prompt: "{aigc_visual_prompt}"
                </p>
            </motion.div>

            {/* 课文对话区 */}
            <motion.section variants={fadeInUp} className="mb-12">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
                    <h2 className="text-2xl font-black flex items-center gap-2">
                        <span>💬</span> 课文对话
                    </h2>
                    <div className="flex items-center gap-3">
                        <button onClick={() => setShowDialoguePinyin(!showDialoguePinyin)} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${showDialoguePinyin ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'}`}>
                            {showDialoguePinyin ? <Eye size={16} /> : <EyeOff size={16} />}
                            {showDialoguePinyin ? '隐藏拼音' : '显示拼音'}
                        </button>
                        <button onClick={() => setShowDialogueTranslation(!showDialogueTranslation)} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${showDialogueTranslation ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'}`}>
                            {showDialogueTranslation ? <Eye size={16} /> : <EyeOff size={16} />}
                            {showDialogueTranslation ? '隐藏翻译' : '显示翻译'}
                        </button>
                    </div>
                </div>

                <div className="flex flex-col gap-6 bg-white p-6 md:p-8 rounded-3xl shadow-sm border border-slate-100">
                    {allLines.map((line, idx) => {
                        const isLeft = idx % 2 === 0; 
                        return (
                            <div key={idx} className={`flex flex-col ${isLeft ? 'items-start' : 'items-end'}`}>
                                <span className="text-xs font-bold text-slate-400 mb-1 px-2 uppercase tracking-wider">{line.role}</span>
                                <div className={`px-5 py-4 rounded-3xl max-w-[90%] md:max-w-[80%] shadow-sm group ${isLeft ? 'bg-slate-50 border border-slate-100 rounded-tl-sm' : 'bg-blue-50/80 border border-blue-100 rounded-tr-sm'}`}>
                                    <div className="relative">
                                        <div className="flex items-end flex-wrap gap-x-1 gap-y-2 mb-2">
                                            {line.words?.map((wordObj, wordIdx) => (
                                                <ruby key={wordIdx} className="flex flex-col items-center m-0 p-0 leading-none">
                                                    <rt className={`text-[13px] font-mono mb-1 tracking-wide ${showDialoguePinyin ? 'text-slate-500' : 'opacity-0 select-none'} transition-opacity duration-300`}>
                                                        {wordObj.py || ' '}
                                                    </rt>
                                                    <span className={`text-[22px] ${wordObj.highlight ? 'text-blue-600 font-black' : 'text-slate-800 font-medium'}`}>
                                                        {wordObj.cn}
                                                    </span>
                                                </ruby>
                                            ))}
                                            <button onClick={() => playAudio(line.words)} className="opacity-0 group-hover:opacity-100 p-1.5 ml-2 text-blue-500 hover:bg-blue-100 hover:text-blue-700 rounded-full transition-all self-center">
                                                <Volume2 size={20} />
                                            </button>
                                        </div>
                                        {showDialogueTranslation && line.english && <p className="text-sm text-slate-500 italic mt-3 font-medium border-t border-slate-200/50 pt-2">{line.english}</p>}
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            </motion.section>

            {/* 生词表区 */}
            <motion.section variants={fadeInUp} className="mb-12">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between mb-6 gap-4">
                    <h2 className="text-2xl font-black flex items-center gap-2">
                        <span>🔤</span> 本课生词
                    </h2>
                    <div className="flex items-center gap-3">
                        <button onClick={() => setShowVocabPinyin(!showVocabPinyin)} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${showVocabPinyin ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'}`}>
                            {showVocabPinyin ? <Eye size={16} /> : <EyeOff size={16} />}
                            {showVocabPinyin ? '隐藏拼音' : '显示拼音'}
                        </button>
                        <button onClick={() => setShowVocabTranslation(!showVocabTranslation)} className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-all ${showVocabTranslation ? 'bg-indigo-100 text-indigo-700 hover:bg-indigo-200' : 'bg-slate-200 text-slate-600 hover:bg-slate-300'}`}>
                            {showVocabTranslation ? <Eye size={16} /> : <EyeOff size={16} />}
                            {showVocabTranslation ? '隐藏翻译' : '显示翻译'}
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-1 gap-4">
                    {vocabulary?.map((vocab, idx) => (
                        <div key={idx} className="flex flex-col p-5 bg-white border border-slate-100 rounded-3xl shadow-sm hover:shadow-md transition">
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div className="flex items-center gap-4">
                                    <span className="text-3xl font-black text-slate-800">{vocab.word}</span>
                                    <button onClick={() => playWordAudio(vocab.word)} className="p-2 bg-blue-50 text-blue-500 hover:bg-blue-600 hover:text-white rounded-full transition-colors shrink-0"><Volume2 size={20} /></button>
                                    <div>
                                        {showVocabPinyin && (
                                            <span className="text-orange-600 font-mono font-bold block">
                                                {vocab.pinyin}
                                            </span>
                                        )}
                                        <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded uppercase font-bold mt-1 inline-block">{vocab.part_of_speech}</span>
                                    </div>
                                </div>
                                <div className="text-left md:text-right mt-2 md:mt-0">
                                    {showVocabTranslation && (
                                        <span className="text-base text-slate-700 font-medium">
                                            {vocab.definition}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {vocab.example_sentence && typeof vocab.example_sentence === 'object' && (
                                <div className="mt-5 pt-4 border-t border-slate-100">
                                    <div className="flex items-start gap-2">
                                        <span className="font-bold text-slate-400 shrink-0 mt-0.5 text-sm">例句:</span> 
                                        <div className="flex-1">
                                            {showVocabPinyin && vocab.example_sentence.py && (
                                                <p className="text-sm text-slate-500 font-mono mb-1">{vocab.example_sentence.py}</p>
                                            )}
                                            
                                            <div className="flex items-center gap-2 mb-1">
                                                <p className="text-lg text-slate-800 font-medium">{vocab.example_sentence.cn}</p>
                                                <button 
                                                    onClick={() => playWordAudio(vocab.example_sentence.cn)} 
                                                    className="p-1.5 text-slate-400 hover:text-blue-500 bg-slate-50 hover:bg-blue-50 rounded-full transition-colors"
                                                    title="朗读例句"
                                                >
                                                    <Volume2 size={16} />
                                                </button>
                                            </div>

                                            {showVocabTranslation && vocab.example_sentence.en && (
                                                <p className="text-sm text-slate-400 italic">{vocab.example_sentence.en}</p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}
                            
                            {vocab.example_sentence && typeof vocab.example_sentence === 'string' && (
                                 <div className="mt-5 pt-4 border-t border-slate-100 text-red-400 text-sm">
                                    ⚠️ 发现旧版数据格式，请重新运行 content_agent.py 生成最新结构的数据。
                                 </div>
                            )}
                        </div>
                    ))}
                </div>
            </motion.section>

            <motion.div variants={fadeInUp} className="flex justify-end pt-4 pb-12">
                <button 
                    onClick={onNext}
                    className="px-8 py-4 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-700 transition shadow-lg shadow-blue-200"
                >
                    完成课文，去测验 👉
                </button>
            </motion.div>
        </div>
    );
}

// ==========================================
// 子组件：PracticeMode
// ==========================================
function PracticeMode({ questions, onComplete }) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [feedback, setFeedback] = useState(null);

    const currentQuestion = questions[currentIndex];

    // 全局监听回车键 (用于跳过反馈、或者进入下一课)
    useEffect(() => {
        const handleGlobalEnter = (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (!currentQuestion) {
                    onComplete();
                } else if (feedback) {
                    handleNextQuestion();
                }
            }
        };

        if (feedback || !currentQuestion) {
            window.addEventListener('keydown', handleGlobalEnter);
        }

        return () => {
            window.removeEventListener('keydown', handleGlobalEnter);
        };
    }, [feedback, currentQuestion, onComplete]);


    if (!currentQuestion) {
        return (
            <motion.div variants={fadeInUp} className="max-w-2xl mx-auto p-12 text-center bg-white rounded-3xl shadow-sm border border-slate-100">
                <h2 className="text-3xl font-black text-green-500 mb-4">🎉 练习完成！</h2>
                <p className="text-slate-500 mb-8">你已经掌握了本课的所有知识点。</p>
                {/* 这里的按钮也顺手改成了全宽居中，保持设计语言统一 */}
                <button onClick={onComplete} className="w-full py-4 bg-slate-900 text-white rounded-xl hover:bg-slate-800 transition font-bold text-lg flex items-center justify-center">
                    进入下一课 <span className="text-slate-400 text-sm font-normal ml-2">(按 Enter)</span>
                </button>
            </motion.div>
        );
    }

    const handleSubmit = async () => {
        if (!userAnswer.trim()) return;
        setIsEvaluating(true);
        setFeedback(null);

        // 🌟 1. 确保拿到正确的 user_id
        const userId = localStorage.getItem('chilan_user_id') || 'test-user-id';
        
        // 🌟 2. 确保 lesson_id 绝对是一个数字，这里优先从当前题目里拿，如果拿不到，给个默认整数
        const lessonIdNum = currentQuestion.lesson_id ? parseInt(currentQuestion.lesson_id) : 101;

        try {
            // 🌟 3. 发送强类型校验过的数据
            const response = await axios.post(`http://127.0.0.1:8000/study/evaluate`, {
                user_id: userId,
                lesson_id: lessonIdNum, // 确保这里是整数
                question_id: parseInt(currentQuestion.question_id), // 强制转换为整数
                question_type: String(currentQuestion.question_type), 
                original_text: String(currentQuestion.original_text),
                // 确保 standard_answers 存在且必须是数组
                standard_answers: Array.isArray(currentQuestion.standard_answers) ? currentQuestion.standard_answers : [currentQuestion.standard_answers],
                user_answer: String(userAnswer)
            });

            const result = response.data.data;
            
            setFeedback({
                isCorrect: result.isCorrect,
                message: result.message
            });

        } catch (err) {
            console.error("判题请求失败", err);
            // 🌟 4. 如果是 Axios 错误，我们可以把后端返回的具体 422 报错信息打印出来，方便以后排查！
            if (err.response && err.response.data) {
                 console.error("后端详细报错:", err.response.data);
            }
            
            setFeedback({
                isCorrect: false,
                message: "哎呀，网络开小差了，或者是 AI 导师在打盹，请重试一下吧！"
            });
        } finally {
            setIsEvaluating(false);
        }
    };

    const handleNextQuestion = () => {
        setUserAnswer('');
        setFeedback(null);
        setCurrentIndex(prev => prev + 1);
    };

    // 输入框内的局部回车监听 (用于提交)
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); 
            if (userAnswer.trim() && !isEvaluating && !feedback) {
                handleSubmit();
            }
        }
    };

    return (
        <div className="max-w-3xl mx-auto px-6">
            <motion.div variants={fadeInUp} className="mb-10 text-center"> 
                <h1 className="text-3xl md:text-6xl font-black text-slate-800 tracking-tight mb-3">
                    智能巩固复习
                </h1>
                <div className="inline-flex items-center justify-center px-4 py-1 bg-slate-100 text-slate-500 font-bold rounded-full text-base tracking-wide">
                    进度 {currentIndex + 1} / {questions.length}
                </div>
            </motion.div>

            <motion.div variants={fadeInUp} className="mb-10 text-center">
                <span className="text-xl font-bold text-slate-400 uppercase tracking-widest block mb-3">
                    Please translate into {currentQuestion.question_type === 'CN_TO_EN' ? 'English' : 'Chinese'}
                </span>
                <p className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-wide px-4">
                    “{currentQuestion.original_text}”
                </p>
            </motion.div>

            <motion.div variants={fadeInUp} className="bg-white p-8 rounded-3xl shadow-sm border border-slate-100 mb-6 flex flex-col">
                <textarea 
                    value={userAnswer}
                    onChange={(e) => setUserAnswer(e.target.value)}
                    onKeyDown={handleKeyDown} 
                    placeholder="请输入你的翻译... (按 Enter 提交)"
                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[100px] resize-none mb-4"
                    disabled={isEvaluating || feedback}
                />
                
                {/* 🌟 提交框：全宽、居中、等宽 */}
                {!feedback && (
                    <button 
                        onClick={handleSubmit}
                        disabled={isEvaluating || !userAnswer.trim()}
                        className="w-full bg-blue-600 text-white py-4 rounded-xl font-bold text-lg hover:bg-blue-700 disabled:bg-slate-300 transition flex items-center justify-center gap-2"
                    >
                        {isEvaluating ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
                        {isEvaluating ? '判卷中...' : '提交翻译'}
                    </button>
                )}

                {/* 🌟 评价区域和下一题按钮的组合 */}
                {feedback && (
                    <motion.div 
                        initial={{ opacity: 0, height: 0 }} 
                        animate={{ opacity: 1, height: 'auto' }} 
                        className="flex flex-col gap-4 overflow-hidden" // 使用 flex-col 和 gap-4 把评价框和按钮分开
                    >
                        {/* 上半部分：评价框 */}
                        <div className={`p-6 rounded-2xl border ${feedback.isCorrect ? 'bg-green-50 border-green-100' : 'bg-red-50 border-red-100'}`}>
                            <div className="flex items-start gap-3">
                                {feedback.isCorrect ? <CheckCircle2 className="text-green-500 shrink-0 mt-0.5" /> : <XCircle className="text-red-500 shrink-0 mt-0.5" />}
                                <div>
                                    <h3 className={`font-bold mb-1 ${feedback.isCorrect ? 'text-green-800' : 'text-red-800'}`}>
                                        {feedback.isCorrect ? '太棒了！' : '还需要改进'}
                                    </h3>
                                    <p className="text-slate-700 text-sm leading-relaxed">{feedback.message}</p>
                                </div>
                            </div>
                        </div>

                        {/* 下半部分：下一题按钮，全宽、居中 */}
                        <button 
                            onClick={handleNextQuestion}
                            className="w-full py-4 bg-slate-900 text-white font-bold text-lg rounded-xl hover:bg-slate-800 transition flex items-center justify-center"
                        >
                            {currentIndex === questions.length - 1 ? '完成练习' : '下一题'} 
                            <span className="text-slate-400 font-normal ml-2">(Enter)</span>
                        </button>
                    </motion.div>
                )}
            </motion.div>
        </div>
    );
}