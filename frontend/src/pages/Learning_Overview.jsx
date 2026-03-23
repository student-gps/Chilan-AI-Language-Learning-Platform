import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Brain, Calendar, Flame, GraduationCap, ChevronRight, Loader2, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';

export default function Learning_Overview() {
    const { t } = useTranslation();
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchTasks = async () => {
            const userId = localStorage.getItem('chilan_user_id');
            try {
                const res = await axios.get(`https://chilan-ai-language-learning-platform.onrender.com/daily_tasks/${userId}`);
                setTasks(res.data);
            } catch (err) { console.error(err); }
            finally { setLoading(false); }
        };
        fetchTasks();
    }, []);

    return (
        <div className="min-h-screen bg-slate-50 p-8 font-sans">
            <div className="max-w-5xl mx-auto">
                <Link to="/" className="inline-flex items-center gap-2 text-slate-400 hover:text-blue-600 font-bold text-sm mb-8 transition-colors group">
                    <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
                    {t('auth_back_home')}
                </Link>

                <header className="mb-12">
                    <h1 className="text-4xl font-black text-slate-900 tracking-tight">{t('overview_title')}</h1>
                    <p className="text-slate-500 font-medium mt-2">基于 FSRS 算法为您定制的今日学习计划</p>
                </header>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
                    <StatCard icon={<Flame className="text-orange-500" />} label="待复习" value={tasks.length} sub="Tasks" />
                    <StatCard icon={<GraduationCap className="text-blue-500" />} label="稳定性" value="88%" sub="Stability" />
                    <StatCard icon={<Brain className="text-purple-500" />} label="学习阶段" value="L3" sub="Level" />
                </div>

                <div className="bg-white rounded-[2.5rem] shadow-xl shadow-slate-200/40 p-8 border border-slate-100">
                    <h2 className="text-xl font-black mb-8 flex items-center gap-3"><Calendar className="text-blue-600" size={20}/> 今日清单</h2>
                    {loading ? <Loader2 className="animate-spin mx-auto text-blue-500 my-10" /> : (
                        <div className="space-y-4">
                            {tasks.map(task => (
                                <div key={task.id} className="flex items-center justify-between p-5 bg-slate-50 rounded-2xl hover:bg-white hover:shadow-md transition-all cursor-pointer group border border-transparent hover:border-blue-100">
                                    <span className="font-bold text-slate-700">{task.text}</span>
                                    <ChevronRight size={18} className="text-slate-300 group-hover:text-blue-600 transition-colors" />
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function StatCard({ icon, label, value, sub }) {
    return (
        <div className="bg-white p-7 rounded-[2rem] border border-slate-100 shadow-sm">
            <div className="w-10 h-10 bg-slate-50 rounded-xl flex items-center justify-center mb-5">{icon}</div>
            <p className="text-slate-400 text-xs font-black uppercase tracking-widest mb-1">{label}</p>
            <div className="flex items-baseline gap-2">
                <span className="text-3xl font-black text-slate-900">{value}</span>
                <span className="text-[10px] font-bold text-slate-300 uppercase">{sub}</span>
            </div>
        </div>
    );
}