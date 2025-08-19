import axios from 'axios';
import { ChatResponse, PlayerSuggestion, QueryValidation, SummaryStats } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const apiService = {
  // Chat endpoints
  async sendMessage(query: string, context?: any): Promise<ChatResponse> {
    const response = await api.post('/chat', { query, context });
    return response.data;
  },

  // Player search
  async searchPlayers(query: string, limit = 10): Promise<PlayerSuggestion[]> {
    const response = await api.get(`/players/search?query=${encodeURIComponent(query)}&limit=${limit}`);
    return response.data;
  },

  // Get all players
  async getAllPlayers(): Promise<string[]> {
    const response = await api.get('/players');
    return response.data;
  },

  // Get all teams
  async getAllTeams(): Promise<string[]> {
    const response = await api.get('/teams');
    return response.data;
  },

  // Get all venues
  async getAllVenues(): Promise<string[]> {
    const response = await api.get('/venues');
    return response.data;
  },

  // Get summary statistics
  async getSummaryStats(): Promise<SummaryStats> {
    const response = await api.get('/stats/summary');
    return response.data;
  },

  // Validate query
  async validateQuery(query: string): Promise<QueryValidation> {
    const response = await api.post('/query/validate', { query });
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<{ message: string }> {
    const response = await api.get('/');
    return response.data;
  }
};

// Add request/response interceptors for error handling
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data);
    
    if (error.response?.status === 500) {
      throw new Error('Server error. Please try again later.');
    } else if (error.response?.status === 400) {
      throw new Error(error.response.data.detail || 'Invalid request');
    } else if (error.code === 'ECONNABORTED') {
      throw new Error('Request timeout. Please try again.');
    } else if (!error.response) {
      throw new Error('Network error. Please check your connection.');
    }
    
    return Promise.reject(error);
  }
);

export default api;