import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { chalk } from '../explanation/templateUtils';
import NarratedCourseIntroDeck from './NarratedCourseIntroDeck';

// Static narration audio — pre-generated with CosyVoice TTS (EN) or Azure TTS (FR/others).
// Run:  cd backend && python generate_intro_narration.py
//       cd backend && python generate_intro_narration.py --lang all
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

export default function CourseIntroVideo() {
    const { t, i18n } = useTranslation();
    const lang = (i18n.language || 'en').split('-')[0];
    const getNarrationText = useCallback((slideId) => {
        const key = `civ_narration_${slideId}`;
        const localized = t(key);
        if (typeof localized === 'string' && localized.trim() && localized !== key) return localized;
        const fallback = t(key, { lng: 'en' });
        return typeof fallback === 'string' && fallback !== key ? fallback : '';
    }, [t]);
    const getAudioUrls = useCallback((slide) => (
        lang !== 'en'
            ? [`${_API}/media/intro/slide_${slide.id}_${lang}.mp3`, `${_API}/media/intro/slide_${slide.id}.mp3`]
            : [`${_API}/media/intro/slide_${slide.id}.mp3`]
    ), [lang]);
    const renderSlide = useCallback((slide) => {
        const SlideContent = SLIDE_COMPONENTS[slide.id];
        return <SlideContent key={slide.id} />;
    }, []);

    return (
        <NarratedCourseIntroDeck
            slides={SLIDES}
            renderSlide={renderSlide}
            getNarrationText={getNarrationText}
            getAudioUrls={getAudioUrls}
            ariaLabel="Chinese course introduction"
        />
    );
}
