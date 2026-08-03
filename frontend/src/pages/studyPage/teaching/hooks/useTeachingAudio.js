import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { claimGlobalAudio, releaseGlobalAudio, stopGlobalAudio } from '../../../../utils/audioPlayback';
import { renewLessonAudioUrl } from '../../../../api/apiClient';

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

const audioAssetRef = (item, fallbackLineRef = null) => {
    if (item?.audio_id) return `audio:${item.audio_id}`;
    const lineRef = normalizeLineRef(item?.line_ref) || normalizeLineRef(fallbackLineRef);
    return lineRef ? `line:${lineRef}` : '';
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

export default function useTeachingAudio({ lessonAudioAssets, lessonFullAudioUrl, apiBase, courseId, lessonId }) {
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

    const renewAudioUrl = useCallback(async (assetRef) => {
        if (!courseId || !lessonId || !assetRef) return '';
        try {
            const result = await renewLessonAudioUrl({ courseId, lessonId, assetRef });
            return buildAbsoluteAudioUrl(result?.audio_url, apiBase);
        } catch (error) {
            console.error('刷新课程音频链接失败:', error);
            return '';
        }
    }, [apiBase, courseId, lessonId]);

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
        if (!lessonFullAudioUrl && !lessonAudioAssets?.full_audio) {
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
    }, [lessonAudioAssets?.full_audio, lessonFullAudioUrl]);

    const playFromUrl = useCallback(async (url, key, assetRef = '') => {
        if (!url && !assetRef) return;
        const initialUrl = url || await renewAudioUrl(assetRef);
        if (!initialUrl) return;

        if (audioLoadingKey === key) {
            return;
        }

        if (playingKey === key) {
            stopCurrentAudio();
            return;
        }

        stopCurrentAudio();
        stopLessonAudio();

        const audio = new Audio(initialUrl);
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
        let hasRenewed = false;
        const cleanupFailedAudio = () => {
            if (audioRef.current === audio) audioRef.current = null;
            releaseGlobalAudio(audio);
            setPlayingKey(clearIfStillCurrent);
            setAudioLoadingKey(clearIfStillCurrent);
        };
        const retryWithRenewedUrl = async () => {
            if (hasRenewed || !assetRef) {
                cleanupFailedAudio();
                return;
            }
            hasRenewed = true;
            const renewedUrl = await renewAudioUrl(assetRef);
            if (!renewedUrl) {
                cleanupFailedAudio();
                return;
            }
            audio.src = renewedUrl;
            try {
                await audio.play();
            } catch (error) {
                console.error('刷新链接后播放音频失败:', error);
                cleanupFailedAudio();
            }
        };

        audio.onerror = () => { void retryWithRenewedUrl(); };
        audio.play().catch((error) => {
            console.error('播放音频失败:', error);
            void retryWithRenewedUrl();
        });
    }, [audioLoadingKey, playingKey, renewAudioUrl, stopCurrentAudio, stopLessonAudio]);

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

        if (readyUrl || audioAssetRef(item, lineRef)) {
            playFromUrl(readyUrl, playbackKey, audioAssetRef(item, lineRef));
            return;
        }

        playTtsFallback(text, playbackKey);
    }, [apiBase, audioAssetMap, playFromUrl, playTtsFallback]);

    const handleLessonAudioToggle = useCallback(async () => {
        const initialUrl = lessonFullAudioUrl || await renewAudioUrl('full');
        if (!initialUrl) return;

        if (!lessonAudioRef.current) {
            const audio = new Audio(initialUrl);
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
            let hasRenewed = false;
            audio.onerror = () => {
                if (hasRenewed) {
                    setIsLessonAudioPlaying(false);
                    releaseGlobalAudio(audio);
                    return;
                }
                hasRenewed = true;
                renewAudioUrl('full').then((renewedUrl) => {
                    if (!renewedUrl) throw new Error('renewal failed');
                    audio.src = renewedUrl;
                    return audio.play();
                }).then(() => {
                    setIsLessonAudioPlaying(true);
                }).catch(() => {
                    setIsLessonAudioPlaying(false);
                    releaseGlobalAudio(audio);
                });
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
    }, [isLessonAudioPlaying, lessonAudioRate, lessonAudioVolume, lessonFullAudioUrl, renewAudioUrl, stopCurrentAudio]);

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
