import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { AnimatePresence, motion } from 'framer-motion';
import apiClient from '../../api/apiClient';
import TeachingSection from './teaching';
import NewConceptTeachingSection from './english/NewConceptTeachingSection';
import PracticeSection from './practice/PracticeSection';
import FinishCard from './FinishCard';
import PinyinPopover from './PinyinPopover';
import { buildCoursePath, buildFoundationPath } from '../../utils/courseRoutes';

const isChinese = (lang = '') => {
    const l = String(lang).toLowerCase();
    return l.includes('chinese') || l.includes('中文') || l === 'zh' || l.startsWith('zh-');
};

const getLessonTargetLanguage = (lessonContent, course) => (
    lessonContent?.target_language ||
    lessonContent?.lesson_metadata?.target_language ||
    course?.target_language ||
    course?.language ||
    ''
);

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

export default function StudyPage({ resolvedCourseId = null, resolvedCourse = null }) {
    const { t, i18n } = useTranslation();
    const params = useParams();
    const courseId = String(resolvedCourseId || params.courseId || '1');
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const lessonId = searchParams.get('lesson_id');
    const isBrowseEntry = searchParams.get('browse') === '1';

    const [mode, setMode] = useState('loading'); // loading, teaching, practice, review, completed, lesson_finished
    const [studyData, setStudyData] = useState(null);
    const [courseInfo, setCourseInfo] = useState(null);
    const [studyCapabilities, setStudyCapabilities] = useState({
        can_practice: false,
        can_write_progress: false,
    });
    const [showPinyinBtn, setShowPinyinBtn] = useState(false);
    const [pinyinPopoverOpen, setPinyinPopoverOpen] = useState(false);
    // 预加载的 practice_items promise（用户在看讲解时后台已在请求）
    const practiceItemsPromiseRef = React.useRef(null);

    // 🌟 核心逻辑：初始化学习流
    const initFlow = useCallback(async () => {
        setMode('loading');
        practiceItemsPromiseRef.current = null;
        try {
            const initParams = { course_id: courseId };
            if (lessonId) initParams.lesson_id = lessonId;
            if (isBrowseEntry) initParams.browse = 1;
            initParams.defer_practice = 1;
            const studyRes = await apiClient.get(`/study/init`, { params: initParams });

            const { mode: responseMode, data } = studyRes.data;
            let nextData = data;

            const lessonContent = data?.lesson_content;
            const course = data?.course_info || resolvedCourse || {
                id: courseId,
                target_language: getLessonTargetLanguage(lessonContent, null),
                source_language: lessonContent?.source_language || lessonContent?.lesson_metadata?.source_language || '',
            };
            const capabilities = data?.capabilities || {};
            const canPractice = !!capabilities.can_practice;

            setCourseInfo(course || null);
            setStudyCapabilities({
                can_practice: !!capabilities.can_practice,
                can_write_progress: !!capabilities.can_write_progress,
            });
            setShowPinyinBtn(isChinese(getLessonTargetLanguage(lessonContent, course)) && !isNewConceptContent(lessonContent, course));

            if (isBrowseEntry && lessonId && data?.lesson_content) {
                // 浏览模式：进入 teaching，同时后台预加载 practice_items
                const practiceApiLessonId = toApiLessonId(data.lesson_content.lesson_metadata?.lesson_id);
                if (practiceApiLessonId && data.practice_deferred && canPractice) {
                    practiceItemsPromiseRef.current = apiClient.get('/study/practice_items', {
                        params: { course_id: courseId, lesson_id: practiceApiLessonId },
                    });
                }
                setStudyData(nextData);
                setMode('teaching');
            } else if (responseMode === 'teaching' && data.skip_content && canPractice) {
                if (data.practice_deferred && data?.lesson_content?.lesson_metadata?.lesson_id) {
                    const practiceRes = await apiClient.get('/study/practice_items', {
                        params: {
                            course_id: courseId,
                            lesson_id: toApiLessonId(data.lesson_content.lesson_metadata.lesson_id),
                        }
                    });
                    nextData = {
                        ...data,
                        pending_items: practiceRes.data?.pending_items || [],
                        practice_resume_index: practiceRes.data?.practice_resume_index || 0,
                        practice_deferred: false,
                    };
                }
                setStudyData(nextData);
                setMode('practice');
            } else {
                // 正常 teaching 模式：后台预加载 practice_items，用户看讲解时静默完成
                if (responseMode === 'teaching' && data.practice_deferred) {
                    const practiceApiLessonId = toApiLessonId(data.lesson_content?.lesson_metadata?.lesson_id);
                    if (practiceApiLessonId && capabilities.can_practice) {
                        practiceItemsPromiseRef.current = apiClient.get('/study/practice_items', {
                            params: { course_id: courseId, lesson_id: practiceApiLessonId },
                        });
                    }
                }
                setStudyData(nextData);
                setMode(responseMode);
            }
        } catch (e) {
            console.error("加载学习流失败:", e);
            setMode('error');
        }
    }, [courseId, isBrowseEntry, lessonId, resolvedCourse]);

    useEffect(() => { initFlow(); }, [initFlow]);

    const loadPracticeItems = useCallback(async () => {
        if (!studyCapabilities.can_practice) return [];
        const lessonIdForPractice = studyData?.lesson_content?.lesson_metadata?.lesson_id;
        if (!lessonIdForPractice) return [];
        // 已有数据直接返回
        if (!studyData?.practice_deferred && Array.isArray(studyData?.pending_items)) {
            return studyData.pending_items;
        }
        // 优先复用预加载的 promise（用户看讲解时已在后台请求）
        const req = practiceItemsPromiseRef.current || apiClient.get('/study/practice_items', {
            params: {
                course_id: courseId,
                lesson_id: toApiLessonId(lessonIdForPractice),
            }
        });
        practiceItemsPromiseRef.current = null; // 消费掉，避免重复使用
        const practiceRes = await req;
        const pendingItems = practiceRes.data?.pending_items || [];
        setStudyData(prev => ({
            ...prev,
            pending_items: pendingItems,
            practice_resume_index: practiceRes.data?.practice_resume_index || 0,
            practice_deferred: false,
        }));
        return pendingItems;
    }, [courseId, studyCapabilities.can_practice, studyData]);

    const handleStartPractice = useCallback(async () => {
        if (isBrowseEntry) return;
        const lessonApiId = toApiLessonId(studyData?.lesson_content?.lesson_metadata?.lesson_id);
        // content_viewed 和等待 practice_items 并发，互不阻塞
        const [pendingItems] = await Promise.all([
            loadPracticeItems(),
            studyCapabilities.can_write_progress && lessonApiId
                ? apiClient.post('/study/content_viewed', {
                    course_id: courseId,
                    lesson_id: lessonApiId,
                  }).catch(e => console.error('content_viewed 失败:', e))
                : Promise.resolve(),
        ]);
        if (pendingItems.length > 0) {
            setMode('practice');
        }
    }, [courseId, isBrowseEntry, loadPracticeItems, studyCapabilities.can_write_progress, studyData]);

    // 🌟 处理一课结束后的逻辑
    const handleLessonComplete = async () => {
        const lessonId = studyData?.lesson_content?.lesson_metadata?.lesson_id;
        
        if (lessonId && mode === 'practice') {
            try {
                await apiClient.post(`/study/complete_lesson`, {
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
        <div className="min-h-screen bg-slate-50 py-8">
            <div className="max-w-3xl mx-auto px-6 space-y-6 pt-8">
                {/* 课程标题区骨架 */}
                <div className="h-8 w-48 rounded-2xl bg-slate-200 animate-pulse" />
                <div className="h-4 w-72 rounded-xl bg-slate-100 animate-pulse" />
                {/* 主内容卡片骨架 */}
                <div className="rounded-3xl bg-white border border-slate-100 shadow-sm overflow-hidden">
                    <div className="h-56 bg-slate-200 animate-pulse" />
                    <div className="p-6 space-y-4">
                        <div className="h-5 w-3/4 rounded-xl bg-slate-100 animate-pulse" />
                        <div className="h-4 w-full rounded-xl bg-slate-100 animate-pulse" />
                        <div className="h-4 w-5/6 rounded-xl bg-slate-100 animate-pulse" />
                        <div className="h-4 w-2/3 rounded-xl bg-slate-100 animate-pulse" />
                    </div>
                </div>
                {/* 词汇区骨架 */}
                <div className="grid grid-cols-2 gap-3">
                    {[1,2,3,4].map(i => (
                        <div key={i} className="h-16 rounded-2xl bg-white border border-slate-100 animate-pulse" />
                    ))}
                </div>
            </div>
        </div>
    );

    return (
        <div className="min-h-screen bg-slate-50 py-8">
            {/* 拼音入口悬浮按钮 — 仅中文课程可见，所有模式下保持悬浮 */}
            {showPinyinBtn && (
                <>
                    {pinyinPopoverOpen && (
                        <PinyinPopover
                            onClose={() => setPinyinPopoverOpen(false)}
                            foundationPath={buildFoundationPath(courseInfo || resolvedCourse || { id: courseId }, 'pinyin')}
                        />
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
                                    onClick={() => navigate(buildCoursePath(courseInfo || resolvedCourse || { id: courseId }))}
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
                            courseInfo={courseInfo || resolvedCourse}
                            courseId={courseId}
                            onStartPractice={handleStartPractice}
                            isDirectLesson={!!lessonId}
                            isBrowseMode={isBrowseEntry}
                            canStartPractice={!isBrowseEntry && studyCapabilities.can_practice}
                            hasPracticeItems={!!studyData?.practice_deferred || (studyData?.pending_items || []).length > 0}
                        />
                    )}

                    {/* 模式 2：练习或复习模式 */}
                    {(mode === 'practice' || mode === 'review') && (
                        <PracticeSection
                            questions={studyData.pending_items}
                            isReview={mode === 'review'}
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
