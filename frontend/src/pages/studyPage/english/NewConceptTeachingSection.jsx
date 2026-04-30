import React, { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
    ArrowLeft,
    ArrowRight,
    BookOpen,
    CheckCircle2,
    GraduationCap,
    Languages,
    Loader2,
    MessageCircle,
    Play,
    Repeat2,
    Volume2,
} from 'lucide-react';
import apiClient from '../../../api/apiClient';
import { claimGlobalAudio, releaseGlobalAudio } from '../../../utils/audioPlayback';

const fadeInUp = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 110, damping: 20 } },
};

const staggerContainer = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.07 } },
};

const getLessonNumber = (lessonId = '') => {
    const digits = String(lessonId).match(/\d+/)?.[0] || '';
    return digits ? digits.padStart(3, '0') : String(lessonId || '');
};

const toApiLessonId = (lessonId = '') => {
    const digits = String(lessonId).match(/\d+/)?.[0];
    return digits ? Number(digits) : lessonId;
};

const extractYouTubeId = (url) => {
    if (!url) return null;
    const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/|v\/))([\w-]{11})/);
    return match ? match[1] : null;
};

const normalizeText = (value) => String(value || '').trim();

const normalizeVocabularyItem = (item = {}) => ({
    term: normalizeText(item.term || item.word || item.text),
    pronunciation: normalizeText(item.pronunciation || item.ipa || item.pinyin),
    partOfSpeech: normalizeText(item.part_of_speech),
    translation: normalizeText(item.translation || item.definition),
    role: normalizeText(item.role),
    sourceLesson: item.source_lesson,
    imageIndex: item.image_index,
    example: item.example_sentence && typeof item.example_sentence === 'object'
        ? {
            text: normalizeText(item.example_sentence.text || item.example_sentence.en),
            translation: normalizeText(item.example_sentence.translation),
            source: normalizeText(item.example_sentence.source),
        }
        : null,
});

