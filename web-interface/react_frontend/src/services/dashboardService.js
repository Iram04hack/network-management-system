/**
 * Service Dashboard - Intégration avec le module dashboard backend
 * Gestion des tableaux de bord personnalisés et WebSocket temps réel
 */

import apiClient from '../api/client.js';

/**
 * Base URLs pour le module dashboard
 */
const DASHBOARD_BASE = '/api/dashboard';

/**
 * Endpoints du module dashboard
 */
export const DASHBOARD_ENDPOINTS = {
  // CRUD Dashboard Configs
  CONFIGS: `${DASHBOARD_BASE}/configs/`,
  CONFIG_DETAIL: (configId) => `${DASHBOARD_BASE}/configs/${configId}/`,
  
  // CRUD Widgets
  WIDGETS: `${DASHBOARD_BASE}/widgets/`,
  WIDGET_DETAIL: (widgetId) => `${DASHBOARD_BASE}/widgets/${widgetId}/`,
  
  // CRUD Presets
  PRESETS: `${DASHBOARD_BASE}/presets/`,
  PRESET_DETAIL: (presetId) => `${DASHBOARD_BASE}/presets/${presetId}/`,
  
  // CRUD Custom Dashboards
  CUSTOM_DASHBOARDS: `${DASHBOARD_BASE}/custom/`,
  CUSTOM_DASHBOARD_DETAIL: (dashboardId) => `${DASHBOARD_BASE}/custom/${dashboardId}/`,
  
  // Data endpoints (lecture seule)
  DASHBOARD_DATA: `${DASHBOARD_BASE}/data/`,
  USER_CONFIG: `${DASHBOARD_BASE}/config/`,
  NETWORK_OVERVIEW: `${DASHBOARD_BASE}/network/overview/`,
  SYSTEM_HEALTH: `${DASHBOARD_BASE}/network/health/`,
  DEVICE_METRICS: (deviceId) => `${DASHBOARD_BASE}/network/device/${deviceId}/metrics/`,
  TOPOLOGY_LIST: `${DASHBOARD_BASE}/topology/list/`,
  TOPOLOGY_DATA: `${DASHBOARD_BASE}/topology/data/`,
  
  // Test endpoint
  TEST_STATUS: `${DASHBOARD_BASE}/test/status/`,
};

/**
 * Types de widgets disponibles
 */
export const WIDGET_TYPES = {
  SYSTEM_HEALTH: 'system_health',
  NETWORK_OVERVIEW: 'network_overview',
  ALERTS: 'alerts',
  DEVICE_STATUS: 'device_status',
  INTERFACE_STATUS: 'interface_status',
  PERFORMANCE_CHART: 'performance_chart',
  TOPOLOGY: 'topology',
  CUSTOM_CHART: 'custom_chart'
};

/**
 * Service principal pour le Dashboard
 */
class DashboardService {
  constructor() {
    this.apiClient = apiClient;
    
    // Cache pour les données fréquemment utilisées
    this.cache = new Map();
    this.cacheTimeout = 30000; // 30 secondes
    
    // WebSocket connections
    this.dashboardSocket = null;
    this.topologySocket = null;
    
    // Statistiques du service
    this.stats = {
      totalRequests: 0,
      cacheHits: 0,
      cacheMisses: 0,
      lastRequestTime: null,
      websocketConnections: 0
    };
  }

  /**
   * ===========================================
   * GESTION DES CONFIGURATIONS UTILISATEUR
   * ===========================================
   */

