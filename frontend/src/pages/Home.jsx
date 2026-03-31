import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion } from 'framer-motion';
import { 
    Brain, Zap, BarChart3, ChevronRight, BookOpen, Coins, Users 
} from 'lucide-react';
import { getAuthState } from '../utils/authStorage';

export default function Home() {
    const { t, i18n } = useTranslation();
    const location = useLocation();
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    // 仅用于 Hero 按钮的跳转逻辑判断
    useEffect(() => {
        const authState = getAuthState();
        setIsLoggedIn(authState.isLoggedIn);
    }, [location]);

    const staggerContainer = {
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { staggerChildren: 0.1 } }
    };

    const fadeInUp = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 120, damping: 20 } }
    };

    return (
        <div className="min-h-screen bg-slate-50 font-sans text-slate-900 selection:bg-blue-100 overflow-x-hidden">
            {/* 导航栏已通过 App.jsx 全局加载，此处不再重复 */}

            {/* Hero Section */}
            <motion.section key={`hero-${i18n.language}`} variants={staggerContainer} initial="hidden" animate="show" className="max-w-6xl mx-auto pt-20 md:pt-32 pb-32 px-6 text-center">
                <motion.div variants={fadeInUp} className="inline-flex items-center px-4 py-1.5 mb-8 text-sm font-semibold text-blue-700 bg-blue-50 rounded-full ring-1 ring-inset ring-blue-700/10 uppercase tracking-widest font-mono">
                    {t('hero_badge')}
                </motion.div>
                <motion.h1 variants={fadeInUp} className="text-5xl md:text-7xl font-black text-slate-900 mb-8 leading-[1.1] tracking-tight">
                    {t('hero_title_1')}<br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-500">
                        {t('hero_title_2')}
                    </span>
                </motion.h1>
                <motion.p variants={fadeInUp} className="text-xl text-slate-500 mb-12 max-w-2xl mx-auto leading-relaxed font-medium">
                    {t('hero_desc')}
                </motion.p>
                <motion.div variants={fadeInUp} className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <Link 
                        to={isLoggedIn ? "/classroom" : "/auth"} 
                        className="group px-10 py-5 bg-slate-900 text-white rounded-2xl font-bold text-lg flex items-center gap-2 hover:bg-blue-600 transition-all shadow-xl shadow-blue-100 active:scale-95"
                    >
                        {t('hero_btn_classroom')} <ChevronRight className="group-hover:translate-x-1 transition-transform" />
                    </Link>
                    <a href="#features" className="px-10 py-5 bg-white text-slate-600 border border-slate-200 rounded-2xl font-bold text-lg hover:bg-slate-50 transition-all">
                        {t('hero_btn_more')}
                    </a>
                </motion.div>
            </motion.section>

            {/* 特性展示区 */}
            <section id="features" className="py-24 bg-white border-t border-slate-100">
                <motion.div key={`features-${i18n.language}`} variants={staggerContainer} initial="hidden" whileInView="show" viewport={{ once: true, amount: 0.1 }} className="max-w-6xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-10">
                    <FeatureCard icon={<Brain size={30} />} title={t('feat_1_title')} desc={t('feat_1_desc')} color="blue" />
                    <FeatureCard icon={<Zap size={30} />} title={t('feat_2_title')} desc={t('feat_2_desc')} color="indigo" />
                    <FeatureCard icon={<BarChart3 size={30} />} title={t('feat_3_title')} desc={t('feat_3_desc')} color="emerald" />
                    <FeatureCard icon={<BookOpen size={30} />} title={t('feat_4_title')} desc={t('feat_4_desc')} color="amber" />
                    <FeatureCard icon={<Coins size={30} />} title={t('feat_5_title')} desc={t('feat_5_desc')} color="rose" />
                    <FeatureCard icon={<Users size={30} />} title={t('feat_6_title')} desc={t('feat_6_desc')} color="cyan" />
                </motion.div>
            </section>

            <footer className="bg-white py-12 border-t border-slate-100 text-center">
                <p className="text-slate-400 text-sm">© 2026 Chilan LRS. Your intelligent language learning partner.</p>
            </footer>
        </div>
    );
}

function FeatureCard({ icon, title, desc, color }) {
    const colorClasses = {
        blue: "bg-blue-600 shadow-blue-100 hover:bg-blue-50/50 hover:border-blue-100",
        indigo: "bg-indigo-600 shadow-indigo-100 hover:bg-indigo-50/50 hover:border-indigo-100",
        emerald: "bg-emerald-600 shadow-emerald-100 hover:bg-emerald-50/50 hover:border-emerald-100",
        amber: "bg-amber-500 shadow-amber-100 hover:bg-amber-50/50 hover:border-amber-100",
        rose: "bg-rose-500 shadow-rose-100 hover:bg-rose-50/50 hover:border-rose-100",
        cyan: "bg-cyan-500 shadow-cyan-100 hover:bg-cyan-50/50 hover:border-cyan-100"
    };

    return (
        <motion.div variants={{ hidden: { opacity: 0, y: 20 }, show: { opacity: 1, y: 0 } }} className={`p-8 rounded-3xl bg-slate-50 transition-all border border-transparent ${colorClasses[color].split(' ').slice(2).join(' ')} group`}>
            <div className={`w-14 h-14 ${colorClasses[color].split(' ')[0]} rounded-2xl flex items-center justify-center text-white mb-6 shadow-lg ${colorClasses[color].split(' ')[1]} group-hover:scale-110 transition-transform`}>
                {icon}
            </div>
            <h3 className="text-2xl font-bold text-slate-900 mb-4">{title}</h3>
            <p className="text-slate-500 leading-relaxed">{desc}</p>
        </motion.div>
    );
}
