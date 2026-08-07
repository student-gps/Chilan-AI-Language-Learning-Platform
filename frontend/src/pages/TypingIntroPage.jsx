import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
    AlertCircle,
    CheckCircle2,
    ChevronRight,
    Keyboard,
    MousePointerClick,
    Settings,
    Sparkles,
} from 'lucide-react';
import IntroFloatingNav from './introNavigation';

const PLATFORM_ICONS = ['▣', '⌘', '◉'];

function KeyboardKey({ children, wide = false, accent = false, muted = false }) {
    return (
        <span
            className={`inline-flex h-9 items-center justify-center rounded-lg border px-2 font-mono text-sm font-black shadow-sm ${
                wide ? 'min-w-28' : 'min-w-9'
            } ${
                accent
                    ? 'border-blue-500 bg-blue-600 text-white shadow-blue-200'
                    : muted
                        ? 'border-slate-100 bg-slate-50 text-slate-300 shadow-none'
                        : 'border-slate-200 bg-white text-slate-700'
            }`}
        >
            {children}
        </span>
    );
}

function CandidateBar({ active = false }) {
    return (
        <div className="flex min-h-11 items-center gap-1.5 overflow-hidden rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm">
            <span className="rounded-lg bg-blue-600 px-2.5 py-1 font-black text-white">你好</span>
            <span className="rounded-lg px-2.5 py-1 font-bold text-slate-400">你号</span>
            <span className="rounded-lg px-2.5 py-1 font-bold text-slate-400">拟好</span>
            <span className={`ml-auto px-1 text-xs font-black ${active ? 'text-blue-500' : 'text-slate-300'}`}>1</span>
        </div>
    );
}

function TypingFlowIllustration() {
    return (
        <div className="relative overflow-hidden rounded-[2rem] border border-slate-200 bg-gradient-to-br from-slate-950 via-slate-900 to-blue-950 p-5 shadow-xl shadow-slate-200/70 sm:p-7">
            <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-blue-400/20 blur-3xl" />
            <div className="absolute -bottom-16 left-1/3 h-44 w-44 rounded-full bg-indigo-400/20 blur-3xl" />
            <div className="relative grid gap-4 lg:grid-cols-[1fr_auto_1fr] lg:items-center">
                <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur-sm">
                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-blue-200">1 · Type pinyin</p>
                    <div className="mt-3 flex flex-wrap gap-1.5">
                        {'nihao'.split('').map((key) => <KeyboardKey key={key}>{key}</KeyboardKey>)}
                    </div>
                    <div className="mt-3 rounded-xl border border-white/10 bg-slate-950/50 px-3 py-2 font-mono text-lg font-black text-white">
                        nihao<span className="ml-0.5 animate-pulse text-blue-300">|</span>
                    </div>
                </div>

                <ChevronRight className="mx-auto rotate-90 text-blue-300 lg:rotate-0" size={28} />

                <div className="rounded-2xl border border-white/10 bg-white/10 p-4 backdrop-blur-sm">
                    <p className="text-[10px] font-black uppercase tracking-[0.22em] text-blue-200">2 · Choose & confirm</p>
                    <div className="mt-3"><CandidateBar active /></div>
                    <div className="mt-3 flex items-center justify-between gap-3">
                        <KeyboardKey wide accent>Space</KeyboardKey>
                        <span className="text-3xl font-black text-white">你好</span>
                    </div>
                </div>
            </div>
            <div className="relative mt-5 flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-xs font-bold text-slate-300">
                <span>不输入声调</span>
                <span className="h-1 w-1 rounded-full bg-blue-300" />
                <span>空格确认候选</span>
                <span className="h-1 w-1 rounded-full bg-blue-300" />
                <span>整词输入更准确</span>
            </div>
        </div>
    );
}

