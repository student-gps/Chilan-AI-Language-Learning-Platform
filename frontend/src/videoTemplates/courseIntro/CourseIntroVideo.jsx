import { useState, useEffect, useCallback, useRef } from 'react';
import { chalk, blackboard } from '../explanation/templateUtils';
import ChalkTexture from '../explanation/ChalkTexture';

// Static narration audio — pre-generated with CosyVoice TTS.
// Run:  cd backend && python generate_intro_narration.py
//       cd backend && python upload_intro_audio_to_r2.py
// Dev:  served from frontend/public/audio/intro/ via backend /media/intro/
// Prod: backend /media/intro/ redirects to R2 zh/audio/intro/
const _API = import.meta.env.VITE_APP_API_BASE_URL || '';
const audioUrl = (id) => `${_API}/media/intro/slide_${id}.mp3`;

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE DEFINITIONS
// ─────────────────────────────────────────────────────────────────────────────

const SLIDES = [
    {
        id: 'welcome',
        duration: 14000,   // fallback if audio fails to load
        narration: "Welcome to Chilan — an AI-powered Chinese language learning platform. This course builds real communication skills: listening, speaking, and typing. We start from first principles, beginning with the sound system.",
    },
    {
        id: 'sounds',
        duration: 14000,
        narration: "Every Chinese syllable has a tone, and changing the tone completely changes the meaning. The four tones are high and level, rising, falling-rising, and falling. Mastering tones is the single most important foundation in Chinese.",
    },
    {
        id: 'skills',
        duration: 14000,
        narration: "This course trains three core skills: listening, speaking, and typing with a pinyin input method. We focus on how Chinese is actually used in daily digital life — not handwriting. You'll be able to read, listen, speak, and type before long.",
    },
    {
        id: 'ai',
        duration: 16000,
        narration: "Every answer you submit is evaluated by a three-tier system. Instant pattern matching handles obvious cases. Semantic comparison catches answers that mean the same thing in different words. And a large language model handles genuine edge cases with a detailed explanation.",
    },
    {
        id: 'fsrs',
        duration: 14000,
        narration: "Your review schedule is powered by FSRS — the Free Spaced Repetition Scheduler. Items you know well come back less often. Tricky items reappear sooner. This ensures you spend your study time exactly where it's needed.",
    },
    {
        id: 'start',
        duration: 13000,
        narration: "You're ready to begin. Start with the foundation modules: pinyin for the sound system, then Chinese characters for structure. Every lesson in the course builds on these foundations.",
    },
];

// ── Shared style helpers ─────────────────────────────────────────────────────

const s = {
    label: {
        fontSize: 11,
        fontWeight: 900,
        letterSpacing: '0.26em',
        textTransform: 'uppercase',
        color: 'rgba(244,240,230,0.35)',
        marginBottom: 16,
    },
    h1: {
        fontSize: 52,
        fontWeight: 900,
        color: chalk.white,
        lineHeight: 1.12,
        letterSpacing: '-0.01em',
        margin: 0,
    },
    h2: {
        fontSize: 40,
        fontWeight: 900,
        color: chalk.white,
        lineHeight: 1.2,
        margin: 0,
    },
    sub: {
        fontSize: 21,
        color: 'rgba(244,240,230,0.62)',
        lineHeight: 1.7,
        margin: 0,
        fontWeight: 400,
    },
    accent: (color = chalk.yellow) => ({
        color,
        fontWeight: 900,
    }),
    pill: (color = chalk.yellow) => ({
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        padding: '7px 18px',
        borderRadius: 999,
        background: `${color}18`,
        border: `1px solid ${color}44`,
        fontSize: 13,
        fontWeight: 800,
        color,
        letterSpacing: '0.08em',
    }),
    card: {
        borderRadius: 14,
        background: 'rgba(0,0,0,0.28)',
        border: '1px solid rgba(244,240,230,0.12)',
        padding: '22px 28px',
    },
};

// ── Individual slides ────────────────────────────────────────────────────────

