import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { motion, AnimatePresence } from 'framer-motion';
import { 
    User, Globe, ChevronDown, CheckCircle2, 
    LogOut, Settings, LayoutDashboard
} from 'lucide-react';

export default function Navbar() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const location = useLocation();
    
    // 状态管理
    const [isLangOpen, setIsLangOpen] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
    const [userEmail, setUserEmail] = useState('');

    // 引用管理（用于监控点击区域和计时器）
    const langRef = useRef(null);
    const userRef = useRef(null);
    const timerRef = useRef(null);

    // 1. 初始化登录状态与路由监听
    useEffect(() => {
        const token = localStorage.getItem('chilan_token');
        const email = localStorage.getItem('chilan_user_email');
        setIsLoggedIn(!!token);
        setUserEmail(email || '');
        
        // 每次跳转路由，强制关闭所有菜单
        setIsLangOpen(false);
        setIsUserMenuOpen(false);
    }, [location]);

    // 2. 核心逻辑：点击菜单外部自动关闭
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (langRef.current && !langRef.current.contains(event.target)) {
                setIsLangOpen(false);
            }
            if (userRef.current && !userRef.current.contains(event.target)) {
                setIsUserMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // 3. 核心逻辑：3秒无操作自动消失（防抖计时器）
    const resetTimer = () => {
        if (timerRef.current) clearTimeout(timerRef.current);
        if (isUserMenuOpen || isLangOpen) {
            timerRef.current = setTimeout(() => {
                setIsUserMenuOpen(false);
                setIsLangOpen(false);
            }, 3000); // 3秒倒计时
        }
    };

    const clearTimer = () => {
        if (timerRef.current) clearTimeout(timerRef.current);
    };

    const handleLogout = () => {
        localStorage.removeItem('chilan_token');
        localStorage.removeItem('chilan_user_id');
        localStorage.removeItem('chilan_user_email');
        setIsLoggedIn(false);
        navigate('/');
    };

    const languages = [
        { code: 'zh', name: '简体中文', flag: '🇨🇳' },
        { code: 'en', name: 'English', flag: '🇺🇸' },
        { code: 'jp', name: '日本語', flag: '🇯🇵' },
        { code: 'fr', name: 'Français', flag: '🇫🇷' },
        { code: 'de', name: 'Deutsch', flag: '🇩🇪' }
    ];
    const currentLang = languages.find(l => i18n.language.startsWith(l.code)) || languages[0];

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
                                        <span className="text-xl">{item.flag}</span> {item.name}
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