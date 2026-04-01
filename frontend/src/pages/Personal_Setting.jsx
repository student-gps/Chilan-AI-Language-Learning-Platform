import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
    Bell,
    Check,
    ChevronRight,
    CircleHelp,
    Clock3,
    Edit3,
    Eye,
    EyeOff,
    Globe,
    Languages,
    LockKeyhole,
    Loader2,
    Mail,
    MessageSquareMore,
    Mic2,
    MonitorCog,
    NotebookPen,
    Shield,
    Siren,
    SlidersHorizontal,
    Sparkles,
    Trash2,
    User,
    LaptopMinimal,
} from 'lucide-react';
import apiClient from '../api/apiClient';

const pageMotion = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0, transition: { staggerChildren: 0.08 } },
};

const blockMotion = {
    hidden: { opacity: 0, y: 18 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 120, damping: 18 } },
};

export default function Personal_Setting() {
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
    const [isSecurityOpen, setIsSecurityOpen] = useState(false);
    const [securityLogs, setSecurityLogs] = useState([]);
    const [isSecurityLoading, setIsSecurityLoading] = useState(false);
    const [securityError, setSecurityError] = useState('');
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

    const passwordChecks = {
        length: newPassword.length >= 8 && newPassword.length <= 32,
        letter: /[A-Za-z]/.test(newPassword),
        number: /[0-9]/.test(newPassword),
        special: /[^A-Za-z0-9]/.test(newPassword),
        noSpace: !/\s/.test(newPassword),
        match: newPassword === confirmPassword && confirmPassword !== '',
        different: currentPassword !== '' && newPassword !== '' && currentPassword !== newPassword,
    };
    const isPasswordValid = Object.values(passwordChecks).every(Boolean);

    const handleStartEditingPassword = () => {
        setIsEditingPassword(true);
        setPasswordError('');
        setPasswordSuccess('');
    };

    const handleCancelEditingPassword = () => {
        setIsEditingPassword(false);
        setCurrentPassword('');
        setNewPassword('');
        setConfirmPassword('');
        setPasswordError('');
        setPasswordSuccess('');
        setShowCurrentPassword(false);
        setShowNewPassword(false);
        setShowConfirmPassword(false);
    };

    const handleSavePassword = async () => {
        if (!userId) {
            setPasswordError('未找到当前用户');
            return;
        }
        if (!isPasswordValid) {
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
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
            setShowCurrentPassword(false);
            setShowNewPassword(false);
            setShowConfirmPassword(false);
            setIsEditingPassword(false);
        } catch (error) {
            setPasswordError(error.response?.data?.detail || '密码修改失败');
        } finally {
            setIsSavingPassword(false);
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
                            eyebrow="Account & Security"
                            title="账户与安全"
                            description="基本资料、密码、安全记录和注销操作都放在这一组里，按最常见的使用顺序往下排。"
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
                                        onToggleCurrentPassword={() => setShowCurrentPassword((prev) => !prev)}
                                        onToggleNewPassword={() => setShowNewPassword((prev) => !prev)}
                                        onToggleConfirmPassword={() => setShowConfirmPassword((prev) => !prev)}
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
                                <DangerRow />
                            </div>
                        </SettingsCard>
                    </motion.div>

                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow="Language"
                            title="界面语言 / 母语"
                            description="显示语言和学习母语分开设置，页面上也按从上往下的方式一项一项展示。"
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
                                        { value: 'en', label: 'English' },
                                        { value: 'jp', label: '日本語' },
                                        { value: 'fr', label: 'Français' },
                                    ]}
                                />
                                <SelectRow
                                    label="母语"
                                    icon={<Languages size={16} />}
                                    value={nativeLang}
                                    onChange={setNativeLang}
                                    options={[
                                        { value: 'zh', label: '中文' },
                                        { value: 'en', label: 'English' },
                                        { value: 'jp', label: '日本語' },
                                        { value: 'fr', label: 'Français' },
                                        { value: 'de', label: 'Deutsch' },
                                    ]}
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>

                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow="Learning Feedback"
                            title="答题与反馈设置"
                            description="这一组和产品核心体验关系最大，所以也改成更慢节奏的单列排版，避免太紧。"
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
                                    <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-400 mb-4">Default Hints</p>
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
                            eyebrow="Notifications"
                            title="通知与提醒"
                            description="学习提醒、复习提醒、课程更新和安全通知都按一个个设置项自然往下排列。"
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
                            eyebrow="Support"
                            title="帮助与支持"
                            description="把支持入口保持简洁，全部按列表形式往下放。"
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

function SettingsCard({ eyebrow, title, description, icon, children }) {
    return (
        <div className="rounded-[2.5rem] border border-white/80 bg-white/90 p-7 md:p-8 shadow-2xl shadow-slate-200/50">
            <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shadow-sm shadow-blue-100">
                    {icon}
                </div>
                <div>
                    <p className="text-[11px] font-black uppercase tracking-[0.24em] text-slate-400">{eyebrow}</p>
                    <h2 className="mt-2 text-2xl font-black tracking-tight text-slate-900">{title}</h2>
                    <p className="mt-2 text-sm leading-relaxed text-slate-500 max-w-2xl">{description}</p>
                </div>
            </div>
            {children}
        </div>
    );
}

function ProfilePanel({ username, email, isLoading }) {
    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-5 shadow-sm">
            <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-4 min-w-0">
                    <div className="h-[72px] w-[72px] rounded-[1.75rem] bg-gradient-to-br from-blue-600 via-indigo-500 to-cyan-400 text-white flex items-center justify-center shadow-xl shadow-blue-200 shrink-0">
                        <User size={28} />
                    </div>
                    <div className="min-w-0">
                        <h3 className="text-xl font-black tracking-tight text-slate-900">
                            {isLoading ? 'Loading...' : (username || 'Chilan Learner')}
                        </h3>
                        <p className="mt-1 text-sm font-medium text-slate-500 truncate">
                            {isLoading ? 'Loading profile...' : (email || 'No email')}
                        </p>
                    </div>
                </div>
                <button className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-black text-slate-700 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600 transition-colors">
                    修改头像
                </button>
            </div>
        </div>
    );
}