  /**
   * Récupère la configuration dashboard de l'utilisateur
   * GET /api/dashboard/config/
   */
  async getUserConfig() {
    const cacheKey = 'user_dashboard_config';
    
    if (this.isInCache(cacheKey)) {
      this.stats.cacheHits++;
      return this.getFromCache(cacheKey);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(DASHBOARD_ENDPOINTS.USER_CONFIG);
      
      this.updateStats(startTime, true);
      
      const result = {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          theme: response.data.theme || 'light',
          layout: response.data.layout || 'grid',
          refreshInterval: response.data.refresh_interval || 60
        }
      };
      
      this.setCache(cacheKey, result);
      this.stats.cacheMisses++;
      
      return result;
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getUserConfig');
    }
  }

  /**
   * Met à jour la configuration dashboard de l'utilisateur
   * PUT /api/dashboard/configs/{id}/
   */
  async updateUserConfig(configData) {
    try {
      const startTime = Date.now();
      
      // D'abord récupérer l'ID de la config existante
      const currentConfig = await this.getUserConfig();
      if (!currentConfig.success) {
        return currentConfig;
      }
      
      const configId = currentConfig.data.id;
      const response = await this.apiClient.put(
        DASHBOARD_ENDPOINTS.CONFIG_DETAIL(configId),
        configData
      );
      
      this.updateStats(startTime, true);
      
      // Invalider le cache
      this.cache.delete('user_dashboard_config');
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          configId,
          updatedFields: Object.keys(configData)
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'updateUserConfig', { configData });
    }
  }

  /**
   * ===========================================
   * GESTION DES DASHBOARDS PERSONNALISÉS
   * ===========================================
   */

  /**
   * Récupère tous les dashboards personnalisés
   * GET /api/dashboard/custom/
   */
  async getCustomDashboards(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(DASHBOARD_ENDPOINTS.CUSTOM_DASHBOARDS, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data.results || response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalCount: response.data.count || response.data.length,
          currentPage: params.page || 1
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getCustomDashboards', { params });
    }
  }

  /**
   * Récupère un dashboard personnalisé spécifique
   * GET /api/dashboard/custom/{id}/
   */
  async getCustomDashboard(dashboardId) {
    if (!dashboardId) {
      return this.createValidationError('getCustomDashboard', ['dashboardId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(DASHBOARD_ENDPOINTS.CUSTOM_DASHBOARD_DETAIL(dashboardId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        dashboardId,
        metadata: {
          timestamp: new Date().toISOString(),
          widgetsCount: response.data.layout?.widgets?.length || 0,
          isDefault: response.data.is_default,
          isPublic: response.data.is_public
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getCustomDashboard', { dashboardId });
    }
  }

  /**
   * Crée un nouveau dashboard personnalisé
   * POST /api/dashboard/custom/
   */
  async createCustomDashboard(dashboardData) {
    const requiredFields = ['name'];
    const validation = this.validateRequiredFields(dashboardData, requiredFields);
    if (!validation.isValid) {
      return this.createValidationError('createCustomDashboard', validation.missingFields);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        DASHBOARD_ENDPOINTS.CUSTOM_DASHBOARDS,
        dashboardData
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        dashboardId: response.data.id,
        metadata: {
          timestamp: new Date().toISOString(),
          name: dashboardData.name,
          isDefault: dashboardData.is_default || false
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'createCustomDashboard', { dashboardData });
    }
  }

  /**
   * Met à jour un dashboard personnalisé
   * PUT /api/dashboard/custom/{id}/
   */
  async updateCustomDashboard(dashboardId, dashboardData) {
    if (!dashboardId) {
      return this.createValidationError('updateCustomDashboard', ['dashboardId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.put(
        DASHBOARD_ENDPOINTS.CUSTOM_DASHBOARD_DETAIL(dashboardId),
        dashboardData
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        dashboardId,
        metadata: {
          timestamp: new Date().toISOString(),
          updatedFields: Object.keys(dashboardData)
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'updateCustomDashboard', { dashboardId, dashboardData });
    }
  }

  /**
   * Supprime un dashboard personnalisé
   * DELETE /api/dashboard/custom/{id}/
   */
  async deleteCustomDashboard(dashboardId) {
    if (!dashboardId) {
      return this.createValidationError('deleteCustomDashboard', ['dashboardId']);
    }

    try {
      const startTime = Date.now();
      await this.apiClient.delete(DASHBOARD_ENDPOINTS.CUSTOM_DASHBOARD_DETAIL(dashboardId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        dashboardId,
        metadata: {
          timestamp: new Date().toISOString(),
          action: 'deleted'
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'deleteCustomDashboard', { dashboardId });
    }
  }

  /**
   * ===========================================
   * GESTION DES WIDGETS
   * ===========================================
   */

  /**
   * Récupère tous les widgets
   * GET /api/dashboard/widgets/
   */
  async getWidgets(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(DASHBOARD_ENDPOINTS.WIDGETS, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data.results || response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalCount: response.data.count || response.data.length,
          activeWidgets: response.data.results ? 
            response.data.results.filter(w => w.is_active).length : 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getWidgets', { params });
    }
  }

  /**
   * Crée un nouveau widget
   * POST /api/dashboard/widgets/
   */
  async createWidget(widgetData) {
    const requiredFields = ['widget_type'];
    const validation = this.validateRequiredFields(widgetData, requiredFields);
    if (!validation.isValid) {
      return this.createValidationError('createWidget', validation.missingFields);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        DASHBOARD_ENDPOINTS.WIDGETS,
        widgetData
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        widgetId: response.data.id,
        metadata: {
          timestamp: new Date().toISOString(),
          widgetType: widgetData.widget_type,
          position: {
            x: widgetData.position_x || 0,
            y: widgetData.position_y || 0
          }
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'createWidget', { widgetData });
    }
  }

  /**
   * Met à jour un widget
   * PUT /api/dashboard/widgets/{id}/
   */
  async updateWidget(widgetId, widgetData) {
    if (!widgetId) {
      return this.createValidationError('updateWidget', ['widgetId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.put(
        DASHBOARD_ENDPOINTS.WIDGET_DETAIL(widgetId),
        widgetData
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        widgetId,
        metadata: {
          timestamp: new Date().toISOString(),
          updatedFields: Object.keys(widgetData)
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'updateWidget', { widgetId, widgetData });
    }
  }

  /**
   * Supprime un widget
   * DELETE /api/dashboard/widgets/{id}/
   */
  async deleteWidget(widgetId) {
    if (!widgetId) {
      return this.createValidationError('deleteWidget', ['widgetId']);
    }

    try {
      const startTime = Date.now();
      await this.apiClient.delete(DASHBOARD_ENDPOINTS.WIDGET_DETAIL(widgetId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        widgetId,
        metadata: {
          timestamp: new Date().toISOString(),
          action: 'deleted'
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'deleteWidget', { widgetId });
    }
  }

  /**
   * ===========================================
   * DONNÉES DE DASHBOARD TEMPS RÉEL
   * ===========================================
   */

  /**
   * Récupère les données agrégées du dashboard
   * GET /api/dashboard/data/
   */
  async getDashboardData(params = {}) {
    const cacheKey = `dashboard_data_${JSON.stringify(params)}`;
    
    if (this.isInCache(cacheKey)) {
      this.stats.cacheHits++;
      return this.getFromCache(cacheKey);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(DASHBOARD_ENDPOINTS.DASHBOARD_DATA, { params });
      
      this.updateStats(startTime, true);
      
      const result = {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          widgetsCount: response.data.widgets?.length || 0,
          metricsCount: Object.keys(response.data.metrics || {}).length,
          refreshInterval: this.cacheTimeout / 1000
        }
      };
      
      this.setCache(cacheKey, result);
      this.stats.cacheMisses++;
      
      return result;
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getDashboardData', { params });
    }
  }

  /**
   * Récupère la vue d'ensemble réseau
   * GET /api/dashboard/network/overview/
   */
  async getNetworkOverview(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(DASHBOARD_ENDPOINTS.NETWORK_OVERVIEW, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          devicesCount: response.data.devices_count || 0,
          networksCount: response.data.networks_count || 0,
          healthStatus: response.data.health_status || 'unknown'
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getNetworkOverview', { params });
    }
  }

  /**
   * Récupère les métriques de santé système
   * GET /api/dashboard/network/health/
   */
  async getSystemHealth(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(DASHBOARD_ENDPOINTS.SYSTEM_HEALTH, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          overallStatus: response.data.overall_status || 'unknown',
          servicesCount: response.data.services?.length || 0,
          alertsCount: response.data.alerts?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getSystemHealth', { params });
    }
  }

  /**
   * ===========================================
   * WEBSOCKET TEMPS RÉEL
   * ===========================================
   */

  /**
   * Connecte au WebSocket dashboard pour les mises à jour temps réel
   */
  connectDashboardWebSocket(callbacks = {}) {
    if (this.dashboardSocket) {
      return this.dashboardSocket;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard/`;

    this.dashboardSocket = new WebSocket(wsUrl);
    this.stats.websocketConnections++;

    this.dashboardSocket.onopen = () => {
      console.log('Dashboard WebSocket connected');
      if (callbacks.onOpen) callbacks.onOpen();
    };

    this.dashboardSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'dashboard_update':
            if (callbacks.onDashboardUpdate) {
              callbacks.onDashboardUpdate(data.data);
            }
            break;
          case 'network_update':
            if (callbacks.onNetworkUpdate) {
              callbacks.onNetworkUpdate(data.data);
            }
            break;
          case 'health_update':
            if (callbacks.onHealthUpdate) {
              callbacks.onHealthUpdate(data.data);
            }
            break;
          case 'error':
            console.error('Dashboard WebSocket error:', data.message);
            if (callbacks.onError) callbacks.onError(data.message);
            break;
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.dashboardSocket.onclose = () => {
      console.log('Dashboard WebSocket disconnected');
      this.dashboardSocket = null;
      if (callbacks.onClose) callbacks.onClose();
    };

    this.dashboardSocket.onerror = (error) => {
      console.error('Dashboard WebSocket error:', error);
      if (callbacks.onError) callbacks.onError(error);
    };

    return this.dashboardSocket;
  }

  /**
   * Envoie une commande via WebSocket
   */
  sendWebSocketCommand(command, data = {}) {
    if (!this.dashboardSocket || this.dashboardSocket.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return false;
    }

    try {
      this.dashboardSocket.send(JSON.stringify({
        command,
        ...data
      }));
      return true;
    } catch (error) {
      console.error('Error sending WebSocket command:', error);
      return false;
    }
  }

  /**
   * Déconnecte le WebSocket dashboard
   */
  disconnectDashboardWebSocket() {
    if (this.dashboardSocket) {
      this.dashboardSocket.close();
      this.dashboardSocket = null;
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

    // Classification des erreurs spécifiques au dashboard
    if (error.response?.status === 404) {
      errorInfo.error.type = 'DASHBOARD_NOT_FOUND';
      errorInfo.error.userMessage = 'Dashboard ou widget non trouvé.';
    } else if (error.response?.status === 403) {
      errorInfo.error.type = 'DASHBOARD_ACCESS_DENIED';
      errorInfo.error.userMessage = 'Accès refusé à ce dashboard.';
    } else if (error.response?.status >= 500) {
      errorInfo.error.type = 'DASHBOARD_SERVER_ERROR';
      errorInfo.error.userMessage = 'Erreur serveur lors de l\'accès au dashboard.';
    } else {
      errorInfo.error.type = 'DASHBOARD_UNKNOWN_ERROR';
      errorInfo.error.userMessage = 'Erreur inattendue lors de l\'opération.';
    }

    console.error(`[Dashboard Service Error] ${operation}:`, errorInfo);
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
      cacheSize: this.cache.size,
      isWebSocketConnected: this.dashboardSocket?.readyState === WebSocket.OPEN
    };
  }

  /**
   * Test de connectivité
   */
  async testConnection() {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(DASHBOARD_ENDPOINTS.TEST_STATUS);
      
      return {
        success: true,
        data: response.data,
        responseTime: Date.now() - startTime,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return this.handleError(error, 'testConnection');
    }
  }
}

// Instance singleton du service
const dashboardService = new DashboardService();

export default dashboardService;