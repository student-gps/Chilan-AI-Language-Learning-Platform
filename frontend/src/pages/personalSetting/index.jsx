import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
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
import { getAuthState } from '../../utils/authStorage';
import { COURSE_LANGUAGE_OPTIONS, getUiLanguageOption, UI_LANGUAGE_OPTIONS } from '../../utils/languageOptions';
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
import useProfileSection from './hooks/useProfileSection';
import useSecuritySection from './hooks/useSecuritySection';
import useDeleteSection from './hooks/useDeleteSection';

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
    const { t, i18n } = useTranslation();
    const { userId, userEmail } = getAuthState();

    // \u2500\u2500 Section hooks\uff1a\u5404\u529f\u80fd\u6a21\u5757\u72ec\u7acb\u7ba1\u7406\u81ea\u5df1\u7684\u72b6\u6001 \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    const {
        profile,
        isProfileLoading,
        isEditingNickname, nicknameDraft, setNicknameDraft, nicknameError, isSavingNickname,
        handleStartEditingNickname, handleCancelEditingNickname, handleSaveNickname,
    } = useProfileSection(userId, userEmail);

    const {
        isSecurityOpen, securityLogs, isSecurityLoading, securityError,
        handleToggleSecurity, loadSecurityLogs,
    } = useSecuritySection(userId);

    const {
        isDeleteOpen, deleteConfirmText, setDeleteConfirmText,
        deletePassword, setDeletePassword, showDeletePassword, setShowDeletePassword,
        deleteError, deleteSuccess, isDeletingAccount,
        handleToggleDelete, handleDeleteAccount,
    } = useDeleteSection(userId, profile.loginProvider);

    const {
        confirmPassword, currentPassword, handleCancelEditingPassword, handleSavePassword,
        handleStartEditingPassword, isEditingPassword, isSavingPassword, newPassword,
        passwordChecks, passwordError, passwordSuccess, setConfirmPassword, setCurrentPassword,
        setNewPassword, showConfirmPassword, showCurrentPassword, showNewPassword,
        toggleConfirmPassword, toggleCurrentPassword, toggleNewPassword,
    } = usePasswordSettings(userId);

    // \u2500\u2500 \u504f\u597d / \u901a\u77e5\uff1a\u672c\u5730\u72b6\u6001\uff08\u6682\u65e0\u540e\u7aef\u63a5\u53e3\uff0c\u540e\u7eed\u6269\u5c55\uff09\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
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
        setInterfaceLang(getUiLanguageOption(i18n.language).code);
    }, [i18n.language]);

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
                            title={t('settings_account_security')}
                            description=""
                            icon={<Shield size={18} />}
                        >
                            <ProfilePanel username={profile.username} email={profile.email} isLoading={isProfileLoading} />
                            <div className="mt-5 space-y-4">
                                <EditableInputRow
                                    label={t('settings_nickname')}
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
                                <InputRow label={t('settings_email')} value={profile.email} icon={<Mail size={16} />} />
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
                            eyebrow={t('settings_language_eyebrow')}
                            title={t('settings_language_title')}
                            description={t('settings_language_desc')}
                            icon={<Languages size={18} />}
                        >
                            <div className="space-y-4">
                                <SelectRow
                                    label={t('settings_interface_language')}
                                    icon={<Globe size={16} />}
                                    value={interfaceLang}
                                    onChange={(value) => {
                                        setInterfaceLang(value);
                                        i18n.changeLanguage(value);
                                    }}
                                    options={UI_LANGUAGE_OPTIONS.map((item) => ({
                                        value: item.code,
                                        label: `${item.flag} ${item.nativeName}`,
                                    }))}
                                />
                                <SelectRow
                                    label={t('settings_native_language')}
                                    icon={<Languages size={16} />}
                                    value={nativeLang}
                                    onChange={setNativeLang}
                                    options={COURSE_LANGUAGE_OPTIONS}
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>

                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow={t('settings_feedback_eyebrow')}
                            title={t('settings_feedback_title')}
                            description={t('settings_feedback_desc')}
                            icon={<NotebookPen size={18} />}
                        >
                            <div className="space-y-5">
                                <ChoicePillGroup
                                    label={t('settings_strictness_label')}
                                    icon={<SlidersHorizontal size={16} />}
                                    value={strictness}
                                    onChange={setStrictness}
                                    options={[
                                        { value: 'strict', label: t('settings_strictness_strict') },
                                        { value: 'balanced', label: t('settings_strictness_balanced') },
                                        { value: 'friendly', label: t('settings_strictness_friendly') },
                                    ]}
                                />

                                <div className="rounded-[2rem] border border-slate-200 bg-slate-50/80 p-5">
                                    <p className="mb-4 text-xs font-black tracking-[0.12em] text-slate-400">{t('settings_default_hints')}</p>
                                    <div className="space-y-3">
                                        <ToggleRow
                                            icon={<Languages size={16} />}
                                            title={t('settings_show_pinyin')}
                                            enabled={showPinyin}
                                            onChange={setShowPinyin}
                                        />
                                        <ToggleRow
                                            icon={<BookOpenGlyph />}
                                            title={t('settings_show_meaning')}
                                            enabled={showMeaning}
                                            onChange={setShowMeaning}
                                        />
                                        <ToggleRow
                                            icon={<CircleHelp size={16} />}
                                            title={t('settings_show_grammar')}
                                            enabled={showGrammar}
                                            onChange={setShowGrammar}
                                        />
                                    </div>
                                </div>

                                <ToggleRow
                                    icon={<Sparkles size={16} />}
                                    title={t('settings_ai_explanation')}
                                    description={t('settings_ai_explanation_desc')}
                                    enabled={showAiExplanation}
                                    onChange={setShowAiExplanation}
                                />
                                <ToggleRow
                                    icon={<Mic2 size={16} />}
                                    title={t('settings_auto_play_audio')}
                                    description={t('settings_auto_play_audio_desc')}
                                    enabled={autoPlayAudio}
                                    onChange={setAutoPlayAudio}
                                />
                                <SelectRow
                                    label={t('settings_playback_speed')}
                                    icon={<Clock3 size={16} />}
                                    value={playbackSpeed}
                                    onChange={setPlaybackSpeed}
                                    options={[
                                        { value: '0.8x', label: t('settings_speed_slow') },
                                        { value: '1.0x', label: t('settings_speed_normal') },
                                        { value: '1.2x', label: t('settings_speed_fast') },
                                    ]}
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>

                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow={t('settings_notifications_eyebrow')}
                            title={t('settings_notifications_title')}
                            description={t('settings_notifications_desc')}
                            icon={<Bell size={18} />}
                        >
                            <div className="space-y-4">
                                <ToggleRow
                                    icon={<Mail size={16} />}
                                    title={t('settings_email_notifications')}
                                    description={t('settings_email_notifications_desc')}
                                    enabled={mailNotifications}
                                    onChange={setMailNotifications}
                                />
                                <ToggleRow
                                    icon={<Bell size={16} />}
                                    title={t('settings_daily_reminder')}
                                    description={t('settings_daily_reminder_desc')}
                                    enabled={dailyReminder}
                                    onChange={setDailyReminder}
                                />
                                <TimeRow
                                    label={t('settings_review_time')}
                                    value={reviewReminderTime}
                                    onChange={setReviewReminderTime}
                                />
                                <ToggleRow
                                    icon={<NotebookPen size={16} />}
                                    title={t('settings_course_updates')}
                                    description={t('settings_course_updates_desc')}
                                    enabled={courseUpdates}
                                    onChange={setCourseUpdates}
                                />
                                <ToggleRow
                                    icon={<Siren size={16} />}
                                    title={t('settings_security_alerts')}
                                    description={t('settings_security_alerts_desc')}
                                    enabled={securityAlerts}
                                    onChange={setSecurityAlerts}
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>

                    <motion.div variants={blockMotion}>
                        <SettingsCard
                            eyebrow={t('settings_support_eyebrow')}
                            title={t('settings_support_title')}
                            description={t('settings_support_desc')}
                            icon={<MessageSquareMore size={18} />}
                        >
                            <div className="space-y-3">
                                <SupportLink
                                    icon={<CircleHelp size={17} />}
                                    title={t('settings_faq')}
                                    description={t('settings_faq_desc')}
                                />
                                <SupportLink
                                    icon={<MessageSquareMore size={17} />}
                                    title={t('settings_feedback_link')}
                                    description={t('settings_feedback_link_desc')}
                                />
                                <SupportLink
                                    icon={<Mail size={17} />}
                                    title={t('settings_contact')}
                                    description={t('settings_contact_desc')}
                                />
                                <SupportLink
                                    icon={<MonitorCog size={17} />}
                                    title={t('settings_version')}
                                    description={t('settings_version_desc')}
                                />
                            </div>
                        </SettingsCard>
                    </motion.div>
                </div>
            </motion.div>
        </div>
    );
}

