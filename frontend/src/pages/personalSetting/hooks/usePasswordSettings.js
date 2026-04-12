import { useState } from 'react';
import apiClient from '../../../api/apiClient';

export default function usePasswordSettings(userId) {
    const [isEditingPassword, setIsEditingPassword] = useState(false);
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [passwordError, setPasswordError] = useState('');
    const [passwordSuccess, setPasswordSuccess] = useState('');
    const [isSavingPassword, setIsSavingPassword] = useState(false);
    const [showCurrentPassword, setShowCurrentPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);

    const passwordChecks = {
        length: newPassword.length >= 8 && newPassword.length <= 32,
        letter: /[A-Za-z]/.test(newPassword),
        number: /[0-9]/.test(newPassword),
        special: /[^A-Za-z0-9]/.test(newPassword),
        noSpace: !/\s/.test(newPassword),
        match: newPassword === confirmPassword && confirmPassword !== '',
        different: currentPassword !== '' && newPassword !== '' && currentPassword !== newPassword,
    };

    const resetPasswordForm = () => {
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setPasswordError('');
        setPasswordSuccess('');
        setShowCurrentPassword(false);
        setShowNewPassword(false);
        setShowConfirmPassword(false);
    };

    const handleStartEditingPassword = () => {
        setIsEditingPassword(true);
        setPasswordError('');
        setPasswordSuccess('');
    };

    const handleCancelEditingPassword = () => {
        setIsEditingPassword(false);
        resetPasswordForm();
    };

    const handleSavePassword = async () => {
        if (!userId) {
            setPasswordError('未找到当前用户');
            return;
        }

        if (!Object.values(passwordChecks).every(Boolean)) {
            setPasswordError('请先满足全部密码要求');
            return;
        }

        setIsSavingPassword(true);
        setPasswordError('');
        setPasswordSuccess('');

        try {
            await apiClient.put(`/auth/change-password/${userId}`, {
                current_password: currentPassword,
                new_password: newPassword,
            });
            setPasswordSuccess('密码已更新');
            resetPasswordForm();
            setIsEditingPassword(false);
        } catch (error) {
            setPasswordError(error.response?.data?.detail || '密码修改失败');
        } finally {
            setIsSavingPassword(false);
        }
    };

    return {
        confirmPassword,
        currentPassword,
        handleCancelEditingPassword,
        handleSavePassword,
        handleStartEditingPassword,
        isEditingPassword,
        isSavingPassword,
        newPassword,
        passwordChecks,
        passwordError,
        passwordSuccess,
        setConfirmPassword,
        setCurrentPassword,
        setNewPassword,
        showConfirmPassword,
        showCurrentPassword,
        showNewPassword,
        toggleConfirmPassword: () => setShowConfirmPassword((prev) => !prev),
        toggleCurrentPassword: () => setShowCurrentPassword((prev) => !prev),
        toggleNewPassword: () => setShowNewPassword((prev) => !prev),
    };
}
