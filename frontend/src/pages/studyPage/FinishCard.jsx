import React from 'react';
import { motion } from 'framer-motion';
import { Trophy, Home, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function FinishCard({ isAllCompleted, onContinue }) {
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
                {/* 🌟 动态标题与文案 */}
                <h2 className="text-4xl font-black text-slate-800 mb-3">
                    {isAllCompleted ? "全部通关！" : "干得漂亮！"}
                </h2>
                <p className="text-slate-500 mb-10 max-w-xs mx-auto text-lg font-medium">
                    {isAllCompleted 
                        ? "你已经扫清了所有到期的复习题，并且完成了所有的课程。给自己鼓个掌吧！"
                        : "你已成功完成当前学习任务！要一鼓作气继续挑战下一关吗？"
                    }
                </p>
                
                {/* 🌟 动态按钮组 */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <button 
                        onClick={() => navigate('/classroom')} 
                        className="px-8 py-4 bg-slate-100 text-slate-600 rounded-2xl font-bold text-lg hover:bg-slate-200 transition flex items-center gap-3"
                    >
                        <Home size={20} /> 回到教室
                    </button>
                    
                    {!isAllCompleted && (
                        <button 
                            onClick={onContinue} 
                            className="group px-8 py-4 bg-slate-900 text-white rounded-2xl font-bold text-lg hover:bg-slate-800 transition shadow-lg flex items-center gap-3"
                        >
                            继续下一课 <ArrowRight size={20} className="group-hover:translate-x-1 transition" />
                        </button>
                    )}
                </div>
            </motion.div>
        </div>
    );
}