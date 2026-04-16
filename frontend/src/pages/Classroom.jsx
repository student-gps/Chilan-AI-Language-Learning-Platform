import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { 
    Layers, ChevronRight,
    CheckCircle2, Zap, Loader2, GraduationCap, ChevronDown, Check
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
// 🚀 引入统一的 API 客户端，不再直接使用原始 axios
import apiClient from '../api/apiClient'; 

// 通用底纹
const SUBTLE_PATTERN = `data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg stroke='%23ffffff' stroke-width='1' opacity='0.05'%3E%3Cpath d='M30 0L0 30M60 30L30 60M30 0l30 30M0 30l30 30' /%3E%3C/g%3E%3C/g%3E%3C/svg%3E`;

function FlagChina({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#DE2910" />
            <g fill="#FFDE00">
                <path d="M14 8l1.9 5.7h6L17 17.1l1.9 5.7L14 19.4l-4.9 3.4 1.9-5.7-4.9-3.4h6z" />
                <path d="M24.5 7.5l.8 2.5H28l-2.2 1.5.8 2.5-2.1-1.5-2.2 1.5.8-2.5L21 10h2.7z" />
                <path d="M28 13.5l.8 2.5h2.7L29.3 17.5l.8 2.5-2.1-1.5-2.2 1.5.8-2.5L24.5 16h2.7z" />
                <path d="M28 21l.8 2.5h2.7L29.3 25l.8 2.5-2.1-1.5-2.2 1.5.8-2.5-2.1-1.5h2.7z" />
                <path d="M24 27l.8 2.5h2.7L25.3 31l.8 2.5-2.1-1.5-2.2 1.5.8-2.5-2.1-1.5h2.7z" />
            </g>
        </svg>
    );
}

function FlagUK({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#012169" />
            <path d="M0 0l64 48M64 0L0 48" stroke="#FFF" strokeWidth="10" />
            <path d="M0 0l64 48M64 0L0 48" stroke="#C8102E" strokeWidth="4" />
            <path d="M32 0v48M0 24h64" stroke="#FFF" strokeWidth="16" />
            <path d="M32 0v48M0 24h64" stroke="#C8102E" strokeWidth="8" />
        </svg>
    );
}

function FlagJapan({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#FFFFFF" stroke="#E5E7EB" />
            <circle cx="32" cy="24" r="11" fill="#BC002D" />
        </svg>
    );
}

function FlagFrance({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#FFFFFF" />
            <rect width="21.34" height="48" rx="6" fill="#0055A4" />
            <rect x="42.66" width="21.34" height="48" rx="6" fill="#EF4135" />
        </svg>
    );
}

const LANGUAGE_LABEL_MAP = {
    zh: {
        chinese: '中文',
        english: '英语',
        japanese: '日语',
        french: '法语',
    },
    en: {
        chinese: 'Chinese',
        english: 'English',
        japanese: 'Japanese',
        french: 'French',
    },
    jp: {
        chinese: '中国語',
        english: '英語',
        japanese: '日本語',
        french: 'フランス語',
    },
    fr: {
        chinese: 'Chinois',
        english: 'Anglais',
        japanese: 'Japonais',
        french: 'Français',
    },
    de: {
        chinese: 'Chinesisch',
        english: 'Englisch',
        japanese: 'Japanisch',
        french: 'Französisch',
    },
};

const FLAG_COMPONENT_MAP = {
    chinese: FlagChina,
    english: FlagUK,
    japanese: FlagJapan,
    french: FlagFrance,
};

const LANGUAGE_STYLE_MAP = {
    chinese: {
        bg: 'from-red-500 via-red-600 to-yellow-500',
        shadow: 'shadow-red-200/60',
        ring: 'ring-red-200/60',
    },
    english: {
        bg: 'from-blue-700 via-blue-800 to-red-500',
        shadow: 'shadow-blue-200/60',
        ring: 'ring-blue-200/60',
    },
    japanese: {
        bg: 'from-white via-rose-50 to-red-300',
        shadow: 'shadow-rose-200/60',
        ring: 'ring-rose-200/60',
    },
    french: {
        bg: 'from-blue-700 via-white to-red-500',
        shadow: 'shadow-slate-200/60',
        ring: 'ring-slate-200/60',
    },
};

const parseCourseLanguagePair = (courseName = '') => {
    const match = courseName.match(/learn\s+(.+?)\s+in\s+(.+)/i);
    if (!match) {
        return { learning: 'chinese', native: 'english' };
    }

    const normalize = (value) => {
        const lower = value.trim().toLowerCase();
        if (lower.includes('chinese')) return 'chinese';
        if (lower.includes('english')) return 'english';
        if (lower.includes('japanese')) return 'japanese';
        if (lower.includes('french')) return 'french';
        if (lower.includes('korean')) return 'korean';
        if (lower.includes('spanish')) return 'spanish';
        if (lower.includes('german')) return 'german';
        return lower;
    };

    return {
        learning: normalize(match[1]),
        native: normalize(match[2]),
    };
};

const normalizeLanguage = (value = '') => {
    const lower = String(value).trim().toLowerCase();
    if (lower.includes('chinese') || lower.includes('中文')) return 'chinese';
    if (lower.includes('english') || lower.includes('英语')) return 'english';
    if (lower.includes('japanese') || lower.includes('日语')) return 'japanese';
    if (lower.includes('french') || lower.includes('法语')) return 'french';
    if (lower.includes('korean') || lower.includes('韩语')) return 'korean';
    if (lower.includes('spanish') || lower.includes('西班牙语')) return 'spanish';
    if (lower.includes('german') || lower.includes('德语')) return 'german';
    return lower;
};

const getCourseLanguagePair = (course = {}) => {
    const target = normalizeLanguage(course.target_language);
    const source = normalizeLanguage(course.source_language);
    if (target && source) {
        return { learning: target, native: source };
    }
    return parseCourseLanguagePair(course.name || '');
};

const getCourseVisual = (course = {}) => {
    const { learning, native } = getCourseLanguagePair(course);
    const style = LANGUAGE_STYLE_MAP[learning] || LANGUAGE_STYLE_MAP.chinese;
    return {
        learning,
        native,
        LearningFlag: FLAG_COMPONENT_MAP[learning] || FlagChina,
        NativeFlag: FLAG_COMPONENT_MAP[native] || FlagUK,
        gradientClass: style.bg,
        shadowClass: style.shadow,
        ringClass: style.ring,
    };
};

function formatLanguageLabel(language, locale = 'zh') {
    if (!language) return '';
    return LANGUAGE_LABEL_MAP[locale]?.[language] || LANGUAGE_LABEL_MAP.en?.[language] || (language.charAt(0).toUpperCase() + language.slice(1));
}

function LanguagePill({ course, compact = false }) {
    const { i18n } = useTranslation();
    const visual = getCourseVisual(course);
    const LearningFlag = visual.LearningFlag;
    const NativeFlag = visual.NativeFlag;
    const learningLabel = formatLanguageLabel(visual.learning, i18n.language);
    const nativeLabel = formatLanguageLabel(visual.native, i18n.language);
    const pillPadding = compact ? 'px-3 py-2' : 'px-4 py-2.5';
    const flagSize = compact ? 'w-5 h-5' : 'w-6 h-6';
    const textSize = compact ? 'text-xs' : 'text-sm';

    return (
        <div className={`inline-flex items-center ${compact ? 'gap-1.5' : 'gap-2.5'} flex-wrap`}>
            <div className={`inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/85 shadow-sm ${pillPadding}`}>
                <div className={`${flagSize} rounded-full overflow-hidden ring-1 ${visual.ringClass} shadow-sm`}>
                    <LearningFlag className="w-full h-full" />
                </div>
                <span className={`${textSize} font-black text-slate-700`}>
                    {learningLabel}
                </span>
            </div>
            <span className={`${compact ? 'text-base' : 'text-lg'} text-slate-300 font-black leading-none`}>
                →
            </span>
            <div className={`inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white/85 shadow-sm ${pillPadding}`}>
                <div className={`${flagSize} rounded-full overflow-hidden ring-1 ring-slate-200 shadow-sm`}>
                    <NativeFlag className="w-full h-full" />
                </div>
                <span className={`${textSize} font-black text-slate-700`}>
                    {nativeLabel}
                </span>
            </div>
        </div>
    );
}

export default function Classroom() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    
    const [stats, setStats] = useState({ totalRemaining: 0, totalReviewed: 0, totalNewLearned: 0 });
    const [myCourses, setMyCourses] = useState([]);
    const [allCourses, setAllCourses] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCoursesLoading, setIsCoursesLoading] = useState(false);
    const [learningFilter, setLearningFilter] = useState('all');
    const [nativeFilter, setNativeFilter] = useState('all');

    const userId = localStorage.getItem('chilan_user_id');

    useEffect(() => {
        if (!userId) return;
        const fetchData = async () => {
            setIsLoading(true);
            setIsCoursesLoading(true);
            const [statRes, myCourseRes, coursesRes] = await Promise.allSettled([
                apiClient.get(`/classroom/stats/${userId}`),
                apiClient.get(`/my-courses/${userId}`),
                apiClient.get('/courses'),
            ]);
            if (statRes.status === 'fulfilled') {
                setStats(statRes.value.data);
            } else {
                console.error("加载统计数据失败", statRes.reason);
            }
            if (myCourseRes.status === 'fulfilled') {
                setMyCourses(myCourseRes.value.data);
            } else {
                console.error("加载我的课程失败", myCourseRes.reason);
            }
            if (coursesRes.status === 'fulfilled') {
                setAllCourses(coursesRes.value.data);
            } else {
                console.error("加载课程库失败", coursesRes.reason);
            }
            setIsLoading(false);
            setIsCoursesLoading(false);
        };
        fetchData();
    }, [userId]);

    const languageOptions = React.useMemo(() => {
        const learning = new Set();
        const native = new Set();
        allCourses.forEach((course) => {
            const pair = getCourseLanguagePair(course);
            learning.add(pair.learning);
            native.add(pair.native);
        });
        return {
            learning: ['all', ...Array.from(learning)],
            native: ['all', ...Array.from(native)],
        };
    }, [allCourses]);

    const filteredCourses = React.useMemo(() => {
        return allCourses.filter((course) => {
            const pair = getCourseLanguagePair(course);
            const learningMatch = learningFilter === 'all' || pair.learning === learningFilter;
            const nativeMatch = nativeFilter === 'all' || pair.native === nativeFilter;
            return learningMatch && nativeMatch;
        });
    }, [allCourses, learningFilter, nativeFilter]);

    const enrolledCourseIds = React.useMemo(
        () => new Set(myCourses.map((course) => course.id)),
        [myCourses]
    );

    const handleEnroll = async (courseId) => {
        try {
            await apiClient.post(`/courses/enroll`, {
                user_id: userId,
                course_id: courseId
            });
            // 只刷新"我的课程"，不需要重新拉全部课程
            const res = await apiClient.get(`/my-courses/${userId}`);
            setMyCourses(res.data);
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

    if (isLoading) {
        return (
            <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50 text-slate-500">
                <Loader2 className="animate-spin w-12 h-12 mb-4 text-blue-500" />
                <p className="font-medium tracking-widest uppercase text-sm">Loading Classroom...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 font-sans text-slate-900 pb-20 pt-24 relative overflow-hidden">
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute -top-16 -left-12 w-72 h-72 rounded-full bg-gradient-to-br from-red-100 via-amber-50 to-transparent blur-3xl opacity-70" />
                <div className="absolute top-1/3 right-0 w-80 h-80 rounded-full bg-gradient-to-br from-blue-100 via-sky-50 to-transparent blur-3xl opacity-60" />
                <div className="absolute bottom-0 left-1/3 w-96 h-72 rounded-full bg-gradient-to-tr from-rose-100 via-orange-50 to-transparent blur-3xl opacity-60" />
            </div>
            
            <AnimatePresence mode="wait">
                <motion.div 
                    key={i18n.language}
                    variants={staggerContainer} 
                    initial="hidden" 
                    animate="show" 
                    exit={{ opacity: 0, y: -20, transition: { duration: 0.2 } }}
                    className="max-w-6xl mx-auto px-8 py-12 relative z-10"
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

                    {/* 入门基础模块 */}
                    <motion.section variants={fadeInUp} className="mb-12">
                        <h2 className="text-xl font-black text-slate-700 mb-4 px-1">入门基础</h2>
                        <div className="flex gap-4 flex-wrap">
                            <button
                                onClick={() => navigate('/learn/intro')}
                                className="flex items-center gap-4 px-6 py-4 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md hover:border-blue-200 transition-all group"
                            >
                                <span className="text-3xl">✨</span>
                                <div className="text-left">
                                    <div className="font-black text-slate-800 group-hover:text-blue-600 transition-colors">课程介绍</div>
                                    <div className="text-xs text-slate-400 mt-0.5">理念 · 学习方式 · 路径</div>
                                </div>
                                <ChevronRight size={16} className="text-slate-300 group-hover:text-blue-400 ml-2" />
                            </button>
                            <button
                                onClick={() => navigate('/learn/hanzi')}
                                className="flex items-center gap-4 px-6 py-4 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all group"
                            >
                                <span className="text-3xl">字</span>
                                <div className="text-left">
                                    <div className="font-black text-slate-800 group-hover:text-indigo-600 transition-colors">汉字入门</div>
                                    <div className="text-xs text-slate-400 mt-0.5">笔画 · 部首 · 结构</div>
                                </div>
                                <ChevronRight size={16} className="text-slate-300 group-hover:text-indigo-400 ml-2" />
                            </button>
                            <button
                                onClick={() => navigate('/learn/pinyin')}
                                className="flex items-center gap-4 px-6 py-4 bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-md hover:border-blue-200 transition-all group"
                            >
                                <span className="text-3xl">🔤</span>
                                <div className="text-left">
                                    <div className="font-black text-slate-800 group-hover:text-blue-600 transition-colors">拼音入门</div>
                                    <div className="text-xs text-slate-400 mt-0.5">声母 · 韵母 · 声调</div>
                                </div>
                                <ChevronRight size={16} className="text-slate-300 group-hover:text-blue-400 ml-2" />
                            </button>
                        </div>
                    </motion.section>

                    {/* 2. 课程列表 */}
                    <section>
                        <motion.div variants={fadeInUp} className="flex items-center justify-between mb-8 px-2">
                            <h2 className="text-2xl font-black flex items-center gap-3">
                                <GraduationCap className="text-blue-600" size={28} /> {t('classroom_my_courses')}
                            </h2>
                        </motion.div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                            {myCourses.map((course) => {
                                return (
                                <CourseCard
                                    key={course.id}
                                    course={course}
                                    variants={fadeInUp}
                                    titleAction={t('classroom_start')}
                                    progressValue={course.mastered}
                                    onClick={() => navigate(`/study/${course.id}`)}
                                    isInteractive
                                />
                                );
                            })}
                        </div>
                    </section>

                    <section className="mt-20">
                        <motion.div variants={fadeInUp} className="flex flex-col md:flex-row gap-4 md:items-center md:justify-between mb-8 px-2">
                            <h2 className="text-2xl font-black flex items-center gap-3">
                                <Layers className="text-blue-600" size={28} /> {t('classroom_all_courses')}
                            </h2>
                            <div className="flex flex-wrap gap-3">
                                <FilterSelect
                                    label={t('classroom_filter_learning')}
                                    value={learningFilter}
                                    options={languageOptions.learning}
                                    onChange={setLearningFilter}
                                />
                                <FilterSelect
                                    label={t('classroom_filter_native')}
                                    value={nativeFilter}
                                    options={languageOptions.native}
                                    onChange={setNativeFilter}
                                />
                            </div>
                        </motion.div>

                        {isCoursesLoading ? (
                            <div className="flex flex-col items-center py-20 text-slate-400 gap-4">
                                <Loader2 className="animate-spin" size={32} />
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                                {filteredCourses.map((course) => {
                                    const isEnrolled = enrolledCourseIds.has(course.id);
                                    return (
                                        <CourseCard
                                            key={course.id}
                                            course={course}
                                            variants={fadeInUp}
                                            titleAction={isEnrolled ? t('classroom_in_learning') : t('classroom_join_course')}
                                            progressValue={null}
                                            actionButton={
                                                <button
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        if (!isEnrolled) handleEnroll(course.id);
                                                    }}
                                                    disabled={isEnrolled}
                                                    className={`shrink-0 px-5 py-2.5 rounded-2xl text-sm font-black transition-all ${
                                                        isEnrolled
                                                            ? 'bg-emerald-50 text-emerald-600 cursor-default'
                                                            : 'bg-slate-900 text-white hover:bg-blue-600 active:scale-95'
                                                    }`}
                                                >
                                                    {isEnrolled ? t('classroom_added') : t('btn_add')}
                                                </button>
                                            }
                                            onClick={isEnrolled ? () => navigate(`/study/${course.id}`) : undefined}
                                            isInteractive={isEnrolled}
                                        />
                                    );
                                })}
                            </div>
                        )}

                        {!isCoursesLoading && filteredCourses.length === 0 && (
                            <div className="py-16 text-center text-slate-400 font-semibold">
                                {t('classroom_no_courses')}
                            </div>
                        )}
                    </section>
                </motion.div>
            </AnimatePresence>
        </div>
    );
}