function SlideWelcome() {
    return (
        <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            padding: '0 80px',
            gap: 24,
        }}>
            <div style={{
                position: 'absolute', inset: 0,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                pointerEvents: 'none', zIndex: 0, overflow: 'hidden',
            }}>
                {['你', '好', '学', '习', '中', '文'].map((char, i) => (
                    <span key={i} style={{
                        fontSize: 120 + (i % 3) * 30,
                        fontWeight: 900,
                        color: 'rgba(244,240,230,0.025)',
                        position: 'absolute',
                        left: `${[8, 22, 38, 55, 70, 85][i]}%`,
                        top: `${[10, 55, 15, 60, 8, 45][i]}%`,
                        transform: `rotate(${[-8, 5, -4, 7, -6, 3][i]}deg)`,
                        userSelect: 'none',
                    }}>{char}</span>
                ))}
            </div>
            <div style={{ position: 'relative', zIndex: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22 }}>
                <div style={s.pill(chalk.blue)}>✦ &nbsp;CHILAN · 汉语</div>
                <h1 style={{ ...s.h1, fontSize: 60 }}>
                    Learn Chinese<br />
                    <span style={s.accent(chalk.yellow)}>the way it's actually used</span>
                </h1>
                <p style={{ ...s.sub, maxWidth: 520 }}>
                    AI-powered · communication-first · built for the digital age
                </p>
            </div>
        </div>
    );
}

function SlideSound() {
    const tones = [
        { mark: 'ā', n: '1', tone: 'high level',    color: chalk.blue },
        { mark: 'á', n: '2', tone: 'rising',         color: chalk.green },
        { mark: 'ǎ', n: '3', tone: 'falling-rising', color: chalk.yellow },
        { mark: 'à', n: '4', tone: 'falling',        color: chalk.pink },
    ];
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px 10px', gap: 24, justifyContent: 'center' }}>
            <div>
                <div style={s.label}>Foundation — Step 1</div>
                <h2 style={s.h2}>We start with <span style={s.accent(chalk.blue)}>sounds</span></h2>
                <p style={{ ...s.sub, marginTop: 12, fontSize: 18 }}>
                    Before words, before grammar — master the 4 tones that change everything.
                </p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16 }}>
                {tones.map((t) => (
                    <div key={t.n} style={{ ...s.card, textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'center' }}>
                        <span style={{ fontSize: 52, fontWeight: 900, color: t.color, lineHeight: 1, fontFamily: 'system-ui, -apple-system, sans-serif' }}>{t.mark}</span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            <span style={{ fontSize: 16, fontWeight: 900, color: 'rgba(244,240,230,0.5)' }}>{t.n}{['st','nd','rd','th'][parseInt(t.n)-1]} tone</span>
                            <span style={{ fontSize: 14, color: 'rgba(244,240,230,0.4)', fontStyle: 'italic' }}>{t.tone}</span>
                        </div>
                    </div>
                ))}
            </div>
            <p style={{ ...s.sub, fontSize: 16, opacity: 0.5, textAlign: 'center' }}>
                妈 (mom) · 麻 (hemp) · 马 (horse) · 骂 (scold) — same syllable, four different meanings
            </p>
        </div>
    );
}

function SlideSkills() {
    const skills = [
        { icon: '👂', label: 'Listen', sub: 'Audio for every word and sentence. Dictation exercises train your ear.', color: chalk.green },
        { icon: '🎤', label: 'Speak',  sub: 'Record your voice. AI checks your meaning, not just pronunciation.', color: chalk.blue },
        { icon: '⌨️', label: 'Type',   sub: 'Pinyin IME — how native speakers write every day on phones and computers.', color: chalk.yellow },
    ];
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px 10px', gap: 24, justifyContent: 'center' }}>
            <div>
                <div style={s.label}>What you'll practise</div>
                <h2 style={s.h2}>Three skills, <span style={s.accent(chalk.green)}>one course</span></h2>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 18 }}>
                {skills.map((sk) => (
                    <div key={sk.label} style={{ ...s.card, display: 'flex', flexDirection: 'column', gap: 14 }}>
                        <span style={{ fontSize: 38 }}>{sk.icon}</span>
                        <div>
                            <div style={{ fontSize: 26, fontWeight: 900, color: sk.color, marginBottom: 8 }}>{sk.label}</div>
                            <p style={{ margin: 0, fontSize: 17, lineHeight: 1.7, color: 'rgba(244,240,230,0.55)' }}>{sk.sub}</p>
                        </div>
                    </div>
                ))}
            </div>
            <div style={{
                display: 'flex', alignItems: 'center', gap: 12,
                background: 'rgba(0,0,0,0.22)', borderRadius: 12,
                padding: '14px 22px', border: '1px solid rgba(244,240,230,0.08)',
            }}>
                <span style={{ fontSize: 20 }}>✏️</span>
                <p style={{ margin: 0, fontSize: 16, color: 'rgba(244,240,230,0.42)', fontStyle: 'italic' }}>
                    Handwriting is a separate skill — this course focuses entirely on reading, listening, speaking, and typing.
                </p>
            </div>
        </div>
    );
}

