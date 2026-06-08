import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { claimGlobalAudio, releaseGlobalAudio, stopGlobalAudio } from '../../../../utils/audioPlayback';

const normalizeLineRef = (value) => {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
};

const audioLineKey = (item) => {
    const lineRef = normalizeLineRef(item?.line_ref);
    if (lineRef) return `line:${lineRef}`;
    const sourceSection = String(item?.source_section || '').trim();
    const sourceRef = normalizeLineRef(item?.source_ref);
    if (sourceSection && sourceRef) return `${sourceSection}:${sourceRef}`;
    return '';
};

const buildAbsoluteAudioUrl = (url, apiBase) => {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    return `${apiBase}${url}`;
};

export const buildLessonAudioUrl = (lessonAudioAssets, apiBase) => {
    const relativeUrl = lessonAudioAssets?.full_audio?.audio_url || '';
    if (!relativeUrl) return '';
    return buildAbsoluteAudioUrl(relativeUrl, apiBase);
};

export default function useTeachingAudio({ lessonAudioAssets, lessonFullAudioUrl, apiBase }) {
    const [playingKey, setPlayingKey] = useState(null);
    const [audioLoadingKey, setAudioLoadingKey] = useState(null);
    const [lessonAudioDuration, setLessonAudioDuration] = useState(0);
    const [lessonAudioCurrentTime, setLessonAudioCurrentTime] = useState(0);
    const [isLessonAudioPlaying, setIsLessonAudioPlaying] = useState(false);
    const [lessonAudioVolume, setLessonAudioVolume] = useState(1);
    const [lessonAudioRate, setLessonAudioRate] = useState(1);
    const [showLessonVolumeControl, setShowLessonVolumeControl] = useState(false);
    const [showFloatingLessonAudio, setShowFloatingLessonAudio] = useState(false);
    const [isFloatingLessonAudioOpen, setIsFloatingLessonAudioOpen] = useState(true);

    const audioRef = useRef(null);
    const lessonAudioRef = useRef(null);
    const lessonVolumeControlRef = useRef(null);
    const lessonAudioSectionRef = useRef(null);

    const audioAssetMap = useMemo(() => {
        const map = new Map();
        (lessonAudioAssets?.items || []).forEach((item) => {
            const lineRef = normalizeLineRef(item?.line_ref);
            if (lineRef) map.set(`line:${lineRef}`, item);
            const key = audioLineKey(item);
            if (key) map.set(key, item);
        });
        return map;
    }, [lessonAudioAssets]);

    const activeLessonLineRef = useMemo(() => {
        if (!isLessonAudioPlaying) return null;
        const currentTime = Number(lessonAudioCurrentTime || 0);
        const matchedItem = (lessonAudioAssets?.items || []).find((item) => {
            const lineRef = normalizeLineRef(item?.line_ref) || normalizeLineRef(item?.source_ref);
            const start = Number(item?.start_time_seconds);
            const end = Number(item?.end_time_seconds);
            return lineRef && Number.isFinite(start) && Number.isFinite(end) && currentTime >= start && currentTime < end;
        });
        return normalizeLineRef(matchedItem?.line_ref) || normalizeLineRef(matchedItem?.source_ref);
    }, [isLessonAudioPlaying, lessonAudioCurrentTime, lessonAudioAssets]);

    const stopCurrentAudio = useCallback(() => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
            releaseGlobalAudio(audioRef.current);
            audioRef.current = null;
        }
        setPlayingKey(null);
        setAudioLoadingKey(null);
    }, []);

    const stopLessonAudio = useCallback(() => {
        if (lessonAudioRef.current) {
            lessonAudioRef.current.pause();
            lessonAudioRef.current.currentTime = 0;
            releaseGlobalAudio(lessonAudioRef.current);
        }
        setIsLessonAudioPlaying(false);
        setLessonAudioCurrentTime(0);
    }, []);

    useEffect(() => {
        return () => {
            if (audioRef.current) {
                audioRef.current.pause();
                audioRef.current = null;
            }
            if (lessonAudioRef.current) {
                lessonAudioRef.current.pause();
                lessonAudioRef.current = null;
            }
            stopGlobalAudio();
        };
    }, []);

    useEffect(() => {
        const handleOutsideClick = (event) => {
            if (!lessonVolumeControlRef.current?.contains(event.target)) {
                setShowLessonVolumeControl(false);
            }
        };

        if (showLessonVolumeControl) {
            document.addEventListener('mousedown', handleOutsideClick);
        }

        return () => {
            document.removeEventListener('mousedown', handleOutsideClick);
        };
    }, [showLessonVolumeControl]);

    useEffect(() => {
        setLessonAudioCurrentTime(0);
        setLessonAudioDuration(0);
        setIsLessonAudioPlaying(false);
        setShowFloatingLessonAudio(false);
        setIsFloatingLessonAudioOpen(true);
        if (lessonAudioRef.current) {
            lessonAudioRef.current.pause();
            lessonAudioRef.current = null;
        }
    }, [lessonFullAudioUrl]);

    useEffect(() => {
        if (lessonAudioRef.current) {
            lessonAudioRef.current.volume = lessonAudioVolume;
        }
    }, [lessonAudioVolume]);

    useEffect(() => {
        if (lessonAudioRef.current) {
            lessonAudioRef.current.playbackRate = lessonAudioRate;
        }
    }, [lessonAudioRate]);

    useEffect(() => {
        if (!lessonFullAudioUrl) {
            setShowFloatingLessonAudio(false);
            return;
        }

        const updateFloatingPlayerVisibility = () => {
            const section = lessonAudioSectionRef.current;
            if (!section) {
                setShowFloatingLessonAudio(false);
                return;
            }

            const rect = section.getBoundingClientRect();
            setShowFloatingLessonAudio(rect.bottom < 96);
        };

        updateFloatingPlayerVisibility();
        window.addEventListener('scroll', updateFloatingPlayerVisibility, { passive: true });
        window.addEventListener('resize', updateFloatingPlayerVisibility);

        return () => {
            window.removeEventListener('scroll', updateFloatingPlayerVisibility);
            window.removeEventListener('resize', updateFloatingPlayerVisibility);
        };
    }, [lessonFullAudioUrl]);

    const playFromUrl = useCallback(async (url, key) => {
        if (!url) return;

        if (audioLoadingKey === key) {
            return;
        }

        if (playingKey === key) {
            stopCurrentAudio();
            return;
        }

        stopCurrentAudio();
        stopLessonAudio();

        const audio = new Audio(url);
        claimGlobalAudio(audio);
        audioRef.current = audio;
        setPlayingKey(key);
        setAudioLoadingKey(key);

        // 用 functional updater 比对当前 key，避免 audio A 的回调在 audio B 启动后
        // 才触发时，错误清掉 audio B 的状态（stale closure race condition）
        const clearIfStillCurrent = (prevKey) => (prevKey === key ? null : prevKey);

        audio.onplaying = () => {
            if (audioRef.current === audio) setAudioLoadingKey(clearIfStillCurrent);
        };
        audio.oncanplay = () => {
            if (audioRef.current === audio) setAudioLoadingKey(clearIfStillCurrent);
        };
        audio.onpause = () => {
            if (audioRef.current === audio) audioRef.current = null;
            releaseGlobalAudio(audio);
            setPlayingKey(clearIfStillCurrent);
            setAudioLoadingKey(clearIfStillCurrent);
        };
        audio.onended = () => {
            if (audioRef.current === audio) audioRef.current = null;
            releaseGlobalAudio(audio);
            setPlayingKey(clearIfStillCurrent);
            setAudioLoadingKey(clearIfStillCurrent);
        };
        audio.onerror = () => {
            if (audioRef.current === audio) audioRef.current = null;
            releaseGlobalAudio(audio);
            setPlayingKey(clearIfStillCurrent);
            setAudioLoadingKey(clearIfStillCurrent);
        };

        try {
            await audio.play();
        } catch (error) {
            console.error('播放音频失败:', error);
            if (audioRef.current === audio) audioRef.current = null;
            releaseGlobalAudio(audio);
            setPlayingKey(clearIfStillCurrent);
            setAudioLoadingKey(clearIfStillCurrent);
        }
    }, [audioLoadingKey, playingKey, stopCurrentAudio, stopLessonAudio]);

    const playTtsFallback = useCallback((text, key, language = 'zh') => {
        if (!text) return;
        const params = new URLSearchParams({
            text,
            language,
        });
        const url = `${apiBase}/study/tts?${params.toString()}`;
        playFromUrl(url, key);
    }, [apiBase, playFromUrl]);

    const playDialogueAudio = useCallback(({ lineRef, text }) => {
        const normalizedLineRef = normalizeLineRef(lineRef);
        const item = audioAssetMap.get(`dialogue:${normalizedLineRef}`) || audioAssetMap.get(`line:${normalizedLineRef}`);
        const readyUrl = buildAbsoluteAudioUrl(item?.audio_url, apiBase);
        const playbackKey = `line-${lineRef}`;

        if (readyUrl) {
            playFromUrl(readyUrl, playbackKey);
            return;
        }

        playTtsFallback(text, playbackKey);
    }, [apiBase, audioAssetMap, playFromUrl, playTtsFallback]);

    const handleLessonAudioToggle = useCallback(async () => {
        if (!lessonFullAudioUrl) return;

        if (!lessonAudioRef.current) {
            const audio = new Audio(lessonFullAudioUrl);
            audio.volume = lessonAudioVolume;
            audio.playbackRate = lessonAudioRate;
            if ('preservesPitch' in audio) audio.preservesPitch = true;
            if ('mozPreservesPitch' in audio) audio.mozPreservesPitch = true;
            if ('webkitPreservesPitch' in audio) audio.webkitPreservesPitch = true;
            lessonAudioRef.current = audio;

            audio.onloadedmetadata = () => {
                setLessonAudioDuration(Number.isFinite(audio.duration) ? audio.duration : 0);
            };
            audio.ontimeupdate = () => {
                setLessonAudioCurrentTime(audio.currentTime || 0);
            };
            audio.onpause = () => {
                setIsLessonAudioPlaying(false);
                releaseGlobalAudio(audio);
            };
            audio.onended = () => {
                setIsLessonAudioPlaying(false);
                setLessonAudioCurrentTime(0);
                releaseGlobalAudio(audio);
                if (lessonAudioRef.current) {
                    lessonAudioRef.current.currentTime = 0;
                }
            };
            audio.onerror = () => {
                setIsLessonAudioPlaying(false);
                releaseGlobalAudio(audio);
            };
        }

        const audio = lessonAudioRef.current;
        if (!audio) return;

        if (isLessonAudioPlaying) {
            audio.pause();
            setIsLessonAudioPlaying(false);
            return;
        }

        stopCurrentAudio();
        claimGlobalAudio(audio, { resetPrevious: true });

        try {
            await audio.play();
            setIsLessonAudioPlaying(true);
        } catch (error) {
            console.error('播放整课音频失败:', error);
            setIsLessonAudioPlaying(false);
            releaseGlobalAudio(audio);
        }
    }, [isLessonAudioPlaying, lessonAudioRate, lessonAudioVolume, lessonFullAudioUrl, stopCurrentAudio]);

    const handleLessonAudioSeek = useCallback((event) => {
        const nextTime = Number(event.target.value || 0);
        setLessonAudioCurrentTime(nextTime);
        if (lessonAudioRef.current) {
            lessonAudioRef.current.currentTime = nextTime;
        }
    }, []);

    const handleLessonAudioVolumeChange = useCallback((event) => {
        setLessonAudioVolume(Number(event.target.value || 0));
    }, []);

    const handleLessonAudioRateChange = useCallback((event) => {
        setLessonAudioRate(Number(event.target.value || 1));
    }, []);

    return {
        playingKey,
        audioLoadingKey,
        lessonAudioDuration,
        lessonAudioCurrentTime,
        isLessonAudioPlaying,
        lessonAudioVolume,
        lessonAudioRate,
        showLessonVolumeControl,
        showFloatingLessonAudio,
        isFloatingLessonAudioOpen,
        lessonVolumeControlRef,
        lessonAudioSectionRef,
        activeLessonLineRef,
        setShowLessonVolumeControl,
        setIsFloatingLessonAudioOpen,
        playTtsFallback,
        playDialogueAudio,
        handleLessonAudioToggle,
        handleLessonAudioSeek,
        handleLessonAudioVolumeChange,
        handleLessonAudioRateChange,
    };
}