function FlowStepCard({ index, title, body }) {
    const visual = [
        <div className="flex flex-wrap gap-1.5" key="type">{'nihao'.split('').map((key) => <KeyboardKey key={key}>{key}</KeyboardKey>)}</div>,
        <CandidateBar key="candidate" active />,
        <div className="flex items-center justify-between gap-3" key="confirm"><KeyboardKey wide accent>Space</KeyboardKey><span className="text-3xl font-black text-slate-900">你好</span></div>,
    ][index] || <KeyboardKey wide>Enter</KeyboardKey>;

    return (
        <article className="relative rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <span className="absolute right-4 top-4 text-sm font-black text-slate-200">0{index + 1}</span>
            <div className="mb-5 min-h-12 rounded-xl bg-slate-50 p-2.5">{visual}</div>
            <h3 className="text-base font-black text-slate-900">{title}</h3>
            <p className="mt-1 text-sm font-medium leading-relaxed text-slate-500">{body}</p>
        </article>
    );
}

function PlatformSetupCard({ icon, name, steps, showAll, onToggle, expandLabel, collapseLabel }) {
    const keySteps = steps.length > 3
        ? [steps[0], steps[Math.max(1, steps.length - 3)], steps[steps.length - 1]]
        : steps;
    const visibleSteps = showAll ? steps : keySteps;

    return (
        <article className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
            <div className="flex items-center gap-2.5">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white font-black text-blue-600 shadow-sm ring-1 ring-slate-100">{icon}</span>
                <h3 className="font-black text-slate-900">{name}</h3>
            </div>
            <ol className="mt-4 space-y-2.5">
                {visibleSteps.map((step, index) => (
                    <li key={`${name}-${step}`} className="flex gap-2.5 text-sm font-medium leading-relaxed text-slate-500">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white text-[10px] font-black text-blue-500 ring-1 ring-slate-200">{index + 1}</span>
                        <span>{step}</span>
                    </li>
                ))}
            </ol>
            {steps.length > 3 && (
                <button
                    type="button"
                    onClick={onToggle}
                    className="mt-4 text-xs font-black text-blue-600 transition hover:text-blue-800"
                >
                    {showAll ? collapseLabel : expandLabel}
                </button>
            )}
        </article>
    );
}

function InputExampleCard({ keys, result, note, compact = false }) {
    return (
        <article className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between gap-3">
                <span className="font-mono text-base font-black text-blue-600">{keys}</span>
                <ChevronRight size={16} className="shrink-0 text-slate-300" />
                <span className="text-2xl font-black text-slate-900">{result}</span>
            </div>
            {!compact && <p className="mt-2 text-sm font-medium leading-relaxed text-slate-500">{note}</p>}
        </article>
    );
}

function CompactTip({ icon, title, body, tone = 'slate' }) {
    const tones = {
        slate: 'border-slate-100 bg-white text-slate-700',
        amber: 'border-amber-100 bg-amber-50 text-amber-900',
        rose: 'border-rose-100 bg-rose-50 text-rose-900',
    };

    return (
        <article className={`rounded-2xl border p-4 ${tones[tone]}`}>
            <div className="flex gap-3">
                <div className="mt-0.5 shrink-0">{icon}</div>
                <div>
                    <h3 className="font-black">{title}</h3>
                    <p className="mt-1 text-sm font-medium leading-relaxed opacity-70">{body}</p>
                </div>
            </div>
        </article>
    );
}

