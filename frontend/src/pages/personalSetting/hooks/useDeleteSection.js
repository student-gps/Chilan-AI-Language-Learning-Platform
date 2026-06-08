import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../../api/apiClient';
import { clearAuthStorage } from '../../../utils/authStorage';

export default function useDeleteSection(userId, loginProvider) {
    const { t } = useTranslation();
    const navigate = useNavigate();

    const [isDeleteOpen, setIsDeleteOpen] = useState(false);
    const [deleteConfirmText, setDeleteConfirmText] = useState('');
    const [deletePassword, setDeletePassword] = useState('');
    const [showDeletePassword, setShowDeletePassword] = useState(false);
    const [deleteError, setDeleteError] = useState('');
    const [deleteSuccess, setDeleteSuccess] = useState('');
    const [isDeletingAccount, setIsDeletingAccount] = useState(false);

    const handleToggleDelete = () => {
        const nextOpen = !isDeleteOpen;
        setIsDeleteOpen(nextOpen);
        if (!nextOpen) {
            setDeleteConfirmText('');
            setDeletePassword('');
            setDeleteError('');
            setDeleteSuccess('');
            setShowDeletePassword(false);
        }
    };

    const handleDeleteAccount = async () => {
        if (!userId) { setDeleteError(t('settings_user_missing')); return; }
        setIsDeletingAccount(true);
        setDeleteError('');
        setDeleteSuccess('');
        try {
            await apiClient.delete(`/auth/account/${userId}`, {
                data: {
                    confirm_text: deleteConfirmText,
                    current_password: loginProvider === 'password' ? deletePassword : null,
                },
            });
            setDeleteSuccess(t('settings_delete_success'));
            clearAuthStorage();
            setTimeout(() => navigate('/'), 1000);
        } catch (error) {
            setDeleteError(error.response?.data?.detail || t('settings_delete_failed'));
        } finally {
            setIsDeletingAccount(false);
        }
    };

    return {
        isDeleteOpen,
        deleteConfirmText,
        setDeleteConfirmText,
        deletePassword,
        setDeletePassword,
        showDeletePassword,
        setShowDeletePassword,
        deleteError,
        deleteSuccess,
        isDeletingAccount,
        handleToggleDelete,
        handleDeleteAccount,
    };
}
