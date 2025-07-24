/**
 * Service API Views - Intégration avec le module api_views backend
 * Gestion des vues agrégées du système et monitoring
 */

import apiClient from '../api/client.js';

/**
 * Base URLs pour le module api_views
 */
const API_VIEWS_BASE = '/api/views';

/**
 * Endpoints du module api_views
 */
export const API_VIEWS_ENDPOINTS = {
  // Dashboard et vues agrégées
  DASHBOARD_OVERVIEW: `${API_VIEWS_BASE}/dashboard/`,
  SYSTEM_OVERVIEW: `${API_VIEWS_BASE}/system/`,
  NETWORK_OVERVIEW: `${API_VIEWS_BASE}/network/`,
  
  // Découverte de topologie
  TOPOLOGY_DISCOVERY: `${API_VIEWS_BASE}/topology/discovery/`,
  TOPOLOGY_STATUS: (discoveryId) => `${API_VIEWS_BASE}/topology/discovery/${discoveryId}/status/`,
  TOPOLOGY_DATA: (networkId) => `${API_VIEWS_BASE}/topology/${networkId}/`,
  TOPOLOGY_SAVE: `${API_VIEWS_BASE}/topology/save/`,
  
  // Gestion d'équipements
  DEVICES_LIST: `${API_VIEWS_BASE}/devices/`,
  DEVICE_DETAIL: (deviceId) => `${API_VIEWS_BASE}/devices/${deviceId}/`,
  DEVICE_CONFIG: (deviceId) => `${API_VIEWS_BASE}/devices/${deviceId}/config/`,
  DEVICE_STATUS: (deviceId) => `${API_VIEWS_BASE}/devices/${deviceId}/status/`,
  DEVICE_INTERFACES: (deviceId) => `${API_VIEWS_BASE}/devices/${deviceId}/interfaces/`,
  
  // Recherche avancée
  SEARCH_GLOBAL: `${API_VIEWS_BASE}/search/`,
  SEARCH_DEVICES: `${API_VIEWS_BASE}/search/devices/`,
  SEARCH_ALERTS: `${API_VIEWS_BASE}/search/alerts/`,
  SEARCH_RESOURCES: `${API_VIEWS_BASE}/search/resources/`,
  
  // Monitoring Enterprise
  MONITORING_METRICS: `${API_VIEWS_BASE}/monitoring/metrics/`,
  MONITORING_ALERTS: `${API_VIEWS_BASE}/monitoring/alerts/`,
  MONITORING_HEALTH: `${API_VIEWS_BASE}/monitoring/health/`,
  PROMETHEUS_DATA: `${API_VIEWS_BASE}/monitoring/prometheus/`,
  GRAFANA_DASHBOARDS: `${API_VIEWS_BASE}/monitoring/grafana/`,
  
  // Sécurité avancée
  SECURITY_OVERVIEW: `${API_VIEWS_BASE}/security/`,
  SECURITY_ALERTS: `${API_VIEWS_BASE}/security/alerts/`,
  FAIL2BAN_STATUS: `${API_VIEWS_BASE}/security/fail2ban/`,
  SURICATA_LOGS: `${API_VIEWS_BASE}/security/suricata/`,
  IDS_EVENTS: `${API_VIEWS_BASE}/security/ids/`,
};

/**
 * Service principal pour les API Views
 */
class APIViewsService {
  constructor() {
    this.apiClient = apiClient;
    
    // Cache pour les données fréquemment utilisées
    this.cache = new Map();
    this.cacheTimeout = 30000; // 30 secondes
    
    // Statistiques du service
    this.stats = {
      totalRequests: 0,
      cacheHits: 0,
      cacheMisses: 0,
      lastRequestTime: null,
    };
  }

  /**
   * ===========================================
   * DASHBOARD ET VUES AGRÉGÉES
   * ===========================================
   */

  /**
   * Récupère la vue d'ensemble du dashboard
   * GET /api/views/dashboard/
   */
  async getDashboardOverview(params = {}) {
    const cacheKey = `dashboard_overview_${JSON.stringify(params)}`;
    
    // Vérifier le cache
    if (this.isInCache(cacheKey)) {
      this.stats.cacheHits++;
      return this.getFromCache(cacheKey);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.DASHBOARD_OVERVIEW, { params });
      
      this.updateStats(startTime, true);
      
      const result = {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          refreshTime: this.cacheTimeout / 1000,
          devicesTotal: response.data.devices?.total || 0,
          alertsTotal: response.data.alerts?.total || 0,
          systemHealth: response.data.system?.overall_status || 'unknown'
        }
      };
      
