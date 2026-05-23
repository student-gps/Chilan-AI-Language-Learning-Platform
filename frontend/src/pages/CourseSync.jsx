import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, DatabaseZap, FileJson, Loader2, RotateCw, Search, UploadCloud } from 'lucide-react';
import apiClient from '../api/apiClient';

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

const inferDefaults = (course) => {
    const courseId = Number(course?.course_id ?? course?.id);
    const category = String(course?.category || '').toUpperCase();
    const target = String(course?.target_language || '').toLowerCase();
    const source = String(course?.source_language || '').toLowerCase();
    if (courseId === 303 || target.includes('japanese') || target.includes('日')) {
        return { pipeline: 'minna_no_nihongo', lang: source.includes('english') ? 'en' : 'zh' };
    }
    if (target.includes('chinese') || target.includes('中文') || category.endsWith('_TO_CN')) {
        const from = category.match(/^([A-Z]+)_TO_CN$/)?.[1]?.toLowerCase();
        return { pipeline: 'integrated_chinese', lang: from || 'en' };
    }
    return { pipeline: '', lang: '' };
};

const courseLabel = (course) => `${course.course_id ?? course.id} · ${course.name || '未命名课程'} · ${course.category || 'UNKNOWN'}`;

const Section = ({ title, children }) => (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-lg font-black text-slate-950">{title}</h2>
        <div className="mt-4">{children}</div>
    </section>
);

const Pill = ({ label, value }) => (
    <span className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-black text-slate-600">
        {label} {value ?? 0}
    </span>
);

