import React from 'react';
import { motion } from 'framer-motion';
import { Trophy, Home, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export default function FinishCard({ isAllCompleted, onContinue }) {
    const navigate = useNavigate();
    const { t } = useTranslation();

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
                    {isAllCompleted ? t('finish_all_title') : t('finish_lesson_title')}
                </h2>
                <p className="text-slate-500 mb-10 max-w-xs mx-auto text-lg font-medium">
                    {isAllCompleted 
                        ? t('finish_all_desc')
                        : t('finish_lesson_desc')
                    }
                </p>
                
                {/* 🌟 动态按钮组 */}
                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <button 
                        onClick={() => navigate('/classroom')} 
                        className="px-8 py-4 bg-slate-100 text-slate-600 rounded-2xl font-bold text-lg hover:bg-slate-200 transition flex items-center gap-3"
                    >
                        <Home size={20} /> {t('finish_back_classroom')}
                    </button>
                    
                    {!isAllCompleted && (
                        <button 
                            onClick={onContinue} 
                            className="group px-8 py-4 bg-slate-900 text-white rounded-2xl font-bold text-lg hover:bg-slate-800 transition shadow-lg flex items-center gap-3"
                        >
                            {t('finish_continue_next')} <ArrowRight size={20} className="group-hover:translate-x-1 transition" />
                        </button>
                    )}
                </div>
            </motion.div>
        </div>
    );
}
