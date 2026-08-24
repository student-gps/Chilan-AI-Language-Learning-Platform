import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { AlertCircle, BookOpenCheck, Loader2, Volume2 } from 'lucide-react';
import IntroFloatingNav from '../introNavigation';

const TONE_STYLES = {
    amber: {
        hero: 'from-amber-50 via-white to-orange-50',
        badge: 'border-amber-200 bg-amber-50 text-amber-700',
        orb: 'bg-amber-300/30',
        glyph: 'from-amber-400 to-orange-500 shadow-amber-200',
    },
    rose: {
        hero: 'from-rose-50 via-white to-pink-50',
        badge: 'border-rose-200 bg-rose-50 text-rose-700',
        orb: 'bg-rose-300/30',
        glyph: 'from-rose-400 to-pink-500 shadow-rose-200',
    },
    sky: {
        hero: 'from-sky-50 via-white to-cyan-50',
        badge: 'border-sky-200 bg-sky-50 text-sky-700',
        orb: 'bg-sky-300/30',
        glyph: 'from-sky-400 to-cyan-500 shadow-sky-200',
    },
    indigo: {
        hero: 'from-indigo-50 via-white to-violet-50',
        badge: 'border-indigo-200 bg-indigo-50 text-indigo-700',
        orb: 'bg-indigo-300/30',
        glyph: 'from-indigo-500 to-violet-500 shadow-indigo-200',
    },
    emerald: {
        hero: 'from-emerald-50 via-white to-teal-50',
        badge: 'border-emerald-200 bg-emerald-50 text-emerald-700',
        orb: 'bg-emerald-300/30',
        glyph: 'from-emerald-500 to-teal-500 shadow-emerald-200',
    },
};

export function useJapaneseAudio(audioErrorMessage) {
    const audioRef = useRef(null);
    const [playingText, setPlayingText] = useState('');
    const [audioError, setAudioError] = useState('');

    const stop = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current = null;
        }
        setPlayingText('');
    }, []);

    useEffect(() => stop, [stop]);

    const play = useCallback((text) => {
        if (!text) return;
        stop();
        setAudioError('');
        setPlayingText(text);
        const apiBase = import.meta.env.VITE_APP_API_BASE_URL || '';
        const params = new URLSearchParams({ text, language: 'ja' });
        const audio = new Audio(`${apiBase}/study/tts?${params.toString()}`);
        audioRef.current = audio;
        audio.onended = stop;
        audio.onerror = () => {
            stop();
            setAudioError(audioErrorMessage);
        };
        audio.play().catch(() => {
            stop();
            setAudioError(audioErrorMessage);
        });
    }, [audioErrorMessage, stop]);

    return { play, playingText, audioError, clearAudioError: () => setAudioError('') };
}

export function AudioButton({ text, label, playingLabel, audio }) {
    const isPlaying = audio.playingText === text;
    return (
        <button
            type="button"
            onClick={() => audio.play(text)}
            aria-label={`${label}: ${text}`}
            className={`inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-black transition ${
                isPlaying
                    ? 'border-rose-200 bg-rose-50 text-rose-600'
                    : 'border-slate-200 bg-white text-slate-500 hover:border-rose-200 hover:text-rose-600'
            }`}
        >
            {isPlaying ? <Loader2 size={14} className="animate-spin" /> : <Volume2 size={14} />}
            {isPlaying ? playingLabel : label}
        </button>
    );
}

export function SectionHeading({ eyebrow, title, body }) {
    return (
        <div className="mb-7 max-w-3xl">
            {eyebrow && <p className="mb-2 text-xs font-black uppercase tracking-[0.24em] text-rose-500">{eyebrow}</p>}
            <h2 className="text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">{title}</h2>
            {body && <p className="mt-3 text-sm font-medium leading-7 text-slate-500 sm:text-base">{body}</p>}
        </div>
    );
}

