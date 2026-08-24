import {
    JAPANESE_FOUNDATION_AUDIO_ROUTE,
    japaneseCourseIntroAudioFilename,
    japaneseFoundationAudioFilename,
} from './japaneseStaticAudioNaming';

const API_BASE = import.meta.env.VITE_APP_API_BASE_URL || '';

export function buildJapaneseFoundationAudioUrl(text) {
    return `${API_BASE}${JAPANESE_FOUNDATION_AUDIO_ROUTE}/${japaneseFoundationAudioFilename(text)}`;
}

export function buildJapaneseCourseIntroAudioUrl(language, slideId) {
    return `${API_BASE}${JAPANESE_FOUNDATION_AUDIO_ROUTE}/${japaneseCourseIntroAudioFilename(language, slideId)}`;
}
