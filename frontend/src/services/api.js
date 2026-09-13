import axios from 'axios';

const API = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

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

export default API;
