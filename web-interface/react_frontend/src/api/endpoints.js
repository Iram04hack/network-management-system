/**
 * Définition des endpoints API pour AI Assistant
 * Basé sur les 11 endpoints validés du backend (score 8.9/10)
 * Conformité avec l'architecture hexagonale backend
 */

// Base URL des endpoints AI Assistant
const AI_BASE = '/api/ai';

/**
 * Endpoints pour les conversations
 */
export const CONVERSATIONS_ENDPOINTS = {
  // GET /api/ai/conversations/ - Liste des conversations avec pagination
  LIST: `${AI_BASE}/conversations/`,
  
  // POST /api/ai/conversations/ - Création d'une nouvelle conversation
  CREATE: `${AI_BASE}/conversations/`,
  
  // GET /api/ai/conversations/{id}/ - Détail d'une conversation
  DETAIL: (id) => `${AI_BASE}/conversations/${id}/`,
  
  // PUT /api/ai/conversations/{id}/ - Mise à jour d'une conversation
  UPDATE: (id) => `${AI_BASE}/conversations/${id}/`,
  
  // DELETE /api/ai/conversations/{id}/ - Suppression d'une conversation
  DELETE: (id) => `${AI_BASE}/conversations/${id}/`,
  
  // GET /api/ai/conversations/{id}/messages/ - Messages d'une conversation
  MESSAGES: (id) => `${AI_BASE}/conversations/${id}/messages/`,
  
  // POST /api/ai/conversations/{id}/messages/ - Nouveau message dans une conversation
  SEND_MESSAGE: (id) => `${AI_BASE}/conversations/${id}/messages/`,
};

/**
 * Endpoints pour les messages
 */
export const MESSAGES_ENDPOINTS = {
  // GET /api/ai/messages/ - Liste globale des messages
  LIST: `${AI_BASE}/messages/`,
  
  // POST /api/ai/messages/ - Création d'un message (usage avancé)
  CREATE: `${AI_BASE}/messages/`,
  
  // GET /api/ai/messages/{id}/ - Détail d'un message spécifique
  DETAIL: (id) => `${AI_BASE}/messages/${id}/`,
};

/**
 * Endpoints pour les documents
 */
export const DOCUMENTS_ENDPOINTS = {
  // GET /api/ai/documents/ - Liste des documents avec pagination
  LIST: `${AI_BASE}/documents/`,
  
  // POST /api/ai/documents/ - Upload d'un nouveau document
  UPLOAD: `${AI_BASE}/documents/`,
  
  // GET /api/ai/documents/search/ - Recherche dans les documents
  SEARCH: `${AI_BASE}/documents/search/`,
  
  // GET /api/ai/documents/{id}/ - Détail d'un document
  DETAIL: (id) => `${AI_BASE}/documents/${id}/`,
  
  // PUT /api/ai/documents/{id}/ - Mise à jour d'un document
  UPDATE: (id) => `${AI_BASE}/documents/${id}/`,
  
  // DELETE /api/ai/documents/{id}/ - Suppression d'un document
  DELETE: (id) => `${AI_BASE}/documents/${id}/`,
};

/**
 * Endpoints pour les commandes
 */
export const COMMANDS_ENDPOINTS = {
  // POST /api/ai/commands/ - Exécution d'une commande AI
  EXECUTE: `${AI_BASE}/commands/`,
  
  // GET /api/ai/commands/ - Liste des commandes disponibles (si implémenté)
  LIST: `${AI_BASE}/commands/`,
};

/**
 * Endpoints pour la recherche globale
 */
export const SEARCH_ENDPOINTS = {
  // GET /api/ai/search/ - Recherche globale dans l'AI Assistant
  GLOBAL: `${AI_BASE}/search/`,
};

/**
 * Endpoints pour l'analyse réseau
 */
export const NETWORK_ENDPOINTS = {
  // POST /api/ai/network-analysis/ - Analyse réseau par AI
  ANALYZE: `${AI_BASE}/network-analysis/`,
};

/**
 * Tous les endpoints regroupés pour validation
 */
export const ALL_ENDPOINTS = {
  CONVERSATIONS: CONVERSATIONS_ENDPOINTS,
  MESSAGES: MESSAGES_ENDPOINTS,
  DOCUMENTS: DOCUMENTS_ENDPOINTS,
  COMMANDS: COMMANDS_ENDPOINTS,
  SEARCH: SEARCH_ENDPOINTS,
  NETWORK: NETWORK_ENDPOINTS,
};

/**
 * Paramètres de requête standards
 */
