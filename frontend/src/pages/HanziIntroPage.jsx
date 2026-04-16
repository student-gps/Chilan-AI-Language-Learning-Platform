import { useNavigate, useLocation } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';

// ─────────────────────────────────────────────────────────────────────────────
// DATA
// ─────────────────────────────────────────────────────────────────────────────

const STROKES = [
    { name: '横 héng', label: '一', desc: 'Horizontal — left to right', example: '王 王 土' },
    { name: '竖 shù',  label: '丨', desc: 'Vertical — top to bottom', example: '中 木 井' },
    { name: '撇 piě',  label: '丿', desc: 'Left-falling sweep', example: '人 八 千' },
    { name: '捺 nà',   label: '㇏', desc: 'Right-falling press', example: '人 大 木' },
    { name: '点 diǎn', label: '丶', desc: 'Dot', example: '心 六 主' },
    { name: '折 zhé',  label: '乛', desc: 'Turn / bend (includes hooks)', example: '口 女 山' },
];

const RADICALS = [
    { radical: '氵', meaning: 'water', hint: 'three dots on the left', examples: ['河 river', '海 sea', '洗 wash'] },
    { radical: '木', meaning: 'wood / tree', hint: 'standalone or as 木 on left', examples: ['树 tree', '林 forest', '桌 table'] },
    { radical: '口', meaning: 'mouth', hint: 'small box shape', examples: ['吃 eat', '喝 drink', '说 speak'] },
    { radical: '人 / 亻', meaning: 'person', hint: 'standing figure or side radical', examples: ['他 he', '你 you', '做 do'] },
    { radical: '心 / 忄', meaning: 'heart / mind', hint: 'standalone or three dots on left', examples: ['想 think', '忘 forget', '情 emotion'] },
    { radical: '言 / 讠', meaning: 'speech / words', hint: 'simplified to two dots + stroke on left', examples: ['说 speak', '话 words', '读 read'] },
];

const STRUCTURES = [
    {
        type: 'Left–right  左右',
        desc: 'Two or more components placed side by side. The most common structure in Chinese.',
        examples: [
            { char: '好', breakdown: '女 (woman) + 子 (child)', pinyin: 'hǎo', meaning: 'good' },
            { char: '明', breakdown: '日 (sun) + 月 (moon)', pinyin: 'míng', meaning: 'bright' },
            { char: '请', breakdown: '讠(speech) + 青 (blue/clear)', pinyin: 'qǐng', meaning: 'please / invite' },
        ],
    },
    {
        type: 'Top–bottom  上下',
        desc: 'One component stacked on top of another.',
        examples: [
            { char: '字', breakdown: '宀 (roof) + 子 (child)', pinyin: 'zì', meaning: 'character / word' },
            { char: '思', breakdown: '田 (field) + 心 (heart)', pinyin: 'sī', meaning: 'to think' },
            { char: '男', breakdown: '田 (field) + 力 (strength)', pinyin: 'nán', meaning: 'male' },
        ],
    },
    {
        type: 'Enclosure  包围',
        desc: 'One component wraps around another — fully or on three sides.',
        examples: [
            { char: '国', breakdown: '囗 (border) + 玉 (jade)', pinyin: 'guó', meaning: 'country' },
            { char: '问', breakdown: '门 (door) + 口 (mouth)', pinyin: 'wèn', meaning: 'to ask' },
            { char: '园', breakdown: '囗 (border) + 元', pinyin: 'yuán', meaning: 'garden' },
        ],
    },
    {
        type: 'Single unit  独体',
        desc: 'A single, indivisible character — often a pictograph from ancient Chinese.',
        examples: [
            { char: '山', breakdown: 'Three peaks — mountain shape', pinyin: 'shān', meaning: 'mountain' },
            { char: '日', breakdown: 'Circle with a line — the sun', pinyin: 'rì', meaning: 'sun / day' },
            { char: '木', breakdown: 'Tree with roots and branches', pinyin: 'mù', meaning: 'wood / tree' },
        ],
    },
];

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT
// ─────────────────────────────────────────────────────────────────────────────

