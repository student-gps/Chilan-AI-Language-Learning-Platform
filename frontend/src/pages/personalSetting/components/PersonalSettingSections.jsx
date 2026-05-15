import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import {
    Check,
    ChevronRight,
    Clock3,
    Edit3,
    Eye,
    EyeOff,
    Loader2,
    LockKeyhole,
    Trash2,
    User,
} from 'lucide-react';

const expandMotion = {
    initial: { opacity: 0, y: -8, height: 0 },
    animate: { opacity: 1, y: 0, height: 'auto', transition: { duration: 0.24, ease: 'easeOut' } },
    exit: { opacity: 0, y: -6, height: 0, transition: { duration: 0.18, ease: 'easeInOut' } },
};

export function SettingsCard({ eyebrow, title, description, icon, children }) {
    return (
        <div className="rounded-[2.5rem] border border-white/80 bg-white/90 p-7 md:p-8 shadow-2xl shadow-slate-200/50">
            <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center shadow-sm shadow-blue-100">
                    {icon}
                </div>
                <div>
                    {eyebrow ? <p className="text-[11px] font-black tracking-[0.18em] text-slate-400">{eyebrow}</p> : null}
                    <h2 className="mt-2 text-2xl font-black tracking-tight text-slate-900">{title}</h2>
                    {description ? <p className="mt-2 text-sm leading-relaxed text-slate-500 max-w-2xl">{description}</p> : null}
                </div>
            </div>
            {children}
        </div>
    );
}

export function ProfilePanel({ username, email, isLoading }) {
    const { t } = useTranslation();
    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-5 shadow-sm">
            <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-4 min-w-0">
                    <div className="h-[72px] w-[72px] rounded-[1.75rem] bg-gradient-to-br from-blue-600 via-indigo-500 to-cyan-400 text-white flex items-center justify-center shadow-xl shadow-blue-200 shrink-0">
                        <User size={28} />
                    </div>
                    <div className="min-w-0">
                        <h3 className="text-xl font-black tracking-tight text-slate-900">
                            {isLoading ? t('settings_loading') : (username || 'Chilan Learner')}
                        </h3>
                        <p className="mt-1 text-sm font-medium text-slate-500 truncate">
                            {isLoading ? t('settings_loading_profile') : (email || t('settings_no_email'))}
                        </p>
                    </div>
                </div>
                <button className="shrink-0 rounded-full border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-black text-slate-700 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600 transition-colors">
                    {t('settings_change_avatar')}
                </button>
            </div>
        </div>
    );
}

export function InputRow({ label, value, icon }) {
    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-600">
                    {icon}
                </span>
                <div className="relative min-w-0 flex-1">
                    <p className="text-sm font-black text-slate-900">{label}</p>
                    <input
                        value={value}
                        readOnly
                        className="mt-2 w-full bg-transparent text-sm font-bold text-slate-600 outline-none"
                    />
                    {!value ? (
                        <div className="absolute inset-y-0 right-0 flex items-center text-slate-300">
                            <Loader2 size={16} className="animate-spin" />
                        </div>
                    ) : null}
                </div>
            </div>
        </div>
    );
}

export function EditableInputRow({
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
    const { t } = useTranslation();
    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-600">
                    {icon}
                </span>
                <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                            <p className="text-sm font-black text-slate-900">{label}</p>
                            <input
                                value={isEditing ? draft : value}
                                onChange={(e) => onChange(e.target.value)}
                                readOnly={!isEditing}
                                className="mt-2 w-full bg-transparent text-sm font-bold text-slate-600 outline-none"
                            />
                        </div>
                        {isEditing ? (
                            <div className="flex items-center gap-2">
                                <button
                                    type="button"
                                    onClick={onCancel}
                                    className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-black text-slate-500 hover:border-slate-300 hover:text-slate-700 transition-colors"
                                >
                                    {t('common_cancel')}
                                </button>
                                <button
                                    type="button"
                                    onClick={onSave}
                                    disabled={isSaving}
                                    className="rounded-full bg-slate-900 px-3 py-1.5 text-xs font-black text-white hover:bg-blue-600 transition-colors disabled:bg-slate-300"
                                >
                                    {isSaving ? <Loader2 size={14} className="animate-spin" /> : <span className="inline-flex items-center gap-1"><Check size={14} />{t('common_save')}</span>}
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
                                    {t('common_edit')}
                                </span>
                            </button>
                        )}
                    </div>
                    {isEditing ? (
                        <p className="mt-3 text-xs font-medium text-slate-400">
                            {t('settings_nickname_hint')}
                        </p>
                    ) : null}
                    {error ? <p className="mt-2 text-xs font-bold text-red-500">{error}</p> : null}
                </div>
            </div>
        </div>
    );
}

