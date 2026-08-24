import { useState } from 'react';
import { CheckCircle2, ExternalLink, RotateCcw, ShieldCheck, XCircle } from 'lucide-react';
import FoundationLayout, { LearningNote, SectionHeading } from './FoundationLayout';
import { TYPING_PRACTICE } from './foundationContent';

const normalizeAnswer = (value) => value.normalize('NFKC').replace(/\s+/g, '').trim();

function KeyCap({ children, accent = false }) {
    return (
        <kbd className={`inline-flex min-h-9 min-w-12 items-center justify-center rounded-lg border px-3 font-mono text-xs font-black shadow-sm ${accent ? 'border-emerald-500 bg-emerald-500 text-white shadow-emerald-200' : 'border-slate-200 bg-white text-slate-600'}`}>
            {children}
        </kbd>
    );
}

function TypingPractice({ copy, content }) {
    const [index, setIndex] = useState(0);
    const [value, setValue] = useState('');
    const [result, setResult] = useState('');
    const complete = index >= TYPING_PRACTICE.length;

    const reset = () => { setIndex(0); setValue(''); setResult(''); };
    const check = () => {
        const normalized = normalizeAnswer(value);
        const matched = TYPING_PRACTICE[index].accepted.some((answer) => normalizeAnswer(answer) === normalized);
        setResult(matched ? 'matched' : 'notMatched');
    };

    if (complete) {
        return (
            <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-8 text-center">
                <CheckCircle2 className="mx-auto text-emerald-500" size={42} />
                <p className="mt-4 text-xl font-black text-emerald-950">{content.matched}</p>
                <button type="button" onClick={reset} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-black text-white"><RotateCcw size={16} /> {copy.common.restart}</button>
            </div>
        );
    }

    const item = TYPING_PRACTICE[index];
    return (
        <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm sm:p-8">
            <div className="flex items-center justify-between text-xs font-black uppercase tracking-[0.2em] text-slate-400">
                <span>{index + 1} / {TYPING_PRACTICE.length}</span>
                <span className="flex items-center gap-2"><ShieldCheck size={14} /> {content.privacy}</span>
            </div>
            <div className="mt-7 rounded-2xl bg-slate-950 p-6 text-center text-white">
                <p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-300">Target</p>
                <p className="mt-3 text-2xl font-black sm:text-3xl">{item.target}</p>
                <p className="mt-3 font-mono text-xs font-bold text-slate-400">{item.romaji}</p>
            </div>
            <div className="mt-5 flex flex-col gap-3 sm:flex-row">
                <input
                    value={value}
                    onChange={(event) => { setValue(event.target.value); setResult(''); }}
                    onKeyDown={(event) => { if (event.key === 'Enter' && !event.nativeEvent.isComposing) check(); }}
                    placeholder={content.inputPlaceholder}
                    lang="ja"
                    autoCapitalize="none"
                    autoCorrect="off"
                    spellCheck="false"
                    className="min-w-0 flex-1 rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4 text-lg font-bold text-slate-900 outline-none transition focus:border-emerald-400 focus:bg-white focus:ring-4 focus:ring-emerald-50"
                />
                <button type="button" onClick={check} disabled={!value.trim()} className="rounded-2xl bg-slate-900 px-7 py-4 text-sm font-black text-white transition hover:bg-emerald-600 disabled:cursor-not-allowed disabled:opacity-40">{content.check}</button>
            </div>
            {result && (
                <div className={`mt-4 flex flex-wrap items-center justify-between gap-4 rounded-2xl border px-5 py-4 ${result === 'matched' ? 'border-emerald-200 bg-emerald-50 text-emerald-800' : 'border-rose-200 bg-rose-50 text-rose-800'}`}>
                    <p className="flex items-center gap-2 text-sm font-black">
                        {result === 'matched' ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                        {content[result]}
                    </p>
                    {result === 'matched' ? (
                        <button type="button" onClick={() => { setIndex((current) => current + 1); setValue(''); setResult(''); }} className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-black text-white">{copy.common.next}</button>
                    ) : (
                        <button type="button" onClick={() => { setValue(''); setResult(''); }} className="rounded-xl border border-rose-300 px-4 py-2 text-xs font-black">{content.reset}</button>
                    )}
                </div>
            )}
        </div>
    );
}

export default function JapaneseTypingBasics(props) {
    const { copy } = props;
    const content = copy.typing;

    return (
        <FoundationLayout {...props} moduleCopy={content} icon="⌨" tone="emerald">
            <section>
                <SectionHeading title={content.flowTitle} />
                <div className="grid gap-4 lg:grid-cols-3">
                    {content.flow.map(([number, title, key, result], index) => (
                        <article key={number} className="relative rounded-3xl border border-slate-100 bg-white p-6 shadow-sm">
                            {index < content.flow.length - 1 && <span className="absolute -right-3 top-1/2 z-10 hidden -translate-y-1/2 text-2xl text-emerald-300 lg:block">→</span>}
                            <p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-500">{copy.common.step} {number}</p>
                            <h3 className="mt-2 text-lg font-black text-slate-900">{title}</h3>
                            <div className="mt-5 flex min-h-14 items-center justify-between gap-3 rounded-2xl bg-slate-50 p-3">
                                <KeyCap accent={index > 0}>{key}</KeyCap>
                                <span className="text-2xl font-black text-slate-900">{result}</span>
                            </div>
                        </article>
                    ))}
                </div>
            </section>

            <section>
                <SectionHeading title={content.setupTitle} body={content.setupNote} />
                <div className="grid gap-4 md:grid-cols-2">
                    {content.platforms.map((platform) => (
                        <article key={platform.name} className="rounded-3xl border border-slate-100 bg-white p-5 shadow-sm">
                            <div className="flex items-center justify-between gap-4">
                                <div className="flex items-center gap-3">
                                    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-lg font-black text-emerald-600">{platform.icon}</span>
                                    <h3 className="font-black text-slate-900">{platform.name}</h3>
                                </div>
                                <a href={platform.url} target="_blank" rel="noreferrer" className="rounded-full p-2 text-slate-300 transition hover:bg-emerald-50 hover:text-emerald-600" aria-label={`${platform.name} official guide`}><ExternalLink size={17} /></a>
                            </div>
                            <ol className="mt-5 space-y-3">
                                {platform.steps.map((step, index) => (
                                    <li key={step} className="flex gap-3 text-sm font-medium leading-6 text-slate-500">
                                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-slate-100 text-[10px] font-black text-slate-500">{index + 1}</span>{step}
                                    </li>
                                ))}
                            </ol>
                        </article>
                    ))}
                </div>
            </section>

            <section>
                <SectionHeading title={content.rulesTitle} />
                <div className="overflow-hidden rounded-3xl border border-slate-100 bg-white shadow-sm">
                    {content.rules.map(([title, example, note], index) => (
                        <article key={title} className={`grid gap-3 px-5 py-5 md:grid-cols-[0.8fr_1fr_1.4fr] md:items-center ${index ? 'border-t border-slate-100' : ''}`}>
                            <h3 className="font-black text-slate-900">{title}</h3>
                            <code className="rounded-xl bg-emerald-50 px-3 py-2 font-mono text-sm font-black text-emerald-700">{example}</code>
                            <p className="text-sm font-medium leading-6 text-slate-500">{note}</p>
                        </article>
                    ))}
                </div>
            </section>

            <section className="grid gap-8 lg:grid-cols-[1.1fr_0.9fr]">
                <div>
                    <SectionHeading title={content.conversionTitle} body={content.conversionBody} />
                    <div className="rounded-[2rem] bg-slate-950 p-6 text-white shadow-xl">
                        <div className="flex flex-wrap gap-2">
                            {'kyouhanihongowobenkyoushimasu'.split('').map((char, index) => <KeyCap key={`${char}-${index}`}>{char}</KeyCap>)}
                        </div>
                        <p className="mt-5 text-lg font-black text-emerald-300">きょうはにほんごをべんきょうします</p>
                        <div className="mt-4 rounded-xl bg-white/10 p-3 text-xl font-black">今日は日本語を勉強します</div>
                    </div>
                </div>
                <div>
                    <SectionHeading title={content.shortcutTitle} />
                    <div className="space-y-3">
                        {content.shortcuts.map(([key, action]) => (
                            <div key={key} className="flex items-center justify-between gap-4 rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                                <KeyCap accent>{key}</KeyCap>
                                <span className="text-right text-sm font-bold text-slate-500">{action}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <section>
                <SectionHeading eyebrow={copy.common.quiz} title={content.practiceTitle} body={content.practiceHelp} />
                <TypingPractice copy={copy} content={content} />
            </section>

            <LearningNote title={content.habitTitle} tone="emerald">
                <ul className="space-y-1.5">{content.habits.map((habit) => <li key={habit} className="flex gap-2"><span>•</span><span>{habit}</span></li>)}</ul>
            </LearningNote>
        </FoundationLayout>
    );
}
