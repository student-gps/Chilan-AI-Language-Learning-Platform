import { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { X, ExternalLink } from 'lucide-react';

// ── 声母分组 ────────────────────────────────────────────────────────────────
const INITIALS = [
    ['b', 'p', 'm', 'f'],
    ['d', 't', 'n', 'l'],
    ['g', 'k', 'h'],
    ['j', 'q', 'x'],
    ['zh', 'ch', 'sh', 'r'],
    ['z', 'c', 's'],
];

// ── 韵母分组 ────────────────────────────────────────────────────────────────
const FINALS = [
    ['a',  'ai',  'an',  'ang', 'ao'],
    ['o',  'ou',  'ong', 'iong'],
    ['e',  'ei',  'en',  'eng', 'er'],
    ['i',  'ie',  'in',  'ing', 'iu'],
    ['u',  'ui',  'un',  'uo'],
    ['ü',  'üe',  'ün',  'üan'],
    ['ia', 'ian', 'iang','iao'],
    ['ua', 'uai', 'uan', 'uang'],
];

// ── 声母对应音频 ─────────────────────────────────────────────────────────────
const INITIAL_AUDIO = {
    b:'bo1.wav', p:'po1.wav', m:'mo1.wav', f:'fo1.wav',
    d:'de1.wav', t:'te1.wav', n:'ne1.wav', l:'le1.wav',
    g:'ge1.wav', k:'ke1.wav', h:'he1.wav',
    j:'ji1.wav', q:'qi1.wav', x:'xi1.wav',
    zh:'zhi1.wav', ch:'chi1.wav', sh:'shi1.wav', r:'ri4.wav',
    z:'zi1.wav',  c:'ci1.wav',  s:'si1.wav',
};

// ── 韵母对应音频 ─────────────────────────────────────────────────────────────
const FINAL_AUDIO = {
    a:'a1.wav',    ai:'ai1.wav',  an:'an1.wav',   ang:'ang1.wav', ao:'ao4.wav',
    o:'o1.wav',    ou:'ou1.wav',  ong:'ong1.wav',  iong:'yong1.wav',
    e:'e1.wav',    ei:'ei1.wav',  en:'en1.wav',   eng:'eng1.wav', er:'er2.wav',
    i:'yi1.wav',   ie:'ye1.wav',  in:'yin1.wav',  ing:'ying1.wav', iu:'you1.wav',
    u:'wu1.wav',   ui:'wei1.wav', un:'wen1.wav',  uo:'wo1.wav',
    ü:'yu1.wav',   üe:'yue1.wav', ün:'yun1.wav',  üan:'yuan1.wav',
    ia:'ya1.wav',  ian:'yan1.wav',iang:'yang1.wav',iao:'yao1.wav',
    ua:'wa1.wav',  uai:'wai1.wav',uan:'wan1.wav',  uang:'wang1.wav',
};

const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';

function playAudio(filename) {
    if (!filename) return;
    const audio = new Audio(`${API_BASE}/media/pinyin/${filename}`);
    audio.play().catch(() => {});
}

function SoundBtn({ label, audioFile }) {
    return (
        <button
            onClick={() => playAudio(audioFile)}
            className="flex items-center justify-center rounded-xl border border-slate-200 bg-white px-2 py-2 text-sm font-semibold text-slate-700 transition hover:border-blue-300 hover:bg-blue-50 hover:text-blue-700 active:scale-95 min-w-[44px]"
        >
            {label}
        </button>
    );
}

export default function PinyinPopover({ onClose }) {
    const navigate = useNavigate();
    const location = useLocation();
    const ref = useRef(null);

    // 点击外部关闭
    useEffect(() => {
        const handler = (e) => {
            if (ref.current && !ref.current.contains(e.target)) onClose();
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, [onClose]);

    // Esc 关闭
    useEffect(() => {
        const handler = (e) => { if (e.key === 'Escape') onClose(); };
        document.addEventListener('keydown', handler);
        return () => document.removeEventListener('keydown', handler);
    }, [onClose]);

    return (
        <div
            ref={ref}
            className="fixed bottom-20 left-6 z-50 w-fit max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-200 bg-white/95 p-5 shadow-2xl backdrop-blur-sm"
        >
            {/* 声母 + 韵母 两栏 */}
            <div className="flex flex-col gap-3">
                {/* 声母 */}
                <div>
                    <div className="mb-2 flex items-center justify-between">
                        <p className="text-xs font-bold uppercase tracking-widest text-slate-400">Initials</p>
                        <button
                            onClick={onClose}
                            className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
                        >
                            <X size={16} />
                        </button>
                    </div>
                    <div className="flex flex-col gap-1.5">
                        {INITIALS.map((row, ri) => (
                            <div key={ri} className="flex gap-1.5">
                                {row.map(s => (
                                    <SoundBtn key={s} label={s} audioFile={INITIAL_AUDIO[s]} />
                                ))}
                            </div>
                        ))}
                    </div>
                </div>

                {/* 韵母 */}
                <div>
                    <p className="mb-2 text-xs font-bold uppercase tracking-widest text-slate-400">
                        Finals
                    </p>
                    <div className="flex flex-col gap-1.5">
                        {FINALS.map((row, ri) => (
                            <div key={ri} className="flex gap-1.5">
                                {row.map(s => (
                                    <SoundBtn key={s} label={s} audioFile={FINAL_AUDIO[s]} />
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* 底部：完整页面入口 */}
            <div className="mt-4 border-t border-slate-100 pt-4">
                <button
                    onClick={() => navigate('/learn/pinyin', { state: { from: location.pathname } })}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
                >
                    <span>Open Full Pinyin Guide</span>
                    <ExternalLink size={14} />
                </button>
            </div>
        </div>
    );
}
