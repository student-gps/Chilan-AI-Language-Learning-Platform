import { useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import apiClient from '../../../api/apiClient';

// sessionStorage key，tab 关闭后自动清除，不会跨 session 泄漏
const SS_KEY = 'chilan_auth_draft';

const loadDraft = () => {
    try {
        const raw = sessionStorage.getItem(SS_KEY);
        return raw ? JSON.parse(raw) : {};
    } catch {
        return {};
    }
};

const saveDraft = (patch) => {
    try {
        const current = loadDraft();
        sessionStorage.setItem(SS_KEY, JSON.stringify({ ...current, ...patch }));
    } catch { /* quota 超限等极端情况，静默忽略 */ }
};

const clearDraft = () => {
    try { sessionStorage.removeItem(SS_KEY); } catch { /* no-op */ }
};

export default function useAuthFlow({ navigate, language }) {
    const draft = loadDraft();

    // step/mode/email 从 sessionStorage 恢复，刷新页面不丢失
    const [step, setStepRaw] = useState(draft.step || 'form');
    const [mode, setModeRaw] = useState(draft.mode || 'login');
    const [email, setEmailRaw] = useState(draft.email || '');

    // password / code / confirmPassword 不持久化（安全起见）
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [code, setCode] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    const setStep = (v) => { setStepRaw(v); saveDraft({ step: v }); };
    const setMode = (v) => { setModeRaw(v); saveDraft({ mode: v }); };
    const setEmail = (v) => { setEmailRaw(v); saveDraft({ email: v }); };

    const checks = {
        length: password.length >= 8 && password.length <= 32,
        letter: /[A-Za-z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[^A-Za-z0-9]/.test(password),
        noSpace: !/\s/.test(password),
        match: (mode === 'register' || step === 'reset') ? (password === confirmPassword && confirmPassword !== '') : true,
    };

    const isPasswordValid = Object.values(checks).every(Boolean);

    const persistAuth = (responseData, fallbackEmail = '') => {
        localStorage.setItem('chilan_token', responseData.access_token);
        localStorage.setItem('chilan_user_id', responseData.user_id);
        localStorage.setItem('chilan_user_email', responseData.email || fallbackEmail);
        clearDraft(); // 登录成功，清除 auth 草稿
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            const authPath = '/auth';

            if (step === 'forgot') {
                await apiClient.post(`${authPath}/forgot-password`, { email });
                setStep('reset');
                setPassword('');
                setConfirmPassword('');
            } else if (step === 'reset') {
                await apiClient.post(`${authPath}/reset-password`, {
                    email,
                    code,
                    new_password: password,
                });
                clearDraft();
                setStep('success');
                setTimeout(() => {
                    setStep('form');
                    setMode('login');
                }, 2000);
            } else if (mode === 'register') {
                if (step === 'form') {
                    await apiClient.post(`${authPath}/signup`, { email, password, lang: language });
                    setStep('verify');
                } else {
                    await apiClient.post(`${authPath}/verify`, { email, code });
                    clearDraft(); // 注册验证成功，清除草稿
                    setStep('success');
                    setTimeout(() => {
                        setMode('login');
                        setStep('form');
                    }, 2000);
                }
            } else {
                const res = await apiClient.post(`${authPath}/login`, { email, password });
                persistAuth(res.data, email);
                setStep('success');
                setTimeout(() => navigate('/'), 2000);
            }
        } catch (err) {
            const status = err.response?.status;
            const detail = err.response?.data?.detail;
            const message = err.message;
            console.error('Auth request failed:', {
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
                    : `Operation failed${status ? ` (HTTP ${status})` : ''}`,
            );
        } finally {
            setIsLoading(false);
        }
    };

    const googleLogin = useGoogleLogin({
        onSuccess: async (tokenResponse) => {
            setIsLoading(true);
            try {
                const res = await apiClient.post('/auth/google', {
                    access_token: tokenResponse.access_token,
                });
                persistAuth(res.data);
                setStep('success');
                setTimeout(() => navigate('/'), 2000);
            } catch (err) {
                console.error('Google auth failed:', {
                    status: err.response?.status,
                    detail: err.response?.data?.detail,
                    message: err.message,
                    response: err.response?.data,
                });
                setError(
                    err.response?.data?.detail
                        ? `${err.response.data.detail}${err.response?.status ? ` (HTTP ${err.response.status})` : ''}`
                        : 'Google Auth Failed',
                );
            } finally {
                setIsLoading(false);
            }
        },
        onError: (errorResponse) => {
            console.error('Google OAuth error:', errorResponse);
            setError('Google OAuth Failed');
            setIsLoading(false);
        },
        onNonOAuthError: (errorResponse) => {
            console.error('Google OAuth non-oauth error:', errorResponse);
            setError('Google OAuth Popup Failed');
            setIsLoading(false);
        },
    });

    return {
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
    };
}
