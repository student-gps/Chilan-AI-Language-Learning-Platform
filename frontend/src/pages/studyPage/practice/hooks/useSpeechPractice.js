import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { transcribeSpeech } from '../../../../api/apiClient';
import { getQuestionTypeConfig, isSpeechQuestion } from '../questionTypeConfig';

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

const createEmptyWaveform = () => Array.from({ length: 18 }, () => 0);

export default function useSpeechPractice({ currentQuestion, onTranscriptReady, onResetFeedback }) {
    const [isRecording, setIsRecording] = useState(false);
    const [isTranscribing, setIsTranscribing] = useState(false);
    const [speechTranscript, setSpeechTranscript] = useState('');
    const [speechMeta, setSpeechMeta] = useState({});
    const [recordingSeconds, setRecordingSeconds] = useState(0);
    const [recordAttempts, setRecordAttempts] = useState(0);
    const [speechError, setSpeechError] = useState('');
    const [liveWaveform, setLiveWaveform] = useState(createEmptyWaveform);

    const recorderRef = useRef(null);
    const mediaStreamRef = useRef(null);
    const chunksRef = useRef([]);
    const stopTimerRef = useRef(null);
    const elapsedTimerRef = useRef(null);
    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const analyserDataRef = useRef(null);
    const waveformFrameRef = useRef(null);

    const speechMode = isSpeechQuestion(currentQuestion);
    const questionConfig = useMemo(() => getQuestionTypeConfig(currentQuestion), [currentQuestion]);
    const speechConfig = useMemo(() => normalizeSpeechConfig(currentQuestion), [currentQuestion]);
    const lowConfidence =
        Number.isFinite(Number(speechMeta?.confidence)) &&
        Number(speechMeta?.confidence) < speechConfig.min_asr_confidence;

    const clearRecordingTimer = useCallback(() => {
        if (stopTimerRef.current) {
            clearTimeout(stopTimerRef.current);
            stopTimerRef.current = null;
        }
    }, []);

    const clearElapsedTimer = useCallback(() => {
        if (elapsedTimerRef.current) {
            clearInterval(elapsedTimerRef.current);
            elapsedTimerRef.current = null;
        }
    }, []);

    const cleanupMedia = useCallback(() => {
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
        setLiveWaveform(createEmptyWaveform());
    }, [clearElapsedTimer, clearRecordingTimer]);

    const resetSpeechState = useCallback(() => {
        setIsRecording(false);
        setIsTranscribing(false);
        setSpeechTranscript('');
        setSpeechMeta({});
        setRecordingSeconds(0);
        setRecordAttempts(0);
        setSpeechError('');
        setLiveWaveform(createEmptyWaveform());
    }, []);

    const startLiveWaveform = useCallback((stream) => {
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
    }, []);

    const handleTranscription = useCallback(async (audioBlob, mimeType) => {
        setIsTranscribing(true);
        setSpeechError('');

        try {
            const result = await transcribeSpeech({
                audioBlob,
                filename: mimeType?.includes('mp4') ? 'speech.mp4' : 'speech.webm',
                language: questionConfig.speechLanguage || 'zh'
            });

            const transcript = sanitizeFrontendTranscript(result?.transcript || '');
            setSpeechTranscript(transcript);
            setSpeechMeta(result || {});
            setRecordAttempts((prev) => prev + 1);
            onTranscriptReady?.(transcript);

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
                onTranscriptReady?.('');
                setSpeechError('未检测到有效语音输入，请重新录音。');
            } else {
                setSpeechError(detail);
            }
        } finally {
            setIsTranscribing(false);
        }
    }, [onTranscriptReady, questionConfig.speechLanguage, speechConfig.min_asr_confidence]);

    const handleStartRecording = useCallback(async () => {
        if (!speechMode || isRecording || isTranscribing) return;
        if (!navigator.mediaDevices?.getUserMedia || typeof window.MediaRecorder === 'undefined') {
            setSpeechError('当前浏览器不支持录音，请更换现代浏览器后再试。');
            return;
        }

        onResetFeedback?.();
        setSpeechError('');
        setSpeechTranscript('');
        setSpeechMeta({});
        setRecordingSeconds(0);
        setLiveWaveform(createEmptyWaveform());
        onTranscriptReady?.('');

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
    }, [
        cleanupMedia,
        clearElapsedTimer,
        clearRecordingTimer,
        handleTranscription,
        isRecording,
        isTranscribing,
        onResetFeedback,
        onTranscriptReady,
        speechConfig.max_duration_sec,
        speechMode,
        startLiveWaveform
    ]);

    const handleStopRecording = useCallback(() => {
        if (!recorderRef.current || recorderRef.current.state !== 'recording') return;
        recorderRef.current.stop();
    }, []);

    useEffect(() => () => cleanupMedia(), [cleanupMedia]);

    return {
        speechMode,
        speechConfig,
        isRecording,
        isTranscribing,
        speechTranscript,
        speechMeta,
        recordingSeconds,
        recordAttempts,
        speechError,
        liveWaveform,
        lowConfidence,
        setSpeechError,
        handleStartRecording,
        handleStopRecording,
        cleanupMedia,
        resetSpeechState
    };
}
