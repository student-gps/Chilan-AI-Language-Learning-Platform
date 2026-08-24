import { useCallback, useEffect, useRef, useState } from 'react';
import { blackboard } from '../explanation/templateUtils';
import ChalkTexture from '../explanation/ChalkTexture';

const NAV_BUTTON_STYLE = {
    background: 'rgba(244,240,230,0.12)',
    border: '1px solid rgba(244,240,230,0.20)',
    borderRadius: 99,
    width: 30,
    height: 30,
    color: 'rgba(244,240,230,0.85)',
    fontSize: 16,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
    lineHeight: 1,
};

function BottomBar({ index, total, progress, playing, onPrev, onToggle, onNext, subtitle, labels }) {
    return (
        <div style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            zIndex: 10,
            background: 'linear-gradient(to top, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0.60) 55%, transparent 100%)',
            paddingTop: 28,
        }}>
            <div style={{ display: 'flex', gap: 4, padding: '0 16px 8px' }}>
                {Array.from({ length: total }).map((_, itemIndex) => {
                    const fill = itemIndex < index ? 1 : itemIndex === index ? progress : 0;
                    return (
                        <div key={itemIndex} style={{ flex: 1, height: 2, borderRadius: 99, background: 'rgba(244,240,230,0.18)', overflow: 'hidden' }}>
                            <div style={{
                                height: '100%',
                                width: `${fill * 100}%`,
                                background: 'rgba(244,240,230,0.80)',
                                borderRadius: 99,
                                transition: fill === 1 || fill === 0 ? 'none' : 'width 0.25s linear',
                            }} />
                        </div>
                    );
                })}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '4px 16px 14px' }}>
                <button type="button" aria-label={labels.previousSlide} onClick={onPrev} disabled={index === 0} style={{ ...NAV_BUTTON_STYLE, cursor: index === 0 ? 'default' : 'pointer', opacity: index === 0 ? 0.28 : 1 }}>‹</button>
                <p style={{
                    flex: 1,
                    margin: 0,
                    fontSize: 13,
                    lineHeight: 1.55,
                    color: 'rgba(244,240,230,0.75)',
                    fontWeight: 400,
                    overflow: 'hidden',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                }}>
                    {subtitle}
                </p>
                <button type="button" aria-label={playing ? labels.pauseNarration : labels.playNarration} onClick={onToggle} style={{
                    ...NAV_BUTTON_STYLE,
                    width: 36,
                    height: 36,
                    fontSize: 14,
                    background: 'rgba(244,240,230,0.20)',
                    border: '1px solid rgba(244,240,230,0.28)',
                    cursor: 'pointer',
                }}>
                    {playing ? '⏸' : '▶'}
                </button>
                <button type="button" aria-label={labels.nextSlide} onClick={onNext} disabled={index === total - 1} style={{ ...NAV_BUTTON_STYLE, cursor: index === total - 1 ? 'default' : 'pointer', opacity: index === total - 1 ? 0.28 : 1 }}>›</button>
            </div>
        </div>
    );
}

