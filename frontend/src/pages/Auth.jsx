import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
// 🚀 引入我们统一的 API 客户端
import apiClient from '../api/apiClient'; 
import { 
    Mail, Lock, ArrowLeft, Loader2, CheckCircle2, 
    ShieldCheck, AlertCircle, Eye, EyeOff, Hash, Check
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';

export default function Auth() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    
    const [step, setStep] = useState('form'); // form, verify, forgot, reset, success
    const [mode, setMode] = useState('login'); 
    
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [code, setCode] = useState('');
    
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const checks = {
        length: password.length >= 8 && password.length <= 32,
        letter: /[A-Za-z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[^A-Za-z0-9]/.test(password),
        noSpace: !/\s/.test(password),
        match: (mode === 'register' || step === 'reset') ? (password === confirmPassword && confirmPassword !== '') : true
    };
    const isPasswordValid = Object.values(checks).every(Boolean);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            // 🚀 定义统一的路径前缀
            const AUTH_PATH = "/auth";

            if (step === 'forgot') {
                await apiClient.post(`${AUTH_PATH}/forgot-password`, { email });
                setStep('reset');
                setPassword('');
                setConfirmPassword('');
            } else if (step === 'reset') {
                // ✅ 已修复：使用 apiClient 和 AUTH_PATH
                await apiClient.post(`${AUTH_PATH}/reset-password`, { 
                    email, 
                    code, 
                    new_password: password 
                });
                setStep('success');
                setTimeout(() => { setStep('form'); setMode('login'); }, 2000);
            } else if (mode === 'register') {
                if (step === 'form') {
                    await apiClient.post(`${AUTH_PATH}/signup`, { email, password, lang: i18n.language });
                    setStep('verify');
                } else {
                    await apiClient.post(`${AUTH_PATH}/verify`, { email, code });
                    setStep('success');
                    setTimeout(() => { setMode('login'); setStep('form'); }, 2000);
                }
            } else {
                // 登录逻辑
                const res = await apiClient.post(`${AUTH_PATH}/login`, { email, password });
                localStorage.setItem('chilan_token', res.data.access_token);
                localStorage.setItem('chilan_user_id', res.data.user_id);
                setStep('success');
                setTimeout(() => navigate('/'), 2000); 
            }
        } catch (err) {
            const status = err.response?.status;
            const detail = err.response?.data?.detail;
            const message = err.message;
            console.error("Auth request failed:", {
                step,
                mode,
                status,
                detail,
                message,
                response: err.response?.data,
            });
            setError(
                detail
                    ? `${detail}${status ? ` (HTTP ${status})` : ''}`
                    : `Operation failed${status ? ` (HTTP ${status})` : ''}`
            );
        } finally {
            setIsLoading(false);
        }
    };

    const googleLogin = useGoogleLogin({
        onSuccess: async (tokenResponse) => {
            setIsLoading(true);
            try {
                // ✅ 使用 apiClient 处理 Google 登录
                const res = await apiClient.post('/auth/google', { 
                    access_token: tokenResponse.access_token 
                });
                localStorage.setItem('chilan_token', res.data.access_token);
                localStorage.setItem('chilan_user_id', res.data.user_id);
                setStep('success');
                setTimeout(() => navigate('/'), 2000);
            } catch (err) { 
                console.error("Google auth failed:", {
                    status: err.response?.status,
                    detail: err.response?.data?.detail,
                    message: err.message,
                    response: err.response?.data,
                });
                setError(
                    err.response?.data?.detail
                        ? `${err.response.data.detail}${err.response?.status ? ` (HTTP ${err.response.status})` : ''}`
                        : "Google Auth Failed"
                ); 
            } finally { 
                setIsLoading(false); 
            }
        }
    });

    const Requirement = ({ met, text }) => (
        <div className={`flex items-center gap-2 text-xs font-bold transition-colors ${met ? 'text-green-500' : 'text-slate-300'}`}>
            {met ? <Check size={12} strokeWidth={3} /> : <div className="w-3 h-3 border-2 border-slate-200 rounded-full" />}
            {text}
        </div>
    );

    return (
        <div className="min-h-screen bg-slate-50 font-sans text-slate-900 pb-20">
            <div className="flex flex-col items-center justify-center pt-20 px-6">
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <button 
                        onClick={() => step === 'form' ? navigate('/') : setStep('form')} 
                        className="flex items-center gap-2 text-slate-400 hover:text-blue-600 font-bold text-sm mb-6 transition-colors group"
                    >
                        <ArrowLeft size={16} className="group-hover:-translate-x-1 transition-transform" />
                        {step === 'form' ? t('auth_back_home') : t('auth_back_to_login')}
                    </button>
                </motion.div>

                <motion.div layout className="w-full max-w-md bg-white rounded-[2.5rem] shadow-2xl p-10 border border-slate-100 min-h-[550px] flex flex-col justify-center overflow-hidden">
                    <AnimatePresence mode="wait">
                        {step === 'success' ? (
                            <motion.div key="success" initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} className="text-center">
                                <div className="w-20 h-20 bg-green-100 text-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
                                    <CheckCircle2 size={40}/>
                                </div>
                                <h2 className="text-2xl font-black mb-2 text-slate-900">{mode === 'login' ? t('auth_login_success_title') : t('auth_success_title')}</h2>
                                <p className="text-slate-500 font-medium mb-8 whitespace-pre-line">{mode === 'login' ? t('auth_login_success_subtitle') : t('auth_success_subtitle')}</p>
                                <Loader2 className="animate-spin mx-auto text-blue-500" />
                            </motion.div>
                        ) : (
                            <motion.div key={step} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                                {step === 'form' && (
                                    <div className="flex bg-slate-100 p-1.5 rounded-2xl mb-8">
                                        <button onClick={() => setMode('login')} className={`flex-1 py-2.5 rounded-xl text-sm font-bold transition-all ${mode === 'login' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500'}`}>{t('auth_login')}</button>
                                        <button onClick={() => setMode('register')} className={`flex-1 py-2.5 rounded-xl text-sm font-bold transition-all ${mode === 'register' ? 'bg-white text-blue-600 shadow-sm' : 'text-slate-500'}`}>{t('auth_register')}</button>
                                    </div>
                                )}

                                <h2 className="text-3xl font-black mb-2 tracking-tight text-slate-900">
                                    {step === 'forgot' ? t('auth_forgot_title') : 
                                     step === 'reset' ? t('auth_reset_title') : 
                                     step === 'verify' ? t('auth_verify_title') : 
                                     mode === 'login' ? t('auth_welcome') : t('auth_create')}
                                </h2>
                                <p className="text-slate-500 mb-8 font-medium text-sm">
                                    {step === 'forgot' ? t('auth_forgot_subtitle') : 
                                     step === 'reset' ? t('auth_reset_subtitle') : 
                                     step === 'verify' ? t('auth_verify_subtitle', { email: email }) :
                                     mode === 'register' ? t('auth_register_tip') : t('auth_login_subtitle')}
                                </p>

                                {error && <div className="mb-6 p-4 bg-red-50 text-red-600 border border-red-100 rounded-2xl text-xs font-bold flex items-center gap-2 animate-pulse"><AlertCircle size={14}/>{error}</div>}

                                <form onSubmit={handleSubmit} className="space-y-4">
                                    {/* 邮箱输入：仅在验证码步骤中隐藏，除非是重置流程 */}
                                    {(step === 'form' || step === 'forgot' || step === 'reset') && (
                                        <div className="relative group">
                                            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18}/>
                                            <input required type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder={t('auth_email')} disabled={step === 'reset'} className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500/20 font-medium disabled:opacity-50" />
                                        </div>
                                    )}

                                    {/* 密码输入：仅在登录/注册表单或重置密码时显示 */}
                                    {(step === 'form' || step === 'reset') && (
                                        <div className="relative group">
                                            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18}/>
                                            <input required type={showPassword ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} placeholder={t('auth_password')} className="w-full pl-12 pr-12 py-4 bg-slate-50 border border-slate-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500/20 font-medium transition-all" />
                                            <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-500">
                                                {showPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
                                            </button>
                                        </div>
                                    )}

                                    {/* 密码确认与强度检查：仅在注册表单(非验证页)或重置密码页显示 */}
                                    {((mode === 'register' && step === 'form') || step === 'reset') && (
                                        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} className="space-y-4">
                                            <div className="relative group">
                                                <ShieldCheck className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18}/>
                                                <input required type={showConfirmPassword ? "text" : "password"} value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} placeholder={t('auth_confirm_password')} className="w-full pl-12 pr-12 py-4 bg-slate-50 border border-slate-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500/20 font-medium transition-all" />
                                                <button type="button" onClick={() => setShowConfirmPassword(!showConfirmPassword)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-blue-500">
                                                    {showConfirmPassword ? <EyeOff size={18}/> : <Eye size={18}/>}
                                                </button>
                                            </div>
                                            <div className="p-4 bg-slate-50 rounded-2xl grid grid-cols-1 md:grid-cols-2 gap-3 border border-slate-100">
                                                <Requirement met={checks.length} text={t('auth_pw_req_length')} />
                                                <Requirement met={checks.letter} text={t('auth_pw_req_letter')} />
                                                <Requirement met={checks.number} text={t('auth_pw_req_number')} />
                                                <Requirement met={checks.special} text={t('auth_pw_req_special')} />
                                                <Requirement met={checks.noSpace} text={t('auth_pw_req_no_space')} />
                                                <Requirement met={checks.match} text={t('auth_pw_match')} />
                                            </div>
                                        </motion.div>
                                    )}

                                    {/* 验证码输入框：仅在验证环节出现 */}
                                    {(step === 'verify' || step === 'reset') && (
                                        <div className="relative group">
                                            <Hash className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18}/>
                                            <input required maxLength="6" value={code} onChange={e => setCode(e.target.value)} placeholder="000000" className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-100 rounded-2xl outline-none focus:ring-2 focus:ring-blue-500/20 text-center tracking-[0.5em] font-black text-2xl text-slate-900" />
                                        </div>
                                    )}

                                    <button 
                                        disabled={isLoading || (( (mode === 'register' && step === 'form') || step === 'reset') && !isPasswordValid)} 
                                        className={`w-full py-4 rounded-2xl font-bold flex items-center justify-center shadow-xl transition-all active:scale-[0.98] ${
                                            (isLoading || (( (mode === 'register' && step === 'form') || step === 'reset') && !isPasswordValid)) 
                                            ? 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none' 
                                            : 'bg-blue-600 text-white shadow-blue-200 hover:bg-blue-700'
                                        }`}
                                    >
                                        {isLoading ? <Loader2 className="animate-spin" /> : 
                                         step === 'forgot' ? t('auth_submit_send_code') :
                                         step === 'reset' ? t('auth_submit_reset') :
                                         step === 'verify' ? t('auth_submit_verify') :
                                         mode === 'login' ? t('auth_submit_login') : t('auth_submit_reg')}
                                    </button>

                                    {mode === 'login' && step === 'form' && (
                                        <button type="button" onClick={() => setStep('forgot')} className="w-full text-xs font-bold text-slate-400 hover:text-blue-600 transition-colors text-center">
                                            {t('auth_forgot_password')}
                                        </button>
                                    )}
                                </form>

                                {step === 'form' && (
                                    <>
                                        <div className="relative my-10 flex items-center justify-center">
                                            <div className="flex-1 border-t border-slate-100"></div>
                                            <span className="mx-6 text-[10px] font-black text-slate-300 uppercase tracking-[0.3em]">{t('auth_or_use')}</span>
                                            <div className="flex-1 border-t border-slate-100"></div>
                                        </div>
                                        <div className="flex flex-col gap-3">
                                            <button onClick={() => googleLogin()} className="w-full h-11 flex items-center justify-center gap-3 bg-white border border-[#dadce0] rounded-full hover:bg-slate-50 transition-all active:scale-[0.98] shadow-sm">
                                                <svg width="18" height="18" viewBox="0 0 48 48"><path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/><path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/><path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/><path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/></svg>
                                                <span className="text-sm font-bold text-slate-700">Google</span>
                                            </button>
                                        </div>
                                    </>
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>
            </div>
        </div>
    );
}
