/**
 * Configuration client API pour NMS
 * Support multiple authentifications + gestion d'erreurs
 * Monitoring APIs intégrées
 */

import axios from 'axios';
import authService from '../utils/auth.js';

// Configuration de base
const API_CONFIG = {
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 15000, // Augmenté pour les APIs monitoring
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
};

// Credentials fallback pour Basic Auth
const FALLBACK_CREDENTIALS = {
  username: import.meta.env.VITE_API_USERNAME || 'admin@hybrido.com',
  password: import.meta.env.VITE_API_PASSWORD || 'hybrido2025',
};

// Création de l'instance Axios
const apiClient = axios.create(API_CONFIG);

// Compteurs pour monitoring
let requestCount = 0;
let errorCount = 0;
let retryCount = 0;

/**
 * Intercepteur de requête - Authentification intelligente
 */
apiClient.interceptors.request.use(
  (config) => {
    requestCount++;
    
    // Tentative d'authentification avec token Bearer d'abord
    const authHeaders = authService.getAuthHeaders();
    if (authHeaders.Authorization) {
      config.headers.Authorization = authHeaders.Authorization;
    } else {
      // Fallback sur Basic Auth pour compatibilité
      const credentials = btoa(`${FALLBACK_CREDENTIALS.username}:${FALLBACK_CREDENTIALS.password}`);
      config.headers.Authorization = `Basic ${credentials}`;
    }
    
    // Ajout d'un ID unique pour traçabilité
    config.metadata = {
      requestId: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      startTime: Date.now(),
    };
    
    // Log pour debugging (dev uniquement)
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
        requestId: config.metadata.requestId,
        params: config.params,
        data: config.data,
      });
    }
    
    return config;
  },
  (error) => {
    errorCount++;
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

/**
 * Intercepteur de réponse - Gestion d'erreurs et monitoring
 */
apiClient.interceptors.response.use(
  (response) => {
    // Calcul du temps de réponse
    const responseTime = Date.now() - response.config.metadata.startTime;
    
    // Log pour debugging (dev uniquement)
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.status} ${response.config.url}`, {
        requestId: response.config.metadata.requestId,
        responseTime: `${responseTime}ms`,
        dataSize: JSON.stringify(response.data).length,
      });
    }
    
    // Ajout des métadonnées de réponse
    response.metadata = {
      ...response.config.metadata,
      responseTime,
      timestamp: new Date().toISOString(),
    };
    
    return response;
  },
  async (error) => {
    errorCount++;
    const originalRequest = error.config;
    
    // Calcul du temps de réponse même en cas d'erreur
    const responseTime = originalRequest?.metadata?.startTime 
      ? Date.now() - originalRequest.metadata.startTime 
      : 0;
    
    // Enrichissement de l'erreur avec métadonnées
    error.metadata = {
      requestId: originalRequest?.metadata?.requestId || 'unknown',
      responseTime,
      timestamp: new Date().toISOString(),
      retryAttempt: originalRequest?._retryCount || 0,
    };
    
    // Gestion des erreurs spécifiques
    if (error.response) {
      // Erreur avec réponse du serveur
      const { status, statusText, data } = error.response;
      
      switch (status) {
        case 401:
          console.error('[API Auth Error] Invalid credentials or session expired');
          // Possibilité d'ajouter une redirection vers login
          break;
          
        case 403:
          console.error('[API Permission Error] Access forbidden');
          break;
          
        case 404:
          console.error('[API Not Found] Resource not found:', originalRequest?.url);
          break;
          
        case 429:
          console.warn('[API Rate Limit] Too many requests');
          break;
          
        case 500:
        case 502:
        case 503:
        case 504:
          console.error('[API Server Error]', { status, statusText });
          
          // Retry automatique pour erreurs serveur
          if (shouldRetry(originalRequest, error)) {
            return retryRequest(originalRequest);
          }
          break;
          
        default:
          console.error('[API Error]', { status, statusText, data });
      }
    } else if (error.request) {
      // Erreur réseau (pas de réponse)
      console.error('[API Network Error] No response received:', error.message);
      
      // Retry pour erreurs réseau
      if (shouldRetry(originalRequest, error)) {
        return retryRequest(originalRequest);
      }
    } else {
      // Erreur de configuration
      console.error('[API Config Error]', error.message);
    }
    
    // Log détaillé pour debugging
    if (import.meta.env.DEV) {
      console.error('[API Error Details]', {
        requestId: error.metadata.requestId,
        url: originalRequest?.url,
        method: originalRequest?.method,
        responseTime: `${responseTime}ms`,
        error: error.message,
        status: error.response?.status,
        data: error.response?.data,
      });
    }
    
    return Promise.reject(error);
  }
);

/**
 * Détermine si une requête doit être retentée
 */
function shouldRetry(config, error) {
  // Pas de retry si déjà tenté 3 fois
  if (config._retryCount >= 3) {
    return false;
  }
  
  // Retry uniquement pour certaines erreurs
  const retryableErrors = [
    'ECONNRESET',
    'ENOTFOUND',
    'ECONNABORTED',
    'ETIMEDOUT',
    'ERR_NETWORK',
  ];
  
  const retryableStatuses = [500, 502, 503, 504];
  
  return (
    retryableErrors.includes(error.code) ||
    retryableStatuses.includes(error.response?.status) ||
    error.message.includes('timeout')
  );
}

/**
 * Retry d'une requête avec backoff exponentiel
 */
async function retryRequest(config) {
  config._retryCount = (config._retryCount || 0) + 1;
  retryCount++;
  
  const delay = Math.pow(2, config._retryCount) * 1000; // 2s, 4s, 8s
  
  console.log(`[API Retry] Attempt ${config._retryCount}/3 in ${delay}ms for ${config.url}`);
  
  await new Promise(resolve => setTimeout(resolve, delay));
  
  return apiClient(config);
}

/**
 * Utilitaires pour monitoring et debugging
 */
export const apiStats = {
  getStats: () => ({
    totalRequests: requestCount,
    totalErrors: errorCount,
    totalRetries: retryCount,
    errorRate: requestCount > 0 ? (errorCount / requestCount * 100).toFixed(2) + '%' : '0%',
    timestamp: new Date().toISOString(),
  }),
  
  reset: () => {
    requestCount = 0;
    errorCount = 0;
    retryCount = 0;
  },
};

/**
 * Helper pour créer des requêtes avec timeout personnalisé
 */
export const createRequestWithTimeout = (timeout) => {
  return axios.create({
    ...API_CONFIG,
    timeout,
  });
};

/**
 * Helper pour upload de fichiers avec progress
 */
export const createUploadClient = () => {
  return axios.create({
    ...API_CONFIG,
    timeout: 60000, // 60s pour uploads
    headers: {
      ...API_CONFIG.headers,
      'Content-Type': 'multipart/form-data',
    },
  });
};

// Configuration des intercepteurs pour le client d'upload
const uploadClient = createUploadClient();
uploadClient.interceptors.request.use(apiClient.interceptors.request.handlers[0].fulfilled);
uploadClient.interceptors.response.use(
  apiClient.interceptors.response.handlers[0].fulfilled,
  apiClient.interceptors.response.handlers[0].rejected
);

export { uploadClient };
export default apiClient;