function CourseCard({
    course,
    variants,
    titleAction,
    progressValue,
    actionButton = null,
    onClick,
    isInteractive = false,
}) {
    const { t } = useTranslation();
    const visual = getCourseVisual(course);

    return (
        <motion.div
            variants={variants}
            whileHover={{ y: -8, scale: 1.01 }}
            onClick={onClick}
            className={`relative h-64 rounded-[2.5rem] p-8 text-slate-900 shadow-2xl overflow-hidden border border-white/70 bg-gradient-to-br from-white via-white to-slate-50/95 ${visual.shadowClass} ${
                isInteractive ? 'cursor-pointer group' : ''
            }`}
        >
            <div
                className="absolute inset-0 opacity-[0.06]"
                style={{ backgroundImage: `url("${SUBTLE_PATTERN}")`, backgroundSize: '60px 60px' }}
            />
            <div className={`absolute inset-0 opacity-[0.10] bg-gradient-to-br ${visual.gradientClass}`} />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.55),transparent_38%),radial-gradient(circle_at_bottom_left,rgba(255,255,255,0.42),transparent_34%)]" />
            <div className="relative h-full flex flex-col justify-between z-10">
                <div>
                    <h3 className="text-3xl font-black mb-1 tracking-tight">{course.name}</h3>
                    <div className="mt-5">
                        <LanguagePill course={course} />
                    </div>
                    {progressValue !== null && (
                        <div className="flex items-center gap-3 mt-6">
                            <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                <div className={`h-full w-1/6 rounded-full bg-gradient-to-r ${visual.gradientClass}`}></div>
                            </div>
                            <p className="text-xs font-bold text-slate-500">{t('classroom_mastered')}: {progressValue}</p>
                        </div>
                    )}
                </div>
                <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-bold text-slate-700 uppercase tracking-widest flex items-center gap-2">
                        {titleAction}
                        <ChevronRight size={16} className={isInteractive ? 'group-hover:translate-x-1 transition-transform' : ''} />
                    </span>
                    {actionButton}
                </div>
            </div>
        </motion.div>
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

