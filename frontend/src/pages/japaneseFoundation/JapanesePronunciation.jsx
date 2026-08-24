import { useState } from 'react';
import { CheckCircle2, RotateCcw, Volume2, XCircle } from 'lucide-react';
import FoundationLayout, { LearningNote, SectionHeading } from './FoundationLayout';
import { MORA_QUIZ } from './foundationContent';

function MoraQuiz({ copy, audio }) {
    const [index, setIndex] = useState(0);
    const [choice, setChoice] = useState(null);
    const [score, setScore] = useState(0);
    const complete = index >= MORA_QUIZ.length;
    const reset = () => { setIndex(0); setChoice(null); setScore(0); };

    if (complete) {
        return (
            <div className="rounded-3xl border border-sky-200 bg-sky-50 p-8 text-center">
                <CheckCircle2 className="mx-auto text-sky-500" size={42} />
                <p className="mt-4 text-2xl font-black text-sky-950">{copy.common.score.replace('{{score}}', score).replace('{{total}}', MORA_QUIZ.length)}</p>
                <button type="button" onClick={reset} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-sky-600 px-5 py-3 text-sm font-black text-white"><RotateCcw size={16} /> {copy.common.restart}</button>
            </div>
        );
    }

    const item = MORA_QUIZ[index];
    const select = (value) => {
        if (choice !== null) return;
        setChoice(value);
        if (value === item.answer) setScore((current) => current + 1);
    };
    const isCorrect = choice === item.answer;

    return (
        <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm sm:p-8">
            <div className="flex items-center justify-between text-xs font-black uppercase tracking-[0.2em] text-slate-400">
                <span>{index + 1} / {MORA_QUIZ.length}</span>
                <span>{copy.common.score.replace('{{score}}', score).replace('{{total}}', MORA_QUIZ.length)}</span>
            </div>
            <div className="mt-7 flex items-center justify-center gap-4">
                <button type="button" onClick={() => audio.play(item.text)} className="rounded-full bg-sky-50 p-3 text-sky-600" aria-label={copy.common.listen}><Volume2 size={20} /></button>
                <span className="text-5xl font-black text-slate-900">{item.text}</span>
            </div>
            <div className="mx-auto mt-8 grid max-w-md grid-cols-4 gap-3">
                {[2, 3, 4, 5].map((number) => {
                    const correct = choice !== null && number === item.answer;
                    const wrong = choice === number && number !== item.answer;
                    return (
                        <button key={number} type="button" onClick={() => select(number)} className={`rounded-2xl border py-4 text-xl font-black transition ${correct ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : wrong ? 'border-rose-300 bg-rose-50 text-rose-700' : 'border-slate-200 text-slate-600 hover:border-sky-300'}`}>
                            {number}
                        </button>
                    );
                })}
            </div>
            {choice !== null && (
                <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-5">
                    <div>
                        <p className={`flex items-center gap-2 text-sm font-black ${isCorrect ? 'text-emerald-600' : 'text-rose-600'}`}>
                            {isCorrect ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                            {isCorrect ? copy.common.correct : copy.common.incorrect}
                        </p>
                        <p className="mt-1 text-sm font-bold text-slate-500">{item.reading} = {item.answer}</p>
                    </div>
                    <button type="button" onClick={() => { setChoice(null); setIndex((value) => value + 1); }} className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-black text-white hover:bg-sky-600">{copy.common.next}</button>
                </div>
            )}
        </div>
    );
}

export default function JapanesePronunciation(props) {
    const { copy, audio } = props;
    const content = copy.pronunciation;

    return (
        <FoundationLayout {...props} moduleCopy={content} icon="音" tone="sky">
            <section>
                <SectionHeading title={content.vowelTitle} />
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                    {content.vowels.map(([kana, romaji, ipa, hint, example]) => (
                        <article key={kana} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                            <div className="flex items-start justify-between">
                                <span className="text-5xl font-black text-sky-500">{kana}</span>
                                <button type="button" onClick={() => audio.play(example.split(' · ')[0])} className="rounded-full p-2 text-slate-300 hover:bg-sky-50 hover:text-sky-600" aria-label={copy.common.listen}><Volume2 size={18} /></button>
                            </div>
                            <p className="mt-3 font-mono text-sm font-black text-slate-500">{romaji} · {ipa}</p>
                            <p className="mt-3 text-sm font-medium leading-6 text-slate-500">{hint}</p>
                            <p className="mt-3 text-sm font-black text-slate-800">{example}</p>
                        </article>
                    ))}
                </div>
            </section>

            <section className="grid items-start gap-8 lg:grid-cols-[1.1fr_0.9fr]">
                <div>
                    <SectionHeading title={content.moraTitle} body={content.moraBody} />
                    <div className="grid gap-3 sm:grid-cols-2">
                        {content.moraExamples.map(([word, breakdown, count]) => (
                            <button key={word} type="button" onClick={() => audio.play(word)} className="rounded-2xl border border-slate-100 bg-white p-5 text-left shadow-sm transition hover:border-sky-200">
                                <span className="flex items-center justify-between text-2xl font-black text-slate-900">{word}<Volume2 size={17} className="text-sky-400" /></span>
                                <span className="mt-3 block font-mono text-sm font-black text-sky-600">{breakdown}</span>
                                <span className="mt-1 block text-xs font-bold text-slate-400">{count}</span>
                            </button>
                        ))}
                    </div>
                </div>
                <div className="rounded-[2rem] bg-slate-950 p-6 text-white shadow-xl">
                    <p className="text-xs font-black uppercase tracking-[0.24em] text-sky-300">Mora timeline</p>
                    <div className="mt-6 space-y-5">
                        {content.moraExamples.map(([word, breakdown]) => (
                            <div key={word}>
                                <div className="flex items-center justify-between text-sm font-black"><span>{word}</span><span className="font-mono text-slate-400">{breakdown}</span></div>
                                <div className="mt-2 flex gap-1.5">
                                    {breakdown.split('・').map((part, idx) => <span key={`${part}-${idx}`} className="h-2 flex-1 rounded-full bg-sky-400" />)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            <section>
                <SectionHeading title={content.contrastsTitle} />
                <div className="grid gap-4 md:grid-cols-2">
                    {content.contrasts.map((item) => (
                        <article key={item.title} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                            <p className="text-xs font-black uppercase tracking-[0.2em] text-sky-500">{item.title}</p>
                            <div className="mt-4 grid grid-cols-[1fr_auto_1fr] items-center gap-3">
                                {[item.left, item.right].map(([word, meaning], index) => (
                                    <div key={word} className={index === 0 ? '' : 'col-start-3'}>
                                        <button type="button" onClick={() => audio.play(word)} className="text-2xl font-black text-slate-900 hover:text-sky-600">{word}</button>
                                        <p className="mt-1 text-xs font-bold text-slate-400">{meaning}</p>
                                    </div>
                                ))}
                                <span className="col-start-2 row-start-1 text-slate-200">≠</span>
                            </div>
                            <p className="mt-4 border-t border-slate-100 pt-4 text-sm font-medium leading-6 text-slate-500">{item.note}</p>
                        </article>
                    ))}
                </div>
            </section>

            <section className="grid gap-8 lg:grid-cols-2">
                <div>
                    <SectionHeading title={content.consonantTitle} />
                    <div className="space-y-3">
                        {content.consonants.map(([title, body]) => (
                            <article key={title} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                                <h3 className="font-black text-slate-900">{title}</h3>
                                <p className="mt-1 text-sm font-medium leading-6 text-slate-500">{body}</p>
                            </article>
                        ))}
                    </div>
                </div>
                <div>
                    <SectionHeading title={content.shadowTitle} />
                    <ol className="space-y-3">
                        {content.shadowSteps.map((step, index) => (
                            <li key={step} className="flex gap-4 rounded-2xl bg-sky-50 p-4 text-sm font-medium leading-6 text-sky-950 ring-1 ring-sky-100">
                                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky-500 text-xs font-black text-white">{index + 1}</span>{step}
                            </li>
                        ))}
                    </ol>
                </div>
            </section>

            <LearningNote title={content.pitchTitle} tone="sky">{content.pitchBody}</LearningNote>

            <section>
                <SectionHeading eyebrow={copy.common.quiz} title={content.quizTitle} body={content.quizHelp} />
                <MoraQuiz copy={copy} audio={audio} />
            </section>
        </FoundationLayout>
    );
}
