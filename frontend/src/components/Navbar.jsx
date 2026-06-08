import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import {
    User, Globe, ChevronDown, CheckCircle2,
    LogOut, Settings, LayoutDashboard, GraduationCap
} from 'lucide-react';
import { clearAuthStorage, getAuthState } from '../utils/authStorage';
import { getUiLanguageOption, UI_LANGUAGE_OPTIONS } from '../utils/languageOptions';
import { useQueryClient } from '@tanstack/react-query';
import { coursesQuery, myCoursesQuery, classroomStatsQuery } from '../api/queries';

export default function Navbar() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const location = useLocation();
    const queryClient = useQueryClient();

    const [isLangOpen, setIsLangOpen] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    const [userEmail, setUserEmail] = useState('');
    const [userId, setUserId] = useState(null);

    const langRef = useRef(null);
    const userRef = useRef(null);
    const timerRef = useRef(null);

    useEffect(() => {
        const authState = getAuthState();
        setIsLoggedIn(authState.isLoggedIn);
        setUserEmail(authState.userEmail || '');
        setUserId(authState.userId || null);
        setIsLangOpen(false);
        setIsUserMenuOpen(false);
    }, [location]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (langRef.current && !langRef.current.contains(event.target)) setIsLangOpen(false);
            if (userRef.current && !userRef.current.contains(event.target)) setIsUserMenuOpen(false);
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const resetTimer = () => {
        if (timerRef.current) clearTimeout(timerRef.current);
        if (isUserMenuOpen || isLangOpen) {
            timerRef.current = setTimeout(() => {
                setIsUserMenuOpen(false);
                setIsLangOpen(false);
            }, 3000);
        }
    };
    const clearTimer = () => { if (timerRef.current) clearTimeout(timerRef.current); };

    // 悬停教室入口时预加载数据，让用户点进去时感觉近乎瞬间
    const handleClassroomPrefetch = () => {
        if (!userId) return;
        queryClient.prefetchQuery(classroomStatsQuery(userId));
        queryClient.prefetchQuery(myCoursesQuery(userId));
        queryClient.prefetchQuery(coursesQuery());
    };

    const handleLogout = () => {
        clearAuthStorage();
        setIsLoggedIn(false);
        navigate('/');
    };

    const languages = UI_LANGUAGE_OPTIONS;
    const currentLang = getUiLanguageOption(i18n.language);

    // 🌟 核心：引入统一的动画变体配置
    const staggerContainer = {
        hidden: { opacity: 0 },
        show: { opacity: 1, transition: { staggerChildren: 0.1 } }
    };

    const fadeInUp = {
        hidden: { opacity: 0, y: -10 },
        show: { opacity: 1, y: 0, transition: { type: "spring", stiffness: 120, damping: 20 } }
    };

    return (
        <nav className="flex items-center justify-between px-8 py-4 bg-white/80 backdrop-blur-md fixed top-0 left-0 w-full z-50 border-b border-slate-100">
            {/* Logo 部分 */}
            <Link to="/" className="text-2xl font-black text-blue-600 tracking-tighter flex items-center gap-2 group">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white text-sm shadow-lg shadow-blue-200 group-hover:scale-110 transition-transform">C</div>
                CHILAN <span className="text-slate-400 font-light text-xl italic font-serif">LRS</span>
            </Link>

            {/* 🌟 核心魔法：使用 motion.div 包裹右侧功能区，并绑定 key={i18n.language} */}
            <motion.div 
                key={i18n.language} 
                variants={staggerContainer}
                initial="hidden"
                animate="show"
                className="flex items-center gap-4 md:gap-6"
            >
                {/* --- 语言选择模块 --- */}
                {/* 🌟 给子元素加上 variants={fadeInUp} */}
                <motion.div variants={fadeInUp} className="relative" ref={langRef} onMouseMove={resetTimer} onMouseLeave={clearTimer}>
                    <button 
                        onClick={() => setIsLangOpen(!isLangOpen)} 
                        className="flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-slate-100 transition-all text-slate-600 font-bold text-sm"
                    >
                        <Globe size={18} className="text-blue-500" />
                        <span className="text-lg leading-none">{currentLang.flag}</span>
                        <ChevronDown size={14} className={`transition-transform duration-300 ${isLangOpen ? 'rotate-180' : ''}`} />
                    </button>

                    <AnimatePresence>
                        {isLangOpen && (
                            <motion.div 
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                className="absolute right-0 mt-2 w-48 bg-white border border-slate-100 rounded-2xl shadow-2xl py-2 z-50 origin-top-right"
                            >
                                {languages.map((item) => (
                                    <button 
                                        key={item.code} 
                                        onClick={() => { i18n.changeLanguage(item.code); setIsLangOpen(false); }} 
                                        className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium transition-colors hover:bg-blue-50 ${i18n.language.startsWith(item.code) ? 'text-blue-600 bg-blue-50/50' : 'text-slate-600'}`}
                                    >
                                        <span className="text-xl">{item.flag}</span>
                                        <span className="flex flex-col items-start leading-tight">
                                            <span>{item.nativeName}</span>
                                            <span className="text-[10px] font-semibold text-slate-400">{item.name}</span>
                                        </span>
                                        {i18n.language.startsWith(item.code) && <CheckCircle2 size={14} className="ml-auto" />}
                                    </button>
                                ))}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>

                {/* --- 账户/登录模块 --- */}
                {isLoggedIn ? (
                    // 🌟 给子元素加上 variants={fadeInUp}
                    <motion.div variants={fadeInUp} className="relative" ref={userRef} onMouseMove={resetTimer} onMouseLeave={clearTimer}>
                        <button 
                            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)} 
                            className="flex items-center gap-3 pl-3 pr-2 py-1.5 bg-slate-50 hover:bg-white rounded-2xl transition-all border border-slate-200 shadow-sm group"
                        >
                            <span className="text-sm font-bold text-slate-700 px-1 hidden sm:inline">{t('nav_profile')}</span>
                            <div className="w-8 h-8 bg-gradient-to-tr from-blue-600 to-indigo-500 rounded-xl flex items-center justify-center text-white shadow-lg shadow-blue-100 group-hover:scale-105 transition-transform">
                                <User size={18} />
                            </div>
                        </button>

                        <AnimatePresence>
                            {isUserMenuOpen && (
                                <motion.div 
                                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                    className="absolute right-0 mt-3 w-60 bg-white border border-slate-100 rounded-[2rem] shadow-2xl py-3 z-50 overflow-hidden"
                                >
                                    <div className="px-6 py-4 mb-2 bg-slate-50/50 border-b border-slate-50">
                                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mb-1">{t('nav_account_title')}</p>
                                        <p className="text-sm font-bold text-slate-800 truncate">{userEmail}</p>
                                    </div>
                                    
                                    <Link to="/overview" className="flex items-center gap-3 px-6 py-3.5 text-sm font-bold text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-colors">
                                        <LayoutDashboard size={18} className="text-blue-500" /> {t('nav_overview')}
                                    </Link>

                                    <Link
                                        to="/classroom"
                                        onMouseEnter={handleClassroomPrefetch}
                                        className="flex items-center gap-3 px-6 py-3.5 text-sm font-bold text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                                    >
                                        <GraduationCap size={18} className="text-blue-500" /> {t('classroom_title')}
                                    </Link>
                                    
                                    <Link to="/settings" className="flex items-center gap-3 px-6 py-3.5 text-sm font-bold text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-colors">
                                        <Settings size={18} /> {t('nav_settings')}
                                    </Link>

                                    <div className="h-px bg-slate-50 my-1 mx-4"></div>

                                    <button 
                                        onClick={handleLogout}
                                        className="w-full flex items-center gap-3 px-6 py-4 text-sm font-bold text-red-500 hover:bg-red-50 transition-colors text-left"
                                    >
                                        <LogOut size={18} /> {t('nav_logout')}
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                ) : (
                    // 🌟 给子元素加上 variants={fadeInUp}
                    <motion.div variants={fadeInUp}>
                        <Link to="/auth" className="group flex items-center gap-2 px-6 py-2.5 bg-slate-900 text-white rounded-xl font-bold hover:bg-blue-600 shadow-xl shadow-slate-200 transition-all active:scale-95">
                            <User size={18} className="text-slate-400 group-hover:text-white" />
                            <span>{t('nav_auth')}</span>
                        </Link>
                    </motion.div>
                )}
            </motion.div>
        </nav>
    );
}
