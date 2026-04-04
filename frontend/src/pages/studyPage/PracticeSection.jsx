import React, { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTranslation } from 'react-i18next';
import { Loader2, Send, Sparkles } from 'lucide-react';
import apiClient, { evaluateStudyAnswer, transcribeSpeech } from '../../api/apiClient';
import AIThinkingIndicator from './components/AIThinkingIndicator';
import PracticeAnswerPanel from './components/PracticeAnswerPanel';
import PracticeFeedbackPanel from './components/PracticeFeedbackPanel';
import PracticePromptCard from './components/PracticePromptCard';

const fadeInUp = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100, damping: 20 } }
};

const staggerContainer = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.08 } }
};

const DEFAULT_SPEECH_CONFIG = {
    pass_threshold: 0.88,
    review_threshold: 0.78,
    min_asr_confidence: 0.6,
    max_attempts: 3,
    max_duration_sec: 15,
    allow_paraphrase: true
};

const RECORDER_MIME_TYPES = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/mp4'
];

const FRONTEND_NOISE_TRANSCRIPT_PATTERNS = [
    /amara\.org/i,
    /^字幕\s*(?:by|由)\s*.+$/i,
    /^字幕(?:由)?.*(?:提供|制作).*$/i,
    /^subtitles?\s*by\s*.+$/i,
    /^caption(?:s)?\s*by\s*.+$/i
];

const isSpeechQuestion = (question) =>
    question?.question_type === 'EN_TO_CN_SPEAK' || question?.metadata?.answer_mode === 'speech';

const normalizeSpeechConfig = (question) => {
    const raw = question?.metadata?.speech_eval_config || {};
    const maxAttempts = Number(raw.max_attempts);
    const maxDurationSec = Number(raw.max_duration_sec);
    const minConfidence = Number(raw.min_asr_confidence);

    return {
        ...DEFAULT_SPEECH_CONFIG,
        ...raw,
        max_attempts: Number.isFinite(maxAttempts) && maxAttempts > 0 ? Math.floor(maxAttempts) : DEFAULT_SPEECH_CONFIG.max_attempts,
        max_duration_sec:
            Number.isFinite(maxDurationSec) && maxDurationSec > 0 ? Math.floor(maxDurationSec) : DEFAULT_SPEECH_CONFIG.max_duration_sec,
        min_asr_confidence:
            Number.isFinite(minConfidence) && minConfidence >= 0 ? minConfidence : DEFAULT_SPEECH_CONFIG.min_asr_confidence
    };
};

const sanitizeFrontendTranscript = (value = '') => {
    const transcript = String(value).trim();
    if (!transcript) return '';
    return FRONTEND_NOISE_TRANSCRIPT_PATTERNS.some((pattern) => pattern.test(transcript)) ? '' : transcript;
};

const getErrorMessage = (error, fallback) => {
    const message = error?.response?.data?.detail || error?.message;
    return message || fallback;
};

