import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
    Layers, ChevronRight,
    CheckCircle2, Zap, Loader2, GraduationCap, ChevronDown, Check, MinusCircle, X
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../api/apiClient';
import {
    coursesQuery,
    myCoursesQuery,
    classroomStatsQuery,
    queryKeys,
} from '../api/queries';

// 通用底纹
const SUBTLE_PATTERN = `data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg stroke='%23ffffff' stroke-width='1' opacity='0.05'%3E%3Cpath d='M30 0L0 30M60 30L30 60M30 0l30 30M0 30l30 30' /%3E%3C/g%3E%3C/g%3E%3C/svg%3E`;
const MAX_ACTIVE_COURSES = 2;

const cleanCourseDisplayName = (name = '') => String(name || '').replace(/\s*(初级|中级)\s*/g, ' ').trim();

const toNumber = (value, fallback = 0) => {
    const number = Number(value);
    return Number.isFinite(number) ? number : fallback;
};

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

function FlagKorea({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#FFFFFF" />
            <circle cx="32" cy="24" r="11" fill="#CD2E3A" />
            <path d="M21 24 a11 11 0 0 0 22 0z" fill="#003478" />
            <circle cx="32" cy="18.5" r="5.5" fill="#CD2E3A" />
            <circle cx="32" cy="29.5" r="5.5" fill="#003478" />
        </svg>
    );
}

function FlagSpain({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#AA151B" />
            <rect y="12" width="64" height="24" fill="#F1BF00" />
        </svg>
    );
}

function FlagGermany({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#000000" />
            <rect y="16" width="64" height="16" fill="#DD0000" />
            <rect y="32" width="64" height="16" fill="#FFCE00" />
        </svg>
    );
}

function FlagVietnam({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#DA251D" />
            <polygon points="32,10 35.5,21 47,21 37.5,27.5 41,38.5 32,32 23,38.5 26.5,27.5 17,21 28.5,21" fill="#FFFF00" />
        </svg>
    );
}

function FlagPortuguese({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#009C3B" />
            <polygon points="32,5 57,24 32,43 7,24" fill="#FFDF00" />
            <circle cx="32" cy="24" r="9" fill="#002776" />
        </svg>
    );
}

function FlagArabic({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#CE1126" />
            <rect y="16" width="64" height="16" fill="#FFFFFF" />
            <rect y="32" width="64" height="16" fill="#000000" />
        </svg>
    );
}

function FlagThailand({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#A51931" />
            <rect y="9.6" width="64" height="9.6" fill="#F4F5F8" />
            <rect y="19.2" width="64" height="9.6" fill="#2D2A4A" />
            <rect y="28.8" width="64" height="9.6" fill="#F4F5F8" />
        </svg>
    );
}

function FlagRussia({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#FFFFFF" />
            <rect y="16" width="64" height="16" fill="#0039A6" />
            <rect y="32" width="64" height="16" fill="#D52B1E" />
        </svg>
    );
}

function FlagIndonesia({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#CE1126" />
            <rect y="24" width="64" height="24" fill="#FFFFFF" />
        </svg>
    );
}

function FlagMalaysia({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#CC0001" />
            <rect y="6.86" width="64" height="6.86" fill="#FFFFFF" />
            <rect y="20.57" width="64" height="6.86" fill="#FFFFFF" />
            <rect y="34.29" width="64" height="6.86" fill="#FFFFFF" />
            <rect width="32" height="24" fill="#010066" />
            <circle cx="14" cy="12" r="6" fill="#FFCC00" />
            <circle cx="16.5" cy="10" r="4.5" fill="#010066" />
            <polygon points="24,8 25,11 28,11 25.5,13 26.5,16 24,14.5 21.5,16 22.5,13 20,11 23,11" fill="#FFCC00" />
        </svg>
    );
}

function FlagItaly({ className = '' }) {
    return (
        <svg viewBox="0 0 64 48" className={className} aria-hidden="true">
            <rect width="64" height="48" rx="6" fill="#FFFFFF" />
            <rect width="21.33" height="48" rx="6" fill="#009246" />
            <rect x="42.67" width="21.33" height="48" rx="6" fill="#CE2B37" />
        </svg>
    );
}

