import React from 'react';
import { Link } from 'react-router-dom';

export default class AppErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { error: null };
    }

    static getDerivedStateFromError(error) {
        return { error };
    }

    componentDidCatch(error, errorInfo) {
        console.error('Unhandled application render error:', error, errorInfo);
    }

    handleRetry = () => {
        this.setState({ error: null });
    };

    render() {
        if (!this.state.error) return this.props.children;

        return (
            <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6 pt-20">
                <section className="w-full max-w-lg rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                    <p className="text-sm font-black uppercase tracking-widest text-blue-600">Chilan</p>
                    <h1 className="mt-3 text-3xl font-black text-slate-900">This page could not load</h1>
                    <p className="mt-3 text-sm font-medium leading-relaxed text-slate-500">
                        We could not display this page. You can retry or return to the classroom.
                    </p>
                    <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
                        <button
                            type="button"
                            onClick={this.handleRetry}
                            className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-black text-white transition hover:bg-blue-600"
                        >
                            Retry
                        </button>
                        <Link
                            to="/classroom"
                            className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-black text-slate-700 transition hover:bg-slate-50"
                        >
                            Back to classroom
                        </Link>
                    </div>
                </section>
            </main>
        );
    }
}