export default function PracticeSection({ questions, isReview, onAllDone, userId, courseId, lessonId, initialIndex = 0 }) {
    const { t, i18n } = useTranslation();
    const [currentIndex, setCurrentIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState('');
    const [lastSubmittedAnswer, setLastSubmittedAnswer] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [isFocused, setIsFocused] = useState(false);
    const [knowledgeDetails, setKnowledgeDetails] = useState(null);
    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const [speechTranscript, setSpeechTranscript] = useState('');
    const [speechMeta, setSpeechMeta] = useState({});
    const [recordingSeconds, setRecordingSeconds] = useState(0);
    const [recordAttempts, setRecordAttempts] = useState(0);
    const [speechError, setSpeechError] = useState('');
    const [typedFeedbackMessage, setTypedFeedbackMessage] = useState('');
    const [liveWaveform, setLiveWaveform] = useState(() => Array.from({ length: 18 }, () => 0));

    const inputRef = useRef(null);
    const speechActionsRef = useRef(null);
    const speechPrimaryButtonRef = useRef(null);
    const speechSubmitButtonRef = useRef(null);
    const lastAutoPlayedKeyRef = useRef('');
    const recorderRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const chunksRef = useRef([]);
    const stopTimerRef = useRef(null);
    const elapsedTimerRef = useRef(null);
    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const analyserDataRef = useRef(null);
    const waveformFrameRef = useRef(null);

    const currentQuestion = questions[currentIndex];
    const speechMode = isSpeechQuestion(currentQuestion);
    const speechConfig = useMemo(() => normalizeSpeechConfig(currentQuestion), [currentQuestion]);
    const activeAnswer = speechMode ? speechTranscript : userAnswer;
    const lowConfidence = Number.isFinite(Number(speechMeta?.confidence)) && Number(speechMeta?.confidence) < speechConfig.min_asr_confidence;
    const speechShouldRetry = speechMode && Boolean(feedback?.shouldRetry);
    const isResubmitDisabled = isEvaluating || isTranscribing || isRecording || !activeAnswer.trim() || (feedback && feedback.level === 1 && activeAnswer === lastSubmittedAnswer);
    const hasSpeechTranscript = speechMode && Boolean(speechTranscript.trim());
    const isPerfectFeedback = feedback?.level === 4;
    const isTypingFeedback = Boolean(feedback && !isPerfectFeedback && typedFeedbackMessage.length < (feedback.message || '').length);
    const primaryButtonClass = 'bg-blue-600 text-white hover:bg-blue-700 shadow-blue-100';
    const secondaryButtonClass = 'bg-slate-900 text-white hover:bg-slate-800 shadow-slate-200';
    const textPromptLabel = currentQuestion?.question_type === 'CN_TO_EN'
        ? t('practice_prompt_cn_to_en')
        : t('practice_prompt_en_to_cn');
    const speechPreviewText = speechTranscript
        || (isRecording
            ? '正在聆听，请开始说话。'
            : isTranscribing
                ? '录音已结束，正在生成识别结果。'
                : '还没有识别结果，点击下方按钮开始录音。');
    const speechInlineHint = isTranscribing
        ? { tone: 'bg-sky-50 text-sky-700 border-sky-100', text: '已经收到录音，正在转换成文字。', emphasis: 'info' }
        : speechError
            ? {
                tone: lowConfidence ? 'bg-amber-50 text-amber-700 border-amber-100' : 'bg-rose-50 text-rose-700 border-rose-100',
                text: speechError,
                emphasis: lowConfidence ? 'warning' : 'error'
            }
            : null;

    const getFeedbackConfig = (level) => {
        if (level === 4) {
            return {
                inputTone: 'border-green-500 bg-green-50/60 shadow-md shadow-green-100/80',
                panelTone: 'border-green-300/80 bg-[linear-gradient(135deg,rgba(240,253,244,0.98),rgba(220,252,231,0.92))]'
            };
        }
        if (level === 2 || level === 3) {
            return {
                inputTone: 'border-amber-400 bg-amber-50/70 shadow-md shadow-amber-100/80',
                panelTone: 'border-amber-300/80 bg-[linear-gradient(135deg,rgba(255,251,235,0.98),rgba(254,243,199,0.92))]'
            };
        }
        return {
            inputTone: 'border-red-400 bg-red-50/70 shadow-md shadow-red-100/80',
            panelTone: 'border-red-300/80 bg-[linear-gradient(135deg,rgba(254,242,242,0.98),rgba(254,226,226,0.92))]'
        };
    };

    const config = feedback ? getFeedbackConfig(feedback.level) : null;

    const playAudio = (text) => {
        if (!text) return;
        const API_BASE = import.meta.env.VITE_API_BASE_URL;
        new Audio(`${API_BASE}/study/tts?text=${encodeURIComponent(text)}`).play();
    };

    const clearRecordingTimer = () => {
        if (stopTimerRef.current) {
            clearTimeout(stopTimerRef.current);
            stopTimerRef.current = null;
        }
    };

    const clearElapsedTimer = () => {
        if (elapsedTimerRef.current) {
            clearInterval(elapsedTimerRef.current);
            elapsedTimerRef.current = null;
        }
    };

    const cleanupMedia = () => {
        clearRecordingTimer();
        clearElapsedTimer();
        if (waveformFrameRef.current) {
            cancelAnimationFrame(waveformFrameRef.current);
            waveformFrameRef.current = null;
        }
        if (audioContextRef.current) {
            audioContextRef.current.close().catch(() => {});
            audioContextRef.current = null;
        }
        analyserRef.current = null;
        analyserDataRef.current = null;
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach((track) => track.stop());
            mediaStreamRef.current = null;
        }
        recorderRef.current = null;
        chunksRef.current = [];
        setLiveWaveform(Array.from({ length: 18 }, () => 0));
    };

    const startLiveWaveform = (stream) => {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) return;

        const audioContext = new AudioContextClass();
        const analyser = audioContext.createAnalyser();
        const source = audioContext.createMediaStreamSource(stream);
        analyser.fftSize = 256;
        analyser.smoothingTimeConstant = 0.82;
        source.connect(analyser);

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        audioContextRef.current = audioContext;
        analyserRef.current = analyser;
        analyserDataRef.current = dataArray;

        const renderWaveform = () => {
            if (!analyserRef.current || !analyserDataRef.current) return;

            analyserRef.current.getByteTimeDomainData(analyserDataRef.current);
            const sourceData = analyserDataRef.current;
            const barCount = 18;
            const halfCount = Math.ceil(barCount / 2);
            const chunkSize = Math.max(1, Math.floor(sourceData.length / halfCount));
            const halfBars = Array.from({ length: halfCount }, (_, idx) => {
                const start = idx * chunkSize;
                const end = Math.min(start + chunkSize, sourceData.length);
                let sumSquares = 0;
                for (let i = start; i < end; i += 1) {
                    const normalized = (sourceData[i] - 128) / 128;
                    sumSquares += normalized * normalized;
                }
                const rms = end > start ? Math.sqrt(sumSquares / (end - start)) : 0;
                const boosted = Math.min(1, Math.pow(rms * 8.5, 0.68));
                return boosted > 0.02 ? boosted : 0;
            });

            const mirroredBars = Array.from({ length: barCount }, (_, idx) => {
                const mirrorIndex = idx < halfCount ? idx : barCount - idx - 1;
                const base = halfBars[Math.min(mirrorIndex, halfBars.length - 1)] || 0;
                const edgeBoost = 1 - Math.abs((idx - (barCount - 1) / 2) / ((barCount - 1) / 2));
                return Math.min(1, base * (0.82 + edgeBoost * 0.32));
            });

            setLiveWaveform(mirroredBars);
            waveformFrameRef.current = requestAnimationFrame(renderWaveform);
        };

        waveformFrameRef.current = requestAnimationFrame(renderWaveform);
    };

    const focusAndMoveCursorToEnd = () => {
        if (inputRef.current) {
            const len = userAnswer.length;
            inputRef.current.focus();
            inputRef.current.setSelectionRange(len, len);
        }
    };

    const handleTranscription = async (audioBlob, mimeType) => {
        setIsTranscribing(true);
        setSpeechError('');

        try {
            const result = await transcribeSpeech({
                audioBlob,
                filename: mimeType?.includes('mp4') ? 'speech.mp4' : 'speech.webm',
                language: 'zh'
            });

            const transcript = sanitizeFrontendTranscript(result?.transcript || '');
            setSpeechTranscript(transcript);
            setUserAnswer(transcript);
            setSpeechMeta(result || {});
            setRecordAttempts((prev) => prev + 1);

            if (!transcript) {
                setSpeechError('未检测到有效语音输入，请重新录音。');
                return;
            }

            const conf = Number(result?.confidence);
            if (Number.isFinite(conf) && conf < speechConfig.min_asr_confidence) {
                setSpeechError(`语音识别置信度较低（${conf.toFixed(2)}），建议重新录音。`);
            }
        } catch (error) {
            const detail = getErrorMessage(error, '语音转写失败，请重试。');
            if (String(detail || '').toLowerCase().includes('asr transcript is empty')) {
                setSpeechTranscript('');
                setUserAnswer('');
                setSpeechError('未检测到有效语音输入，请重新录音。');
            } else {
                setSpeechError(detail);
            }
        } finally {
            setIsTranscribing(false);
        }
    };

    const handleStartRecording = async () => {
        if (!speechMode || isRecording || isTranscribing) return;
        if (!navigator.mediaDevices?.getUserMedia || typeof window.MediaRecorder === 'undefined') {
            setSpeechError('当前浏览器不支持录音，请更换现代浏览器后再试。');
            return;
        }

        setFeedback(null);
        setLastSubmittedAnswer('');
        setSpeechError('');
        setSpeechTranscript('');
        setSpeechMeta({});
        setRecordingSeconds(0);
        setLiveWaveform(Array.from({ length: 18 }, () => 0));

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;
            chunksRef.current = [];
            startLiveWaveform(stream);

            const isTypeSupported =
                typeof window.MediaRecorder.isTypeSupported === 'function'
                    ? window.MediaRecorder.isTypeSupported.bind(window.MediaRecorder)
                    : () => false;
            const mimeType = RECORDER_MIME_TYPES.find((type) => isTypeSupported(type));
            const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream);
            recorderRef.current = recorder;

            recorder.ondataavailable = (event) => {
                if (event.data?.size > 0) chunksRef.current.push(event.data);
            };

            recorder.onstop = async () => {
                setIsRecording(false);
                clearRecordingTimer();
                clearElapsedTimer();

                if (mediaStreamRef.current) {
                    mediaStreamRef.current.getTracks().forEach((track) => track.stop());
                    mediaStreamRef.current = null;
                }

                if (!chunksRef.current.length) {
                    setSpeechError('没有录到有效音频，请重新录音。');
                    return;
                }

                const blobType = recorder.mimeType || mimeType || 'audio/webm';
                const audioBlob = new Blob(chunksRef.current, { type: blobType });
                chunksRef.current = [];
                await handleTranscription(audioBlob, blobType);
            };

            recorder.start();
            setIsRecording(true);
            elapsedTimerRef.current = setInterval(() => {
                setRecordingSeconds((prev) => prev + 1);
            }, 1000);

            stopTimerRef.current = setTimeout(() => {
                if (recorder.state === 'recording') {
                    setSpeechError('已达到最长录音时长，系统已自动停止并开始转写。');
                    recorder.stop();
                }
            }, speechConfig.max_duration_sec * 1000);
        } catch (error) {
            cleanupMedia();
            setIsRecording(false);
            setRecordingSeconds(0);
            setSpeechError(getErrorMessage(error, '麦克风权限不可用，或当前设备无法录音。'));
        }
    };

    const handleStopRecording = () => {
        if (!recorderRef.current || recorderRef.current.state !== 'recording') return;
        recorderRef.current.stop();
    };

    const handleSubmit = async () => {
        if (isEvaluating) return;
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
                lesson_id: currentQuestion.lesson_id || 101,
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
    };

    const handleNext = () => {
        if (currentIndex < questions.length - 1) {
            setCurrentIndex((prev) => prev + 1);
            setUserAnswer('');
            setLastSubmittedAnswer('');
            setFeedback(null);
            setKnowledgeDetails(null);
            setSpeechTranscript('');
            setSpeechMeta({});
            setRecordingSeconds(0);
            setRecordAttempts(0);
            setSpeechError('');
            setTypedFeedbackMessage('');
            cleanupMedia();
        } else {
            onAllDone();
        }
    };

    useEffect(() => () => cleanupMedia(), []);

    useEffect(() => {
        const safeIndex = Number.isInteger(initialIndex)
            ? Math.max(0, Math.min(initialIndex, Math.max(questions.length - 1, 0)))
            : 0;
        setCurrentIndex(safeIndex);
        setUserAnswer('');
        setLastSubmittedAnswer('');
        setFeedback(null);
        setKnowledgeDetails(null);
        setIsRecording(false);
        setIsTranscribing(false);
        setSpeechTranscript('');
        setSpeechMeta({});
        setRecordingSeconds(0);
        setRecordAttempts(0);
        setSpeechError('');
        setTypedFeedbackMessage('');
        setLiveWaveform(Array.from({ length: 18 }, () => 0));
        cleanupMedia();
    }, [initialIndex, questions]);

    useEffect(() => {
        if (!currentQuestion || speechMode || currentQuestion.question_type !== 'CN_TO_EN') return;

        const questionKey = `${currentQuestion.item_id || currentQuestion.question_id || currentIndex}:${currentQuestion.original_text || ''}`;
        if (lastAutoPlayedKeyRef.current === questionKey) return;

        lastAutoPlayedKeyRef.current = questionKey;
        const timer = setTimeout(() => {
            playAudio(currentQuestion.original_text);
        }, 250);

        return () => clearTimeout(timer);
    }, [currentQuestion, currentIndex, speechMode]);

    useEffect(() => {
        if (!questions?.length || !userId || !courseId || !lessonId || isReview) return;
        const syncProgress = async () => {
            try {
                await apiClient.post('/study/practice_progress', {
                    user_id: userId,
                    course_id: Number(courseId),
                    lesson_id: lessonId,
                    current_index: currentIndex,
                });
            } catch (e) {
                console.error('同步练习进度失败:', e);
            }
        };
        syncProgress();
    }, [currentIndex, questions, userId, courseId, lessonId, isReview]);

    useEffect(() => {
        if (speechMode) return;
        if (!feedback && !isEvaluating && inputRef.current) {
            const timer = setTimeout(() => { focusAndMoveCursorToEnd(); }, 100);
            return () => clearTimeout(timer);
        }
        if (feedback && feedback.level === 1 && !isEvaluating) {
            focusAndMoveCursorToEnd();
        }
    }, [currentIndex, feedback, isEvaluating, speechMode]);

    useEffect(() => {
        if (!feedback || !currentQuestion?.item_id) {
            setKnowledgeDetails(null);
            return;
        }

        const fetchKnowledge = async () => {
            try {
                const res = await apiClient.get('/study/knowledge', {
                    params: { item_id: currentQuestion.item_id }
                });
                setKnowledgeDetails(res.data?.data || null);
            } catch (e) {
                console.error('加载动态知识点失败:', e);
                setKnowledgeDetails(null);
            }
        };

        fetchKnowledge();
    }, [feedback, currentQuestion]);

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
                } else if (userAnswer.trim() && !isEvaluating) {
                    handleSubmit();
                }
            }
        };

        window.addEventListener('keydown', handleEnter);
        return () => window.removeEventListener('keydown', handleEnter);
    }, [userAnswer, feedback, isEvaluating, lastSubmittedAnswer, speechMode]);

    useEffect(() => {
        if (!speechMode) return;
        const timer = setTimeout(() => {
            const shouldFocusSubmit = !feedback && !isRecording && !isTranscribing && hasSpeechTranscript && !lowConfidence && !speechShouldRetry;
            if (shouldFocusSubmit) {
                speechSubmitButtonRef.current?.focus();
            } else {
                speechPrimaryButtonRef.current?.focus();
            }
        }, 80);
        return () => clearTimeout(timer);
    }, [speechMode, currentIndex, feedback, isRecording, isTranscribing, hasSpeechTranscript, isEvaluating, lowConfidence, speechShouldRetry]);

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
    }, [speechMode, feedback, isRecording, isTranscribing, speechTranscript, lowConfidence, speechShouldRetry]);

    if (!currentQuestion) return null;

    const speechPrimaryLabel = isRecording ? '结束录音' : hasSpeechTranscript ? '重新录音' : '开始录音';
    const speechPrimaryTone = isRecording || !hasSpeechTranscript || lowConfidence || speechShouldRetry
        ? primaryButtonClass
        : secondaryButtonClass;

    return (
        <AnimatePresence mode="wait">
            <motion.div
                key={`practice-${i18n.language}`}
                variants={staggerContainer}
                initial="hidden"
                animate="show"
                exit={{ opacity: 0, y: -10, transition: { duration: 0.18 } }}
                className="max-w-4xl mx-auto px-6 pt-20 pb-0"
            >
                <motion.div variants={fadeInUp} initial="hidden" animate="show" className="flex items-center justify-center gap-5 mb-8">
                    <div className="flex items-center gap-3">
                        <Sparkles className="text-blue-500" size={28} />
                        <h1 className="text-5xl font-black text-slate-900 tracking-tight">
                            {isReview ? t('practice_title_review') : t('practice_title_lesson')}
                        </h1>
                    </div>
                    <div className="px-5 py-1.5 bg-slate-200/50 rounded-full text-xl font-black text-slate-500 tracking-tighter">
                        {currentIndex + 1} / {questions.length}
                    </div>
                </motion.div>

                <PracticePromptCard
                    fadeInUp={fadeInUp}
                    speechMode={speechMode}
                    promptLabel={textPromptLabel}
                    originalText={currentQuestion.original_text}
                />

                <motion.div variants={fadeInUp} initial="hidden" animate="show" className="bg-white p-8 md:p-10 rounded-[2.5rem] shadow-xl shadow-slate-200/40 border border-slate-100">
                    <PracticeAnswerPanel
                        speechMode={speechMode}
                        value={userAnswer}
                        inputRef={inputRef}
                        onChange={(e) => setUserAnswer(e.target.value)}
                        onFocus={() => setIsFocused(true)}
                        onBlur={() => setIsFocused(false)}
                        placeholder={isFocused ? '' : t('practice_input_placeholder')}
                        disabled={isEvaluating || (feedback && feedback.level >= 2)}
                        isFocused={isFocused}
                        statusTone={feedback ? config.inputTone : null}
                        isRecording={isRecording}
                        isTranscribing={isTranscribing}
                        recordAttempts={recordAttempts}
                        maxDurationSec={speechConfig.max_duration_sec}
                        recordingSeconds={recordingSeconds}
                        liveWaveform={liveWaveform}
                        speechPreviewText={speechPreviewText}
                        speechInlineHint={speechInlineHint}
                        onPrimaryAction={isRecording ? handleStopRecording : handleStartRecording}
                        primaryLabel={speechPrimaryLabel}
                        primaryDisabled={isTranscribing}
                        showSubmit={hasSpeechTranscript && !isRecording && !isTranscribing}
                        onSubmit={handleSubmit}
                        submitDisabled={!activeAnswer.trim() || isEvaluating || lowConfidence || speechShouldRetry}
                        isEvaluating={isEvaluating}
                        primaryButtonRef={speechMode ? speechPrimaryButtonRef : undefined}
                        submitButtonRef={speechMode ? speechSubmitButtonRef : undefined}
                        actionsRef={speechMode ? speechActionsRef : undefined}
                        primaryButtonClass={speechPrimaryTone}
                        secondaryButtonClass={secondaryButtonClass}
                    />

                    <AnimatePresence mode="wait">
                        {!feedback && !isEvaluating ? (
                            !speechMode && (
                                <motion.button
                                    key="text-submit"
                                    whileTap={{ scale: 0.98 }}
                                    onClick={handleSubmit}
                                    disabled={!userAnswer.trim() || isEvaluating}
                                    className={`w-full py-5 rounded-[1.2rem] font-black text-xl disabled:bg-slate-200 transition-all flex items-center justify-center gap-3 shadow-lg ${primaryButtonClass}`}
                                >
                                    {isEvaluating ? <Loader2 className="animate-spin" /> : <Send size={22} />}
                                    {isEvaluating ? t('practice_evaluating') : t('practice_submit')}
                                </motion.button>
                            )
                        ) : feedback ? (
                            <PracticeFeedbackPanel
                                feedback={feedback}
                                isPerfectFeedback={isPerfectFeedback}
                                isTypingFeedback={isTypingFeedback}
                                typedFeedbackMessage={typedFeedbackMessage}
                                speechMode={speechMode}
                                onRetry={speechMode ? handleStartRecording : handleSubmit}
                                onSkip={handleNext}
                                onNext={handleNext}
                                retryDisabled={speechMode ? (isRecording || isTranscribing) : isResubmitDisabled}
                                currentIndex={currentIndex}
                                totalQuestions={questions.length}
                                isBusy={isEvaluating || isTranscribing}
                                primaryButtonRef={speechMode ? speechPrimaryButtonRef : undefined}
                                actionsRef={speechMode ? speechActionsRef : undefined}
                                primaryButtonClass={primaryButtonClass}
                                secondaryButtonClass={secondaryButtonClass}
                                currentQuestion={currentQuestion}
                                knowledgeDetails={knowledgeDetails}
                            />
                        ) : (
                            <motion.div
                                key="thinking-area"
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -3, scale: 0.985, filter: 'blur(2px)' }}
                                transition={{ duration: 0.28, ease: 'easeOut' }}
                                className="space-y-5"
                            >
                                <AIThinkingIndicator label="AI 导师正在分析你的回答..." />
                            </motion.div>
                        )}
                    </AnimatePresence>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
