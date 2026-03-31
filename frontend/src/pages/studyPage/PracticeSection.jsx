import React, { useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { evaluateStudyAnswer, transcribeSpeech } from '../../lib/api';
import {
    Loader2,
    Send,
    CheckCircle2,
    XCircle,
    Sparkles,
    RefreshCcw,
    ArrowRight,
    AlertCircle,
    BookOpen,
    Mic,
    Square
} from 'lucide-react';

const fadeInUp = {
    hidden: { opacity: 0, y: 15 },
    show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 100, damping: 20 } }
};

const DEFAULT_SPEECH_CONFIG = {
    pass_threshold: 0.88,
    review_threshold: 0.78,
    min_asr_confidence: 0.6,
    max_attempts: 3,
    max_duration_sec: 15
};

const RECORDER_MIME_TYPES = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/mp4'
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

const getQuestionPrompt = (questionType) => {
    if (questionType === 'CN_TO_EN') return 'Translate into English';
    if (questionType === 'EN_TO_CN_SPEAK') return 'Speak in Chinese';
    return 'Translate into Chinese';
};

const getErrorMessage = (error, fallback) => {
    const message = error?.response?.data?.detail || error?.message;
    return message || fallback;
};

const WordContextCard = ({ metadata }) => {
    const examples = metadata?.context_examples || [];
    const history = metadata?.history || [];

    if (examples.length === 0 && history.length === 0) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-4 mb-6 bg-slate-50/80 rounded-[2rem] border border-slate-200/50 p-7 text-left"
        >
            <div className="flex items-center gap-3 mb-5">
                <div className="p-2 bg-blue-50 rounded-xl">
                    <BookOpen className="text-blue-500" size={20} />
                </div>
                <h4 className="text-xl font-black text-slate-800 tracking-tight">Knowledge Point</h4>
                <div className="h-px flex-1 bg-slate-200/60" />
            </div>

            <div className="space-y-4">
                {examples.map((ex, idx) => (
                    <div key={idx} className="bg-white/80 p-5 rounded-2xl border border-white shadow-sm">
                        <p className="text-2xl font-black text-slate-800 mb-1 leading-tight">{ex.cn}</p>
                        <p className="text-sm font-bold text-slate-400 mb-3 tracking-wide uppercase">{ex.py}</p>
                        <div className="py-2 px-4 bg-blue-50/50 rounded-lg inline-block">
                            <p className="text-base font-bold text-blue-600 italic leading-snug">{ex.en}</p>
                        </div>
                    </div>
                ))}
            </div>

            {history.length > 0 && (
                <div className="mt-6 pt-5 border-t border-slate-200/60">
                    <p className="text-xs font-black text-slate-400 uppercase tracking-[0.2em] mb-3">Other Meanings</p>
                    <div className="flex flex-wrap gap-2">
                        {history.map((item, i) => (
                            <span key={i} className="px-3 py-1.5 bg-slate-200/50 rounded-xl text-sm font-black text-slate-600">
                                {item.definition}
                            </span>
                        ))}
                    </div>
                </div>
            )}
        </motion.div>
    );
};