export default function NarratedCourseIntroDeck({
    slides,
    renderSlide,
    getNarrationText,
    getAudioUrls,
    ariaLabel = 'Course introduction',
    labels = {},
}) {
    const playerLabels = {
        previousSlide: 'Previous slide',
        nextSlide: 'Next slide',
        playNarration: 'Play narration',
        pauseNarration: 'Pause narration',
        ...labels,
    };
    const [index, setIndex] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const audioRef = useRef(null);
    const timerRef = useRef(null);
    const advanceTimeoutRef = useRef(null);
    const elapsedRef = useRef(0);
    const currentSlide = slides[index];
    const subtitle = playing || progress > 0 ? getNarrationText(currentSlide.id) : '';

    const stopAudio = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.onended = null;
            audioRef.current.ontimeupdate = null;
            audioRef.current.onerror = null;
            audioRef.current = null;
        }
        clearInterval(timerRef.current);
        timerRef.current = null;
        clearTimeout(advanceTimeoutRef.current);
        advanceTimeoutRef.current = null;
    }, []);

    const advance = useCallback(() => {
        setIndex((currentIndex) => {
            if (currentIndex < slides.length - 1) return currentIndex + 1;
            setPlaying(false);
            return currentIndex;
        });
    }, [slides.length]);

    const startTimerFallback = useCallback((slide) => {
        const duration = slide.duration;
        timerRef.current = setInterval(() => {
            elapsedRef.current += 200;
            setProgress(Math.min(elapsedRef.current / duration, 1));
            if (elapsedRef.current >= duration) {
                clearInterval(timerRef.current);
                timerRef.current = null;
                advance();
            }
        }, 200);
    }, [advance]);

    const startAudio = useCallback((slide) => {
        stopAudio();
        elapsedRef.current = 0;
        setProgress(0);
        const narration = getNarrationText(slide.id);
        const urls = getAudioUrls(slide, narration).filter(Boolean);
        let urlIndex = 0;

        const tryNext = () => {
            if (urlIndex >= urls.length) {
                startTimerFallback(slide);
                return;
            }

            const audio = new Audio(urls[urlIndex++]);
            audioRef.current = audio;
            audio.ontimeupdate = () => {
                if (audio.duration && audio.duration > 0) setProgress(audio.currentTime / audio.duration);
            };
            audio.onended = () => {
                setProgress(1);
                advanceTimeoutRef.current = setTimeout(advance, 600);
            };
            audio.onerror = () => {
                audio.onerror = null;
                tryNext();
            };
            audio.play().catch(() => {
                audio.onerror = null;
                tryNext();
            });
        };

        tryNext();
    }, [advance, getAudioUrls, getNarrationText, startTimerFallback, stopAudio]);

    const goTo = useCallback((nextIndex) => {
        const clamped = Math.max(0, Math.min(slides.length - 1, nextIndex));
        stopAudio();
        setProgress(0);
        setIndex(clamped);
    }, [slides.length, stopAudio]);

    const toggle = useCallback(() => {
        setPlaying((wasPlaying) => {
            if (wasPlaying) {
                if (audioRef.current) audioRef.current.pause();
                clearInterval(timerRef.current);
            }
            return !wasPlaying;
        });
    }, []);

    useEffect(() => {
        if (playing) startAudio(slides[index]);
    }, [index, playing, slides, startAudio]);

    useEffect(() => () => stopAudio(), [stopAudio]);

    return (
        <div
            role="region"
            aria-label={ariaLabel}
            style={{
                ...blackboard.shell,
                aspectRatio: '16/9',
                borderRadius: 20,
                boxShadow: 'inset 0 0 100px rgba(0,0,0,0.30), 0 0 0 4px #6B4820, 0 40px 100px rgba(0,0,0,0.50)',
                overflow: 'hidden',
                userSelect: 'none',
            }}
        >
            <ChalkTexture opacity={0.07} zIndex={0} />
            <div style={{
                position: 'absolute',
                inset: 0,
                pointerEvents: 'none',
                zIndex: 0,
                boxShadow: 'inset 0 0 0 18px #9C7040, inset 0 0 130px rgba(0,0,0,0.14)',
            }} />
            <div style={{
                position: 'absolute',
                inset: 0,
                paddingTop: 18,
                paddingBottom: 72,
                display: 'flex',
                flexDirection: 'column',
                zIndex: 2,
            }}>
                {renderSlide(currentSlide)}
            </div>
            <BottomBar
                index={index}
                total={slides.length}
                progress={progress}
                playing={playing}
                onPrev={() => goTo(index - 1)}
                onToggle={toggle}
                onNext={() => goTo(index + 1)}
                subtitle={subtitle}
                labels={playerLabels}
            />
        </div>
    );
}
