// ── Chalk / Blackboard palette ──────────────────────────────────────────────
export const chalk = {
    white:  '#F4F0E6',
    yellow: '#F5D76E',
    blue:   '#89CFEF',
    green:  '#7ECBA1',
    pink:   '#F4A7B9',
    dim:    'rgba(244,240,230,0.58)',
    faint:  'rgba(244,240,230,0.30)',
};

// Shared blackboard-style layout primitives used by all three templates
export const blackboard = {
    shell: {
        aspectRatio: '16/9',
        overflow: 'hidden',
        borderRadius: 18,
        border: '18px solid #9C7040',
        background: 'linear-gradient(150deg, #1F3B2D 0%, #243D31 55%, #192C24 100%)',
        boxShadow: 'inset 0 0 100px rgba(0,0,0,0.30), 0 0 0 4px #6B4820, 0 40px 100px rgba(0,0,0,0.50)',
        fontFamily: '"Inter","Segoe UI","Helvetica Neue",Arial,sans-serif',
        color: '#F4F0E6',
        position: 'relative',
        display: 'flex',
        flexDirection: 'column',
    },
    // Darker panel — for primary content areas
    panel: {
        borderRadius: 10,
        background: 'rgba(0,0,0,0.24)',
        border: '1px solid rgba(244,240,230,0.14)',
        padding: 28,
    },
    // Lighter panel — for secondary / sidebar content
    panelLight: {
        borderRadius: 10,
        background: 'rgba(255,255,255,0.06)',
        border: '1px solid rgba(244,240,230,0.09)',
        padding: 28,
    },
    header: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid rgba(244,240,230,0.10)',
        padding: '13px 34px',
    },
    labelRow: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 14,
        fontSize: 11,
        fontWeight: 900,
        letterSpacing: '0.22em',
        textTransform: 'uppercase',
        color: 'rgba(244,240,230,0.38)',
    },
};
// ────────────────────────────────────────────────────────────────────────────

export const formatSeconds = (value) => {
    const seconds = Math.max(0, Math.floor(Number(value) || 0));
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
};

export const buildTemplateAccent = (segmentType = '') => {
    switch (segmentType) {
        case 'line_walkthrough':
            return {
                pillBackground: '#dbeafe',
                pillText: '#1d4ed8',
                border: '#dbeafe',
                surface: 'linear-gradient(135deg, #ffffff 0%, #eff6ff 58%, #e2e8f0 100%)',
                focus: '#1d4ed8',
            };
        case 'vocabulary_focus':
            return {
                pillBackground: '#fef3c7',
                pillText: '#b45309',
                border: '#fde68a',
                surface: 'linear-gradient(135deg, #ffffff 0%, #fffbeb 55%, #fff7ed 100%)',
                focus: '#b45309',
            };
        case 'grammar_focus':
            return {
                pillBackground: '#d1fae5',
                pillText: '#047857',
                border: '#a7f3d0',
                surface: 'linear-gradient(135deg, #ffffff 0%, #ecfdf5 56%, #f0fdfa 100%)',
                focus: '#047857',
            };
        case 'recap':
            return {
                pillBackground: '#ede9fe',
                pillText: '#7c3aed',
                border: '#ddd6fe',
                surface: 'linear-gradient(135deg, #ffffff 0%, #f5f3ff 56%, #fdf4ff 100%)',
                focus: '#7c3aed',
            };
        default:
            return {
                pillBackground: '#f1f5f9',
                pillText: '#334155',
                border: '#e2e8f0',
                surface: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 56%, #e2e8f0 100%)',
                focus: '#334155',
            };
    }
};

export const fontStack = '"Georgia", "Cambria", "Times New Roman", serif';
export const sansStack = '"Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif';

export const panelShadow = '0 30px 90px rgba(15, 23, 42, 0.08)';
export const cardShadow = '0 12px 28px rgba(15, 23, 42, 0.08)';

export const styles = {
    shell(accent) {
        return {
            overflow: 'hidden',
            borderRadius: 40,
            border: `2px solid ${accent.border}`,
            background: accent.surface,
            boxShadow: panelShadow,
            fontFamily: sansStack,
            color: '#0f172a',
        };
    },
    header: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid rgba(255,255,255,0.72)',
        padding: '28px 38px',
    },
    headerLeft: {
        display: 'flex',
        alignItems: 'center',
        gap: 14,
    },
    pill(accent) {
        return {
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: 999,
            padding: '8px 16px',
            fontSize: 12,
            fontWeight: 900,
            letterSpacing: '0.24em',
            textTransform: 'uppercase',
            background: accent.pillBackground,
            color: accent.pillText,
        };
    },
    eyebrow: {
        fontSize: 12,
        fontWeight: 800,
        letterSpacing: '0.24em',
        textTransform: 'uppercase',
        color: '#94a3b8',
    },
    duration: {
        fontSize: 18,
        fontWeight: 700,
        color: '#94a3b8',
    },
    twoColumn(left = '1.2fr', right = '0.8fr') {
        return {
            display: 'grid',
            gridTemplateColumns: `${left} ${right}`,
            gap: 28,
            padding: 36,
            alignItems: 'stretch',
        };
    },
    whitePanel: {
        borderRadius: 32,
        background: 'rgba(255,255,255,0.88)',
        padding: 32,
        boxShadow: cardShadow,
    },
    darkPanel: {
        borderRadius: 32,
        background: '#0f172a',
        padding: 28,
        boxShadow: cardShadow,
        color: '#ffffff',
    },
    labelRow: {
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        marginBottom: 16,
        fontSize: 12,
        fontWeight: 900,
        letterSpacing: '0.22em',
        textTransform: 'uppercase',
        color: '#94a3b8',
    },
    stack: {
        display: 'flex',
        flexDirection: 'column',
        gap: 20,
    },
};
