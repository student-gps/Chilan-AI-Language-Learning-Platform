import { BrainCircuit, Headphones, Keyboard, MessageCircle, Repeat2, ScanText } from 'lucide-react';
import JapaneseCourseIntroVideo from '../../videoTemplates/courseIntro/JapaneseCourseIntroVideo';
import FoundationLayout, { LearningNote, SectionHeading } from './FoundationLayout';

const PRINCIPLE_ICONS = [Headphones, MessageCircle, ScanText, BrainCircuit, Repeat2, Keyboard];
const SCRIPT_TONES = [
    'border-rose-100 bg-gradient-to-br from-rose-50 to-white text-rose-600',
    'border-sky-100 bg-gradient-to-br from-sky-50 to-white text-sky-600',
    'border-indigo-100 bg-gradient-to-br from-indigo-50 to-white text-indigo-600',
];

export default function JapaneseCourseIntro(props) {
    const { copy, supportLanguage } = props;
    const content = copy.intro;

    return (
        <FoundationLayout {...props} moduleCopy={content} icon="日" tone="amber">
            <section aria-label={content.slidesAriaLabel}>
                <JapaneseCourseIntroVideo supportLanguage={supportLanguage} />
            </section>

            <section>
                <SectionHeading title={content.scriptTitle} />
                <div className="grid gap-5 lg:grid-cols-3">
                    {content.scripts.map((script, index) => (
                        <article key={script.title} className={`rounded-3xl border p-6 shadow-sm ${SCRIPT_TONES[index]}`}>
                            <div className="flex items-start justify-between gap-4">
                                <span className="text-6xl font-black leading-none">{script.glyph}</span>
                                <span className="rounded-full bg-white px-3 py-1 text-[10px] font-black uppercase tracking-[0.16em] text-slate-500 shadow-sm">{script.tag}</span>
                            </div>
                            <h3 className="mt-5 text-xl font-black text-slate-900">{script.title}</h3>
                            <p className="mt-2 text-sm font-medium leading-7 text-slate-600">{script.body}</p>
                            <p className="mt-5 rounded-2xl bg-white/90 px-4 py-3 text-lg font-black text-slate-800 ring-1 ring-slate-100">{script.example}</p>
                        </article>
                    ))}
                </div>
            </section>

            <section>
                <SectionHeading title={content.principlesTitle} />
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {content.principles.map((item, index) => {
                        const Icon = PRINCIPLE_ICONS[index];
                        return (
                            <article key={item.title} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white">
                                    <Icon size={19} />
                                </div>
                                <h3 className="mt-4 font-black text-slate-900">{item.title}</h3>
                                <p className="mt-2 text-sm font-medium leading-6 text-slate-500">{item.body}</p>
                            </article>
                        );
                    })}
                </div>
            </section>

            <section className="rounded-[2rem] bg-slate-950 p-6 text-white shadow-xl sm:p-8">
                <h2 className="mb-7 text-2xl font-black tracking-tight text-white sm:text-3xl">{content.lessonTitle}</h2>
                <div className="grid gap-4 md:grid-cols-2">
                    {content.lessonSteps.map(([number, title, body]) => (
                        <article key={number} className="flex gap-4 rounded-2xl border border-white/10 bg-white/5 p-5">
                            <span className="text-2xl font-black text-amber-300">{number}</span>
                            <div>
                                <h3 className="font-black text-white">{title}</h3>
                                <p className="mt-1 text-sm font-medium leading-6 text-slate-400">{body}</p>
                            </div>
                        </article>
                    ))}
                </div>
            </section>

            <section>
                <SectionHeading title={content.scopeTitle} />
                <div className="relative grid gap-4 lg:grid-cols-4">
                    {content.scope.map(([number, title, body], index) => (
                        <article key={number} className="relative rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                            {index < content.scope.length - 1 && <span className="absolute -right-3 top-8 z-10 hidden text-slate-200 lg:block">→</span>}
                            <span className="text-xs font-black uppercase tracking-[0.2em] text-rose-400">{copy.common.step} {number}</span>
                            <h3 className="mt-2 text-lg font-black text-slate-900">{title}</h3>
                            <p className="mt-2 text-sm font-medium leading-6 text-slate-500">{body}</p>
                        </article>
                    ))}
                </div>
            </section>

            <LearningNote title={content.noteTitle} tone="amber">{content.note}</LearningNote>
        </FoundationLayout>
    );
}
