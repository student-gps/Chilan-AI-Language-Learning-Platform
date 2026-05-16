import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { BookOpenText, Grid3X3, Layers3, PenLine, Shapes } from 'lucide-react';
import IntroFloatingNav from './introNavigation';

const SKETCH_CLASS = 'relative h-14 w-14 shrink-0 rounded-xl border-2 border-slate-300 bg-white';
const HANZI_FONT = '"STKaiti", "KaiTi", "KaiTi SC", "Songti SC", "Noto Serif CJK SC", serif';

function SectionHeader({ icon, eyebrow, title, body }) {
    return (
        <div className="mb-6">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1.5 text-sm font-black uppercase tracking-widest text-indigo-600">
                {icon}
                {eyebrow}
            </div>
            <h2 className="text-4xl font-black tracking-tight text-slate-900">{title}</h2>
            <p className="mt-3 max-w-3xl text-base font-medium leading-relaxed text-slate-500">{body}</p>
        </div>
    );
}

function StructureSketch({ type }) {
    return (
        <div className={SKETCH_CLASS}>
            {type === 'leftRight' && <div className="absolute left-1/2 top-0 h-full w-0.5 -translate-x-1/2 bg-slate-300" />}
            {type === 'topBottom' && <div className="absolute left-0 top-1/2 h-0.5 w-full -translate-y-1/2 bg-slate-300" />}
            {type === 'semiEnclosing' && (
                <>
                    <div className="absolute left-2 top-2 h-9 w-0.5 bg-slate-300" />
                    <div className="absolute left-2 top-2 h-0.5 w-9 bg-slate-300" />
                </>
            )}
            {type === 'enclosing' && <div className="absolute inset-3 rounded-md border-2 border-slate-300" />}
            {type === 'horizontalTrisection' && (
                <>
                    <div className="absolute left-1/3 top-0 h-full w-0.5 -translate-x-1/2 bg-slate-300" />
                    <div className="absolute left-2/3 top-0 h-full w-0.5 -translate-x-1/2 bg-slate-300" />
                </>
            )}
            {type === 'verticalTrisection' && (
                <>
                    <div className="absolute left-0 top-1/3 h-0.5 w-full -translate-y-1/2 bg-slate-300" />
                    <div className="absolute left-0 top-2/3 h-0.5 w-full -translate-y-1/2 bg-slate-300" />
                </>
            )}
            {type === 'leftBottomEnclosing' && (
                <>
                    <div className="absolute bottom-2 left-2 h-0.5 w-10 bg-slate-300" />
                    <div className="absolute bottom-2 left-2 h-9 w-0.5 bg-slate-300" />
                </>
            )}
            {type === 'leftTopEnclosing' && (
                <>
                    <div className="absolute left-2 top-2 h-10 w-0.5 bg-slate-300" />
                    <div className="absolute left-2 top-2 h-0.5 w-10 bg-slate-300" />
                </>
            )}
        </div>
    );
}

function splitText(value) {
    return String(value || '').split(' · ').filter(Boolean);
}

function normalizeExample(example, glosses = {}) {
    if (example && typeof example === 'object') {
        return {
            char: example.char || '',
            pinyin: example.pinyin || '',
            meaning: example.meaning || glosses[example.char] || '',
        };
    }

    const [char, ...rest] = String(example || '').trim().split(/\s+/);
    return {
        char,
        pinyin: rest.join(' '),
        meaning: glosses[char] || '',
    };
}

function splitRadical(value) {
    const [main, variant] = String(value || '').split('/');
    return { main, variant };
}