function PasswordInput({ label, value, onChange, visible, onToggleVisible }) {
    return (
        <label className="block">
            <span className="mb-2 block text-xs font-black tracking-[0.12em] text-slate-400">
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

export function PasswordSection({
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
    const { t } = useTranslation();
    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="w-11 h-11 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                    {icon}
                </span>
                <div className="flex-1">
                    <div className="flex items-center justify-between gap-4">
                        <div>
                            <h3 className="text-sm font-black text-slate-900">{t('settings_password_title')}</h3>
                            <p className="mt-1 text-sm leading-relaxed text-slate-500">
                                {t('settings_password_desc')}
                            </p>
                        </div>
                        {!isEditing ? (
                            <button
                                type="button"
                                onClick={onStartEdit}
                                className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-black text-slate-600 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                            >
                                {t('common_edit')}
                            </button>
                        ) : null}
                    </div>

                    <AnimatePresence initial={false}>
                        {isEditing ? (
                            <motion.div {...expandMotion} className="overflow-hidden">
                                <div className="mt-4 space-y-4">
                                    <PasswordInput
                                        label={t('settings_current_password')}
                                        value={currentPassword}
                                        onChange={onCurrentPasswordChange}
                                        visible={showCurrentPassword}
                                        onToggleVisible={onToggleCurrentPassword}
                                    />
                                    <PasswordInput
                                        label={t('settings_new_password')}
                                        value={newPassword}
                                        onChange={onNewPasswordChange}
                                        visible={showNewPassword}
                                        onToggleVisible={onToggleNewPassword}
                                    />
                                    <PasswordInput
                                        label={t('settings_confirm_new_password')}
                                        value={confirmPassword}
                                        onChange={onConfirmPasswordChange}
                                        visible={showConfirmPassword}
                                        onToggleVisible={onToggleConfirmPassword}
                                    />

                                    <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
                                        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                                            <Requirement met={passwordChecks.length} text={t('settings_pw_req_length')} />
                                            <Requirement met={passwordChecks.letter} text={t('settings_pw_req_letter')} />
                                            <Requirement met={passwordChecks.number} text={t('settings_pw_req_number')} />
                                            <Requirement met={passwordChecks.special} text={t('settings_pw_req_special')} />
                                            <Requirement met={passwordChecks.noSpace} text={t('settings_pw_req_no_space')} />
                                            <Requirement met={passwordChecks.match} text={t('settings_pw_req_match')} />
                                            <Requirement met={passwordChecks.different} text={t('settings_pw_req_different')} />
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
                                            {t('common_cancel')}
                                        </button>
                                        <button
                                            type="button"
                                            onClick={onSave}
                                            disabled={isSaving}
                                            className="rounded-full bg-slate-900 px-4 py-2 text-xs font-black text-white hover:bg-blue-600 transition-colors disabled:bg-slate-300"
                                        >
                                            {isSaving ? <Loader2 size={14} className="animate-spin" /> : t('settings_save_new_password')}
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        ) : null}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}

export function ProviderPasswordNotice({ provider }) {
    const { t } = useTranslation();
    const providerName = provider === 'google' ? 'Google' : 'Apple';

    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="w-11 h-11 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                    <LockKeyhole size={18} />
                </span>
                <div className="flex-1">
                    <h3 className="text-sm font-black text-slate-900">{t('settings_password_title')}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-500">
                        {t('settings_provider_password_desc', { provider: providerName })}
                    </p>
                </div>
            </div>
        </div>
    );
}

function SecurityLogItem({ log }) {
    const { t, i18n } = useTranslation();
    const providerMap = {
        password: t('settings_provider_password'),
        google: 'Google',
        apple: 'Apple',
    };

    const timeLabel = log.login_time
        ? new Date(log.login_time).toLocaleString(i18n.language || undefined, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
        })
        : t('settings_unknown_time');

    const statusLabel = log.status === 'success' ? t('settings_status_success') : log.status || t('settings_status_success');

    return (
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4">
            <div className="flex items-center justify-between gap-4">
                <div>
                    <p className="text-sm font-black text-slate-900">{providerMap[log.login_provider] || log.login_provider}</p>
                    <p className="mt-1 text-xs font-medium text-slate-500">{timeLabel}</p>
                </div>
                <span className="rounded-full bg-emerald-50 px-3 py-1 text-[11px] font-black tracking-[0.16em] text-emerald-600">
                    {statusLabel}
                </span>
            </div>
            <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-2 text-xs font-medium text-slate-500">
                <p>{t('settings_device_label')}: {log.device_info || t('settings_unknown_device')}</p>
                <p>IP: {log.ip_address || t('settings_unknown_ip')}</p>
            </div>
        </div>
    );
}

export function SecurityLogSection({ icon, isOpen, isLoading, logs, error, onToggle, onRefresh }) {
    const { t } = useTranslation();
    return (
        <div className="rounded-[1.8rem] border border-slate-200 bg-white px-5 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="w-11 h-11 rounded-2xl bg-slate-100 text-slate-600 flex items-center justify-center shrink-0">
                    {icon}
                </span>
                <div className="flex-1">
                    <div className="flex items-center justify-between gap-4">
                        <h3 className="text-sm font-black text-slate-900">{t('settings_security_log_title')}</h3>
                        <button
                            type="button"
                            onClick={onToggle}
                            className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-black text-slate-600 hover:border-blue-200 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                        >
                            <span className="inline-flex items-center gap-1">
                                {isOpen ? t('knowledge_hide') : t('settings_view')}
                                <ChevronRight size={14} className={`transition-transform ${isOpen ? 'rotate-90' : ''}`} />
                            </span>
                        </button>
                    </div>
                    <AnimatePresence initial={false}>
                        {isOpen ? (
                            <motion.div {...expandMotion} className="overflow-hidden">
                                <div className="mt-4 space-y-3">
                                    <div className="flex justify-end">
                                        <button
                                            type="button"
                                            onClick={onRefresh}
                                            className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-black text-slate-500 hover:border-slate-300 hover:text-slate-700 transition-colors"
                                        >
                                            {t('settings_refresh_logs')}
                                        </button>
                                    </div>
                                    {isLoading ? (
                                        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm font-bold text-slate-400 flex items-center justify-center gap-2">
                                            <Loader2 size={16} className="animate-spin" />
                                            {t('settings_loading')}
                                        </div>
                                    ) : null}
                                    {error ? (
                                        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-xs font-bold text-red-500">
                                            {error}
                                        </div>
                                    ) : null}
                                    {!isLoading && !error && logs.length === 0 ? (
                                        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-6 text-sm font-bold text-slate-400">
                                            {t('settings_no_login_logs')}
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
                            </motion.div>
                        ) : null}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}

export function DeleteAccountSection({
    provider,
    isOpen,
    isDeleting,
    confirmText,
    password,
    error,
    success,
    showPassword,
    onToggle,
    onConfirmTextChange,
    onPasswordChange,
    onTogglePassword,
    onDelete,
}) {
    const { t } = useTranslation();
    return (
        <div className="rounded-[1.8rem] border border-red-200 bg-red-50/70 px-5 py-4 shadow-sm">
            <div className="flex items-start gap-4">
                <span className="w-11 h-11 rounded-2xl bg-white text-red-500 flex items-center justify-center shadow-sm shrink-0">
                    <Trash2 size={18} />
                </span>
                <div className="flex-1">
                    <div className="flex items-center justify-between gap-4">
                        <h3 className="text-sm font-black text-slate-900">{t('settings_delete_account_title')}</h3>
                        <button
                            type="button"
                            onClick={onToggle}
                            className="rounded-full bg-red-500 px-4 py-2 text-xs font-black tracking-[0.08em] text-white hover:bg-red-600 transition-colors"
                        >
                            {isOpen ? t('knowledge_hide') : t('settings_delete')}
                        </button>
                    </div>
                    <AnimatePresence initial={false}>
                        {isOpen ? (
                            <motion.div {...expandMotion} className="overflow-hidden">
                                <div className="mt-4 space-y-4">
                                    <p className="text-sm leading-relaxed text-slate-500">
                                        {t('settings_delete_confirm_desc_prefix')} <span className="font-black text-slate-700">DELETE</span> {t('settings_delete_confirm_desc_suffix')}
                                    </p>
                                    <label className="block">
                                        <span className="mb-2 block text-xs font-black tracking-[0.12em] text-red-400">
                                            {t('settings_confirm_text')}
                                        </span>
                                        <input
                                            value={confirmText}
                                            onChange={(e) => onConfirmTextChange(e.target.value)}
                                            className="w-full rounded-2xl border border-red-200 bg-white px-4 py-3 text-sm font-bold text-slate-700 outline-none focus:border-red-300"
                                            placeholder="DELETE"
                                        />
                                    </label>
                                    {provider === 'password' ? (
                                        <label className="block">
                                            <span className="mb-2 block text-xs font-black tracking-[0.12em] text-red-400">
                                                {t('settings_current_password')}
                                            </span>
                                            <div className="relative">
                                                <input
                                                    type={showPassword ? 'text' : 'password'}
                                                    value={password}
                                                    onChange={(e) => onPasswordChange(e.target.value)}
                                                    className="w-full rounded-2xl border border-red-200 bg-white px-4 py-3 pr-12 text-sm font-bold text-slate-700 outline-none focus:border-red-300"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={onTogglePassword}
                                                    className="absolute inset-y-0 right-4 flex items-center text-slate-400 hover:text-red-500"
                                                >
                                                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                                                </button>
                                            </div>
                                        </label>
                                    ) : null}
                                    {success ? <p className="text-xs font-bold text-emerald-600">{success}</p> : null}
                                    {error ? <p className="text-xs font-bold text-red-500">{error}</p> : null}
                                    <div className="flex justify-end">
                                        <button
                                            type="button"
                                            onClick={onDelete}
                                            disabled={isDeleting}
                                            className="rounded-full bg-red-500 px-4 py-2 text-xs font-black tracking-[0.08em] text-white hover:bg-red-600 transition-colors disabled:bg-red-300"
                                        >
                                            {isDeleting ? <Loader2 size={14} className="animate-spin" /> : t('settings_confirm_delete')}
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        ) : null}
                    </AnimatePresence>
                </div>
            </div>
        </div>
    );
}

export function SelectRow({ label, icon, value, onChange, options }) {
    return (
        <label className="block">
            <span className="mb-2 flex items-center gap-2 text-xs font-black tracking-[0.12em] text-slate-400">
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

export function ChoicePillGroup({ label, icon, value, onChange, options }) {
    return (
        <div>
            <p className="mb-3 flex items-center gap-2 text-xs font-black tracking-[0.12em] text-slate-400">
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

export function ToggleRow({ icon, title, description, enabled, onChange }) {
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

export function TimeRow({ label, value, onChange }) {
    return (
        <label className="block rounded-[1.6rem] border border-slate-200 bg-white px-4 py-4 shadow-sm">
            <span className="mb-2 flex items-center gap-2 text-xs font-black tracking-[0.12em] text-slate-400">
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

export function SupportLink({ icon, title, description }) {
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

export function BookOpenGlyph() {
    return (
        <svg viewBox="0 0 24 24" className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v15.5A2.5 2.5 0 0 0 17.5 16H4z" />
            <path d="M4 5.5V19a2 2 0 0 0 2 2h13.5" />
        </svg>
    );
}
