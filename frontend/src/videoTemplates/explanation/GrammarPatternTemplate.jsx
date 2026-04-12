import React from 'react';
import { blackboard, chalk, fontStack } from './templateUtils';
import ChalkTexture from './ChalkTexture';
import { PatternFormula, extractPinyinSyllables } from './chalkUtils';
import BlackboardShell from './BlackboardShell';

// Strip any trailing (…) group from pattern text — greedy outer so it always
// matches the LAST parenthesised group, avoiding false matches on mid-string parens.
function parsePatternText(raw) {
    if (!raw) return { chinese: '', pinyin: '' };
    const m = raw.match(/^(.+)\s*\(([^)]+)\)\s*$/);
    if (m) return { chinese: m[1].trim(), pinyin: m[2].trim() };
    return { chinese: raw, pinyin: '' };
}

// Split on "/" but only outside [...] and (...) brackets
function splitSlashOutsideBrackets(text) {
    const parts = [];
    let depth = 0;
    let current = '';
    for (const ch of text) {
        if (ch === '[' || ch === '(') { depth++; current += ch; }
        else if (ch === ']' || ch === ')') { depth = Math.max(0, depth - 1); current += ch; }
        else if (ch === '/' && depth === 0) {
            const part = current.trim();
            if (part) parts.push(part);
            current = '';
        } else {
            current += ch;
        }
    }
    const last = current.trim();
    if (last) parts.push(last);
    return parts;
}

// Split patterns onto separate lines.
// Returns: [{ icon, text, color }]
//   icon: '?' for question, '›' for answer, null for single line
// Supports: "Q: ... A: ..." and "/" separator (bracket-aware)
// Also handles legacy "A: ... / B: ..." labels (strips them) and lone "Q: ..." prefix.
function splitQA(text) {
    if (!text) return [{ icon: null, text: '', color: chalk.green }];
    // Q: ... A: ... format (s flag so \n between Q/A is fine)
    const qaMatch = text.match(/^Q[:：]\s*(.+?)\s+A[:：]\s*(.+)$/is);
    if (qaMatch) {
        const qPart = qaMatch[1].trim();
        // Also split the A part on "/" so "我是。/我不是。" becomes two › lines
        const aParts = splitSlashOutsideBrackets(qaMatch[2].trim());
        return [
            { icon: '?', text: qPart, color: chalk.blue },
            ...aParts.map((p) => ({ icon: '›', text: p, color: chalk.green })),
        ];
    }
    // Lone Q: without A: → render as a single question line (strip the Q: prefix)
    const loneQMatch = text.match(/^Q[:：]\s*(.+)/i);
    if (loneQMatch) {
        return [{ icon: '?', text: loneQMatch[1].trim(), color: chalk.blue }];
    }
    // "/" separator — skip slashes inside [...]
    // Only split if BOTH sides look like complete patterns (not bare alternative words).
    // A "complete pattern" has length > 4 chars or contains a "+" or Chinese + Latin mix.
    const slashParts = splitSlashOutsideBrackets(text);
    const looksComplete = (s) => s.trim().length > 4 || s.includes('+') || (s.includes('[') && s.includes(']'));
    if (slashParts.length > 1 && slashParts.every(looksComplete)) {
        // Strip letter labels like "A:", "B:" if every part has one (legacy format)
        const hasLabels = slashParts.every((p) => /^[A-Z][：:]/.test(p.trim()));
        const parts = hasLabels
            ? slashParts.map((p) => p.trim().replace(/^[A-Z][：:]\s*/i, ''))
            : slashParts;
        return [
            { icon: '?', text: parts[0], color: chalk.blue },
            ...parts.slice(1).map((p) => ({ icon: '›', text: p, color: chalk.green })),
        ];
    }
    return [{ icon: null, text, color: chalk.green }];
}


