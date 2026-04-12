import React, { useEffect, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import apiClient from '../api/apiClient';
import ExplanationSegmentTemplate from '../videoTemplates/explanation/ExplanationSegmentTemplate';

// ── Mock data for local UI preview (used when backend returns no render plan) ──
const MOCK_RENDER_PLAN = {
    lesson_title: "Preview — Lesson 1",
    segments: [
        {
            segment_id: "mock-1",
            segment_type: "line_walkthrough",
            template_name: "line_focus",
            segment_title: "Greeting the teacher",
            duration_seconds: 18,
            on_screen_text: {
                focus_text: "你好！",
                focus_pinyin: "nǐ hǎo",
                focus_gloss_en: "Hello!",
            },
            highlight_words: [
                { word: "你", pinyin: "nǐ", english: "you" },
                { word: "好", pinyin: "hǎo", english: "good / well" },
            ],
            narration_track: {
                subtitle_en: "This is the most common Chinese greeting. Literally it means 'you good'. Both syllables carry tones — nǐ is third tone, hǎo is also third tone.",
            },
            visual_blocks: [
                {
                    block_type: "hero_line",
                    content: {
                        focus_text: "你好！",
                        focus_pinyin: "nǐ hǎo",
                        focus_gloss_en: "Hello!",
                    },
                },
                {
                    block_type: "teaching_points",
                    content: {
                        highlight_words: [
                            { word: "你", pinyin: "nǐ", english: "you" },
                            { word: "好", pinyin: "hǎo", english: "good / well" },
                        ],
                        notes: "Drop the final tone on 好 slightly when used in greetings — it sounds more natural.",
                    },
                },
            ],
        },
        {
            segment_id: "mock-2",
            segment_type: "vocabulary_focus",
            template_name: "vocab_spotlight",
            segment_title: "Key vocabulary — names & titles",
            duration_seconds: 22,
            on_screen_text: { focus_text: "老师 · 同学" },
            narration_track: {
                subtitle_en: "Let's look at the two key address terms in this lesson. 老师 means teacher, and 同学 is used to address a classmate or fellow student.",
            },
            visual_notes: "Both words are extremely common in school settings. You'll hear them used as direct address forms — similar to how English speakers say 'Teacher' or 'Classmate'.",
            visual_blocks: [
                {
                    block_type: "vocab_grid",
                    content: {
                        focus_text: "老师 · 同学",
                        highlight_words: [
                            { word: "老师", pinyin: "lǎo shī", english: "teacher", character_insight_en: "老 means old/experienced; 师 means master/instructor." },
                            { word: "同学", pinyin: "tóng xué", english: "classmate / fellow student", character_insight_en: "同 means same/together; 学 means study." },
                            { word: "您好", pinyin: "nín hǎo", english: "formal: How do you do?" },
                            { word: "贵姓", pinyin: "guì xìng", english: "your honorable surname" },
                        ],
                    },
                },
                {
                    block_type: "micro_note",
                    content: {
                        notes: "Use 您好 instead of 你好 when addressing someone older or in a formal setting. 您 is the polite second-person pronoun.",
                    },
                },
            ],
        },
        {
            segment_id: "mock-3",
            segment_type: "grammar_focus",
            template_name: "grammar_pattern",
            segment_title: "Verb 是 — identity statements",
            duration_seconds: 26,
            on_screen_text: {
                focus_text: "我是学生。",
                focus_pinyin: "wǒ shì xuésheng",
                focus_gloss_en: "I am a student.",
            },
            narration_track: {
                subtitle_en: "The verb 是 links a subject to a noun. Unlike English 'to be', 是 does not change form — it's the same for I am, you are, she is.",
            },
            visual_notes: "是 is only used for identity (nouns), not for descriptions. To say 'I am tall' you would NOT use 是 — that uses a stative verb instead.",
            visual_blocks: [
                {
                    block_type: "pattern_hero",
                    content: {
                        focus_text: "我是学生。",
                        focus_gloss_en: "I am a student.",
                    },
                },
                {
                    block_type: "pattern_breakdown",
                    content: {
                        notes: "是 only connects subject + noun (identity). For adjectives, Chinese uses stative verbs directly without 是.",
                        grammar_points: [
                            { pattern: "Subject + 是 + Noun", explanation_en: "Basic identity statement. 我是老师 = I am a teacher." },
                            { pattern: "Subject + 不是 + Noun", explanation_en: "Negation: add 不 before 是. 我不是学生 = I'm not a student." },
                            { pattern: "是…吗？", explanation_en: "Yes/no question: add 吗 at the end. 你是老师吗？= Are you a teacher?" },
                        ],
                    },
                },
            ],
        },
    ],
};
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Renders a template at the same width Remotion uses (1920 - 2×64px padding = 1792px)
 * and scales it down proportionally to fit the preview container.
 * This ensures the preview looks identical to the final rendered video.
 */
const RENDER_WIDTH = 1792;

function ScaledFrame({ children }) {
    const outerRef = useRef(null);
    const [scale, setScale] = useState(1);

    useEffect(() => {
        const el = outerRef.current;
        if (!el) return;
        const update = () => setScale(el.offsetWidth / RENDER_WIDTH);
        update();
        const ro = new ResizeObserver(update);
        ro.observe(el);
        return () => ro.disconnect();
    }, []);

    return (
        <div ref={outerRef} style={{ width: '100%', aspectRatio: '16/9', position: 'relative', overflow: 'hidden' }}>
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: RENDER_WIDTH,
                transformOrigin: 'top left',
                transform: `scale(${scale})`,
            }}>
                {children}
            </div>
        </div>
    );
}

