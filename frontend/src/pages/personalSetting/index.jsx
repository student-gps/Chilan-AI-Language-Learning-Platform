import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    Bell,
    CircleHelp,
    Clock3,
    Globe,
    Languages,
    LockKeyhole,
    Mail,
    MessageSquareMore,
    Mic2,
    MonitorCog,
    NotebookPen,
    Shield,
    Siren,
    SlidersHorizontal,
    Sparkles,
    LaptopMinimal,
    User,
} from 'lucide-react';
import apiClient from '../../api/apiClient';
import { clearAuthStorage } from '../../utils/authStorage';
import {
    BookOpenGlyph,
    ChoicePillGroup,
    DeleteAccountSection,
    EditableInputRow,
    InputRow,
    PasswordSection,
    ProfilePanel,
    ProviderPasswordNotice,
    SecurityLogSection,
    SelectRow,
    SettingsCard,
    SupportLink,
    TimeRow,
    ToggleRow,
} from './components/PersonalSettingSections';
import usePasswordSettings from './hooks/usePasswordSettings';

const pageMotion = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { staggerChildren: 0.08 } },
};

const blockMotion = {
    hidden: { opacity: 0, y: 18 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 120, damping: 18 } },
};

export default function Personal_Setting() {
    const navigate = useNavigate();
    const userId = localStorage.getItem('chilan_user_id');
    const [profile, setProfile] = useState({
        username: 'Chilan Learner',
        email: localStorage.getItem('chilan_user_email') || '',
        loginProvider: 'password',
    });
    const [isProfileLoading, setIsProfileLoading] = useState(true);
    const [isEditingNickname, setIsEditingNickname] = useState(false);
    const [nicknameDraft, setNicknameDraft] = useState('');
    const [nicknameError, setNicknameError] = useState('');
    const [isSavingNickname, setIsSavingNickname] = useState(false);
    const [isSecurityOpen, setIsSecurityOpen] = useState(false);
    const [securityLogs, setSecurityLogs] = useState([]);
    const [isSecurityLoading, setIsSecurityLoading] = useState(false);
    const [securityError, setSecurityError] = useState('');
    const [isDeleteOpen, setIsDeleteOpen] = useState(false);
    const [deleteConfirmText, setDeleteConfirmText] = useState('');
    const [deletePassword, setDeletePassword] = useState('');
    const [showDeletePassword, setShowDeletePassword] = useState(false);
    const [deleteError, setDeleteError] = useState('');
    const [deleteSuccess, setDeleteSuccess] = useState('');
    const [isDeletingAccount, setIsDeletingAccount] = useState(false);
    const [strictness, setStrictness] = useState('balanced');
    const [interfaceLang, setInterfaceLang] = useState('auto');
    const [nativeLang, setNativeLang] = useState('zh');
    const [showPinyin, setShowPinyin] = useState(true);
    const [showMeaning, setShowMeaning] = useState(true);
    const [showGrammar, setShowGrammar] = useState(false);
    const [showAiExplanation, setShowAiExplanation] = useState(true);
    const [autoPlayAudio, setAutoPlayAudio] = useState(true);
    const [playbackSpeed, setPlaybackSpeed] = useState('1.0x');
    const [mailNotifications, setMailNotifications] = useState(true);
    const [dailyReminder, setDailyReminder] = useState(true);
    const [reviewReminderTime, setReviewReminderTime] = useState('20:00');
    const [courseUpdates, setCourseUpdates] = useState(true);
    const [securityAlerts, setSecurityAlerts] = useState(true);
    const {
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
        toggleConfirmPassword,
        toggleCurrentPassword,
        toggleNewPassword,
    } = usePasswordSettings(userId);

    useEffect(() => {
        let active = true;

        const loadProfile = async () => {
            if (!userId) {
                setIsProfileLoading(false);
                return;
            }

            try {
                const res = await apiClient.get(`/auth/profile/${userId}`);
                if (!active) return;

                const nextProfile = {
                    username: res.data.username || 'Chilan Learner',
                    email: res.data.email || '',
                    loginProvider: res.data.login_provider || 'password',
                };

                setProfile(nextProfile);
                setNicknameDraft(nextProfile.username || 'Chilan Learner');
                if (nextProfile.email) {
                    localStorage.setItem('chilan_user_email', nextProfile.email);
                }
            } catch (error) {
                if (!active) return;
                console.error('Failed to load profile:', error);
            } finally {
                if (active) {
                    setIsProfileLoading(false);
                }
            }
        };

        loadProfile();

        return () => {
            active = false;
        };
    }, [userId]);

    const validateNickname = (value) => {
        const trimmed = value.trim();
        if (trimmed.length < 2 || trimmed.length > 24) {
            return '昵称需为 2 到 24 个字符';
        }
        if (!/^[A-Za-z0-9_\-.\u4e00-\u9fff ]+$/.test(trimmed)) {
            return '昵称仅支持中英文、数字、空格和 _-.';
        }
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
        const validationError = validateNickname(nicknameDraft);
        if (validationError) {
            setNicknameError(validationError);
            return;
        }
        if (!userId) {
            setNicknameError('未找到当前用户');
            return;
        }

        setIsSavingNickname(true);
        setNicknameError('');
        try {
            const res = await apiClient.put(`/auth/profile/${userId}`, {
                username: nicknameDraft.trim(),
            });
            setProfile((prev) => ({
                ...prev,
                username: res.data.username || nicknameDraft.trim(),
                email: res.data.email || prev.email,
            }));
            setNicknameDraft(res.data.username || nicknameDraft.trim());
            setIsEditingNickname(false);
        } catch (error) {
            setNicknameError(error.response?.data?.detail || '昵称保存失败');
        } finally {
            setIsSavingNickname(false);
        }
    };

    const loadSecurityLogs = async () => {
        if (!userId) {
            setSecurityError('未找到当前用户');
            return;
        }
        setIsSecurityLoading(true);
        setSecurityError('');
        try {
            const res = await apiClient.get(`/auth/login-history/${userId}`);
            setSecurityLogs(res.data.logs || []);
        } catch (error) {
            setSecurityError(error.response?.data?.detail || '登录记录加载失败');
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
        if (!userId) {
            setDeleteError('未找到当前用户');
            return;
        }

        setIsDeletingAccount(true);
        setDeleteError('');
        setDeleteSuccess('');
        try {
            await apiClient.delete(`/auth/account/${userId}`, {
                data: {
                    confirm_text: deleteConfirmText,
                    current_password: profile.loginProvider === 'password' ? deletePassword : null,
                },
            });
            setDeleteSuccess('账号已注销，正在返回首页');
            clearAuthStorage();
            setTimeout(() => navigate('/'), 1000);
        } catch (error) {
            setDeleteError(error.response?.data?.detail || '账号注销失败');
        } finally {
            setIsDeletingAccount(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-50 pt-24 pb-20 relative overflow-hidden">
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute -top-10 left-0 w-80 h-80 rounded-full bg-gradient-to-br from-blue-100 via-sky-50 to-transparent blur-3xl opacity-80" />
                <div className="absolute top-1/3 right-0 w-96 h-96 rounded-full bg-gradient-to-br from-indigo-100 via-violet-50 to-transparent blur-3xl opacity-60" />
                <div className="absolute bottom-0 left-1/4 w-80 h-72 rounded-full bg-gradient-to-tr from-cyan-100 via-white to-transparent blur-3xl opacity-60" />
            </div>

            <motion.div
                variants={pageMotion}
                initial="hidden"
                animate="show"
                className="max-w-4xl mx-auto px-6 md:px-8 relative z-10"
            >
                <div className="space-y-8">
                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow=""
                            title="账户与安全"
                            description=""
                            icon={<Shield size={18} />}
                        >
                            <ProfilePanel username={profile.username} email={profile.email} isLoading={isProfileLoading} />
                            <div className="mt-5 space-y-4">
                                <EditableInputRow
                                    label="昵称"
                                    value={profile.username}
                                    draft={nicknameDraft}
                                    isEditing={isEditingNickname}
                                    isSaving={isSavingNickname}
                                    error={nicknameError}
                                    icon={<User size={16} />}
                                    onChange={setNicknameDraft}
                                    onEdit={handleStartEditingNickname}
                                    onCancel={handleCancelEditingNickname}
                                    onSave={handleSaveNickname}
                                />
                                <InputRow label="邮箱" value={profile.email} icon={<Mail size={16} />} />
                                {profile.loginProvider === 'password' ? (
                                    <PasswordSection
                                        icon={<LockKeyhole size={18} />}
                                        isEditing={isEditingPassword}
                                        isSaving={isSavingPassword}
                                        currentPassword={currentPassword}
                                        newPassword={newPassword}
                                        confirmPassword={confirmPassword}
                                        passwordChecks={passwordChecks}
                                        passwordError={passwordError}
                                        passwordSuccess={passwordSuccess}
                                        showCurrentPassword={showCurrentPassword}
                                        showNewPassword={showNewPassword}
                                        showConfirmPassword={showConfirmPassword}
                                        onStartEdit={handleStartEditingPassword}
                                        onCancel={handleCancelEditingPassword}
                                        onSave={handleSavePassword}
                                        onCurrentPasswordChange={setCurrentPassword}
                                        onNewPasswordChange={setNewPassword}
                                        onConfirmPasswordChange={setConfirmPassword}
                                        onToggleCurrentPassword={toggleCurrentPassword}
                                        onToggleNewPassword={toggleNewPassword}
                                        onToggleConfirmPassword={toggleConfirmPassword}
                                    />
                                ) : (
                                    <ProviderPasswordNotice provider={profile.loginProvider} />
                                )}
                                <SecurityLogSection
                                    icon={<LaptopMinimal size={18} />}
                                    isOpen={isSecurityOpen}
                                    isLoading={isSecurityLoading}
                                    logs={securityLogs}
                                    error={securityError}
                                    onToggle={handleToggleSecurity}
                                    onRefresh={loadSecurityLogs}
                                />
                                <DeleteAccountSection
                                    provider={profile.loginProvider}
                                    isOpen={isDeleteOpen}
                                    isDeleting={isDeletingAccount}
                                    confirmText={deleteConfirmText}
                                    password={deletePassword}
                                    error={deleteError}
                                    success={deleteSuccess}
                                    showPassword={showDeletePassword}
                                    onToggle={handleToggleDelete}
                                    onConfirmTextChange={setDeleteConfirmText}
                                    onPasswordChange={setDeletePassword}
                                    onTogglePassword={() => setShowDeletePassword((prev) => !prev)}
                                    onDelete={handleDeleteAccount}
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>

                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow="语言"
                            title="界面语言 / 母语"
                            description="统一管理界面显示语言和学习母语。"
                            icon={<Languages size={18} />}
                        >
                            <div className="space-y-4">
                                <SelectRow
                                    label="界面语言"
                                    icon={<Globe size={16} />}
                                    value={interfaceLang}
                                    onChange={setInterfaceLang}
                                    options={[
                                        { value: 'auto', label: '自动跟随系统' },
                                        { value: 'zh', label: '简体中文' },
                                        { value: 'en', label: '英语' },
                                        { value: 'jp', label: '日语' },
                                        { value: 'fr', label: '法语' },
                                    ]}
                                />
                                <SelectRow
                                    label="母语"
                                    icon={<Languages size={16} />}
                                    value={nativeLang}
                                    onChange={setNativeLang}
                                    options={[
                                        { value: 'zh', label: '中文' },
                                        { value: 'en', label: '英语' },
                                        { value: 'jp', label: '日语' },
                                        { value: 'fr', label: '法语' },
                                        { value: 'de', label: '德语' },
                                    ]}
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>

                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow="答题反馈"
                            title="答题与反馈设置"
                            description="控制判题标准、提示信息和语音播放方式。"
                            icon={<NotebookPen size={18} />}
                        >
                            <div className="space-y-5">
                                <ChoicePillGroup
                                    label="判题严格度偏好"
                                    icon={<SlidersHorizontal size={16} />}
                                    value={strictness}
                                    onChange={setStrictness}
                                    options={[
                                        { value: 'strict', label: '严格' },
                                        { value: 'balanced', label: '平衡' },
                                        { value: 'friendly', label: '宽松' },
                                    ]}
                                />

                                <div className="rounded-[2rem] border border-slate-200 bg-slate-50/80 p-5">
                                    <p className="mb-4 text-xs font-black tracking-[0.12em] text-slate-400">默认提示</p>
                                    <div className="space-y-3">
                                        <ToggleRow
                                            icon={<Languages size={16} />}
                                            title="默认显示拼音"
                                            enabled={showPinyin}
                                            onChange={setShowPinyin}
                                        />
                                        <ToggleRow
                                            icon={<BookOpenGlyph />}
                                            title="默认显示释义"
                                            enabled={showMeaning}
                                            onChange={setShowMeaning}
                                        />
                                        <ToggleRow
                                            icon={<CircleHelp size={16} />}
                                            title="默认显示语法提示"
                                            enabled={showGrammar}
                                            onChange={setShowGrammar}
                                        />
                                    </div>
                                </div>

                                <ToggleRow
                                    icon={<Sparkles size={16} />}
                                    title="答错后立即显示 AI 解释"
                                    description="在用户答错后马上给出解释、错误分析和更自然的替代表达。"
                                    enabled={showAiExplanation}
                                    onChange={setShowAiExplanation}
                                />
                                <ToggleRow
                                    icon={<Mic2 size={16} />}
                                    title="音频自动播放"
                                    description="进入题目或讲解内容时自动播报音频。"
                                    enabled={autoPlayAudio}
                                    onChange={setAutoPlayAudio}
                                />
                                <SelectRow
                                    label="发音语速"
                                    icon={<Clock3 size={16} />}
                                    value={playbackSpeed}
                                    onChange={setPlaybackSpeed}
                                    options={[
                                        { value: '0.8x', label: '0.8x 慢速' },
                                        { value: '1.0x', label: '1.0x 标准' },
                                        { value: '1.2x', label: '1.2x 稍快' },
                                    ]}
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>

                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow="通知提醒"
                            title="通知与提醒"
                            description="统一管理学习提醒、课程更新和账号通知。"
                            icon={<Bell size={18} />}
                        >
                            <div className="space-y-4">
                                <ToggleRow
                                    icon={<Mail size={16} />}
                                    title="邮件通知开关"
                                    description="统一控制所有邮件类通知。"
                                    enabled={mailNotifications}
                                    onChange={setMailNotifications}
                                />
                                <ToggleRow
                                    icon={<Bell size={16} />}
                                    title="每日学习提醒"
                                    description="在每天固定时间提醒用户开始学习。"
                                    enabled={dailyReminder}
                                    onChange={setDailyReminder}
                                />
                                <TimeRow
                                    label="复习提醒时间"
                                    value={reviewReminderTime}
                                    onChange={setReviewReminderTime}
                                />
                                <ToggleRow
                                    icon={<NotebookPen size={16} />}
                                    title="课程更新提醒"
                                    description="新课上线、课程内容变更时发送提醒。"
                                    enabled={courseUpdates}
                                    onChange={setCourseUpdates}
                                />
                                <ToggleRow
                                    icon={<Siren size={16} />}
                                    title="账号安全通知"
                                    description="密码更新、异常登录等安全事件即时提醒。"
                                    enabled={securityAlerts}
                                    onChange={setSecurityAlerts}
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>

                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow="帮助支持"
                            title="帮助与支持"
                            description="查看帮助入口、反馈渠道和版本信息。"
                            icon={<MessageSquareMore size={18} />}
                        >
                            <div className="space-y-3">
                                <SupportLink
                                    icon={<CircleHelp size={17} />}
                                    title="常见问题"
                                    description="账号、学习流、AI 判题和提醒相关说明。"
                                />
                                <SupportLink
                                    icon={<MessageSquareMore size={17} />}
                                    title="问题反馈"
                                    description="提交 bug、体验建议和课程内容修正意见。"
                                />
                                <SupportLink
                                    icon={<Mail size={17} />}
                                    title="联系方式"
                                    description="支持邮箱、合作联系和课程沟通入口。"
                                />
                                <SupportLink
                                    icon={<MonitorCog size={17} />}
                                    title="版本号与更新说明"
                                    description="展示当前版本和最近更新内容。"
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>
                </div>
            </motion.div>
        </div>
    );
}

