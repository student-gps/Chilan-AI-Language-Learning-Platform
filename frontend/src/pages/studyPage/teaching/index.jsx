import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import apiClient from '../../../api/apiClient';
import {
    ArrowRight,
    Loader2,
    Pause,
    Play,
    VolumeX,
    Volume2
} from 'lucide-react';
import DialogueSection from './components/DialogueSection';
import useTeachingAudio, { buildLessonAudioUrl } from './hooks/useTeachingAudio';
import VocabularySection from './components/VocabularySection';

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

const normalizeLineRef = (value) => {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
};

const LESSON_AUDIO_RATES = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3];

const extractYouTubeId = (url) => {
    if (!url) return null;
    const m = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|v\/))([\w-]{11})/);
    return m ? m[1] : null;
};

function ExplanationVideoPlayer({ videoUrls, title, apiBase, t }) {
    const youtubeId = extractYouTubeId(videoUrls?.youtube_url);
    const bilibiliUrl = (videoUrls?.bilibili_url || '').trim();
    const youtubeUrl  = (videoUrls?.youtube_url  || '').trim();

    const cosRaw = (videoUrls?.cos_url || '').trim();
    const cosUrl = cosRaw
        ? (cosRaw.startsWith('http') ? cosRaw : `${apiBase}/media/video/${cosRaw}`)
        : '';

    const localPath = (videoUrls?.local_path || '').trim();
    // Derive a relative /media/video URL from the local absolute path as fallback
    const localFilename = localPath ? localPath.replace(/\\/g, '/').split('/').pop() : '';
    const localUrl = (!cosUrl && localFilename) ? `${apiBase}/media/video/${localFilename}` : '';

    const videoSrc = cosUrl || localUrl;
    const hasVideo = !!(youtubeId || videoSrc);

    return (
        <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mb-16">
            <div className="w-full overflow-hidden rounded-[2.5rem] bg-slate-900 shadow-2xl" style={{ aspectRatio: '16/9' }}>
                {youtubeId ? (
                    <iframe
                        src={`https://www.youtube.com/embed/${youtubeId}`}
                        className="h-full w-full"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowFullScreen
                        title={title}
                        style={{ border: 'none' }}
                    />
                ) : videoSrc ? (
                    <video
                        src={videoSrc}
                        controls
                        preload="metadata"
                        className="h-full w-full"
                        style={{ background: '#0f172a' }}
                    />
                ) : (
                    // Placeholder — video not yet available
                    <div className="group relative flex h-full w-full flex-col items-center justify-center">
                        <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                        <div className="z-10 text-center">
                            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full border border-white/20 bg-white/10 backdrop-blur-xl transition-transform group-hover:scale-110">
                                <div className="ml-1 h-0 w-0 border-b-[10px] border-l-[18px] border-t-[10px] border-b-transparent border-l-white border-t-transparent" />
                            </div>
                            <p className="text-[10px] font-black uppercase tracking-[0.4em] text-white/40">
                                {t('teaching_video_label')}
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {(youtubeUrl || bilibiliUrl) && (
                <div className="mt-3 flex justify-end gap-3">
                    {youtubeUrl && (
                        <a
                            href={youtubeUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 rounded-full bg-red-600 px-5 py-2 text-sm font-bold text-white transition-colors hover:bg-red-700"
                        >
                            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M23.5 6.2a3 3 0 0 0-2.1-2.1C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.4.6a3 3 0 0 0-2.1 2.1C0 8.1 0 12 0 12s0 3.9.5 5.8a3 3 0 0 0 2.1 2.1c1.9.6 9.4.6 9.4.6s7.5 0 9.4-.6a3 3 0 0 0 2.1-2.1C24 15.9 24 12 24 12s0-3.9-.5-5.8zM9.7 15.5V8.5l6.3 3.5-6.3 3.5z"/>
                            </svg>
                            YouTube
                        </a>
                    )}
                    {bilibiliUrl && (
                        <a
                            href={bilibiliUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center gap-2 rounded-full bg-[#00a1d6] px-5 py-2 text-sm font-bold text-white transition-colors hover:bg-[#0090c0]"
                        >
                            <svg className="h-4 w-4" viewBox="0 0 24 24" fill="currentColor">
                                <path d="M17.813 4.653h.854c1.51.054 2.769.578 3.773 1.574 1.004.995 1.524 2.249 1.56 3.76v7.36c-.036 1.51-.556 2.769-1.56 3.773s-2.262 1.524-3.773 1.56H5.333c-1.51-.036-2.769-.556-3.773-1.56S.036 18.858 0 17.347v-7.36c.036-1.511.556-2.765 1.56-3.76 1.004-.996 2.262-1.52 3.773-1.574h.774l-1.174-1.12a1.234 1.234 0 0 1-.373-.906c0-.356.124-.658.373-.907l.027-.027c.267-.249.573-.373.92-.373.347 0 .653.124.92.373L9.653 4.44c.071.071.134.142.187.213h4.267a.836.836 0 0 1 .16-.213l2.853-2.747c.267-.249.573-.373.92-.373.347 0 .662.151.929.4.267.249.391.551.391.907 0 .355-.124.657-.373.906zM5.333 7.24c-.746.018-1.373.276-1.88.773-.506.498-.769 1.13-.786 1.894v7.52c.017.764.28 1.395.786 1.893.507.498 1.134.756 1.88.773h13.334c.746-.017 1.373-.275 1.88-.773.506-.498.769-1.129.786-1.893v-7.52c-.017-.765-.28-1.396-.786-1.894-.507-.497-1.134-.755-1.88-.773zM8 11.107c.373 0 .684.124.933.373.25.249.374.56.374.933v2.667c0 .373-.125.684-.374.933-.249.25-.56.374-.933.374s-.684-.125-.933-.374c-.25-.249-.374-.56-.374-.933v-2.667c0-.373.125-.684.374-.933.249-.249.56-.373.933-.373zm8 0c.373 0 .684.124.933.373.25.249.374.56.374.933v2.667c0 .373-.125.684-.374.933-.249.25-.56.374-.933.374s-.684-.125-.933-.374c-.25-.249-.374-.56-.374-.933v-2.667c0-.373.125-.684.374-.933.249-.249.56-.373.933-.373z"/>
                            </svg>
                            Bilibili
                        </a>
                    )}
                </div>
            )}
        </motion.div>
    );
}

export default function TeachingSection({ data, courseId, userId, onStartPractice }) {
    const { t, i18n } = useTranslation();
    const [diagPinyin, setDiagPinyin] = useState(true);
    const [diagTrans, setDiagTrans] = useState(true);
    const [vocabPinyin, setVocabPinyin] = useState(true);
    const [vocabTrans, setVocabTrans] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';
    const lesson_metadata = data?.lesson_metadata || {};
    const course_content = data?.course_content || {};
    const aigc_visual_prompt = data?.aigc_visual_prompt || '';
    const lesson_audio_assets = data?.lesson_audio_assets || null;
    const explanation_video_urls = data?.explanation_video_urls || {};
    const { dialogues, vocabulary } = course_content || {};
    const contentType = lesson_metadata?.content_type || 'dialogue';
    const isReadingMode = ['diary', 'article', 'passage'].includes(contentType);
    const isMixedMode = contentType === 'mixed';
    const lessonHeading = isReadingMode
        ? (contentType === 'diary' ? `🗒️ ${t('teaching_diary_original')}` : `📖 ${t('teaching_reading')}`)
        : (isMixedMode ? `🎭 ${t('teaching_content')}` : `💬 ${t('teaching_dialogue')}`);
    const lineItems = dialogues?.flatMap((section) => section.lines || []) || [];
    const lessonFullAudioUrl = buildLessonAudioUrl(lesson_audio_assets, API_BASE);
    const {
        playingKey,
        lessonAudioDuration,
        lessonAudioCurrentTime,
        isLessonAudioPlaying,
        lessonAudioVolume,
        lessonAudioRate,
        showLessonVolumeControl,
        showFloatingLessonAudio,
        isFloatingLessonAudioOpen,
        lessonVolumeControlRef,
        lessonAudioSectionRef,
        activeLessonLineRef,
        setShowLessonVolumeControl,
        setIsFloatingLessonAudioOpen,
        playTtsFallback,
        playDialogueAudio,
        handleLessonAudioToggle,
        handleLessonAudioSeek,
        handleLessonAudioVolumeChange,
        handleLessonAudioRateChange,
    } = useTeachingAudio({
        lessonAudioAssets: lesson_audio_assets,
        lessonFullAudioUrl,
        apiBase: API_BASE,
    });

    if (!data) return null;

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

                <ExplanationVideoPlayer
                    videoUrls={explanation_video_urls}
                    title={lesson_metadata.title}
                    apiBase={API_BASE}
                    t={t}
                />

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

                <DialogueSection
                    fadeInUp={fadeInUp}
                    lessonHeading={lessonHeading}
                    contentType={contentType}
                    isReadingMode={isReadingMode}
                    lessonMetadata={lesson_metadata}
                    lineItems={lineItems}
                    diagPinyin={diagPinyin}
                    setDiagPinyin={setDiagPinyin}
                    diagTrans={diagTrans}
                    setDiagTrans={setDiagTrans}
                    playingKey={playingKey}
                    activeLessonLineRef={activeLessonLineRef}
                    playDialogueAudio={playDialogueAudio}
                    t={t}
                />

                <VocabularySection
                    fadeInUp={fadeInUp}
                    vocabulary={vocabulary}
                    vocabPinyin={vocabPinyin}
                    setVocabPinyin={setVocabPinyin}
                    vocabTrans={vocabTrans}
                    setVocabTrans={setVocabTrans}
                    playTtsFallback={playTtsFallback}
                    t={t}
                />

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
