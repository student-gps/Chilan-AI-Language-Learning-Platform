import axios from 'axios';
import { clearAuthStorage } from '../utils/authStorage';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_APP_API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// 全局 401 拦截：token 失效时自动清除本地状态并跳转登录
// 排除 /auth 路径的请求，避免登录接口本身的 401 触发循环跳转
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (
      error.response?.status === 401 &&
      !error.config?.url?.includes('/auth')
    ) {
      clearAuthStorage();
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);

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
