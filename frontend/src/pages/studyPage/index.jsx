import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';
import apiClient from '../../api/apiClient';
import TeachingSection from './teaching';
import NewConceptTeachingSection from './english/NewConceptTeachingSection';
import PracticeSection from './practice/PracticeSection';
import FinishCard from './FinishCard';
import { Loader2 } from 'lucide-react';
import PinyinPopover from './PinyinPopover';

const isChinese = (lang = '') => {
    const l = String(lang).toLowerCase();
    return l.includes('chinese') || l.includes('中文') || l === 'zh' || l.startsWith('zh-');
};

const isNewConceptContent = (lessonContent, course) => {
    const pipelineId = String(lessonContent?.pipeline_id || course?.pipeline_id || '').toLowerCase();
    const courseId = String(lessonContent?.lesson_metadata?.course_id || course?.course_id || course?.id || '').toLowerCase();
    return (
        pipelineId === 'new_concept_english' ||
        pipelineId === 'new-concept-english' ||
        courseId === '101' ||
        courseId.includes('new_concept_english')
    );
};

const toApiLessonId = (value) => {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    const digits = String(value || '').match(/\d+/)?.[0];
    return digits ? Number(digits) : value;
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
    const isBrowseEntry = searchParams.get('browse') === '1';
    const userId = localStorage.getItem('chilan_user_id') || 'test-user-id';

    const [mode, setMode] = useState('loading'); // loading, teaching, practice, review, completed, lesson_finished
    const [studyData, setStudyData] = useState(null);
    const [courseInfo, setCourseInfo] = useState(null);
    const [isCourseEnrolled, setIsCourseEnrolled] = useState(false);
    const [showPinyinBtn, setShowPinyinBtn] = useState(false);
    const [pinyinPopoverOpen, setPinyinPopoverOpen] = useState(false);

    // 🌟 核心逻辑：初始化学习流
    const initFlow = useCallback(async () => {
        setMode('loading');
        try {
            const initParams = { course_id: courseId, user_id: userId };
            if (lessonId) initParams.lesson_id = lessonId;
            const [studyRes, coursesRes, myCoursesRes] = await Promise.all([
                apiClient.get(`/study/init`, { params: initParams }),
                apiClient.get(`/courses`),
                apiClient.get(`/my-courses/${userId}`).catch(() => ({ data: [] })),
            ]);

            const { mode: responseMode, data } = studyRes.data;
            setStudyData(data);

            // 判断目标语言是否为中文，决定是否显示拼音入口
            const course = (coursesRes.data || []).find(c => String(c.id) === String(courseId));
            const myCourses = myCoursesRes.data || [];
            setCourseInfo(course || null);
            setIsCourseEnrolled(myCourses.some(c => String(c.id) === String(courseId)));
            setShowPinyinBtn(isChinese(course?.target_language) && !isNewConceptContent(data?.lesson_content, course));

            // Course catalog browsing should always open the selected lesson normally,
            // independent of resume/progress state.
            if (isBrowseEntry && lessonId && data?.lesson_content) {
                setMode('teaching');
            } else if (responseMode === 'teaching' && data.skip_content) {
                setMode('practice');
            } else {
                setMode(responseMode);
            }
        } catch (e) {
            console.error("加载学习流失败:", e);
            setMode('error');
        }
    }, [courseId, isBrowseEntry, lessonId, userId]);

    useEffect(() => { initFlow(); }, [initFlow]);

    // 🌟 处理一课结束后的逻辑
    const handleLessonComplete = async () => {
        const lessonId = studyData?.lesson_content?.lesson_metadata?.lesson_id;
        
        if (lessonId && mode === 'practice') {
            try {
                await apiClient.post(`/study/complete_lesson`, {
                    user_id: userId,
                    course_id: courseId,
                    lesson_id: toApiLessonId(lessonId)
                });
            } catch (e) {
                console.error("更新进度失败:", e);
            }
        }
        setMode('lesson_finished'); 
    };

    // --- 渲染逻辑 ---
    const lessonContent = studyData?.lesson_content;
    const useNewConceptTeaching = isNewConceptContent(lessonContent, courseInfo);
    const TeachingComponent = useNewConceptTeaching ? NewConceptTeachingSection : TeachingSection;

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
                    {mode === 'not_enrolled' && (
                        <div className="flex min-h-[70vh] flex-col items-center justify-center gap-5 px-6 text-center">
                            <div className="rounded-3xl border border-blue-100 bg-white px-8 py-7 shadow-sm">
                                <p className="text-lg font-black text-slate-900">{t('study_not_enrolled_title')}</p>
                                <p className="mt-2 max-w-md text-sm font-semibold text-slate-500">{t('study_not_enrolled_desc')}</p>
                                <button
                                    onClick={() => navigate(`/course/${courseId}`)}
                                    className="mt-6 rounded-2xl bg-blue-600 px-6 py-3 text-sm font-black text-white transition hover:bg-slate-900 active:scale-95"
                                >
                                    {t('study_not_enrolled_action')}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* 模式 1：教学讲解模式 */}
                    {mode === 'teaching' && (
                        <TeachingComponent
                            data={lessonContent}
                            courseInfo={courseInfo}
                            courseId={courseId}
                            userId={userId}
                            onStartPractice={() => setMode('practice')}
                            isDirectLesson={!!lessonId}
                            canStartPractice={!lessonId || isCourseEnrolled}
                            hasPracticeItems={(studyData?.pending_items || []).length > 0}
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
                            initialIndex={isBrowseEntry ? 0 : (studyData?.practice_resume_index || 0)}
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
