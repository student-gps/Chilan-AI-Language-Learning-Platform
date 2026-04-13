import React from 'react';
import { Check } from 'lucide-react';

export default function AuthRequirement({ met, text }) {
    return (
        <div className={`flex items-center gap-2 text-xs font-bold transition-colors ${met ? 'text-green-500' : 'text-slate-300'}`}>
            {met ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 border-2 border-slate-200 rounded-full" />}
            {text}
        </div>
    );
}

