import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { 
    Mail, Lock, ArrowLeft, Loader2,
    ShieldCheck, AlertCircle, Eye, EyeOff, Hash
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import AuthRequirement from './components/AuthRequirement';
import AuthSocialSection from './components/AuthSocialSection';
import AuthSuccessState from './components/AuthSuccessState';
import useAuthFlow from './hooks/useAuthFlow';

export default function Auth() {
    const { t, i18n } = useTranslation();
    const navigate = useNavigate();
    const {
        checks,
        code,
        confirmPassword,
        email,
        error,
        googleLogin,
        handleSubmit,
        isLoading,
        isPasswordValid,
        mode,
        password,
        setCode,
        setConfirmPassword,
        setEmail,
        setMode,
        setPassword,
        setShowConfirmPassword,
        setShowPassword,
        setStep,
        showConfirmPassword,
        showPassword,
        step,
    } = useAuthFlow({
        navigate,
        language: i18n.language,
    });

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
                            <AuthSuccessState
                                isLogin={mode === 'login'}
                                title={mode === 'login' ? t('auth_login_success_title') : t('auth_success_title')}
                                subtitle={mode === 'login' ? t('auth_login_success_subtitle') : t('auth_success_subtitle')}
                            />
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
                                                <AuthRequirement met={checks.length} text={t('auth_pw_req_length')} />
                                                <AuthRequirement met={checks.letter} text={t('auth_pw_req_letter')} />
                                                <AuthRequirement met={checks.number} text={t('auth_pw_req_number')} />
                                                <AuthRequirement met={checks.special} text={t('auth_pw_req_special')} />
                                                <AuthRequirement met={checks.noSpace} text={t('auth_pw_req_no_space')} />
                                                <AuthRequirement met={checks.match} text={t('auth_pw_match')} />
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
                                    <AuthSocialSection dividerLabel={t('auth_or_use')} onGoogleLogin={() => googleLogin()} />
                                )}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>
            </div>
        </div>
    );
}
