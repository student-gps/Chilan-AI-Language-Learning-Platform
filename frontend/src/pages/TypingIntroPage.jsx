import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

export default function TypingIntroPage() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen bg-slate-50 pt-24 pb-20">
            <div className="max-w-6xl mx-auto px-8">
                <button
                    onClick={() => navigate(-1)}
                    className="flex items-center gap-2 text-slate-400 hover:text-slate-700 transition-colors mb-8 font-semibold"
                >
                    <ArrowLeft size={18} /> 返回
                </button>

                <h1 className="text-4xl font-black text-slate-900 mb-3">电脑打字教程</h1>
                <p className="text-slate-400 font-medium mb-12">输入法 · 拼音打字 · 练习</p>

                <div className="bg-white rounded-3xl border border-slate-100 shadow-sm p-12 text-center">
                    <span className="text-6xl">⌨️</span>
                    <p className="mt-6 text-xl font-black text-slate-700">内容即将上线</p>
                    <p className="mt-2 text-slate-400 font-medium">这里将包含中文输入法安装、拼音打字方法和打字练习等内容。</p>
                </div>
            </div>
        </div>
    );
}
