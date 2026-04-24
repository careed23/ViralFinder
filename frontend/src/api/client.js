import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  getHealth: () => client.get('/api/health'),
  
  startScan: (config) => client.post('/api/scan/start', config),
  
  getScanStatus: (jobId) => client.get(`/api/scan/status/${jobId}`),
  
  getScanResults: (jobId, params) => client.get(`/api/scan/results/${jobId}`, { params }),
  
  exportResults: (jobId) => `${API_BASE_URL}/api/scan/results/${jobId}/export`,
  
  getDomainDetail: (domain) => client.get(`/api/domain/${domain}/detail`),
};

export default api;