function ExampleChip({ example, glosses, tone = 'indigo', compact = false }) {
    const item = normalizeExample(example, glosses);
    if (!item.char) return null;

    const shellClass = tone === 'slate'
        ? 'bg-slate-50 text-slate-700'
        : 'bg-indigo-50 text-indigo-700';
    const meaningClass = tone === 'slate' ? 'text-slate-500' : 'text-indigo-500';

    return (
        <span className={`inline-flex items-center gap-1.5 rounded-xl ${shellClass} ${compact ? 'px-2.5 py-1.5 text-sm' : 'px-3.5 py-2.5 text-base'} font-black`}>
            <span className={compact ? 'text-lg' : 'text-xl'} style={{ fontFamily: HANZI_FONT }}>{item.char}</span>
            {item.pinyin && <span>{item.pinyin}</span>}
            {item.meaning && (
                <>
                    <span className={meaningClass}>·</span>
                    <span className={meaningClass}>{item.meaning}</span>
                </>
            )}
        </span>
    );
}

function FormationBreakdowns({ item, glosses }) {
    if (!item.breakdowns?.length) return null;

    return (
        <div className="mt-4 space-y-2 rounded-2xl bg-slate-50 p-3">
            {item.breakdowns.map((breakdown) => (
                <div key={breakdown.result.char} className="flex flex-wrap items-center gap-2">
                    {breakdown.parts.map((part, index) => (
                        <span key={`${breakdown.result.char}-${part.char}`} className="inline-flex items-center gap-2">
                            <ExampleChip example={part} glosses={glosses} tone="slate" compact />
                            {index < breakdown.parts.length - 1 && <span className="text-sm font-black text-slate-300">+</span>}
                        </span>
                    ))}
                    <span className="text-sm font-black text-slate-300">→</span>
                    <ExampleChip example={breakdown.result} glosses={glosses} compact />
                </div>
            ))}
        </div>
    );
}

function RadicalMark({ value, compact = false }) {
    const { main, variant } = splitRadical(value);
    const boxClass = compact ? 'h-16 w-16 rounded-lg' : 'h-20 w-20 rounded-xl';
    const mainClass = variant
        ? compact ? 'text-3xl' : 'text-4xl'
        : compact ? 'text-4xl' : 'text-5xl';
    const variantClass = compact ? 'bottom-1 right-1 text-base' : 'bottom-1.5 right-1.5 text-xl';

    return (
        <div className={`relative flex ${boxClass} shrink-0 items-center justify-center overflow-hidden bg-slate-950 text-white shadow-inner`}>
            <div className="absolute inset-0 opacity-20">
                <div className="absolute left-1/2 top-0 h-full w-px bg-white/40" />
                <div className="absolute left-0 top-1/2 h-px w-full bg-white/40" />
            </div>
            <span
                className={`${mainClass} relative leading-none`}
                style={{ fontFamily: HANZI_FONT }}
            >
                {main}
            </span>
            {variant && (
                <span
                    className={`absolute ${variantClass} rounded-md bg-white px-1.5 py-0.5 font-black leading-none text-slate-950`}
                    style={{ fontFamily: HANZI_FONT }}
                >
                    {variant}
                </span>
            )}
        </div>
    );
}

function LearningModel({ model }) {
    if (!model) return null;

    return (
        <section className="mb-16">
            <div className="mb-4">
                <p className="text-sm font-black uppercase tracking-widest text-indigo-600">{model.eyebrow}</p>
                <h2 className="mt-2 text-3xl font-black text-slate-900">{model.title}</h2>
                <p className="mt-3 max-w-3xl text-base font-medium leading-relaxed text-slate-500">{model.body}</p>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
                {model.steps.map((step, index) => (
                    <div key={step.title} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                        <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-full bg-indigo-600 text-base font-black text-white">
                            {index + 1}
                        </div>
                        <p className="text-lg font-black text-slate-900">{step.title}</p>
                        <p className="mt-2 text-base font-medium leading-relaxed text-slate-500">{step.body}</p>
                    </div>
                ))}
            </div>
        </section>
    );
}

