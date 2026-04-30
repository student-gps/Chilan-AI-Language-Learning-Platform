import { useState, useEffect, useCallback, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { chalk, blackboard } from '../explanation/templateUtils';
import ChalkTexture from '../explanation/ChalkTexture';

// Static narration audio — pre-generated with CosyVoice TTS (EN) or Azure TTS (FR/others).
// Run:  cd backend && python generate_intro_narration.py
//       cd backend && python generate_intro_narration.py --lang fr
//       cd backend && python upload_intro_audio_to_r2.py
// Dev:  served from frontend/public/audio/intro/ via backend /media/intro/
// Prod: backend /media/intro/ redirects to R2 zh/audio/intro/
const _API = import.meta.env.VITE_APP_API_BASE_URL || '';

const SLIDES = [
    { id: 'welcome', duration: 14000 },
    { id: 'sounds',  duration: 14000 },
    { id: 'skills',  duration: 14000 },
    { id: 'ai',      duration: 16000 },
    { id: 'fsrs',    duration: 14000 },
    { id: 'start',   duration: 13000 },
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
    const { t } = useTranslation();
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
                    {t('civ_welcome_h1')}<br />
                    <span style={s.accent(chalk.yellow)}>{t('civ_welcome_accent')}</span>
                </h1>
                <p style={{ ...s.sub, maxWidth: 520 }}>
                    {t('civ_welcome_sub')}
                </p>
            </div>
        </div>
    );
}

function SlideSound() {
    const { t } = useTranslation();
    const tones = [
        { mark: 'ā', color: chalk.blue },
        { mark: 'á', color: chalk.green },
        { mark: 'ǎ', color: chalk.yellow },
        { mark: 'à', color: chalk.pink },
    ];
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px 10px', gap: 24, justifyContent: 'center' }}>
            <div>
                <div style={s.label}>{t('civ_sounds_label')}</div>
                <h2 style={s.h2}>
                    {t('civ_sounds_h2_pre')}<span style={s.accent(chalk.blue)}>{t('civ_sounds_h2_accent')}</span>
                </h2>
                <p style={{ ...s.sub, marginTop: 12, fontSize: 18 }}>
                    {t('civ_sounds_sub')}
                </p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 16 }}>
                {tones.map((tone, i) => (
                    <div key={i} style={{ ...s.card, textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 10, alignItems: 'center' }}>
                        <span style={{ fontSize: 52, fontWeight: 900, color: tone.color, lineHeight: 1, fontFamily: 'system-ui, -apple-system, sans-serif' }}>{tone.mark}</span>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                            <span style={{ fontSize: 16, fontWeight: 900, color: 'rgba(244,240,230,0.5)' }}>{t(`civ_sounds_tone${i}_label`)}</span>
                            <span style={{ fontSize: 14, color: 'rgba(244,240,230,0.4)', fontStyle: 'italic' }}>{t(`civ_sounds_tone${i}_name`)}</span>
                        </div>
                    </div>
                ))}
            </div>
            <p style={{ ...s.sub, fontSize: 16, opacity: 0.5, textAlign: 'center' }}>
                {t('civ_sounds_example')}
            </p>
        </div>
    );
}