      // Mettre en cache
      this.setCache(cacheKey, result);
      this.stats.cacheMisses++;
      
      return result;
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getDashboardOverview', { params });
    }
  }

  /**
   * Récupère la vue d'ensemble du système
   * GET /api/views/system/
   */
  async getSystemOverview(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.SYSTEM_OVERVIEW, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          cpuUsage: response.data.cpu?.usage_percent || 0,
          memoryUsage: response.data.memory?.usage_percent || 0,
          diskUsage: response.data.disk?.usage_percent || 0,
          servicesCount: response.data.services?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getSystemOverview', { params });
    }
  }

  /**
   * Récupère la vue d'ensemble du réseau
   * GET /api/views/network/
   */
  async getNetworkOverview(params = {}) {
    const cacheKey = `network_overview_${JSON.stringify(params)}`;
    
    if (this.isInCache(cacheKey)) {
      this.stats.cacheHits++;
      return this.getFromCache(cacheKey);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.NETWORK_OVERVIEW, { params });
      
      this.updateStats(startTime, true);
      
      const result = {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          devicesCount: response.data.devices?.length || 0,
          topologyNodes: response.data.topology?.nodes?.length || 0,
          topologyEdges: response.data.topology?.edges?.length || 0,
          networkHealth: response.data.health?.status || 'unknown'
        }
      };
      
      this.setCache(cacheKey, result);
      this.stats.cacheMisses++;
      
      return result;
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getNetworkOverview', { params });
    }
  }

  /**
   * ===========================================
   * DÉCOUVERTE DE TOPOLOGIE
   * ===========================================
   */

  /**
   * Lance une découverte de topologie
   * POST /api/views/topology/discovery/
   */
  async startTopologyDiscovery(discoveryParams) {
    const requiredFields = ['network_id'];
    const validation = this.validateRequiredFields(discoveryParams, requiredFields);
    if (!validation.isValid) {
      return this.createValidationError('startTopologyDiscovery', validation.missingFields);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        API_VIEWS_ENDPOINTS.TOPOLOGY_DISCOVERY,
        discoveryParams
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        discoveryId: response.data.discovery_id,
        metadata: {
          timestamp: new Date().toISOString(),
          networkId: discoveryParams.network_id,
          estimatedTime: response.data.estimated_time
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'startTopologyDiscovery', { discoveryParams });
    }
  }

  /**
   * Récupère le statut d'une découverte
   * GET /api/views/topology/discovery/{id}/status/
   */
  async getTopologyDiscoveryStatus(discoveryId) {
    if (!discoveryId) {
      return this.createValidationError('getTopologyDiscoveryStatus', ['discoveryId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.TOPOLOGY_STATUS(discoveryId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        discoveryId,
        metadata: {
          timestamp: new Date().toISOString(),
          progress: response.data.progress || 0,
          status: response.data.status,
          devicesFound: response.data.devices_found || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getTopologyDiscoveryStatus', { discoveryId });
    }
  }

  /**
   * Récupère les données de topologie
   * GET /api/views/topology/{network_id}/
   */
  async getTopologyData(networkId, params = {}) {
    if (!networkId) {
      return this.createValidationError('getTopologyData', ['networkId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.TOPOLOGY_DATA(networkId), { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        networkId,
        metadata: {
          timestamp: new Date().toISOString(),
          nodesCount: response.data.nodes?.length || 0,
          edgesCount: response.data.edges?.length || 0,
          lastUpdate: response.data.metadata?.last_update
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getTopologyData', { networkId, params });
    }
  }

  /**
   * ===========================================
   * GESTION D'ÉQUIPEMENTS
   * ===========================================
   */

  /**
   * Récupère la liste des équipements
   * GET /api/views/devices/
   */
  async getDevices(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.DEVICES_LIST, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalDevices: response.data.count || response.data.length || 0,
          onlineDevices: response.data.results ? 
            response.data.results.filter(d => d.status === 'online').length : 0,
          deviceTypes: response.data.results ? 
            [...new Set(response.data.results.map(d => d.device_type))] : []
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getDevices', { params });
    }
  }

  /**
   * Récupère les détails d'un équipement
   * GET /api/views/devices/{id}/
   */
  async getDevice(deviceId) {
    if (!deviceId) {
      return this.createValidationError('getDevice', ['deviceId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.DEVICE_DETAIL(deviceId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        deviceId,
        metadata: {
          timestamp: new Date().toISOString(),
          deviceType: response.data.device_type,
          status: response.data.status,
          interfacesCount: response.data.interfaces?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getDevice', { deviceId });
    }
  }

  /**
   * ===========================================
   * RECHERCHE AVANCÉE
   * ===========================================
   */

  /**
   * Recherche globale dans le système
   * GET /api/views/search/
   */
  async globalSearch(query, params = {}) {
    if (!query || query.trim() === '') {
      return this.createValidationError('globalSearch', ['query']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.SEARCH_GLOBAL, {
        params: { q: query.trim(), ...params }
      });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        query: query.trim(),
        metadata: {
          timestamp: new Date().toISOString(),
          resultsCount: response.data.total || response.data.results?.length || 0,
          searchTypes: params.type ? [params.type] : ['devices', 'alerts', 'resources'],
          searchTime: Date.now() - startTime
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'globalSearch', { query, params });
    }
  }

  /**
   * ===========================================
   * MONITORING ENTERPRISE
   * ===========================================
   */

  /**
   * Récupère les métriques de monitoring
   * GET /api/views/monitoring/metrics/
   */
  async getMonitoringMetrics(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.MONITORING_METRICS, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          metricsCount: response.data.metrics?.length || 0,
          timeRange: params.time_range || '1h',
          sourceSystem: 'prometheus'
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getMonitoringMetrics', { params });
    }
  }

  /**
   * Récupère les alertes de monitoring
   * GET /api/views/monitoring/alerts/
   */
  async getMonitoringAlerts(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(API_VIEWS_ENDPOINTS.MONITORING_ALERTS, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          alertsCount: response.data.length || response.data.results?.length || 0,
          criticalAlerts: response.data.filter ? 
            response.data.filter(a => a.severity === 'critical').length : 0,
          activeAlerts: response.data.filter ? 
            response.data.filter(a => a.status === 'active').length : 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getMonitoringAlerts', { params });
    }
  }

  /**
   * ===========================================
   * GESTION DU CACHE
   * ===========================================
   */

  isInCache(key) {
    const cached = this.cache.get(key);
    if (!cached) return false;
    
    const now = Date.now();
    if (now - cached.timestamp > this.cacheTimeout) {
      this.cache.delete(key);
      return false;
    }
    
    return true;
  }

  getFromCache(key) {
    return this.cache.get(key).data;
  }

  setCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
  }

  clearCache() {
    this.cache.clear();
  }

  /**
   * ===========================================
   * MÉTHODES UTILITAIRES
   * ===========================================
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

    // Classification des erreurs spécifiques aux vues
    if (error.response?.status === 404) {
      errorInfo.error.type = 'RESOURCE_NOT_FOUND';
      errorInfo.error.userMessage = 'Ressource demandée non trouvée.';
    } else if (error.response?.status === 503) {
      errorInfo.error.type = 'SERVICE_UNAVAILABLE';
      errorInfo.error.userMessage = 'Service temporairement indisponible.';
    } else if (error.response?.status >= 500) {
      errorInfo.error.type = 'SERVER_ERROR';
      errorInfo.error.userMessage = 'Erreur serveur lors de la récupération des données.';
    } else {
      errorInfo.error.type = 'UNKNOWN_ERROR';
      errorInfo.error.userMessage = 'Erreur inattendue lors de la requête.';
    }

    console.error(`[API Views Service Error] ${operation}:`, errorInfo);
    return errorInfo;
  }

  validateRequiredFields(data, requiredFields) {
    const missingFields = requiredFields.filter(field =>
      !data || data[field] === null || data[field] === undefined || data[field] === ''
    );

    return {
      isValid: missingFields.length === 0,
      missingFields
    };
  }

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

  updateStats(startTime, success) {
    this.stats.totalRequests++;
    this.stats.lastRequestTime = new Date().toISOString();
  }

  getStats() {
    return {
      ...this.stats,
      cacheHitRate: this.stats.totalRequests > 0
        ? Math.round((this.stats.cacheHits / this.stats.totalRequests) * 100)
        : 0,
      cacheSize: this.cache.size
    };
  }
}

// Instance singleton du service
const apiViewsService = new APIViewsService();

export default apiViewsService;