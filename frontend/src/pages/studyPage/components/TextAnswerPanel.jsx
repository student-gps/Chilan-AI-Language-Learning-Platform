import React from 'react';

export default function TextAnswerPanel({
    value,
    inputRef,
    onChange,
    onFocus,
    onBlur,
    placeholder,
    disabled,
    isFocused,
    statusTone,
}) {
    return (
        <div className={`
            w-full h-20 px-8 flex items-center justify-center transition-all duration-300
            bg-slate-50 border-2 rounded-[2rem]
            ${statusTone || (isFocused ? 'border-blue-500 bg-white shadow-md' : 'border-slate-100')}
            opacity-100
            mb-6
        `}>
            <textarea
                ref={inputRef}
                value={value}
                onChange={onChange}
                onFocus={onFocus}
                onBlur={onBlur}
                placeholder={placeholder}
                disabled={disabled}
                className="w-full h-auto max-h-full bg-transparent text-center focus:outline-none resize-none leading-relaxed text-slate-800 placeholder:text-slate-400 text-3xl font-bold"
                rows={1}
            />
        </div>
    );
}
