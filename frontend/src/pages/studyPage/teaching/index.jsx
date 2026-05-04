import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../../api/apiClient';
import {
    ArrowLeft,
    ArrowRight,
    Loader2,
    Pause,
    Play,
    VolumeX,
    Volume2
} from 'lucide-react';
import DialogueSection from './components/DialogueSection';
import LessonSlideDeckPlayer from './components/LessonSlideDeckPlayer';
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


const LESSON_AUDIO_RATES = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3];


export default function TeachingSection({ data, courseId, userId, onStartPractice, isDirectLesson }) {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const [diagPinyin, setDiagPinyin] = useState(true);
    const [diagTrans, setDiagTrans] = useState(true);
    const [vocabPinyin, setVocabPinyin] = useState(true);
    const [vocabTrans, setVocabTrans] = useState(true);
    const [isSaving, setIsSaving] = useState(false);
    const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';
    const lesson_metadata = data?.lesson_metadata || {};
    const course_content = data?.course_content || {};
    const lesson_audio_assets = data?.lesson_audio_assets || null;
    const teaching_slide_deck =
        data?.teaching_slide_deck ||
        data?.video_render_plan?.teaching_slide_deck ||
        data?.video_render_plan?.explanation?.teaching_slide_deck ||
        null;
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
            className="mx-auto max-w-5xl px-5 pt-16 md:px-6"
            >
                <motion.div variants={fadeInUp} initial="hidden" animate="show" className="mb-4 flex items-center gap-3">
                    <span className="rounded-full bg-slate-900 px-3 py-1 text-[10px] font-black uppercase tracking-widest text-white">
                        {t('teaching_new_unit')}
                    </span>
                    <span className="font-mono text-sm font-bold text-slate-400">
                        LEVEL {formatLessonId(lesson_metadata.lesson_id)}
                    </span>
                </motion.div>

                <h1 className="mb-2 text-5xl font-black tracking-tight text-slate-900">
                    {lesson_metadata.title}
                </h1>
                {lesson_metadata.title_localized && (
                    <p className="mb-4 text-xl font-medium text-slate-400">
                        {lesson_metadata.title_localized}
                    </p>
                )}

                <motion.div variants={fadeInUp} initial="hidden" animate="show">
                    <LessonSlideDeckPlayer deck={teaching_slide_deck} apiBase={API_BASE} />
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

                {!isDirectLesson && (
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
                )}

                {isDirectLesson && (
                    <button
                        onClick={() => navigate(`/course/${courseId}`)}
                        className="fixed top-24 left-6 z-50 flex items-center gap-2 px-4 py-2.5 bg-white text-slate-600 font-semibold rounded-2xl shadow-md border border-slate-100 hover:bg-slate-50 hover:text-slate-900 transition-all"
                    >
                        <ArrowLeft size={16} /> {t('teaching_back_to_course')}
                    </button>
                )}
            </motion.div>
        </AnimatePresence>
    );
}
