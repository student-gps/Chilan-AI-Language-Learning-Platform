import { useMemo, useState } from 'react';
import { CheckCircle2, RotateCcw, Volume2, XCircle } from 'lucide-react';
import FoundationLayout, { LearningNote, SectionHeading } from './FoundationLayout';
import { CONTRACTED_SOUNDS, KANA_QUIZ, KANA_ROWS, VOICED_KANA } from './foundationContent';

function KanaCell({ cell, scriptIndex, audio }) {
    if (!cell) return <div className="min-h-16 rounded-xl bg-slate-50/50" />;
    const kana = cell[scriptIndex];
    const active = audio.playingText === kana;
    return (
        <button
            type="button"
            onClick={() => audio.play(kana)}
            className={`group flex min-h-16 flex-col items-center justify-center rounded-xl border transition ${
                active
                    ? 'border-rose-300 bg-rose-50 text-rose-600 shadow-sm'
                    : 'border-slate-100 bg-white text-slate-800 hover:-translate-y-0.5 hover:border-rose-200 hover:shadow-sm'
            }`}
        >
            <span className="text-2xl font-black sm:text-3xl">{kana}</span>
            <span className="mt-1 text-[10px] font-black uppercase tracking-wider text-slate-400 group-hover:text-rose-400">{cell[2]}</span>
        </button>
    );
}

