import React, { useCallback, useMemo, useRef, useState } from 'react';
import { FileCode2, Loader2, Play, Search, Square, TerminalSquare } from 'lucide-react';
import apiClient from '../api/apiClient';

const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';

const parseIntOrNull = (value) => {
    const text = String(value || '').trim();
    if (!text) return null;
    const digits = text.match(/\d+/)?.[0];
    return digits ? Number(digits) : null;
};

const compactArg = (arg) => String(arg || '').replaceAll('\\', '/').replace(/^.*?backend\//, 'backend/');

const Section = ({ title, children }) => (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-black text-slate-950">{title}</h2>
        <div className="mt-4">{children}</div>
    </section>
);

const Toggle = ({ label, checked, onChange }) => (
    <label className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-black text-slate-700">
        {label}
        <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} className="h-5 w-5 accent-slate-950" />
    </label>
);

export default function ContentBuilderConsole() {
    const [pipeline, setPipeline] = useState('minna_no_nihongo');
    const [lang, setLang] = useState('zh');
    const [lessonStart, setLessonStart] = useState('001');
    const [lessonEnd, setLessonEnd] = useState('001');
    const [runStage1, setRunStage1] = useState(true);
    const [runStage2, setRunStage2] = useState(true);
    const [stage2Mode, setStage2Mode] = useState('full');
    const [forceStage1, setForceStage1] = useState(true);
    const [forceNarration, setForceNarration] = useState(true);
    const [forceSlides, setForceSlides] = useState(true);
    const [refreshRenderPlan, setRefreshRenderPlan] = useState(false);
    const [lessonAudioMetadataOnly, setLessonAudioMetadataOnly] = useState(false);
    const [onlySlide, setOnlySlide] = useState('');
    const [loading, setLoading] = useState('');
    const [error, setError] = useState('');
    const [report, setReport] = useState(null);
    const [logs, setLogs] = useState([]);
    const [previewUrl, setPreviewUrl] = useState('');
    const abortRef = useRef(null);

    const payload = useMemo(() => ({
        pipeline,
        lang,
        lesson_start: parseIntOrNull(lessonStart),
        lesson_end: parseIntOrNull(lessonEnd),
        run_stage1: runStage1,
        run_stage2: runStage2,
        stage2_mode: stage2Mode,
        force_stage1: forceStage1,
        force_narration: forceNarration,
        force_slides: forceSlides,
        refresh_render_plan: refreshRenderPlan,
        lesson_audio_metadata_only: lessonAudioMetadataOnly,
        only_slide: parseIntOrNull(onlySlide),
        confirm: false,
        confirm_code: '',
    }), [
        forceNarration,
        forceSlides,
        forceStage1,
        lang,
        lessonAudioMetadataOnly,
        lessonEnd,
        lessonStart,
        onlySlide,
        pipeline,
        refreshRenderPlan,
        runStage1,
        runStage2,
        stage2Mode,
    ]);

    const addLog = useCallback((event) => {
        const now = new Date();
        setLogs((items) => [
            ...items,
            {
                id: `${now.getTime()}-${items.length}`,
                time: now.toLocaleTimeString(),
                type: event.type || 'info',
                message: event.message || JSON.stringify(event),
            },
        ].slice(-500));
    }, []);

    const preview = async () => {
        setLoading('preview');
        setError('');
        setReport(null);
        setLogs([]);
        addLog({ type: 'preview', message: '正在生成运行计划...' });
        try {
            const res = await apiClient.post('/dev/content-builder/preview', payload);
            setReport(res.data || null);
            addLog({ type: 'report', message: `计划完成：${res.data?.summary?.command_count || 0} 条命令。` });
        } catch (err) {
            const message = err?.response?.data?.detail || '预览失败。';
            setError(typeof message === 'string' ? message : JSON.stringify(message));
            addLog({ type: 'fatal', message: typeof message === 'string' ? message : JSON.stringify(message) });
        } finally {
            setLoading('');
        }
    };

    const run = async () => {
        const ok = window.confirm('确认开始运行 content builder？这会调用 LLM/TTS，并可能覆盖本地 JSON、音频或 slides。');
        if (!ok) {
            addLog({ type: 'cancelled', message: '已取消运行。' });
            return;
        }
        const controller = new AbortController();
        abortRef.current = controller;
        setLoading('run');
        setError('');
        setLogs([]);
        setPreviewUrl('');
        addLog({ type: 'start', message: '正在连接 content builder 日志流...' });
        try {
            const res = await fetch(`${API_BASE}/dev/content-builder/run-stream`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...payload, confirm: true }),
                signal: controller.signal,
            });
            if (!res.ok) {
                throw new Error(await res.text());
            }
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                for (const line of lines) {
                    if (!line.trim()) continue;
                    const event = JSON.parse(line);
                    addLog(event);
                    if (event.plan) setReport(event.plan);
                    if (event.preview_url) setPreviewUrl(event.preview_url);
                    if (event.type === 'fatal') setError(event.message || '运行失败。');
                }
            }
        } catch (err) {
            if (err?.name === 'AbortError') {
                addLog({ type: 'stopped', message: '已停止运行。' });
            } else {
                const message = err?.message || '运行失败。';
                setError(message);
                addLog({ type: 'fatal', message });
            }
        } finally {
            abortRef.current = null;
            setLoading('');
        }
    };

    const stopRun = () => {
        abortRef.current?.abort();
        addLog({ type: 'stopping', message: '正在停止当前运行...' });
    };

    const commands = report?.commands || [];
    const canRun = !loading;

    return (
        <main className="min-h-screen bg-slate-50 px-5 py-24">
            <div className="mx-auto max-w-6xl">
                <header className="mb-8 border-b border-slate-200 pb-6">
                    <p className="text-xs font-black uppercase tracking-[0.28em] text-slate-400">开发工具</p>
                    <h1 className="mt-3 text-4xl font-black tracking-tight text-slate-950">Content Builder</h1>
                </header>

                <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
                    <aside className="space-y-5">
                        <Section title="课程">
                            <div className="space-y-3">
                                <label className="block">
                                    <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">流水线</span>
                                    <input value={pipeline} onChange={(e) => setPipeline(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                </label>
                                <div className="grid grid-cols-3 gap-3">
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">语言</span>
                                        <input value={lang} onChange={(e) => setLang(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">起始</span>
                                        <input value={lessonStart} onChange={(e) => setLessonStart(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">结束</span>
                                        <input value={lessonEnd} onChange={(e) => setLessonEnd(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                </div>
                            </div>
                        </Section>

                        <Section title="阶段">
                            <div className="space-y-3">
                                <Toggle label="Stage1 JSON + 课文音频" checked={runStage1} onChange={setRunStage1} />
                                <Toggle label="Stage2 旁白 / Slides" checked={runStage2} onChange={setRunStage2} />
                                <label className="block">
                                    <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">Stage2 模式</span>
                                    <select value={stage2Mode} onChange={(e) => setStage2Mode(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold outline-none focus:border-slate-500">
                                        <option value="full">旁白 + slides</option>
                                        <option value="slides_only">只渲 slides</option>
                                    </select>
                                </label>
                                <label className="block">
                                    <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">单页重渲</span>
                                    <input value={onlySlide} onChange={(e) => setOnlySlide(e.target.value)} placeholder="留空表示全部" className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                </label>
                            </div>
                        </Section>

                        <Section title="选项">
                            <div className="space-y-3">
                                <Toggle label="覆盖 Stage1 JSON" checked={forceStage1} onChange={setForceStage1} />
                                <Toggle label="重生成旁白" checked={forceNarration} onChange={setForceNarration} />
                                <Toggle label="重渲 slides" checked={forceSlides} onChange={setForceSlides} />
                                <Toggle label="刷新 render plan" checked={refreshRenderPlan} onChange={setRefreshRenderPlan} />
                                <Toggle label="跳过课文音频生成" checked={lessonAudioMetadataOnly} onChange={setLessonAudioMetadataOnly} />
                            </div>
                        </Section>

                        <Section title="执行">
                            <div className="space-y-3">
                                <button type="button" onClick={preview} disabled={!!loading} className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:bg-slate-400">
                                    {loading === 'preview' ? <Loader2 className="animate-spin" size={16} /> : <Search size={16} />}
                                    预览命令
                                </button>
                                {loading === 'run' ? (
                                    <button type="button" onClick={stopRun} className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-red-600 text-sm font-black text-white transition hover:bg-red-700">
                                        <Square size={15} />
                                        停止运行
                                    </button>
                                ) : (
                                    <button type="button" onClick={run} disabled={!canRun} className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-blue-600 text-sm font-black text-white transition hover:bg-blue-700 disabled:bg-slate-300">
                                        <Play size={16} />
                                        开始运行
                                    </button>
                                )}
                            </div>
                        </Section>
                    </aside>

                    <section className="space-y-5">
                        {error && <div className="rounded-2xl border border-red-100 bg-red-50 px-5 py-4 text-sm font-bold text-red-700">{error}</div>}

                        {!!logs.length && (
                            <Section title="日志">
                                <div className="max-h-[520px] overflow-auto rounded-2xl bg-slate-950 p-4 font-mono text-xs text-slate-200">
                                    {logs.map((log) => (
                                        <div key={log.id} className="flex gap-3 border-b border-white/5 py-1.5 last:border-0">
                                            <span className="shrink-0 text-slate-500">{log.time}</span>
                                            <span className={
                                                log.type === 'fatal' || log.type === 'command_failed'
                                                    ? 'text-red-300'
                                                    : log.type === 'complete' || log.type === 'command_success'
                                                        ? 'text-emerald-300'
                                                        : log.type === 'log'
                                                            ? 'text-slate-100'
                                                            : 'text-blue-200'
                                            }>
                                                {log.message}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </Section>
                        )}

                        {previewUrl && (
                            <a href={previewUrl} className="flex items-center gap-2 rounded-2xl border border-emerald-100 bg-emerald-50 px-5 py-4 text-sm font-black text-emerald-800">
                                <FileCode2 size={18} />
                                打开本地预览
                            </a>
                        )}

                        {!report && !logs.length && (
                            <div className="flex min-h-[360px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white text-sm font-bold text-slate-400">
                                先预览命令，确认这次会跑哪些阶段。
                            </div>
                        )}

                        {!!commands.length && (
                            <Section title="运行计划">
                                <div className="space-y-3">
                                    {commands.map((command, index) => (
                                        <article key={`${command.lesson_id}-${command.stage}-${index}`} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                                            <div className="mb-2 flex items-center gap-2 text-sm font-black text-slate-950">
                                                <TerminalSquare size={16} />
                                                lesson{String(command.lesson_id).padStart(3, '0')} · {command.stage}
                                            </div>
                                            <div className="break-all rounded-xl bg-white px-3 py-2 font-mono text-xs font-semibold text-slate-500">
                                                {command.argv.map(compactArg).join(' ')}
                                            </div>
                                        </article>
                                    ))}
                                </div>
                            </Section>
                        )}
                    </section>
                </div>
            </div>
        </main>
    );
}