export default function CourseSync() {
    const [courses, setCourses] = useState([]);
    const [coursesLoading, setCoursesLoading] = useState(false);
    const [pipeline, setPipeline] = useState('minna_no_nihongo');
    const [courseId, setCourseId] = useState('303');
    const [lang, setLang] = useState('zh');
    const [lessonStart, setLessonStart] = useState('');
    const [lessonEnd, setLessonEnd] = useState('');
    const [includeSynced, setIncludeSynced] = useState(true);
    const [uploadAssets, setUploadAssets] = useState(true);
    const [confirmCode, setConfirmCode] = useState('');
    const [report, setReport] = useState(null);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState('');

    const requiredCode = useMemo(() => `SYNC-${String(courseId || '').trim() || 'COURSE'}`, [courseId]);
    const canExecute = report && confirmCode === requiredCode && !loading;

    const payload = useMemo(() => ({
        pipeline: pipeline.trim(),
        course_id: Number(courseId),
        lang: lang.trim(),
        lesson_start: parseIntOrNull(lessonStart),
        lesson_end: parseIntOrNull(lessonEnd),
        include_synced: includeSynced,
        upload_assets: uploadAssets,
        confirm: confirmCode === requiredCode,
        confirm_code: confirmCode,
    }), [confirmCode, courseId, includeSynced, lang, lessonEnd, lessonStart, pipeline, requiredCode, uploadAssets]);

    const applyCourse = useCallback((course) => {
        if (!course) return;
        const defaults = inferDefaults(course);
        setCourseId(String(course.course_id ?? course.id));
        if (defaults.pipeline) setPipeline(defaults.pipeline);
        if (defaults.lang) setLang(defaults.lang);
        setReport(null);
        setConfirmCode('');
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

    const callApi = async (mode) => {
        setLoading(mode);
        setError('');
        try {
            const endpoint = mode === 'preview' ? '/dev/course-sync/preview' : '/dev/course-sync/execute';
            const res = await apiClient.post(endpoint, payload);
            setReport(res.data || null);
            if (mode === 'execute') setConfirmCode('');
        } catch (err) {
            console.error('course sync failed:', err);
            const detail = err?.response?.data?.detail;
            setError(typeof detail === 'string' ? detail : '同步失败。');
        } finally {
            setLoading('');
        }
    };

    const summary = report?.summary || {};
    const lessons = report?.lessons || [];
    const warnings = report?.warnings || [];

    return (
        <main className="min-h-screen bg-slate-50 px-5 py-24">
            <div className="mx-auto max-w-6xl">
                <header className="mb-8 border-b border-slate-200 pb-6">
                    <p className="text-xs font-black uppercase tracking-[0.28em] text-slate-400">开发工具</p>
                    <h1 className="mt-3 text-4xl font-black tracking-tight text-slate-950">课程入库</h1>
                </header>

                <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
                    <aside className="space-y-5">
                        <Section title="课程">
                            <div className="space-y-3">
                                <label className="block">
                                    <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">数据库课程</span>
                                    <select
                                        value={courses.some((course) => Number(course.course_id ?? course.id) === Number(courseId)) ? String(courseId) : ''}
                                        onChange={(e) => applyCourse(courses.find((course) => String(course.course_id ?? course.id) === e.target.value))}
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
                                    <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">内容流水线</span>
                                    <input value={pipeline} onChange={(e) => setPipeline(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                </label>
                                <div className="grid grid-cols-2 gap-3">
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">课程 ID</span>
                                        <input value={courseId} onChange={(e) => setCourseId(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">讲解语言</span>
                                        <input value={lang} onChange={(e) => setLang(e.target.value)} className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">起始课</span>
                                        <input value={lessonStart} onChange={(e) => setLessonStart(e.target.value)} placeholder="001" className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                    <label className="block">
                                        <span className="mb-1 block text-[11px] font-black uppercase tracking-widest text-slate-400">结束课</span>
                                        <input value={lessonEnd} onChange={(e) => setLessonEnd(e.target.value)} placeholder="005" className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-bold outline-none focus:border-slate-500" />
                                    </label>
                                </div>
                            </div>
                        </Section>

                        <Section title="选项">
                            <div className="space-y-3">
                                <label className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-black text-slate-700">
                                    扫描 synced_json
                                    <input type="checkbox" checked={includeSynced} onChange={(e) => setIncludeSynced(e.target.checked)} className="h-5 w-5 accent-slate-950" />
                                </label>
                                <label className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-black text-slate-700">
                                    上传 R2 媒体
                                    <input type="checkbox" checked={uploadAssets} onChange={(e) => setUploadAssets(e.target.checked)} className="h-5 w-5 accent-slate-950" />
                                </label>
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
                                    预览入库
                                </button>
                                <input
                                    value={confirmCode}
                                    onChange={(e) => setConfirmCode(e.target.value)}
                                    placeholder={requiredCode}
                                    className="h-11 w-full rounded-xl border border-slate-200 px-3 text-sm font-black outline-none focus:border-slate-500"
                                />
                                <button
                                    type="button"
                                    onClick={() => callApi('execute')}
                                    disabled={!canExecute}
                                    className="flex h-12 w-full items-center justify-center gap-2 rounded-xl bg-blue-600 text-sm font-black text-white transition hover:bg-blue-700 disabled:bg-slate-300"
                                >
                                    {loading === 'execute' ? <Loader2 className="animate-spin" size={16} /> : <UploadCloud size={16} />}
                                    执行入库
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
                                先预览待入库 JSON。
                            </div>
                        )}
                        {report && (
                            <>
                                <div className={`rounded-2xl border px-5 py-4 ${report.executed ? 'border-emerald-100 bg-emerald-50 text-emerald-800' : 'border-blue-100 bg-blue-50 text-blue-800'}`}>
                                    <div className="flex items-center gap-3 text-sm font-black">
                                        {report.executed ? <CheckCircle2 size={18} /> : <DatabaseZap size={18} />}
                                        {report.executed ? '已执行入库' : '入库预览'}
                                    </div>
                                </div>

                                <Section title="概要">
                                    <div className="flex flex-wrap gap-2">
                                        {Object.entries(summary).map(([key, value]) => <Pill key={key} label={key} value={value} />)}
                                    </div>
                                </Section>

                                {!!warnings.length && (
                                    <Section title="提醒">
                                        {warnings.map((warning) => (
                                            <div key={warning} className="text-sm font-bold text-amber-700">{warning}</div>
                                        ))}
                                    </Section>
                                )}

                                <Section title="课次">
                                    <div className="space-y-3">
                                        {lessons.map((lesson) => (
                                            <article key={lesson.path} className="rounded-2xl border border-slate-100 bg-slate-50 p-4">
                                                <div className="flex flex-wrap items-start justify-between gap-3">
                                                    <div>
                                                        <div className="text-base font-black text-slate-950">
                                                            {lesson.lesson_id ? `lesson${String(lesson.lesson_id).padStart(3, '0')}` : 'unknown'} · {lesson.title || lesson.status}
                                                        </div>
                                                        <div className="mt-1 max-w-2xl truncate font-mono text-xs font-semibold text-slate-400">
                                                            {compactPath(lesson.path)}
                                                        </div>
                                                    </div>
                                                    <span className={`rounded-full px-3 py-1 text-xs font-black ${lesson.sync_status === 'success' ? 'bg-emerald-100 text-emerald-700' : lesson.sync_status === 'failed' ? 'bg-red-100 text-red-700' : lesson.will_overwrite_db ? 'bg-amber-100 text-amber-800' : 'bg-white text-slate-600'}`}>
                                                        {lesson.sync_status || (lesson.will_overwrite_db ? 'overwrite' : lesson.source)}
                                                    </span>
                                                </div>
                                                <div className="mt-3 flex flex-wrap gap-2">
                                                    <Pill label="幻灯片" value={lesson.slide_count} />
                                                    <Pill label="题目" value={lesson.database_item_count} />
                                                    <Pill label="音频" value={lesson.lesson_audio_item_count} />
                                                    <Pill label="对象" value={lesson.object_key_count} />
                                                    <Pill label="来源" value={lesson.source} />
                                                    <Pill label="入库课程" value={lesson.sync_course_id} />
                                                </div>
                                                {lesson.course_id_will_be_normalized && (
                                                    <div className="mt-3 rounded-xl bg-amber-50 px-3 py-2 text-xs font-bold text-amber-800">
                                                        JSON 原 course_id 为 {lesson.metadata_course_id ?? '空'}，执行时会按 {lesson.sync_course_id} 入库。
                                                    </div>
                                                )}
                                                {lesson.error && (
                                                    <div className="mt-3 rounded-xl bg-red-50 px-3 py-2 text-xs font-bold text-red-700">
                                                        {lesson.error}
                                                    </div>
                                                )}
                                                {lesson.archived_to && (
                                                    <div className="mt-3 rounded-xl bg-emerald-50 px-3 py-2 text-xs font-bold text-emerald-700">
                                                        已归档到 {compactPath(lesson.archived_to)}
                                                    </div>
                                                )}
                                            </article>
                                        ))}
                                    </div>
                                </Section>
                            </>
                        )}
                    </section>
                </div>
            </div>
        </main>
    );
}
