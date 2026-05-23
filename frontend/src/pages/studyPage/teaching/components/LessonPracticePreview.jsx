import React, { useMemo, useState } from 'react';
import { CheckCircle2, Database, Layers3, Search, Tags } from 'lucide-react';

const asArray = (value) => (Array.isArray(value) ? value : []);

const textOf = (...values) => {
    for (const value of values) {
        const text = String(value || '').trim();
        if (text) return text;
    }
    return '';
};

const TYPE_LABELS = {
    CN_TO_JA: '中译日',
    JA_TO_CN: '日译中',
    JA_LISTEN_WRITE: '听写',
    JA_SPEAK: '口说',
    CONJUGATION: '活用',
};

const TYPE_HINTS = {
    CN_TO_JA: '看中文，写出日语。',
    JA_TO_CN: '看日语，理解中文意思。',
    JA_LISTEN_WRITE: '听日语音频，写出原句。',
    JA_SPEAK: '看中文提示，说出日语。',
    CONJUGATION: '针对动词、形容词等做形式变化。',
};

const typeLabel = (type) => TYPE_LABELS[type] || type || '未分类';

const sourceLabel = (metadata = {}) => {
    const context = metadata.context || {};
    return textOf(
        metadata.source_section && metadata.source_ref
            ? `${metadata.source_section} #${metadata.source_ref}`
            : '',
        context.source_section && context.source_ref
            ? `${context.source_section} #${context.source_ref}`
            : '',
        context.source,
        metadata.audio_id,
        '未知来源',
    );
};

function AnswerPills({ answers }) {
    const normalized = asArray(answers).map(String).map((item) => item.trim()).filter(Boolean);
    if (!normalized.length) return <span className="text-sm font-bold text-slate-400">无标准答案</span>;
    return (
        <div className="flex flex-wrap gap-2">
            {normalized.map((answer, index) => (
                <span
                    key={`${answer}-${index}`}
                    className="rounded-full bg-emerald-50 px-3 py-1 text-sm font-black text-emerald-700 ring-1 ring-emerald-100"
                >
                    {answer}
                </span>
            ))}
        </div>
    );
}

function ContextExamples({ examples }) {
    const visible = asArray(examples).slice(0, 2);
    if (!visible.length) return null;
    return (
        <div className="mt-4 space-y-2">
            {visible.map((example, index) => (
                <div key={`${example?.text || index}`} className="rounded-2xl bg-white/80 px-4 py-3 ring-1 ring-slate-100">
                    <p className="text-base font-black text-slate-900">{textOf(example.text)}</p>
                    {example.reading && (
                        <p className="mt-1 text-xs font-black text-rose-500">{example.reading}</p>
                    )}
                    {example.translation && (
                        <p className="mt-1 text-sm font-bold text-slate-500">{example.translation}</p>
                    )}
                </div>
            ))}
        </div>
    );
}

function PracticeCard({ item }) {
    const type = item?.question_type || 'UNKNOWN';
    const metadata = item?.metadata || {};
    const prompt = textOf(item.original_text, item.prompt);
    const reading = textOf(item.original_pinyin, item.reading);
    const answers = asArray(item.standard_answers);
    return (
        <article className="rounded-[1.5rem] border border-slate-100 bg-slate-50/80 p-5 shadow-sm">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                    <span className="rounded-full bg-slate-900 px-3 py-1 text-xs font-black text-white">
                        #{item?.question_id || '?'}
                    </span>
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-blue-700 ring-1 ring-blue-100">
                        {typeLabel(type)}
                    </span>
                </div>
                <span className="inline-flex items-center gap-1.5 rounded-full bg-white px-3 py-1 text-xs font-black text-slate-500 ring-1 ring-slate-100">
                    <Tags size={13} />
                    {sourceLabel(metadata)}
                </span>
            </div>

            <div className="grid gap-4 md:grid-cols-[1fr_1fr]">
                <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                    <p className="mb-2 text-xs font-black tracking-[0.18em] text-slate-400">题干</p>
                    <p className="break-words text-2xl font-black leading-snug text-slate-950">{prompt || '空题干'}</p>
                    {reading && (
                        <p className="mt-2 break-words text-sm font-black text-rose-500">{reading}</p>
                    )}
                </div>
                <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-100">
                    <p className="mb-2 text-xs font-black tracking-[0.18em] text-slate-400">标准答案</p>
                    <AnswerPills answers={answers} />
                </div>
            </div>

            <ContextExamples examples={item.context_examples} />

            {metadata?.skill_tags?.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                    {metadata.skill_tags.map((tag) => (
                        <span key={tag} className="rounded-full bg-purple-50 px-2.5 py-1 text-xs font-black text-purple-700">
                            {tag}
                        </span>
                    ))}
                </div>
            )}
        </article>
    );
}