export default function TypingIntroPage({ foundationNavigation, locationState: routeLocationState, navigate: routeNavigate }) {
    const routerNavigate = useNavigate();
    const location = useLocation();
    const navigate = routeNavigate || routerNavigate;
    const locationState = routeLocationState ?? location.state;
    const { t } = useTranslation();
    const [expandedPlatforms, setExpandedPlatforms] = useState({});
    const [showMoreTips, setShowMoreTips] = useState(false);
    const englishContent = t('typing_intro', { returnObjects: true, lng: 'en' });
    const localizedContent = t('typing_intro', { returnObjects: true });
    const content = {
        ...englishContent,
        ...localizedContent,
        platforms: localizedContent?.platforms || englishContent.platforms,
        flow: localizedContent?.flow || englishContent.flow,
        demos: localizedContent?.demos || englishContent.demos,
        specialExamples: localizedContent?.specialExamples || englishContent.specialExamples,
        skills: localizedContent?.skills || englishContent.skills,
        pitfalls: localizedContent?.pitfalls || englishContent.pitfalls,
        expandLabel: localizedContent?.expandLabel || englishContent.expandLabel || 'Show full steps',
        collapseLabel: localizedContent?.collapseLabel || englishContent.collapseLabel || 'Show less',
        moreTipsLabel: localizedContent?.moreTipsLabel || englishContent.moreTipsLabel || 'More tips',
        hideMoreTipsLabel: localizedContent?.hideMoreTipsLabel || englishContent.hideMoreTipsLabel || 'Hide extra tips',
        enterHint: localizedContent?.enterHint || englishContent.enterHint || 'Enter keeps raw letters for names, URLs, and English words.',
    };
    const visualFlow = content.flow.slice(0, 3);
    const examples = content.demos.filter((_, index) => [0, 2, 3].includes(index));

    return (
        <div className="min-h-screen bg-slate-50 pt-16">
            <IntroFloatingNav
                currentPath="/learn/typing"
                locationState={locationState}
                navigate={navigate}
                t={t}
                foundationNavigation={foundationNavigation}
            />

            <div className="mx-auto max-w-5xl px-5 py-10 pb-28 sm:px-6 sm:py-12">
                <section className="grid items-center gap-8 lg:grid-cols-[0.9fr_1.1fr]">
                    <div>
                        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-4 py-2 text-sm font-black uppercase tracking-widest text-blue-600">
                            <Keyboard size={15} /> {content.badge}
                        </div>
                        <h1 className="max-w-xl text-4xl font-black leading-tight tracking-tight text-slate-900 sm:text-5xl">
                            {content.title}
                        </h1>
                        <p className="mt-4 max-w-xl text-base font-medium leading-relaxed text-slate-500 sm:text-lg">
                            {content.subtitle}
                        </p>
                        <div className="mt-6 flex flex-wrap gap-2">
                            <span className="rounded-full bg-white px-3 py-1.5 text-xs font-black text-slate-600 shadow-sm ring-1 ring-slate-100">拼音 → 候选词 → 汉字</span>
                            <span className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-black text-blue-700 ring-1 ring-blue-100">不用输入声调</span>
                        </div>
                    </div>
                    <TypingFlowIllustration />
                </section>

                <section className="mt-12">
                    <div className="mb-5 flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><MousePointerClick size={20} /></div>
                        <div>
                            <p className="text-sm font-black uppercase tracking-widest text-blue-600">How it works</p>
                            <h2 className="text-2xl font-black text-slate-900">{content.flowTitle}</h2>
                        </div>
                    </div>
                    <div className="grid gap-3 md:grid-cols-3">
                        {visualFlow.map(([title, body], index) => <FlowStepCard key={title} index={index} title={title} body={body} />)}
                    </div>
                    <p className="mt-3 rounded-2xl border border-slate-100 bg-white px-4 py-3 text-sm font-semibold text-slate-500">
                        <span className="mr-2 font-mono font-black text-slate-700">Enter</span>{content.enterHint}
                    </p>
                </section>

                <section className="mt-12 rounded-[2rem] border border-slate-100 bg-white p-5 shadow-sm sm:p-6">
                    <div className="mb-5 flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><Settings size={20} /></div>
                        <div>
                            <p className="text-sm font-black uppercase tracking-widest text-blue-600">One-time setup</p>
                            <h2 className="text-2xl font-black text-slate-900">{content.setupTitle}</h2>
                        </div>
                    </div>
                    <p className="mb-5 max-w-3xl text-sm font-medium leading-relaxed text-slate-500">{content.setupLead}</p>
                    <div className="grid gap-3 md:grid-cols-3">
                        {content.platforms.map(([name, body], index) => {
                            const steps = Array.isArray(body) ? body : body.split(' → ').map((part) => part.trim()).filter(Boolean);
                            return (
                                <PlatformSetupCard
                                    key={name}
                                    icon={PLATFORM_ICONS[index] || '⌨'}
                                    name={name}
                                    steps={steps}
                                    showAll={Boolean(expandedPlatforms[name])}
                                    onToggle={() => setExpandedPlatforms((current) => ({ ...current, [name]: !current[name] }))}
                                    expandLabel={content.expandLabel}
                                    collapseLabel={content.collapseLabel}
                                />
                            );
                        })}
                    </div>
                </section>

                <section className="mt-12 grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
                    <div>
                        <div className="mb-5 flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><Keyboard size={20} /></div>
                            <div>
                                <p className="text-sm font-black uppercase tracking-widest text-blue-600">Quick practice</p>
                                <h2 className="text-2xl font-black text-slate-900">{content.demoTitle}</h2>
                            </div>
                        </div>
                        <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-1">
                            {examples.map(([keys, result, note]) => <InputExampleCard key={keys} keys={keys} result={result} note={note} />)}
                        </div>
                    </div>

                    <section className="rounded-[2rem] border border-amber-100 bg-amber-50 p-5 shadow-sm sm:p-6">
                        <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white text-amber-600 shadow-sm"><Sparkles size={20} /></div>
                            <h2 className="text-2xl font-black text-amber-900">{content.specialTitle}</h2>
                        </div>
                        <div className="mt-5 rounded-2xl border border-amber-200 bg-white/80 p-4">
                            <div className="flex items-center gap-3">
                                <div className="grid grid-cols-3 gap-1.5">
                                    <KeyboardKey muted>u</KeyboardKey>
                                    <KeyboardKey accent>v</KeyboardKey>
                                    <KeyboardKey muted>w</KeyboardKey>
                                </div>
                                <ChevronRight size={18} className="text-amber-400" />
                                <span className="text-3xl font-black text-amber-700">ü</span>
                            </div>
                            <p className="mt-3 text-sm font-medium leading-relaxed text-amber-800">{content.specialBody}</p>
                        </div>
                        <div className="mt-4 space-y-2">
                            {content.specialExamples.map((item) => <InputExampleCard key={item} keys={item.split(' → ')[1] || item} result={item.split(' → ').at(-1)} compact />)}
                        </div>
                    </section>
                </section>

                <section className="mt-12">
                    <div className="mb-5 flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600"><CheckCircle2 size={20} /></div>
                        <div>
                            <p className="text-sm font-black uppercase tracking-widest text-emerald-600">Keep it simple</p>
                            <h2 className="text-2xl font-black text-slate-900">{content.skillsTitle}</h2>
                        </div>
                    </div>
                    <div className="grid gap-3 md:grid-cols-3">
                        {content.skills.slice(0, 3).map(([title, body]) => <CompactTip key={title} icon={<CheckCircle2 size={18} className="text-emerald-500" />} title={title} body={body} />)}
                    </div>
                </section>

                <section className="mt-10">
                    <div className="mb-5 flex items-center gap-3">
                        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-50 text-rose-600"><AlertCircle size={20} /></div>
                        <div>
                            <p className="text-sm font-black uppercase tracking-widest text-rose-600">Quick fixes</p>
                            <h2 className="text-2xl font-black text-slate-900">{content.pitfallsTitle}</h2>
                        </div>
                    </div>
                    <div className="grid gap-3 md:grid-cols-3">
                        {content.pitfalls.slice(0, 3).map(([title, body]) => <CompactTip key={title} icon={<AlertCircle size={18} className="text-rose-500" />} title={title} body={body} tone="rose" />)}
                    </div>
                </section>

                {(content.skills.length > 3 || content.pitfalls.length > 3) && (
                    <section className="mt-5 rounded-2xl border border-slate-100 bg-white px-5 py-4 shadow-sm">
                        <button
                            type="button"
                            onClick={() => setShowMoreTips((value) => !value)}
                            className="flex w-full items-center justify-between text-left text-sm font-black text-slate-700"
                        >
                            <span>{showMoreTips ? content.hideMoreTipsLabel : content.moreTipsLabel}</span>
                            <ChevronRight size={18} className={`text-slate-400 transition-transform ${showMoreTips ? 'rotate-90' : ''}`} />
                        </button>
                        {showMoreTips && (
                            <div className="mt-4 grid gap-3 border-t border-slate-100 pt-4 md:grid-cols-2">
                                {content.skills.slice(3).map(([title, body]) => <CompactTip key={title} icon={<CheckCircle2 size={17} className="text-emerald-500" />} title={title} body={body} />)}
                                {content.pitfalls.slice(3).map(([title, body]) => <CompactTip key={title} icon={<AlertCircle size={17} className="text-rose-500" />} title={title} body={body} tone="rose" />)}
                            </div>
                        )}
                    </section>
                )}
            </div>
        </div>
    );
}
