import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';
import apiClient from '../../api/apiClient';
import TeachingSection from './teaching';
import PracticeSection from './practice/PracticeSection';
import FinishCard from './FinishCard';
import { Loader2 } from 'lucide-react';
import PinyinPopover from './PinyinPopover';

const isChinese = (lang = '') => {
    const l = String(lang).toLowerCase();
    return l.includes('chinese') || l.includes('中文') || l === 'zh' || l.startsWith('zh-');
};

const pageTransition = {
    hidden: { opacity: 0, y: 12 },
    show: { opacity: 1, y: 0, transition: { duration: 0.28 } },
    exit: { opacity: 0, y: -12, transition: { duration: 0.18 } }
};

export default function StudyPage() {
    const { t, i18n } = useTranslation();
    const { courseId = 1 } = useParams();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const lessonId = searchParams.get('lesson_id');
    const userId = localStorage.getItem('chilan_user_id') || 'test-user-id';

    const [mode, setMode] = useState('loading'); // loading, teaching, practice, review, completed, lesson_finished
    const [studyData, setStudyData] = useState(null);
    const [showPinyinBtn, setShowPinyinBtn] = useState(false);
    const [pinyinPopoverOpen, setPinyinPopoverOpen] = useState(false);

    // 🌟 核心逻辑：初始化学习流
    const initFlow = async () => {
        setMode('loading');
        try {
            const initParams = { course_id: courseId, user_id: userId };
            if (lessonId) initParams.lesson_id = lessonId;
            const [studyRes, coursesRes] = await Promise.all([
                apiClient.get(`/study/init`, { params: initParams }),
                apiClient.get(`/courses`),
            ]);

            const { mode: responseMode, data } = studyRes.data;
            setStudyData(data);

            // 判断目标语言是否为中文，决定是否显示拼音入口
            const course = (coursesRes.data || []).find(c => String(c.id) === String(courseId));
            setShowPinyinBtn(isChinese(course?.target_language));

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

    return (
        <div className="min-h-screen bg-slate-50 py-8">
            {/* 拼音入口悬浮按钮 — 仅中文课程可见，所有模式下保持悬浮 */}
            {showPinyinBtn && (
                <>
                    {pinyinPopoverOpen && (
                        <PinyinPopover onClose={() => setPinyinPopoverOpen(false)} />
                    )}
                    <button
                        onClick={() => setPinyinPopoverOpen(o => !o)}
                        title="Pinyin Guide"
                        className={`fixed bottom-6 left-6 z-50 flex items-center gap-2.5 rounded-full bg-white px-5 py-3 text-base font-semibold shadow-lg ring-1 transition active:scale-95 ${
                            pinyinPopoverOpen
                                ? 'ring-blue-400 text-blue-600 bg-blue-50 shadow-xl'
                                : 'ring-slate-200 text-slate-700 hover:bg-slate-50 hover:shadow-xl hover:ring-blue-300'
                        }`}
                    >
                        <span className="text-lg leading-none">拼</span>
                        <span className="tracking-wide">Pinyin</span>
                    </button>
                </>
            )}

            <AnimatePresence mode="wait">
                <motion.div
                    key={`${mode}-${i18n.language}`}
                    variants={pageTransition}
                    initial="hidden"
                    animate="show"
                    exit="exit"
                >
                    {/* 完成状态 */}
                    {mode === 'completed' && <FinishCard isAllCompleted={true} />}
                    {mode === 'lesson_finished' && <FinishCard isAllCompleted={false} onContinue={initFlow} />}

                    {/* 模式 1：教学讲解模式 */}
                    {mode === 'teaching' && (
                        <TeachingSection
                            data={studyData.lesson_content}
                            courseId={courseId}
                            userId={userId}
                            onStartPractice={() => setMode('practice')}
                            isDirectLesson={!!lessonId}
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
                            lessonAudioAssets={studyData?.lesson_content?.lesson_audio_assets}
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
