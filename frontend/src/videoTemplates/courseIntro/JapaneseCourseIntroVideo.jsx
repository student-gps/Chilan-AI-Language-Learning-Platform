import { useCallback, useMemo } from 'react';
import { buildJapaneseCourseIntroAudioUrl } from '../../utils/japaneseStaticAudio';
import { chalk } from '../explanation/templateUtils';
import NarratedCourseIntroDeck from './NarratedCourseIntroDeck';
import {
    JAPANESE_COURSE_INTRO_COPY,
    JAPANESE_COURSE_INTRO_SLIDES,
} from './japaneseCourseIntroContent';

const styles = {
    label: { fontSize: 11, fontWeight: 900, letterSpacing: '0.26em', textTransform: 'uppercase', color: 'rgba(244,240,230,0.35)', marginBottom: 16 },
    h1: { fontSize: 52, fontWeight: 900, color: chalk.white, lineHeight: 1.12, letterSpacing: '-0.01em', margin: 0 },
    h2: { fontSize: 40, fontWeight: 900, color: chalk.white, lineHeight: 1.2, margin: 0 },
    sub: { fontSize: 21, color: 'rgba(244,240,230,0.62)', lineHeight: 1.7, margin: 0, fontWeight: 400 },
    accent: (color = chalk.yellow) => ({ color, fontWeight: 900 }),
    pill: (color = chalk.yellow) => ({ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '7px 18px', borderRadius: 999, background: `${color}18`, border: `1px solid ${color}44`, fontSize: 13, fontWeight: 800, color, letterSpacing: '0.08em' }),
    card: { borderRadius: 14, background: 'rgba(0,0,0,0.28)', border: '1px solid rgba(244,240,230,0.12)', padding: '22px 28px' },
};

function SlideWelcome({ content, common }) {
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center', padding: '0 80px', gap: 24 }}>
            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none', zIndex: 0, overflow: 'hidden' }}>
                {['あ', 'ア', '日', '本', '語', '学'].map((char, index) => (
                    <span key={char} style={{ fontSize: 120 + (index % 3) * 30, fontWeight: 900, color: 'rgba(244,240,230,0.025)', position: 'absolute', left: `${[8, 22, 38, 55, 70, 85][index]}%`, top: `${[10, 55, 15, 60, 8, 45][index]}%`, transform: `rotate(${[-8, 5, -4, 7, -6, 3][index]}deg)`, userSelect: 'none' }}>{char}</span>
                ))}
            </div>
            <div style={{ position: 'relative', zIndex: 2, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 22 }}>
                <div style={styles.pill(chalk.pink)}>✦ &nbsp;{common.course}</div>
                <h1 style={{ ...styles.h1, fontSize: 60 }}>{content.title}<br /><span style={styles.accent(chalk.yellow)}>{content.accent}</span></h1>
                <p style={{ ...styles.sub, maxWidth: 560 }}>{content.subtitle}</p>
            </div>
        </div>
    );
}

function SlideSounds({ content }) {
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px', gap: 24, justifyContent: 'center' }}>
            <div>
                <div style={styles.label}>{content.label}</div>
                <h2 style={styles.h2}>{content.title}<span style={styles.accent(chalk.pink)}>{content.accent}</span></h2>
                <p style={{ ...styles.sub, marginTop: 12, fontSize: 18 }}>{content.subtitle}</p>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16 }}>
                {content.cards.map(([glyph, title, body, color]) => (
                    <div key={title} style={{ ...styles.card, textAlign: 'center', display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
                        <span style={{ fontSize: 50, fontWeight: 900, color, lineHeight: 1 }}>{glyph}</span>
                        <span style={{ fontSize: 18, fontWeight: 900, color }}>{title}</span>
                        <span style={{ fontSize: 13, lineHeight: 1.5, color: 'rgba(244,240,230,0.42)' }}>{body}</span>
                    </div>
                ))}
            </div>
            <p style={{ ...styles.sub, fontSize: 15, opacity: 0.6, textAlign: 'center', fontWeight: 700 }}>{content.example}</p>
        </div>
    );
}

