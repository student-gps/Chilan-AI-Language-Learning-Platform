import React, { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { ChevronDown, ChevronLeft, ChevronRight, Maximize2, Minimize2, Pause, Play, Scan } from 'lucide-react';

const SLIDE_AUDIO_RATES = [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3];
const PLAYER_ASPECT_RATIO = 16 / 9;
const MAX_FULLSCREEN_PLAYER_WIDTH = 1760;
const MAX_EXPANDED_PLAYER_WIDTH = 1600;
const FULLSCREEN_PADDING = 4;
const EXPANDED_TOP_GAP = 12;
const EXPANDED_BOTTOM_GAP = 16;
const CARD_CHROME_HEIGHT = 4;

const fitPlayerWidth = ({ availableWidth, availableHeight, controlsHeight, maxWidth }) => {
    const availableStageHeight = availableHeight - controlsHeight - CARD_CHROME_HEIGHT;
    if (availableWidth <= 0 || availableStageHeight <= 0) return null;

    return Math.floor(Math.min(
        availableWidth,
        availableStageHeight * PLAYER_ASPECT_RATIO,
        maxWidth,
    ));
};

function RateSelector({ rate, setRate }) {
    const [open, setOpen] = useState(false);
    const ref = useRef(null);

    useEffect(() => {
        if (!open) return;
        const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [open]);

    return (
        <div ref={ref} className="relative shrink-0">
            <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="flex items-center gap-1 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-bold text-white transition hover:bg-white/20"
            >
                {rate.toFixed(1)}x <ChevronDown size={12} />
            </button>
            {open && (
                <div className="absolute bottom-[calc(100%+8px)] left-1/2 -translate-x-1/2 z-50 overflow-hidden rounded-2xl border border-white/15 bg-slate-900 shadow-2xl py-1.5 min-w-[72px]">
                    {SLIDE_AUDIO_RATES.map((r) => (
                        <button
                            key={r}
                            type="button"
                            onClick={() => { setRate(r); setOpen(false); }}
                            className={`w-full px-4 py-1.5 text-xs font-bold text-center transition hover:bg-white/10 ${r === rate ? 'text-white bg-white/15' : 'text-white/60'}`}
                        >
                            {r.toFixed(1)}x
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}

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

const cleanCaptionText = (text = '') => String(text).replace(/\[[a-z]{2}:([^\]]+)\]/gi, '$1');

export default function LessonSlideDeckPlayer({ deck, apiBase = '' }) {
    const slides = Array.isArray(deck?.slides) ? deck.slides : [];
    const [index, setIndex] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [localMs, setLocalMs] = useState(0);
    const [rate, setRate] = useState(1.0);
    const [expanded, setExpanded] = useState(false);
    const [fullscreen, setFullscreen] = useState(false);
    const [controlsHeight, setControlsHeight] = useState(0);
    const [fittedWidth, setFittedWidth] = useState(null);

    const sectionRef = useRef(null);
    const panelRef = useRef(null);
    const controlsRef = useRef(null);
    const audioRef = useRef(null);
    const rafRef = useRef(null);
    const tickRef = useRef(null);

    // --- Data refs: tick reads from these so it never needs to be recreated ---
    const indexRef = useRef(0);
    const startMsRef = useRef(0);
    const endMsRef = useRef(1);
    const durationMsRef = useRef(1);
    const rateRef = useRef(1.0);
    const slidesRef = useRef(slides);
    const apiBaseRef = useRef(apiBase);
    // playSlide ref so tick can call it without a closure dep
    const playSlideRef = useRef(null);

    const slide = slides[index] || null;
    const hasAudio = deck?.audio_mode !== 'none';
    const imageUrl = resolveAssetUrl(slide?.image, apiBase);
    const audioUrl = hasAudio ? resolveAssetUrl(slide?.audio, apiBase) : '';
    const startMs = Number(slide?.audio?.start_ms || 0);
    const endMs = Number(slide?.audio?.end_ms || startMs + (slide?.duration_ms || 0));
    const durationMs = Math.max(1, Number(slide?.duration_ms || endMs - startMs || 1));
    const progress = Math.max(0, Math.min(1, localMs / durationMs));
    const cue = useMemo(() => currentCueFor(slide, hasAudio ? localMs : 0), [hasAudio, slide, localMs]);
    const cueKey = cue ? `${cue.start_ms}-${cue.end_ms}` : 'empty';

    // Sync all data refs every render so tick always reads fresh values
    useLayoutEffect(() => {
        indexRef.current = index;
        startMsRef.current = startMs;
        endMsRef.current = endMs;
        durationMsRef.current = durationMs;
        rateRef.current = rate;
        slidesRef.current = slides;
        apiBaseRef.current = apiBase;
    });

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

    // Advance to the next slide (or stop at the end). Called from both tick and
    // onended so that whichever fires first handles the transition. The mutual-
    // exclusion guarantee: the first caller runs stopAudio() which sets
    // audioRef.current = null and audio.onended = null, so the second path
    // either exits via `if (!audio) return` (tick) or finds a null handler
    // (onended) — no double-advance possible.
    const advanceRef = useRef(null);
    const advance = useCallback(() => {
        stopAudio();
        setPlaying(false);
        const nextIdx = indexRef.current + 1;
        if (nextIdx < slidesRef.current.length) {
            setTimeout(() => playSlideRef.current?.(nextIdx), 300);
        }
    }, [stopAudio]);
    useLayoutEffect(() => { advanceRef.current = advance; });

    // Stable tick: reads everything from refs, never needs to be recreated
    const tick = useCallback(() => {
        const audio = audioRef.current;
        if (!audio) return;
        const absoluteMs = audio.currentTime * 1000;
        const nextLocalMs = Math.max(0, absoluteMs - startMsRef.current);
        setLocalMs(Math.min(durationMsRef.current, nextLocalMs));
        if (absoluteMs >= endMsRef.current || nextLocalMs >= durationMsRef.current) {
            advanceRef.current?.();
            return;
        }
        rafRef.current = requestAnimationFrame(() => tickRef.current?.());
    }, []); // reads everything via refs
    useLayoutEffect(() => { tickRef.current = tick; });

    // playSlide: imperatively starts playing the slide at idx.
    // Updates refs first so the stable tick immediately reads correct data.
    const playSlide = useCallback((idx) => {
        const allSlides = slidesRef.current;
        const targetSlide = allSlides[idx];
        if (!targetSlide) return;
        const audioAsset = targetSlide.audio;
        const targetAudioUrl = resolveAssetUrl(audioAsset, apiBaseRef.current);
        if (!targetAudioUrl) return;

        const nStartMs = Number(audioAsset?.start_ms || 0);
        const nEndMs = Number(audioAsset?.end_ms || nStartMs + (targetSlide?.duration_ms || 0));
        const nDurationMs = Math.max(1, Number(targetSlide?.duration_ms || nEndMs - nStartMs || 1));

        // Update refs BEFORE starting RAF so tick reads correct slide data
        indexRef.current = idx;
        startMsRef.current = nStartMs;
        endMsRef.current = nEndMs;
        durationMsRef.current = nDurationMs;

        stopAudio();
        setLocalMs(0);
        setIndex(idx);

        const audio = new Audio(targetAudioUrl);
        audioRef.current = audio;
        audio.preload = 'auto';
        audio.playbackRate = rateRef.current;
        audio.preservesPitch = true;
        audio.currentTime = nStartMs / 1000;
        audio.onended = () => advanceRef.current?.();
        audio.onerror = () => { stopAudio(); setPlaying(false); };
        audio.play()
            .then(() => { setPlaying(true); rafRef.current = requestAnimationFrame(tick); })
            .catch(() => { stopAudio(); setPlaying(false); });
    }, [stopAudio, tick]);

    // Keep playSlideRef current so tick's setTimeout always calls the latest version
    useLayoutEffect(() => { playSlideRef.current = playSlide; });

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
        if (!hasAudio) {
            goTo(targetIndex);
            return;
        }
        const rect = event.currentTarget.getBoundingClientRect();
        const ratio = rect.width > 0 ? (event.clientX - rect.left) / rect.width : 0;
        if (targetIndex !== index) {
            if (playing) playSlide(targetIndex); else goTo(targetIndex);
            return;
        }
        seekTo(durationMs * Math.max(0, Math.min(1, ratio)));
    }, [durationMs, goTo, hasAudio, index, playSlide, playing, seekTo]);

    // play: resume/start current slide from localMs (used by toggle button)
    const play = useCallback(() => {
        if (!slide || !audioUrl) return;
        stopAudio();
        const audio = new Audio(audioUrl);
        audioRef.current = audio;
        audio.preload = 'auto';
        audio.playbackRate = rateRef.current;
        audio.preservesPitch = true;
        audio.currentTime = (startMs + localMs) / 1000;
        audio.onended = () => advanceRef.current?.();
        audio.onerror = () => { stopAudio(); setPlaying(false); };
        audio.play()
            .then(() => { setPlaying(true); rafRef.current = requestAnimationFrame(tick); })
            .catch(() => { stopAudio(); setPlaying(false); });
    }, [audioUrl, localMs, slide, startMs, stopAudio, tick]);

    const toggle = useCallback(() => {
        if (playing) {
            if (audioRef.current) {
                const syncedMs = Math.max(0, Math.min(durationMs, audioRef.current.currentTime * 1000 - startMs));
                setLocalMs(syncedMs);
            }
            stopAudio();
            setPlaying(false);
        } else {
            play();
        }
    }, [durationMs, play, playing, startMs, stopAudio]);

    useEffect(() => () => stopAudio(), [stopAudio]);

    // 图片预加载：当前 ±2 张，浏览器空闲时静默加载
    // 避免翻页时图片从空白闪出来
    useEffect(() => {
        if (!slides.length) return;
        const targets = [index - 1, index, index + 1, index + 2]
            .filter((i) => i >= 0 && i < slides.length);
        targets.forEach((i) => {
            const url = resolveAssetUrl(slides[i]?.image, apiBase);
            if (!url) return;
            const img = new Image();
            img.src = url;          // 触发浏览器缓存，不挂载到 DOM
        });
    }, [index, slides, apiBase]);

    // 音频预缓冲：当前 slide 和下一张 slide 的音频提前 preload
    // 用 <audio preload="auto"> 触发浏览器缓冲，不实际播放
    useEffect(() => {
        if (!hasAudio || !slides.length) return;
        const targets = [index, index + 1]
            .filter((i) => i >= 0 && i < slides.length);
        const nodes = targets.map((i) => {
            const url = resolveAssetUrl(slides[i]?.audio, apiBase);
            if (!url) return null;
            const audio = document.createElement('audio');
            audio.preload = 'auto';
            audio.src = url;
            return audio;
        }).filter(Boolean);
        // 不需要挂载 DOM，创建即触发缓冲
        return () => { nodes.forEach((a) => { a.src = ''; }); };
    }, [hasAudio, index, slides, apiBase]);

    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.playbackRate = rate;
            audioRef.current.preservesPitch = true;
        }
    }, [rate]);

    useEffect(() => {
        if (!controlsRef.current) return undefined;

        const updateControlsHeight = () => {
            setControlsHeight(Math.ceil(controlsRef.current?.getBoundingClientRect().height || 0));
        };
        updateControlsHeight();

        if (typeof ResizeObserver === 'undefined') return undefined;
        const observer = new ResizeObserver(updateControlsHeight);
        observer.observe(controlsRef.current);
        return () => observer.disconnect();
    }, []);

    useEffect(() => {
        const updateFittedWidth = () => {
            if (!fullscreen && !expanded) {
                setFittedWidth(null);
                return;
            }

            const panel = panelRef.current;
            if (!panel || controlsHeight <= 0) return;

            if (fullscreen) {
                setFittedWidth(fitPlayerWidth({
                    availableWidth: window.innerWidth - FULLSCREEN_PADDING * 2,
                    availableHeight: window.innerHeight - FULLSCREEN_PADDING * 2,
                    controlsHeight,
                    maxWidth: MAX_FULLSCREEN_PLAYER_WIDTH,
                }));
                return;
            }

            const panelTop = panel.getBoundingClientRect().top;
            setFittedWidth(fitPlayerWidth({
                availableWidth: window.innerWidth * 0.96,
                availableHeight: window.innerHeight - panelTop - EXPANDED_BOTTOM_GAP,
                controlsHeight,
                maxWidth: MAX_EXPANDED_PLAYER_WIDTH,
            }));
        };

        updateFittedWidth();
        window.addEventListener('resize', updateFittedWidth);
        window.addEventListener('scroll', updateFittedWidth, { passive: true });
        return () => {
            window.removeEventListener('resize', updateFittedWidth);
            window.removeEventListener('scroll', updateFittedWidth);
        };
    }, [controlsHeight, expanded, fullscreen]);

    useEffect(() => {
        if (!expanded || !sectionRef.current) return;
        const navEl = document.querySelector('nav');
        const navH = navEl ? navEl.getBoundingClientRect().height : 64;
        const top = sectionRef.current.getBoundingClientRect().top + window.scrollY - navH - EXPANDED_TOP_GAP;
        window.scrollTo({ top, behavior: 'smooth' });
    }, [expanded]);

    useEffect(() => {
        const onFullscreenChange = () => setFullscreen(document.fullscreenElement === panelRef.current);
        document.addEventListener('fullscreenchange', onFullscreenChange);
        return () => document.removeEventListener('fullscreenchange', onFullscreenChange);
    }, []);

    const toggleFullscreen = useCallback(() => {
        const panel = panelRef.current;
        if (!panel) return;
        if (document.fullscreenElement === panel) { document.exitFullscreen?.(); return; }
        panel.requestFullscreen?.().catch(() => {});
    }, []);

    if (!slides.length || !slide) return null;

    return (
        <section
            ref={sectionRef}
            className={`mb-16 ${expanded ? 'relative left-1/2 -translate-x-1/2' : ''}`}
            style={expanded ? { width: fittedWidth ? `${fittedWidth}px` : 'min(96vw, 128vh, 1600px)' } : undefined}
        >
            <div ref={panelRef} className="lesson-slide-deck">
                <style>
                    {`
                        @keyframes lesson-caption-in {
                            from { opacity: 0; transform: translateY(8px); }
                            to { opacity: 1; transform: translateY(0); }
                        }
                        .lesson-slide-deck:fullscreen {
                            box-sizing: border-box;
                            background: #020617;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            padding: ${FULLSCREEN_PADDING}px;
                        }
                        .lesson-slide-deck:fullscreen .lesson-slide-deck-card {
                            max-height: none;
                            border-radius: 0;
                            border-color: transparent;
                        }
                        .lesson-slide-deck:fullscreen .lesson-slide-deck-controls {
                            padding: 0.75rem 1rem;
                        }
                        .lesson-slide-deck:fullscreen .lesson-slide-deck-control-row {
                            min-height: 3.25rem;
                            flex-wrap: wrap;
                        }
                        .lesson-slide-deck:fullscreen .lesson-slide-deck-control-row > .flex-1 {
                            order: -1;
                            flex-basis: 100%;
                        }
                        .lesson-slide-deck:fullscreen .lesson-slide-deck-caption {
                            min-height: 0;
                            padding: 0.5rem 0.75rem;
                        }
                        .lesson-slide-deck:fullscreen .lesson-slide-deck-caption-text {
                            display: block;
                            overflow: visible;
                            font-size: 1.125rem;
                            line-height: 1.45;
                        }
                    `}
                </style>
                <div
                    className="lesson-slide-deck-card overflow-hidden rounded-[1.75rem] border border-slate-200 bg-slate-950 shadow-2xl"
                    style={fittedWidth ? { width: `${fittedWidth}px` } : undefined}
                >
                    <div className="lesson-slide-deck-stage relative w-full bg-slate-950" style={{ aspectRatio: '16/9' }}>
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

                    <div ref={controlsRef} className="lesson-slide-deck-controls border-t border-white/10 bg-slate-950 px-4 py-4">
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
                                        className="h-full rounded-full bg-white/85"
                                        style={{ width: `${i < index ? 100 : i === index ? progress * 100 : 0}%` }}
                                    />
                                </button>
                            ))}
                        </div>

                        <div className="lesson-slide-deck-control-row flex min-h-[4.75rem] items-center gap-3">
                            <button
                                type="button"
                                onClick={() => playing ? playSlide(index - 1) : goTo(index - 1)}
                                disabled={index === 0}
                                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white transition hover:bg-white/20 disabled:opacity-30"
                                aria-label="Previous slide"
                            >
                                <ChevronLeft size={20} />
                            </button>

                            <div className="flex min-w-0 flex-1 flex-col justify-center">
                                <div className="mb-1 flex items-center justify-center">
                                    <p className="truncate text-center text-xs font-black uppercase tracking-[0.18em] text-white/45">
                                        {hasAudio
                                            ? `${index + 1} / ${slides.length} · ${formatTime(localMs)} / ${formatTime(durationMs)}`
                                            : `${index + 1} / ${slides.length}`}
                                    </p>
                                </div>
                                <div className="lesson-slide-deck-caption flex min-h-[3.25rem] items-center rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                                    <p
                                        key={cueKey}
                                        className={`lesson-slide-deck-caption-text text-base font-semibold leading-relaxed text-white md:text-lg ${fullscreen ? '' : 'line-clamp-2'}`}
                                        style={{ animation: cue ? 'lesson-caption-in 180ms ease-out' : undefined }}
                                    >
                                        {cleanCaptionText(cue?.text || '')}
                                    </p>
                                </div>
                            </div>

                            {hasAudio && (
                                <button
                                    type="button"
                                    onClick={toggle}
                                    className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full border border-white/25 bg-white/20 text-white transition hover:bg-white/30"
                                    aria-label={playing ? 'Pause slide narration' : 'Play slide narration'}
                                >
                                    {playing ? <Pause size={22} /> : <Play size={22} className="ml-0.5" />}
                                </button>
                            )}

                            <button
                                type="button"
                                onClick={() => playing ? playSlide(index + 1) : goTo(index + 1)}
                                disabled={index === slides.length - 1}
                                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white transition hover:bg-white/20 disabled:opacity-30"
                                aria-label="Next slide"
                            >
                                <ChevronRight size={20} />
                            </button>

                            {hasAudio && <RateSelector rate={rate} setRate={setRate} />}

                            {!fullscreen && (
                                <button
                                    type="button"
                                    onClick={() => setExpanded((value) => !value)}
                                    className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white transition hover:bg-white/20 md:flex"
                                    aria-label={expanded ? 'Use normal size' : 'Use larger size'}
                                    title={expanded ? 'Normal size' : 'Larger size'}
                                >
                                    {expanded ? <Minimize2 size={18} /> : <Scan size={18} />}
                                </button>
                            )}

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
