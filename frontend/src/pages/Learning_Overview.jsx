import React from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Brain, Calendar, Flame, GraduationCap, ChevronRight, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../api/apiClient';
import { overviewStatsQuery } from '../api/queries';
import { getAuthState } from '../utils/authStorage';

const fadeInUp = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 120, damping: 20 } },
};

const stagger = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.08 } },
};

export default function Learning_Overview() {
    const { t } = useTranslation();
    const { userId } = getAuthState();

    const { data: overviewStats, isLoading: isStatsLoading } = useQuery(overviewStatsQuery(userId));

    const { data: tasks = [], isLoading: isTasksLoading } = useQuery({
        queryKey: ['daily-tasks', String(userId)],
        queryFn:  () => apiClient.get(`/daily_tasks/${userId}`).then(r => r.data),
        staleTime: 60 * 1000,
        enabled:  Boolean(userId),
    });

    const isLoading = isStatsLoading || isTasksLoading;

    return (
        <div className="min-h-screen bg-slate-50 p-8 font-sans">
            <div className="max-w-5xl mx-auto">
                {/* 返回教室，而不是首页 */}
                <Link
                    to="/classroom"
                    className="inline-flex items-center gap-2 text-slate-400 hover:text-blue-600 font-bold text-sm mb-8 transition-colors group"
                >
                    <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
                    {t('teaching_back_to_course')}
                </Link>

                <motion.div variants={stagger} initial="hidden" animate="show">
                    <motion.header variants={fadeInUp} className="mb-12">
                        <h1 className="text-4xl font-black text-slate-900 tracking-tight">{t('overview_title')}</h1>
                        <p className="text-slate-500 font-medium mt-2">{t('overview_subtitle')}</p>
                    </motion.header>

                    <motion.div variants={fadeInUp} className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                        <StatCard
                            icon={<Flame className="text-orange-500" />}
                            label={t('overview_due_review')}
                            value={isStatsLoading ? '—' : (overviewStats?.due_count ?? tasks.length)}
                            sub={t('overview_tasks_unit')}
                            loading={isStatsLoading}
                        />
                        <StatCard
                            icon={<GraduationCap className="text-blue-500" />}
                            label={t('overview_stability')}
                            value={isStatsLoading ? '—' : `${Math.round((overviewStats?.avg_stability ?? 0) * 100)}%`}
                            sub={t('overview_stability_unit')}
                            loading={isStatsLoading}
                        />
                        <StatCard
                            icon={<Brain className="text-purple-500" />}
                            label={t('overview_learning_stage')}
                            value={isStatsLoading ? '—' : (overviewStats?.level ?? 'L1')}
                            sub={t('overview_level_unit')}
                            loading={isStatsLoading}
                        />
                    </motion.div>

                    <motion.div variants={fadeInUp} className="bg-white rounded-[2.5rem] shadow-xl shadow-slate-200/40 p-8 border border-slate-100">
                        <h2 className="text-xl font-black mb-8 flex items-center gap-3">
                            <Calendar className="text-blue-600" size={20} /> {t('overview_today_list')}
                        </h2>

                        {isTasksLoading ? (
                            <div className="space-y-3 py-2">
                                {[1, 2, 3].map(i => (
                                    <div key={i} className="h-14 rounded-2xl bg-slate-100 animate-pulse" />
                                ))}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {tasks.length > 0 ? (
                                    tasks.map(task => (
                                        <div
                                            key={task.id}
                                            className="flex items-center justify-between p-5 bg-slate-50 rounded-2xl hover:bg-white hover:shadow-md transition-all cursor-pointer group border border-transparent hover:border-blue-100"
                                        >
                                            <span className="font-bold text-slate-700">{task.text}</span>
                                            <ChevronRight size={18} className="text-slate-300 group-hover:text-blue-600 transition-colors" />
                                        </div>
                                    ))
                                ) : (
                                    <div className="py-10 text-center text-slate-400 font-bold">
                                        {t('overview_all_done')}
                                    </div>
                                )}
                            </div>
                        )}
                    </motion.div>
                </motion.div>
            </div>
        </div>
    );
}

function StatCard({ icon, label, value, sub, loading = false }) {
    return (
        <div className="bg-white p-7 rounded-[2rem] border border-slate-100 shadow-sm">
            <div className="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center mb-5">{icon}</div>
            <p className="text-slate-400 text-xs font-black uppercase tracking-widest mb-1">{label}</p>
            <div className="flex items-baseline gap-2">
                {loading ? (
                    <div className="h-8 w-16 rounded-xl bg-slate-200 animate-pulse" />
                ) : (
                    <>
                        <span className="text-3xl font-black text-slate-900">{value}</span>
                        <span className="text-[10px] font-bold text-slate-300 uppercase">{sub}</span>
                    </>
                )}
            </div>
        </div>
    );
}
