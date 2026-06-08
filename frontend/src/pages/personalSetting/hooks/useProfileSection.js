import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import apiClient from '../../../api/apiClient';

export default function useProfileSection(userId, userEmail) {
    const { t } = useTranslation();

    const [profile, setProfile] = useState({
        username: 'Chilan Learner',
        email: userEmail || '',
        loginProvider: 'password',
    });
    const [isProfileLoading, setIsProfileLoading] = useState(true);
    const [isEditingNickname, setIsEditingNickname] = useState(false);
    const [nicknameDraft, setNicknameDraft] = useState('');
    const [nicknameError, setNicknameError] = useState('');
    const [isSavingNickname, setIsSavingNickname] = useState(false);

    useEffect(() => {
        let active = true;
        const loadProfile = async () => {
            if (!userId) { setIsProfileLoading(false); return; }
            try {
                const res = await apiClient.get(`/auth/profile/${userId}`);
                if (!active) return;
                const next = {
                    username: res.data.username || 'Chilan Learner',
                    email: res.data.email || '',
                    loginProvider: res.data.login_provider || 'password',
                };
                setProfile(next);
                setNicknameDraft(next.username);
                if (next.email) localStorage.setItem('chilan_user_email', next.email);
            } catch {
                // 保留默认值，不阻断页面
            } finally {
                if (active) setIsProfileLoading(false);
            }
        };
        loadProfile();
        return () => { active = false; };
    }, [userId]);

    const validateNickname = (value) => {
        const trimmed = value.trim();
        if (trimmed.length < 2 || trimmed.length > 24) return t('settings_nickname_length_error');
        if (!/^[A-Za-z0-9_\-.一-鿿 ]+$/.test(trimmed)) return t('settings_nickname_format_error');
        return '';
    };

    const handleStartEditingNickname = () => {
        setNicknameDraft(profile.username || '');
        setNicknameError('');
        setIsEditingNickname(true);
    };

    const handleCancelEditingNickname = () => {
        setNicknameDraft(profile.username || '');
        setNicknameError('');
        setIsEditingNickname(false);
    };

    const handleSaveNickname = async () => {
        const err = validateNickname(nicknameDraft);
        if (err) { setNicknameError(err); return; }
        if (!userId) { setNicknameError(t('settings_user_missing')); return; }
        setIsSavingNickname(true);
        setNicknameError('');
        try {
            const res = await apiClient.put(`/auth/profile/${userId}`, { username: nicknameDraft.trim() });
            const saved = res.data.username || nicknameDraft.trim();
            setProfile(prev => ({ ...prev, username: saved, email: res.data.email || prev.email }));
            setNicknameDraft(saved);
            setIsEditingNickname(false);
        } catch (error) {
            setNicknameError(error.response?.data?.detail || t('settings_nickname_save_failed'));
        } finally {
            setIsSavingNickname(false);
        }
    };

    return {
        profile,
        isProfileLoading,
        isEditingNickname,
        nicknameDraft,
        setNicknameDraft,
        nicknameError,
        isSavingNickname,
        handleStartEditingNickname,
        handleCancelEditingNickname,
        handleSaveNickname,
    };
}
