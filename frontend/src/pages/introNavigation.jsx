import { ChevronLeft, ChevronRight } from 'lucide-react';

const FOUNDATION_PATHS = new Set(['/learn/intro', '/learn/hanzi', '/learn/pinyin', '/learn/typing']);
const DEFAULT_COURSE_OVERVIEW_PATH = '/course/1';

const INTRO_STEPS = [
    { path: '/learn/intro', label: (t) => t('ci_h1_line1') },
    { path: '/learn/hanzi', label: (t) => cleanLabel(t('ci_cta_hanzi')) },
    { path: '/learn/pinyin', label: (t) => t('ci_cta_pinyin') },
    { path: '/learn/typing', label: (t) => t('typing_intro_title') },
];

const cleanLabel = (text) => (text || '').replace('→', '').trim();

const getIntroEntryState = (state) => {
    let cursor = state;

    while (cursor?.from && FOUNDATION_PATHS.has(cursor.from)) {
        cursor = cursor.fromState;
    }

    if (cursor?.from && String(cursor.from).startsWith('/course/')) {
        return cursor.fromState ? { from: cursor.from, fromState: cursor.fromState } : { from: cursor.from };
    }

    return { from: DEFAULT_COURSE_OVERVIEW_PATH };
};

const getIntroExitTarget = (state) => {
    const entryState = getIntroEntryState(state);
    return {
        path: entryState.from || '/classroom',
        state: entryState.fromState || null,
    };
};

function navigateWithState(navigate, path, state) {
    navigate(path, state ? { state } : undefined);
}

export default function IntroFloatingNav({ currentPath, locationState, navigate, t }) {
    const currentIndex = INTRO_STEPS.findIndex((step) => step.path === currentPath);
    const introState = getIntroEntryState(locationState);
    const exitTarget = getIntroExitTarget(locationState);
    const previousStep = currentIndex > 0 ? INTRO_STEPS[currentIndex - 1] : null;
    const nextStep = currentIndex >= 0 && currentIndex < INTRO_STEPS.length - 1
        ? INTRO_STEPS[currentIndex + 1]
        : null;

    return (
        <>
            <button
                onClick={() => navigateWithState(navigate, exitTarget.path, exitTarget.state)}
                className="fixed left-6 top-24 z-50 flex items-center gap-2 rounded-full bg-white px-5 py-3 text-base font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200 transition hover:bg-slate-50 hover:shadow-xl hover:ring-blue-300 active:scale-95"
            >
                <ChevronLeft size={18} />
                <span>{t('common_back')}</span>
            </button>

            {previousStep && (
                <button
                    onClick={() => navigateWithState(navigate, previousStep.path, introState)}
                    className="fixed bottom-6 left-6 z-50 flex items-center gap-2 rounded-full bg-white px-5 py-3 text-base font-semibold text-slate-700 shadow-lg ring-1 ring-slate-200 transition hover:bg-slate-50 hover:shadow-xl hover:ring-blue-300 active:scale-95"
                >
                    <ChevronLeft size={18} />
                    <span>{previousStep.label(t)}</span>
                </button>
            )}

            {nextStep && (
                <button
                    onClick={() => navigateWithState(navigate, nextStep.path, introState)}
                    className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full bg-slate-900 px-5 py-3 text-base font-semibold text-white shadow-lg ring-1 ring-slate-800 transition hover:bg-blue-600 hover:shadow-xl active:scale-95"
                >
                    <span>{nextStep.label(t)}</span>
                    <ChevronRight size={18} />
                </button>
            )}
        </>
    );
}