const LANGUAGE_LABEL_MAP = {
    zh: {
        chinese: '中文', english: '英语', japanese: '日语', french: '法语',
        korean: '韩语', spanish: '西班牙语', german: '德语', vietnamese: '越南语',
        portuguese: '葡萄牙语', arabic: '阿拉伯语', thai: '泰语', russian: '俄语',
        indonesian: '印尼语', malay: '马来语', italian: '意大利语',
    },
    en: {
        chinese: 'Chinese', english: 'English', japanese: 'Japanese', french: 'French',
        korean: 'Korean', spanish: 'Spanish', german: 'German', vietnamese: 'Vietnamese',
        portuguese: 'Portuguese', arabic: 'Arabic', thai: 'Thai', russian: 'Russian',
        indonesian: 'Indonesian', malay: 'Malay', italian: 'Italian',
    },
    jp: {
        chinese: '中国語', english: '英語', japanese: '日本語', french: 'フランス語',
        korean: '韓国語', spanish: 'スペイン語', german: 'ドイツ語', vietnamese: 'ベトナム語',
        portuguese: 'ポルトガル語', arabic: 'アラビア語', thai: 'タイ語', russian: 'ロシア語',
        indonesian: 'インドネシア語', malay: 'マレー語', italian: 'イタリア語',
    },
    fr: {
        chinese: 'Chinois', english: 'Anglais', japanese: 'Japonais', french: 'Français',
        korean: 'Coréen', spanish: 'Espagnol', german: 'Allemand', vietnamese: 'Vietnamien',
        portuguese: 'Portugais', arabic: 'Arabe', thai: 'Thaï', russian: 'Russe',
        indonesian: 'Indonésien', malay: 'Malais', italian: 'Italien',
    },
    de: {
        chinese: 'Chinesisch', english: 'Englisch', japanese: 'Japanisch', french: 'Französisch',
        korean: 'Koreanisch', spanish: 'Spanisch', german: 'Deutsch', vietnamese: 'Vietnamesisch',
        portuguese: 'Portugiesisch', arabic: 'Arabisch', thai: 'Thailändisch', russian: 'Russisch',
        indonesian: 'Indonesisch', malay: 'Malaiisch', italian: 'Italienisch',
    },
};

const FLAG_COMPONENT_MAP = {
    chinese: FlagChina,
    english: FlagUK,
    japanese: FlagJapan,
    french: FlagFrance,
    korean: FlagKorea,
    spanish: FlagSpain,
    german: FlagGermany,
    vietnamese: FlagVietnam,
    portuguese: FlagPortuguese,
    arabic: FlagArabic,
    thai: FlagThailand,
    russian: FlagRussia,
    indonesian: FlagIndonesia,
    malay: FlagMalaysia,
    italian: FlagItaly,
};

const _DEFAULT_STYLE = {
    headerBg: 'bg-blue-50',
    textColor: 'text-slate-800',
    subtitleColor: 'text-slate-400',
    arrowColor: 'text-slate-300',
    barBg: 'bg-slate-300',
    shadow: 'shadow-slate-200/60',
    ring: 'ring-slate-200/60',
};

const LANGUAGE_STYLE_MAP = {
    chinese: _DEFAULT_STYLE, english: _DEFAULT_STYLE, japanese: _DEFAULT_STYLE,
    french: _DEFAULT_STYLE, korean: _DEFAULT_STYLE, spanish: _DEFAULT_STYLE,
    german: _DEFAULT_STYLE, vietnamese: _DEFAULT_STYLE, portuguese: _DEFAULT_STYLE,
    arabic: _DEFAULT_STYLE, thai: _DEFAULT_STYLE, russian: _DEFAULT_STYLE,
    indonesian: _DEFAULT_STYLE, malay: _DEFAULT_STYLE, italian: _DEFAULT_STYLE,
};