function SlideSkills({ content }) {
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px', gap: 24, justifyContent: 'center' }}>
            <div>
                <div style={styles.label}>{content.label}</div>
                <h2 style={styles.h2}>{content.title}<span style={styles.accent(chalk.green)}>{content.accent}</span></h2>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 18 }}>
                {content.cards.map(([icon, title, body, color]) => (
                    <div key={title} style={{ ...styles.card, display: 'flex', flexDirection: 'column', gap: 12 }}>
                        <span style={{ fontSize: 38 }}>{icon}</span>
                        <div style={{ fontSize: 25, fontWeight: 900, color }}>{title}</div>
                        <p style={{ margin: 0, fontSize: 15, lineHeight: 1.6, color: 'rgba(244,240,230,0.52)' }}>{body}</p>
                    </div>
                ))}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, background: 'rgba(0,0,0,0.22)', borderRadius: 12, padding: '13px 22px', border: '1px solid rgba(244,240,230,0.08)' }}>
                <span style={{ fontSize: 20 }}>⌨️</span><p style={{ margin: 0, fontSize: 15, color: 'rgba(244,240,230,0.42)', fontStyle: 'italic' }}>{content.note}</p>
            </div>
        </div>
    );
}

function SlideAI({ content }) {
    return (
        <div style={{ flex: 1, display: 'flex', padding: '10px 52px', gap: 36, alignItems: 'center' }}>
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 18 }}>
                <div>
                    <div style={styles.label}>{content.label}</div>
                    <h2 style={{ ...styles.h2, fontSize: 34 }}>{content.title}<br /><span style={styles.accent(chalk.pink)}>{content.accent}</span></h2>
                    <p style={{ ...styles.sub, marginTop: 10, fontSize: 16 }}>{content.subtitle}</p>
                </div>
                <div style={{ ...styles.card, display: 'flex', flexDirection: 'column', gap: 8 }}>
                    <div style={{ fontSize: 11, fontWeight: 900, letterSpacing: '0.16em', textTransform: 'uppercase', color: 'rgba(244,240,230,0.28)' }}>{content.exampleLabel}</div>
                    {content.answers.map((answer) => <div key={answer} style={{ display: 'flex', alignItems: 'center', gap: 9, fontSize: 15, color: chalk.green, fontWeight: 700 }}><span>✓</span>{answer}</div>)}
                    <span style={{ borderTop: '1px solid rgba(244,240,230,0.08)', paddingTop: 7, fontSize: 12, color: 'rgba(244,240,230,0.36)', fontStyle: 'italic' }}>{content.exampleNote}</span>
                </div>
            </div>
            <div style={{ width: 235, display: 'flex', flexDirection: 'column', gap: 12 }}>
                {content.tiers.map(([number, title, body, color]) => (
                    <div key={number} style={{ ...styles.card, display: 'flex', gap: 13, alignItems: 'flex-start', padding: '18px 20px' }}>
                        <div style={{ width: 30, height: 30, borderRadius: 8, background: `${color}22`, border: `1px solid ${color}44`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 900, color, flexShrink: 0 }}>{number}</div>
                        <div><div style={{ fontSize: 15, fontWeight: 800, color, marginBottom: 3 }}>{title}</div><div style={{ fontSize: 12, lineHeight: 1.4, color: 'rgba(244,240,230,0.42)' }}>{body}</div></div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function SlideFSRS({ content, common }) {
    const days = [1, 3, 7, 14, 30, 60, 120];
    const colors = [chalk.pink, chalk.yellow, chalk.green];
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 52px', gap: 24, justifyContent: 'center' }}>
            <div>
                <div style={styles.label}>{content.label}</div>
                <h2 style={styles.h2}>{content.title}<span style={styles.accent(chalk.yellow)}>{content.accent}</span></h2>
                <p style={{ ...styles.sub, marginTop: 12, fontSize: 18 }}>{content.subtitle}</p>
            </div>
            <div style={{ ...styles.card, display: 'flex', flexDirection: 'column', gap: 18 }}>
                <div style={{ fontSize: 12, fontWeight: 900, letterSpacing: '0.2em', textTransform: 'uppercase', color: 'rgba(244,240,230,0.28)' }}>{content.chartLabel}</div>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: 10, height: 70 }}>
                    {days.map((day, index) => {
                        const color = index < 3 ? chalk.pink : index < 5 ? chalk.yellow : chalk.green;
                        return <div key={day} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6, flex: 1 }}><div style={{ width: '100%', height: 18 + index * 7, borderRadius: 6, background: `${color}44`, border: `1px solid ${color}66` }} /><span style={{ fontSize: 12, color: 'rgba(244,240,230,0.4)', fontWeight: 700 }}>{day < 30 ? `${day}${common.day}` : `${day / 30}${common.month}`}</span></div>;
                    })}
                </div>
                <div style={{ display: 'flex', gap: 20, fontSize: 12, color: 'rgba(244,240,230,0.4)' }}>{content.legends.map((legend, index) => <span key={legend}><span style={{ color: colors[index] }}>■</span> {legend}</span>)}</div>
            </div>
        </div>
    );
}