function FormationPriority({ priority }) {
    if (!priority) return null;
    const examples = priority.examples || [];

    return (
        <div className={`mt-4 grid gap-4 ${examples.length ? 'lg:grid-cols-[0.95fr_1.35fr]' : ''}`}>
            <div className="rounded-2xl bg-slate-950 p-5 text-white shadow-sm">
                <p className="text-xl font-black">{priority.title}</p>
                <p className="mt-3 text-base font-medium leading-relaxed text-slate-300">{priority.body}</p>
            </div>
            {examples.length > 0 && (
                <div className="grid gap-3 sm:grid-cols-3">
                    {examples.map((example) => (
                        <div key={example.char} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                            <div className="mb-3 text-5xl leading-none text-slate-950" style={{ fontFamily: HANZI_FONT }}>
                                {example.char}
                            </div>
                            <div className="space-y-1.5">
                                {example.parts.map((part) => (
                                    <p key={part} className="rounded-lg bg-slate-50 px-2.5 py-1 text-sm font-black text-slate-600">
                                        {part}
                                    </p>
                                ))}
                            </div>
                            <p className="mt-3 text-sm font-semibold leading-relaxed text-slate-400">{example.note}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

function StrokeMark({ item, index }) {
    return (
        <div className="relative mb-4 flex aspect-square w-full max-w-28 items-center justify-center overflow-hidden rounded-xl border border-amber-200/80 bg-[#fffaf0] shadow-inner">
            <div className="absolute inset-0">
                <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-amber-200" />
                <div className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 bg-amber-200" />
                <div className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 rotate-45 bg-amber-100" />
                <div className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 -rotate-45 bg-amber-100" />
            </div>
            <span
                className="relative -mt-1 text-6xl leading-none text-slate-950 drop-shadow-sm"
                style={{ fontFamily: HANZI_FONT }}
            >
                {item.mark}
            </span>
            <span className="absolute left-2 top-2 flex h-5 min-w-5 items-center justify-center rounded-full bg-indigo-600 px-1 text-[10px] font-black leading-none text-white shadow-sm">
                {index + 1}
            </span>
        </div>
    );
}

export default function HanziIntroPage() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const location = useLocation();
    const content = t('hanzi_intro', { returnObjects: true });

    return (
        <div className="min-h-screen bg-slate-50 pt-16">
            <IntroFloatingNav
                currentPath="/learn/hanzi"
                locationState={location.state}
                navigate={navigate}
                t={t}
            />

            <div className="mx-auto max-w-7xl px-4 py-12 pb-28 sm:px-5 lg:px-6">
                <section className="mb-12">
                    <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-4 py-2 text-base font-black uppercase tracking-widest text-indigo-600">
                        <BookOpenText size={16} />
                        {content.badge}
                    </div>
                    <h1 className="max-w-4xl text-6xl font-black leading-tight tracking-tight text-slate-900">
                        {content.title}
                    </h1>
                </section>

                <LearningModel model={content.studyModel} />

                <div className="space-y-16">
                    <section>
                        <SectionHeader
                            icon={<Shapes size={14} />}
                            eyebrow={content.formation.eyebrow}
                            title={content.formation.title}
                            body={content.formation.body}
                        />
                        <div className="grid gap-3 md:grid-cols-2">
                            {content.formation.types.map((item) => (
                                <div key={item.title} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                                    <div className="flex items-start justify-between gap-4">
                                        <div>
                                            <p className="text-lg font-black text-slate-900">{item.title}</p>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-5xl font-black leading-none text-indigo-600" style={{ fontFamily: HANZI_FONT }}>{item.glyph}</div>
                                            {item.glyphMeaning && (
                                                <p className="mt-2 text-base font-black text-indigo-500">{item.glyphMeaning}</p>
                                            )}
                                        </div>
                                    </div>
                                    <p className="mt-4 text-base font-medium leading-relaxed text-slate-500">{item.description}</p>
                                    <div className="mt-4 flex flex-wrap gap-2">
                                        {item.examples.map((example) => (
                                            <ExampleChip key={typeof example === 'object' ? example.char : example} example={example} glosses={content.glosses} />
                                        ))}
                                    </div>
                                    <FormationBreakdowns item={item} glosses={content.glosses} />
                                </div>
                            ))}
                        </div>
                        <FormationPriority priority={content.formation.priority} />
                    </section>

                    <section>
                        <SectionHeader
                            icon={<Layers3 size={14} />}
                            eyebrow={content.radicals.eyebrow}
                            title={content.radicals.title}
                            body={content.radicals.body}
                        />
                        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                            {content.radicals.items.map((item) => (
                                <div key={`${item.no}-${item.radical}`} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                                    <div className="mb-3 flex items-center gap-3">
                                        <RadicalMark value={item.radical} compact />
                                        <div className="min-w-0 flex-1">
                                            <p className="text-xl font-black text-slate-900">{item.meaning}</p>
                                            <p className="text-base font-black italic text-indigo-500">{item.pinyin}</p>
                                        </div>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {splitText(item.examples).map((example) => (
                                            <ExampleChip key={example} example={example} glosses={content.glosses} tone="slate" compact />
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section>
                        <SectionHeader
                            icon={<Grid3X3 size={14} />}
                            eyebrow={content.structures.eyebrow}
                            title={content.structures.title}
                            body={content.structures.body}
                        />
                        <div className="grid gap-3 md:grid-cols-3">
                            {content.structures.items.map((item) => (
                                <div key={item.type} className="rounded-2xl border border-slate-100 bg-white p-4 shadow-sm">
                                    <div className="mb-4 flex items-center gap-3">
                                        <StructureSketch type={item.sketch} />
                                        <div>
                                            <p className="text-lg font-black text-slate-900">{item.type}</p>
                                            <p className="text-sm font-semibold text-slate-400">{item.label}</p>
                                        </div>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {splitText(item.examples).map((example) => (
                                            <ExampleChip key={example} example={example} glosses={content.glosses} />
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section>
                        <SectionHeader
                            icon={<PenLine size={14} />}
                            eyebrow={content.strokes.eyebrow}
                            title={content.strokes.title}
                            body={content.strokes.body}
                        />
                        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                            {content.strokes.items.map((item, index) => (
                                <div key={item.name} className="rounded-2xl border border-slate-100 bg-white p-5 shadow-sm">
                                    <StrokeMark item={item} index={index} />
                                    <p className="text-xl font-black text-slate-900">{item.name}</p>
                                    <p className="mt-1 text-base font-medium text-slate-500">{item.description}</p>
                                    <div className="mt-4 flex flex-wrap gap-2">
                                        {splitText(item.examples).map((example) => (
                                            <ExampleChip key={example} example={example} glosses={content.glosses} tone="slate" compact />
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section>
                        <SectionHeader
                            icon={<PenLine size={14} />}
                            eyebrow={content.strokeOrder.eyebrow}
                            title={content.strokeOrder.title}
                            body={content.strokeOrder.body}
                        />
                        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                            {content.strokeOrder.rules.map((rule, index) => (
                                <div key={rule.title} className="flex items-center gap-4 rounded-2xl border border-slate-100 bg-white px-5 py-5 shadow-sm">
                                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-950 text-base font-black text-white shadow-sm">
                                        {index + 1}
                                    </div>
                                    <p className="text-xl font-black leading-tight text-slate-900">{rule.title}</p>
                                </div>
                            ))}
                        </div>
                    </section>

                    <section className="rounded-3xl bg-slate-900 px-6 py-7 text-white shadow-sm">
                        <h2 className="text-2xl font-black">{content.typing.title}</h2>
                        <div className="mt-4 space-y-3 text-base font-medium leading-relaxed text-slate-300">
                            <p dangerouslySetInnerHTML={{ __html: content.typing.p1 }} />
                            <p dangerouslySetInnerHTML={{ __html: content.typing.p2 }} />
                        </div>
                    </section>
                </div>
            </div>
        </div>
    );
}