function SlideAI() {
    return (
        <div style={{ flex: 1, display: 'flex', padding: '10px 52px 10px', gap: 36, alignItems: 'center' }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div>
                    <div style={s.label}>How answers are judged</div>
                    <h2 style={{ ...s.h2, fontSize: 34 }}>
                        AI evaluates<br /><span style={s.accent(chalk.pink)}>every answer</span>
                    </h2>
                    <p style={{ ...s.sub, marginTop: 12, fontSize: 17 }}>
                        A three-tier system: instant pattern match → semantic similarity → full LLM analysis.
                        Meaning matters more than exact wording.
                    </p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ fontSize: 12, fontWeight: 900, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(244,240,230,0.28)' }}>example</div>
                    <div style={{ ...s.card, display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span style={{ fontSize: 18 }}>✅</span>
                            <span style={{ fontSize: 17, color: chalk.green, fontWeight: 700 }}>"What do you usually do?"</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span style={{ fontSize: 18 }}>✅</span>
                            <span style={{ fontSize: 17, color: chalk.green, fontWeight: 700 }}>"What do you normally do?"</span>
                        </div>
                        <div style={{ width: '100%', height: 1, background: 'rgba(244,240,230,0.08)', margin: '2px 0' }} />
                        <span style={{ fontSize: 14, color: 'rgba(244,240,230,0.38)', fontStyle: 'italic' }}>
                            Both accepted — same meaning, different words
                        </span>
                    </div>
                </div>
            </div>
            <div style={{ width: 220, display: 'flex', flexDirection: 'column', gap: 12 }}>
                {[
                    { n: '1', label: 'Exact match', color: chalk.blue,  desc: 'Regex / pattern check — instant' },
                    { n: '2', label: 'Semantic',    color: chalk.green, desc: 'Embedding similarity score' },
                    { n: '3', label: 'AI analysis', color: chalk.pink,  desc: 'LLM judgment + explanation' },
                ].map((t) => (
                    <div key={t.n} style={{ ...s.card, display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                        <div style={{
                            width: 30, height: 30, borderRadius: 8,
                            background: `${t.color}22`, border: `1px solid ${t.color}44`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: 14, fontWeight: 900, color: t.color, flexShrink: 0,
                        }}>{t.n}</div>
                        <div>
                            <div style={{ fontSize: 15, fontWeight: 800, color: t.color, marginBottom: 3 }}>{t.label}</div>
                            <div style={{ fontSize: 13, color: 'rgba(244,240,230,0.42)' }}>{t.desc}</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function SlideFSRS() {
    const days = [1, 3, 7, 14, 30, 60, 120];
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px 10px', gap: 24, justifyContent: 'center' }}>
            <div>
                <div style={s.label}>Memory science</div>
                <h2 style={s.h2}>Nothing falls through <span style={s.accent(chalk.yellow)}>the cracks</span></h2>
                <p style={{ ...s.sub, marginTop: 12, fontSize: 18 }}>
                    FSRS — the Free Spaced Repetition Scheduler — calculates exactly when to review each word.
                </p>
            </div>
            <div style={{ ...s.card, display: 'flex', flexDirection: 'column', gap: 18 }}>
                <div style={{ fontSize: 13, fontWeight: 900, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(244,240,230,0.28)' }}>
                    example review schedule for one word
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, height: 70 }}>
                    {days.map((d, i) => {
                        const h = 18 + i * 7;
                        const color = i < 3 ? chalk.pink : i < 5 ? chalk.yellow : chalk.green;
                        return (
                            <div key={d} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flex: 1 }}>
                                <div style={{ width: '100%', height: h, borderRadius: 6, background: `${color}44`, border: `1px solid ${color}66` }} />
                                <span style={{ fontSize: 12, color: 'rgba(244,240,230,0.4)', fontWeight: 700 }}>
                                    {d < 30 ? `${d}d` : `${d/30}mo`}
                                </span>
                            </div>
                        );
                    })}
                </div>
                <div style={{ display: 'flex', gap: 20, fontSize: 13, color: 'rgba(244,240,230,0.4)' }}>
                    <span><span style={{ color: chalk.pink }}>■</span> frequent early reviews</span>
                    <span><span style={{ color: chalk.yellow }}>■</span> spacing increases</span>
                    <span><span style={{ color: chalk.green }}>■</span> long-term retention</span>
                </div>
            </div>
        </div>
    );
}

function SlideStart() {
    const steps = [
        { n: '1', label: 'Pinyin',     sub: 'Sounds & tones',      color: chalk.blue },
        { n: '2', label: 'Characters', sub: 'Structure & radicals', color: '#a78bfa' },
        { n: '3', label: 'Vocabulary', sub: 'Words in context',     color: chalk.yellow },
        { n: '4', label: 'Sentences',  sub: 'Grammar patterns',     color: chalk.green },
    ];
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px 10px', gap: 28, justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
            <div>
                <div style={s.label}>Your path</div>
                <h2 style={{ ...s.h2, fontSize: 48 }}>Ready to <span style={s.accent(chalk.green)}>start?</span></h2>
                <p style={{ ...s.sub, marginTop: 12, fontSize: 18 }}>
                    Begin with the foundation — everything else builds on top.
                </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%', justifyContent: 'center' }}>
                {steps.map((step, i) => (
                    <div key={step.n} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ ...s.card, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, padding: '18px 24px', minWidth: 120 }}>
                            <div style={{
                                width: 36, height: 36, borderRadius: '50%',
                                background: `${step.color}22`, border: `2px solid ${step.color}55`,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: 15, fontWeight: 900, color: step.color,
                            }}>{step.n}</div>
                            <div>
                                <div style={{ fontSize: 17, fontWeight: 900, color: step.color }}>{step.label}</div>
                                <div style={{ fontSize: 13, color: 'rgba(244,240,230,0.4)', marginTop: 3 }}>{step.sub}</div>
                            </div>
                        </div>
                        {i < steps.length - 1 && (
                            <span style={{ fontSize: 20, color: 'rgba(244,240,230,0.2)', fontWeight: 900 }}>→</span>
                        )}
                    </div>
                ))}
            </div>
            <p style={{ fontSize: 15, color: 'rgba(244,240,230,0.35)', fontStyle: 'italic' }}>
                Use the foundation modules in the classroom to get started.
            </p>
        </div>
    );
}

const SLIDE_COMPONENTS = {
    welcome: SlideWelcome,
    sounds:  SlideSound,
    skills:  SlideSkills,
    ai:      SlideAI,
    fsrs:    SlideFSRS,
    start:   SlideStart,
};

// ─────────────────────────────────────────────────────────────────────────────
// BOTTOM CONTROL BAR  (progress + subtitle + prev/play/next — one compact band)
// ─────────────────────────────────────────────────────────────────────────────

const NAV_BTN = {
    background: 'rgba(244,240,230,0.12)',
    border: '1px solid rgba(244,240,230,0.20)',
    borderRadius: 99,
    width: 30, height: 30,
    color: 'rgba(244,240,230,0.85)',
    fontSize: 16,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    flexShrink: 0,
    lineHeight: 1,
};

function BottomBar({ index, total, progress, playing, onPrev, onToggle, onNext, subtitle }) {
    return (
        <div style={{
            position: 'absolute', bottom: 0, left: 0, right: 0,
            zIndex: 10,
            background: 'linear-gradient(to top, rgba(0,0,0,0.78) 0%, rgba(0,0,0,0.60) 55%, transparent 100%)',
            paddingTop: 28,
        }}>
            {/* Progress strips */}
            <div style={{ display: 'flex', gap: 4, padding: '0 16px 8px' }}>
                {Array.from({ length: total }).map((_, i) => {
                    const fill = i < index ? 1 : i === index ? progress : 0;
                    return (
                        <div key={i} style={{ flex: 1, height: 2, borderRadius: 99, background: 'rgba(244,240,230,0.18)', overflow: 'hidden' }}>
                            <div style={{
                                height: '100%', width: `${fill * 100}%`,
                                background: 'rgba(244,240,230,0.80)', borderRadius: 99,
                                transition: fill === 1 || fill === 0 ? 'none' : 'width 0.25s linear',
                            }} />
                        </div>
                    );
                })}
            </div>

            {/* Single row: prev | subtitle text | play | next */}
            <div style={{
                display: 'flex', alignItems: 'center', gap: 10,
                padding: '4px 16px 14px',
            }}>
                {/* Prev */}
                <button onClick={onPrev} disabled={index === 0} style={{ ...NAV_BTN, cursor: index === 0 ? 'default' : 'pointer', opacity: index === 0 ? 0.28 : 1 }}>‹</button>

                {/* Subtitle */}
                <p style={{
                    flex: 1, margin: 0,
                    fontSize: 13, lineHeight: 1.55,
                    color: 'rgba(244,240,230,0.75)',
                    fontWeight: 400,
                    overflow: 'hidden',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                }}>
                    {subtitle}
                </p>

                {/* Play / Pause */}
                <button onClick={onToggle} style={{
                    ...NAV_BTN,
                    width: 36, height: 36, fontSize: 14,
                    background: 'rgba(244,240,230,0.20)',
                    border: '1px solid rgba(244,240,230,0.28)',
                    cursor: 'pointer',
                }}>
                    {playing ? '⏸' : '▶'}
                </button>

                {/* Next */}
                <button onClick={onNext} disabled={index === total - 1} style={{ ...NAV_BTN, cursor: index === total - 1 ? 'default' : 'pointer', opacity: index === total - 1 ? 0.28 : 1 }}>›</button>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export default function CourseIntroVideo() {
    const [index, setIndex] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [progress, setProgress] = useState(0);   // 0–1, driven by audio or fallback timer
    const audioRef = useRef(null);
    const timerRef = useRef(null);
    const elapsedRef = useRef(0);

    const currentSlide = SLIDES[index];
    const SlideContent = SLIDE_COMPONENTS[currentSlide.id];

    // ── Stop whatever is currently playing ──────────────────────────────────
    const stopAudio = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.onended = null;
            audioRef.current.ontimeupdate = null;
            audioRef.current = null;
        }
        clearInterval(timerRef.current);
    }, []);

    // ── Start pre-generated narration audio for current slide ───────────────
    const startAudio = useCallback((slide) => {
        stopAudio();
        elapsedRef.current = 0;
        setProgress(0);

        const url = audioUrl(slide.id);
        const audio = new Audio(url);
        audioRef.current = audio;

        // Drive progress from audio currentTime
        audio.ontimeupdate = () => {
            if (audio.duration && audio.duration > 0) {
                setProgress(audio.currentTime / audio.duration);
            }
        };

        // Auto-advance on end
        audio.onended = () => {
            setProgress(1);
            setTimeout(() => {
                setIndex((idx) => {
                    if (idx < SLIDES.length - 1) {
                        return idx + 1;
                    }
                    setPlaying(false);
                    return idx;
                });
            }, 600);
        };

        // Fallback timer if audio fails to load
        audio.onerror = () => {
            const duration = slide.duration;
            timerRef.current = setInterval(() => {
                elapsedRef.current += 200;
                setProgress(Math.min(elapsedRef.current / duration, 1));
                if (elapsedRef.current >= duration) {
                    clearInterval(timerRef.current);
                    setIndex((idx) => {
                        if (idx < SLIDES.length - 1) return idx + 1;
                        setPlaying(false);
                        return idx;
                    });
                }
            }, 200);
        };

        audio.play().catch(() => {});
    }, [stopAudio]);

    // ── Navigation ───────────────────────────────────────────────────────────
    const goTo = useCallback((i) => {
        const clamped = Math.max(0, Math.min(SLIDES.length - 1, i));
        stopAudio();
        setProgress(0);
        setIndex(clamped);
        // If currently playing, audio for new slide starts via the index effect below
    }, [stopAudio]);

    // ── Play / Pause toggle ──────────────────────────────────────────────────
    const toggle = useCallback(() => {
        setPlaying((prev) => {
            if (prev) {
                // Pause
                if (audioRef.current) audioRef.current.pause();
                clearInterval(timerRef.current);
            }
            return !prev;
        });
    }, []);

    // ── When playing becomes true or slide index changes while playing ───────
    useEffect(() => {
        if (playing) {
            startAudio(SLIDES[index]);
        } else {
            // Just paused — audio already paused in toggle, don't restart
        }
        return () => {
            // Cleanup handled by stopAudio in goTo / toggle
        };
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [playing, index]);

    // ── Unmount cleanup ──────────────────────────────────────────────────────
    useEffect(() => () => stopAudio(), [stopAudio]);

    return (
        <div style={{
            ...blackboard.shell,
            aspectRatio: '16/9',
            borderRadius: 20,
            boxShadow: 'inset 0 0 100px rgba(0,0,0,0.30), 0 0 0 4px #6B4820, 0 40px 100px rgba(0,0,0,0.50)',
            overflow: 'hidden',
            userSelect: 'none',
        }}>
            <ChalkTexture opacity={0.07} zIndex={0} />

            {/* Wooden frame vignette */}
            <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
                boxShadow: 'inset 0 0 0 18px #9C7040, inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

            {/* Slide content — paddingBottom just enough for the compact bar (~72px) */}
            <div style={{
                position: 'absolute', inset: 0,
                paddingTop: 18,
                paddingBottom: 72,
                display: 'flex', flexDirection: 'column',
                zIndex: 2,
            }}>
                <SlideContent key={currentSlide.id} />
            </div>

            <BottomBar
                index={index}
                total={SLIDES.length}
                progress={progress}
                playing={playing}
                onPrev={() => goTo(index - 1)}
                onToggle={toggle}
                onNext={() => goTo(index + 1)}
                subtitle={playing || progress > 0 ? currentSlide.narration : ''}
            />
        </div>
    );
}
