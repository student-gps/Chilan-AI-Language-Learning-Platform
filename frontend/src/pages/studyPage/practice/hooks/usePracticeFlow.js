import { useCallback, useEffect, useMemo, useState } from 'react';
import { evaluateStudyAnswer } from '../../../../api/apiClient';

const getErrorMessage = (error, fallback) => {
    const message = error?.response?.data?.detail || error?.message;
    return message || fallback;
};

const toApiLessonId = (value) => {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    const digits = String(value || '').match(/\d+/)?.[0];
    return digits ? Number(digits) : 101;
};

export default function usePracticeFlow({
    currentQuestion,
    userId,
    t,
    speechMode,
    speechTranscript,
    speechMeta,
    isRecording,
    isTranscribing,
    lowConfidence,
    setSpeechError,
    cleanupMedia,
    resetSpeechState,
}) {
    const [userAnswer, setUserAnswer] = useState('');
    const [lastSubmittedAnswer, setLastSubmittedAnswer] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [knowledgeDetails, setKnowledgeDetails] = useState(null);
    const [typedFeedbackMessage, setTypedFeedbackMessage] = useState('');

    const activeAnswer = speechMode ? speechTranscript : userAnswer;
    const speechShouldRetry = speechMode && Boolean(feedback?.shouldRetry);
    const hasSpeechTranscript = speechMode && Boolean(speechTranscript.trim());
    const isPerfectFeedback = feedback?.level === 4;
    const isTypingFeedback = Boolean(feedback && !isPerfectFeedback && typedFeedbackMessage.length < (feedback.message || '').length);
    const isResubmitDisabled =
        isEvaluating ||
        isTranscribing ||
        isRecording ||
        !activeAnswer.trim() ||
        (feedback && feedback.level === 1 && activeAnswer === lastSubmittedAnswer);

    const resetQuestionUiState = useCallback(() => {
        setUserAnswer('');
        setLastSubmittedAnswer('');
        setFeedback(null);
        setKnowledgeDetails(null);
        setTypedFeedbackMessage('');
        resetSpeechState();
        cleanupMedia();
    }, [cleanupMedia, resetSpeechState]);

    const handleForfeit = useCallback(async () => {
        if (!currentQuestion || isEvaluating) return;
        setIsEvaluating(true);
        try {
            const res = await evaluateStudyAnswer({
                user_id: userId || localStorage.getItem('chilan_user_id') || 'test-user-id',
                lesson_id: toApiLessonId(currentQuestion.lesson_id),
                question_id: currentQuestion.question_id,
                question_type: currentQuestion.question_type,
                original_text: currentQuestion.original_text,
                standard_answers: Array.isArray(currentQuestion.standard_answers)
                    ? currentQuestion.standard_answers
                    : [currentQuestion.standard_answers],
                user_answer: '',
                forfeit: true,
            });
            setFeedback(res.data.data);
        } catch (e) {
            setFeedback({ level: 1, isCorrect: false, message: '', forfeited: true });
        } finally {
            setIsEvaluating(false);
        }
    }, [currentQuestion, isEvaluating, userId]);

    const handleSubmit = useCallback(async () => {
        if (!currentQuestion || isEvaluating) return;
        if (speechMode) {
            if (isRecording || isTranscribing) return;
            if (!activeAnswer.trim()) return;
            if (lowConfidence) {
                setSpeechError('语音识别结果不够稳定，请重新录音后再提交。');
                return;
            }
        } else if (!userAnswer.trim()) {
            return;
        }

        setIsEvaluating(true);
        try {
            const res = await evaluateStudyAnswer({
                user_id: userId || localStorage.getItem('chilan_user_id') || 'test-user-id',
                lesson_id: toApiLessonId(currentQuestion.lesson_id),
                question_id: currentQuestion.question_id,
                question_type: currentQuestion.question_type,
                original_text: currentQuestion.original_text,
                standard_answers: Array.isArray(currentQuestion.standard_answers) ? currentQuestion.standard_answers : [currentQuestion.standard_answers],
                user_answer: activeAnswer,
                input_mode: speechMode ? 'speech' : 'text',
                asr_text: speechMode ? speechTranscript : '',
                audio_meta: speechMode
                    ? {
                        duration_ms: speechMeta?.duration_ms ?? null,
                        confidence: speechMeta?.confidence ?? null,
                        provider: speechMeta?.provider ?? null,
                        model: speechMeta?.model ?? null
                    }
                    : {}
            });
            setFeedback(res.data.data);
            setLastSubmittedAnswer(activeAnswer);
        } catch (e) {
            setFeedback({ level: 1, isCorrect: false, message: getErrorMessage(e, t('practice_eval_failed')) });
        } finally {
            setIsEvaluating(false);
        }
    }, [
        activeAnswer,
        currentQuestion,
        isEvaluating,
        isRecording,
        isTranscribing,
        lowConfidence,
        setSpeechError,
        speechMeta,
        speechMode,
        speechTranscript,
        t,
        userAnswer,
        userId
    ]);

    useEffect(() => {
        resetQuestionUiState();
    }, [currentQuestion, resetQuestionUiState]);

    useEffect(() => {
        const fullMessage = feedback?.message || '';
        if (!fullMessage || feedback?.level === 4) {
            setTypedFeedbackMessage('');
            return;
        }

        setTypedFeedbackMessage('');
        let index = 0;
        const timer = setInterval(() => {
            index += 1;
            setTypedFeedbackMessage(fullMessage.slice(0, index));
            if (index >= fullMessage.length) {
                clearInterval(timer);
            }
        }, 18);

        return () => clearInterval(timer);
    }, [feedback]);

    const feedbackTone = useMemo(() => {
        if (!feedback) return null;
        if (feedback.level === 4) {
            return {
                inputTone: 'border-green-500 bg-green-50/60 shadow-md shadow-green-100/80',
                panelTone: 'border-green-300/80 bg-[linear-gradient(135deg,rgba(240,253,244,0.98),rgba(220,252,231,0.92))]'
            };
        }
        if (feedback.level === 2 || feedback.level === 3) {
            return {
                inputTone: 'border-amber-400 bg-amber-50/70 shadow-md shadow-amber-100/80',
                panelTone: 'border-amber-300/80 bg-[linear-gradient(135deg,rgba(255,251,235,0.98),rgba(254,243,199,0.92))]'
            };
        }
        return {
            inputTone: 'border-red-400 bg-red-50/70 shadow-md shadow-red-100/80',
            panelTone: 'border-red-300/80 bg-[linear-gradient(135deg,rgba(254,242,242,0.98),rgba(254,226,226,0.92))]'
        };
    }, [feedback]);

    return {
        currentQuestion,
        userAnswer,
        setUserAnswer,
        lastSubmittedAnswer,
        setLastSubmittedAnswer,
        isEvaluating,
        feedback,
        setFeedback,
        knowledgeDetails,
        setKnowledgeDetails,
        typedFeedbackMessage,
        activeAnswer,
        speechShouldRetry,
        hasSpeechTranscript,
        isPerfectFeedback,
        isTypingFeedback,
        isResubmitDisabled,
        feedbackTone,
        resetQuestionUiState,
        handleSubmit,
        handleForfeit,
    };
}
