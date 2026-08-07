import { ChevronLeft, ChevronRight } from 'lucide-react';

const LEGACY_STEPS = [
    { path: '/learn/intro', label: (t) => t('ci_h1_line1') },
    { path: '/learn/hanzi', label: (t) => cleanLabel(t('ci_cta_hanzi')) },
    { path: '/learn/pinyin', label: (t) => t('ci_cta_pinyin') },
    { path: '/learn/typing', label: (t) => t('typing_intro_title') },
];

const cleanLabel = (text) => (text || '').replace('→', '').trim();

function navigateWithState(navigate, path, state) {
    navigate(path, state ? { state } : undefined);
}

function LegacyIntroNavigation({ currentPath, locationState, t }) {
    const currentIndex = LEGACY_STEPS.findIndex((step) => step.path === currentPath);
    const previousStep = currentIndex > 0 ? LEGACY_STEPS[currentIndex - 1] : null;
    const nextStep = currentIndex >= 0 && currentIndex < LEGACY_STEPS.length - 1
        ? LEGACY_STEPS[currentIndex + 1]
        : null;
    const from = locationState?.from || '/course/1';

    return {
        coursePath: from,
        previous: previousStep && { path: previousStep.path, label: previousStep.label(t) },
        next: nextStep && { path: nextStep.path, label: nextStep.label(t) },
    };
}

export default function IntroFloatingNav({
    currentPath,
    locationState,
    navigate,
    t,
    foundationNavigation = null,
}) {
    const navigation = foundationNavigation || LegacyIntroNavigation({ currentPath, locationState, t });

    return (
        <>
            <button
                onClick={() => navigateWithState(navigate, navigation.coursePath, locationState?.fromState || null)}
                className="fixed left-6 top-24 z-50 flex items-center gap-2 rounded-full bg-white px-5 py-3 text-base font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200 transition hover:bg-slate-50 hover:shadow-xl hover:ring-blue-300 active:scale-95"
            >
                <ChevronLeft size={18} />
                <span>{t('common_back')}</span>
            </button>

            {navigation.previous && (
                <button
                    onClick={() => navigateWithState(navigate, navigation.previous.path, locationState)}
                    className="fixed bottom-6 left-6 z-50 flex items-center gap-2 rounded-full bg-white px-5 py-3 text-base font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200 transition hover:bg-slate-50 hover:shadow-xl hover:ring-blue-300 active:scale-95"
                >
                    <ChevronLeft size={18} />
                    <span>{navigation.previous.label}</span>
                </button>
            )}

            {navigation.next && (
                <button
                    onClick={() => navigateWithState(navigate, navigation.next.path, locationState)}
                    className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-slate-900 px-5 py-3 text-base font-semibold text-white shadow-lg ring-1 ring-slate-800 transition hover:bg-blue-600 hover:shadow-xl active:scale-95"
                >
                    <span>{navigation.next.label}</span>
                    <ChevronRight size={18} />
                </button>
            )}
        </>
    );
}