function SlideStart({ content }) {
    return (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '10px 48px', gap: 28, justifyContent: 'center', alignItems: 'center', textAlign: 'center' }}>
            <div>
                <div style={styles.label}>{content.label}</div>
                <h2 style={{ ...styles.h2, fontSize: 46 }}>{content.title}<span style={styles.accent(chalk.green)}>{content.accent}</span></h2>
                <p style={{ ...styles.sub, marginTop: 12, fontSize: 17 }}>{content.subtitle}</p>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 9, width: '100%', justifyContent: 'center' }}>
                {content.steps.map(([title, body, color], index) => (
                    <div key={title} style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
                        <div style={{ ...styles.card, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 9, padding: '16px 18px', minWidth: 114 }}>
                            <div style={{ width: 34, height: 34, borderRadius: '50%', background: `${color}22`, border: `2px solid ${color}55`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 900, color }}>{index + 1}</div>
                            <div><div style={{ fontSize: 16, fontWeight: 900, color }}>{title}</div><div style={{ fontSize: 12, color: 'rgba(244,240,230,0.4)', marginTop: 3 }}>{body}</div></div>
                        </div>
                        {index < content.steps.length - 1 && <span style={{ fontSize: 18, color: 'rgba(244,240,230,0.2)', fontWeight: 900 }}>→</span>}
                    </div>
                ))}
            </div>
            <p style={{ fontSize: 14, color: 'rgba(244,240,230,0.35)', fontStyle: 'italic' }}>{content.note}</p>
        </div>
    );
}

const SLIDE_COMPONENTS = { welcome: SlideWelcome, sounds: SlideSounds, skills: SlideSkills, ai: SlideAI, fsrs: SlideFSRS, start: SlideStart };

export default function JapaneseCourseIntroVideo({ supportLanguage = 'zh' }) {
    const language = supportLanguage === 'zh' ? 'zh' : 'en';
    const content = JAPANESE_COURSE_INTRO_COPY[language];
    const getNarrationText = useCallback((slideId) => content[slideId]?.narration || '', [content]);
    const getAudioUrls = useCallback((slide) => [buildJapaneseCourseIntroAudioUrl(language, slide.id)], [language]);
    const renderSlide = useCallback((slide) => {
        const SlideComponent = SLIDE_COMPONENTS[slide.id];
        return <SlideComponent key={slide.id} content={content[slide.id]} common={content.common} />;
    }, [content]);
    const ariaLabel = useMemo(() => language === 'zh' ? '日语课程介绍幻灯片' : 'Japanese course introduction slides', [language]);

    return (
        <NarratedCourseIntroDeck
            slides={JAPANESE_COURSE_INTRO_SLIDES}
            renderSlide={renderSlide}
            getNarrationText={getNarrationText}
            getAudioUrls={getAudioUrls}
            ariaLabel={ariaLabel}
        />
    );
}
