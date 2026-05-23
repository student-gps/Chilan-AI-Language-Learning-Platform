import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Loader2, RefreshCw } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import apiClient from '../api/apiClient';
import JapaneseLessonReference from './studyPage/teaching/components/JapaneseLessonReference';
import LessonPracticePreview from './studyPage/teaching/components/LessonPracticePreview';
import LessonSlideDeckPlayer from './studyPage/teaching/components/LessonSlideDeckPlayer';

const DEFAULTS = {
    pipeline: 'minna_no_nihongo',
    lang: 'zh',
    lesson: '001',
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

export default function LocalTeachingPreview() {
    const [searchParams, setSearchParams] = useSearchParams();
    const [pipeline, setPipeline] = useState(searchParams.get('pipeline') || DEFAULTS.pipeline);
    const [lang, setLang] = useState(searchParams.get('lang') || DEFAULTS.lang);
    const [lesson, setLesson] = useState(searchParams.get('lesson') || DEFAULTS.lesson);
    const [payload, setPayload] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [cacheVersion, setCacheVersion] = useState('');
    const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';

    const query = useMemo(() => ({
        pipeline_id: searchParams.get('pipeline') || DEFAULTS.pipeline,
        lang: searchParams.get('lang') || DEFAULTS.lang,
        lesson_id: normalizeLesson(searchParams.get('lesson') || DEFAULTS.lesson),
    }), [searchParams]);

    const loadPreview = useCallback(async () => {
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
    }, [query]);

    useEffect(() => {
        setPipeline(query.pipeline_id);
        setLang(query.lang);
        setLesson(query.lesson_id);
        loadPreview();
    }, [loadPreview, query]);

    const applyParams = useCallback((event) => {
        event?.preventDefault();
        setSearchParams({
            pipeline: pipeline.trim() || DEFAULTS.pipeline,
            lang: lang.trim() || DEFAULTS.lang,
            lesson: normalizeLesson(lesson),
        });
    }, [lang, lesson, pipeline, setSearchParams]);

    const data = payload?.lesson_content || {};
    const metadata = data?.lesson_metadata || {};
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
                                <input
                                    value={pipeline}
                                    onChange={(event) => setPipeline(event.target.value)}
                                    className="h-11 w-52 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-800 outline-none focus:border-slate-500"
                                />
                            </label>
                            <label className="block">
                                <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">Lang</span>
                                <input
                                    value={lang}
                                    onChange={(event) => setLang(event.target.value)}
                                    className="h-11 w-20 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-800 outline-none focus:border-slate-500"
                                />
                            </label>
                            <label className="block">
                                <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">Lesson</span>
                                <input
                                    value={lesson}
                                    onChange={(event) => setLesson(event.target.value)}
                                    className="h-11 w-24 rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold text-slate-800 outline-none focus:border-slate-500"
                                />
                            </label>
                            <button
                                type="submit"
                                className="inline-flex h-11 items-center gap-2 rounded-xl bg-slate-950 px-4 text-sm font-black text-white transition hover:bg-slate-800"
                            >
                                <RefreshCw size={16} />
                                加载
                            </button>
                        </form>
                    </div>

                    <div className="mt-5 flex flex-wrap gap-2 text-xs font-black uppercase tracking-wider">
                        <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-slate-600">
                            Slides {slideCount}
                        </span>
                        <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-slate-600">
                            Audio {audioStatus}
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