function KanaQuiz({ copy, audio }) {
    const [index, setIndex] = useState(0);
    const [choice, setChoice] = useState('');
    const [score, setScore] = useState(0);
    const item = KANA_QUIZ[index];
    const complete = index >= KANA_QUIZ.length;

    const reset = () => {
        setIndex(0);
        setChoice('');
        setScore(0);
    };

    if (complete) {
        return (
            <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-8 text-center">
                <CheckCircle2 className="mx-auto text-emerald-500" size={42} />
                <p className="mt-4 text-2xl font-black text-emerald-900">
                    {copy.common.score.replace('{{score}}', score).replace('{{total}}', KANA_QUIZ.length)}
                </p>
                <button type="button" onClick={reset} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-3 text-sm font-black text-white">
                    <RotateCcw size={16} /> {copy.common.restart}
                </button>
            </div>
        );
    }

    const isCorrect = choice === item.answer;
    const select = (nextChoice) => {
        if (choice) return;
        setChoice(nextChoice);
        if (nextChoice === item.answer) setScore((value) => value + 1);
    };
    const next = () => {
        setChoice('');
        setIndex((value) => value + 1);
    };

    return (
        <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm sm:p-8">
            <div className="flex items-center justify-between text-xs font-black uppercase tracking-[0.2em] text-slate-400">
                <span>{index + 1} / {KANA_QUIZ.length}</span>
                <span>{copy.common.score.replace('{{score}}', score).replace('{{total}}', KANA_QUIZ.length)}</span>
            </div>
            <div className="mt-6 flex items-center justify-center gap-4">
                <button type="button" onClick={() => audio.play(item.kana)} className="rounded-full bg-rose-50 p-3 text-rose-500 transition hover:bg-rose-100" aria-label={copy.common.listen}>
                    <Volume2 size={20} />
                </button>
                <span className="text-7xl font-black text-slate-900">{item.kana}</span>
            </div>
            <div className="mx-auto mt-8 grid max-w-xl grid-cols-2 gap-3">
                {item.choices.map((option) => {
                    const showCorrect = choice && option === item.answer;
                    const showWrong = choice === option && option !== item.answer;
                    return (
                        <button
                            key={option}
                            type="button"
                            onClick={() => select(option)}
                            className={`rounded-2xl border px-4 py-3 font-mono text-base font-black transition ${
                                showCorrect ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                                    : showWrong ? 'border-rose-300 bg-rose-50 text-rose-700'
                                        : 'border-slate-200 bg-white text-slate-600 hover:border-rose-200 hover:text-rose-600'
                            }`}
                        >
                            {option}
                        </button>
                    );
                })}
            </div>
            {choice && (
                <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-5">
                    <p className={`flex items-center gap-2 text-sm font-black ${isCorrect ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {isCorrect ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                        {isCorrect ? copy.common.correct : `${copy.common.incorrect} · ${item.answer}`}
                    </p>
                    <button type="button" onClick={next} className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-black text-white hover:bg-rose-600">{copy.common.next}</button>
                </div>
            )}
        </div>
    );
}

export default function JapaneseKanaBasics(props) {
    const { copy, audio } = props;
    const content = copy.kana;
    const [script, setScript] = useState('hiragana');
    const scriptIndex = script === 'hiragana' ? 0 : 1;
    const contracted = useMemo(() => CONTRACTED_SOUNDS.map((item) => [item[scriptIndex], item[2]]), [scriptIndex]);

    return (
        <FoundationLayout {...props} moduleCopy={content} icon="あ" tone="rose">
            <section>
                <SectionHeading title={content.chartTitle} body={content.chartNote} />
                <div className="mb-5 inline-flex rounded-2xl bg-slate-100 p-1">
                    {['hiragana', 'katakana'].map((key) => (
                        <button
                            key={key}
                            type="button"
                            onClick={() => setScript(key)}
                            className={`rounded-xl px-5 py-2.5 text-sm font-black transition ${script === key ? 'bg-white text-rose-600 shadow-sm' : 'text-slate-400'}`}
                        >
                            {content[key]}
                        </button>
                    ))}
                </div>
                <div className="overflow-x-auto rounded-3xl border border-slate-100 bg-white p-3 shadow-sm sm:p-5">
                    <div className="min-w-[560px]">
                        <div className="grid grid-cols-[2.5rem_repeat(5,minmax(0,1fr))] gap-2 pb-2">
                            <div />
                            {content.vowels.map((vowel) => <div key={vowel} className="text-center text-xs font-black uppercase text-slate-400">{vowel}</div>)}
                        </div>
                        <div className="space-y-2">
                            {KANA_ROWS.map((row, rowIndex) => (
                                <div key={`${row.label}-${rowIndex}`} className="grid grid-cols-[2.5rem_repeat(5,minmax(0,1fr))] gap-2">
                                    <div className="flex items-center justify-center text-xs font-black text-slate-300">{row.label}</div>
                                    {row.cells.map((cell, cellIndex) => <KanaCell key={`${rowIndex}-${cellIndex}`} cell={cell} scriptIndex={scriptIndex} audio={audio} />)}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </section>

            <section>
                <SectionHeading title={content.voicedTitle} body={content.voicedBody} />
                <div className="grid gap-3 lg:grid-cols-2">
                    {VOICED_KANA.map((row, rowIndex) => (
                        <article key={row.label} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                            <h3 className="text-sm font-black text-slate-700">{content.voicedLabels[rowIndex]}</h3>
                            <div className="mt-3 grid grid-cols-5 gap-2">
                                {row.pairs.map(([base, voiced, romaji]) => {
                                    const display = scriptIndex === 0 ? voiced : voiced.replace(/[ぁ-ゖ]/g, (char) => String.fromCharCode(char.charCodeAt(0) + 0x60));
                                    return (
                                        <button key={voiced} type="button" onClick={() => audio.play(display)} className="rounded-xl bg-slate-50 px-2 py-3 text-center hover:bg-rose-50">
                                            <span className="block text-xl font-black text-slate-800">{display}</span>
                                            <span className="mt-1 block text-[9px] font-black text-slate-400">{base}→{romaji}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </article>
                    ))}
                </div>
            </section>

            <section>
                <SectionHeading title={content.contractedTitle} body={content.contractedBody} />
                <div className="grid grid-cols-3 gap-2 rounded-3xl border border-slate-100 bg-white p-4 shadow-sm sm:grid-cols-6 lg:grid-cols-8">
                    {contracted.map(([kana, romaji]) => (
                        <button key={kana} type="button" onClick={() => audio.play(kana)} className="rounded-xl px-2 py-3 hover:bg-rose-50">
                            <span className="block text-xl font-black text-slate-800">{kana}</span>
                            <span className="mt-1 block text-[10px] font-black text-slate-400">{romaji}</span>
                        </button>
                    ))}
                </div>
            </section>

            <section>
                <SectionHeading title={content.marksTitle} />
                <div className="grid gap-4 md:grid-cols-2">
                    {content.marks.map(([glyph, title, body, example]) => (
                        <article key={glyph} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                            <div className="flex items-start justify-between gap-4">
                                <span className="text-3xl font-black text-rose-500">{glyph}</span>
                                <button type="button" onClick={() => audio.play(example.split(' · ')[0])} className="text-slate-300 hover:text-rose-500" aria-label={copy.common.listen}><Volume2 size={18} /></button>
                            </div>
                            <h3 className="mt-3 font-black text-slate-900">{title}</h3>
                            <p className="mt-1 text-sm font-medium leading-6 text-slate-500">{body}</p>
                            <p className="mt-3 text-sm font-black text-slate-700">{example}</p>
                        </article>
                    ))}
                </div>
            </section>

            <section className="grid gap-6 lg:grid-cols-2">
                <div>
                    <SectionHeading title={content.planTitle} />
                    <ol className="space-y-3">
                        {content.plan.map((item, index) => (
                            <li key={item} className="flex gap-3 rounded-2xl border border-slate-100 bg-white p-4 text-sm font-medium leading-6 text-slate-600 shadow-sm">
                                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-rose-100 text-xs font-black text-rose-600">{index + 1}</span>
                                {item}
                            </li>
                        ))}
                    </ol>
                </div>
                <div>
                    <SectionHeading title={content.confusionTitle} />
                    <div className="space-y-3">
                        {content.confusions.map(([pair, note]) => (
                            <article key={pair} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                                <h3 className="text-xl font-black text-slate-900">{pair}</h3>
                                <p className="mt-1 text-sm font-medium leading-6 text-slate-500">{note}</p>
                            </article>
                        ))}
                    </div>
                </div>
            </section>

            <section>
                <SectionHeading eyebrow={copy.common.quiz} title={content.quizTitle} body={content.quizHelp} />
                <KanaQuiz copy={copy} audio={audio} />
            </section>

            <LearningNote title={content.planTitle} tone="rose">{content.plan[content.plan.length - 1]}</LearningNote>
        </FoundationLayout>
    );
}