export default function LessonPracticePreview({ items = [], className = '' }) {
    const [activeType, setActiveType] = useState('ALL');
    const [query, setQuery] = useState('');
    const normalizedItems = asArray(items).filter((item) => item && typeof item === 'object');

    const groups = useMemo(() => {
        const map = new Map();
        for (const item of normalizedItems) {
            const type = item.question_type || 'UNKNOWN';
            if (!map.has(type)) map.set(type, []);
            map.get(type).push(item);
        }
        return Array.from(map.entries()).sort(([a], [b]) => a.localeCompare(b));
    }, [normalizedItems]);

    const filteredItems = useMemo(() => {
        const needle = query.trim().toLowerCase();
        return normalizedItems.filter((item) => {
            if (activeType !== 'ALL' && item.question_type !== activeType) return false;
            if (!needle) return true;
            const haystack = [
                item.question_type,
                item.original_text,
                item.original_pinyin,
                ...asArray(item.standard_answers),
                ...asArray(item.context_examples).flatMap((example) => [example?.text, example?.reading, example?.translation]),
            ].map((value) => String(value || '').toLowerCase()).join('\n');
            return haystack.includes(needle);
        });
    }, [activeType, normalizedItems, query]);

    if (!normalizedItems.length) return null;

    return (
        <section className={`mb-20 ${className}`}>
            <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
                <div>
                    <h2 className="text-3xl font-black tracking-tight text-slate-900">题目预览</h2>
                    <p className="mt-1 text-sm font-bold text-slate-500">
                        直接查看 Stage1 生成的 database_items，用来快速检查题干、答案和来源。
                    </p>
                </div>
                <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
                    <Search size={16} className="text-slate-400" />
                    <input
                        value={query}
                        onChange={(event) => setQuery(event.target.value)}
                        placeholder="搜索题干 / 答案"
                        className="h-8 w-56 bg-transparent text-sm font-bold text-slate-800 outline-none placeholder:text-slate-400"
                    />
                </div>
            </div>

            <div className="mb-5 flex flex-wrap gap-2">
                <button
                    type="button"
                    onClick={() => setActiveType('ALL')}
                    className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-black transition ${
                        activeType === 'ALL' ? 'bg-slate-950 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200'
                    }`}
                >
                    <Database size={15} />
                    全部 {normalizedItems.length}
                </button>
                {groups.map(([type, groupItems]) => (
                    <button
                        key={type}
                        type="button"
                        onClick={() => setActiveType(type)}
                        className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm font-black transition ${
                            activeType === type ? 'bg-slate-950 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200'
                        }`}
                        title={TYPE_HINTS[type] || ''}
                    >
                        <Layers3 size={15} />
                        {typeLabel(type)} {groupItems.length}
                    </button>
                ))}
            </div>

            <div className="mb-4 flex items-center gap-2 rounded-2xl bg-emerald-50 px-4 py-3 text-sm font-black text-emerald-700 ring-1 ring-emerald-100">
                <CheckCircle2 size={17} />
                当前显示 {filteredItems.length} / {normalizedItems.length} 道题。
            </div>

            <div className="grid grid-cols-1 gap-4">
                {filteredItems.map((item, index) => (
                    <PracticeCard key={`${item.question_type}-${item.question_id || index}`} item={item} />
                ))}
            </div>
        </section>
    );
}
