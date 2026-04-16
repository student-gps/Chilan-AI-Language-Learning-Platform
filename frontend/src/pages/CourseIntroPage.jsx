import { useNavigate, useLocation } from 'react-router-dom';
import { ChevronLeft, ChevronRight, Sparkles, Keyboard, Headphones, MessageSquare, BookOpen, BrainCircuit, BarChart3 } from 'lucide-react';
import CourseIntroVideo from '../videoTemplates/courseIntro/CourseIntroVideo';

const FEATURES = [
    {
        icon: <Sparkles size={22} className="text-blue-500" />,
        bg: 'bg-blue-50',
        title: 'AI-powered feedback',
        desc: 'Three-tier evaluation — instant regex check, semantic similarity, then deep LLM analysis. Honest, nuanced feedback on every answer.',
    },
    {
        icon: <Headphones size={22} className="text-emerald-500" />,
        bg: 'bg-emerald-50',
        title: 'Listening first',
        desc: 'Audio for every word and sentence. Dictation exercises train your ear to hear tones and sounds.',
    },
    {
        icon: <MessageSquare size={22} className="text-orange-500" />,
        bg: 'bg-orange-50',
        title: 'Speaking practice',
        desc: 'Speak your answers aloud. Speech recognition + AI checks your meaning — not just pronunciation.',
    },
    {
        icon: <Keyboard size={22} className="text-violet-500" />,
        bg: 'bg-violet-50',
        title: 'Keyboard input focus',
        desc: 'Learn to type Chinese with a standard pinyin IME — the way native speakers write every day. No handwriting required.',
    },
    {
        icon: <BrainCircuit size={22} className="text-rose-500" />,
        bg: 'bg-rose-50',
        title: 'Spaced repetition (FSRS)',
        desc: 'Every question is scheduled by FSRS. Items you know well come back less often; tricky ones reappear sooner.',
    },
    {
        icon: <BarChart3 size={22} className="text-cyan-500" />,
        bg: 'bg-cyan-50',
        title: 'Progress you can see',
        desc: 'Your classroom tracks reviewed, remaining, and mastered items. Every session moves the needle.',
    },
];

export default function CourseIntroPage() {
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

            {/* ── Hero + Video ── */}
            <div className="bg-slate-900 pb-16 pt-12">
                <div className="max-w-6xl mx-auto px-6">
                    {/* Eyebrow */}
                    <div className="flex items-center gap-2 mb-5">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/15 border border-blue-400/30 text-sm font-black text-blue-400 uppercase tracking-widest">
                            <Sparkles size={13} /> Chilan · Chinese
                        </div>
                    </div>
                    <h1 className="text-5xl sm:text-6xl font-black text-white leading-tight tracking-tight mb-4">
                        Learn Chinese<br />
                        <span className="text-yellow-400">the way it's actually used</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mb-10 leading-relaxed">
                        An AI-powered course that builds real communication skills — listening, speaking, and typing — starting from first principles.
                    </p>

                    {/* Video player */}
                    <div className="w-full">
                        <CourseIntroVideo />
                    </div>
                </div>
            </div>

            {/* ── Rest of content ── */}
            <div className="max-w-6xl mx-auto px-6 py-16 space-y-20">

                {/* What makes this different */}
                <section>
                    <h2 className="text-3xl font-black text-slate-900 mb-8">What makes this different</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                        {FEATURES.map((f) => (
                            <div key={f.title} className="flex gap-4 bg-white rounded-2xl border border-slate-100 shadow-sm p-5">
                                <div className={`shrink-0 w-10 h-10 rounded-xl ${f.bg} flex items-center justify-center`}>
                                    {f.icon}
                                </div>
                                <div>
                                    <p className="font-black text-slate-800 mb-1">{f.title}</p>
                                    <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* No handwriting note */}
                <section className="bg-amber-50 border border-amber-100 rounded-2xl px-6 py-5 flex gap-4">
                    <span className="text-2xl shrink-0">✏️</span>
                    <div>
                        <p className="font-black text-amber-800 mb-1">We don't teach handwriting</p>
                        <p className="text-sm text-amber-700 leading-relaxed">
                            Stroke order and handwriting are genuinely important, but they're a separate skill that takes years of dedicated practice.
                            This course focuses entirely on <strong>reading, listening, speaking, and typing with a pinyin IME</strong> —
                            the skills most learners need first.
                        </p>
                    </div>
                </section>

                {/* How each lesson works */}
                <section>
                    <h2 className="text-3xl font-black text-slate-900 mb-8">How each lesson works</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {[
                            { n: '1', title: 'Teaching phase', desc: 'New words with pinyin, translation, audio, and an optional video explanation. No timer — take your time.', color: 'bg-blue-500' },
                            { n: '2', title: 'Practice phase', desc: 'Four question types: translate to English, translate to Chinese, speak aloud, or write from audio dictation.', color: 'bg-violet-500' },
                            { n: '3', title: 'AI evaluation', desc: 'Three-tier check — exact match, semantic similarity, then full LLM judgment with explanation for edge cases.', color: 'bg-rose-500' },
                            { n: '4', title: 'FSRS scheduling', desc: 'Based on your result, FSRS calculates exactly when to show this item again — hours, days, or weeks.', color: 'bg-emerald-500' },
                        ].map((step) => (
                            <div key={step.n} className="flex gap-4 bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-5">
                                <div className={`shrink-0 w-9 h-9 rounded-full ${step.color} text-white text-sm font-black flex items-center justify-center mt-0.5`}>
                                    {step.n}
                                </div>
                                <div>
                                    <p className="font-black text-slate-800">{step.title}</p>
                                    <p className="text-sm text-slate-500 mt-1 leading-relaxed">{step.desc}</p>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* CTA */}
                <section className="text-center pb-8">
                    <p className="text-slate-500 text-sm mb-5">Ready to start? Begin with the foundation modules.</p>
                    <div className="flex flex-wrap gap-3 justify-center">
                        <button
                            onClick={() => navigate('/learn/hanzi', { state: { from: '/learn/intro' } })}
                            className="flex items-center gap-2 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-black rounded-2xl transition-all shadow-sm"
                        >
                            <BookOpen size={18} /> Chinese Characters →
                        </button>
                        <button
                            onClick={() => navigate('/learn/pinyin', { state: { from: '/learn/intro' } })}
                            className="flex items-center gap-2 px-6 py-3 bg-white hover:bg-slate-50 text-slate-700 font-black rounded-2xl border border-slate-200 transition-all shadow-sm"
                        >
                            Pinyin <ChevronRight size={16} />
                        </button>
                    </div>
                </section>
            </div>
        </div>
    );
}
