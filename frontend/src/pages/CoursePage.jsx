import React, { useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ChevronRight, BookOpen, Play, ArrowLeft, Loader2, PlusCircle, CheckCircle2 } from 'lucide-react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/apiClient';
import { courseQuery, foundationModulesQuery, lessonsQuery, myCoursesQuery, queryKeys } from '../api/queries';
import { buildFoundationPath, buildStudyPath } from '../utils/courseRoutes';
import { getAuthState } from '../utils/authStorage';

const MAX_ACTIVE_COURSES = 2;

const cleanCourseDisplayName = (name = '') => String(name || '').replace(/\s*(初级|中级)\s*/g, ' ').trim();

const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 120, damping: 20 } },
};

const stagger = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};

const toNumber = (value, fallback = 0) => {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
};

const getLessonDisplayTitle = (lesson, fallback = '') =>
    lesson?.title_localized || lesson?.title || fallback;

const buildCourseProgress = (enrollment, lessons, t) => {
    const lessonTotal = toNumber(enrollment?.lesson_total, lessons.length) || lessons.length;
    const lastCompletedLessonId = toNumber(enrollment?.last_completed_lesson_id, 0);
    const completedFromLessons = lessons.filter(
        (lesson) => toNumber(lesson.lesson_id) <= lastCompletedLessonId
    ).length;
    const completedLessonCount = Math.min(
        lessonTotal,
        toNumber(enrollment?.completed_lesson_count, completedFromLessons) || completedFromLessons
    );
    const progressPercent = lessonTotal > 0
        ? Math.round((completedLessonCount / lessonTotal) * 100)
        : 0;
    const nextLesson = enrollment?.next_lesson_id
        ? {
            lesson_id: enrollment.next_lesson_id,
            title: enrollment.next_lesson_title,
            title_localized: enrollment.next_lesson_title_localized,
        }
        : lessons.find((lesson) => toNumber(lesson.lesson_id) > lastCompletedLessonId);
    const nextLessonId = toNumber(nextLesson?.lesson_id, 0);
    const viewedLessonId = toNumber(enrollment?.viewed_lesson_id, 0);
    const practiceQuestionIndex = toNumber(enrollment?.practice_question_index, 0);
    const hasViewedCurrentLesson = nextLessonId > 0 && viewedLessonId === nextLessonId;
    const isCompleted = lessonTotal > 0 && completedLessonCount >= lessonTotal && !nextLessonId;

    let statusText = t('course_progress_next_lesson');
    if (lessonTotal === 0) {
        statusText = t('course_no_lessons');
    } else if (isCompleted) {
        statusText = t('course_progress_completed');
    } else if (hasViewedCurrentLesson && practiceQuestionIndex > 0) {
        statusText = t('course_progress_resume_practice', { number: practiceQuestionIndex + 1 });
    } else if (hasViewedCurrentLesson) {
        statusText = t('course_progress_start_practice');
    }

    return {
        lessonTotal,
        completedLessonCount,
        progressPercent,
        lastCompletedLessonId,
        nextLesson,
        nextLessonId,
        statusText,
        isCompleted,
    };
};