function FilterSelect({ label, value, options, onChange }) {
    const { t, i18n } = useTranslation();
    const [isOpen, setIsOpen] = useState(false);
    const selectedLabel = value === 'all' ? t('classroom_filter_all') : formatLanguageLabel(value, i18n.language);

    useEffect(() => {
        const handlePointerDown = () => {
            setIsOpen(false);
        };

        if (isOpen) {
            window.addEventListener('pointerdown', handlePointerDown);
        }

        return () => {
            window.removeEventListener('pointerdown', handlePointerDown);
        };
    }, [isOpen]);

    return (
        <div className="relative min-w-[220px] rounded-[1.5rem] border border-slate-200/80 bg-white/90 p-2 shadow-md shadow-slate-200/50">
            <div className="mb-2 px-2">
                <span className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400 whitespace-nowrap">
                    {label}
                </span>
            </div>
            <div className="relative" onPointerDown={(e) => e.stopPropagation()}>
                <button
                    type="button"
                    onClick={() => setIsOpen((open) => !open)}
                    className={`w-full rounded-[1.15rem] border px-4 py-3.5 text-left text-sm font-black text-slate-700 outline-none shadow-inner shadow-white/60 transition ${
                        isOpen
                            ? 'border-blue-300 bg-gradient-to-br from-white via-white to-blue-50 ring-4 ring-blue-100'
                            : 'border-slate-200/80 bg-gradient-to-br from-slate-50 via-white to-slate-100 hover:border-slate-300'
                    }`}
                >
                    <span className="block pr-12 text-base">{selectedLabel}</span>
                    <div className="pointer-events-none absolute inset-y-0 right-3 top-0 flex items-center">
                        <div className={`flex h-8 w-8 items-center justify-center rounded-full bg-white/90 shadow-sm ring-1 transition-all ${
                            isOpen ? 'text-blue-500 ring-blue-200' : 'text-slate-400 ring-slate-200/80'
                        }`}>
                            <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                        </div>
                    </div>
                </button>

                <AnimatePresence>
                    {isOpen && (
                        <motion.div
                            initial={{ opacity: 0, y: 10, scale: 0.98 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 6, scale: 0.98 }}
                            transition={{ duration: 0.16 }}
                            className="absolute left-0 right-0 top-[calc(100%+0.65rem)] z-30 overflow-hidden rounded-[1.35rem] border border-slate-200/80 bg-white/95 p-2 shadow-2xl shadow-slate-300/40 backdrop-blur"
                        >
                            <div className="space-y-1">
                                {options.map((option) => {
                                    const optionLabel = option === 'all'
                                        ? t('classroom_filter_all')
                                        : formatLanguageLabel(option, i18n.language);
                                    const isSelected = option === value;

                                    return (
                                        <button
                                            key={option}
                                            type="button"
                                            onClick={() => {
                                                onChange(option);
                                                setIsOpen(false);
                                            }}
                                            className={`flex w-full items-center justify-between rounded-[1rem] px-4 py-3 text-left text-sm font-black transition-all ${
                                                isSelected
                                                    ? 'bg-gradient-to-r from-blue-600 to-indigo-500 text-white shadow-lg shadow-blue-200/70'
                                                    : 'text-slate-600 hover:bg-slate-50'
                                            }`}
                                        >
                                            <span>{optionLabel}</span>
                                            {isSelected && <Check size={16} />}
                                        </button>
                                    );
                                })}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
