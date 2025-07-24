/**
 * Service API Clients - Intégration avec le module api_clients backend
 * Gestion des 8 clients API externes (GNS3, SNMP, Prometheus, etc.)
 */

import apiClient from '../api/client.js';

/**
 * Base URLs pour le module api_clients
 */
const API_CLIENTS_BASE = '/api/clients';

/**
 * Endpoints du module api_clients
 */
export const API_CLIENTS_ENDPOINTS = {
  // Gestion des clients API
  LIST_CLIENTS: `${API_CLIENTS_BASE}/`,
  CLIENT_DETAIL: (clientId) => `${API_CLIENTS_BASE}/${clientId}/`,
  CLIENT_STATUS: (clientId) => `${API_CLIENTS_BASE}/${clientId}/status/`,
  CLIENT_TEST: (clientId) => `${API_CLIENTS_BASE}/${clientId}/test/`,
  CLIENT_CONFIG: (clientId) => `${API_CLIENTS_BASE}/${clientId}/config/`,
  
  // Clients spécialisés
  GNS3_CLIENT: `${API_CLIENTS_BASE}/gns3/`,
  SNMP_CLIENT: `${API_CLIENTS_BASE}/snmp/`,
  PROMETHEUS_CLIENT: `${API_CLIENTS_BASE}/prometheus/`,
  GRAFANA_CLIENT: `${API_CLIENTS_BASE}/grafana/`,
  ELASTICSEARCH_CLIENT: `${API_CLIENTS_BASE}/elasticsearch/`,
  NETFLOW_CLIENT: `${API_CLIENTS_BASE}/netflow/`,
  HAPROXY_CLIENT: `${API_CLIENTS_BASE}/haproxy/`,
  FAIL2BAN_CLIENT: `${API_CLIENTS_BASE}/fail2ban/`,
  
  // Métriques et monitoring
  CLIENTS_HEALTH: `${API_CLIENTS_BASE}/health/`,
  CLIENTS_METRICS: `${API_CLIENTS_BASE}/metrics/`,
  CLIENTS_LOGS: `${API_CLIENTS_BASE}/logs/`,
};

/**
 * Service principal pour la gestion des API Clients
 */
class APIClientsService {
  constructor() {
    this.apiClient = apiClient;
    
    // Statistiques du service
    this.stats = {
      totalRequests: 0,
      successfulRequests: 0,
      failedRequests: 0,
      lastRequestTime: null,
    };
  }

  /**
   * ===========================================
   * GESTION GÉNÉRALE DES CLIENTS API
   * ===========================================
   */

