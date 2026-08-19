import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Loader2, RefreshCw } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import apiClient from '../api/apiClient';
import { claimGlobalAudio, releaseGlobalAudio } from '../utils/audioPlayback';
import JapaneseLessonReference from './studyPage/teaching/components/JapaneseLessonReference';
import LessonPracticePreview from './studyPage/teaching/components/LessonPracticePreview';
import LessonSlideDeckPlayer from './studyPage/teaching/components/LessonSlideDeckPlayer';

const DEFAULTS = {
    pipeline: 'minna_no_nihongo',
    lang: 'zh',
    lesson: '001',
};

const LANG_LABELS = {
    zh: '中文',
    en: 'English',
    ja: '日本語',
    fr: 'Français',
    de: 'Deutsch',
    ko: '한국어',
    es: 'Español',
    pt: 'Português',
    ru: 'Русский',
    th: 'ไทย',
    vi: 'Tiếng Việt',
};

const normalizeLesson = (value) => {
    const digits = String(value || '').match(/\d+/)?.[0] || DEFAULTS.lesson;
    return digits.length >= 3 ? digits : digits.padStart(3, '0');
};

const withCacheBust = (value, version) => {
    if (!value || !version) return value;
    const joiner = String(value).includes('?') ? '&' : '?';
    return `${value}${joiner}preview_v=${version}`;
};

const cacheBustAsset = (asset, version) => {
    if (!asset || typeof asset !== 'object') return asset;
    return {
        ...asset,
        media_url: withCacheBust(asset.media_url, version),
        image_url: withCacheBust(asset.image_url, version),
        audio_url: withCacheBust(asset.audio_url, version),
        url: withCacheBust(asset.url, version),
        media_path: withCacheBust(asset.media_path, version),
    };
};

const normalizeAudioNumber = (value) => {
    const num = Number(value);
    return Number.isFinite(num) ? String(num) : '';
};

const normalizeAudioText = (value) => String(value || '')
    .trim()
    .replace(/\[[^\]]+\]/g, '')
    .replace(/[［][^］]+[］]/g, '')
    .replace(/[\s「」『』（）()]/g, '')
    .replace(/[。！？!?、，,.・]/g, '');

const basenameOf = (value) => {
    const text = String(value || '').trim();
    if (!text) return '';
    return text.split(/[\\/]/).pop() || '';
};

