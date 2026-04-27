import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { ChevronRight, BookOpen, Play, ArrowLeft, Loader2 } from 'lucide-react';
import apiClient from '../api/apiClient';

const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 120, damping: 20 } },
};

const stagger = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};

export default function CoursePage() {
    const { courseId } = useParams();
    const navigate = useNavigate();
    const { t } = useTranslation();
    const [lessons, setLessons] = useState([]);
    const [course, setCourse] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const load = async () => {
            setLoading(true);
            const [lessonsRes, coursesRes] = await Promise.allSettled([
                apiClient.get(`/courses/${courseId}/lessons`),
                apiClient.get('/courses'),
            ]);
            if (lessonsRes.status === 'fulfilled') setLessons(lessonsRes.value.data);
            if (coursesRes.status === 'fulfilled') {
                const found = (coursesRes.value.data || []).find(c => String(c.id) === String(courseId));
                setCourse(found || null);
            }
            setLoading(false);
        };
        load();
    }, [courseId]);

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <Loader2 className="animate-spin w-10 h-10 text-blue-500" />
            </div>
        );
    }

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
                        {course?.name || '课程'}
                    </h1>
                </motion.div>

                {/* 开始学习 CTA */}
                <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mb-10 flex justify-center">
                    <button
                        onClick={() => navigate(`/study/${courseId}`)}
                        className="flex items-center gap-3 px-12 py-5 bg-slate-900 text-white rounded-2xl font-black text-xl hover:bg-blue-600 active:scale-95 transition-all shadow-lg shadow-slate-300/40"
                    >
                        <Play size={22} fill="white" /> {t('course_start_learning')}
                    </button>
                </motion.div>

                {/* 入门基础 */}
                <motion.section variants={stagger} initial="hidden" animate="show" className="mb-10">
                    <h2 className="text-sm font-black text-slate-400 uppercase tracking-widest mb-4">{t('course_foundations')}</h2>
                    <div className="flex gap-3 flex-wrap">
                        {[
                            { label: '课程介绍', sub: '理念 · 学习方式 · 路径', icon: '✨', path: '/learn/intro', hover: 'hover:border-amber-200 group-hover:text-amber-600' },
                            { label: '汉字入门', sub: '笔画 · 部首 · 结构', icon: '字', path: '/learn/hanzi', hover: 'hover:border-indigo-200 group-hover:text-indigo-600' },
                            { label: '拼音入门', sub: '声母 · 韵母 · 声调', icon: 'abc', path: '/learn/pinyin', hover: 'hover:border-blue-200 group-hover:text-blue-600' },
                            { label: '电脑打字', sub: '输入法 · 拼音打字 · 练习', icon: '⌨', path: '/learn/typing', hover: 'hover:border-green-200 group-hover:text-green-600' },
                        ].map(item => (
                            <motion.button
                                key={item.path}
                                variants={fadeInUp}
                                onClick={() => navigate(item.path)}
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
                        {lessons.map((lesson, idx) => (
                            <motion.button
                                key={lesson.lesson_id}
                                variants={fadeInUp}
                                onClick={() => navigate(`/study/${courseId}?lesson_id=${lesson.lesson_id}`)}
                                className="flex items-center gap-5 px-6 py-4 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md hover:border-blue-200 transition-all group text-left"
                            >
                                <div className="w-10 h-10 rounded-xl bg-slate-100 group-hover:bg-blue-50 flex items-center justify-center shrink-0 transition-colors">
                                    <BookOpen size={18} className="text-slate-400 group-hover:text-blue-500 transition-colors" />
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
                                </div>
                                <ChevronRight size={18} className="text-slate-300 group-hover:text-blue-400 group-hover:translate-x-1 transition-all shrink-0" />
                            </motion.button>
                        ))}

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