export default function PracticeSection({ questions, isReview, onAllDone }) {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [userAnswer, setUserAnswer] = useState('');
    const [lastSubmittedAnswer, setLastSubmittedAnswer] = useState('');
    const [isEvaluating, setIsEvaluating] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [isFocused, setIsFocused] = useState(false);

    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const [speechTranscript, setSpeechTranscript] = useState('');
    const [speechMeta, setSpeechMeta] = useState({});
    const [recordAttempts, setRecordAttempts] = useState(0);
    const [speechError, setSpeechError] = useState('');

    const inputRef = useRef(null);
    const recorderRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const chunksRef = useRef([]);
    const stopTimerRef = useRef(null);

    const questionList = Array.isArray(questions) ? questions : [];
    const currentQuestion = questionList[currentIndex];
    const speechMode = isSpeechQuestion(currentQuestion);
    const speechConfig = useMemo(() => normalizeSpeechConfig(currentQuestion), [currentQuestion]);
    const activeAnswer = speechMode ? speechTranscript : userAnswer;

    const confidenceValue = Number(speechMeta?.confidence);
    const hasConfidence = Number.isFinite(confidenceValue);
    const lowConfidence = hasConfidence && confidenceValue < speechConfig.min_asr_confidence;
    const canRecordMore = recordAttempts < speechConfig.max_attempts;

    const clearRecordingTimer = () => {
        if (stopTimerRef.current) {
            clearTimeout(stopTimerRef.current);
            stopTimerRef.current = null;
        }
    };

    const cleanupMedia = () => {
        clearRecordingTimer();
        if (mediaStreamRef.current) {
            mediaStreamRef.current.getTracks().forEach((track) => track.stop());
            mediaStreamRef.current = null;
        }
        recorderRef.current = null;
        chunksRef.current = [];
    };

    const getFeedbackConfig = (level) => {
        if (level === 4) {
            return {
                card: 'bg-green-50/50 border-green-100',
                titleColor: 'text-green-800',
                msgColor: 'text-green-700/90',
                icon: <CheckCircle2 className="text-green-500 shrink-0" size={32} />,
                title: 'Excellent'
            };
        }
        if (level === 2 || level === 3) {
            return {
                card: 'bg-amber-50/50 border-amber-100',
                titleColor: 'text-amber-800',
                msgColor: 'text-amber-700',
                icon: <AlertCircle className="text-amber-500 shrink-0" size={32} />,
                title: 'Good Progress'
            };
        }
        return {
            card: 'bg-red-50/50 border-red-100',
            titleColor: 'text-red-800',
            msgColor: 'text-red-700',
            icon: <XCircle className="text-red-500 shrink-0" size={32} />,
            title: 'Keep Practicing'
        };
    };

    const focusAndMoveCursorToEnd = () => {
        if (!inputRef.current) return;
        const len = userAnswer.length;
        inputRef.current.focus();
        inputRef.current.setSelectionRange(len, len);
    };

    useEffect(() => {
        return () => cleanupMedia();
    }, []);

    useEffect(() => {
        cleanupMedia();
        setUserAnswer('');
        setLastSubmittedAnswer('');
        setFeedback(null);
        setIsFocused(false);
        setIsRecording(false);
        setIsTranscribing(false);
        setSpeechTranscript('');
        setSpeechMeta({});
        setRecordAttempts(0);
        setSpeechError('');
    }, [currentQuestion?.question_id]);

    useEffect(() => {
        if (speechMode) return;
        if (!feedback && !isEvaluating && inputRef.current) {
            const timer = setTimeout(() => {
                focusAndMoveCursorToEnd();
            }, 100);
            return () => clearTimeout(timer);
        }
        if (feedback && feedback.level === 1 && !isEvaluating) {
            focusAndMoveCursorToEnd();
        }
    }, [currentIndex, feedback, isEvaluating, speechMode, userAnswer]);

    useEffect(() => {
        if (speechMode) return;
        const handleEnter = (e) => {
            if (e.key !== 'Enter' || e.shiftKey) return;

            if (feedback && feedback.level >= 2) {
                e.preventDefault();
                handleNext();
                return;
            }

            if (document.activeElement !== inputRef.current) return;
            e.preventDefault();

            if (feedback && feedback.level === 1) {
                if (userAnswer.trim() !== lastSubmittedAnswer) handleSubmit();
                return;
            }

            if (userAnswer.trim() && !isEvaluating) handleSubmit();
        };

        window.addEventListener('keydown', handleEnter);
        return () => window.removeEventListener('keydown', handleEnter);
    }, [speechMode, userAnswer, feedback, isEvaluating, lastSubmittedAnswer]);

    const handleTranscription = async (audioBlob, mimeType) => {
        setIsTranscribing(true);
        setSpeechError('');

        try {
            const result = await transcribeSpeech({
                audioBlob,
                filename: mimeType?.includes('mp4') ? 'speech.mp4' : 'speech.webm',
                language: 'zh'
            });

            const transcript = (result?.transcript || '').trim();
            setSpeechTranscript(transcript);
            setUserAnswer(transcript);
            setSpeechMeta(result || {});
            setRecordAttempts((prev) => prev + 1);

            if (!transcript) {
                setSpeechError('No transcript detected. Please record again.');
                return;
            }

            const conf = Number(result?.confidence);
            if (Number.isFinite(conf) && conf < speechConfig.min_asr_confidence) {
                setSpeechError(`ASR confidence is low (${conf.toFixed(2)}). Please record again.`);
            }
        } catch (error) {
            setSpeechError(getErrorMessage(error, 'Speech transcription failed. Please retry.'));
        } finally {
            setIsTranscribing(false);
        }
    };

    const handleStartRecording = async () => {
        if (!speechMode || isRecording || isTranscribing) return;
        if (!canRecordMore) {
            setSpeechError(`You reached the max attempts (${speechConfig.max_attempts}).`);
            return;
        }
        if (!navigator.mediaDevices?.getUserMedia || typeof window.MediaRecorder === 'undefined') {
            setSpeechError('Current browser does not support recording. Please switch to a modern browser.');
            return;
        }

        setFeedback(null);
        setLastSubmittedAnswer('');
        setSpeechError('');

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaStreamRef.current = stream;
            chunksRef.current = [];

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

                if (mediaStreamRef.current) {
                    mediaStreamRef.current.getTracks().forEach((track) => track.stop());
                    mediaStreamRef.current = null;
                }

                if (!chunksRef.current.length) {
                    setSpeechError('No audio captured. Please record again.');
                    return;
                }

                const blobType = recorder.mimeType || mimeType || 'audio/webm';
                const audioBlob = new Blob(chunksRef.current, { type: blobType });
                chunksRef.current = [];
                await handleTranscription(audioBlob, blobType);
            };

            recorder.start();
            setIsRecording(true);

            stopTimerRef.current = setTimeout(() => {
                if (recorder.state === 'recording') {
                    setSpeechError('Max recording duration reached. Auto-stopped and transcribing.');
                    recorder.stop();
                }
            }, speechConfig.max_duration_sec * 1000);
        } catch (error) {
            cleanupMedia();
            setIsRecording(false);
            setSpeechError(getErrorMessage(error, 'Microphone permission denied or unavailable.'));
        }
    };

    const handleStopRecording = () => {
        if (!recorderRef.current || recorderRef.current.state !== 'recording') return;
        recorderRef.current.stop();
    };

    const handleSubmit = async () => {
        if (isEvaluating || !currentQuestion) return;
        if (!activeAnswer.trim()) return;

        if (speechMode) {
            if (isRecording || isTranscribing) return;
            if (lowConfidence) {
                setSpeechError(
                    `ASR confidence is below threshold (${speechConfig.min_asr_confidence.toFixed(2)}). Please record again.`
                );
                return;
            }
        }

        setIsEvaluating(true);
        try {
            const payload = {
                user_id: localStorage.getItem('chilan_user_id') || 'test-user-id',
                lesson_id: currentQuestion.lesson_id || 101,
                question_id: currentQuestion.question_id,
                question_type: currentQuestion.question_type,
                original_text: currentQuestion.original_text,
                standard_answers: Array.isArray(currentQuestion.standard_answers)
                    ? currentQuestion.standard_answers
                    : [currentQuestion.standard_answers],
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
            };

            const res = await evaluateStudyAnswer(payload);
            setFeedback(res?.data?.data || null);
            setLastSubmittedAnswer(activeAnswer);
        } catch (error) {
            setFeedback({
                level: 1,
                isCorrect: false,
                message: getErrorMessage(error, 'Evaluation service failed. Please try again.')
            });
        } finally {
            setIsEvaluating(false);
        }
    };

    const handleNext = () => {
        if (currentIndex < questionList.length - 1) {
            setCurrentIndex((prev) => prev + 1);
            return;
        }
        onAllDone();
    };

    if (!currentQuestion) return null;

    const isResubmitDisabled =
        isEvaluating ||
        isTranscribing ||
        isRecording ||
        !activeAnswer.trim() ||
        (!speechMode && feedback?.level === 1 && activeAnswer === lastSubmittedAnswer);

    const config = feedback ? getFeedbackConfig(feedback.level) : null;

    return (
        <div className="max-w-4xl mx-auto px-6 pt-20 pb-0">
            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="flex items-center justify-center gap-5 mb-8">
                <div className="flex items-center gap-3">
                    <Sparkles className="text-blue-500" size={28} />
                    <h1 className="text-5xl font-black text-slate-900 tracking-tight">
                        {isReview ? 'Smart Review' : 'Practice Session'}
                    </h1>
                </div>
                <div className="px-5 py-1.5 bg-slate-200/50 rounded-full text-xl font-black text-slate-500 tracking-tighter">
                    {currentIndex + 1} / {questionList.length}
                </div>
            </motion.div>

            <motion.div variants={fadeInUp} initial="hidden" animate="show" className="text-center mb-8">
                <span className="text-xl font-bold text-blue-500 uppercase tracking-[0.3em] block mb-1">
                    {getQuestionPrompt(currentQuestion.question_type)}
                </span>
                <p className="text-4xl md:text-5xl font-black text-slate-900 leading-tight px-4">
                    "{currentQuestion.original_text}"
                </p>
            </motion.div>

            <motion.div
                variants={fadeInUp}
                initial="hidden"
                animate="show"
                className="bg-white p-8 md:p-10 rounded-[2.5rem] shadow-xl shadow-slate-200/40 border border-slate-100"
            >
                {!speechMode ? (
                    <>
                        <div
                            className={`
                                w-full h-20 px-8 flex items-center justify-center transition-all duration-300
                                bg-slate-50 border-2 rounded-[2rem]
                                ${isFocused ? 'border-blue-500 bg-white shadow-md' : 'border-slate-100'}
                                ${feedback && feedback.level >= 2 ? 'opacity-60' : 'opacity-100'}
                                mb-6
                            `}
                        >
                            <textarea
                                ref={inputRef}
                                value={userAnswer}
                                onChange={(e) => setUserAnswer(e.target.value)}
                                onFocus={() => setIsFocused(true)}
                                onBlur={() => setIsFocused(false)}
                                placeholder={isFocused ? '' : 'Type your answer here...'}
                                disabled={isEvaluating || (feedback && feedback.level >= 2)}
                                className="w-full h-auto max-h-full bg-transparent text-center focus:outline-none resize-none leading-relaxed text-slate-800 placeholder:text-slate-400 text-3xl font-bold"
                                rows={1}
                            />
                        </div>

                        <motion.button
                            key="submit-btn"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleSubmit}
                            disabled={!activeAnswer.trim() || isEvaluating}
                            className="w-full py-5 bg-slate-900 text-white rounded-[1.2rem] font-black text-xl hover:bg-blue-600 disabled:bg-slate-200 transition-all flex items-center justify-center gap-3 shadow-lg"
                        >
                            {isEvaluating ? <Loader2 className="animate-spin" /> : <Send size={22} />}
                            {isEvaluating ? 'Evaluating...' : 'Submit Answer'}
                        </motion.button>
                    </>
                ) : (
                    <>
                        <div className="mb-5 rounded-[1.5rem] border border-slate-200 bg-slate-50 p-5">
                            <p className="text-xs font-black uppercase tracking-[0.2em] text-slate-500 mb-2">Transcript Preview</p>
                            <p className={`text-2xl font-bold min-h-10 ${speechTranscript ? 'text-slate-800' : 'text-slate-400'}`}>
                                {speechTranscript || 'No transcript yet. Click Start Recording.'}
                            </p>
                            <p className="text-xs text-slate-500 mt-3">
                                Attempts: {recordAttempts} / {speechConfig.max_attempts} | Max duration: {speechConfig.max_duration_sec}s
                            </p>
                            {hasConfidence && (
                                <p className={`text-xs mt-1 ${lowConfidence ? 'text-red-600' : 'text-slate-500'}`}>
                                    ASR confidence: {confidenceValue.toFixed(2)} (threshold: {speechConfig.min_asr_confidence.toFixed(2)})
                                </p>
                            )}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
                            <button
                                onClick={isRecording ? handleStopRecording : handleStartRecording}
                                disabled={isTranscribing || (!isRecording && !canRecordMore)}
                                className={`py-4 rounded-[1.1rem] font-black text-lg transition-all flex items-center justify-center gap-2 ${
                                    isRecording
                                        ? 'bg-red-600 text-white hover:bg-red-700'
                                        : 'bg-slate-900 text-white hover:bg-blue-600 disabled:bg-slate-300'
                                }`}
                            >
                                {isRecording ? <Square size={18} /> : <Mic size={18} />}
                                {isRecording ? 'Stop Recording' : 'Start Recording'}
                            </button>

                            <button
                                onClick={handleStartRecording}
                                disabled={isRecording || isTranscribing || !canRecordMore}
                                className="py-4 rounded-[1.1rem] font-black text-lg transition-all bg-white text-slate-800 border border-slate-200 hover:bg-slate-100 disabled:bg-slate-100 disabled:text-slate-400"
                            >
                                Re-record
                            </button>
                        </div>

                        {isTranscribing && (
                            <div className="mb-4 py-3 rounded-xl bg-blue-50 text-blue-700 font-bold flex items-center justify-center gap-2">
                                <Loader2 className="animate-spin" size={18} />
                                Transcribing audio...
                            </div>
                        )}

                        {speechError && (
                            <div className="mb-4 py-3 px-4 rounded-xl bg-red-50 text-red-700 font-bold text-sm">{speechError}</div>
                        )}

                        <button
                            onClick={handleSubmit}
                            disabled={!activeAnswer.trim() || isEvaluating || isTranscribing || isRecording || lowConfidence}
                            className="w-full py-5 bg-slate-900 text-white rounded-[1.2rem] font-black text-xl hover:bg-blue-600 disabled:bg-slate-200 transition-all flex items-center justify-center gap-3 shadow-lg"
                        >
                            {isEvaluating ? <Loader2 className="animate-spin" /> : <Send size={22} />}
                            {isEvaluating ? 'Evaluating...' : 'Submit Transcript'}
                        </button>
                    </>
                )}

                <AnimatePresence mode="wait">
                    {feedback && (
                        <motion.div key="feedback-area" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-5 mt-6">
                            <div className={`p-6 rounded-[2rem] border-2 transition-colors duration-500 ${config.card}`}>
                                <div className="flex gap-4">
                                    {config.icon}
                                    <div className="flex-1">
                                        <h4 className={`text-xl font-black mb-1 ${config.titleColor}`}>{config.title}</h4>
                                        <p
                                            style={{ fontFamily: '"Times New Roman", Times, serif' }}
                                            className={`mt-3 text-xl md:text-2xl font-bold whitespace-pre-line leading-snug ${config.msgColor}`}
                                        >
                                            {feedback.message}
                                        </p>
                                        {speechMode && feedback.recognizedText && (
                                            <p className="mt-4 text-base font-semibold text-slate-600">
                                                Recognized: "{feedback.recognizedText}"
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <WordContextCard metadata={currentQuestion.metadata} />

                            <div className="flex flex-col gap-3">
                                {feedback.level === 1 ? (
                                    <>
                                        <button
                                            onClick={handleSubmit}
                                            disabled={isResubmitDisabled}
                                            className="w-full py-5 bg-slate-900 text-white rounded-[1.2rem] font-black text-xl hover:bg-slate-800 transition-all flex items-center justify-center gap-3 shadow-lg disabled:bg-slate-200 disabled:text-slate-400"
                                        >
                                            {isEvaluating ? <Loader2 className="animate-spin" /> : <RefreshCcw size={22} />}
                                            {speechMode ? 'Submit Current Transcript' : 'Resubmit'}
                                        </button>
                                        <button
                                            onClick={handleNext}
                                            className="w-full py-5 bg-blue-600 text-white rounded-[1.2rem] font-black text-xl hover:bg-blue-700 transition-all flex items-center justify-center gap-3 shadow-lg"
                                        >
                                            Skip This Question
                                            <ArrowRight size={22} />
                                        </button>
                                    </>
                                ) : (
                                    <button
                                        onClick={handleNext}
                                        className="w-full py-5 bg-blue-600 text-white rounded-[1.2rem] font-black text-xl hover:bg-blue-700 transition-all flex items-center justify-center shadow-lg shadow-blue-100"
                                    >
                                        {currentIndex === questionList.length - 1 ? 'Finish Practice' : 'Next Question'}
                                        <span className="ml-3 text-blue-200 font-normal text-xs uppercase tracking-widest">Enter</span>
                                    </button>
                                )}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
}