function InputRow({ label, value, icon }) {
    return (
        <label className="block">
            <span className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                {icon}
                {label}
            </span>
            <div className="relative">
                <input
                    value={value}
                    readOnly
                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 outline-none"
                />
                {!value ? (
                    <div className="absolute inset-y-0 right-4 flex items-center text-slate-300">
                        <Loader2 size={16} className="animate-spin" />
                    </div>
                ) : null}
            </div>
        </label>
    );
}

function EditableInputRow({
    label,
    value,
    draft,
    isEditing,
    isSaving,
    error,
    icon,
    onChange,
    onEdit,
    onCancel,
    onSave,
}) {
    return (
        <label className="block">
            <span className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                {icon}
                {label}
            </span>
            <div className="rounded-[1.6rem] border border-slate-200 bg-white px-4 py-3 shadow-sm">
                <div className="flex items-center gap-3">
                    <input
                        value={isEditing ? draft : value}
                        onChange={(e) => onChange(e.target.value)}
                        readOnly={!isEditing}
                        className="flex-1 bg-transparent text-sm font-bold text-slate-700 outline-none"
                    />
                    {isEditing ? (
                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                onClick={onCancel}
                                className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-black text-slate-500 hover:border-slate-300 hover:text-slate-700 transition-colors"
                            >
                                取消
                            </button>
                            <button
                                type="button"
                                onClick={onSave}
                                disabled={isSaving}
                                className="rounded-full bg-slate-900 px-3 py-1.5 text-xs font-black text-white hover:bg-blue-600 transition-colors disabled:bg-slate-300"
                            >
                                {isSaving ? <Loader2 size={14} className="animate-spin" /> : <span className="inline-flex items-center gap-1"><Check size={14} />保存</span>}
                            </button>
                        </div>
                    ) : (
                        <button
                            type="button"
                            onClick={onEdit}
                            className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-black text-slate-600 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                        >
                            <span className="inline-flex items-center gap-1">
                                <Edit3 size={13} />
                                修改
                            </span>
                        </button>
                    )}
                </div>
                {isEditing ? (
                    <p className="mt-3 text-xs font-medium text-slate-400">
                        2-24 个字符，支持中英文、数字、空格和 `_ - .`，且昵称不能重复。
                    </p>
                ) : null}
                {error ? <p className="mt-2 text-xs font-bold text-red-500">{error}</p> : null}
            </div>
        </label>
    );
}

