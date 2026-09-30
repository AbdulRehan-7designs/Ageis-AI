import axios from 'axios';

const API = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

const notifyUnauthorized = () => {
  localStorage.removeItem('aegis_jwt_token');
  localStorage.removeItem('aegis_user');
  window.dispatchEvent(new CustomEvent('aegis:session-expired'));
};

const notifyForbidden = (detail = 'Access denied for this operation.') => {
  window.dispatchEvent(new CustomEvent('aegis:access-denied', { detail }));
};

API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) notifyUnauthorized();
    if (error.response?.status === 403) notifyForbidden(error.response.data?.detail);
    return Promise.reject(error);
  },
);

API.interceptors.request.use((config) => {
  const token = localStorage.getItem('aegis_jwt_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (typeof FormData !== 'undefined' && config.data instanceof FormData) {
    delete config.headers['Content-Type'];
  }
  return config;
});

export const loginUser = async (username, password) => {
  try {
    const response = await API.post('/auth/login', {
      username,
      password,
    });
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

export const fetchModelCatalog = async () => {
  const response = await API.get('/models');
  return response.data;
};

export const createConversation = async (title = 'New conversation') => {
  const response = await API.post('/conversations', { title });
  return response.data;
};

export const fetchConversations = async () => {
  const response = await API.get('/conversations');
  return response.data;
};

export const fetchConversation = async (conversationId) => {
  const response = await API.get(`/conversations/${encodeURIComponent(conversationId)}`);
  return response.data;
};

export const fetchEgressStatus = async () => {
  try {
    const response = await API.get('/egress');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch egress status:', error);
    return null;
  }
};

export const fetchHealthStatus = async () => {
  const response = await API.get('/health');
  return response.data;
};

export const sendChatMessage = async (payload = {}) => {
  try {
    const normalized = {
      ...payload,
      message: payload.message ?? payload.query ?? '',
      model_override: payload.model_override ?? payload.model ?? undefined,
    };
    delete normalized.query;
    delete normalized.model;

    const response = await API.post('/chat', normalized);
    return response.data;
  } catch (error) {
    console.error('Failed to send chat message:', error);
    throw error;
  }
};

export const sendChatMessageStream = async (payload, onChunk, onComplete, onStatus, signal) => {
  try {
    const normalized = {
      ...payload,
      message: payload.message ?? payload.query ?? '',
      model_override: payload.model_override ?? payload.model ?? undefined,
    };
    delete normalized.query;
    delete normalized.model;

    const token = localStorage.getItem('aegis_jwt_token');
    const response = await fetch('/api/v1/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      signal,
      body: JSON.stringify(normalized),
    });

    if (!response.ok) {
      if (response.status === 401) notifyUnauthorized();
      if (response.status === 403) notifyForbidden();
      throw new Error(`Chat stream failed: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('ReadableStream not supported in this browser');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const messages = buffer.split('\n\n');
      buffer = messages.pop() || '';

      for (const message of messages) {
        const trimmed = message.trim();
        if (!trimmed.startsWith('data:')) continue;
        const payloadText = trimmed.slice(5).trim();
        if (!payloadText) continue;
        const event = JSON.parse(payloadText);
        if (event.type === 'status') {
          if (onStatus) onStatus(event.content || '');
        }
        if (event.type === 'chunk' && onChunk) onChunk(event.content || '');
        if (event.type === 'final' && onComplete) onComplete(event.result || null);
      }
    }

    if (buffer.trim().startsWith('data:')) {
      const finalPayload = buffer.trim().slice(5).trim();
      if (finalPayload) {
        const event = JSON.parse(finalPayload);
        if (event.type === 'final' && onComplete) onComplete(event.result || null);
      }
    }
  } catch (error) {
    console.error('Failed to stream chat message:', error);
    throw error;
  }
};

export const uploadDocument = async (file, classificationTag = 'INTERNAL') => {
  const batch = await uploadDocuments([file], classificationTag);
  return batch.documents[0];
};

export const uploadDocuments = async (files, classificationTag = 'INTERNAL') => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  const response = await API.post(
    `/document/upload-batch?classification_tag=${encodeURIComponent(classificationTag)}`,
    formData
  );
  return response.data;
};

export const fetchDocumentList = async () => {
  const response = await API.get('/document/list');
  return response.data?.documents || response.data?.items || [];
};

export const searchDocuments = async (query) => {
  const response = await API.get('/document/list', { params: { q: query } });
  return response.data?.documents || response.data?.items || [];
};

export const analyzeDocumentPage = async (documentId, page = 1, instruction = 'Describe the visible content without inventing engineering facts.') => {
  const response = await API.post(`/document/${encodeURIComponent(documentId)}/visual-analysis`, {
    page,
    instruction,
  });
  return response.data;
};

export const fetchAgentRuns = async () => {
  const response = await API.get('/agent-runs');
  return response.data || [];
};

export const getDocumentFileUrl = (storedFilename, docName) => {
  const params = new URLSearchParams();
  if (storedFilename) params.set('stored_filename', storedFilename);
  if (docName && !storedFilename) params.set('doc_name', docName);
  const query = params.toString();
  return query ? `/api/v1/document/file?${query}` : '/api/v1/document/file';
};

export const fetchAuditLogs = async () => {
  const response = await API.get('/audit/logs');
  return response.data?.logs || response.data?.events || response.data || [];
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

export const submitHitlDecision = async (payload) => {
  try {
    const response = await API.post('/hitl/decision', payload);
    return response.data;
  } catch (error) {
    console.error('Failed to submit HITL decision:', error);
    throw error;
  }
};

export const generateMaintenanceReport = async (payload) => {
  try {
    const response = await API.post('/reports/maintenance', payload);
    return response.data;
  } catch (error) {
    console.error('Failed to generate maintenance report:', error);
    throw error;
  }
};

export const generateReportArtifact = async (payload) => {
  const response = await API.post('/reports/generate', payload);
  return response.data;
};

export const approveReportArtifact = async (artifactId) => {
  const response = await API.post(`/reports/${encodeURIComponent(artifactId)}/approve`);
  return response.data;
};

export const reportArtifactUrl = (artifactId) => `/api/v1/reports/${encodeURIComponent(artifactId)}/download`;

export const executeSandboxCode = async (code, timeoutSec = 5.0, inputs = {}, purpose = 'engineering_calculation') => {
  try {
    const response = await API.post('/sandbox/execute', {
      code,
      timeout_sec: timeoutSec,
      inputs,
      purpose,
    });
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