const LANGUAGE_CODE_MAP = {
    CN: 'chinese',
    ZH: 'chinese',
    EN: 'english',
    JA: 'japanese',
    JP: 'japanese',
    FR: 'french',
    KO: 'korean',
    KR: 'korean',
    ES: 'spanish',
    DE: 'german',
    VI: 'vietnamese',
    VN: 'vietnamese',
    PT: 'portuguese',
    AR: 'arabic',
    TH: 'thai',
    RU: 'russian',
    ID: 'indonesian',
    MS: 'malay',
    IT: 'italian',
};

const LANGUAGE_BY_COURSE_SLOT = {
    1: 'english',
    2: 'french',
    4: 'japanese',
    5: 'korean',
    6: 'spanish',
    7: 'vietnamese',
    8: 'portuguese',
    9: 'german',
    10: 'arabic',
    11: 'thai',
    12: 'russian',
    13: 'indonesian',
    14: 'malay',
    15: 'italian',
};

const parseCourseIdPair = (courseId) => {
    const numericId = Number(courseId);
    if (!Number.isInteger(numericId)) return null;

    if (LANGUAGE_BY_COURSE_SLOT[numericId]) {
        return { learning: 'chinese', native: LANGUAGE_BY_COURSE_SLOT[numericId] };
    }

    const sourceSlot = numericId - 100;
    if (LANGUAGE_BY_COURSE_SLOT[sourceSlot]) {
        return { learning: 'english', native: LANGUAGE_BY_COURSE_SLOT[sourceSlot] };
    }

    return null;
};

const isKnownLanguage = (language) => Boolean(LANGUAGE_LABEL_MAP.en[language]);

const parseCourseLanguagePair = (courseName = '') => {
    const match = courseName.match(/learn\s+(.+?)\s+in\s+(.+)/i);
    if (!match) {
        return null;
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
        if (lower.includes('vietnamese') || lower.includes('vietnam') || lower.includes('viet')) return 'vietnamese';
        return lower;
    };

    const pair = {
        learning: normalize(match[1]),
        native: normalize(match[2]),
    };
    return isKnownLanguage(pair.learning) && isKnownLanguage(pair.native) ? pair : null;
};

const parseCourseCategoryPair = (category = '') => {
    const match = String(category || '').trim().toUpperCase().match(/^([A-Z]{2})_TO_([A-Z]{2})$/);
    if (!match) return null;

    const native = LANGUAGE_CODE_MAP[match[1]];
    const learning = LANGUAGE_CODE_MAP[match[2]];
    if (!native || !learning) return null;

    return { learning, native };
};

const normalizeLanguage = (value = '') => {
    const lower = String(value).trim().toLowerCase();
    if (['zh', 'zh-cn', 'cn'].includes(lower) || lower.includes('chinese') || lower.includes('中文') || lower.includes('chinois') || lower.includes('chinesisch')) return 'chinese';
    if (['en', 'en-us', 'en-gb'].includes(lower) || lower.includes('english') || lower.includes('英语') || lower.includes('anglais') || lower.includes('englisch')) return 'english';
    if (['ja', 'jp'].includes(lower) || lower.includes('japanese') || lower.includes('日语') || lower.includes('日本') || lower.includes('japonais') || lower.includes('japanisch')) return 'japanese';
    if (lower === 'fr' || lower.includes('french') || lower.includes('fran') || lower.includes('法语') || lower.includes('französisch')) return 'french';
    if (['ko', 'kr'].includes(lower) || lower.includes('korean') || lower.includes('한국') || lower.includes('韩语')) return 'korean';
    if (['es', 'sp'].includes(lower) || lower.includes('spanish') || lower.includes('español') || lower.includes('espagnol') || lower.includes('西班牙语')) return 'spanish';
    if (lower === 'de' || lower.includes('german') || lower.includes('deutsch') || lower.includes('allemand') || lower.includes('德语')) return 'german';
    if (['vi', 'vn'].includes(lower) || lower.includes('viet') || lower.includes('việt') || lower.includes('vietnamese') || lower.includes('越南')) return 'vietnamese';
    if (lower.includes('portugu') || lower.includes('葡萄牙')) return 'portuguese';
    if (lower.includes('عرب') || lower.includes('arabic') || lower.includes('阿拉伯')) return 'arabic';
    if (lower.includes('ไทย') || lower.includes('thai') || lower.includes('泰语')) return 'thai';
    if (lower.includes('русс') || lower.includes('russian') || lower.includes('俄语')) return 'russian';
    if (lower.includes('indonesia') || lower.includes('印尼')) return 'indonesian';
    if (lower.includes('melayu') || lower.includes('malay') || lower.includes('马来')) return 'malay';
    if (lower.includes('italian') || lower.includes('italiano') || lower.includes('意大利')) return 'italian';
    return lower;
};