export default function CoursePage({ resolvedCourseId = null, resolvedCourse = null }) {
    const params = useParams();
    const courseId = String(resolvedCourseId || params.courseId || '');
    const navigate = useNavigate();
    const location = useLocation();
    const { t } = useTranslation();
    const queryClient = useQueryClient();

    const [enrollError, setEnrollError] = useState('');
    const userId = getAuthState().userId;
    const coursePath = `${location.pathname}${location.search || ''}`;
    const routeCourse = resolvedCourse || location.state?.course;
    const hasMatchingRouteCourse = String(routeCourse?.id) === String(courseId);
    const cachedCourse = queryClient.getQueryData(queryKeys.course(courseId));
    const cachedCourses = queryClient.getQueryData(queryKeys.courses()) || [];
    const catalogCourse = cachedCourses.find((candidate) => String(candidate.id) === String(courseId));
    const initialCourse = hasMatchingRouteCourse ? routeCourse : cachedCourse || catalogCourse;
    const courseCacheState = queryClient.getQueryState(queryKeys.course(courseId));
    const coursesCacheState = queryClient.getQueryState(queryKeys.courses());
    const initialCourseUpdatedAt = cachedCourse
        ? courseCacheState?.dataUpdatedAt
        : coursesCacheState?.dataUpdatedAt;

    // ── 服务端数据：课程信息优先复用教室页缓存，课时与报名状态独立刷新 ─────────
    const { data: course = initialCourse, isLoading: isCourseLoading } = useQuery({
        ...courseQuery(courseId),
        initialData: initialCourse,
        initialDataUpdatedAt: initialCourseUpdatedAt,
    });
    const { data: lessons = [], isLoading: isLessonsLoading } = useQuery(lessonsQuery(courseId));
    const { data: foundations = [] } = useQuery(foundationModulesQuery(course?.slug));
    const { data: myCourses = [] } = useQuery(myCoursesQuery(userId));

    // 从 myCourses 派生当前课程的报名状态（缓存命中时零请求）
    const currentEnrollment = myCourses.find(c => String(c.id) === String(courseId)) ?? null;
    const isEnrolled = Boolean(currentEnrollment);
    const enrolledCount = myCourses.length;

    const loading = isCourseLoading && !course;

    // ── 报名 mutation ────────────────────────────────────────────────────────
    const enrollMutation = useMutation({
        mutationFn: () => apiClient.post('/courses/enroll', {
            course_id: Number(courseId),
        }),
        onSuccess: () => {
            setEnrollError('');
            // 使 my-courses 缓存失效 → 自动重新拉取 → isEnrolled / currentEnrollment 自动更新
            queryClient.invalidateQueries({ queryKey: queryKeys.myCourses(userId) });
            queryClient.invalidateQueries({ queryKey: queryKeys.classroomStats(userId) });
        },
        onError: (err) => {
            setEnrollError(err.response?.status === 409
                ? t('course_limit_reached')
                : t('course_enroll_failed'));
        },
    });

    const handleEnroll = () => {
        if (!userId || enrollMutation.isPending || isEnrolled) return;
        if (enrolledCount >= MAX_ACTIVE_COURSES) {
            setEnrollError(t('course_limit_reached'));
            return;
        }
        enrollMutation.mutate();
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <Loader2 className="animate-spin w-10 h-10 text-blue-500" />
            </div>
        );
    }

    const courseProgress = buildCourseProgress(currentEnrollment, lessons, t);

    return (
        <div className="min-h-screen bg-slate-50 pt-24 pb-20">
            <div className="max-w-6xl mx-auto px-8">

                {/* Back */}
                <button
                    onClick={() => navigate('/classroom')}
                    className="fixed top-24 left-6 z-50 flex items-center gap-2 px-4 py-2.5 bg-white text-slate-600 font-semibold rounded-2xl shadow-md border border-slate-100 hover:bg-slate-50 hover:text-slate-900 transition-all"
                >
                    <ArrowLeft size={16} /> {t('course_back')}
                </button>

                {/* Course title */}
                <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mb-10">
                    <h1 className="text-4xl font-black text-slate-900 mb-2">
                        {cleanCourseDisplayName(course?.name) || '课程'}
                    </h1>
                </motion.div>

                {isEnrolled && (
                    <motion.section variants={fadeInUp} initial="hidden" animate="show" className="mb-8 rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
                        <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
                            <div className="min-w-0 flex-1">
                                <div className="mb-3 flex items-center justify-between gap-4">
                                    <p className="text-xs font-black uppercase tracking-widest text-slate-400">
                                        {t('course_progress_label')}
                                    </p>
                                    <p className="text-sm font-black text-slate-900">
                                        {courseProgress.progressPercent}%
                                    </p>
                                </div>
                                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                                    <div
                                        className="h-full rounded-full bg-blue-600 transition-all"
                                        style={{ width: `${courseProgress.progressPercent}%` }}
                                    />
                                </div>
                                <p className="mt-3 text-sm font-bold text-slate-500">
                                    {t('course_progress_completed_count', {
                                        completed: courseProgress.completedLessonCount,
                                        total: courseProgress.lessonTotal,
                                    })}
                                </p>
                            </div>

                            <div className="min-w-0 rounded-2xl bg-slate-50 px-5 py-4 lg:w-96">
                                <p className="text-xs font-black uppercase tracking-widest text-slate-400">
                                    {courseProgress.statusText}
                                </p>
                                <p className="mt-1 truncate text-lg font-black text-slate-900">
                                    {courseProgress.isCompleted
                                        ? t('course_progress_all_done')
                                        : courseProgress.nextLessonId
                                            ? `Lesson ${courseProgress.nextLessonId} · ${getLessonDisplayTitle(courseProgress.nextLesson, t('course_untitled_lesson'))}`
                                            : t('course_no_lessons')}
                                </p>
                            </div>
                        </div>
                    </motion.section>
                )}

                {/* Course CTA */}
                <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mb-10 flex justify-center">
                    {isEnrolled ? (
                        <button
                            onClick={() => navigate(buildStudyPath(course || { id: courseId }))}
                            className="flex items-center gap-3 px-12 py-5 bg-slate-900 text-white rounded-2xl font-black text-xl hover:bg-blue-600 active:scale-95 transition-all shadow-lg shadow-slate-300/40"
                        >
                            <Play size={22} fill="white" /> {t('course_start_learning')}
                        </button>
                    ) : (
                        <button
                            onClick={handleEnroll}
                            disabled={enrollMutation.isPending || enrolledCount >= MAX_ACTIVE_COURSES}
                            className="flex items-center gap-3 px-12 py-5 bg-blue-600 text-white rounded-2xl font-black text-xl hover:bg-slate-900 active:scale-95 disabled:opacity-70 disabled:cursor-wait transition-all shadow-lg shadow-blue-200/70"
                        >
                            {enrollMutation.isPending ? <Loader2 size={22} className="animate-spin" /> : <PlusCircle size={22} />}
                            {enrollMutation.isPending ? t('course_adding_learning') : t('classroom_join_course')}
                        </button>
                    )}
                </motion.div>

                {!isEnrolled && (enrollError || enrolledCount >= MAX_ACTIVE_COURSES) && (
                    <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mb-5 rounded-2xl border border-amber-100 bg-amber-50 px-5 py-4 text-center text-sm font-bold text-amber-700">
                        {enrollError || t('course_limit_reached')}
                    </motion.div>
                )}

                {!isEnrolled && (
                    <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mb-10 rounded-2xl border border-blue-100 bg-blue-50 px-5 py-4 text-center text-sm font-semibold text-blue-700">
                        {t('course_preview_before_join')}
                    </motion.div>
                )}

                {foundations.length > 0 && (
                    <motion.section variants={stagger} initial="hidden" animate="show" className="mb-10">
                        <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-4">{t('course_foundations')}</h2>
                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                            {foundations.map((item) => (
                                <motion.button
                                    key={item.key}
                                    variants={fadeInUp}
                                    onClick={() => navigate(buildFoundationPath(course || { id: courseId }, item.key), { state: { from: coursePath } })}
                                    className="flex items-center gap-3 px-5 py-3.5 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md hover:border-blue-200 transition-all group"
                                >
                                    <span className="text-2xl w-8 text-center font-black text-slate-500">{item.icon}</span>
                                    <div className="text-left">
                                        <div className="font-black text-slate-800 text-sm transition-colors group-hover:text-blue-600">{t(item.title_key)}</div>
                                        <div className="text-xs text-slate-400">{t(item.description_key)}</div>
                                    </div>
                                    <ChevronRight size={14} className="text-slate-300 ml-1" />
                                </motion.button>
                            ))}
                        </div>
                    </motion.section>
                )}

                {/* Lesson list */}
                <section>
                    <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-4">{t('course_all_lessons')}</h2>
                    {isLessonsLoading ? (
                        <div className="flex items-center justify-center py-16 text-slate-300">
                            <Loader2 className="animate-spin" size={28} />
                        </div>
                    ) : (
                    <motion.div variants={stagger} initial="hidden" animate="show" className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                        {lessons.map((lesson, idx) => {
                            const lessonId = toNumber(lesson.lesson_id);
                            const isCompleted = isEnrolled && lessonId <= courseProgress.lastCompletedLessonId;
                            const isCurrent = isEnrolled && lessonId === courseProgress.nextLessonId;
                            const statusLabel = isCompleted
                                ? t('course_lesson_completed')
                                : isCurrent
                                    ? t('course_lesson_current')
                                    : t('course_lesson_not_started');
                            const Icon = isCompleted ? CheckCircle2 : isCurrent ? Play : BookOpen;
                            return (
                                <motion.button
                                    key={lesson.lesson_id}
                                    variants={fadeInUp}
                                    onClick={() => navigate(`${buildStudyPath(course || { id: courseId })}?lesson_id=${lesson.lesson_id}&browse=1`)}
                                    className={`flex items-center gap-5 px-6 py-4 bg-white rounded-2xl border shadow-sm hover:shadow-md hover:border-blue-200 transition-all group text-left ${
                                        isCurrent ? 'border-blue-200 ring-2 ring-blue-50' : 'border-slate-100'
                                    }`}
                                >
                                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 transition-colors ${
                                        isCompleted
                                            ? 'bg-emerald-50'
                                            : isCurrent
                                                ? 'bg-blue-50'
                                                : 'bg-slate-100 group-hover:bg-blue-50'
                                    }`}>
                                        <Icon
                                            size={18}
                                            className={`transition-colors ${
                                                isCompleted
                                                    ? 'text-emerald-500'
                                                    : isCurrent
                                                        ? 'text-blue-500'
                                                        : 'text-slate-400 group-hover:text-blue-500'
                                            }`}
                                            fill={isCurrent ? 'currentColor' : 'none'}
                                        />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-xs font-black text-slate-400 uppercase tracking-widest mb-0.5">
                                            Lesson {lesson.lesson_id}
                                        </div>
                                        <div className="font-black text-slate-800 truncate group-hover:text-blue-700 transition-colors">
                                            {lesson.title || `第 ${idx + 1} 课`}
                                        </div>
                                        {lesson.title_localized && (
                                            <div className="text-xs font-medium text-slate-400 truncate mt-0.5">
                                                {lesson.title_localized}
                                            </div>
                                        )}
                                        {isEnrolled && (
                                            <div className={`mt-1 text-xs font-black ${
                                                isCompleted ? 'text-emerald-500' : isCurrent ? 'text-blue-500' : 'text-slate-300'
                                            }`}>
                                                {statusLabel}
                                            </div>
                                        )}
                                    </div>
                                    <ChevronRight size={18} className="text-slate-300 group-hover:text-blue-400 group-hover:translate-x-1 transition-all shrink-0" />
                                </motion.button>
                            );
                        })}

                        {lessons.length === 0 && (
                            <div className="py-16 text-center text-slate-400 font-semibold">
                                {t('course_no_lessons')}
                            </div>
                        )}
                    </motion.div>
                    )}
                </section>
            </div>
        </div>
    );
}