export function LearningNote({ title, children, tone = 'amber' }) {
    const styles = {
        amber: 'border-amber-200 bg-amber-50 text-amber-900',
        rose: 'border-rose-200 bg-rose-50 text-rose-900',
        sky: 'border-sky-200 bg-sky-50 text-sky-900',
        indigo: 'border-indigo-200 bg-indigo-50 text-indigo-900',
        emerald: 'border-emerald-200 bg-emerald-50 text-emerald-900',
    };
    return (
        <aside className={`rounded-3xl border p-5 sm:p-6 ${styles[tone]}`}>
            <div className="flex gap-3">
                <BookOpenCheck className="mt-0.5 shrink-0" size={20} />
                <div>
                    <h3 className="font-black">{title}</h3>
                    <div className="mt-1 text-sm font-medium leading-7 opacity-75">{children}</div>
                </div>
            </div>
        </aside>
    );
}

export default function FoundationLayout({
    copy,
    moduleCopy,
    icon,
    tone,
    foundationNavigation,
    locationState: routeLocationState,
    navigate: routeNavigate,
    audio,
    children,
}) {
    const routerNavigate = useNavigate();
    const location = useLocation();
    const navigate = routeNavigate || routerNavigate;
    const locationState = routeLocationState ?? location.state;
    const styles = TONE_STYLES[tone] || TONE_STYLES.rose;

    return (
        <div className="min-h-screen bg-slate-50 pt-16">
            <IntroFloatingNav
                currentPath=""
                locationState={locationState}
                navigate={navigate}
                t={(key) => key === 'common_back' ? (copy.common.courseBadge.startsWith('Chilan · 日') ? '返回' : 'Back') : key}
                foundationNavigation={foundationNavigation}
            />

            <header className={`relative overflow-hidden border-b border-slate-100 bg-gradient-to-br ${styles.hero}`}>
                <div className={`absolute -right-20 -top-24 h-72 w-72 rounded-full blur-3xl ${styles.orb}`} />
                <div className="relative mx-auto grid max-w-6xl items-center gap-8 px-5 pb-14 pt-24 sm:px-6 sm:py-20 lg:grid-cols-[1fr_auto]">
                    <div>
                        <div className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-xs font-black uppercase tracking-[0.2em] ${styles.badge}`}>
                            {moduleCopy.eyebrow}
                        </div>
                        <h1 className="mt-5 max-w-4xl text-4xl font-black leading-tight tracking-tight text-slate-950 sm:text-5xl lg:text-6xl">
                            {moduleCopy.title}
                        </h1>
                        <p className="mt-5 max-w-3xl text-base font-medium leading-8 text-slate-600 sm:text-lg">
                            {moduleCopy.subtitle}
                        </p>
                        <p className="mt-5 inline-flex rounded-full bg-white/80 px-4 py-2 text-xs font-bold text-slate-500 shadow-sm ring-1 ring-slate-200/70 backdrop-blur">
                            {copy.common.readingOnly}
                        </p>
                    </div>
                    <div className={`hidden h-36 w-36 items-center justify-center rounded-[2.25rem] bg-gradient-to-br text-6xl font-black text-white shadow-2xl lg:flex ${styles.glyph}`}>
                        {icon}
                    </div>
                </div>
            </header>

            {audio?.audioError && (
                <div className="mx-auto mt-6 flex max-w-4xl items-center justify-between gap-4 rounded-2xl border border-rose-200 bg-rose-50 px-5 py-3 text-sm font-bold text-rose-700">
                    <span className="flex items-center gap-2"><AlertCircle size={17} /> {audio.audioError}</span>
                    <button type="button" onClick={audio.clearAudioError} className="text-xs font-black uppercase tracking-wider">OK</button>
                </div>
            )}

            <main className="mx-auto max-w-6xl space-y-20 px-5 py-14 pb-32 sm:px-6 sm:py-16">
                {children}
            </main>
        </div>
    );
}
