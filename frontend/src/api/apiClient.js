import axios from 'axios';

// 🚀 这里会自动根据环境切换 URL
const apiClient = axios.create({
    baseURL: import.meta.env.VITE_APP_API_BASE_URL || import.meta.env.VITE_API_BASE_URL,
    headers: {
        'Content-Type': 'application/json'
    }
});

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

export default apiClient;
