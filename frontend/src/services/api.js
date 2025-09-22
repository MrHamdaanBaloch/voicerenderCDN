import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to add the JWT token to headers
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for global error handling (e.g., token expiration)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            // Token expired or invalid, redirect to login
            localStorage.removeItem('access_token');
            // You might want to use a more robust way to redirect, e.g., a global context or history object
            window.location.href = '/login'; 
        }
        return Promise.reject(error);
    }
);

const auth = {
    register: (userData) => api.post('/register', userData),
    login: (email, password) => api.post('/token', new URLSearchParams({ username: email, password: password }), {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    }),
    getMe: () => api.get('/users/me'),
};

const agents = {
    getAgents: () => api.get('/agents'),
    getAgent: (agentId) => api.get(`/agents/${agentId}`),
    createAgent: (agentData) => api.post('/agents', agentData),
    updateAgent: (agentId, agentData) => api.put(`/agents/${agentId}`, agentData),
    deleteAgent: (agentId) => api.delete(`/agents/${agentId}`),
};

const calls = {
    getCalls: () => api.get('/calls'),
    getCallDetails: (callId) => api.get(`/calls/${callId}`),
};

export default {
    auth,
    agents,
    calls,
};