const toAbsoluteMediaUrl = (value, apiBase) => {
    const raw = String(value || '').trim();
    if (!raw) return '';
    if (/^https?:\/\//i.test(raw)) return raw;
    const base = String(apiBase || '').replace(/\/$/, '');
    return `${base}${raw.startsWith('/') ? raw : `/${raw}`}`;
};

export default function LocalTeachingPreview() {
    const [searchParams, setSearchParams] = useSearchParams();
    const [pipeline, setPipeline] = useState(searchParams.get('pipeline') || DEFAULTS.pipeline);
    const [lang, setLang] = useState(searchParams.get('lang') || DEFAULTS.lang);
    const [lesson, setLesson] = useState(searchParams.get('lesson') || DEFAULTS.lesson);
    const [artifactOptions, setArtifactOptions] = useState([]);
    const [optionsLoading, setOptionsLoading] = useState(true);
    const [optionsError, setOptionsError] = useState('');
    const [payload, setPayload] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [cacheVersion, setCacheVersion] = useState('');
    const [playingKey, setPlayingKey] = useState(null);
    const [audioLoadingKey, setAudioLoadingKey] = useState(null);
    const audioRef = useRef(null);
    const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';

    const query = useMemo(() => ({
        pipeline_id: searchParams.get('pipeline') || DEFAULTS.pipeline,
        lang: searchParams.get('lang') || DEFAULTS.lang,
        lesson_id: normalizeLesson(searchParams.get('lesson') || DEFAULTS.lesson),
    }), [searchParams]);

    const pipelineOptions = useMemo(() => {
        if (artifactOptions.length) return artifactOptions;
        return [{
            pipeline_id: pipeline,
            display_name: pipeline,
            languages: [{ lang, lessons: [normalizeLesson(lesson)] }],
        }];
    }, [artifactOptions, lang, lesson, pipeline]);
    const selectedPipelineOption = pipelineOptions.find((item) => item.pipeline_id === pipeline);
    const languageOptions = useMemo(
        () => selectedPipelineOption?.languages || [],
        [selectedPipelineOption],
    );
    const selectedLanguageOption = languageOptions.find((item) => item.lang === lang);
    const lessonOptions = selectedLanguageOption?.lessons || [];
    const hasAvailableSelection = lessonOptions.includes(normalizeLesson(lesson));

    useEffect(() => {
        let cancelled = false;

        const loadArtifactOptions = async () => {
            setOptionsLoading(true);
            setOptionsError('');
            try {
                const res = await apiClient.get('/dev/lesson-artifact-options');
                const options = Array.isArray(res.data?.pipelines) ? res.data.pipelines : [];
                if (!cancelled) setArtifactOptions(options);
            } catch (err) {
                console.error('Local teaching preview options failed:', err);
                if (!cancelled) setOptionsError('无法读取产物列表，当前仍可加载 URL 中的选项。');
            } finally {
                if (!cancelled) setOptionsLoading(false);
            }
        };

        loadArtifactOptions();
        return () => {
            cancelled = true;
        };
    }, []);

    const stopPreviewAudio = useCallback(() => {
        const audio = audioRef.current;
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
            releaseGlobalAudio(audio);
            if (audioRef.current === audio) {
                audioRef.current = null;
            }
        }
        setPlayingKey(null);
        setAudioLoadingKey(null);
    }, []);

    const loadPreview = useCallback(async () => {
        stopPreviewAudio();
        setLoading(true);
        setError('');
        try {
            const res = await apiClient.get('/dev/lesson-artifact-preview', { params: query });
            setPayload(res.data || null);
            setCacheVersion(String(Date.now()));
        } catch (err) {
            console.error('Local teaching preview failed:', err);
            const detail = err?.response?.data?.detail;
            const message = typeof detail === 'string'
                ? detail
                : detail?.message || '本地 artifact 加载失败。';
            setPayload(null);
            setError(message);
        } finally {
            setLoading(false);
        }
    }, [query, stopPreviewAudio]);

    useEffect(() => {
        setPipeline(query.pipeline_id);
        setLang(query.lang);
        setLesson(query.lesson_id);
        loadPreview();
    }, [loadPreview, query]);

    useEffect(() => () => stopPreviewAudio(), [stopPreviewAudio]);

    const applyParams = useCallback((event) => {
        event?.preventDefault();
        setSearchParams({
            pipeline: pipeline.trim() || DEFAULTS.pipeline,
            lang: lang.trim() || DEFAULTS.lang,
            lesson: normalizeLesson(lesson),
        });
    }, [lang, lesson, pipeline, setSearchParams]);

    const changePipeline = useCallback((event) => {
        const nextPipelineId = event.target.value;
        const nextPipeline = pipelineOptions.find((item) => item.pipeline_id === nextPipelineId);
        const nextLanguage = nextPipeline?.languages?.find((item) => item.lang === lang)
            || nextPipeline?.languages?.[0];
        const currentLesson = normalizeLesson(lesson);
        const nextLesson = nextLanguage?.lessons?.includes(currentLesson)
            ? currentLesson
            : nextLanguage?.lessons?.[0] || '';

        setPipeline(nextPipelineId);
        setLang(nextLanguage?.lang || '');
        setLesson(nextLesson);
    }, [lang, lesson, pipelineOptions]);

    const changeLanguage = useCallback((event) => {
        const nextLang = event.target.value;
        const nextLanguage = languageOptions.find((item) => item.lang === nextLang);
        const currentLesson = normalizeLesson(lesson);
        const nextLesson = nextLanguage?.lessons?.includes(currentLesson)
            ? currentLesson
            : nextLanguage?.lessons?.[0] || '';

        setLang(nextLang);
        setLesson(nextLesson);
    }, [languageOptions, lesson]);

    const data = payload?.lesson_content || {};
    const metadata = data?.lesson_metadata || {};
    const lessonAudioAssets = data?.lesson_audio_assets || null;
    const deck = payload?.teaching_slide_deck || null;
    const previewDeck = useMemo(() => {
        if (!deck || !Array.isArray(deck.slides)) return deck;
        return {
            ...deck,
            slides: deck.slides.map((slide) => ({
                ...slide,
                image: cacheBustAsset(slide?.image, cacheVersion),
                audio: cacheBustAsset(slide?.audio, cacheVersion),
            })),
        };
    }, [cacheVersion, deck]);
    const slideCount = Array.isArray(deck?.slides) ? deck.slides.length : 0;
    const audioStatus = data?.explanation_narration_audio?.status || deck?.audio_status || 'unknown';
    const lessonAudioItems = useMemo(
        () => (Array.isArray(lessonAudioAssets?.items) ? lessonAudioAssets.items : []),
        [lessonAudioAssets?.items],
    );
    const readyLessonAudioItems = useMemo(
        () => lessonAudioItems.filter((item) => item?.status === 'ready').length,
        [lessonAudioItems],
    );

    const buildPreviewAudioUrl = useCallback((asset) => {
        if (!asset || typeof asset !== 'object') return '';
        const raw = asset.audio_url || asset.media_url || asset.url || asset.media_path || '';
        if (raw) return toAbsoluteMediaUrl(withCacheBust(raw, cacheVersion), API_BASE);

        const filename = basenameOf(asset.local_audio_file);
        if (!filename) return '';
        const fallbackPath = `/media/lesson-audio/${query.pipeline_id}/${query.lesson_id}/${encodeURIComponent(filename)}`;
        return toAbsoluteMediaUrl(withCacheBust(fallbackPath, cacheVersion), API_BASE);
    }, [API_BASE, cacheVersion, query.lesson_id, query.pipeline_id]);

    const lessonAudioLookup = useMemo(() => {
        const map = new Map();
        const add = (key, item) => {
            if (key && !map.has(key)) map.set(key, item);
        };

        const sectionCounts = {};
        lessonAudioItems.forEach((item) => {
            if (!item || typeof item !== 'object') return;
            const section = String(item.source_section || '').trim();
            const sourceRef = normalizeAudioNumber(item.source_ref);
            const lineRef = normalizeAudioNumber(item.line_ref);
            const textKey = normalizeAudioText(item.source_text);
            sectionCounts[section] = (sectionCounts[section] || 0) + 1;

            add(`audio:${item.audio_id || ''}`, item);
            if (section && sourceRef) add(`${section}:source:${sourceRef}`, item);
            if (section && lineRef) add(`${section}:line:${lineRef}`, item);
            if (section) add(`${section}:index:${sectionCounts[section]}`, item);
            if (textKey) add(`text:${textKey}`, item);
        });

        return map;
    }, [lessonAudioItems]);

    const resolveLessonAudioAsset = useCallback((text, audioKey, meta = {}) => {
        const keys = [];
        const sourceSection = String(meta?.sourceSection || '').trim();
        const sourceRef = normalizeAudioNumber(meta?.sourceRef);
        const lineRef = normalizeAudioNumber(meta?.lineRef);
        const index = Number(meta?.index);
        const itemNumber = Number.isFinite(index) ? String(index + 1) : '';

        if (sourceSection && sourceRef) keys.push(`${sourceSection}:source:${sourceRef}`);
        if (sourceSection && lineRef) keys.push(`${sourceSection}:line:${lineRef}`);
        if (sourceSection && itemNumber) keys.push(`${sourceSection}:index:${itemNumber}`);

        const textKey = normalizeAudioText(text);
        if (textKey) keys.push(`text:${textKey}`);

        const directKey = String(audioKey || '').trim();
        if (directKey) keys.push(`audio:${directKey}`);

        return keys.map((key) => lessonAudioLookup.get(key)).find(Boolean) || null;
    }, [lessonAudioLookup]);

    const canPlayTextAudio = useCallback((text, audioKey, meta) => {
        const asset = resolveLessonAudioAsset(text, audioKey, meta);
        return Boolean(buildPreviewAudioUrl(asset));
    }, [buildPreviewAudioUrl, resolveLessonAudioAsset]);

    const playTextAudio = useCallback((text, key, meta) => {
        const asset = resolveLessonAudioAsset(text, key, meta);
        const audioUrl = buildPreviewAudioUrl(asset);
        if (!audioUrl) return;

        if (audioLoadingKey === key) return;
        if (playingKey === key) {
            stopPreviewAudio();
            return;
        }

        stopPreviewAudio();
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        claimGlobalAudio(audio);
        setPlayingKey(key);
        setAudioLoadingKey(key);

        const clearIfStillCurrent = (prevKey) => (prevKey === key ? null : prevKey);
        const cleanup = () => {
            if (audioRef.current === audio) audioRef.current = null;
            releaseGlobalAudio(audio);
            setPlayingKey(clearIfStillCurrent);
            setAudioLoadingKey(clearIfStillCurrent);
        };

        audio.onplaying = () => {
            if (audioRef.current === audio) setAudioLoadingKey(clearIfStillCurrent);
        };
        audio.oncanplay = () => {
            if (audioRef.current === audio) setAudioLoadingKey(clearIfStillCurrent);
        };
        audio.onpause = cleanup;
        audio.onended = cleanup;
        audio.onerror = cleanup;
        audio.play().catch((err) => {
            console.error('播放本地预览音频失败:', err);
            cleanup();
        });
    }, [audioLoadingKey, buildPreviewAudioUrl, playingKey, resolveLessonAudioAsset, stopPreviewAudio]);

    return (
        <main className="min-h-screen bg-slate-50 px-5 py-24">
            <div className="mx-auto max-w-6xl">
                <section className="mb-8 border-b border-slate-200 pb-6">
                    <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
                        <div>
                            <p className="text-xs font-black uppercase tracking-[0.28em] text-slate-400">
                                Local Artifact Preview
                            </p>
                            <h1 className="mt-3 text-4xl font-black tracking-tight text-slate-950">
                                {metadata?.title_localized || metadata?.title || `Lesson ${query.lesson_id}`}
                            </h1>
                            <p className="mt-2 text-sm font-semibold text-slate-500">
                                {payload?.artifact_path || '直接读取本地生成产物，不入库、不上传 R2。'}
                            </p>
                        </div>

                        <form onSubmit={applyParams} className="flex flex-wrap items-end gap-3">
                            <label className="block">
                                <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">Pipeline</span>
                                <select
                                    value={pipeline}
                                    onChange={changePipeline}
                                    disabled={optionsLoading}
                                    className="h-11 w-64 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-800 outline-none focus:border-slate-500 disabled:cursor-wait disabled:bg-slate-100"
                                >
                                    {pipelineOptions.map((item) => (
                                        <option key={item.pipeline_id} value={item.pipeline_id}>
                                            {item.display_name || item.pipeline_id}
                                        </option>
                                    ))}
                                </select>
                            </label>
                            <label className="block">
                                <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">Lang</span>
                                <select
                                    value={lang}
                                    onChange={changeLanguage}
                                    disabled={optionsLoading || !languageOptions.length}
                                    className="h-11 w-36 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-800 outline-none focus:border-slate-500 disabled:cursor-not-allowed disabled:bg-slate-100"
                                >
                                    {!languageOptions.length && <option value="">暂无产物</option>}
                                    {languageOptions.map((item) => (
                                        <option key={item.lang} value={item.lang}>
                                            {LANG_LABELS[item.lang] ? `${LANG_LABELS[item.lang]} (${item.lang})` : item.lang}
                                        </option>
                                    ))}
                                </select>
                            </label>
                            <label className="block">
                                <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">Lesson</span>
                                <select
                                    value={lesson}
                                    onChange={(event) => setLesson(event.target.value)}
                                    disabled={optionsLoading || !lessonOptions.length}
                                    className="h-11 w-32 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-800 outline-none focus:border-slate-500 disabled:cursor-not-allowed disabled:bg-slate-100"
                                >
                                    {!lessonOptions.length && <option value="">暂无课次</option>}
                                    {lessonOptions.map((lessonId) => (
                                        <option key={lessonId} value={lessonId}>Lesson {lessonId}</option>
                                    ))}
                                </select>
                            </label>
                            <button
                                type="submit"
                                disabled={optionsLoading || !hasAvailableSelection}
                                className="inline-flex h-11 items-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-black text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                            >
                                <RefreshCw size={16} />
                                加载
                            </button>
                        </form>
                    </div>

                    {optionsError && (
                        <p className="mt-3 text-xs font-bold text-amber-700">{optionsError}</p>
                    )}

                    <div className="mt-5 flex flex-wrap gap-2 text-xs font-black uppercase tracking-wider">
                        <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-slate-600">
                            Slides {slideCount}
                        </span>
                        <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-slate-600">
                            Audio {audioStatus}
                        </span>
                        <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-slate-600">
                            Lesson Audio {readyLessonAudioItems}/{lessonAudioItems.length}
                        </span>
                        <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-slate-600">
                            {query.pipeline_id} / {query.lang} / {query.lesson_id}
                        </span>
                    </div>
                </section>

                {loading && (
                    <div className="flex h-64 items-center justify-center">
                        <Loader2 className="animate-spin text-slate-500" size={32} />
                    </div>
                )}

                {!loading && error && (
                    <div className="rounded-2xl border border-red-100 bg-red-50 px-5 py-4 text-sm font-bold text-red-700">
                        {error}
                    </div>
                )}

                {!loading && !error && previewDeck && (
                    <>
                        <LessonSlideDeckPlayer deck={previewDeck} apiBase={API_BASE} />
                        <JapaneseLessonReference
                            courseContent={data?.course_content || {}}
                            lessonMetadata={metadata}
                            playTextAudio={playTextAudio}
                            canPlayTextAudio={canPlayTextAudio}
                            playingKey={playingKey}
                            audioLoadingKey={audioLoadingKey}
                            className="mt-12"
                        />
                        <LessonPracticePreview
                            items={data?.database_items || []}
                            className="mt-12"
                        />
                    </>
                )}

                {!loading && !error && !deck && (
                    <div className="rounded-2xl border border-amber-100 bg-amber-50 px-5 py-4 text-sm font-bold text-amber-800">
                        找到了 JSON，但里面没有 teaching_slide_deck。先跑 stage2 生成 slides/audio。
                    </div>
                )}
            </div>
        </main>
    );
}
