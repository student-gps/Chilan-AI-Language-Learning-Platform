import React from 'react';
import { motion } from 'framer-motion';
import { Trophy, Home } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function FinishCard() {
    const navigate = useNavigate();

    return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-white p-6 text-center">
            <motion.div 
                initial={{ scale: 0, rotate: -20 }} 
                animate={{ scale: 1, rotate: 0 }} 
                className="mb-6 p-8 bg-yellow-100 rounded-full text-yellow-600 shadow-xl shadow-yellow-100/50"
            >
                <Trophy size={80} />
            </motion.div>
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
            >
                <h2 className="text-4xl font-black text-slate-800 mb-3">任务达成！</h2>
                <p className="text-slate-500 mb-10 max-w-xs mx-auto text-lg">
                    你已经扫清了所有到期的复习题，并且完成了今天的课程。保持这个势头！
                </p>
                <button 
                    onClick={() => navigate('/classroom')} 
                    className="group px-10 py-4 bg-slate-900 text-white rounded-2xl font-bold text-lg hover:bg-slate-800 transition flex items-center gap-3 mx-auto"
                >
                    回到教室 <Home size={20} className="group-hover:scale-110 transition" />
                </button>
            </motion.div>
        </div>
    );
}