export default function HanziIntroPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const fromPath = location.state?.from || '/classroom';

    return (
        <div className="min-h-screen bg-slate-50 pt-16">
            {/* Back button */}
            <button
                onClick={() => navigate(fromPath)}
                className="fixed bottom-6 left-6 z-50 flex items-center gap-2 rounded-full bg-white px-5 py-3 text-base font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200 transition hover:bg-slate-50 hover:shadow-xl hover:ring-blue-300 active:scale-95"
            >
                <ChevronLeft size={18} />
                <span>Back</span>
            </button>

            <div className="max-w-3xl mx-auto px-5 py-12 space-y-16">

                {/* ── Hero ── */}
                <section className="space-y-4">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100 text-sm font-black text-indigo-500 uppercase tracking-widest">
                        Foundation · 基础
                    </div>
                    <h1 className="text-5xl font-black text-slate-900 tracking-tight leading-tight">
                        Chinese Characters
                    </h1>
                    <p className="text-lg text-slate-500 leading-relaxed max-w-xl">
                        Before diving into vocabulary, it helps to understand what Chinese characters
                        are and how they're built. This is a conceptual overview — no memorisation required.
                    </p>
                    {/* No-quiz note */}
                    <div className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 text-sm font-semibold text-slate-500">
                        <span>📖</span> Reading only — no practice questions here
                    </div>
                </section>

                {/* ── What is a Chinese character? ── */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-4">What is a Chinese character?</h2>
                    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-6 py-5 space-y-4 text-slate-600 leading-relaxed">
                        <p>
                            Each Chinese character is a <strong className="text-slate-800">logogram</strong> — a written symbol that represents
                            a morpheme (a unit of meaning and sound), not just a sound.
                            The character <span className="font-mono text-2xl text-indigo-600 align-middle">山</span> means <em>mountain</em> and is pronounced <em>shān</em>.
                            Both the meaning and the sound are tied to that single symbol.
                        </p>
                        <p>
                            Modern Mandarin uses roughly <strong className="text-slate-800">3,000–4,000 characters</strong> for everyday literacy.
                            HSK 6 (advanced) covers around 5,000. The good news: most characters are made of
                            smaller recurring pieces, so patterns emerge quickly.
                        </p>
                        <p>
                            Unlike alphabetic scripts, Chinese has no uppercase or lowercase, no spaces between words,
                            and characters don't tell you their pronunciation directly —
                            that's what <strong className="text-slate-800">pinyin</strong> is for.
                        </p>
                    </div>
                </section>

                {/* ── Basic strokes ── */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">Basic strokes</h2>
                    <p className="text-slate-500 text-sm mb-5">
                        Every character is built from a small set of fundamental brush strokes.
                        There are about 6–8 basic types; everything else is a variant or combination.
                    </p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        {STROKES.map((s) => (
                            <div key={s.name} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-4">
                                <div className="text-4xl font-bold text-indigo-600 mb-2 leading-none">{s.label}</div>
                                <p className="font-black text-slate-800 text-sm">{s.name}</p>
                                <p className="text-xs text-slate-500 mt-1">{s.desc}</p>
                                <p className="text-xs text-slate-400 mt-2 font-mono">{s.example}</p>
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-slate-400 mt-3">
                        We don't teach stroke order in this course, but knowing these names helps when you look characters up in a dictionary.
                    </p>
                </section>

                {/* ── Radicals ── */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">Radicals (部首 bùshǒu)</h2>
                    <p className="text-slate-500 text-sm mb-5">
                        Radicals are recurring components that often hint at a character's <strong>category of meaning</strong>.
                        Dictionaries are traditionally organized by radical. Recognizing them makes new characters easier to guess and remember.
                    </p>
                    <div className="space-y-3">
                        {RADICALS.map((r) => (
                            <div key={r.radical} className="flex gap-5 bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 items-start">
                                <div className="shrink-0 text-5xl font-bold text-indigo-600 leading-none w-14 text-center pt-1">{r.radical}</div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex flex-wrap items-baseline gap-2 mb-1">
                                        <span className="font-black text-slate-800">{r.meaning}</span>
                                        <span className="text-xs text-slate-400 italic">({r.hint})</span>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {r.examples.map((ex) => (
                                            <span key={ex} className="px-2.5 py-1 bg-indigo-50 rounded-lg text-xs font-semibold text-indigo-700">{ex}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="mt-4 bg-blue-50 border border-blue-100 rounded-2xl px-5 py-4 text-sm text-blue-700 leading-relaxed">
                        <strong>Tip:</strong> Radicals don't always predict pronunciation, and one character can have multiple components.
                        Think of them as rough semantic hints, not strict rules.
                    </div>
                </section>

                {/* ── Character structure ── */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">How characters are structured</h2>
                    <p className="text-slate-500 text-sm mb-5">
                        Characters combine components in predictable spatial arrangements.
                        Once you see the pattern, you start to "read" the shape of new characters at a glance.
                    </p>
                    <div className="space-y-5">
                        {STRUCTURES.map((s) => (
                            <div key={s.type} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-5">
                                <p className="font-black text-slate-800 text-lg mb-1">{s.type}</p>
                                <p className="text-sm text-slate-500 mb-4">{s.desc}</p>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                    {s.examples.map((ex) => (
                                        <div key={ex.char} className="flex items-center gap-3 bg-slate-50 rounded-xl px-3 py-3">
                                            <span className="text-4xl font-bold text-slate-800 leading-none shrink-0">{ex.char}</span>
                                            <div>
                                                <p className="font-mono text-xs text-indigo-600">{ex.pinyin}</p>
                                                <p className="text-xs font-semibold text-slate-700">{ex.meaning}</p>
                                                <p className="text-[11px] text-slate-400 mt-0.5">{ex.breakdown}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* ── Typing vs handwriting ── */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-4">Typing Chinese characters</h2>
                    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-6 py-5 space-y-4 text-slate-600 leading-relaxed">
                        <p>
                            In this course, you type Chinese using a <strong className="text-slate-800">pinyin IME</strong> (Input Method Editor)
                            — the same method virtually all native speakers use on phones and computers.
                            You type the romanised pronunciation, and the IME offers matching characters to pick from.
                        </p>
                        <p>
                            For example, typing <span className="font-mono text-indigo-600">hao</span> and selecting the right character gives you <span className="text-2xl font-bold text-slate-800 align-middle">好</span>.
                            You don't need to know how to draw the character to produce it digitally.
                        </p>
                        <p>
                            This is why <strong className="text-slate-800">pinyin mastery comes first</strong>: accurate typing
                            depends on knowing how each character is pronounced.
                        </p>
                    </div>
                </section>

                {/* ── Next step ── */}
                <section className="text-center pb-8">
                    <p className="text-slate-500 text-sm mb-5">
                        Now that you have a mental model of Chinese characters, you're ready for the sound system.
                    </p>
                    <button
                        onClick={() => navigate('/learn/pinyin', { state: { from: '/learn/hanzi' } })}
                        className="inline-flex items-center gap-2 px-7 py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-2xl transition-all shadow-sm text-lg"
                    >
                        Continue to Pinyin <ChevronRight size={20} />
                    </button>
                </section>

            </div>
        </div>
    );
}
