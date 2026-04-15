import BlackboardShell from './BlackboardShell';
import ChalkTexture from './ChalkTexture';
import { chalk } from './templateUtils';

// Color cycle for grid items
const COLORS = [chalk.yellow, chalk.green, chalk.blue, chalk.pink];

/**
 * PinyinGridTemplate
 *
 * visual_blocks:
 *   [{
 *     block_type: 'pinyin_grid',
 *     content: {
 *       columns: 7,           // grid columns (default 5)
 *       items: [{ symbol, hint, color? }]
 *     }
 *   }]
 */
export default function PinyinGridTemplate({ segment }) {
    const narrationText = segment?.narration_track?.subtitle_en || '';
    const block   = (segment?.visual_blocks || []).find(b => b.block_type === 'pinyin_grid');
    const content = block?.content || {};
    const items   = content.items || [];
    const cols    = content.columns || 5;

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
                    {segment?.segment_title}
                </span>
                {content.subtitle && (
                    <span style={{
                        fontSize: 11, fontWeight: 900, letterSpacing: '0.20em',
                        textTransform: 'uppercase', color: 'rgba(244,240,230,0.28)',
                    }}>
                        {content.subtitle}
                    </span>
                )}
            </div>

            {/* Grid */}
            <div style={{
                flex: 1,
                display: 'grid',
                gridTemplateColumns: `repeat(${cols}, 1fr)`,
                gap: 14,
                padding: '18px 36px 22px',
                position: 'relative', zIndex: 2,
                alignContent: 'stretch',
            }}>
                {items.map((item, i) => {
                    const color = item.color || COLORS[i % COLORS.length];
                    return (
                        <div key={i} style={{
                            display: 'flex', flexDirection: 'column', alignItems: 'center',
                            justifyContent: 'center', gap: 8,
                            background: 'rgba(0,0,0,0.26)',
                            border: '1px solid rgba(244,240,230,0.07)',
                            borderTop: `2px solid ${color}55`,
                            borderRadius: 10,
                            padding: '14px 8px',
                        }}>
                            <span style={{
                                fontSize: item.large ? 72 : 52,
                                fontWeight: 900,
                                color,
                                lineHeight: 1,
                                letterSpacing: '-0.01em',
                                textShadow: `0 0 20px ${color}44`,
                            }}>
                                {item.symbol}
                            </span>
                            {item.hint && (
                                <span style={{
                                    fontSize: 13, fontWeight: 500,
                                    color: chalk.faint,
                                    textAlign: 'center', lineHeight: 1.3,
                                    letterSpacing: '0.01em',
                                }}>
                                    {item.hint}
                                </span>
                            )}
                        </div>
                    );
                })}
            </div>
        </BlackboardShell>
    );
}