function ExplanationVideoPlayer({ videoUrls = {}, title = '', apiBase = '' }) {
    const youtubeId = extractYouTubeId(videoUrls.youtube_url);
    const mediaRaw = normalizeText(videoUrls.media_url);
    const mediaUrl = mediaRaw
        ? (mediaRaw.startsWith('http') ? mediaRaw : `${apiBase}/media/video/${mediaRaw}`)
        : '';
    const localFilename = normalizeText(videoUrls.local_path).replace(/\\/g, '/').split('/').pop();
    const localUrl = !mediaUrl && localFilename ? `${apiBase}/media/video/${localFilename}` : '';
    const videoSrc = mediaUrl || localUrl;

    return (
        <motion.section variants={fadeInUp} className="mb-10">
            <div className="overflow-hidden rounded-lg border border-slate-200 bg-slate-950 shadow-sm" style={{ aspectRatio: '16/9' }}>
                {youtubeId ? (
                    <iframe
                        src={`https://www.youtube.com/embed/${youtubeId}`}
                        className="h-full w-full"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                        allowFullScreen
                        title={title}
                        style={{ border: 'none' }}
                    />
                ) : videoSrc ? (
                    <video
                        src={videoSrc}
                        controls
                        preload="metadata"
                        className="h-full w-full"
                        style={{ background: '#020617' }}
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-[radial-gradient(circle_at_50%_40%,rgba(20,184,166,0.22),transparent_34%),linear-gradient(135deg,#020617,#1e293b)]">
                        <div className="flex h-16 w-16 items-center justify-center rounded-full border border-white/20 bg-white/10 text-white shadow-lg">
                            <Play size={28} className="ml-1" />
                        </div>
                    </div>
                )}
            </div>
        </motion.section>
    );
}

function EnglishTokenLine({ tokens = [], text = '' }) {
    const normalizedTokens = Array.isArray(tokens) && tokens.length
        ? tokens
        : String(text || '').split(/(\s+)/).filter(Boolean).map((part) => ({ text: part, highlight: false }));

    return (
        <p className="text-2xl font-semibold leading-relaxed text-slate-950 md:text-3xl">
            {normalizedTokens.map((token, index) => {
                const tokenText = token?.text ?? '';
                if (!String(tokenText).trim()) {
                    return <React.Fragment key={index}>{tokenText}</React.Fragment>;
                }
                return (
                    <span
                        key={`${tokenText}-${index}`}
                        className={token.highlight ? 'font-black text-teal-700' : ''}
                    >
                        {tokenText}
                        {index < normalizedTokens.length - 1 && !/^[,.!?;:]$/.test(normalizedTokens[index + 1]?.text || '') ? ' ' : ''}
                    </span>
                );
            })}
        </p>
    );
}

function AnchorTextSection({ anchor = {}, onPlayText }) {
    const lines = Array.isArray(anchor.lines) ? anchor.lines : [];
    const isPassage = anchor.type === 'passage';

    return (
        <motion.section variants={fadeInUp} className="mb-10">
            <div className="mb-4 flex items-center justify-between gap-4">
                <div>
                    <div className="flex items-center gap-2 text-sm font-black uppercase tracking-[0.18em] text-teal-700">
                        {isPassage ? <BookOpen size={18} /> : <MessageCircle size={18} />}
                        Text
                    </div>
                    <h2 className="mt-1 text-2xl font-black text-slate-950">{anchor.title}</h2>
                </div>
                {anchor.listening_question?.text && (
                    <div className="hidden max-w-sm rounded-lg border border-teal-100 bg-teal-50 px-4 py-3 text-sm font-semibold text-teal-900 md:block">
                        {anchor.listening_question.text}
                    </div>
                )}
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm md:p-6">
                <div className={isPassage ? 'space-y-6' : 'space-y-4'}>
                    {lines.map((line, index) => {
                        const speaker = normalizeText(line.speaker || line.role);
                        return (
                            <article
                                key={line.line_ref || index}
                                className="grid gap-4 rounded-lg border border-slate-100 bg-slate-50 px-4 py-4 md:grid-cols-[9rem_1fr_auto] md:items-start"
                            >
                                <div className="text-xs font-black uppercase tracking-[0.16em] text-slate-500">
                                    {isPassage ? `Line ${line.line_ref || index + 1}` : speaker}
                                </div>
                                <div className="min-w-0">
                                    <EnglishTokenLine tokens={line.tokens} text={line.text} />
                                    {line.translation && (
                                        <p className="mt-2 text-base font-medium leading-relaxed text-slate-500">
                                            {line.translation}
                                        </p>
                                    )}
                                </div>
                                <button
                                    type="button"
                                    onClick={() => onPlayText(line.text)}
                                    className="flex h-10 w-10 items-center justify-center rounded-full text-slate-500 transition hover:bg-white hover:text-teal-700"
                                    aria-label="Play line audio"
                                >
                                    <Volume2 size={20} />
                                </button>
                            </article>
                        );
                    })}
                </div>
            </div>
        </motion.section>
    );
}

function VocabularySection({ vocabulary = [], onPlayText }) {
    const normalized = vocabulary.map(normalizeVocabularyItem).filter((item) => item.term);
    const dialogueWords = normalized.filter((item) => item.role !== 'pattern_slot');
    const patternWords = normalized.filter((item) => item.role === 'pattern_slot');
    const groups = [
        { key: 'dialogue', title: 'Text Vocabulary', items: dialogueWords, tone: 'border-sky-200 bg-sky-50 text-sky-800' },
        { key: 'pattern', title: 'Pattern Words', items: patternWords, tone: 'border-amber-200 bg-amber-50 text-amber-800' },
    ].filter((group) => group.items.length);

    return (
        <motion.section variants={fadeInUp} className="mb-10">
            <div className="mb-4 flex items-center gap-2 text-sm font-black uppercase tracking-[0.18em] text-sky-700">
                <Languages size={18} />
                Vocabulary
            </div>

            <div className="space-y-5">
                {groups.map((group) => (
                    <div key={group.key}>
                        <h3 className="mb-3 text-lg font-black text-slate-900">{group.title}</h3>
                        <div className="grid gap-3 md:grid-cols-2">
                            {group.items.map((item, index) => (
                                <article key={`${group.key}-${item.term}-${index}`} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="min-w-0">
                                            <div className="flex flex-wrap items-center gap-2">
                                                <h4 className="text-2xl font-black text-slate-950">{item.term}</h4>
                                                {item.imageIndex != null && (
                                                    <span className={`rounded-full border px-2 py-0.5 text-xs font-black ${group.tone}`}>
                                                        {item.imageIndex}
                                                    </span>
                                                )}
                                            </div>
                                            <div className="mt-1 flex flex-wrap items-center gap-2">
                                                {item.pronunciation && (
                                                    <span className="font-mono text-sm font-bold text-teal-700">{item.pronunciation}</span>
                                                )}
                                                {item.partOfSpeech && (
                                                    <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-black uppercase tracking-wider text-slate-500">
                                                        {item.partOfSpeech}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => onPlayText(item.term)}
                                            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-slate-400 transition hover:bg-slate-100 hover:text-teal-700"
                                            aria-label="Play word audio"
                                        >
                                            <Volume2 size={18} />
                                        </button>
                                    </div>

                                    {item.translation && (
                                        <p className="mt-3 text-base font-bold text-slate-700">{item.translation}</p>
                                    )}

                                    {item.example?.text && (
                                        <div className="mt-4 border-t border-slate-100 pt-3">
                                            <p className="text-base font-semibold leading-relaxed text-slate-900">
                                                {item.example.text}
                                            </p>
                                            {item.example.translation && (
                                                <p className="mt-1 text-sm font-medium text-slate-500">{item.example.translation}</p>
                                            )}
                                        </div>
                                    )}
                                </article>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </motion.section>
    );
}

function PatternText({ pattern = '' }) {
    const pieces = String(pattern || '').split(/(\{item\})/g).filter(Boolean);
    return (
        <p className="text-3xl font-black tracking-tight text-slate-950 md:text-4xl">
            {pieces.map((piece, index) => (
                piece === '{item}' ? (
                    <span key={index} className="mx-1 rounded-md bg-amber-100 px-2 text-amber-800">
                        item
                    </span>
                ) : (
                    <React.Fragment key={index}>{piece}</React.Fragment>
                )
            ))}
        </p>
    );
}

function PatternDrillSection({ patternDrills = [], onPlayText }) {
    if (!patternDrills.length) return null;

    return (
        <motion.section variants={fadeInUp} className="mb-10">
            <div className="mb-4 flex items-center gap-2 text-sm font-black uppercase tracking-[0.18em] text-amber-700">
                <Repeat2 size={18} />
                Pattern Drill
            </div>

            <div className="space-y-4">
                {patternDrills.map((drill, drillIndex) => (
                    <article key={drillIndex} className="rounded-lg border border-amber-200 bg-white p-5 shadow-sm">
                        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                            <div>
                                <PatternText pattern={drill.pattern} />
                                {drill.translation_pattern && (
                                    <p className="mt-2 text-lg font-semibold text-slate-500">{drill.translation_pattern}</p>
                                )}
                            </div>
                            <button
                                type="button"
                                onClick={() => onPlayText(String(drill.pattern || '').replace('{item}', ''))}
                                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-slate-500 transition hover:bg-amber-50 hover:text-amber-700"
                                aria-label="Play pattern audio"
                            >
                                <Volume2 size={20} />
                            </button>
                        </div>

                        {Array.isArray(drill.response_patterns) && drill.response_patterns.length > 0 && (
                            <div className="mt-4 flex flex-wrap gap-2">
                                {drill.response_patterns.map((response, index) => (
                                    <span key={index} className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-sm font-bold text-slate-700">
                                        {response.text}
                                        {response.translation ? <span className="ml-2 font-medium text-slate-400">{response.translation}</span> : null}
                                    </span>
                                ))}
                            </div>
                        )}

                        {Array.isArray(drill.slots) && drill.slots.length > 0 && (
                            <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-5">
                                {drill.slots.map((slot, index) => (
                                    <button
                                        key={`${slot.text}-${index}`}
                                        type="button"
                                        onClick={() => onPlayText(slot.text)}
                                        className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-3 text-left transition hover:border-amber-300 hover:bg-amber-50"
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <span className="text-lg font-black text-slate-900">{slot.text}</span>
                                            {slot.image_index != null && (
                                                <span className="rounded-full bg-white px-2 py-0.5 text-xs font-black text-slate-400">
                                                    {slot.image_index}
                                                </span>
                                            )}
                                        </div>
                                        {slot.translation && (
                                            <p className="mt-1 text-sm font-semibold text-slate-500">{slot.translation}</p>
                                        )}
                                    </button>
                                ))}
                            </div>
                        )}

                        {Array.isArray(drill.generated_prompts) && drill.generated_prompts.length > 0 && (
                            <div className="mt-5 grid gap-2">
                                {drill.generated_prompts.slice(0, 6).map((prompt, index) => (
                                    <div key={`${prompt.text}-${index}`} className="flex items-center justify-between gap-3 rounded-lg bg-slate-50 px-4 py-3">
                                        <div>
                                            <p className="text-base font-bold text-slate-900">{prompt.text}</p>
                                            {prompt.translation && <p className="text-sm font-medium text-slate-500">{prompt.translation}</p>}
                                        </div>
                                        <button
                                            type="button"
                                            onClick={() => onPlayText(prompt.text)}
                                            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-slate-400 transition hover:bg-white hover:text-amber-700"
                                            aria-label="Play drill sentence"
                                        >
                                            <Volume2 size={16} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </article>
                ))}
            </div>
        </motion.section>
    );
}

function GrammarNotesSection({ teachingMaterials = {} }) {
    const notes = Array.isArray(teachingMaterials.notes_on_text) ? teachingMaterials.notes_on_text : [];
    const grammarSections = Array.isArray(teachingMaterials.grammar_sections) ? teachingMaterials.grammar_sections : [];
    if (!notes.length && !grammarSections.length) return null;

    return (
        <motion.section variants={fadeInUp} className="mb-10">
            <div className="mb-4 flex items-center gap-2 text-sm font-black uppercase tracking-[0.18em] text-rose-700">
                <GraduationCap size={18} />
                Notes & Grammar
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
                {notes.map((note, index) => (
                    <article key={`note-${index}`} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                        <h3 className="text-xl font-black text-slate-950">{note.focus_text}</h3>
                        {note.translation && <p className="mt-1 font-semibold text-slate-500">{note.translation}</p>}
                        {note.explanation && <p className="mt-3 leading-relaxed text-slate-700">{note.explanation}</p>}
                    </article>
                ))}

                {grammarSections.map((section, index) => (
                    <article key={`grammar-${index}`} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                        <h3 className="text-xl font-black text-slate-950">{section.title}</h3>
                        {(section.explanation || section.explanation_en) && (
                            <p className="mt-2 leading-relaxed text-slate-700">{section.explanation || section.explanation_en}</p>
                        )}
                        {Array.isArray(section.patterns) && section.patterns.length > 0 && (
                            <div className="mt-3 space-y-2">
                                {section.patterns.map((pattern, pIndex) => (
                                    <div key={pIndex} className="rounded-lg bg-rose-50 px-3 py-2">
                                        <p className="font-black text-rose-900">{pattern.pattern}</p>
                                        {(pattern.translation || pattern.meaning_en) && (
                                            <p className="text-sm font-semibold text-rose-700">{pattern.translation || pattern.meaning_en}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </article>
                ))}
            </div>
        </motion.section>
    );
}

export default function NewConceptTeachingSection({
    data,
    courseId,
    userId,
    onStartPractice,
    isDirectLesson,
}) {
    const navigate = useNavigate();
    const [isSaving, setIsSaving] = useState(false);
    const activeAudioRef = useRef(null);
    const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';

    if (!data) return null;

    const metadata = data.lesson_metadata || {};
    const content = data.course_content || {};
    const anchor = content.anchor || {};
    const source = metadata.source || {};
    const sourceLessons = Array.isArray(source.source_lessons) ? source.source_lessons : [];

    const playTts = (text) => {
        const cleanText = normalizeText(text);
        if (!cleanText) return;
        if (activeAudioRef.current) {
            activeAudioRef.current.pause();
            releaseGlobalAudio(activeAudioRef.current);
        }
        const audio = new Audio(`${API_BASE}/study/tts?text=${encodeURIComponent(cleanText)}`);
        activeAudioRef.current = audio;
        claimGlobalAudio(audio);
        audio.onpause = () => releaseGlobalAudio(audio);
        audio.onended = () => releaseGlobalAudio(audio);
        audio.onerror = () => releaseGlobalAudio(audio);
        audio.play().catch(() => releaseGlobalAudio(audio));
    };

    const handleStartPracticeClick = async () => {
        if (isSaving) return;
        setIsSaving(true);
        try {
            await apiClient.post('/study/content_viewed', {
                user_id: userId,
                course_id: courseId,
                lesson_id: toApiLessonId(metadata.lesson_id),
            });
        } catch (error) {
            console.error('记录阅读进度失败:', error);
        } finally {
            setIsSaving(false);
            onStartPractice();
        }
    };

    return (
        <motion.div
            key="new-concept-teaching"
            variants={staggerContainer}
            initial="hidden"
            animate="show"
            exit={{ opacity: 0, y: -10, transition: { duration: 0.18 } }}
            className="mx-auto max-w-6xl px-5 pt-24 md:px-6"
        >
            <motion.header variants={fadeInUp} className="mb-8">
                <div className="flex flex-wrap items-center gap-3">
                    <span className="rounded-full bg-teal-700 px-3 py-1 text-xs font-black uppercase tracking-[0.18em] text-white">
                        New Concept English
                    </span>
                    <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-black uppercase tracking-[0.18em] text-slate-600">
                        Lesson {getLessonNumber(metadata.lesson_slug || metadata.lesson_id)}
                    </span>
                    {sourceLessons.length > 0 && (
                        <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-black uppercase tracking-[0.18em] text-amber-800">
                            Source {sourceLessons.join(' + ')}
                        </span>
                    )}
                </div>
                <h1 className="mt-4 text-4xl font-black tracking-tight text-slate-950 md:text-5xl">
                    {metadata.title}
                </h1>
                {metadata.title_localized && (
                    <p className="mt-2 text-xl font-semibold text-slate-500">
                        {metadata.title_localized}
                    </p>
                )}
            </motion.header>

            <ExplanationVideoPlayer
                videoUrls={data.explanation_video_urls || {}}
                title={metadata.title}
                apiBase={API_BASE}
            />

            <AnchorTextSection anchor={anchor} onPlayText={playTts} />

            <VocabularySection vocabulary={content.vocabulary || []} onPlayText={playTts} />

            <PatternDrillSection patternDrills={content.pattern_drills || []} onPlayText={playTts} />

            <GrammarNotesSection teachingMaterials={data.teaching_materials || {}} />

            {!isDirectLesson && (
                <motion.div variants={fadeInUp} className="flex justify-center pb-24 pt-4">
                    <button
                        type="button"
                        onClick={handleStartPracticeClick}
                        disabled={isSaving}
                        className="flex items-center gap-3 rounded-lg bg-slate-950 px-10 py-4 text-lg font-black text-white shadow-sm transition hover:bg-teal-700 disabled:bg-slate-400"
                    >
                        {isSaving ? (
                            <>
                                <Loader2 className="animate-spin" size={22} />
                                生成练习
                            </>
                        ) : (
                            <>
                                <CheckCircle2 size={22} />
                                开始练习
                                <ArrowRight size={20} />
                            </>
                        )}
                    </button>
                </motion.div>
            )}

            {isDirectLesson && (
                <button
                    type="button"
                    onClick={() => navigate(`/course/${courseId}`)}
                    className="fixed left-6 top-24 z-50 flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2.5 font-semibold text-slate-600 shadow-sm transition hover:bg-slate-50 hover:text-slate-950"
                >
                    <ArrowLeft size={16} /> 返回课程
                </button>
            )}
        </motion.div>
    );
}
