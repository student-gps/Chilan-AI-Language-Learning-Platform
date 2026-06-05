import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ChevronRight, BookOpen, Play, ArrowLeft, Loader2, PlusCircle, CheckCircle2 } from 'lucide-react';
import apiClient from '../api/apiClient';

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

export default function CoursePage() {
    const { courseId } = useParams();
    const navigate = useNavigate();
    const location = useLocation();
    const { t } = useTranslation();
    const [lessons, setLessons] = useState([]);
    const [course, setCourse] = useState(null);
    const [isEnrolled, setIsEnrolled] = useState(false);
    const [currentEnrollment, setCurrentEnrollment] = useState(null);
    const [isEnrolling, setIsEnrolling] = useState(false);
    const [enrolledCount, setEnrolledCount] = useState(0);
    const [enrollError, setEnrollError] = useState('');
    const [loading, setLoading] = useState(true);
    const userId = localStorage.getItem('chilan_user_id');
    const coursePath = `${location.pathname}${location.search || ''}`;

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            const [lessonsRes, coursesRes, myCoursesRes] = await Promise.allSettled([
                apiClient.get(`/courses/${courseId}/lessons`),
                apiClient.get('/courses'),
                userId ? apiClient.get(`/my-courses/${userId}`) : Promise.resolve({ data: [] }),
            ]);
            if (lessonsRes.status === 'fulfilled') setLessons(lessonsRes.value.data);
            if (coursesRes.status === 'fulfilled') {
                const found = (coursesRes.value.data || []).find(c => String(c.id) === String(courseId));
                setCourse(found || null);
            }
            if (myCoursesRes.status === 'fulfilled') {
                const myCourses = myCoursesRes.value.data || [];
                const matchedCourse = myCourses.find(c => String(c.id) === String(courseId));
                setEnrolledCount(myCourses.length);
                setCurrentEnrollment(matchedCourse || null);
                setIsEnrolled(Boolean(matchedCourse));
            }
            setLoading(false);
        };
        load();
    }, [courseId, userId]);

    const handleEnroll = async () => {
        if (!userId || isEnrolling || isEnrolled) return;
        if (enrolledCount >= MAX_ACTIVE_COURSES) {
            setEnrollError(t('course_limit_reached'));
            return;
        }
        setIsEnrolling(true);
        setEnrollError('');
        try {
            await apiClient.post('/courses/enroll', {
                user_id: userId,
                course_id: Number(courseId),
            });
            setIsEnrolled(true);
            setCurrentEnrollment({
                id: Number(courseId),
                lesson_total: lessons.length,
                completed_lesson_count: 0,
                last_completed_lesson_id: 0,
                viewed_lesson_id: 0,
                practice_question_index: 0,
                next_lesson_id: lessons[0]?.lesson_id,
                next_lesson_title: lessons[0]?.title,
                next_lesson_title_localized: lessons[0]?.title_localized,
            });
            setEnrolledCount((count) => Math.min(count + 1, MAX_ACTIVE_COURSES));
        } catch (err) {
            if (err.response?.status === 409) {
                setEnrollError(t('course_limit_reached'));
            } else {
                setEnrollError(t('course_enroll_failed'));
            }
        } finally {
            setIsEnrolling(false);
        }
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
                            onClick={() => navigate(`/study/${courseId}`)}
                            className="flex items-center gap-3 px-12 py-5 bg-slate-900 text-white rounded-2xl font-black text-xl hover:bg-blue-600 active:scale-95 transition-all shadow-lg shadow-slate-300/40"
                        >
                            <Play size={22} fill="white" /> {t('course_start_learning')}
                        </button>
                    ) : (
                        <button
                            onClick={handleEnroll}
                            disabled={isEnrolling || enrolledCount >= MAX_ACTIVE_COURSES}
                            className="flex items-center gap-3 px-12 py-5 bg-blue-600 text-white rounded-2xl font-black text-xl hover:bg-slate-900 active:scale-95 disabled:opacity-70 disabled:cursor-wait transition-all shadow-lg shadow-blue-200/70"
                        >
                            {isEnrolling ? <Loader2 size={22} className="animate-spin" /> : <PlusCircle size={22} />}
                            {isEnrolling ? t('course_adding_learning') : t('classroom_join_course')}
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

                {/* 入门基础 */}
                <motion.section variants={stagger} initial="hidden" animate="show" className="mb-10">
                    <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-4">{t('course_foundations')}</h2>
                    <div className="flex gap-3 flex-wrap">
                        {[
                            { label: t('course_intro_card_title'), sub: t('course_intro_card_sub'), icon: '✨', path: '/learn/intro', hover: 'hover:border-amber-200 group-hover:text-amber-600' },
                            { label: t('course_hanzi_card_title'), sub: t('course_hanzi_card_sub'), icon: '字', path: '/learn/hanzi', hover: 'hover:border-indigo-200 group-hover:text-indigo-600' },
                            { label: t('course_pinyin_card_title'), sub: t('course_pinyin_card_sub'), icon: 'abc', path: '/learn/pinyin', hover: 'hover:border-blue-200 group-hover:text-blue-600' },
                            { label: t('course_typing_card_title'), sub: t('course_typing_card_sub'), icon: '⌨', path: '/learn/typing', hover: 'hover:border-green-200 group-hover:text-green-600' },
                        ].map(item => (
                            <motion.button
                                key={item.path}
                                variants={fadeInUp}
                                onClick={() => navigate(item.path, { state: { from: coursePath } })}
                                className={`flex items-center gap-3 px-5 py-3.5 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-all group ${item.hover}`}
                            >
                                <span className="text-2xl w-8 text-center font-black text-slate-500">{item.icon}</span>
                                <div className="text-left">
                                    <div className="font-black text-slate-800 text-sm transition-colors">{item.label}</div>
                                    <div className="text-xs text-slate-400">{item.sub}</div>
                                </div>
                                <ChevronRight size={14} className="text-slate-300 ml-1" />
                            </motion.button>
                        ))}
                    </div>
                </motion.section>

                {/* Lesson list */}
                <section>
                    <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-4">{t('course_all_lessons')}</h2>
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
                                    onClick={() => navigate(`/study/${courseId}?lesson_id=${lesson.lesson_id}&browse=1`)}
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
                </section>
            </div>
        </div>
    );
}