function SlideSkills() {
    const { t } = useTranslation();
    const skills = [
        { icon: '👂', color: chalk.green },
        { icon: '🎤', color: chalk.blue },
        { icon: '⌨️', color: chalk.yellow },
    ];
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px 10px', gap: 24, justifyContent: 'center' }}>
            <div>
                <div style={s.label}>{t('civ_skills_label')}</div>
                <h2 style={s.h2}>{t('civ_skills_h2_pre')}<span style={s.accent(chalk.green)}>{t('civ_skills_h2_accent')}</span></h2>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 18 }}>
                {skills.map((sk, i) => (
                    <div key={i} style={{ ...s.card, display: 'flex', flexDirection: 'column', gap: 14 }}>
                        <span style={{ fontSize: 38 }}>{sk.icon}</span>
                        <div>
                            <div style={{ fontSize: 26, fontWeight: 900, color: sk.color, marginBottom: 8 }}>{t(`civ_skills_sk${i}_label`)}</div>
                            <p style={{ margin: 0, fontSize: 17, lineHeight: 1.7, color: 'rgba(244,240,230,0.55)' }}>{t(`civ_skills_sk${i}_sub`)}</p>
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
                    {t('civ_skills_no_hw')}
                </p>
            </div>
        </div>
    );
}

function SlideAI() {
    const { t } = useTranslation();
    const tiers = [
        { n: '1', color: chalk.blue },
        { n: '2', color: chalk.green },
        { n: '3', color: chalk.pink },
    ];
    return (
        <div style={{ flex: 1, display: 'flex', padding: '10px 52px 10px', gap: 36, alignItems: 'center' }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
                <div>
                    <div style={s.label}>{t('civ_ai_label')}</div>
                    <h2 style={{ ...s.h2, fontSize: 34 }}>
                        {t('civ_ai_h2_pre')}<br /><span style={s.accent(chalk.pink)}>{t('civ_ai_h2_accent')}</span>
                    </h2>
                    <p style={{ ...s.sub, marginTop: 12, fontSize: 17 }}>
                        {t('civ_ai_sub')}
                    </p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    <div style={{ fontSize: 12, fontWeight: 900, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(244,240,230,0.28)' }}>{t('civ_ai_example_label')}</div>
                    <div style={{ ...s.card, display: 'flex', flexDirection: 'column', gap: 10 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span style={{ fontSize: 18 }}>✅</span>
                            <span style={{ fontSize: 17, color: chalk.green, fontWeight: 700 }}>{t('civ_ai_example_ans1')}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                            <span style={{ fontSize: 18 }}>✅</span>
                            <span style={{ fontSize: 17, color: chalk.green, fontWeight: 700 }}>{t('civ_ai_example_ans2')}</span>
                        </div>
                        <div style={{ width: '100%', height: 1, background: 'rgba(244,240,230,0.08)', margin: '2px 0' }} />
                        <span style={{ fontSize: 14, color: 'rgba(244,240,230,0.38)', fontStyle: 'italic' }}>
                            {t('civ_ai_example_note')}
                        </span>
                    </div>
                </div>
            </div>
            <div style={{ width: 220, display: 'flex', flexDirection: 'column', gap: 12 }}>
                {tiers.map((tier, i) => (
                    <div key={tier.n} style={{ ...s.card, display: 'flex', gap: 14, alignItems: 'flex-start' }}>
                        <div style={{
                            width: 30, height: 30, borderRadius: 8,
                            background: `${tier.color}22`, border: `1px solid ${tier.color}44`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: 14, fontWeight: 900, color: tier.color, flexShrink: 0,
                        }}>{tier.n}</div>
                        <div>
                            <div style={{ fontSize: 15, fontWeight: 800, color: tier.color, marginBottom: 3 }}>{t(`civ_ai_tier${i}_label`)}</div>
                            <div style={{ fontSize: 13, color: 'rgba(244,240,230,0.42)' }}>{t(`civ_ai_tier${i}_desc`)}</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function SlideFSRS() {
    const { t } = useTranslation();
    const days = [1, 3, 7, 14, 30, 60, 120];
    const legendColors = [chalk.pink, chalk.yellow, chalk.green];
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px 10px', gap: 24, justifyContent: 'center' }}>
            <div>
                <div style={s.label}>{t('civ_fsrs_label')}</div>
                <h2 style={s.h2}>{t('civ_fsrs_h2_pre')}<span style={s.accent(chalk.yellow)}>{t('civ_fsrs_h2_accent')}</span></h2>
                <p style={{ ...s.sub, marginTop: 12, fontSize: 18 }}>
                    {t('civ_fsrs_sub')}
                </p>
            </div>
            <div style={{ ...s.card, display: 'flex', flexDirection: 'column', gap: 18 }}>
                <div style={{ fontSize: 13, fontWeight: 900, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(244,240,230,0.28)' }}>
                    {t('civ_fsrs_chart_label')}
                </div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, height: 70 }}>
                    {days.map((d, i) => {
                        const h = 18 + i * 7;
                        const color = i < 3 ? chalk.pink : i < 5 ? chalk.yellow : chalk.green;
                        return (
                            <div key={d} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flex: 1 }}>
                                <div style={{ width: '100%', height: h, borderRadius: 6, background: `${color}44`, border: `1px solid ${color}66` }} />
                                <span style={{ fontSize: 12, color: 'rgba(244,240,230,0.4)', fontWeight: 700 }}>
                                    {d < 30 ? `${d}d` : `${d / 30}mo`}
                                </span>
                            </div>
                        );
                    })}
                </div>
                <div style={{ display: 'flex', gap: 20, fontSize: 13, color: 'rgba(244,240,230,0.4)' }}>
                    {legendColors.map((color, i) => (
                        <span key={i}><span style={{ color }}>■</span> {t(`civ_fsrs_leg${i}`)}</span>
                    ))}
                </div>
            </div>
        </div>
    );
}

function SlideStart() {
    const { t } = useTranslation();
    const stepColors = [chalk.blue, '#a78bfa', chalk.yellow, chalk.green];
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px 10px', gap: 28, justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
            <div>
                <div style={s.label}>{t('civ_start_label')}</div>
                <h2 style={{ ...s.h2, fontSize: 48 }}>{t('civ_start_h2_pre')}<span style={s.accent(chalk.green)}>{t('civ_start_h2_accent')}</span></h2>
                <p style={{ ...s.sub, marginTop: 12, fontSize: 18 }}>
                    {t('civ_start_sub')}
                </p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, width: '100%', justifyContent: 'center' }}>
                {stepColors.map((color, i) => (
                    <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div style={{ ...s.card, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, padding: '18px 24px', minWidth: 120 }}>
                            <div style={{
                                width: 36, height: 36, borderRadius: '50%',
                                background: `${color}22`, border: `2px solid ${color}55`,
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: 15, fontWeight: 900, color,
                            }}>{i + 1}</div>
                            <div>
                                <div style={{ fontSize: 17, fontWeight: 900, color }}>{t(`civ_start_step${i}_label`)}</div>
                                <div style={{ fontSize: 13, color: 'rgba(244,240,230,0.4)', marginTop: 3 }}>{t(`civ_start_step${i}_sub`)}</div>
                            </div>
                        </div>
                        {i < stepColors.length - 1 && (
                            <span style={{ fontSize: 20, color: 'rgba(244,240,230,0.2)', fontWeight: 900 }}>→</span>
                        )}
                    </div>
                ))}
            </div>
            <p style={{ fontSize: 15, color: 'rgba(244,240,230,0.35)', fontStyle: 'italic' }}>
                {t('civ_start_note')}
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
// BOTTOM CONTROL BAR
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

            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '4px 16px 14px' }}>
                <button onClick={onPrev} disabled={index === 0} style={{ ...NAV_BTN, cursor: index === 0 ? 'default' : 'pointer', opacity: index === 0 ? 0.28 : 1 }}>‹</button>

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

                <button onClick={onToggle} style={{
                    ...NAV_BTN,
                    width: 36, height: 36, fontSize: 14,
                    background: 'rgba(244,240,230,0.20)',
                    border: '1px solid rgba(244,240,230,0.28)',
                    cursor: 'pointer',
                }}>
                    {playing ? '⏸' : '▶'}
                </button>

                <button onClick={onNext} disabled={index === total - 1} style={{ ...NAV_BTN, cursor: index === total - 1 ? 'default' : 'pointer', opacity: index === total - 1 ? 0.28 : 1 }}>›</button>
            </div>
        </div>
    );
}

// ─────────────────────────────────────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export default function CourseIntroVideo() {
    const { t, i18n } = useTranslation();
    const [index, setIndex] = useState(0);
    const [playing, setPlaying] = useState(false);
    const [progress, setProgress] = useState(0);
    const audioRef = useRef(null);
    const timerRef = useRef(null);
    const elapsedRef = useRef(0);

    const lang = (i18n.language || 'en').split('-')[0];

    const currentSlide = SLIDES[index];
    const SlideContent = SLIDE_COMPONENTS[currentSlide.id];

    // ── Stop whatever is currently playing ──────────────────────────────────
    const stopAudio = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.onended = null;
            audioRef.current.ontimeupdate = null;
            audioRef.current.onerror = null;
            audioRef.current = null;
        }
        clearInterval(timerRef.current);
    }, []);

    // ── Start narration audio with lang-specific → EN → timer fallback chain ─
    const startAudio = useCallback((slide) => {
        stopAudio();
        elapsedRef.current = 0;
        setProgress(0);

        const urls = lang !== 'en'
            ? [`${_API}/media/intro/slide_${slide.id}_${lang}.mp3`, `${_API}/media/intro/slide_${slide.id}.mp3`]
            : [`${_API}/media/intro/slide_${slide.id}.mp3`];

        let urlIdx = 0;

        const tryNext = () => {
            if (urlIdx >= urls.length) {
                // All audio URLs failed — fall back to timer
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
                return;
            }

            const url = urls[urlIdx++];
            const audio = new Audio(url);
            audioRef.current = audio;

            audio.ontimeupdate = () => {
                if (audio.duration && audio.duration > 0) {
                    setProgress(audio.currentTime / audio.duration);
                }
            };

            audio.onended = () => {
                setProgress(1);
                setTimeout(() => {
                    setIndex((idx) => {
                        if (idx < SLIDES.length - 1) return idx + 1;
                        setPlaying(false);
                        return idx;
                    });
                }, 600);
            };

            audio.onerror = () => tryNext();

            audio.play().catch(() => {});
        };

        tryNext();
    }, [stopAudio, lang]);

    // ── Navigation ───────────────────────────────────────────────────────────
    const goTo = useCallback((i) => {
        const clamped = Math.max(0, Math.min(SLIDES.length - 1, i));
        stopAudio();
        setProgress(0);
        setIndex(clamped);
    }, [stopAudio]);

    // ── Play / Pause toggle ──────────────────────────────────────────────────
    const toggle = useCallback(() => {
        setPlaying((prev) => {
            if (prev) {
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
        }
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

            <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
                boxShadow: 'inset 0 0 0 18px #9C7040, inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

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
                subtitle={playing || progress > 0 ? t(`civ_narration_${currentSlide.id}`) : ''}
            />
        </div>
    );
}
