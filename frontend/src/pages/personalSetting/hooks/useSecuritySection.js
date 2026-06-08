import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import apiClient from '../../../api/apiClient';

export default function useSecuritySection(userId) {
    const { t } = useTranslation();

    const [isSecurityOpen, setIsSecurityOpen] = useState(false);
    const [securityLogs, setSecurityLogs] = useState([]);
    const [isSecurityLoading, setIsSecurityLoading] = useState(false);
    const [securityError, setSecurityError] = useState('');

    const loadSecurityLogs = async () => {
        if (!userId) { setSecurityError(t('settings_user_missing')); return; }
        setIsSecurityLoading(true);
        setSecurityError('');
        try {
            const res = await apiClient.get(`/auth/login-history/${userId}`);
            setSecurityLogs(res.data.logs || []);
        } catch (error) {
            setSecurityError(error.response?.data?.detail || t('settings_login_history_failed'));
        } finally {
            setIsSecurityLoading(false);
        }
    };

    const handleToggleSecurity = async () => {
        const nextOpen = !isSecurityOpen;
        setIsSecurityOpen(nextOpen);
        if (nextOpen && securityLogs.length === 0 && !isSecurityLoading) {
            await loadSecurityLogs();
        }
    };

    return {
        isSecurityOpen,
        securityLogs,
        isSecurityLoading,
        securityError,
        handleToggleSecurity,
        loadSecurityLogs,
    };
}
