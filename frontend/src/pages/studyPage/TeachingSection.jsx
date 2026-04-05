import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import apiClient from '../../api/apiClient';
import { claimGlobalAudio, releaseGlobalAudio, stopGlobalAudio } from '../../utils/audioPlayback';
import {
    ArrowRight,
    BookOpen,
    Eye,
    EyeOff,
    Languages,
    Loader2,
    Pause,
    Play,
    VolumeX,
    Volume2
} from 'lucide-react';

const fadeInUp = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 120, damping: 20 } }
};

const staggerContainer = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.08 } }
};

const formatLessonId = (id) => {
    const numId = parseInt(id, 10);
    return numId < 100 ? id : `${Math.floor(numId / 100)}.${numId % 100}`;
};

const InlineAnnotatedText = ({ words = [], showPinyin, pinyinClassName = '', textClassName = '' }) => {
    if (!showPinyin) {
        return (
            <div className={`leading-[1.95] ${textClassName}`}>
                {words.map((w, idx) => (
                    <span key={idx} className={w.highlight ? 'text-blue-600 font-black' : ''}>
                        {w.cn}
                    </span>
                ))}
            </div>
        );
    }

    return (
        <div className="flex flex-wrap items-end gap-x-2 gap-y-4 leading-relaxed">
            {words.map((w, idx) => (
                <ruby key={idx} className="flex flex-col items-center">
                    <rt className={pinyinClassName}>{w.py}</rt>
                    <span className={`${textClassName} ${w.highlight ? 'text-blue-600 font-black' : ''}`}>
                        {w.cn}
                    </span>
                </ruby>
            ))}
        </div>
    );
};

const normalizeLineRef = (value) => {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
};

const buildLessonAudioUrl = (lessonAudioAssets, apiBase) => {
    const relativeUrl = lessonAudioAssets?.full_audio?.audio_url || '';
    if (!relativeUrl) return '';
    if (relativeUrl.startsWith('http://') || relativeUrl.startsWith('https://')) return relativeUrl;
    return `${apiBase}${relativeUrl}`;
};

const LESSON_AUDIO_RATES = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3];