export const QUERY_PARAMS = {
  // Pagination
  PAGE: 'page',
  PAGE_SIZE: 'page_size',
  LIMIT: 'limit',
  OFFSET: 'offset',
  
  // Tri
  ORDERING: 'ordering',
  
  // Filtres
  SEARCH: 'search',
  USER: 'user',
  CREATED_AFTER: 'created_after',
  CREATED_BEFORE: 'created_before',
  
  // Spécifiques aux conversations
  TITLE: 'title',
  HAS_MESSAGES: 'has_messages',
  
  // Spécifiques aux messages
  ROLE: 'role',
  CONVERSATION: 'conversation',
  
  // Spécifiques aux documents
  CONTENT_TYPE: 'content_type',
  TAGS: 'tags',
  IS_ACTIVE: 'is_active',
  
  // Recherche
  QUERY: 'q',
  TYPE: 'type',
};

/**
 * Valeurs par défaut pour les paramètres
 */
export const DEFAULT_PARAMS = {
  PAGE_SIZE: 20,
  ORDERING: '-created_at', // Plus récent en premier
  SEARCH_LIMIT: 50,
};

/**
 * Headers spéciaux pour certaines requêtes
 */
export const SPECIAL_HEADERS = {
  // Pour les uploads de fichiers
  MULTIPART: {
    'Content-Type': 'multipart/form-data',
  },
  
  // Pour les requêtes de streaming (si implémenté)
  STREAMING: {
    'Accept': 'text/event-stream',
    'Cache-Control': 'no-cache',
  },
  
  // Pour les requêtes avec timeout étendu
  LONG_TIMEOUT: {
    'X-Request-Timeout': '60000',
  },
};

/**
 * Codes de statut HTTP attendus par endpoint
 */
export const EXPECTED_STATUS_CODES = {
  // Conversations
  LIST_CONVERSATIONS: [200],
  CREATE_CONVERSATION: [201],
  GET_CONVERSATION: [200],
  UPDATE_CONVERSATION: [200],
  DELETE_CONVERSATION: [204],
  
  // Messages
  LIST_MESSAGES: [200],
  SEND_MESSAGE: [201],
  GET_MESSAGE: [200],
  
  // Documents
  LIST_DOCUMENTS: [200],
  UPLOAD_DOCUMENT: [201],
  SEARCH_DOCUMENTS: [200],
  GET_DOCUMENT: [200],
  UPDATE_DOCUMENT: [200],
  DELETE_DOCUMENT: [204],
  
  // Commandes
  EXECUTE_COMMAND: [200, 201],
  
  // Recherche
  GLOBAL_SEARCH: [200],
  
  // Analyse réseau
  NETWORK_ANALYSIS: [200, 201],
};

/**
 * Validation des endpoints (pour tests)
 */
export const validateEndpoint = (endpoint) => {
  if (typeof endpoint === 'function') {
    // Endpoint avec paramètre (ex: DETAIL(id))
    return endpoint(1).startsWith('/api/ai/');
  }
  return endpoint.startsWith('/api/ai/');
};

/**
 * Helper pour construire des URLs avec paramètres
 */
export const buildUrl = (endpoint, params = {}) => {
  const url = new URL(endpoint, 'https://localhost:8000');
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      url.searchParams.append(key, value);
    }
  });
  
  return url.pathname + url.search;
};

/**
 * Validation de la structure des endpoints
 */
export const validateAllEndpoints = () => {
  const errors = [];
  
  // Validation des endpoints de conversations
  Object.entries(CONVERSATIONS_ENDPOINTS).forEach(([key, endpoint]) => {
    if (!validateEndpoint(endpoint)) {
      errors.push(`Invalid conversation endpoint: ${key}`);
    }
  });
  
  // Validation des autres endpoints
  [MESSAGES_ENDPOINTS, DOCUMENTS_ENDPOINTS, COMMANDS_ENDPOINTS, SEARCH_ENDPOINTS, NETWORK_ENDPOINTS]
    .forEach((endpointGroup, index) => {
      const groupNames = ['MESSAGES', 'DOCUMENTS', 'COMMANDS', 'SEARCH', 'NETWORK'];
      Object.entries(endpointGroup).forEach(([key, endpoint]) => {
        if (!validateEndpoint(endpoint)) {
          errors.push(`Invalid ${groupNames[index]} endpoint: ${key}`);
        }
      });
    });
  
  return {
    isValid: errors.length === 0,
    errors,
    totalEndpoints: Object.values(ALL_ENDPOINTS).reduce((total, group) => 
      total + Object.keys(group).length, 0
    ),
  };
};

// Export par défaut pour usage simple
export default ALL_ENDPOINTS;
