import { normalizeJapaneseFoundationLanguage } from './japaneseFoundationLanguages.js';

const FNV_OFFSET_BASIS_64 = 0xcbf29ce484222325n;
const FNV_PRIME_64 = 0x100000001b3n;

export const JAPANESE_FOUNDATION_AUDIO_ROUTE = '/media/japanese-foundation';

export function japaneseFoundationAudioFilename(text) {
    const bytes = new TextEncoder().encode(String(text || '').trim());
    let hash = FNV_OFFSET_BASIS_64;
    for (const byte of bytes) {
        hash ^= BigInt(byte);
        hash = BigInt.asUintN(64, hash * FNV_PRIME_64);
    }
    return `ja-${hash.toString(16).padStart(16, '0')}.mp3`;
}

export function japaneseCourseIntroAudioFilename(language, slideId) {
    const safeLanguage = normalizeJapaneseFoundationLanguage(language);
    const safeSlideId = String(slideId || '').replace(/[^a-z0-9_-]/gi, '');
    return `course-intro-${safeLanguage}-${safeSlideId}.mp3`;
}
