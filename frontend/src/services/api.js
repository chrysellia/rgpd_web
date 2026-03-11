import axios from 'axios';

const API_URL = 'http://localhost:8001';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' }
});

// Injecte le token JWT automatiquement
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Redirige vers login si token expiré
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authService = {
  login: (email, password) => {
    const formData = new FormData();
    formData.append('username', email);
    formData.append('password', password);
    return api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  register: (email, password) =>
    api.post('/auth/register', { email, password }),

  forgotPassword: (email) =>
    api.post('/auth/forgot-password', { email }),

  resetPassword: (token, newPassword) =>
    api.post('/auth/reset-password', {
      token,
      new_password: newPassword
    }),
};

//Ajout d'historique des conversations et de domaine pour la RGPD
export const rgpdService = {
  chat: (question, historique = [], domaine = 'general') =>
    api.post('/rgpd/chat', { question, historique, domaine }),

  chatWithFile: (question, domaine, file) => {
    const formData = new FormData();
    formData.append('question', question);
    formData.append('domaine', domaine);
    formData.append('file', file);
    return api.post('/rgpd/chat-with-file', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },

  getHistorique: () =>
    api.get('/rgpd/historique'),

  analyserTraitement: (traitement) =>
    api.post('/rgpd/analyser-traitement', traitement),

  status: () =>
    api.get('/rgpd/status'),
};

export default api;