import SubtitleBar from './SubtitleBar';

/**
 * Shared blackboard outer shell used by all explanation templates.
 *
 * Layout layers (bottom → top):
 *  1. Green blackboard background div (fills full area, flex column)
 *     - paddingTop: 18   → keeps content below the top wooden border
 *     - paddingBottom: 46 → reserves space equal to the subtitle bar height
 *  2. Wooden frame overlay (z-index 6) — solid border drawn on top of content;
 *     the bottom portion is visually covered by the subtitle bar below it.
 *  3. Subtitle bar (z-index 10, position: absolute bottom 0) — overlaps the
 *     bottom 18 px of the wooden border, reclaiming that vertical space for
 *     main content and giving the subtitle a clean floating appearance.
 */
export default function BlackboardShell({ children, subtitleText }) {
    return (
        <div style={{
            aspectRatio: '16/9',
            position: 'relative',
            overflow: 'hidden',
            borderRadius: 18,
            boxShadow: 'inset 0 0 100px rgba(0,0,0,0.30), 0 0 0 4px #6B4820, 0 40px 100px rgba(0,0,0,0.50)',
            fontFamily: '"Inter","Segoe UI","Helvetica Neue",Arial,sans-serif',
            color: '#F4F0E6',
        }}>
            {/* ── Green blackboard background + content ── */}
            <div style={{
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(150deg, #1F3B2D 0%, #243D31 55%, #192C24 100%)',
                display: 'flex',
                flexDirection: 'column',
                paddingTop: 18,   // same as wooden border width — keeps content below the top frame
                paddingBottom: 76, // matches subtitle bar height (minHeight 74 + borders) — reserves
                                   // space so body content doesn't slide behind the floating subtitle bar
            }}>
                {children}
            </div>

            {/* ── Wooden frame overlay ── */}
            <div style={{
                position: 'absolute',
                inset: 0,
                border: '18px solid #9C7040',
                borderRadius: 18,
                pointerEvents: 'none',
                zIndex: 6,
            }} />

            {/* ── Subtitle bar — floats above bottom wooden border ── */}
            <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                zIndex: 10,
            }}>
                <SubtitleBar text={subtitleText} />
            </div>
        </div>
    );
}
