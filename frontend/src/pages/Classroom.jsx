import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { 
    Layers, ChevronRight, X, Plus, 
    CheckCircle2, Zap, Loader2, GraduationCap 
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

// 通用底纹
const SUBTLE_PATTERN = `data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg stroke='%23ffffff' stroke-width='1' opacity='0.05'%3E%3Cpath d='M30 0L0 30M60 30L30 60M30 0l30 30M0 30l30 30' /%3E%3C/g%3E%3C/g%3E%3C/svg%3E`;

export default function Classroom() {
    // 🌟 核心修改 1：提取了 i18n 对象
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    
    const [stats, setStats] = useState({ totalRemaining: 0, totalReviewed: 0, totalNewLearned: 0 });
    const [myCourses, setMyCourses] = useState([]);
    const [allCourses, setAllCourses] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCoursesLoading, setIsCoursesLoading] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);

    const userId = localStorage.getItem('chilan_user_id');

    useEffect(() => {
        if (userId) fetchData();
    }, [userId]);

    const fetchData = async () => {
        setIsLoading(true);
        try {
            const [statRes, myCourseRes] = await Promise.all([
                axios.get(`http://127.0.0.1:8000/classroom/stats/${userId}`),
                axios.get(`http://127.0.0.1:8000/my-courses/${userId}`)
            ]);
            setStats(statRes.data);
            setMyCourses(myCourseRes.data);
        } catch (err) {
            console.error("加载数据失败", err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleOpenModal = async () => {
        setIsModalOpen(true);
        setIsCoursesLoading(true);
        try {
            const res = await axios.get('http://127.0.0.1:8000/courses');
            setAllCourses(res.data);
        } catch (err) {
            console.error("加载课程库失败", err);
        } finally {
            setIsCoursesLoading(false);
        }
    };

    const handleEnroll = async (courseId) => {
        try {
            await axios.post(`http://127.0.0.1:8000/courses/enroll`, { 
                user_id: userId, 
                course_id: courseId 
            });
            setIsModalOpen(false);
            fetchData();
        } catch (err) {
            alert("订阅失败");
        }
    };

    // 统一的入场动画配置
    const staggerContainer = {
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { staggerChildren: 0.1 } }
    };

    const fadeInUp = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 120, damping: 20 } }
    };

    // 优雅的 Loading 界面
    if (isLoading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-500">
                <Loader2 className="animate-spin w-12 h-12 mb-4 text-blue-500" />
                <p className="font-medium tracking-widest uppercase text-sm">Loading Classroom...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 font-sans text-slate-900 pb-20 pt-24">
            
            {/* 🌟 核心修复：加入 AnimatePresence 并设置 mode="wait" (先出后进) */}
            <AnimatePresence mode="wait">
                <motion.div 
                    key={i18n.language}
                    variants={staggerContainer} 
                    initial="hidden" 
                    animate="show" 
                    exit={{ opacity: 0, y: -20, transition: { duration: 0.2 } }} // 🌟 增加秒退出的过渡动画
                    className="max-w-6xl mx-auto px-8 py-12"
                >
                    
                    {/* 1. 顶部统计 */}
                    <header className="flex flex-col md:flex-row md:items-end justify-between gap-8 mb-16">
                        <motion.div variants={fadeInUp}>
                            <h1 className="text-5xl font-black tracking-tight mb-4">{t('classroom_title')}</h1>
                            <p className="text-slate-500 font-medium">{t('classroom_subtitle')}</p>
                        </motion.div>
                        
                        <motion.div variants={fadeInUp} className="bg-white p-2 rounded-[2.5rem] shadow-xl shadow-slate-200/50 border border-slate-100 flex items-center min-h-[92px]">
                            <StatItem icon={<CheckCircle2 size={20} />} color="text-emerald-500 bg-emerald-50" label={t('classroom_reviewed_today')} value={stats.totalReviewed} />
                            <div className="hidden md:block w-px h-8 bg-slate-100"></div>
                            <StatItem icon={<Layers size={20} />} color="text-orange-500 bg-orange-50" label={t('classroom_remaining_today')} value={stats.totalRemaining} />
                            <div className="hidden md:block w-px h-8 bg-slate-100"></div>
                            <StatItem icon={<Zap size={20} />} color="text-blue-500 bg-blue-50" label={t('classroom_new_learned_today')} value={stats.totalNewLearned} />
                        </motion.div>
                    </header>

                    {/* 2. 课程列表 */}
                    <section>
                        <motion.div variants={fadeInUp} className="flex items-center justify-between mb-8 px-2">
                            <h2 className="text-2xl font-black flex items-center gap-3">
                                <GraduationCap className="text-blue-600" size={28} /> {t('classroom_my_courses')}
                            </h2>
                            <button 
                                onClick={handleOpenModal}
                                className="w-12 h-12 bg-white shadow-lg text-blue-600 rounded-2xl flex items-center justify-center hover:bg-blue-600 hover:text-white transition-all active:scale-95"
                            >
                                <Plus size={24} />
                            </button>
                        </motion.div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {myCourses.map((course) => (
                                <motion.div 
                                    key={course.id}
                                    variants={fadeInUp}
                                    whileHover={{ y: -8, scale: 1.01 }}
                                    onClick={() => navigate(`/study/${course.id}`)}
                                    className={`relative h-64 rounded-[2.5rem] ${course.color} p-8 text-white shadow-2xl shadow-slate-300/40 cursor-pointer overflow-hidden group border-2 border-white/10`}
                                    style={{ 
                                        backgroundImage: `url("${SUBTLE_PATTERN}")`,
                                        backgroundSize: '60px 60px'
                                    }}
                                >
                                    <div className="relative h-full flex flex-col justify-between z-10">
                                        <div>
                                            <h3 className="text-3xl font-black mb-1 tracking-tight">{course.name}</h3>
                                            <div className="flex items-center gap-3 mt-6">
                                                <div className="flex-1 h-1.5 bg-white/30 rounded-full overflow-hidden">
                                                    <div className="h-full bg-white w-1/6 rounded-full"></div>
                                                </div>
                                                <p className="text-xs font-bold opacity-90">{t('classroom_mastered')}: {course.mastered}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-bold opacity-90 uppercase tracking-widest flex items-center gap-2">
                                                {t('classroom_start')} <ChevronRight size={16} className="group-hover:translate-x-1 transition-transform"/>
                                            </span>
                                        </div>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    </section>
                </motion.div>
            </AnimatePresence>

            {/* 3. 选课 Modal */}
            <AnimatePresence>
                {isModalOpen && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
                        <motion.div 
                            initial={{ opacity: 0 }} 
                            animate={{ opacity: 1 }} 
                            exit={{ opacity: 0 }} 
                            onClick={() => setIsModalOpen(false)} 
                            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm" 
                        />
                        <motion.div 
                            initial={{ scale: 0.9, opacity: 0, y: 20 }} 
                            animate={{ scale: 1, opacity: 1, y: 0 }} 
                            exit={{ scale: 0.9, opacity: 0, y: 20 }} 
                            transition={{ type: "spring", stiffness: 300, damping: 25 }}
                            className="relative w-full max-w-xl bg-white rounded-[3rem] shadow-2xl p-10 max-h-[85vh] flex flex-col"
                        >
                            <h2 className="text-3xl font-black mb-8">{t('classroom_add_course')}</h2>
                            <div className="space-y-4 overflow-y-auto pr-2 custom-scrollbar">
                                {isCoursesLoading ? (
                                    <div className="flex flex-col items-center py-20 text-slate-400 gap-4"><Loader2 className="animate-spin" size={32} /></div>
                                ) : (
                                    allCourses.map(course => (
                                        <motion.div 
                                            key={course.id} 
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            className="p-3 border border-slate-100 rounded-[2rem] flex items-center justify-between hover:bg-slate-50 group transition-colors"
                                        >
                                            <div className="flex items-center gap-4">
                                                <div className={`w-16 h-16 rounded-2xl ${course.color} shadow-sm shadow-black/10`} />
                                                <div>
                                                    <p className="font-black text-lg text-slate-800">{course.name}</p>
                                                    <p className="text-xs font-bold text-slate-400 uppercase">{course.id}</p>
                                                </div>
                                            </div>
                                            <button onClick={() => handleEnroll(course.id)} className="mr-2 px-6 py-2 bg-slate-900 text-white text-sm font-bold rounded-xl hover:bg-blue-600 active:scale-95 transition-all">
                                                {t('btn_add')}
                                            </button>
                                        </motion.div>
                                    ))
                                )}
                            </div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>
        </div>
    );
}

function StatItem({ icon, label, value, color }) {
    return (
        <div className="flex items-center gap-4 px-6 py-4 min-w-[150px]">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}>{icon}</div>
            <div>
                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest leading-tight">{label}</p>
                <p className="text-2xl font-black text-slate-900 leading-tight">{value}</p>
            </div>
        </div>
    );
}