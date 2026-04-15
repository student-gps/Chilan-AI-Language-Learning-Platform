import BlackboardShell from './BlackboardShell';
import ChalkTexture from './ChalkTexture';
import { chalk } from './templateUtils';

const TONE_DATA = [
    { num: '1st tone', mark: 'ā', char: '妈',  meaning: 'flat & high',  color: chalk.yellow },
    { num: '2nd tone', mark: 'á', char: '麻',  meaning: 'rising',       color: chalk.green  },
    { num: '3rd tone', mark: 'ǎ', char: '马',  meaning: 'dip & rise',   color: chalk.blue   },
    { num: '4th tone', mark: 'à', char: '骂',  meaning: 'falling',      color: chalk.pink   },
    { num: 'neutral',  mark: '·', char: '吗',  meaning: 'light & short', color: chalk.dim   },
];

export default function PinyinTonesTemplate({ segment }) {
    const narrationText = segment?.narration_track?.subtitle_en || '';

    return (
        <BlackboardShell subtitleText={narrationText}>
            <ChalkTexture opacity={0.09} zIndex={0} />
            <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
                boxShadow: 'inset 0 0 0 2px rgba(68,42,24,0.35), inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

            {/* Header */}
            <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                borderBottom: '1px solid rgba(244,240,230,0.10)',
                padding: '14px 40px',
                position: 'relative', zIndex: 2,
            }}>
                <span style={{ fontSize: 28, fontWeight: 800, letterSpacing: '0.04em', color: chalk.dim }}>
                    {segment?.segment_title || 'The Four Tones'}
                </span>
                <span style={{
                    fontSize: 11, fontWeight: 900, letterSpacing: '0.22em',
                    textTransform: 'uppercase', color: 'rgba(244,240,230,0.28)',
                }}>
                    tone changes meaning — same letters, four different words
                </span>
            </div>

            {/* Five tone cards — fill remaining space */}
            <div style={{
                flex: 1,
                display: 'grid',
                gridTemplateColumns: 'repeat(5, 1fr)',
                gap: 20,
                padding: '20px 36px 24px',
                position: 'relative', zIndex: 2,
            }}>
                {TONE_DATA.map(({ num, mark, char, meaning, color }) => (
                    <div key={num} style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center',
                        justifyContent: 'center', gap: 10,
                        background: 'rgba(0,0,0,0.28)',
                        border: '1px solid rgba(244,240,230,0.08)',
                        borderTop: `3px solid ${color}`,
                        borderRadius: 14,
                        padding: '28px 16px',
                    }}>
                        {/* Tone number */}
                        <span style={{
                            fontSize: 12, fontWeight: 900, letterSpacing: '0.20em',
                            textTransform: 'uppercase', color, opacity: 0.65,
                        }}>
                            {num}
                        </span>

                        {/* Tone diacritic mark */}
                        <span style={{
                            fontSize: 96, lineHeight: 1, fontWeight: 400,
                            color, fontFamily: 'Georgia, serif',
                            textShadow: `0 0 40px ${color}55`,
                        }}>
                            {mark}
                        </span>

                        {/* Divider */}
                        <div style={{ width: 40, height: 1, background: `${color}44` }} />

                        {/* Chinese character */}
                        <span style={{
                            fontSize: 110, lineHeight: 1, fontWeight: 900,
                            color: chalk.white,
                            textShadow: '0 0 4px rgba(255,255,255,0.15), 1px 1px 0 rgba(9,20,16,0.40)',
                        }}>
                            {char}
                        </span>

                        {/* English meaning */}
                        <span style={{
                            fontSize: 18, fontWeight: 600, color: chalk.dim,
                            letterSpacing: '0.03em', textAlign: 'center', lineHeight: 1.3,
                        }}>
                            {meaning}
                        </span>
                    </div>
                ))}
            </div>
        </BlackboardShell>
    );
}
