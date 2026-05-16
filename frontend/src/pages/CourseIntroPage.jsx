import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Sparkles, Keyboard, Headphones, MessageSquare, BrainCircuit, BarChart3 } from 'lucide-react';
import CourseIntroVideo from '../videoTemplates/courseIntro/CourseIntroVideo';
import IntroFloatingNav from './introNavigation';

const FEAT_ICONS = [
    { icon: <Sparkles size={22} className="text-blue-500" />,   bg: 'bg-blue-50' },
    { icon: <Headphones size={22} className="text-emerald-500" />, bg: 'bg-emerald-50' },
    { icon: <MessageSquare size={22} className="text-orange-500" />, bg: 'bg-orange-50' },
    { icon: <Keyboard size={22} className="text-violet-500" />,  bg: 'bg-violet-50' },
    { icon: <BrainCircuit size={22} className="text-rose-500" />, bg: 'bg-rose-50' },
    { icon: <BarChart3 size={22} className="text-cyan-500" />,   bg: 'bg-cyan-50' },
];

const STEP_COLORS = ['bg-blue-500', 'bg-violet-500', 'bg-rose-500', 'bg-emerald-500'];

export default function CourseIntroPage() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const location = useLocation();

    const FEATURES = FEAT_ICONS.map((f, i) => ({
        ...f,
        title: t(`ci_feat${i}_title`),
        desc:  t(`ci_feat${i}_desc`),
    }));

    const STEPS = STEP_COLORS.map((color, i) => ({
        n: String(i + 1),
        color,
        title: t(`ci_step${i}_title`),
        desc:  t(`ci_step${i}_desc`),
    }));

    return (
        <div className="min-h-screen bg-slate-50 pt-16">
            <IntroFloatingNav
                currentPath="/learn/intro"
                locationState={location.state}
                navigate={navigate}
                t={t}
            />

            {/* Hero + Video */}
            <div className="bg-slate-900 pb-16 pt-12">
                <div className="max-w-6xl mx-auto px-6">
                    <div className="flex items-center gap-2 mb-5">
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-500/15 border border-blue-400/30 text-sm font-black text-blue-400 uppercase tracking-widest">
                            <Sparkles size={13} /> {t('ci_badge')}
                        </div>
                    </div>
                    <h1 className="text-5xl sm:text-6xl font-black text-white leading-tight tracking-tight mb-4">
                        {t('ci_h1_line1')}<br />
                        <span className="text-yellow-400">{t('ci_h1_line2')}</span>
                    </h1>
                    <p className="text-lg text-slate-400 max-w-2xl mb-10 leading-relaxed">
                        {t('ci_subtitle')}
                    </p>
                    <div className="w-full">
                        <CourseIntroVideo />
                    </div>
                </div>
            </div>

            <div className="max-w-6xl mx-auto px-6 py-16 space-y-20">

                {/* What makes this different */}
                <section>
                    <h2 className="text-3xl font-black text-slate-900 mb-8">{t('ci_diff_heading')}</h2>
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
                        <p className="font-black text-amber-800 mb-1">{t('ci_no_hw_title')}</p>
                        <p
                            className="text-sm text-amber-700 leading-relaxed"
                            dangerouslySetInnerHTML={{ __html: t('ci_no_hw_body') }}
                        />
                    </div>
                </section>

                {/* How each lesson works */}
                <section>
                    <h2 className="text-3xl font-black text-slate-900 mb-8">{t('ci_how_heading')}</h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        {STEPS.map((step) => (
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

            </div>
        </div>
    );
}