const getCourseLanguagePair = (course = {}) => {
    const courseIdPair = parseCourseIdPair(course.id ?? course.course_id);
    if (courseIdPair) {
        return courseIdPair;
    }

    const categoryPair = parseCourseCategoryPair(course.category);
    if (categoryPair) {
        return categoryPair;
    }

    const target = normalizeLanguage(course.target_language);
    const source = normalizeLanguage(course.source_language);
    if (isKnownLanguage(target) && isKnownLanguage(source)) {
        return { learning: target, native: source };
    }

    return parseCourseLanguagePair(course.name || '') || { learning: 'chinese', native: 'english' };
};

const hasCourseForFilters = (courses, learning, native) =>
    courses.some((course) => {
        const pair = getCourseLanguagePair(course);
        const learningMatch = learning === 'all' || pair.learning === learning;
        const nativeMatch = native === 'all' || pair.native === native;
        return learningMatch && nativeMatch;
    });

const getCourseVisual = (course = {}) => {
    const { learning, native } = getCourseLanguagePair(course);
    const style = LANGUAGE_STYLE_MAP[native] || LANGUAGE_STYLE_MAP[learning] || LANGUAGE_STYLE_MAP.english;
    return {
        learning,
        native,
        LearningFlag: FLAG_COMPONENT_MAP[learning] || FlagChina,
        NativeFlag: FLAG_COMPONENT_MAP[native] || FlagUK,
        headerBg: style.headerBg,
        textColor: style.textColor,
        subtitleColor: style.subtitleColor,
        arrowColor: style.arrowColor,
        barBg: style.barBg,
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
    const queryClient = useQueryClient();

    // ── UI-only 状态（不是服务端数据，不用 React Query 管理）──────────────────
    const [removingCourseId, setRemovingCourseId] = useState(null);
    const [coursePendingPause, setCoursePendingPause] = useState(null);
    const [learningFilter, setLearningFilter] = useState('all');
    const [nativeFilter, setNativeFilter] = useState('all');

    const userId = localStorage.getItem('chilan_user_id');

    // ── 服务端数据：三个并发查询 ─────────────────────────────────────────────
    const { data: stats = { totalRemaining: 0, totalReviewed: 0, totalNewLearned: 0 } } =
        useQuery(classroomStatsQuery(userId));

    const { data: myCourses = [], isLoading: isMyCoursesLoading } =
        useQuery(myCoursesQuery(userId));

    const { data: allCourses = [], isLoading: isCoursesLoading } =
        useQuery(coursesQuery());

    const isLoading = isMyCoursesLoading && myCourses.length === 0;

    // ── 取消/暂停课程 mutation ────────────────────────────────────────────────
    const removeMutation = useMutation({
        mutationFn: ({ courseId, action }) => apiClient.delete('/courses/enroll', {
            data: { user_id: userId, course_id: Number(courseId), action },
        }),
        onMutate: ({ courseId }) => setRemovingCourseId(courseId),
        onSuccess: () => {
            // 使 my-courses 和 classroom-stats 缓存失效，自动重新拉取
            queryClient.invalidateQueries({ queryKey: queryKeys.myCourses(userId) });
            queryClient.invalidateQueries({ queryKey: queryKeys.classroomStats(userId) });
        },
        onError: () => alert(t('course_remove_failed')),
        onSettled: () => setRemovingCourseId(null),
    });

    // 1课：flex居中；2课：并排两列；3课以上：正常三列网格
    const myCoursesGridClass = myCourses.length === 1
        ? 'flex justify-center'
        : myCourses.length === 2
            ? 'grid grid-cols-1 md:grid-cols-2 gap-8 md:max-w-2xl md:mx-auto'
            : 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8';

    const languageOptions = React.useMemo(() => {
        const learning = new Set();
        const native = new Set();
        allCourses.forEach((course) => {
            const pair = getCourseLanguagePair(course);
            learning.add(pair.learning);
            native.add(pair.native);
        });
        const sortLanguages = (items) => Array.from(items).sort((a, b) => (
            formatLanguageLabel(a, i18n.language).localeCompare(formatLanguageLabel(b, i18n.language), i18n.language)
        ));
        return {
            learning: ['all', ...sortLanguages(learning)],
            native: ['all', ...sortLanguages(native)],
        };
    }, [allCourses, i18n.language]);

    const filteredCourses = React.useMemo(() => {
        return allCourses.filter((course) => {
            const pair = getCourseLanguagePair(course);
            const learningMatch = learningFilter === 'all' || pair.learning === learningFilter;
            const nativeMatch = nativeFilter === 'all' || pair.native === nativeFilter;
            return learningMatch && nativeMatch;
        });
    }, [allCourses, learningFilter, nativeFilter]);

    useEffect(() => {
        if (!allCourses.length || hasCourseForFilters(allCourses, learningFilter, nativeFilter)) return;
        if (learningFilter !== 'all') { setLearningFilter('all'); return; }
        if (nativeFilter !== 'all') { setNativeFilter('all'); }
    }, [allCourses, learningFilter, nativeFilter]);

    const handleLearningFilterChange = React.useCallback((nextLearning) => {
        setLearningFilter(nextLearning);
        setNativeFilter('all');
    }, []);

    const handleNativeFilterChange = React.useCallback((nextNative) => {
        setNativeFilter(nextNative);
        setLearningFilter('all');
    }, []);

    const enrolledCourseIds = React.useMemo(
        () => new Set(myCourses.map((course) => course.id)),
        [myCourses]
    );

    const handleRemoveCourse = (courseId, action = 'pause') => {
        if (!userId || removingCourseId) return;
        removeMutation.mutate({ courseId, action });
    };

    const handleConfirmPauseCourse = (action = 'pause') => {
        if (!coursePendingPause) return;
        handleRemoveCourse(coursePendingPause.id, action);
        setCoursePendingPause(null);
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

                    {/* 2. 课程列表 */}
                    <section>
                        <motion.div variants={fadeInUp} className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between mb-8 px-2">
                            <h2 className="text-2xl font-black flex items-center gap-3">
                                <GraduationCap className="text-blue-600" size={28} /> {t('classroom_my_courses')}
                            </h2>
                            <p className="text-sm font-bold text-slate-400">
                                {t('classroom_active_limit', { count: myCourses.length, max: MAX_ACTIVE_COURSES })}
                            </p>
                        </motion.div>

                        <div className={myCoursesGridClass}>
                            {myCourses.map((course) => {
                                const singleCourse = myCourses.length === 1;
                                return (
                                    <div
                                        key={course.id}
                                        className={singleCourse ? 'w-80' : 'w-full'}
                                    >
                                        <CourseCard
                                            course={course}
                                            variants={fadeInUp}
                                            titleAction={t('classroom_start')}
                                            masteredCount={course.mastered}
                                            actionButton={
                                                <button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                setCoursePendingPause(course);
                                            }}
                                                    disabled={removingCourseId === course.id}
                                                    className="shrink-0 inline-flex items-center gap-1.5 px-4 py-2 rounded-2xl text-xs font-black bg-rose-50 text-rose-600 hover:bg-rose-100 disabled:opacity-60 disabled:cursor-wait transition"
                                                >
                                                    {removingCourseId === course.id ? (
                                                        <Loader2 size={14} className="animate-spin" />
                                                    ) : (
                                                        <MinusCircle size={14} />
                                                    )}
                                                    {t('course_remove_learning')}
                                                </button>
                                            }
                                            onClick={() => navigate(`/course/${course.id}`)}
                                            isInteractive
                                        />
                                    </div>
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
                                    onChange={handleLearningFilterChange}
                                />
                                <FilterSelect
                                    label={t('classroom_filter_native')}
                                    value={nativeFilter}
                                    options={languageOptions.native}
                                    onChange={handleNativeFilterChange}
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
                                            titleAction={isEnrolled ? t('classroom_in_learning') : t('classroom_start')}
                                            masteredCount={null}
                                            actionButton={isEnrolled ? (
                                                <span className="shrink-0 px-5 py-2.5 rounded-2xl text-sm font-black bg-emerald-50 text-emerald-600">
                                                    {t('classroom_added')}
                                                </span>
                                            ) : null}
                                            onClick={() => navigate(`/course/${course.id}`)}
                                            isInteractive
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

            <AnimatePresence>
                {coursePendingPause && (
                    <motion.div
                        className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/40 px-4 backdrop-blur-sm"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <motion.div
                            role="dialog"
                            aria-modal="true"
                            aria-labelledby="pause-course-title"
                            initial={{ opacity: 0, y: 18, scale: 0.96 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: 10, scale: 0.97 }}
                            transition={{ type: 'spring', stiffness: 180, damping: 22 }}
                            className="w-full max-w-md rounded-[2rem] border border-white/80 bg-white p-7 shadow-2xl shadow-slate-900/20"
                        >
                            <div className="flex items-start justify-between gap-4">
                                <div>
                                    <p className="text-xs font-black uppercase tracking-[0.22em] text-rose-500">
                                        {t('course_remove_confirm_eyebrow')}
                                    </p>
                                    <h3 id="pause-course-title" className="mt-2 text-2xl font-black tracking-tight text-slate-900">
                                        {t('course_remove_confirm_title')}
                                    </h3>
                                </div>
                                <button
                                    type="button"
                                    onClick={() => setCoursePendingPause(null)}
                                    className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition hover:bg-slate-200 hover:text-slate-900"
                                    aria-label={t('common_cancel')}
                                >
                                    <X size={18} />
                                </button>
                            </div>

                            <p className="mt-4 text-sm font-semibold leading-6 text-slate-500">
                                {t('course_remove_confirm_desc', { course: coursePendingPause.name })}
                            </p>

                            <div className="mt-7 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
                                <button
                                    type="button"
                                    onClick={() => setCoursePendingPause(null)}
                                    className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-600 transition hover:bg-slate-50"
                                >
                                    {t('common_cancel')}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => handleConfirmPauseCourse('pause')}
                                    disabled={removingCourseId === coursePendingPause.id}
                                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-black text-white shadow-lg shadow-slate-200 transition hover:bg-slate-800 disabled:cursor-wait disabled:bg-slate-300"
                                >
                                    {removingCourseId === coursePendingPause.id && <Loader2 size={16} className="animate-spin" />}
                                    {t('course_pause_confirm_action')}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => handleConfirmPauseCourse('clear')}
                                    disabled={removingCourseId === coursePendingPause.id}
                                    className="inline-flex items-center justify-center gap-2 rounded-2xl bg-rose-600 px-5 py-3 text-sm font-black text-white shadow-lg shadow-rose-200 transition hover:bg-rose-700 disabled:cursor-wait disabled:bg-rose-300"
                                >
                                    {removingCourseId === coursePendingPause.id && <Loader2 size={16} className="animate-spin" />}
                                    {t('course_clear_confirm_action')}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}

function CourseCard({
    course,
    variants,
    titleAction,
    masteredCount,
    actionButton = null,
    onClick,
    isInteractive = false,
}) {
    const { t, i18n } = useTranslation();
    const visual = getCourseVisual(course);
    const LearningFlag = visual.LearningFlag;
    const NativeFlag = visual.NativeFlag;
    const learningLabel = formatLanguageLabel(visual.learning, i18n.language);
    const nativeLabel = formatLanguageLabel(visual.native, i18n.language);
    const lessonTotal = toNumber(course.lesson_total, 0);
    const completedLessonCount = Math.min(toNumber(course.completed_lesson_count, 0), lessonTotal);
    const lessonProgressPercent = lessonTotal > 0
        ? Math.round((completedLessonCount / lessonTotal) * 100)
        : 0;
    // showLessonProgress：仅在「我的课程」区（传入 masteredCount）且课程有课时数据时显示进度条
    const showLessonProgress = masteredCount !== null && lessonTotal > 0;
    const masteredTotal = toNumber(course.total_items, 0);

    return (
        <motion.div
            variants={variants}
            whileHover={{ y: -6, scale: 1.01 }}
            onClick={onClick}
            className={`rounded-3xl overflow-hidden shadow-lg ${visual.shadowClass} border border-white/60 ${isInteractive ? 'cursor-pointer group' : ''}`}
        >
            {/* Colored top section */}
            <div className={`relative ${visual.headerBg} px-6 py-6 h-44 flex flex-col items-center justify-center text-center`}>
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-14 h-10 rounded-lg overflow-hidden shadow-md ring-2 ring-black/10">
                        <NativeFlag className="w-full h-full" />
                    </div>
                    <span className={`${visual.arrowColor} font-black text-base`}>→</span>
                    <div className="w-14 h-10 rounded-lg overflow-hidden shadow-md ring-2 ring-black/10">
                        <LearningFlag className="w-full h-full" />
                    </div>
                </div>
                <h3 className={`text-xl font-black ${visual.textColor} leading-snug`}>
                    {cleanCourseDisplayName(course.name)}
                </h3>
                <p className={`mt-1 ${visual.subtitleColor} text-sm font-semibold`}>{nativeLabel} → {learningLabel}</p>
            </div>

            {/* White bottom section */}
            <div className="bg-white px-6 py-4">
                {showLessonProgress && (
                    <div className="mb-3">
                        <div className="mb-2 flex items-center justify-between gap-3">
                            <p className="truncate text-xs font-black text-slate-500">
                                {t('course_progress_completed_count', {
                                    completed: completedLessonCount,
                                    total: lessonTotal,
                                })}
                            </p>
                            <p className="shrink-0 text-xs font-black text-slate-900">{lessonProgressPercent}%</p>
                        </div>
                        <div className="h-1.5 overflow-hidden rounded-full bg-slate-100">
                            <div className={`h-full rounded-full ${visual.barBg}`} style={{ width: `${lessonProgressPercent}%` }} />
                        </div>
                        <p className="mt-2 text-xs font-bold text-slate-400">
                            {t('classroom_mastered')}: {masteredCount}{masteredTotal > 0 ? ` / ${masteredTotal}` : ''}
                        </p>
                    </div>
                )}
                {/* 全部课程区：显示课时数 + 词汇数 */}
                {masteredCount === null && (lessonTotal > 0 || masteredTotal > 0) && (
                    <div className="mb-3 flex items-center gap-3">
                        {lessonTotal > 0 && (
                            <span className="text-xs font-black text-slate-400">
                                {t('classroom_course_lessons', { count: lessonTotal })}
                            </span>
                        )}
                        {lessonTotal > 0 && masteredTotal > 0 && (
                            <span className="text-slate-200 font-black text-xs">·</span>
                        )}
                        {masteredTotal > 0 && (
                            <span className="text-xs font-black text-slate-400">
                                {t('classroom_course_items', { count: masteredTotal })}
                            </span>
                        )}
                    </div>
                )}
                <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-bold text-slate-600 flex items-center gap-1.5">
                        {titleAction}
                        <ChevronRight size={14} className={isInteractive ? 'group-hover:translate-x-1 transition-transform' : ''} />
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
    const containerRef = useRef(null);
    const selectedLabel = value === 'all' ? t('classroom_filter_all') : formatLanguageLabel(value, i18n.language);

    // 标准外部点击关闭：监听 document mousedown，判断点击是否在容器之外
    useEffect(() => {
        if (!isOpen) return;
        const handleOutsideClick = (e) => {
            if (containerRef.current && !containerRef.current.contains(e.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleOutsideClick);
        return () => document.removeEventListener('mousedown', handleOutsideClick);
    }, [isOpen]);

    return (
        <div ref={containerRef} className="relative min-w-[220px] rounded-[1.5rem] border border-slate-200/80 bg-white/90 p-2 shadow-md shadow-slate-200/50">
            <div className="mb-2 px-2">
                <span className="text-[11px] font-black uppercase tracking-[0.22em] text-slate-400 whitespace-nowrap">
                    {label}
                </span>
            </div>
            <div className="relative">
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
