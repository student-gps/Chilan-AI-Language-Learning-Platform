import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, DatabaseZap, Hammer, RotateCcw } from 'lucide-react';

const tools = [
    {
        title: '跑 Pipeline',
        description: '生成 Stage1 JSON、课文音频、旁白和 slides。',
        href: '/dev/content-builder',
        icon: Hammer,
        tone: 'bg-blue-50 text-blue-700 border-blue-100',
    },
    {
        title: '入库',
        description: '预览并同步课程 JSON、slides、audio 到 DB / R2。',
        href: '/dev/course-sync',
        icon: DatabaseZap,
        tone: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    },
    {
        title: '删除 / 回退',
        description: '预览并 reset DB、R2、本地产物或回退 synced JSON。',
        href: '/dev/course-maintenance',
        icon: RotateCcw,
        tone: 'bg-rose-50 text-rose-700 border-rose-100',
    },
];

export default function DevTools() {
    return (
        <main className="min-h-screen bg-slate-50 px-5 py-24">
            <div className="mx-auto max-w-6xl">
                <header className="mb-8 border-b border-slate-200 pb-6">
                    <p className="text-xs font-black uppercase tracking-[0.28em] text-slate-400">开发工具</p>
                    <h1 className="mt-3 text-4xl font-black tracking-tight text-slate-950">Dev Console</h1>
                    <p className="mt-3 max-w-2xl text-sm font-semibold leading-6 text-slate-500">
                        本地课程生产流程的总入口：先跑 pipeline，再入库；需要清理时从 reset 页面操作。
                    </p>
                </header>

                <section className="grid gap-5 md:grid-cols-3">
                    {tools.map((tool) => {
                        const Icon = tool.icon;
                        return (
                            <Link
                                key={tool.href}
                                to={tool.href}
                                className="group flex min-h-[220px] flex-col justify-between rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
                            >
                                <div>
                                    <div className={`mb-5 flex h-12 w-12 items-center justify-center rounded-2xl border ${tool.tone}`}>
                                        <Icon size={22} />
                                    </div>
                                    <h2 className="text-2xl font-black tracking-tight text-slate-950">{tool.title}</h2>
                                    <p className="mt-3 text-sm font-semibold leading-6 text-slate-500">{tool.description}</p>
                                </div>
                                <div className="mt-8 flex items-center gap-2 text-sm font-black text-slate-900">
                                    打开
                                    <ArrowRight size={16} className="transition group-hover:translate-x-1" />
                                </div>
                            </Link>
                        );
                    })}
                </section>
            </div>
        </main>
    );
}