export default function TeachingSection({ data, courseId, userId, onStartPractice }) {
    const { t, i18n } = useTranslation();
    const [diagPinyin, setDiagPinyin] = useState(true);
    const [diagTrans, setDiagTrans] = useState(true);
    const [vocabPinyin, setVocabPinyin] = useState(true);
    const [vocabTrans, setVocabTrans] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const [playingKey, setPlayingKey] = useState(null);
    const [lessonAudioDuration, setLessonAudioDuration] = useState(0);
    const [lessonAudioCurrentTime, setLessonAudioCurrentTime] = useState(0);
    const [isLessonAudioPlaying, setIsLessonAudioPlaying] = useState(false);
    const [lessonAudioVolume, setLessonAudioVolume] = useState(1);
    const [lessonAudioRate, setLessonAudioRate] = useState(1);
    const [showLessonVolumeControl, setShowLessonVolumeControl] = useState(false);
    const [showFloatingLessonAudio, setShowFloatingLessonAudio] = useState(false);
    const [isFloatingLessonAudioOpen, setIsFloatingLessonAudioOpen] = useState(true);

    const audioRef = useRef(null);
    const lessonAudioRef = useRef(null);
    const lessonVolumeControlRef = useRef(null);
    const lessonAudioSectionRef = useRef(null);
    const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';
    const lesson_metadata = data?.lesson_metadata || {};
    const course_content = data?.course_content || {};
    const aigc_visual_prompt = data?.aigc_visual_prompt || '';
    const lesson_audio_assets = data?.lesson_audio_assets || null;
    const { dialogues, vocabulary } = course_content || {};
    const contentType = lesson_metadata?.content_type || 'dialogue';
    const isReadingMode = ['diary', 'article', 'passage'].includes(contentType);
    const isMixedMode = contentType === 'mixed';
    const lessonHeading = isReadingMode
        ? (contentType === 'diary' ? `🗒️ ${t('teaching_diary_original')}` : `📖 ${t('teaching_reading')}`)
        : (isMixedMode ? `🎭 ${t('teaching_content')}` : `💬 ${t('teaching_dialogue')}`);
    const lineItems = dialogues?.flatMap((section) => section.lines || []) || [];
    const lessonFullAudioUrl = buildLessonAudioUrl(lesson_audio_assets, API_BASE);

    const audioAssetMap = useMemo(() => {
        const map = new Map();
        (lesson_audio_assets?.items || []).forEach((item) => {
            const lineRef = normalizeLineRef(item?.line_ref);
            if (lineRef) map.set(lineRef, item);
        });
        return map;
    }, [lesson_audio_assets]);

    const activeLessonLineRef = useMemo(() => {
        if (!isLessonAudioPlaying) return null;
        const currentTime = Number(lessonAudioCurrentTime || 0);
        const matchedItem = (lesson_audio_assets?.items || []).find((item) => {
            const lineRef = normalizeLineRef(item?.line_ref);
            const start = Number(item?.start_time_seconds);
            const end = Number(item?.end_time_seconds);
            return lineRef && Number.isFinite(start) && Number.isFinite(end) && currentTime >= start && currentTime < end;
        });
        return normalizeLineRef(matchedItem?.line_ref);
    }, [isLessonAudioPlaying, lessonAudioCurrentTime, lesson_audio_assets]);

    useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
            }
            if (lessonAudioRef.current) {
                lessonAudioRef.current.pause();
                lessonAudioRef.current = null;
            }
            stopGlobalAudio();
        };
    }, []);

    useEffect(() => {
        const handleOutsideClick = (event) => {
            if (!lessonVolumeControlRef.current?.contains(event.target)) {
                setShowLessonVolumeControl(false);
            }
        };

        if (showLessonVolumeControl) {
            document.addEventListener('mousedown', handleOutsideClick);
        }

        return () => {
            document.removeEventListener('mousedown', handleOutsideClick);
        };
    }, [showLessonVolumeControl]);

    useEffect(() => {
        setLessonAudioCurrentTime(0);
        setLessonAudioDuration(0);
        setIsLessonAudioPlaying(false);
        setShowFloatingLessonAudio(false);
        setIsFloatingLessonAudioOpen(true);
        if (lessonAudioRef.current) {
            lessonAudioRef.current.pause();
            lessonAudioRef.current = null;
        }
    }, [lessonFullAudioUrl]);

    useEffect(() => {
        if (lessonAudioRef.current) {
            lessonAudioRef.current.volume = lessonAudioVolume;
        }
    }, [lessonAudioVolume]);

    useEffect(() => {
        if (lessonAudioRef.current) {
            lessonAudioRef.current.playbackRate = lessonAudioRate;
        }
    }, [lessonAudioRate]);

    useEffect(() => {
        if (!lessonFullAudioUrl) {
            setShowFloatingLessonAudio(false);
            return;
        }

        const updateFloatingPlayerVisibility = () => {
            const section = lessonAudioSectionRef.current;
            if (!section) {
                setShowFloatingLessonAudio(false);
                return;
            }

            const rect = section.getBoundingClientRect();
            const shouldFloat = rect.bottom < 96;
            setShowFloatingLessonAudio(shouldFloat);
        };

        updateFloatingPlayerVisibility();
        window.addEventListener('scroll', updateFloatingPlayerVisibility, { passive: true });
        window.addEventListener('resize', updateFloatingPlayerVisibility);

        return () => {
            window.removeEventListener('scroll', updateFloatingPlayerVisibility);
            window.removeEventListener('resize', updateFloatingPlayerVisibility);
        };
    }, [lessonFullAudioUrl]);

    if (!data) return null;

    const buildAbsoluteAudioUrl = (url) => {
        if (!url) return '';
        if (url.startsWith('http://') || url.startsWith('https://')) return url;
        return `${API_BASE}${url}`;
    };

    const stopCurrentAudio = () => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
            releaseGlobalAudio(audioRef.current);
            audioRef.current = null;
        }
        setPlayingKey(null);
    };

    const stopLessonAudio = () => {
        if (lessonAudioRef.current) {
            lessonAudioRef.current.pause();
            lessonAudioRef.current.currentTime = 0;
            releaseGlobalAudio(lessonAudioRef.current);
        }
        setIsLessonAudioPlaying(false);
        setLessonAudioCurrentTime(0);
    };

    const playFromUrl = async (url, key) => {
        if (!url) return;

        if (playingKey === key) {
            stopCurrentAudio();
            return;
        }

        stopCurrentAudio();
        stopLessonAudio();

        const audio = new Audio(url);
        claimGlobalAudio(audio);
        audioRef.current = audio;
        setPlayingKey(key);

        audio.onpause = () => {
            if (audioRef.current === audio) {
                audioRef.current = null;
            }
            releaseGlobalAudio(audio);
            setPlayingKey(null);
        };
        audio.onended = () => {
            if (audioRef.current === audio) {
                audioRef.current = null;
            }
            releaseGlobalAudio(audio);
            setPlayingKey(null);
        };

        audio.onerror = () => {
            if (audioRef.current === audio) {
                audioRef.current = null;
            }
            releaseGlobalAudio(audio);
            setPlayingKey(null);
        };

        try {
            await audio.play();
        } catch (error) {
            console.error('播放音频失败:', error);
            if (audioRef.current === audio) {
                audioRef.current = null;
            }
            releaseGlobalAudio(audio);
            setPlayingKey(null);
        }
    };

    const playTtsFallback = (text, key) => {
        if (!text) return;
        const url = `${API_BASE}/study/tts?text=${encodeURIComponent(text)}`;
        playFromUrl(url, key);
    };

    const playDialogueAudio = ({ lineRef, text }) => {
        const item = audioAssetMap.get(normalizeLineRef(lineRef));
        const readyUrl = buildAbsoluteAudioUrl(item?.audio_url);
        const playbackKey = `line-${lineRef}`;

        if (readyUrl) {
            playFromUrl(readyUrl, playbackKey);
            return;
        }

        playTtsFallback(text, playbackKey);
    };

    const handleLessonAudioToggle = async () => {
        if (!lessonFullAudioUrl) return;

        if (!lessonAudioRef.current) {
            const audio = new Audio(lessonFullAudioUrl);
            audio.volume = lessonAudioVolume;
            audio.playbackRate = lessonAudioRate;
            if ('preservesPitch' in audio) audio.preservesPitch = true;
            if ('mozPreservesPitch' in audio) audio.mozPreservesPitch = true;
            if ('webkitPreservesPitch' in audio) audio.webkitPreservesPitch = true;
            lessonAudioRef.current = audio;

            audio.onloadedmetadata = () => {
                setLessonAudioDuration(Number.isFinite(audio.duration) ? audio.duration : 0);
            };
            audio.ontimeupdate = () => {
                setLessonAudioCurrentTime(audio.currentTime || 0);
            };
            audio.onpause = () => {
                setIsLessonAudioPlaying(false);
                releaseGlobalAudio(audio);
            };
            audio.onended = () => {
                setIsLessonAudioPlaying(false);
                setLessonAudioCurrentTime(0);
                releaseGlobalAudio(audio);
                if (lessonAudioRef.current) {
                    lessonAudioRef.current.currentTime = 0;
                }
            };
            audio.onerror = () => {
                setIsLessonAudioPlaying(false);
                releaseGlobalAudio(audio);
            };
        }

        const audio = lessonAudioRef.current;
        if (!audio) return;

        if (isLessonAudioPlaying) {
            audio.pause();
            setIsLessonAudioPlaying(false);
            return;
        }

        stopCurrentAudio();
        claimGlobalAudio(audio, { resetPrevious: true });

        try {
            await audio.play();
            setIsLessonAudioPlaying(true);
        } catch (error) {
            console.error('播放整课音频失败:', error);
            setIsLessonAudioPlaying(false);
            releaseGlobalAudio(audio);
        }
    };

    const handleLessonAudioSeek = (event) => {
        const nextTime = Number(event.target.value || 0);
        setLessonAudioCurrentTime(nextTime);
        if (lessonAudioRef.current) {
            lessonAudioRef.current.currentTime = nextTime;
        }
    };

    const handleLessonAudioVolumeChange = (event) => {
        const nextVolume = Number(event.target.value || 0);
        setLessonAudioVolume(nextVolume);
    };

    const handleLessonAudioRateChange = (event) => {
        const nextRate = Number(event.target.value || 1);
        setLessonAudioRate(nextRate);
    };

    const handleStartPracticeClick = async () => {
        if (isSaving) return;
        setIsSaving(true);
        try {
            await apiClient.post('/study/content_viewed', {
                user_id: userId,
                course_id: courseId,
                lesson_id: lesson_metadata.lesson_id
            });
        } catch (error) {
            console.error('记录阅读进度失败:', error);
        } finally {
            setIsSaving(false);
            onStartPractice();
        }
    };

    const ControlCapsule = ({ pinyin, setPinyin, trans, setTrans }) => (
        <div className="flex items-center gap-2 rounded-2xl border border-slate-200/50 bg-slate-100 p-1 shadow-inner">
            <button
                onClick={() => setPinyin(!pinyin)}
                className={`flex items-center gap-2 rounded-xl px-4 py-1.5 text-xs font-black transition-all duration-300 ${
                    pinyin ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400'
                }`}
            >
                {pinyin ? <Eye size={14} /> : <EyeOff size={14} />}
                {pinyin ? t('teaching_pinyin_on') : t('teaching_pinyin_off')}
            </button>
            <button
                onClick={() => setTrans(!trans)}
                className={`flex items-center gap-2 rounded-xl px-4 py-1.5 text-xs font-black transition-all duration-300 ${
                    trans ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-400'
                }`}
            >
                {trans ? <Languages size={14} /> : <BookOpen size={14} />}
                {trans ? t('teaching_translation_on') : t('teaching_translation_off')}
            </button>
        </div>
    );

    const renderAudioButton = ({ onClick, active, accent = 'slate', size = 20 }) => {
        const baseClass = active
            ? 'bg-blue-600 text-white shadow-lg'
            : accent === 'blue'
                ? 'text-blue-400 hover:text-blue-600'
                : 'text-slate-400 hover:text-blue-500';

        return (
            <button
                onClick={onClick}
                className={`rounded-2xl p-2 transition-all ${baseClass}`}
                title="播放音频"
            >
                <Volume2 size={size} />
            </button>
        );
    };

    const formatAudioTime = (value) => {
        const totalSeconds = Math.max(0, Math.floor(value || 0));
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes}:${String(seconds).padStart(2, '0')}`;
    };

    return (
        <AnimatePresence mode="wait">
            <motion.div
                key={`teaching-${i18n.language}`}
                variants={staggerContainer}
                initial="hidden"
                animate="show"
                exit={{ opacity: 0, y: -10, transition: { duration: 0.18 } }}
            className="mx-auto max-w-5xl px-5 pt-24 md:px-6"
            >
                <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mb-4 flex items-center gap-3">
                    <span className="rounded-full bg-slate-900 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-white">
                        {t('teaching_new_unit')}
                    </span>
                    <span className="font-mono text-sm font-bold text-slate-400">
                        LEVEL {formatLessonId(lesson_metadata.lesson_id)}
                    </span>
                </motion.div>

                <h1 className="mb-12 text-5xl font-black tracking-tight text-slate-900">
                    {lesson_metadata.title}
                </h1>

                <motion.div
                    variants={fadeInUp}
                    initial="hidden"
                    animate="show"
                    className="group relative mb-16 flex aspect-video w-full flex-col items-center justify-center overflow-hidden rounded-[2.5rem] bg-slate-900 shadow-2xl"
                >
                    <div className="absolute inset-0 z-10 bg-gradient-to-t from-black/40 to-transparent" />
                    <div className="z-20 text-center">
                        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-white/20 bg-white/10 backdrop-blur-xl transition-transform group-hover:scale-110">
                            <div className="ml-1 h-0 w-0 border-b-[10px] border-l-[18px] border-t-[10px] border-b-transparent border-l-white border-t-transparent" />
                        </div>
                        <p className="text-[10px] font-black uppercase tracking-[0.4em] text-white/40">
                            {t('teaching_video_label')}
                        </p>
                    </div>
                    <p className="absolute bottom-6 left-10 right-10 text-sm font-light italic text-white/60 opacity-0 transition-all duration-700 group-hover:opacity-100">
                        "{aigc_visual_prompt}"
                    </p>
                </motion.div>

                {lessonFullAudioUrl && (
                    <motion.section ref={lessonAudioSectionRef} variants={fadeInUp} initial="hidden" animate="show" className="mb-10">
                        <div className="rounded-[2.5rem] border border-slate-200 bg-white px-6 py-6 shadow-sm">
                            <h2 className="text-2xl font-black text-slate-900">
                                本课完整对话音频
                            </h2>

                            <div className="mt-5 rounded-full bg-slate-100/90 px-4 py-3">
                                <div className="flex flex-wrap items-center gap-4 md:flex-nowrap">
                                    <button
                                        onClick={handleLessonAudioToggle}
                                        className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-white text-slate-900 shadow-sm transition-all hover:bg-slate-50"
                                        aria-label={isLessonAudioPlaying ? '暂停播放整课音频' : '播放整课音频'}
                                    >
                                        {isLessonAudioPlaying ? <Pause size={22} /> : <Play size={22} className="ml-0.5" />}
                                    </button>

                                    <div className="min-w-[96px] shrink-0 text-lg font-bold tabular-nums text-slate-800">
                                        {formatAudioTime(lessonAudioCurrentTime)} / {formatAudioTime(lessonAudioDuration)}
                                    </div>

                                    <input
                                        type="range"
                                        min={0}
                                        max={lessonAudioDuration || 0}
                                        step={0.1}
                                        value={Math.min(lessonAudioCurrentTime, lessonAudioDuration || 0)}
                                        onChange={handleLessonAudioSeek}
                                        className="h-2 min-w-[140px] flex-1 cursor-pointer appearance-none rounded-full bg-slate-300 accent-slate-900"
                                    />

                                    <div ref={lessonVolumeControlRef} className="relative flex shrink-0 items-center">
                                        <button
                                            type="button"
                                            onClick={() => setShowLessonVolumeControl((prev) => !prev)}
                                            className="flex h-11 w-11 items-center justify-center rounded-full text-slate-800 transition-colors hover:bg-white"
                                            aria-label="调节音量"
                                        >
                                            {lessonAudioVolume <= 0.01 ? <VolumeX size={22} /> : <Volume2 size={22} />}
                                        </button>

                                        <div
                                            className={`absolute bottom-[calc(100%+0.75rem)] left-1/2 z-20 flex -translate-x-1/2 items-center justify-center rounded-[1.5rem] border border-slate-200 bg-white px-3 py-4 shadow-xl transition-all ${
                                                showLessonVolumeControl
                                                    ? 'pointer-events-auto opacity-100'
                                                    : 'pointer-events-none opacity-0'
                                            }`}
                                        >
                                            <input
                                                type="range"
                                                min={0}
                                                max={1}
                                                step={0.01}
                                                value={lessonAudioVolume}
                                                onChange={handleLessonAudioVolumeChange}
                                                className="h-28 w-2 cursor-pointer appearance-none rounded-full bg-slate-200 accent-slate-900 [writing-mode:bt-lr]"
                                                style={{ writingMode: 'vertical-lr', direction: 'rtl' }}
                                            />
                                        </div>
                                    </div>

                                    <div className="shrink-0">
                                        <select
                                            value={lessonAudioRate}
                                            onChange={handleLessonAudioRateChange}
                                            className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-bold text-slate-700 outline-none transition-colors hover:border-slate-300"
                                            aria-label="设置播放倍速"
                                        >
                                            {LESSON_AUDIO_RATES.map((rate) => (
                                                <option key={rate} value={rate}>
                                                    {rate}x
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            </div>

                        </div>
                    </motion.section>
                )}

                {lessonFullAudioUrl && showFloatingLessonAudio && (
                    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">
                        <AnimatePresence>
                            {isFloatingLessonAudioOpen && (
                                <motion.div
                                    initial={{ opacity: 0, y: 12, scale: 0.96 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, y: 10, scale: 0.96 }}
                                    className="w-[min(340px,calc(100vw-2rem))] rounded-[1.75rem] border border-slate-200 bg-white/95 p-4 shadow-2xl backdrop-blur"
                                >
                                    <div className="flex items-center gap-3">
                                        <button
                                            onClick={handleLessonAudioToggle}
                                            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-slate-900 text-white shadow-sm transition-colors hover:bg-blue-600"
                                            aria-label={isLessonAudioPlaying ? '暂停播放整课音频' : '播放整课音频'}
                                        >
                                            {isLessonAudioPlaying ? <Pause size={20} /> : <Play size={20} className="ml-0.5" />}
                                        </button>

                                        <div className="min-w-0 flex-1">
                                            <div className="flex items-center justify-between gap-3">
                                                <p className="truncate text-sm font-black tracking-[0.16em] text-slate-700">
                                                    课文音频
                                                </p>
                                                <select
                                                    value={lessonAudioRate}
                                                    onChange={handleLessonAudioRateChange}
                                                    className="shrink-0 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-bold text-slate-600 outline-none transition-colors hover:border-slate-300"
                                                    aria-label="设置悬浮课文音频倍速"
                                                >
                                                    {LESSON_AUDIO_RATES.map((rate) => (
                                                        <option key={rate} value={rate}>
                                                            {rate}x
                                                        </option>
                                                    ))}
                                                </select>
                                            </div>

                                            <input
                                                type="range"
                                                min={0}
                                                max={lessonAudioDuration || 0}
                                                step={0.1}
                                                value={Math.min(lessonAudioCurrentTime, lessonAudioDuration || 0)}
                                                onChange={handleLessonAudioSeek}
                                                className="mt-2 h-1.5 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-slate-900"
                                            />

                                            <div className="mt-2 flex items-center justify-between text-xs font-semibold text-slate-500">
                                                <span>{formatAudioTime(lessonAudioCurrentTime)} / {formatAudioTime(lessonAudioDuration)}</span>
                                                <span>倍速 {lessonAudioRate}x</span>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        <button
                            onClick={() => setIsFloatingLessonAudioOpen((prev) => !prev)}
                            className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-900 text-white shadow-2xl transition-all hover:-translate-y-0.5 hover:bg-blue-600"
                            aria-label={isFloatingLessonAudioOpen ? '收起悬浮课文音频条' : '展开悬浮课文音频条'}
                        >
                            <Volume2 size={22} />
                        </button>
                    </div>
                )}

                <motion.section variants={fadeInUp} initial="hidden" animate="show" className="mb-24">
                    <div className="mb-8 flex items-end justify-between">
                        <div>
                            <h2 className="text-2xl font-black text-slate-800">{lessonHeading}</h2>
                            <p className="mt-1 text-xs font-black uppercase tracking-[0.24em] text-slate-400">
                                {contentType}
                            </p>
                        </div>
                        <ControlCapsule
                            pinyin={diagPinyin}
                            setPinyin={setDiagPinyin}
                            trans={diagTrans}
                            setTrans={setDiagTrans}
                        />
                    </div>

                    <div className={`rounded-[3rem] border border-slate-100 bg-white shadow-sm ${
                        isReadingMode ? 'p-8 md:p-12' : 'p-10 md:p-14'
                    }`}>
                        {isReadingMode ? (
                            <div className="mx-auto max-w-3xl rounded-[2.5rem] border border-stone-200/80 bg-gradient-to-b from-stone-50 to-white px-8 py-10 shadow-[0_24px_60px_rgba(15,23,42,0.06)] md:px-14 md:py-14">
                                <div className="mb-10 border-b border-stone-200/80 pb-6">
                                    <div className="flex items-center justify-between gap-4">
                                        <div>
                                            <p className="text-[10px] font-black uppercase tracking-[0.36em] text-stone-400">
                                                {contentType === 'diary' ? t('teaching_diary_original') : t('teaching_reading')}
                                            </p>
                                            <h3 className="mt-3 text-3xl font-black tracking-tight text-stone-800 md:text-4xl">
                                                {lesson_metadata.title}
                                            </h3>
                                        </div>
                                        <div className="hidden items-center gap-2 rounded-full border border-stone-200 bg-white/80 px-4 py-2 text-[10px] font-black uppercase tracking-[0.28em] text-stone-400 md:flex">
                                            {contentType}
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-8">
                                    {lineItems.map((line, idx) => {
                                        const lineRef = idx + 1;
                                        const cnText = (line.words || []).map((w) => w.cn).join('');
                                        const isShortMetaLine = idx === 0 && cnText.length <= 12;
                                        const isActive = playingKey === `line-${lineRef}`;

                                        return (
                                            <article key={idx} className={`group ${isShortMetaLine ? 'text-center' : ''}`}>
                                                <div className={`flex gap-3 ${isShortMetaLine ? 'items-end justify-center' : 'items-end'}`}>
                                                    <div className="min-w-0 flex-1">
                                                        <InlineAnnotatedText
                                                            words={line.words || []}
                                                            showPinyin={diagPinyin}
                                                            pinyinClassName={`mb-1 text-sm font-mono text-stone-400 md:text-base ${
                                                                isShortMetaLine ? 'text-center' : ''
                                                            }`}
                                                            textClassName={`text-stone-800 ${
                                                                isShortMetaLine
                                                                    ? 'text-4xl font-black tracking-[0.12em] md:text-5xl'
                                                                    : 'text-3xl font-medium md:text-[2.15rem]'
                                                            }`}
                                                        />
                                                    </div>
                                                    {renderAudioButton({
                                                        onClick: () => playDialogueAudio({ lineRef, text: cnText }),
                                                        active: isActive,
                                                        accent: 'slate'
                                                    })}
                                                </div>

                                                {diagTrans && line.english && (
                                                    <p className={`mt-3 text-lg leading-relaxed text-stone-500 md:text-xl ${
                                                        isShortMetaLine ? 'text-center' : ''
                                                    }`}>
                                                        {line.english}
                                                    </p>
                                                )}
                                            </article>
                                        );
                                    })}
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-7">
                                {lineItems.map((line, idx) => {
                                    const isLeft = idx % 2 === 0;
                                    const lineRef = idx + 1;
                                    const cnText = (line.words || []).map((w) => w.cn).join('');
                                    const isActive = playingKey === `line-${lineRef}`;
                                    const isLessonActive = activeLessonLineRef === lineRef;

                                    return (
                                        <div key={idx} className={`flex ${isLeft ? 'justify-start' : 'justify-end'}`}>
                                            <div className={`flex max-w-full items-start gap-3 ${isLeft ? 'flex-row' : 'flex-row-reverse'}`}>
                                                <span className={`pt-4 text-xl font-black uppercase tracking-[0.22em] transition-colors md:text-2xl ${
                                                    isLessonActive ? (isLeft ? 'text-slate-500' : 'text-blue-500') : 'text-slate-300'
                                                }`}>
                                                    {line.role}
                                                </span>

                                                <div className={`group relative max-w-[88%] rounded-[2.2rem] px-6 py-4 transition-all hover:shadow-lg ${
                                                    isLessonActive
                                                        ? isLeft
                                                            ? 'rounded-tl-none border border-slate-300 bg-slate-100 text-slate-900 shadow-lg shadow-slate-200/60'
                                                            : 'rounded-tr-none border border-blue-300 bg-blue-100 text-slate-900 shadow-lg shadow-blue-200/60'
                                                        : isLeft
                                                            ? 'rounded-tl-none border border-slate-100 bg-slate-50 text-slate-800'
                                                            : 'rounded-tr-none border border-blue-100 bg-blue-50 text-slate-800'
                                                }`}>
                                                    <div className="flex items-end gap-3">
                                                        <div className="min-w-0 flex-1">
                                                            <InlineAnnotatedText
                                                                words={line.words || []}
                                                                showPinyin={diagPinyin}
                                                                pinyinClassName={`mb-1 text-xl font-mono ${
                                                                    isLessonActive
                                                                        ? isLeft
                                                                            ? 'text-slate-500'
                                                                            : 'text-blue-500'
                                                                        : isLeft
                                                                            ? 'text-slate-400'
                                                                            : 'text-blue-400'
                                                                }`}
                                                                textClassName="text-3xl font-medium"
                                                            />
                                                        </div>

                                                        {renderAudioButton({
                                                            onClick: () => playDialogueAudio({ lineRef, text: cnText }),
                                                            active: isActive,
                                                            accent: isLeft ? 'slate' : 'blue'
                                                        })}
                                                    </div>

                                                    {diagTrans && line.english && (
                                                        <p className={`mt-4 border-t pt-3 text-xl ${
                                                            isLessonActive
                                                                ? isLeft
                                                                    ? 'border-slate-300/70 text-slate-600'
                                                                    : 'border-blue-300/70 text-blue-800/80'
                                                                : isLeft
                                                                    ? 'border-slate-200/60 text-slate-500'
                                                                    : 'border-blue-200/60 text-blue-700/70'
                                                        }`}>
                                                            {line.english}
                                                        </p>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </motion.section>

                <motion.section variants={fadeInUp} initial="hidden" animate="show" className="mb-20">
                    <div className="mb-8 flex items-end justify-between">
                        <h2 className="text-2xl font-black text-slate-800">🔤 {t('teaching_vocab_title')}</h2>
                        <ControlCapsule
                            pinyin={vocabPinyin}
                            setPinyin={setVocabPinyin}
                            trans={vocabTrans}
                            setTrans={setVocabTrans}
                        />
                    </div>

                    <div className="grid grid-cols-1 gap-6">
                        {vocabulary?.map((vocab, idx) => (
                            <div
                                key={idx}
                                className="group rounded-[2.5rem] border border-slate-100 bg-white p-8 shadow-sm transition-all duration-500 hover:shadow-xl"
                            >
                                <div className="flex flex-col justify-between gap-6 md:flex-row md:items-start">
                                    <div className="flex items-start gap-5">
                                        <span className="text-4xl font-black text-slate-900">{vocab.word}</span>
                                        <button
                                            onClick={() => playTtsFallback(vocab.word, `vocab-${idx}`)}
                                            className="rounded-2xl bg-slate-50 p-2.5 text-slate-400 shadow-sm transition-all hover:bg-blue-600 hover:text-white"
                                        >
                                            <Volume2 size={20} />
                                        </button>
                                        <div className="flex flex-col gap-1">
                                            <span className={`font-mono font-bold text-orange-600 transition-all duration-500 ${
                                                vocabPinyin ? 'opacity-100' : 'opacity-0'
                                            }`}>
                                                {vocab.pinyin}
                                            </span>
                                            <span className="self-start rounded-lg bg-slate-100 px-2 py-0.5 text-[10px] font-black uppercase tracking-widest text-slate-400">
                                                {vocab.part_of_speech}
                                            </span>
                                        </div>
                                    </div>
                                    <div className={`transition-all duration-500 ${
                                        vocabTrans ? 'translate-x-0 opacity-100' : 'translate-x-4 opacity-0'
                                    }`}>
                                        <span className="text-xl font-black text-slate-800">{vocab.definition}</span>
                                    </div>
                                </div>

                                {vocab.example_sentence && (
                                    <div className="mt-8 flex items-start gap-4 border-t border-slate-50 pt-6">
                                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-slate-50">
                                            <span className="text-[10px] font-black text-slate-300">{t('teaching_example')}</span>
                                        </div>
                                        <div className="flex-1">
                                            <p className={`mb-1 text-sm font-mono text-slate-400 transition-all duration-500 ${
                                                vocabPinyin ? 'opacity-100' : 'opacity-0'
                                            }`}>
                                                {vocab.example_sentence.py}
                                            </p>
                                            <div className="mb-2 flex items-center gap-3">
                                                <p className="text-xl font-bold tracking-wide text-slate-800">
                                                    {vocab.example_sentence.cn}
                                                </p>
                                                <button
                                                    onClick={() => playTtsFallback(vocab.example_sentence.cn, `example-${idx}`)}
                                                    className="p-1.5 text-slate-300 transition-colors hover:text-blue-600"
                                                >
                                                    <Volume2 size={18} />
                                                </button>
                                            </div>
                                            <p className={`text-sm font-medium italic text-slate-400 transition-all duration-500 ${
                                                vocabTrans ? 'opacity-100' : 'opacity-0'
                                            }`}>
                                                {vocab.example_sentence.en}
                                            </p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </motion.section>

                <motion.div variants={fadeInUp} initial="hidden" animate="show" className="flex justify-center pb-24 pt-8">
                    <button
                        onClick={handleStartPracticeClick}
                        disabled={isSaving}
                        className="flex items-center gap-4 rounded-[2rem] bg-slate-900 px-14 py-5 text-lg font-black text-white shadow-xl transition-all hover:-translate-y-1 hover:bg-blue-600 disabled:bg-slate-400 disabled:hover:translate-y-0"
                    >
                        {isSaving ? (
                            <>
                                {t('teaching_generating_quiz')}
                                <Loader2 className="animate-spin" size={22} />
                            </>
                        ) : (
                            <>
                                {t('teaching_start_quiz')}
                                <ArrowRight size={22} />
                            </>
                        )}
                    </button>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
