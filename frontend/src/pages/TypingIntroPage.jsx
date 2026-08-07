import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
    AlertCircle,
    CheckCircle2,
    ChevronRight,
    Command,
    Keyboard,
    Languages,
    ListChecks,
    MousePointerClick,
    Settings,
    Sparkles,
    ToggleLeft,
} from 'lucide-react';
import IntroFloatingNav from './introNavigation';

const replaceArrow = (text) => (text || '').replace('→', '').trim();

function InfoCard({ icon, title, children }) {
    return (
        <section className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
            <div className="mb-4 flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-blue-50 text-blue-600">
                    {icon}
                </div>
                <h2 className="text-2xl font-black text-slate-900">{title}</h2>
            </div>
            {children}
        </section>
    );
}

function NumberedList({ items }) {
    return (
        <div className="grid gap-3">
            {items.map(([title, body], index) => (
                <div key={title} className="flex gap-4 rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-black text-white">
                        {index + 1}
                    </div>
                    <div>
                        <p className="font-black text-slate-800">{title}</p>
                        <p className="mt-1 text-sm font-medium leading-relaxed text-slate-500">{body}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default function TypingIntroPage({ foundationNavigation, locationState: routeLocationState, navigate: routeNavigate }) {
    const routerNavigate = useNavigate();
    const location = useLocation();
    const navigate = routeNavigate || routerNavigate;
    const locationState = routeLocationState ?? location.state;
    const { t } = useTranslation();
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
    };

    return (
        <div className="min-h-screen bg-slate-50 pt-16">
            <IntroFloatingNav
                currentPath="/learn/typing"
                locationState={locationState}
                navigate={navigate}
                t={t}
                foundationNavigation={foundationNavigation}
            />

            <div className="mx-auto max-w-5xl px-6 py-12 pb-28">
                <section className="mb-10">
                    <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-4 py-2 text-sm font-black uppercase tracking-widest text-blue-600">
                        <Keyboard size={15} /> {content.badge}
                    </div>
                    <h1 className="max-w-4xl text-5xl font-black leading-tight tracking-tight text-slate-900">
                        {content.title}
                    </h1>
                    <p className="mt-5 max-w-3xl text-lg font-medium leading-relaxed text-slate-500">
                        {content.subtitle}
                    </p>
                </section>

                <div className="space-y-6">
                    <InfoCard icon={<Settings size={22} />} title={content.setupTitle}>
                        <p className="mb-5 text-base font-medium leading-relaxed text-slate-500">{content.setupLead}</p>
                        <div className="grid gap-3 md:grid-cols-3">
                            {content.platforms.map(([name, body]) => {
                                const steps = Array.isArray(body) ? body : body.split(' → ').map((part) => part.trim()).filter(Boolean);
                                return (
                                <div key={name} className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4">
                                    <p className="font-black text-slate-800">{name}</p>
                                    <ol className="mt-3 space-y-2">
                                        {steps.map((step, index) => (
                                            <li key={`${name}-${step}`} className="flex gap-2 text-sm font-medium leading-relaxed text-slate-500">
                                                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-white text-xs font-black text-blue-500 ring-1 ring-slate-200">
                                                    {index + 1}
                                                </span>
                                                <span>{step}</span>
                                            </li>
                                        ))}
                                    </ol>
                                </div>
                            )})}
                        </div>
                    </InfoCard>

                    <InfoCard icon={<ListChecks size={22} />} title={content.flowTitle}>
                        <NumberedList items={content.flow} />
                    </InfoCard>

                    <InfoCard icon={<MousePointerClick size={22} />} title={content.demoTitle}>
                        <div className="grid gap-3 md:grid-cols-2">
                            {content.demos.map(([keys, result, note]) => (
                                <div key={keys} className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4">
                                    <div className="flex items-center justify-between gap-3">
                                        <span className="font-mono text-lg font-black text-blue-600">{keys}</span>
                                        <ChevronRight size={16} className="shrink-0 text-slate-300" />
                                        <span className="text-2xl font-black text-slate-900">{result}</span>
                                    </div>
                                    <p className="mt-3 text-sm font-medium leading-relaxed text-slate-500">{note}</p>
                                </div>
                            ))}
                        </div>
                    </InfoCard>

                    <section className="rounded-3xl border border-amber-100 bg-amber-50 p-6 shadow-sm">
                        <div className="mb-4 flex items-center gap-3">
                            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-amber-600 ring-1 ring-amber-100">
                                <Sparkles size={22} />
                            </div>
                            <h2 className="text-2xl font-black text-amber-900">{content.specialTitle}</h2>
                        </div>
                        <p className="text-base font-medium leading-relaxed text-amber-800">{content.specialBody}</p>
                        <div className="mt-4 flex flex-wrap gap-2">
                            {content.specialExamples.map((item) => (
                                <span key={item} className="rounded-full bg-white px-3 py-1.5 font-mono text-sm font-black text-amber-700 ring-1 ring-amber-100">
                                    {item}
                                </span>
                            ))}
                        </div>
                    </section>

                    <InfoCard icon={<Command size={22} />} title={content.skillsTitle}>
                        <div className="grid gap-3 md:grid-cols-2">
                            {content.skills.map(([title, body]) => (
                                <div key={title} className="rounded-2xl border border-slate-100 bg-white px-4 py-4">
                                    <div className="mb-2 flex items-center gap-2">
                                        <CheckCircle2 size={17} className="text-emerald-500" />
                                        <p className="font-black text-slate-800">{title}</p>
                                    </div>
                                    <p className="text-sm font-medium leading-relaxed text-slate-500">{body}</p>
                                </div>
                            ))}
                        </div>
                    </InfoCard>

                    <InfoCard icon={<AlertCircle size={22} />} title={content.pitfallsTitle}>
                        <div className="grid gap-3 md:grid-cols-2">
                            {content.pitfalls.map(([title, body]) => (
                                <div key={title} className="rounded-2xl border border-slate-100 bg-slate-50 px-4 py-4">
                                    <p className="font-black text-slate-800">{title}</p>
                                    <p className="mt-1 text-sm font-medium leading-relaxed text-slate-500">{body}</p>
                                </div>
                            ))}
                        </div>
                    </InfoCard>

                    <div className="grid gap-3 md:grid-cols-2">
                        <div className="flex gap-3 rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
                            <ToggleLeft className="mt-1 shrink-0 text-blue-500" size={22} />
                            <p className="text-sm font-semibold leading-relaxed text-slate-500">
                                {content.flow[3][1]}
                            </p>
                        </div>
                        <div className="flex gap-3 rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
                            <Languages className="mt-1 shrink-0 text-blue-500" size={22} />
                            <p className="text-sm font-semibold leading-relaxed text-slate-500">
                                {replaceArrow(t('ci_cta_hanzi'))} → {t('ci_cta_pinyin')} → {t('typing_intro_title')}
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