  /**
   * Récupère la liste de tous les clients API
   * GET /api/clients/
   */
  async getClients(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_CLIENTS_ENDPOINTS.LIST_CLIENTS, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalClients: response.data.length,
          activeClients: response.data.filter(client => client.is_active).length,
          clientTypes: [...new Set(response.data.map(client => client.client_type))]
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getClients', { params });
    }
  }

  /**
   * Récupère les détails d'un client spécifique
   * GET /api/clients/{id}/
   */
  async getClient(clientId) {
    if (!clientId) {
      return this.createValidationError('getClient', ['clientId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_CLIENTS_ENDPOINTS.CLIENT_DETAIL(clientId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          clientId,
          clientType: response.data.client_type
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getClient', { clientId });
    }
  }

  /**
   * Vérifie le statut d'un client API
   * GET /api/clients/{id}/status/
   */
  async getClientStatus(clientId) {
    if (!clientId) {
      return this.createValidationError('getClientStatus', ['clientId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_CLIENTS_ENDPOINTS.CLIENT_STATUS(clientId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        clientId,
        metadata: {
          timestamp: new Date().toISOString(),
          isHealthy: response.data.status === 'healthy',
          responseTime: response.data.response_time
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getClientStatus', { clientId });
    }
  }

  /**
   * Teste la connexion d'un client API
   * POST /api/clients/{id}/test/
   */
  async testClient(clientId, testParams = {}) {
    if (!clientId) {
      return this.createValidationError('testClient', ['clientId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        API_CLIENTS_ENDPOINTS.CLIENT_TEST(clientId),
        testParams
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        clientId,
        metadata: {
          timestamp: new Date().toISOString(),
          testPassed: response.data.success,
          testDuration: response.data.duration
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'testClient', { clientId, testParams });
    }
  }

  /**
   * Met à jour la configuration d'un client
   * PUT /api/clients/{id}/config/
   */
  async updateClientConfig(clientId, configData) {
    if (!clientId) {
      return this.createValidationError('updateClientConfig', ['clientId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.put(
        API_CLIENTS_ENDPOINTS.CLIENT_CONFIG(clientId),
        configData
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        clientId,
        metadata: {
          timestamp: new Date().toISOString(),
          configUpdated: true
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'updateClientConfig', { clientId, configData });
    }
  }

  /**
   * ===========================================
   * CLIENTS SPÉCIALISÉS
   * ===========================================
   */

  /**
   * Gestion du client GNS3
   */
  async getGNS3Client(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_CLIENTS_ENDPOINTS.GNS3_CLIENT, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        clientType: 'gns3',
        metadata: {
          timestamp: new Date().toISOString(),
          serversCount: response.data.servers?.length || 0,
          projectsCount: response.data.projects?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getGNS3Client', { params });
    }
  }

  /**
   * Gestion du client SNMP
   */
  async getSNMPClient(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_CLIENTS_ENDPOINTS.SNMP_CLIENT, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        clientType: 'snmp',
        metadata: {
          timestamp: new Date().toISOString(),
          devicesCount: response.data.monitored_devices?.length || 0,
          communityStrings: response.data.communities?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getSNMPClient', { params });
    }
  }

  /**
   * Gestion du client Prometheus
   */
  async getPrometheusClient(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_CLIENTS_ENDPOINTS.PROMETHEUS_CLIENT, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        clientType: 'prometheus',
        metadata: {
          timestamp: new Date().toISOString(),
          metricsCount: response.data.metrics?.length || 0,
          targetsCount: response.data.targets?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getPrometheusClient', { params });
    }
  }

  /**
   * ===========================================
   * MONITORING ET SANTÉ DES CLIENTS
   * ===========================================
   */

  /**
   * Récupère la santé globale de tous les clients
   * GET /api/clients/health/
   */
  async getClientsHealth() {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_CLIENTS_ENDPOINTS.CLIENTS_HEALTH);
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          overallStatus: response.data.overall_status,
          healthyClients: response.data.healthy_count,
          totalClients: response.data.total_count,
          healthPercentage: response.data.health_percentage
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getClientsHealth');
    }
  }

  /**
   * Récupère les métriques de performance des clients
   * GET /api/clients/metrics/
   */
  async getClientsMetrics(timeRange = '1h') {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_CLIENTS_ENDPOINTS.CLIENTS_METRICS, {
        params: { time_range: timeRange }
      });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        timeRange,
        metadata: {
          timestamp: new Date().toISOString(),
          metricsCollected: response.data.metrics_count,
          averageResponseTime: response.data.avg_response_time
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getClientsMetrics', { timeRange });
    }
  }

  /**
   * ===========================================
   * MÉTHODES UTILITAIRES
   * ===========================================
   */

  /**
   * Gestion centralisée des erreurs
   */
  handleError(error, operation, context = {}) {
    const errorInfo = {
      success: false,
      operation,
      timestamp: new Date().toISOString(),
      context,
      error: {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        code: error.code
      }
    };

    // Classification des erreurs
    if (error.response?.status === 404) {
      errorInfo.error.type = 'CLIENT_NOT_FOUND';
      errorInfo.error.userMessage = 'Client API non trouvé.';
    } else if (error.response?.status === 503) {
      errorInfo.error.type = 'CLIENT_UNAVAILABLE';
      errorInfo.error.userMessage = 'Service client temporairement indisponible.';
    } else if (error.response?.status >= 500) {
      errorInfo.error.type = 'SERVER_ERROR';
      errorInfo.error.userMessage = 'Erreur serveur lors de la communication avec le client API.';
    } else {
      errorInfo.error.type = 'UNKNOWN_ERROR';
      errorInfo.error.userMessage = 'Erreur inattendue avec le client API.';
    }

    console.error(`[API Clients Service Error] ${operation}:`, errorInfo);
    return errorInfo;
  }

  /**
   * Validation des champs requis
   */
  validateRequiredFields(data, requiredFields) {
    const missingFields = requiredFields.filter(field =>
      !data || data[field] === null || data[field] === undefined || data[field] === ''
    );

    return {
      isValid: missingFields.length === 0,
      missingFields
    };
  }

  /**
   * Création d'une erreur de validation
   */
  createValidationError(operation, missingFields) {
    return {
      success: false,
      operation,
      timestamp: new Date().toISOString(),
      error: {
        type: 'VALIDATION_ERROR',
        message: `Missing required fields: ${missingFields.join(', ')}`,
        userMessage: 'Veuillez fournir tous les champs obligatoires.',
        missingFields,
        status: 400
      }
    };
  }

  /**
   * Mise à jour des statistiques du service
   */
  updateStats(startTime, success) {
    this.stats.totalRequests++;
    this.stats.lastRequestTime = new Date().toISOString();

    if (success) {
      this.stats.successfulRequests++;
    } else {
      this.stats.failedRequests++;
    }
  }

  /**
   * Récupération des statistiques du service
   */
  getStats() {
    return {
      ...this.stats,
      successRate: this.stats.totalRequests > 0
        ? Math.round((this.stats.successfulRequests / this.stats.totalRequests) * 100)
        : 0,
      errorRate: this.stats.totalRequests > 0
        ? Math.round((this.stats.failedRequests / this.stats.totalRequests) * 100)
        : 0
    };
  }
}

// Instance singleton du service
const apiClientsService = new APIClientsService();

export default apiClientsService;