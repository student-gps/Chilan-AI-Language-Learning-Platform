import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, Database, FileJson, HardDrive, Loader2, RotateCcw, Search, Trash2 } from 'lucide-react';
import apiClient from '../api/apiClient';

const ACTIONS = [
    { id: 'db', label: '数据库', icon: Database },
    { id: 'r2', label: 'R2 媒体', icon: Trash2 },
    { id: 'restore_synced', label: 'JSON 回退', icon: FileJson },
    { id: 'local_stage2', label: '本地 Stage2', icon: HardDrive },
];

const parseIntOrNull = (value) => {
    const text = String(value || '').trim();
    if (!text) return null;
    const digits = text.match(/\d+/)?.[0];
    return digits ? Number(digits) : null;
};

const compactPath = (path) => {
    const text = String(path || '');
    const marker = 'backend\\';
    const idx = text.indexOf(marker);
    return idx >= 0 ? text.slice(idx) : text;
};

const CountPill = ({ label, value }) => (
    <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-black text-slate-600">
        {label} {value ?? 0}
    </span>
);

const Section = ({ title, children }) => (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-black text-slate-950">{title}</h2>
        <div className="mt-4">{children}</div>
    </section>
);

const inferMaintenanceDefaults = (course) => {
    const courseId = Number(course?.course_id ?? course?.id);
    const category = String(course?.category || '').toUpperCase();
    const target = String(course?.target_language || '').toLowerCase();
    const source = String(course?.source_language || '').toLowerCase();

    if (courseId === 303 || target.includes('japanese') || target.includes('日')) {
        return { pipeline: 'minna_no_nihongo', lang: source.includes('english') ? 'en' : 'zh' };
    }
    if (target.includes('chinese') || target.includes('中文') || category.endsWith('_TO_CN')) {
        const from = category.match(/^([A-Z]+)_TO_CN$/)?.[1]?.toLowerCase();
        return { pipeline: 'integrated_chinese', lang: from || (source.includes('english') ? 'en' : 'en') };
    }
    return { pipeline: '', lang: '' };
};

const courseLabel = (course) => {
    if (!course) return '';
    return `${course.course_id ?? course.id} · ${course.name || '未命名课程'} · ${course.category || 'UNKNOWN'}`;
};