function PasswordSection({
    icon,
    isEditing,
    isSaving,
    currentPassword,
    newPassword,
    confirmPassword,
    passwordChecks,
    passwordError,
    passwordSuccess,
    showCurrentPassword,
    showNewPassword,
    showConfirmPassword,
    onStartEdit,
    onCancel,
    onSave,
    onCurrentPasswordChange,
    onNewPasswordChange,
    onConfirmPasswordChange,
    onToggleCurrentPassword,
    onToggleNewPassword,
    onToggleConfirmPassword,
}) {
    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="w-11 h-11 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                    {icon}
                </span>
                <div className="flex-1">
                    <div className="flex items-center justify-between gap-4">
                        <div>
                            <h3 className="text-sm font-black text-slate-900">修改密码</h3>
                            <p className="mt-1 text-sm leading-relaxed text-slate-500">
                                使用当前密码验证身份，再设置一个新的登录密码。
                            </p>
                        </div>
                        {!isEditing ? (
                            <button
                                type="button"
                                onClick={onStartEdit}
                                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-black text-slate-600 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                            >
                                修改
                            </button>
                        ) : null}
                    </div>

                    {isEditing ? (
                        <div className="mt-4 space-y-4">
                            <PasswordInput
                                label="当前密码"
                                value={currentPassword}
                                onChange={onCurrentPasswordChange}
                                visible={showCurrentPassword}
                                onToggleVisible={onToggleCurrentPassword}
                            />
                            <PasswordInput
                                label="新密码"
                                value={newPassword}
                                onChange={onNewPasswordChange}
                                visible={showNewPassword}
                                onToggleVisible={onToggleNewPassword}
                            />
                            <PasswordInput
                                label="确认新密码"
                                value={confirmPassword}
                                onChange={onConfirmPasswordChange}
                                visible={showConfirmPassword}
                                onToggleVisible={onToggleConfirmPassword}
                            />

                            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    <Requirement met={passwordChecks.length} text="8 到 32 位" />
                                    <Requirement met={passwordChecks.letter} text="至少一个字母" />
                                    <Requirement met={passwordChecks.number} text="至少一个数字" />
                                    <Requirement met={passwordChecks.special} text="至少一个特殊字符" />
                                    <Requirement met={passwordChecks.noSpace} text="不能有空格" />
                                    <Requirement met={passwordChecks.match} text="确认密码一致" />
                                    <Requirement met={passwordChecks.different} text="新旧密码不能相同" />
                                </div>
                            </div>

                            {passwordError ? <p className="text-xs font-bold text-red-500">{passwordError}</p> : null}
                            {passwordSuccess ? <p className="text-xs font-bold text-emerald-600">{passwordSuccess}</p> : null}

                            <div className="flex items-center justify-end gap-2">
                                <button
                                    type="button"
                                    onClick={onCancel}
                                    className="rounded-full border border-slate-200 px-4 py-2 text-xs font-black text-slate-500 hover:border-slate-300 hover:text-slate-700 transition-colors"
                                >
                                    取消
                                </button>
                                <button
                                    type="button"
                                    onClick={onSave}
                                    disabled={isSaving}
                                    className="rounded-full bg-slate-900 px-4 py-2 text-xs font-black text-white hover:bg-blue-600 transition-colors disabled:bg-slate-300"
                                >
                                    {isSaving ? <Loader2 size={14} className="animate-spin" /> : '保存新密码'}
                                </button>
                            </div>
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
}

function PasswordInput({ label, value, onChange, visible, onToggleVisible }) {
    return (
        <label className="block">
            <span className="mb-2 block text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                {label}
            </span>
            <div className="relative">
                <input
                    type={visible ? 'text' : 'password'}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 pr-12 text-sm font-bold text-slate-700 outline-none focus:border-blue-300"
                />
                <button
                    type="button"
                    onClick={onToggleVisible}
                    className="absolute inset-y-0 right-4 flex items-center text-slate-400 hover:text-blue-600"
                >
                    {visible ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
            </div>
        </label>
    );
}

function Requirement({ met, text }) {
    return (
        <div className={`flex items-center gap-2 text-xs font-bold ${met ? 'text-emerald-600' : 'text-slate-300'}`}>
            {met ? <Check size={12} strokeWidth={3} /> : <div className="h-3 w-3 rounded-full border-2 border-slate-200" />}
            {text}
        </div>
    );
}

function ProviderPasswordNotice({ provider }) {
    const providerName = provider === 'google' ? 'Google' : 'Apple';

    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="w-11 h-11 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                    <LockKeyhole size={18} />
                </span>
                <div className="flex-1">
                    <h3 className="text-sm font-black text-slate-900">修改密码</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-500">
                        当前账号通过 {providerName} 登录，密码由 {providerName} 账户管理，这里不提供单独修改密码。
                    </p>
                </div>
            </div>
        </div>
    );
}

function SecurityLogSection({ icon, isOpen, isLoading, logs, error, onToggle, onRefresh }) {
    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="w-11 h-11 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                    {icon}
                </span>
                <div className="flex-1">
                    <div className="flex items-center justify-between gap-4">
                        <div>
                            <h3 className="text-sm font-black text-slate-900">账号安全记录</h3>
                            <p className="mt-1 text-sm leading-relaxed text-slate-500">
                                查看最近登录时间、登录方式、设备信息和访问来源。
                            </p>
                        </div>
                        <button
                            type="button"
                            onClick={onToggle}
                            className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-black text-slate-600 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                        >
                            <span className="inline-flex items-center gap-1">
                                {isOpen ? '收起' : '查看'}
                                <ChevronRight size={14} className={`transition-transform ${isOpen ? 'rotate-90' : ''}`} />
                            </span>
                        </button>
                    </div>
                    {isOpen ? (
                        <div className="mt-4 space-y-3">
                            <div className="flex justify-end">
                                <button
                                    type="button"
                                    onClick={onRefresh}
                                    className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-black text-slate-500 hover:border-slate-300 hover:text-slate-700 transition-colors"
                                >
                                    刷新记录
                                </button>
                            </div>
                            {isLoading ? (
                                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm font-bold text-slate-400 flex items-center justify-center gap-2">
                                    <Loader2 size={16} className="animate-spin" />
                                    加载中
                                </div>
                            ) : null}
                            {error ? (
                                <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-xs font-bold text-red-500">
                                    {error}
                                </div>
                            ) : null}
                            {!isLoading && !error && logs.length === 0 ? (
                                <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm font-bold text-slate-400">
                                    暂无登录记录
                                </div>
                            ) : null}
                            {!isLoading && !error && logs.length > 0 ? (
                                <div className="space-y-3">
                                    {logs.map((log) => (
                                        <SecurityLogItem key={log.log_id} log={log} />
                                    ))}
                                </div>
                            ) : null}
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
}

function SecurityLogItem({ log }) {
    const providerMap = {
        password: '邮箱密码',
        google: 'Google',
        apple: 'Apple',
    };

    const timeLabel = log.login_time
        ? new Date(log.login_time).toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        })
        : 'Unknown time';

    return (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
            <div className="flex items-center justify-between gap-4">
                <div>
                    <p className="text-sm font-black text-slate-900">{providerMap[log.login_provider] || log.login_provider}</p>
                    <p className="mt-1 text-xs font-medium text-slate-500">{timeLabel}</p>
                </div>
                <span className="rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-black uppercase tracking-[0.16em] text-emerald-600">
                    {log.status || 'success'}
                </span>
            </div>
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-medium text-slate-500">
                <p>设备：{log.device_info || 'Unknown device'}</p>
                <p>IP：{log.ip_address || 'Unknown IP'}</p>
            </div>
        </div>
    );
}

function DangerRow() {
    return (
        <div className="rounded-[1.8rem] border border-red-200 bg-red-50/70 px-5 py-4">
            <div className="flex items-start gap-4">
                <span className="w-11 h-11 rounded-2xl bg-white text-red-500 flex items-center justify-center shadow-sm shrink-0">
                    <Trash2 size={18} />
                </span>
                <div className="flex-1">
                    <div className="flex items-center justify-between gap-4">
                        <div>
                            <p className="text-[11px] font-black uppercase tracking-[0.2em] text-red-400">Danger Zone</p>
                            <h3 className="mt-1 text-sm font-black text-slate-900">注销账号</h3>
                        </div>
                        <button className="rounded-full bg-red-500 px-4 py-2 text-xs font-black uppercase tracking-[0.16em] text-white hover:bg-red-600 transition-colors">
                            Delete
                        </button>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-slate-500">
                        后面这里可以补确认弹窗、风险说明和二次身份校验。
                    </p>
                </div>
            </div>
        </div>
    );
}

function SelectRow({ label, icon, value, onChange, options }) {
    return (
        <label className="block">
            <span className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                {icon}
                {label}
            </span>
            <select
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 outline-none focus:border-blue-300"
            >
                {options.map((option) => (
                    <option key={option.value} value={option.value}>
                        {option.label}
                    </option>
                ))}
            </select>
        </label>
    );
}

function ChoicePillGroup({ label, icon, value, onChange, options }) {
    return (
        <div>
            <p className="mb-3 flex items-center gap-2 text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                {icon}
                {label}
            </p>
            <div className="flex flex-wrap gap-3">
                {options.map((option) => {
                    const active = option.value === value;
                    return (
                        <button
                            key={option.value}
                            type="button"
                            onClick={() => onChange(option.value)}
                            className={`rounded-full px-5 py-3 text-sm font-black transition-all ${
                                active
                                    ? 'bg-slate-900 text-white shadow-lg shadow-slate-200'
                                    : 'bg-white text-slate-600 border border-slate-200 hover:border-blue-200 hover:text-blue-600'
                            }`}
                        >
                            {option.label}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}

function ToggleRow({ icon, title, description, enabled, onChange }) {
    return (
        <div className="rounded-[1.6rem] border border-slate-200 bg-white px-4 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="w-10 h-10 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                    {icon}
                </span>
                <div className="flex-1">
                    <div className="flex items-start justify-between gap-4">
                        <div>
                            <h3 className="text-sm font-black text-slate-900">{title}</h3>
                            {description ? <p className="mt-1 text-sm leading-relaxed text-slate-500">{description}</p> : null}
                        </div>
                        <button
                            type="button"
                            onClick={() => onChange(!enabled)}
                            className={`relative h-8 w-14 rounded-full transition-colors shrink-0 ${enabled ? 'bg-blue-600' : 'bg-slate-200'}`}
                            aria-pressed={enabled}
                        >
                            <span
                                className={`absolute top-1 h-6 w-6 rounded-full bg-white shadow-sm transition-transform ${
                                    enabled ? 'translate-x-7' : 'translate-x-1'
                                }`}
                            />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function TimeRow({ label, value, onChange }) {
    return (
        <label className="block rounded-[1.6rem] border border-slate-200 bg-white px-4 py-4 shadow-sm">
            <span className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-[0.18em] text-slate-400">
                <Clock3 size={16} />
                {label}
            </span>
            <input
                type="time"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-bold text-slate-700 outline-none focus:border-blue-300"
            />
        </label>
    );
}

function SupportLink({ icon, title, description }) {
    return (
        <button className="w-full rounded-[1.8rem] border border-slate-200 bg-white px-5 py-4 text-left hover:border-blue-200 hover:bg-blue-50/40 transition-colors">
            <div className="flex items-start gap-4">
                <span className="w-10 h-10 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                    {icon}
                </span>
                <div className="flex-1">
                    <div className="flex items-center justify-between gap-4">
                        <h3 className="text-sm font-black text-slate-900">{title}</h3>
                        <ChevronRight size={16} className="text-slate-300 shrink-0" />
                    </div>
                    <p className="mt-1 text-sm leading-relaxed text-slate-500">{description}</p>
                </div>
            </div>
        </button>
    );
}

function BookOpenGlyph() {
    return (
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15.5A2.5 2.5 0 0 0 17.5 16H4z" />
            <path d="M4 5.5V19a2 2 0 0 0 2 2h13.5" />
        </svg>
    );
}
