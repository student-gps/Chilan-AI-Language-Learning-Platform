import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';
// 🚀 确保路径指向你存放 apiClient 的地方
import apiClient from '../../api/apiClient'; 
import TeachingSection from './teaching';
import PracticeSection from './practice/PracticeSection';
import FinishCard from './FinishCard';
import { Loader2 } from 'lucide-react';

const pageTransition = {
    hidden: { opacity: 0, y: 12 },
    show: { opacity: 1, y: 0, transition: { duration: 0.28 } },
    exit: { opacity: 0, y: -12, transition: { duration: 0.18 } }
};

export default function StudyPage() {
    const { t, i18n } = useTranslation();
    const { courseId = 1 } = useParams();
    const userId = localStorage.getItem('chilan_user_id') || 'test-user-id';
    
    const [mode, setMode] = useState('loading'); // loading, teaching, practice, review, completed, lesson_finished
    const [studyData, setStudyData] = useState(null);

    // 🌟 核心逻辑：初始化学习流
    const initFlow = async () => {
        setMode('loading');
        try {
            // 请求后端的 /study/init 接口
            const res = await apiClient.get(`/study/init`, {
                params: { course_id: courseId, user_id: userId }
            });
            
            const { mode: responseMode, data } = res.data;
            setStudyData(data);
            
            // 如果后端说这节课已经看过了，直接跳到练习
            if (responseMode === 'teaching' && data.skip_content) {
                setMode('practice');
            } else {
                setMode(responseMode);
            }
        } catch (e) { 
            console.error("加载学习流失败:", e);
            setMode('error'); 
        }
    };

    useEffect(() => { initFlow(); }, [courseId]);

    // 🌟 处理一课结束后的逻辑
    const handleLessonComplete = async () => {
        const lessonId = studyData?.lesson_content?.lesson_metadata?.lesson_id;
        
        if (lessonId && mode === 'practice') {
            try {
                await apiClient.post(`/study/complete_lesson`, {
                    user_id: userId,
                    course_id: courseId,
                    lesson_id: lessonId 
                });
            } catch (e) {
                console.error("更新进度失败:", e);
            }
        }
        setMode('lesson_finished'); 
    };

    // --- 渲染逻辑 ---

    if (mode === 'loading') return (
        <div className="flex h-screen items-center justify-center">
            <Loader2 className="animate-spin text-blue-500" size={32} />
        </div>
    );
    
    if (mode === 'completed') return <FinishCard isAllCompleted={true} />;
    
    if (mode === 'lesson_finished') return <FinishCard isAllCompleted={false} onContinue={initFlow} />;

    return (
        <div className="min-h-screen bg-slate-50 py-8">
            <AnimatePresence mode="wait">
                <motion.div
                    key={`${mode}-${i18n.language}`}
                    variants={pageTransition}
                    initial="hidden"
                    animate="show"
                    exit="exit"
                >
                    {/* 模式 1：教学讲解模式 */}
                    {mode === 'teaching' && (
                        <TeachingSection 
                            data={studyData.lesson_content} 
                            courseId={courseId} 
                            userId={userId}     
                            onStartPractice={() => setMode('practice')} 
                        />
                    )}
                    
                    {/* 模式 2：练习或复习模式 */}
                    {(mode === 'practice' || mode === 'review') && (
                        <PracticeSection 
                            questions={studyData.pending_items} 
                            isReview={mode === 'review'}
                            userId={userId}
                            courseId={courseId}
                            lessonId={studyData?.lesson_content?.lesson_metadata?.lesson_id}
                            initialIndex={studyData?.practice_resume_index || 0}
                            onAllDone={handleLessonComplete}
                        />
                    )}

                    {/* 错误处理 */}
                    {mode === 'error' && (
                        <div className="flex flex-col h-screen items-center justify-center gap-4">
                            <p className="text-slate-500 font-bold">{t('study_error_load')}</p>
                            <button onClick={initFlow} className="px-6 py-2 bg-blue-600 text-white rounded-xl font-bold">{t('study_retry')}</button>
                        </div>
                    )}
                </motion.div>
            </AnimatePresence>
        </div>
    );
}
