import { useEffect } from 'react';

export default function usePracticeKeyboardShortcuts({
    speechMode,
    feedback,
    inputRef,
    userAnswer,
    lastSubmittedAnswer,
    handleSubmit,
    handleNext,
    speechActionsRef,
    speechTranscript,
    isRecording,
    isTranscribing,
    lowConfidence,
    speechShouldRetry,
    handleStartRecording,
    handleStopRecording,
    isListenWrite,
    onPlayAudio,
}) {
    // ↑ to replay audio for question types that have audio (CN_LISTEN_WRITE, CN_TO_EN)
    // Safe in a single-line input (cursor can't move up), and e.isComposing guards against IME candidate navigation
    useEffect(() => {
        if (!onPlayAudio) return;

        const handleReplay = (e) => {
            if (e.key !== 'ArrowUp' || e.isComposing) return;
            e.preventDefault();
            onPlayAudio();
        };

        window.addEventListener('keydown', handleReplay);
        return () => window.removeEventListener('keydown', handleReplay);
    }, [onPlayAudio]);

    useEffect(() => {
        if (speechMode) return;

        const handleEnter = (e) => {
            if (e.key !== 'Enter' || e.shiftKey) return;

            if (feedback && feedback.level >= 2) {
                e.preventDefault();
                handleNext();
                return;
            }

            if (document.activeElement === inputRef.current) {
                e.preventDefault();
                if (feedback && feedback.level === 1) {
                    if (userAnswer.trim() !== lastSubmittedAnswer) handleSubmit();
                } else if (userAnswer.trim()) {
                    handleSubmit();
                }
            }
        };

        window.addEventListener('keydown', handleEnter);
        return () => window.removeEventListener('keydown', handleEnter);
    }, [speechMode, feedback, inputRef, userAnswer, lastSubmittedAnswer, handleSubmit, handleNext]);

    useEffect(() => {
        if (!speechMode) return;
        const hasTranscript = Boolean((speechTranscript || '').trim());

        const handleSpeechKeys = (e) => {
            if (e.key === 'Tab') {
                const root = speechActionsRef.current;
                if (!root) return;

                const focusable = Array.from(root.querySelectorAll('button:not([disabled])'));
                if (!focusable.length) return;

                e.preventDefault();
                const currentIdx = focusable.indexOf(document.activeElement);
                const direction = e.shiftKey ? -1 : 1;
                const nextIdx = currentIdx === -1
                    ? 0
                    : (currentIdx + direction + focusable.length) % focusable.length;
                focusable[nextIdx]?.focus();
                return;
            }

            if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.metaKey && !e.altKey) {
                const activeEl = document.activeElement;
                const root = speechActionsRef.current;
                if (activeEl && root?.contains(activeEl) && activeEl.tagName === 'BUTTON') return;

                if (feedback) {
                    e.preventDefault();
                    if (feedback.level === 1) {
                        handleStartRecording();
                    } else {
                        handleNext();
                    }
                    return;
                }

                if (isRecording) {
                    e.preventDefault();
                    handleStopRecording();
                    return;
                }

                if (!isTranscribing) {
                    e.preventDefault();
                    if (hasTranscript && !lowConfidence && !speechShouldRetry) {
                        handleSubmit();
                    } else {
                        handleStartRecording();
                    }
                }
            }
        };

        window.addEventListener('keydown', handleSpeechKeys);
        return () => window.removeEventListener('keydown', handleSpeechKeys);
    }, [
        speechMode,
        feedback,
        speechActionsRef,
        speechTranscript,
        isRecording,
        isTranscribing,
        lowConfidence,
        speechShouldRetry,
        handleSubmit,
        handleNext,
        handleStartRecording,
        handleStopRecording,
    ]);
}
