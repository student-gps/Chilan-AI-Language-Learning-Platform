import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Loader2 } from 'lucide-react';

export default function AuthSuccessState({ isLogin, title, subtitle }) {
    return (
        <motion.div key="success" initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="text-center">
            <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle2 size={40} />
            </div>
            <h2 className="text-2xl font-black mb-2 text-slate-900">{title}</h2>
            <p className="text-slate-500 font-medium mb-8 whitespace-pre-line">{subtitle}</p>
            <Loader2 className="animate-spin mx-auto text-blue-500" />
        </motion.div>
    );
}

