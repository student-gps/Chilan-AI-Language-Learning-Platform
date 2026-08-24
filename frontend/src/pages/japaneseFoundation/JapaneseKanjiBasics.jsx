import { useState } from 'react';
import { CheckCircle2, RotateCcw, Volume2, XCircle } from 'lucide-react';
import FoundationLayout, { LearningNote, SectionHeading } from './FoundationLayout';
import { KANJI_QUIZ } from './foundationContent';

function KanjiQuiz({ copy, audio }) {
    const [index, setIndex] = useState(0);
    const [choice, setChoice] = useState('');
    const [score, setScore] = useState(0);
    const complete = index >= KANJI_QUIZ.length;
    const reset = () => { setIndex(0); setChoice(''); setScore(0); };

    if (complete) {
        return (
            <div className="rounded-3xl border border-indigo-200 bg-indigo-50 p-8 text-center">
                <CheckCircle2 className="mx-auto text-indigo-500" size={42} />
                <p className="mt-4 text-2xl font-black text-indigo-950">{copy.common.score.replace('{{score}}', score).replace('{{total}}', KANJI_QUIZ.length)}</p>
                <button type="button" onClick={reset} className="mt-5 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-black text-white"><RotateCcw size={16} /> {copy.common.restart}</button>
            </div>
        );
    }

    const item = KANJI_QUIZ[index];
    const choose = (value) => {
        if (choice) return;
        setChoice(value);
        if (value === item.answer) setScore((current) => current + 1);
    };
    const correct = choice === item.answer;

    return (
        <div className="rounded-3xl border border-slate-100 bg-white p-6 shadow-sm sm:p-8">
            <div className="flex items-center justify-between text-xs font-black uppercase tracking-[0.2em] text-slate-400">
                <span>{index + 1} / {KANJI_QUIZ.length}</span>
                <span>{copy.common.score.replace('{{score}}', score).replace('{{total}}', KANJI_QUIZ.length)}</span>
            </div>
            <p className="mt-7 text-center text-6xl font-black text-slate-900">{item.word}</p>
            <div className="mx-auto mt-8 grid max-w-2xl gap-3 sm:grid-cols-2">
                {item.choices.map((option) => {
                    const showCorrect = choice && option === item.answer;
                    const showWrong = choice === option && option !== item.answer;
                    return (
                        <button key={option} type="button" onClick={() => choose(option)} className={`rounded-2xl border px-4 py-3 text-lg font-black transition ${showCorrect ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : showWrong ? 'border-rose-300 bg-rose-50 text-rose-700' : 'border-slate-200 text-slate-600 hover:border-indigo-300 hover:text-indigo-600'}`}>
                            {option}
                        </button>
                    );
                })}
            </div>
            {choice && (
                <div className="mt-6 flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-5">
                    <p className={`flex items-center gap-2 text-sm font-black ${correct ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {correct ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
                        {correct ? copy.common.correct : `${copy.common.incorrect} · ${item.answer}`}
                    </p>
                    <div className="flex gap-2">
                        <button type="button" onClick={() => audio.play(item.word)} className="rounded-xl border border-slate-200 px-3 py-2 text-slate-500"><Volume2 size={17} /></button>
                        <button type="button" onClick={() => { setChoice(''); setIndex((value) => value + 1); }} className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-black text-white hover:bg-indigo-600">{copy.common.next}</button>
                    </div>
                </div>
            )}
        </div>
    );
}

export default function JapaneseKanjiBasics(props) {
    const { copy, audio, supportLanguage } = props;
    const content = copy.kanji;
    const contextHeaders = supportLanguage === 'zh' ? ['字', '词语', '读音', '含义'] : ['Kanji', 'Word', 'Reading', 'Meaning'];
    const componentHeaders = supportLanguage === 'zh' ? ['部件', '线索', '例字', '常见关联'] : ['Part', 'Cue', 'Examples', 'Common link'];

    return (
        <FoundationLayout {...props} moduleCopy={content} icon="漢" tone="indigo">
            <section>
                <SectionHeading title={content.systemTitle} />
                <div className="grid gap-5 lg:grid-cols-3">
                    {content.system.map((item, index) => (
                        <article key={item.title} className="rounded-3xl border border-indigo-100 bg-white p-6 shadow-sm">
                            <div className="flex h-20 items-center text-5xl font-black text-indigo-500">{item.glyph}</div>
                            <p className="text-xs font-black uppercase tracking-[0.2em] text-indigo-400">0{index + 1}</p>
                            <h3 className="mt-2 text-xl font-black text-slate-900">{item.title}</h3>
                            <p className="mt-2 text-sm font-medium leading-7 text-slate-500">{item.body}</p>
                            <button type="button" onClick={() => audio.play(item.examples.split('・')[0].split('（')[0])} className="mt-5 flex w-full items-center justify-between rounded-2xl bg-indigo-50 px-4 py-3 text-left text-sm font-black text-indigo-800">
                                <span>{item.examples}</span><Volume2 size={16} />
                            </button>
                        </article>
                    ))}
                </div>
            </section>

            <section>
                <SectionHeading title={content.contextTitle} />
                <div className="overflow-x-auto rounded-3xl border border-slate-100 bg-white shadow-sm">
                    <table className="w-full min-w-[620px] border-collapse text-left">
                        <thead className="bg-slate-50 text-xs font-black uppercase tracking-[0.16em] text-slate-400">
                            <tr>{contextHeaders.map((header) => <th key={header} className="px-5 py-4">{header}</th>)}<th className="w-14" /></tr>
                        </thead>
                        <tbody>
                            {content.contextRows.map(([kanji, word, reading, meaning]) => (
                                <tr key={`${word}-${reading}`} className="border-t border-slate-100">
                                    <td className="px-5 py-4 text-2xl font-black text-indigo-500">{kanji}</td>
                                    <td className="px-5 py-4 text-xl font-black text-slate-900">{word}</td>
                                    <td className="px-5 py-4 font-black text-rose-500">{reading}</td>
                                    <td className="px-5 py-4 text-sm font-medium text-slate-500">{meaning}</td>
                                    <td className="pr-4"><button type="button" onClick={() => audio.play(word)} className="rounded-full p-2 text-slate-300 hover:bg-indigo-50 hover:text-indigo-600" aria-label={copy.common.listen}><Volume2 size={17} /></button></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            <section>
                <SectionHeading title={content.componentsTitle} body={content.componentsBody} />
                <div className="overflow-x-auto rounded-3xl border border-slate-100 bg-white shadow-sm">
                    <table className="w-full min-w-[620px] border-collapse text-left">
                        <thead className="bg-slate-50 text-xs font-black uppercase tracking-[0.16em] text-slate-400">
                            <tr>{componentHeaders.map((header) => <th key={header} className="px-5 py-4">{header}</th>)}</tr>
                        </thead>
                        <tbody>
                            {content.components.map(([part, cue, examples, link]) => (
                                <tr key={part} className="border-t border-slate-100">
                                    <td className="px-5 py-4 text-3xl font-black text-indigo-500">{part}</td>
                                    <td className="px-5 py-4 font-black text-slate-800">{cue}</td>
                                    <td className="px-5 py-4 text-lg font-black tracking-wider text-slate-700">{examples}</td>
                                    <td className="px-5 py-4 text-sm font-medium text-slate-500">{link}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </section>

            <section>
                <SectionHeading title={content.chineseTitle} />
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                    {content.chinesePairs.map(([word, reading, meaning, warning]) => (
                        <article key={word} className="rounded-2xl border border-amber-100 bg-amber-50 p-4">
                            <button type="button" onClick={() => audio.play(word)} className="flex w-full items-center justify-between text-2xl font-black text-slate-900"><span>{word}</span><Volume2 size={16} className="text-amber-500" /></button>
                            <p className="mt-2 text-sm font-black text-rose-500">{reading}</p>
                            <p className="mt-2 text-sm font-black text-amber-950">{meaning}</p>
                            <p className="mt-2 border-t border-amber-200 pt-2 text-xs font-medium leading-5 text-amber-700">{warning}</p>
                        </article>
                    ))}
                </div>
            </section>

            <section>
                <SectionHeading title={content.methodTitle} />
                <div className="grid gap-4 lg:grid-cols-4">
                    {content.methodSteps.map(([number, title, body]) => (
                        <article key={number} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                            <span className="text-3xl font-black text-indigo-200">{number}</span>
                            <h3 className="mt-3 font-black text-slate-900">{title}</h3>
                            <p className="mt-2 text-sm font-medium leading-6 text-slate-500">{body}</p>
                        </article>
                    ))}
                </div>
            </section>

            <LearningNote title={content.cautionTitle} tone="indigo">{content.caution}</LearningNote>

            <section>
                <SectionHeading eyebrow={copy.common.quiz} title={content.quizTitle} body={content.quizHelp} />
                <KanjiQuiz copy={copy} audio={audio} />
            </section>
        </FoundationLayout>
    );
}
