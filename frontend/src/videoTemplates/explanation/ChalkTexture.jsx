import React from 'react';

/**
 * Renders an SVG feTurbulence noise layer that simulates chalk-dust / streak
 * texture on a blackboard.  Place it as a direct child of the shell container
 * (which must have position:relative / overflow:hidden).
 *
 * @param {number} opacity  0–1, default 0.09
 * @param {number} zIndex   stacking order inside the shell, default 1
 */
export default function ChalkTexture({ opacity = 0.09, zIndex = 1 }) {
    return (
        <svg
            style={{
                position: 'absolute',
                inset: 0,
                width: '100%',
                height: '100%',
                pointerEvents: 'none',
                zIndex,
            }}
        >
            <defs>
                <filter id="chalk-grain" x="0%" y="0%" width="100%" height="100%">
                    {/* fractalNoise gives that uneven chalk-smear look */}
                    <feTurbulence
                        type="fractalNoise"
                        baseFrequency="0.68 0.78"
                        numOctaves="4"
                        seed="7"
                        stitchTiles="stitch"
                    />
                    {/* Tint toward warm chalk-white */}
                    <feColorMatrix
                        type="matrix"
                        values="0 0 0 0 0.95  0 0 0 0 0.93  0 0 0 0 0.88  0 0 0 1 0"
                    />
                </filter>
            </defs>
            <rect width="100%" height="100%" filter="url(#chalk-grain)" opacity={opacity} />
        </svg>
    );
}