export default function CourseMaintenance() {
    const [pipeline, setPipeline] = useState('minna_no_nihongo');
    const [courseId, setCourseId] = useState('303');
    const [lang, setLang] = useState('zh');
    const [lessonStart, setLessonStart] = useState('');
    const [lessonEnd, setLessonEnd] = useState('');
    const [actions, setActions] = useState(['db']);
    const [report, setReport] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState('');
    const [courses, setCourses] = useState([]);
    const [coursesLoading, setCoursesLoading] = useState(false);

    const canExecute = report && !loading;

    const payload = useMemo(() => ({
        pipeline: pipeline.trim(),
        course_id: Number(courseId),
        lang: lang.trim(),
        actions,
        lesson_start: parseIntOrNull(lessonStart),
        lesson_end: parseIntOrNull(lessonEnd),
        confirm: false,
        confirm_code: '',
    }), [actions, courseId, lang, lessonEnd, lessonStart, pipeline]);

    const applyCourse = useCallback((course) => {
        if (!course) return;
        const defaults = inferMaintenanceDefaults(course);
        setCourseId(String(course.course_id ?? course.id));
        if (defaults.pipeline) setPipeline(defaults.pipeline);
        if (defaults.lang) setLang(defaults.lang);
        setReport(null);
    }, []);

    useEffect(() => {
        let cancelled = false;
        const loadCourses = async () => {
            setCoursesLoading(true);
            try {
                const res = await apiClient.get('/courses');
                const rows = Array.isArray(res.data) ? res.data : [];
                if (cancelled) return;
                setCourses(rows);
                const current = rows.find((course) => Number(course.course_id ?? course.id) === Number(courseId));
                if (current) applyCourse(current);
            } catch (err) {
                console.error('load courses failed:', err);
            } finally {
                if (!cancelled) setCoursesLoading(false);
            }
        };
        loadCourses();
        return () => { cancelled = true; };
    }, []);

    const toggleAction = (id) => {
        setActions((prev) => {
            if (prev.includes(id)) {
                const next = prev.filter((item) => item !== id);
                return next.length ? next : prev;
            }
            return [...prev, id];
        });
        setReport(null);
    };

    const callApi = async (mode) => {
        if (mode === 'execute') {
            const ok = window.confirm('确认执行删除 / 回退？这会按当前操作项修改数据库、R2 或本地产物。');
            if (!ok) return;
        }
        setLoading(mode);
        setError('');
        try {
            const endpoint = mode === 'preview' ? '/dev/course-reset/preview' : '/dev/course-reset/execute';
            const res = await apiClient.post(endpoint, mode === 'execute' ? { ...payload, confirm: true } : payload);
            setReport(res.data || null);
        } catch (err) {
            console.error('course maintenance failed:', err);
            const detail = err?.response?.data?.detail;
            setError(typeof detail === 'string' ? detail : '操作失败。');
        } finally {
            setLoading('');
        }
    };

    const dbCounts = report?.db?.counts || report?.db?.before?.counts || {};
    const r2Keys = report?.r2?.object_keys || [];
    const localEntries = report?.local?.entries || [];
    const restoreFiles = report?.restore_synced?.files || [];
    const warnings = report?.warnings || [];

    return (
        <main className="min-h-screen bg-slate-50 px-5 py-24">
            <div className="mx-auto max-w-6xl">
                <header className="mb-8 border-b border-slate-200 pb-6">
                    <p className="text-xs font-black uppercase tracking-[0.28em] text-slate-400">Dev Maintenance</p>
                    <h1 className="mt-3 text-4xl font-black tracking-tight text-slate-950">课程维护</h1>
                </header>

                <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
                    <aside className="space-y-5">
                        <Section title="课程">
                            <div className="space-y-3">
                                <label className="block">
                                    <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">From Database</span>
                                    <select
                                        value={courses.some((course) => Number(course.course_id ?? course.id) === Number(courseId)) ? String(courseId) : ''}
                                        onChange={(e) => {
                                            const selected = courses.find((course) => String(course.course_id ?? course.id) === e.target.value);
                                            applyCourse(selected);
                                        }}
                                        className="h-11 w-full rounded-xl border border-slate-200 bg-white px-3 text-sm font-bold outline-none focus:border-slate-500"
                                        disabled={coursesLoading}
                                    >
                                        <option value="">{coursesLoading ? '加载课程中...' : '手动输入 / 未选择'}</option>
                                        {courses.map((course) => (
                                            <option key={course.course_id ?? course.id} value={course.course_id ?? course.id}>
                                                {courseLabel(course)}
                                            </option>
                                        ))}
                                    </select>
                                </label>
                                <label className="block">
                                    <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">Pipeline</span>
                                    <input value={pipeline} onChange={(e) => setPipeline(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                </label>
                                <div className="grid grid-cols-2 gap-3">
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">Course ID</span>
                                        <input value={courseId} onChange={(e) => setCourseId(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">Lang</span>
                                        <input value={lang} onChange={(e) => setLang(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">From</span>
                                        <input value={lessonStart} onChange={(e) => setLessonStart(e.target.value)} placeholder="001" className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">To</span>
                                        <input value={lessonEnd} onChange={(e) => setLessonEnd(e.target.value)} placeholder="005" className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                </div>
                            </div>
                        </Section>

                        <Section title="操作">
                            <div className="grid grid-cols-2 gap-2">
                                {ACTIONS.map(({ id, label, icon: Icon }) => {
                                    const active = actions.includes(id);
                                    return (
                                        <button
                                            key={id}
                                            type="button"
                                            onClick={() => toggleAction(id)}
                                            className={`flex items-center gap-2 rounded-xl border px-3 py-3 text-sm font-black transition ${active ? 'border-slate-950 bg-slate-950 text-white' : 'border-slate-200 bg-white text-slate-600 hover:border-slate-400'}`}
                                        >
                                            <Icon size={16} />
                                            {label}
                                        </button>
                                    );
                                })}
                            </div>
                        </Section>

                        <Section title="确认">
                            <div className="space-y-3">
                                <button
                                    type="button"
                                    onClick={() => callApi('preview')}
                                    disabled={!!loading}
                                    className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-slate-950 text-sm font-black text-white transition hover:bg-slate-800 disabled:bg-slate-400"
                                >
                                    {loading === 'preview' ? <Loader2 className="animate-spin" size={16} /> : <Search size={16} />}
                                    预览影响
                                </button>
                                <button
                                    type="button"
                                    onClick={() => callApi('execute')}
                                    disabled={!canExecute}
                                    className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-red-600 text-sm font-black text-white transition hover:bg-red-700 disabled:bg-slate-300"
                                >
                                    {loading === 'execute' ? <Loader2 className="animate-spin" size={16} /> : <RotateCcw size={16} />}
                                    执行
                                </button>
                            </div>
                        </Section>
                    </aside>

                    <section className="space-y-5">
                        {error && (
                            <div className="rounded-2xl border border-red-100 bg-red-50 px-5 py-4 text-sm font-bold text-red-700">
                                {error}
                            </div>
                        )}

                        {!report && !error && (
                            <div className="flex min-h-[360px] items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-white text-sm font-bold text-slate-400">
                                先预览影响范围。
                            </div>
                        )}

                        {report && (
                            <>
                                <div className={`rounded-2xl border px-5 py-4 ${report.executed ? 'border-emerald-100 bg-emerald-50 text-emerald-800' : 'border-amber-100 bg-amber-50 text-amber-800'}`}>
                                    <div className="flex items-center gap-3 text-sm font-black">
                                        {report.executed ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
                                        {report.executed ? '已执行' : 'Dry-run 预览'}
                                    </div>
                                </div>

                                {!!Object.keys(dbCounts).length && (
                                    <Section title="数据库">
                                        <div className="flex flex-wrap gap-2">
                                            {Object.entries(dbCounts).map(([key, value]) => <CountPill key={key} label={key} value={value} />)}
                                        </div>
                                        {report?.db?.result?.deleted && (
                                            <pre className="mt-4 max-h-48 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-100">{JSON.stringify(report.db.result.deleted, null, 2)}</pre>
                                        )}
                                    </Section>
                                )}

                                {!!r2Keys.length && (
                                    <Section title="R2 媒体">
                                        <CountPill label="objects" value={r2Keys.length} />
                                        <div className="mt-4 max-h-56 overflow-auto rounded-xl border border-slate-100 bg-slate-50 p-3">
                                            {r2Keys.slice(0, 160).map((key) => (
                                                <div key={key} className="truncate py-1 font-mono text-xs text-slate-600">{key}</div>
                                            ))}
                                        </div>
                                    </Section>
                                )}

                                {!!restoreFiles.length && (
                                    <Section title="JSON 回退">
                                        <CountPill label="files" value={restoreFiles.length} />
                                        <div className="mt-4 space-y-2">
                                            {restoreFiles.map((file) => (
                                                <div key={file.source} className="rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs font-bold text-slate-600">
                                                    <div>{compactPath(file.source)}</div>
                                                    <div className="text-slate-400">→ {compactPath(file.destination)}</div>
                                                    {file.destination_exists && <div className="mt-1 text-red-600">destination exists</div>}
                                                </div>
                                            ))}
                                        </div>
                                    </Section>
                                )}

                                {!!localEntries.length && (
                                    <Section title="本地产物">
                                        <CountPill label="entries" value={localEntries.length} />
                                        <div className="mt-4 space-y-2">
                                            {localEntries.map((entry) => (
                                                <div key={entry.path} className="rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs font-bold text-slate-600">
                                                    {compactPath(entry.path)}
                                                    <span className="ml-2 text-slate-400">{entry.file_count} files</span>
                                                </div>
                                            ))}
                                        </div>
                                    </Section>
                                )}

                                {!!warnings.length && (
                                    <Section title="Warnings">
                                        {warnings.map((warning) => (
                                            <div key={warning} className="text-sm font-bold text-amber-700">{warning}</div>
                                        ))}
                                    </Section>
                                )}
                            </>
                        )}
                    </section>
                </div>
            </div>
        </main>
    );
}