export default function ExplanationTemplatePreview() {
    const { courseId = 1 } = useParams();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [renderPlan, setRenderPlan] = useState(null);
    const [lessonTitle, setLessonTitle] = useState('');
    const [inputLessonId, setInputLessonId] = useState('101');

    const loadLesson = async (lessonId) => {
        setLoading(true);
        setError('');
        try {
            const res = await apiClient.get('/study/lesson_preview', {
                params: { course_id: courseId, lesson_id: lessonId },
            });
            const data = res?.data || {};
            const explanation = data?.video_render_plan?.explanation || null;
            setLessonTitle(data.title || `Lesson ${lessonId}`);
            setRenderPlan(explanation?.segments?.length ? explanation : MOCK_RENDER_PLAN);
        } catch (err) {
            console.error('加载失败:', err);
            setError(`Lesson ${lessonId} 未找到或加载失败。`);
            setRenderPlan(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadLesson(inputLessonId);
    }, []);

    if (loading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-50">
                <Loader2 className="animate-spin text-blue-500" size={32} />
            </div>
        );
    }

    if (error || !renderPlan) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-50">
                <div className="rounded-[2rem] border border-slate-200 bg-white px-8 py-8 text-center shadow-sm">
                    <p className="text-lg font-bold text-slate-800">{error || 'No explanation render plan found.'}</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[linear-gradient(180deg,#f8fafc_0%,#eef2ff_48%,#f8fafc_100%)] px-6 py-10">
            <div className="mx-auto max-w-6xl">
                <div className="mb-8 rounded-[2.5rem] border border-slate-100 bg-white/80 px-8 py-8 shadow-sm backdrop-blur">
                    <div className="text-xs font-black uppercase tracking-[0.3em] text-slate-400">
                        Explanation Video Preview
                    </div>
                    <h1 className="mt-4 text-5xl font-black tracking-tight text-slate-900">
                        {lessonTitle || renderPlan?.lesson_title || '—'}
                    </h1>
                    <div className="mt-5 flex items-center gap-3">
                        <input
                            type="number"
                            value={inputLessonId}
                            onChange={(e) => setInputLessonId(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && loadLesson(inputLessonId)}
                            placeholder="Lesson ID"
                            className="w-32 rounded-xl border border-slate-200 px-4 py-2 text-base font-bold text-slate-700 shadow-sm outline-none focus:border-blue-400"
                        />
                        <button
                            onClick={() => loadLesson(inputLessonId)}
                            disabled={loading}
                            className="rounded-xl bg-slate-800 px-5 py-2 text-sm font-bold text-white shadow hover:bg-slate-700 disabled:opacity-50"
                        >
                            {loading ? '加载中…' : '加载'}
                        </button>
                        {error && <span className="text-sm text-red-500">{error}</span>}
                    </div>
                </div>

                <div className="space-y-8">
                    {(renderPlan?.segments || []).map((segment) => (
                        <ScaledFrame key={`${segment?.segment_id}-${segment?.template_name}`}>
                            <ExplanationSegmentTemplate segment={segment} />
                        </ScaledFrame>
                    ))}
                </div>
            </div>
        </div>
    );
}