export default function GrammarPatternTemplate({ segment }) {
    const blocks = segment?.visual_blocks || [];
    const hero = blocks.find((b) => b.block_type === 'pattern_hero');
    const breakdown = blocks.find((b) => b.block_type === 'pattern_breakdown');
    const heroContent = hero?.content || {};
    const breakdownContent = breakdown?.content || {};
    const grammarPoints = breakdownContent?.grammar_points || segment?.grammar_points || [];
    const narrationText = segment?.narration_track?.subtitle_en || '';
    const patternNotes = breakdownContent?.notes || segment?.visual_notes;

    const focusText  = heroContent?.focus_text  || segment?.on_screen_text?.focus_text;
    const focusPinyin = heroContent?.focus_pinyin || segment?.on_screen_text?.focus_pinyin;
    const focusGloss = heroContent?.focus_gloss_en || segment?.on_screen_text?.focus_gloss_en;

    // Compact layout when right side has many cards
    const totalCards = Math.min(grammarPoints.length, 4) + (patternNotes ? 1 : 0);
    const compact = totalCards >= 4;
    const cardPad = compact ? '10px 16px' : '16px 22px';
    const cardGap = compact ? 10 : 18;
    const patternSize = compact ? 32 : 40;
    const explanationSize = compact ? 22 : 26;
    const noteSize = compact ? 22 : 28;

    return (
        <BlackboardShell subtitleText={narrationText}>
            <ChalkTexture opacity={0.09} zIndex={0} />

            {/* Inner vignette */}
            <div style={{
                position: 'absolute', inset: 0, pointerEvents: 'none', zIndex: 0,
                boxShadow: 'inset 0 0 0 2px rgba(68,42,24,0.35), inset 0 0 130px rgba(0,0,0,0.14)',
            }} />

            {/* Header */}
            <div style={{ ...blackboard.header, position: 'relative', zIndex: 2 }}>
                <span style={{ fontSize: 26, fontWeight: 800, letterSpacing: '0.04em', color: chalk.dim }}>
                    {segment?.segment_title}
                </span>
            </div>

            {/* Body */}
            <div style={{
                display: 'grid', gridTemplateColumns: '0.8fr 1.2fr',
                gap: 28, padding: '20px 44px 16px',
                position: 'relative', zIndex: 2,
                flex: 1, overflow: 'hidden',
            }}>
                {/* Left — pattern hero */}
                <section style={{ ...blackboard.panel, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 16, overflow: 'hidden' }}>
                    {/* Wrapping char-by-char hero with stepped font sizing */}
                    {(() => {
                        const heroLines = splitQA(focusText);

                        // Estimate panel content width (0.8fr panel minus 44px side padding each side)
                        const PANEL_W = 860;
                        // Max vertical space for the hero chars (leave ~160px for focusGloss)
                        const MAX_H = focusGloss ? 450 : 620;
                        // Stepped sizes: try largest first, pick first that fits
                        const SIZES = [68, 58, 50, 42, 35, 29];
                        let heroCharSize = 22;
                        for (const sz of SIZES) {
                            const pySize = Math.round(sz * 0.30);
                            const slotW = sz + 4;  // char width + margin
                            const lineH = sz + pySize + 10;
                            let totalH = 0;
                            for (const { text, icon } of heroLines) {
                                const cnCount = [...text].filter(c => /[\u4e00-\u9fff]/.test(c)).length;
                                const otherCount = [...text].length - cnCount;
                                const estW = cnCount * slotW + otherCount * sz * 0.55;
                                const effectiveW = PANEL_W - (icon ? 20 : 0);
                                const wrappedLines = Math.max(1, Math.ceil(estW / effectiveW));
                                totalH += wrappedLines * lineH;
                            }
                            totalH += (heroLines.length - 1) * 16; // gap between Q/A lines
                            if (totalH <= MAX_H) { heroCharSize = sz; break; }
                        }
                        const heroPinyinSize = Math.round(heroCharSize * 0.30);
                        const cellH = heroCharSize + heroPinyinSize + 8;

                        // Extract all syllables once from full focusPinyin, shared across all lines
                        const allHeroSyllables = extractPinyinSyllables(focusPinyin);
                        const totalHeroCh = heroLines.reduce((n, { text }) =>
                            n + [...text].filter(c => /[\u4e00-\u9fff]/.test(c)).length, 0);
                        const hasPinyin = allHeroSyllables.length > 0 && allHeroSyllables.length === totalHeroCh;
                        let globalPi = 0;

                        // Tokenize a line into atomic render units:
                        //   'chinese' → single CJK char (rendered with optional pinyin above)
                        //   'word'    → non-Chinese run / [bracket] / (paren) group — no-wrap atom
                        //   'space'   → wrap opportunity between tokens
                        const tokenizeLine = (text) => {
                            const atoms = [];
                            let i = 0;
                            while (i < text.length) {
                                const ch = text[i];
                                if (/[\u4e00-\u9fff]/.test(ch)) {
                                    atoms.push({ type: 'chinese', value: ch });
                                    i++;
                                } else if (ch === ' ' || ch === '\u00a0') {
                                    atoms.push({ type: 'space' });
                                    i++;
                                } else if (ch === '(' || ch === '[') {
                                    // Collect entire (…) / […] as one no-wrap word
                                    const close = ch === '(' ? ')' : ']';
                                    let j = i, depth = 0;
                                    while (j < text.length) {
                                        if (text[j] === ch) depth++;
                                        else if (text[j] === close) { depth--; if (depth === 0) { j++; break; } }
                                        j++;
                                    }
                                    atoms.push({ type: 'word', value: text.slice(i, j) });
                                    i = j;
                                } else {
                                    // Collect consecutive non-space, non-CJK, non-bracket chars
                                    let j = i;
                                    while (j < text.length && text[j] !== ' ' && !/[\u4e00-\u9fff]/.test(text[j]) && text[j] !== '(' && text[j] !== '[') j++;
                                    const word = text.slice(i, j);
                                    // Look ahead: if next token is a space followed by another
                                    // Title-Cased word (capital first letter), merge them as a
                                    // single no-wrap atom (e.g. "Measure Word", "Measure Word + Noun" stays
                                    // broken at +, but "Measure Word" stays together).
                                    let merged = word;
                                    let k = j;
                                    while (
                                        k < text.length &&
                                        text[k] === ' ' &&
                                        k + 1 < text.length &&
                                        /[A-Z]/.test(text[k + 1]) &&
                                        text[k + 1] !== '(' && text[k + 1] !== '['
                                    ) {
                                        // Collect the next capitalized word
                                        let m = k + 1;
                                        while (m < text.length && text[m] !== ' ' && !/[\u4e00-\u9fff]/.test(text[m]) && text[m] !== '(' && text[m] !== '[') m++;
                                        const nextWord = text.slice(k + 1, m);
                                        // Only merge if next word is also Title-Case (not a separator like '+')
                                        if (/^[A-Z][a-z]/.test(nextWord)) {
                                            merged += ' ' + nextWord;
                                            k = m;
                                        } else {
                                            break;
                                        }
                                    }
                                    atoms.push({ type: 'word', value: merged });
                                    i = k > j ? k : j;
                                }
                            }
                            return atoms;
                        };

                        return heroLines.map(({ icon, text, color }, li) => {
                            const atoms = tokenizeLine(text);
                            return (
                                <div key={li} style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-end', gap: 0 }}>
                                    {icon && (
                                        <span style={{
                                            fontSize: 13, fontWeight: 900,
                                            color, opacity: 0.55, flexShrink: 0,
                                            paddingBottom: heroCharSize * 0.15,
                                            marginRight: 4,
                                            fontStyle: icon === '?' ? 'italic' : 'normal',
                                        }}>
                                            {icon}
                                        </span>
                                    )}
                                    {atoms.map((atom, ai) => {
                                        if (atom.type === 'space') {
                                            // Flex wrap is allowed here; render as a small gap
                                            return <span key={ai} style={{ display: 'inline-block', width: heroCharSize * 0.28, flexShrink: 0 }} />;
                                        }
                                        if (atom.type === 'word') {
                                            return (
                                                <span key={ai} style={{
                                                    whiteSpace: 'nowrap',
                                                    fontSize: heroCharSize * 0.62,
                                                    fontWeight: 900,
                                                    color,
                                                    lineHeight: 1,
                                                    alignSelf: 'flex-end',
                                                    paddingBottom: 2,
                                                    textShadow: '0 0 2px rgba(255,255,255,0.15), 1px 1px 0 rgba(9,20,16,0.35)',
                                                }}>
                                                    {atom.value}
                                                </span>
                                            );
                                        }
                                        // type === 'chinese'
                                        const py = hasPinyin ? (allHeroSyllables[globalPi++] || '') : null;
                                        return (
                                            <span key={ai} style={{
                                                display: 'inline-flex',
                                                flexDirection: 'column',
                                                alignItems: 'center',
                                                height: py !== null ? cellH : undefined,
                                                justifyContent: 'flex-end',
                                                marginRight: 1,
                                            }}>
                                                {py !== null && (
                                                    <span style={{
                                                        fontSize: heroPinyinSize,
                                                        color: 'rgba(244,240,230,0.50)',
                                                        letterSpacing: '0.01em',
                                                        marginBottom: 4,
                                                        lineHeight: 1,
                                                    }}>
                                                        {py}
                                                    </span>
                                                )}
                                                <span style={{
                                                    fontFamily: fontStack,
                                                    fontSize: heroCharSize,
                                                    fontWeight: 900,
                                                    color,
                                                    lineHeight: 1,
                                                    textShadow: '0 0 2px rgba(255,255,255,0.15), 1px 1px 0 rgba(9,20,16,0.35)',
                                                }}>
                                                    {atom.value}
                                                </span>
                                            </span>
                                        );
                                    })}
                                </div>
                            );
                        });
                    })()}
                    {focusGloss && (
                        <div style={{
                            borderRadius: 6,
                            background: 'rgba(126,203,161,0.10)',
                            border: '1px solid rgba(126,203,161,0.22)',
                            padding: '10px 16px',
                            display: 'flex', flexDirection: 'column', gap: 3,
                        }}>
                            {splitQA(focusGloss).map(({ icon, text, color }, i) => (
                                <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'baseline' }}>
                                    {icon && (
                                        <span style={{ fontSize: 14, color, opacity: 0.5, flexShrink: 0, fontStyle: icon === '?' ? 'italic' : 'normal' }}>
                                            {icon}
                                        </span>
                                    )}
                                    <span style={{ fontSize: 26, fontWeight: 600, color: chalk.white, lineHeight: 1.4, opacity: 0.9 }}>
                                        {text}
                                    </span>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* Right — pattern notes + grammar breakdown */}
                <section style={{ display: 'flex', flexDirection: 'column', gap: cardGap, overflow: 'hidden' }}>
                    {patternNotes && (
                        <div style={{
                            display: 'flex', gap: 10, alignItems: 'flex-start',
                            background: 'rgba(0,0,0,0.22)',
                            borderRadius: 7,
                            border: '1px solid rgba(244,240,230,0.08)',
                            borderLeftWidth: 3,
                            borderLeftColor: chalk.blue,
                            padding: cardPad,
                        }}>
                            <span style={{
                                fontSize: 13, fontWeight: 900, letterSpacing: '0.14em',
                                color: chalk.blue, opacity: 0.75, textTransform: 'uppercase',
                                paddingTop: 2, flexShrink: 0,
                            }}>
                                Note
                            </span>
                            <p style={{ margin: 0, fontSize: noteSize, lineHeight: 1.6, color: chalk.white, opacity: 0.6, fontStyle: 'italic' }}>
                                {patternNotes}
                            </p>
                        </div>
                    )}
                    {grammarPoints.slice(0, 4).map((item, index) => {
                        const accentColors = [chalk.yellow, chalk.blue, chalk.green, chalk.pink];
                        const accent = accentColors[index % accentColors.length];
                        const lines = splitQA(item?.pattern);

                        // Pre-assign pinyin syllables across all lines of this card sequentially.
                        // pattern_pinyin covers all Chinese chars in pattern order (excluding [Placeholder] content).
                        const allSyllables = extractPinyinSyllables(item?.pattern_pinyin || '');
                        const totalCardCh = lines.reduce((n, { text }) => {
                            const { chinese } = parsePatternText(text);
                            return n + [...chinese].filter(c => /[\u4e00-\u9fff]/.test(c)).length;
                        }, 0);
                        const cardPinyinValid = allSyllables.length > 0 && allSyllables.length === totalCardCh;
                        let si = 0;
                        const linesWithPinyin = lines.map(({ icon, text, color }) => {
                            const { chinese } = parsePatternText(text);
                            const chCount = [...chinese].filter(c => /[\u4e00-\u9fff]/.test(c)).length;
                            const linePinyin = cardPinyinValid && chCount > 0 ? allSyllables.slice(si, si + chCount).join(' ') : '';
                            si += chCount;
                            return { icon, text, color, linePinyin };
                        });

                        return (
                            <div key={`${item?.pattern || 'pattern'}-${index}`} style={{
                                borderRadius: 8,
                                background: 'rgba(0,0,0,0.28)',
                                borderLeft: `3px solid ${accent}`,
                                borderTop: '1px solid rgba(244,240,230,0.08)',
                                borderRight: '1px solid rgba(244,240,230,0.08)',
                                borderBottom: '1px solid rgba(244,240,230,0.08)',
                                padding: cardPad,
                                display: 'flex', flexDirection: 'column', gap: 3,
                            }}>
                                {linesWithPinyin.map(({ icon, text, color: lineColor, linePinyin }, li) => {
                                    const { chinese } = parsePatternText(text);
                                    const displayColor = linesWithPinyin.length > 1 ? lineColor : accent;
                                    const hasChinese = /[\u4e00-\u9fff]/.test(chinese);
                                    const isFormula = chinese.includes('[');
                                    // Mixed-script (e.g. "Subject + 也 + Verb"): route to PatternFormula
                                    const hasMixedScript = hasChinese && /[a-zA-Z]{2,}/.test(chinese);
                                    const isPureChinese = hasChinese && !isFormula && !hasMixedScript;
                                    return (
                                        <div key={li} style={{ display: 'flex', alignItems: 'flex-end', gap: 6, flexWrap: 'wrap' }}>
                                            {icon && (
                                                <span style={{
                                                    fontSize: 11, fontWeight: 900, color: displayColor,
                                                    opacity: 0.5, flexShrink: 0,
                                                    fontStyle: icon === '?' ? 'italic' : 'normal',
                                                    paddingBottom: 3,
                                                }}>
                                                    {icon}
                                                </span>
                                            )}
                                            {isPureChinese ? (
                                                // Pure Chinese: render char-by-char with pinyin above each char
                                                (() => {
                                                    const charSyllables = extractPinyinSyllables(linePinyin);
                                                    const hasCharPinyin = charSyllables.length > 0;
                                                    const pySize = Math.round(patternSize * 0.42);
                                                    const cellH = patternSize + pySize + 4;
                                                    let cpi = 0;
                                                    return (
                                                        <span style={{ display: 'inline-flex', flexWrap: 'wrap', alignItems: 'flex-end', gap: 2 }}>
                                                            {[...chinese].map((char, ci) => {
                                                                const isCh = /[\u4e00-\u9fff]/.test(char);
                                                                const py = isCh && hasCharPinyin ? (charSyllables[cpi++] || '') : null;
                                                                return (
                                                                    <span key={ci} style={{
                                                                        display: 'inline-flex', flexDirection: 'column',
                                                                        alignItems: 'center',
                                                                        height: py !== null ? cellH : undefined,
                                                                        justifyContent: 'flex-end',
                                                                    }}>
                                                                        {py !== null && (
                                                                            <span style={{
                                                                                fontSize: pySize,
                                                                                color: 'rgba(244,240,230,0.50)',
                                                                                letterSpacing: '0.01em',
                                                                                marginBottom: 3,
                                                                                lineHeight: 1,
                                                                                whiteSpace: 'nowrap',
                                                                            }}>
                                                                                {py}
                                                                            </span>
                                                                        )}
                                                                        <span style={{
                                                                            fontFamily: fontStack,
                                                                            fontSize: isCh ? patternSize : patternSize * 0.8,
                                                                            fontWeight: 900,
                                                                            color: displayColor,
                                                                            lineHeight: 1,
                                                                        }}>
                                                                            {char}
                                                                        </span>
                                                                    </span>
                                                                );
                                                            })}
                                                        </span>
                                                    );
                                                })()
                                            ) : (isFormula || hasMixedScript) ? (
                                                <PatternFormula
                                                    text={chinese}
                                                    pinyin={linePinyin || undefined}
                                                    color={displayColor}
                                                    size={patternSize}
                                                />
                                            ) : (
                                                <span style={{
                                                    fontSize: patternSize, fontWeight: 800,
                                                    color: displayColor, letterSpacing: '0.02em',
                                                    fontStyle: 'italic',
                                                }}>
                                                    {chinese}
                                                </span>
                                            )}
                                        </div>
                                    );
                                })}
                                {item?.explanation_en && (
                                    <p style={{
                                        margin: '5px 0 0', fontSize: explanationSize, lineHeight: 1.55,
                                        color: chalk.white, opacity: 0.45,
                                        fontStyle: 'italic',
                                        borderTop: '1px solid rgba(244,240,230,0.08)',
                                        paddingTop: 5,
                                    }}>
                                        {item.explanation_en}
                                    </p>
                                )}
                            </div>
                        );
                    })}
                </section>
            </div>

        </BlackboardShell>
    );
}
