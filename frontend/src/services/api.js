import axios from 'axios';

const API = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('aegis_jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const loginUser = async (username, role = 'ENGINEER') => {
  try {
    const response = await API.post('/auth/login', { username, role });
    if (response.data.access_token) {
      localStorage.setItem('aegis_jwt_token', response.data.access_token);
      localStorage.setItem('aegis_user', JSON.stringify(response.data.user));
    }
    return response.data;
  } catch (error) {
    console.error('Failed to login:', error);
    throw error;
  }
};

export const fetchHealthStatus = async () => {
  try {
    const response = await API.get('/health');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch health status:', error);
    return null;
  }
};

export const sendChatMessage = async (payload) => {
  try {
    const response = await API.post('/chat', payload);
    return response.data;
  } catch (error) {
    console.error('Failed to send chat message:', error);
    throw error;
  }
};

export const uploadDocument = async (file, classificationTag = 'INTERNAL') => {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const response = await API.post(
      `/document/upload?classification_tag=${encodeURIComponent(classificationTag)}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error('Failed to upload document:', error);
    throw error;
  }
};

export const fetchAuditLogs = async () => {
  try {
    const response = await API.get('/audit/logs');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch audit logs:', error);
    return [];
  }
};

export const verifyAuditChain = async () => {
  try {
    const response = await API.get('/audit/verify');
    return response.data;
  } catch (error) {
    console.error('Failed to verify audit chain:', error);
    throw error;
  }
};

export const approveHitlAction = async (payload) => {
  try {
    const response = await API.post('/hitl/approve', payload);
    return response.data;
  } catch (error) {
    console.error('Failed to approve HITL action:', error);
    throw error;
  }
};

export const executeSandboxCode = async (code, timeoutSec = 5.0) => {
  try {
    const response = await API.post('/sandbox/execute', { code, timeout_sec: timeoutSec });
    return response.data;
  } catch (error) {
    console.error('Failed to execute sandbox code:', error);
    throw error;
  }
};

export const sendFeedback = async (payload) => {
  try {
    const response = await API.post('/chat/feedback', payload);
    return response.data;
  } catch (error) {
    console.error('Failed to send feedback:', error);
    throw error;
  }
};

export default API;
