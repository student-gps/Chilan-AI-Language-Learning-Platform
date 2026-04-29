import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const STROKE_NAMES  = ['横 héng', '竖 shù', '撇 piě', '捺 nà', '点 diǎn', '折 zhé'];
const STROKE_LABELS = ['一', '丨', '丿', '㇏', '丶', '乛'];
const STROKE_EXAMPLES = ['王 王 土', '中 木 井', '人 八 千', '人 大 木', '心 六 主', '口 女 山'];

const RADICAL_CHARS = ['氵', '木', '口', '人 / 亻', '心 / 忄', '言 / 讠'];

const STRUCT_CHARS = [
    [
        { char: '好', pinyin: 'hǎo' },
        { char: '明', pinyin: 'míng' },
        { char: '请', pinyin: 'qǐng' },
    ],
    [
        { char: '字', pinyin: 'zì' },
        { char: '思', pinyin: 'sī' },
        { char: '男', pinyin: 'nán' },
    ],
    [
        { char: '国', pinyin: 'guó' },
        { char: '问', pinyin: 'wèn' },
        { char: '园', pinyin: 'yuán' },
    ],
    [
        { char: '山', pinyin: 'shān' },
        { char: '日', pinyin: 'rì' },
        { char: '木', pinyin: 'mù' },
    ],
];

export default function HanziIntroPage() {
    const { t } = useTranslation();
    const navigate = useNavigate();
    const location = useLocation();
    const fromPath = location.state?.from || '/classroom';

    return (
        <div className="min-h-screen bg-slate-50 pt-16">
            <button
                onClick={() => navigate(fromPath)}
                className="fixed bottom-6 left-6 z-50 flex items-center gap-2 rounded-full bg-white px-5 py-3 text-base font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200 transition hover:bg-slate-50 hover:shadow-xl hover:ring-blue-300 active:scale-95"
            >
                <ChevronLeft size={18} />
                <span>{t('hi_back')}</span>
            </button>

            <div className="max-w-3xl mx-auto px-5 py-12 space-y-16">

                {/* Hero */}
                <section className="space-y-4">
                    <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-50 border border-indigo-100 text-sm font-black text-indigo-500 uppercase tracking-widest">
                        {t('hi_badge')}
                    </div>
                    <h1 className="text-5xl font-black text-slate-900 tracking-tight leading-tight">
                        {t('hi_h1')}
                    </h1>
                    <p className="text-lg text-slate-500 leading-relaxed max-w-xl">
                        {t('hi_subtitle')}
                    </p>
                    <div className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 text-sm font-semibold text-slate-500">
                        <span>📖</span> {t('hi_reading_only')}
                    </div>
                </section>

                {/* What is a Chinese character? */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-4">{t('hi_what_h2')}</h2>
                    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-6 py-5 space-y-4 text-slate-600 leading-relaxed">
                        <p dangerouslySetInnerHTML={{ __html: t('hi_what_p1') }} />
                        <p dangerouslySetInnerHTML={{ __html: t('hi_what_p2') }} />
                        <p dangerouslySetInnerHTML={{ __html: t('hi_what_p3') }} />
                    </div>
                </section>

                {/* Basic strokes */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">{t('hi_strokes_h2')}</h2>
                    <p className="text-slate-500 text-sm mb-5">{t('hi_strokes_intro')}</p>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        {STROKE_NAMES.map((name, i) => (
                            <div key={name} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-4 py-4">
                                <div className="text-4xl font-bold text-indigo-600 mb-2 leading-none">{STROKE_LABELS[i]}</div>
                                <p className="font-black text-slate-800 text-sm">{name}</p>
                                <p className="text-xs text-slate-500 mt-1">{t(`hi_stroke${i}_desc`)}</p>
                                <p className="text-xs text-slate-400 mt-2 font-mono">{STROKE_EXAMPLES[i]}</p>
                            </div>
                        ))}
                    </div>
                    <p className="text-xs text-slate-400 mt-3">{t('hi_strokes_note')}</p>
                </section>

                {/* Radicals */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">{t('hi_radicals_h2')}</h2>
                    <p
                        className="text-slate-500 text-sm mb-5"
                        dangerouslySetInnerHTML={{ __html: t('hi_radicals_intro') }}
                    />
                    <div className="space-y-3">
                        {RADICAL_CHARS.map((radical, i) => (
                            <div key={radical} className="flex gap-5 bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-4 items-start">
                                <div className="shrink-0 text-5xl font-bold text-indigo-600 leading-none w-14 text-center pt-1">{radical}</div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex flex-wrap items-baseline gap-2 mb-1">
                                        <span className="font-black text-slate-800">{t(`hi_rad${i}_meaning`)}</span>
                                        <span className="text-xs text-slate-400 italic">({t(`hi_rad${i}_hint`)})</span>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {t(`hi_rad${i}_ex`).split(' · ').map(ex => (
                                            <span key={ex} className="px-2.5 py-1 bg-indigo-50 rounded-lg text-xs font-semibold text-indigo-700">{ex}</span>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                    <div
                        className="mt-4 bg-blue-50 border border-blue-100 rounded-2xl px-5 py-4 text-sm text-blue-700 leading-relaxed"
                        dangerouslySetInnerHTML={{ __html: t('hi_radicals_tip') }}
                    />
                </section>

                {/* Character structure */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-2">{t('hi_struct_h2')}</h2>
                    <p className="text-slate-500 text-sm mb-5">{t('hi_struct_intro')}</p>
                    <div className="space-y-5">
                        {STRUCT_CHARS.map((examples, si) => (
                            <div key={si} className="bg-white rounded-2xl border border-slate-100 shadow-sm px-5 py-5">
                                <p className="font-black text-slate-800 text-lg mb-1">{t(`hi_struct${si}_type`)}</p>
                                <p className="text-sm text-slate-500 mb-4">{t(`hi_struct${si}_desc`)}</p>
                                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                                    {examples.map((ex, ei) => (
                                        <div key={ex.char} className="flex items-center gap-3 bg-slate-50 rounded-xl px-3 py-3">
                                            <span className="text-4xl font-bold text-slate-800 leading-none shrink-0">{ex.char}</span>
                                            <div>
                                                <p className="font-mono text-xs text-indigo-600">{ex.pinyin}</p>
                                                <p className="text-xs font-semibold text-slate-700">{t(`hi_struct${si}_ex${ei}_m`)}</p>
                                                <p className="text-[11px] text-slate-400 mt-0.5">{t(`hi_struct${si}_ex${ei}_b`)}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Typing */}
                <section>
                    <h2 className="text-2xl font-black text-slate-900 mb-4">{t('hi_typing_h2')}</h2>
                    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-6 py-5 space-y-4 text-slate-600 leading-relaxed">
                        <p dangerouslySetInnerHTML={{ __html: t('hi_typing_p1') }} />
                        <p dangerouslySetInnerHTML={{ __html: t('hi_typing_p2') }} />
                        <p dangerouslySetInnerHTML={{ __html: t('hi_typing_p3') }} />
                    </div>
                </section>

                {/* CTA */}
                <section className="text-center pb-8">
                    <p className="text-slate-500 text-sm mb-5">{t('hi_cta_text')}</p>
                    <button
                        onClick={() => navigate('/learn/pinyin', { state: { from: '/learn/hanzi' } })}
                        className="inline-flex items-center gap-2 px-7 py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-black rounded-2xl transition-all shadow-sm text-lg"
                    >
                        {t('hi_cta_btn')} <ChevronRight size={20} />
                    </button>
                </section>

            </div>
        </div>
    );
}
