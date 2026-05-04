import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Maximize2, Minimize2, Pause, Play, Scan } from 'lucide-react';

const resolveAssetUrl = (asset = {}, apiBase = '') => {
    const raw = asset.media_url || asset.image_url || asset.audio_url || asset.url || asset.media_path || '';
    if (!raw) return '';
    if (/^https?:\/\//i.test(raw)) return raw;
    return `${apiBase}${raw.startsWith('/') ? raw : `/${raw}`}`;
};

const formatTime = (ms) => {
    const total = Math.max(0, Math.floor((ms || 0) / 1000));
    const minutes = Math.floor(total / 60);
    const seconds = total % 60;
    return `${minutes}:${String(seconds).padStart(2, '0')}`;
};

const currentCueFor = (slide, localMs) => {
    const cues = Array.isArray(slide?.caption_cues) ? slide.caption_cues : [];
    return cues.find((cue) => localMs >= Number(cue.start_ms || 0) && localMs < Number(cue.end_ms || 0)) || null;
};

const cleanCaptionText = (text = '') => String(text).replace(/\[zh:([^\]]+)\]/g, '$1');

export default function LessonSlideDeckPlayer({ deck, apiBase = '' }) {
    const slides = Array.isArray(deck?.slides) ? deck.slides : [];
    const [index, setIndex] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [localMs, setLocalMs] = useState(0);
    const [expanded, setExpanded] = useState(false);
    const [fullscreen, setFullscreen] = useState(false);
    const panelRef = useRef(null);
    const audioRef = useRef(null);
    const rafRef = useRef(null);

    const slide = slides[index] || null;
    const imageUrl = resolveAssetUrl(slide?.image, apiBase);
    const audioUrl = resolveAssetUrl(slide?.audio, apiBase);
    const startMs = Number(slide?.audio?.start_ms || 0);
    const endMs = Number(slide?.audio?.end_ms || startMs + (slide?.duration_ms || 0));
    const durationMs = Math.max(1, Number(slide?.duration_ms || endMs - startMs || 1));
    const progress = Math.max(0, Math.min(1, localMs / durationMs));
    const cue = useMemo(() => currentCueFor(slide, localMs), [slide, localMs]);
    const cueKey = cue ? `${cue.start_ms}-${cue.end_ms}` : 'empty';

    const stopTicker = useCallback(() => {
        if (rafRef.current) {
            cancelAnimationFrame(rafRef.current);
            rafRef.current = null;
        }
    }, []);

    const stopAudio = useCallback(() => {
        stopTicker();
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.onended = null;
            audioRef.current.onerror = null;
            audioRef.current = null;
        }
    }, [stopTicker]);

    const goTo = useCallback((nextIndex) => {
        const clamped = Math.max(0, Math.min(slides.length - 1, nextIndex));
        stopAudio();
        setPlaying(false);
        setLocalMs(0);
        setIndex(clamped);
    }, [slides.length, stopAudio]);

    const seekTo = useCallback((nextLocalMs) => {
        const clamped = Math.max(0, Math.min(durationMs, nextLocalMs));
        setLocalMs(clamped);
        if (audioRef.current) {
            audioRef.current.currentTime = (startMs + clamped) / 1000;
        }
    }, [durationMs, startMs]);

    const handleTimelineClick = useCallback((event, targetIndex) => {
        const rect = event.currentTarget.getBoundingClientRect();
        const ratio = rect.width > 0 ? (event.clientX - rect.left) / rect.width : 0;
        if (targetIndex !== index) {
            goTo(targetIndex);
            return;
        }
        seekTo(durationMs * Math.max(0, Math.min(1, ratio)));
    }, [durationMs, goTo, index, seekTo]);

    const tick = useCallback(() => {
        const audio = audioRef.current;
        if (!audio) return;
        const absoluteMs = audio.currentTime * 1000;
        const nextLocalMs = Math.max(0, absoluteMs - startMs);
        setLocalMs(Math.min(durationMs, nextLocalMs));
        if (absoluteMs >= endMs || nextLocalMs >= durationMs) {
            stopAudio();
            setPlaying(false);
            if (index < slides.length - 1) {
                setTimeout(() => goTo(index + 1), 250);
            }
            return;
        }
        rafRef.current = requestAnimationFrame(tick);
    }, [durationMs, endMs, goTo, index, slides.length, startMs, stopAudio]);

    const play = useCallback(() => {
        if (!slide || !audioUrl) return;
        stopAudio();
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.preload = 'auto';
        audio.currentTime = (startMs + localMs) / 1000;
        audio.onended = () => {
            stopTicker();
            setPlaying(false);
        };
        audio.onerror = () => {
            stopAudio();
            setPlaying(false);
        };
        audio.play()
            .then(() => {
                setPlaying(true);
                rafRef.current = requestAnimationFrame(tick);
            })
            .catch(() => {
                stopAudio();
                setPlaying(false);
            });
    }, [audioUrl, localMs, slide, startMs, stopAudio, stopTicker, tick]);

    const toggle = useCallback(() => {
        if (playing) {
            stopAudio();
            setPlaying(false);
        } else {
            play();
        }
    }, [play, playing, stopAudio]);

    useEffect(() => () => stopAudio(), [stopAudio]);

    useEffect(() => {
        const onFullscreenChange = () => setFullscreen(document.fullscreenElement === panelRef.current);
        document.addEventListener('fullscreenchange', onFullscreenChange);
        return () => document.removeEventListener('fullscreenchange', onFullscreenChange);
    }, []);

    const toggleFullscreen = useCallback(() => {
        const panel = panelRef.current;
        if (!panel) return;
        if (document.fullscreenElement === panel) {
            document.exitFullscreen?.();
            return;
        }
        panel.requestFullscreen?.().catch(() => {});
    }, []);

    if (!slides.length || !slide) return null;

    return (
        <section
            className={`mb-16 ${expanded ? 'relative left-1/2 -translate-x-1/2' : ''}`}
            style={expanded ? { width: 'min(96vw, 128vh, 1600px)' } : undefined}
        >
            <div ref={panelRef} className="lesson-slide-deck">
                <style>
                    {`
                        @keyframes lesson-caption-in {
                            from { opacity: 0; transform: translateY(8px); }
                            to { opacity: 1; transform: translateY(0); }
                        }
                        .lesson-slide-deck:fullscreen {
                            background: #020617;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            padding: 18px;
                        }
                        .lesson-slide-deck:fullscreen .lesson-slide-deck-card {
                            width: min(100%, 150vh, 1760px);
                            max-height: calc(100vh - 36px);
                        }
                    `}
                </style>
                <div className="lesson-slide-deck-card overflow-hidden rounded-[1.75rem] border border-slate-200 bg-slate-950 shadow-2xl">
                    <div className="relative w-full bg-slate-950" style={{ aspectRatio: '16/9' }}>
                        {imageUrl ? (
                            <img
                                src={imageUrl}
                                alt={slide.title || `Slide ${index + 1}`}
                                className="h-full w-full object-contain"
                                draggable={false}
                            />
                        ) : (
                            <div className="flex h-full w-full items-center justify-center text-white/50">
                                Slide unavailable
                            </div>
                        )}
                    </div>

                    <div className="border-t border-white/10 bg-slate-950 px-4 py-4">
                        <div className="mb-3 flex gap-1.5" aria-label="Slide timeline">
                            {slides.map((item, i) => (
                                <button
                                    key={i}
                                    type="button"
                                    onClick={(event) => handleTimelineClick(event, i)}
                                    className="group h-2 flex-1 overflow-hidden rounded-full bg-white/15 transition hover:bg-white/25 focus:outline-none focus:ring-2 focus:ring-white/40"
                                    aria-label={`Go to slide ${i + 1}${item?.title ? `: ${item.title}` : ''}`}
                                    title={item?.title || `Slide ${i + 1}`}
                                >
                                    <div
                                        className="h-full rounded-full bg-white/85 transition-[width]"
                                        style={{ width: `${i < index ? 100 : i === index ? progress * 100 : 0}%` }}
                                    />
                                </button>
                            ))}
                        </div>

                        <div className="flex min-h-[4.75rem] items-center gap-3">
                            <button
                                type="button"
                                onClick={() => goTo(index - 1)}
                                disabled={index === 0}
                                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white transition hover:bg-white/20 disabled:opacity-30"
                                aria-label="Previous slide"
                            >
                                <ChevronLeft size={20} />
                            </button>

                            <div className="flex min-w-0 flex-1 flex-col justify-center">
                                <div className="mb-1 flex items-center justify-center">
                                    <p className="truncate text-center text-xs font-black uppercase tracking-[0.18em] text-white/45">
                                        {index + 1} / {slides.length} · {formatTime(localMs)} / {formatTime(durationMs)}
                                    </p>
                                </div>
                                <div className="flex min-h-[3.25rem] items-center rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                                    <p
                                        key={cueKey}
                                        className="line-clamp-2 text-base font-semibold leading-relaxed text-white md:text-lg"
                                        style={{ animation: cue ? 'lesson-caption-in 180ms ease-out' : undefined }}
                                    >
                                        {cleanCaptionText(cue?.text || '')}
                                    </p>
                                </div>
                            </div>

                            <button
                                type="button"
                                onClick={toggle}
                                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-white/25 bg-white/20 text-white transition hover:bg-white/30"
                                aria-label={playing ? 'Pause slide narration' : 'Play slide narration'}
                            >
                                {playing ? <Pause size={22} /> : <Play size={22} className="ml-0.5" />}
                            </button>

                            <button
                                type="button"
                                onClick={() => goTo(index + 1)}
                                disabled={index === slides.length - 1}
                                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white transition hover:bg-white/20 disabled:opacity-30"
                                aria-label="Next slide"
                            >
                                <ChevronRight size={20} />
                            </button>

                            <button
                                type="button"
                                onClick={() => setExpanded((value) => !value)}
                                className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white transition hover:bg-white/20 md:flex"
                                aria-label={expanded ? 'Use normal size' : 'Use larger size'}
                                title={expanded ? 'Normal size' : 'Larger size'}
                            >
                                {expanded ? <Minimize2 size={18} /> : <Scan size={18} />}
                            </button>

                            <button
                                type="button"
                                onClick={toggleFullscreen}
                                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white transition hover:bg-white/20"
                                aria-label={fullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
                                title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
                            >
                                {fullscreen ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
