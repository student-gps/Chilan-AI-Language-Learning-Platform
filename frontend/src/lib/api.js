import apiClient from '../api/apiClient';

const trimTrailingSlash = (value = '') => value.replace(/\/+$/, '');
const ensureLeadingSlash = (value = '') => (value.startsWith('/') ? value : `/${value}`);

export const buildApiUrl = (path = '') => {
    const base = trimTrailingSlash(import.meta.env.VITE_API_BASE_URL || '');
    return `${base}${ensureLeadingSlash(path)}`;
};

export const evaluateStudyAnswer = (payload) => apiClient.post('/study/evaluate', payload);

export const transcribeSpeech = async ({ audioBlob, filename = 'speech.webm', language = 'zh', prompt = '' }) => {
    const formData = new FormData();
    formData.append('audio', audioBlob, filename);
    formData.append('language', language);
    if (prompt) formData.append('prompt', prompt);

    const res = await apiClient.post('/study/speech/transcribe', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });

    return res.data?.data || null;
};

export const api = apiClient;
export default apiClient;
