/**
 * ApiService.js - Service API unifié
 * 
 * Remplace tous les services dispersés par une interface unifiée
 * Intégré avec CentralDataManager et RealtimeDataSync
 * Conserve les actions POST spécifiques par module
 * Point d'entrée unique pour toutes les interactions API
 */

import apiClient from '../api/client.js';
import centralDataManager from './CentralDataManager.js';
import realtimeDataSync from './RealtimeDataSync.js';

/**
 * Configuration des endpoints par module
 */
const MODULE_ENDPOINTS = {
  dashboard: {
    // GET centralisés (via CentralDataManager)
    get: {
      data: () => centralDataManager.getDashboardData(),
      systemHealth: () => centralDataManager.getDashboardData().then(r => r.success ? r.data.system_health : null),
      networkSummary: () => centralDataManager.getDashboardData().then(r => r.success ? r.data.network_summary : null)
    },
    // POST spécifiques conservés
    post: {
      updateConfig: (configData) => apiClient.put('/api/dashboard/configs/', configData),
      createWidget: (widgetData) => apiClient.post('/api/dashboard/widgets/', widgetData),
      updateWidget: (widgetId, widgetData) => apiClient.put(`/api/dashboard/widgets/${widgetId}/`, widgetData),
      deleteWidget: (widgetId) => apiClient.delete(`/api/dashboard/widgets/${widgetId}/`)
    }
  },
  
  equipment: {
    // GET centralisés
    get: {
      data: () => centralDataManager.getEquipmentData(),
      devices: () => centralDataManager.getEquipmentData().then(r => r.success ? r.data.devices : []),
      discovery: () => apiClient.get('/api/network/discovery/'),
      topology: () => apiClient.get('/api/network/topology/')
    },
    // POST spécifiques
    post: {
      startDiscovery: (discoveryData) => apiClient.post('/api/network/discovery/', discoveryData),
      updateDevice: (deviceId, deviceData) => apiClient.put(`/api/network/devices/${deviceId}/`, deviceData),
      deleteDevice: (deviceId) => apiClient.delete(`/api/network/devices/${deviceId}/`),
      runNetworkScan: (scanParams) => apiClient.post('/api/network/scan/', scanParams)
    }
  },
  
  gns3: {
    // GET centralisés
    get: {
      data: () => centralDataManager.getGNS3Data(),
      projects: () => centralDataManager.getGNS3Data().then(r => r.success ? r.data.projects : []),
      servers: () => centralDataManager.getGNS3Data().then(r => r.success ? r.data.servers : []),
      nodes: () => centralDataManager.getGNS3Data().then(r => r.success ? r.data.nodes : [])
    },
    // POST spécifiques conservés
    post: {
      createProject: (projectData) => apiClient.post('/api/gns3_integration/api/projects/', projectData),
      updateProject: (projectId, projectData) => apiClient.put(`/api/gns3_integration/api/projects/${projectId}/`, projectData),
      deleteProject: (projectId) => apiClient.delete(`/api/gns3_integration/api/projects/${projectId}/`),
      startProject: (projectId) => apiClient.post(`/api/gns3_integration/api/projects/${projectId}/start/`),
      stopProject: (projectId) => apiClient.post(`/api/gns3_integration/api/projects/${projectId}/stop/`),
      closeProject: (projectId) => apiClient.post(`/api/gns3_integration/api/projects/${projectId}/close/`),
      startNode: (nodeId) => apiClient.post(`/api/gns3_integration/api/nodes/${nodeId}/start/`),
      stopNode: (nodeId) => apiClient.post(`/api/gns3_integration/api/nodes/${nodeId}/stop/`),
      suspendNode: (nodeId) => apiClient.post(`/api/gns3_integration/api/nodes/${nodeId}/suspend/`),
      reloadNode: (nodeId) => apiClient.post(`/api/gns3_integration/api/nodes/${nodeId}/reload/`),
      createServer: (serverData) => apiClient.post('/api/gns3_integration/api/servers/', serverData),
      updateServer: (serverId, serverData) => apiClient.put(`/api/gns3_integration/api/servers/${serverId}/`, serverData),
      deleteServer: (serverId) => apiClient.delete(`/api/gns3_integration/api/servers/${serverId}/`),
      testServer: (serverId) => apiClient.post(`/api/gns3_integration/api/servers/${serverId}/test/`)
    }
  },
  
  monitoring: {
    // GET centralisés
    get: {
      data: () => centralDataManager.getMonitoringData(),
      alerts: () => centralDataManager.getMonitoringData().then(r => r.success ? r.data.alerts : []),
      metrics: () => centralDataManager.getMonitoringData().then(r => r.success ? r.data.metrics : []),
      notifications: () => centralDataManager.getMonitoringData().then(r => r.success ? r.data.notifications : []),
      realtimeMetrics: () => apiClient.get('/api/monitoring/unified/metrics/'),
      systemStatus: () => apiClient.get('/api/monitoring/unified/status/')
    },
    // POST spécifiques conservés
    post: {
      createAlert: (alertData) => apiClient.post('/api/monitoring/alerts/', alertData),
      acknowledgeAlert: (alertId) => apiClient.post(`/api/monitoring/alerts/${alertId}/acknowledge/`),
      resolveAlert: (alertId) => apiClient.post(`/api/monitoring/alerts/${alertId}/resolve/`),
      createThreshold: (thresholdData) => apiClient.post('/api/monitoring/metrics-definitions/', thresholdData),
      updateThreshold: (thresholdId, thresholdData) => apiClient.put(`/api/monitoring/metrics-definitions/${thresholdId}/`, thresholdData),
      testThreshold: (thresholdData) => apiClient.post('/api/monitoring/device-checks/', thresholdData),
      markNotificationRead: (notificationId) => apiClient.post(`/api/monitoring/notifications/${notificationId}/mark_read/`),
      markAllNotificationsRead: () => apiClient.post('/api/monitoring/notifications/mark_all_read/')
    }
  },
  
  qos: {
    // GET centralisés
    get: {
      data: () => centralDataManager.getQoSData(),
      policies: () => centralDataManager.getQoSData().then(r => r.success ? r.data.policies : []),
      trafficClasses: () => centralDataManager.getQoSData().then(r => r.success ? r.data.trafficClasses : []),
      classifiers: () => centralDataManager.getQoSData().then(r => r.success ? r.data.classifiers : []),
      interfacePolicies: () => centralDataManager.getQoSData().then(r => r.success ? r.data.interfacePolicies : []),
      statistics: () => centralDataManager.getQoSData().then(r => r.success ? r.data.statistics : [])
    },
    // POST spécifiques conservés
    post: {
      createPolicy: (policyData) => apiClient.post('/api/qos/policies/', policyData),
      updatePolicy: (policyId, policyData) => apiClient.put(`/api/qos/policies/${policyId}/`, policyData),
      deletePolicy: (policyId) => apiClient.delete(`/api/qos/policies/${policyId}/`),
      activatePolicy: (policyId) => apiClient.post(`/api/qos/policies/${policyId}/activate/`),
      deactivatePolicy: (policyId) => apiClient.post(`/api/qos/policies/${policyId}/deactivate/`),
      createTrafficClass: (classData) => apiClient.post('/api/qos/traffic-classes/', classData),
      updateTrafficClass: (classId, classData) => apiClient.put(`/api/qos/traffic-classes/${classId}/`, classData),
      deleteTrafficClass: (classId) => apiClient.delete(`/api/qos/traffic-classes/${classId}/`),
      createClassifier: (classifierData) => apiClient.post('/api/qos/classifiers/', classifierData),
      updateClassifier: (classifierId, classifierData) => apiClient.put(`/api/qos/classifiers/${classifierId}/`, classifierData),
      deleteClassifier: (classifierId) => apiClient.delete(`/api/qos/classifiers/${classifierId}/`),
      createInterfacePolicy: (interfacePolicyData) => apiClient.post('/api/qos/interface-policies/', interfacePolicyData),
      updateInterfacePolicy: (interfacePolicyId, interfacePolicyData) => apiClient.put(`/api/qos/interface-policies/${interfacePolicyId}/`, interfacePolicyData),
      deleteInterfacePolicy: (interfacePolicyId) => apiClient.delete(`/api/qos/interface-policies/${interfacePolicyId}/`)
    }
  }
};

/**
 * Service API unifié
 */
class ApiService {
  constructor() {
    this.centralDataManager = centralDataManager;
    this.realtimeDataSync = realtimeDataSync;
    
    // Cache pour les POST récents (éviter doublons)
    this.postCache = new Map();
    this.postCacheTimeout = 5000; // 5 secondes
    
    // Statistiques
    this.stats = {
      getRequests: 0,
      postRequests: 0,
      cacheHits: 0,
      errors: 0,
      lastActivity: null
    };
    
    console.log('[ApiService] Service API unifié initialisé');
  }

  /**
   * ===========================================
   * INTERFACE GET UNIFIÉE
   * ===========================================
   */
  
  /**
   * Obtenir des données pour un module (via cache centralisé)
   */
  async get(module, dataType = 'data', forceRefresh = false) {
    try {
      this.stats.getRequests++;
      this.stats.lastActivity = new Date().toISOString();
      
      const moduleEndpoints = MODULE_ENDPOINTS[module];
      if (!moduleEndpoints || !moduleEndpoints.get) {
        throw new Error(`Module ${module} non supporté ou pas de endpoints GET`);
      }
      
      const getter = moduleEndpoints.get[dataType];
      if (!getter) {
        throw new Error(`Type de données ${dataType} non disponible pour le module ${module}`);
      }
      
      // Pour les données centralisées, passer par le cache
      if (dataType === 'data') {
        const result = await getter(forceRefresh);
        return this.formatGetResponse(result, module, dataType);
      }
      
      // Pour les requêtes spécifiques, appel direct
      const result = await getter();
      return this.formatGetResponse({ success: true, data: result.data }, module, dataType);
      
    } catch (error) {
      this.stats.errors++;
      console.error(`[ApiService] Erreur GET ${module}.${dataType}:`, error);
      return this.formatGetResponse({ success: false, error }, module, dataType);
    }
  }
  
  /**
   * Formater la réponse GET
   */
  formatGetResponse(result, module, dataType) {
    return {
      success: result.success,
      data: result.data,
      error: result.error,
      module,
      dataType,
      timestamp: new Date().toISOString(),
      fromCache: result.fromCache || false
    };
  }

  /**
   * ===========================================
   * INTERFACE POST UNIFIÉE
   * ===========================================
   */
  
  /**
   * Exécuter une action POST
   */
  async post(module, action, data = null, options = {}) {
    try {
      this.stats.postRequests++;
      this.stats.lastActivity = new Date().toISOString();
      
      // Vérifier le cache POST pour éviter les doublons
      const cacheKey = this.buildPostCacheKey(module, action, data);
      if (this.isPostCached(cacheKey) && !options.bypassCache) {
        this.stats.cacheHits++;
        return this.getPostFromCache(cacheKey);
      }
      
      const moduleEndpoints = MODULE_ENDPOINTS[module];
      if (!moduleEndpoints || !moduleEndpoints.post) {
        throw new Error(`Module ${module} non supporté ou pas de endpoints POST`);
      }
      
      const postAction = moduleEndpoints.post[action];
      if (!postAction) {
        throw new Error(`Action ${action} non disponible pour le module ${module}`);
      }
      
      // Exécuter l'action POST
      const startTime = Date.now();
      let result;
      
      if (typeof postAction === 'function') {
        // Action avec paramètres
        result = await postAction(data);
      } else {
        // URL directe
        result = await apiClient.post(postAction, data);
      }
      
      const responseTime = Date.now() - startTime;
      
      const formattedResult = this.formatPostResponse(result, module, action, responseTime);
      
      // Mettre en cache
      this.setPostCache(cacheKey, formattedResult);
      
      // Invalider le cache des données GET correspondantes
      this.invalidateRelatedCache(module, action);
      
      // Déclencher rafraîchissement des données si nécessaire
      await this.handlePostRefresh(module, action, formattedResult);
      
      return formattedResult;
      
    } catch (error) {
      this.stats.errors++;
      console.error(`[ApiService] Erreur POST ${module}.${action}:`, error);
      return this.formatPostResponse({ success: false, error }, module, action, 0);
    }
  }
  
  /**
   * Formater la réponse POST
   */
  formatPostResponse(result, module, action, responseTime) {
    return {
      success: result.status ? result.status < 400 : !!result.data,
      data: result.data,
      error: result.error || (result.status >= 400 ? { message: `HTTP ${result.status}`, status: result.status } : null),
      module,
      action,
      responseTime,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * ===========================================
   * GESTION CACHE POST
   * ===========================================
   */
  
  buildPostCacheKey(module, action, data) {
    const dataHash = data ? JSON.stringify(data).substring(0, 50) : 'no-data';
    return `${module}_${action}_${dataHash}`;
  }
  
  isPostCached(key) {
    const cached = this.postCache.get(key);
    if (!cached) return false;
    
    const now = Date.now();
    if (now - cached.timestamp > this.postCacheTimeout) {
      this.postCache.delete(key);
      return false;
    }
    
    return true;
  }
  
  getPostFromCache(key) {
    const cached = this.postCache.get(key);
    return { ...cached.data, fromCache: true };
  }
  
  setPostCache(key, data) {
    this.postCache.set(key, {
      data,
      timestamp: Date.now()
    });
  }
  
  invalidateRelatedCache(module, action) {
    // Invalider le cache CentralDataManager pour ce module
    this.centralDataManager.invalidateCache(module);
    
    // Actions spécifiques qui affectent d'autres modules
    const crossModuleActions = {
      'gns3': ['startProject', 'stopProject', 'createProject', 'deleteProject'], // Affecte equipment
      'equipment': ['startDiscovery'], // Affecte dashboard
      'monitoring': ['createAlert', 'resolveAlert'] // Affecte dashboard
    };
    
    if (crossModuleActions[module] && crossModuleActions[module].includes(action)) {
      // Invalider les modules reliés
      if (module === 'gns3') {
        this.centralDataManager.invalidateCache('equipment');
      } else if (module === 'equipment' || module === 'monitoring') {
        this.centralDataManager.invalidateCache('dashboard');
      }
    }
  }
  
  async handlePostRefresh(module, action, result) {
    if (!result.success) return;
    
    // Actions qui nécessitent un rafraîchissement immédiat
    const refreshActions = {
      'gns3': ['createProject', 'deleteProject', 'startProject', 'stopProject'],
      'equipment': ['startDiscovery', 'updateDevice', 'deleteDevice'],
      'monitoring': ['createAlert', 'acknowledgeAlert', 'resolveAlert'],
      'qos': ['createPolicy', 'activatePolicy', 'deactivatePolicy']
    };
    
    if (refreshActions[module] && refreshActions[module].includes(action)) {
      // Rafraîchir les données du module
      setTimeout(() => {
        this.centralDataManager.syncModuleData(module);
      }, 1000); // Délai pour laisser le backend traiter
      
      // Rafraîchir les modules reliés si nécessaire
      if (module === 'gns3' && ['createProject', 'deleteProject', 'startProject', 'stopProject'].includes(action)) {
        setTimeout(() => {
          this.centralDataManager.syncModuleData('equipment');
        }, 2000);
      }
    }
  }

  /**
   * ===========================================
   * MÉTHODES DE CONVENANCE PAR MODULE
   * ===========================================
   */
  
  // Dashboard
  dashboard = {
    getData: (forceRefresh = false) => this.get('dashboard', 'data', forceRefresh),
    getSystemHealth: () => this.get('dashboard', 'systemHealth'),
    getNetworkSummary: () => this.get('dashboard', 'networkSummary'),
    updateConfig: (configData) => this.post('dashboard', 'updateConfig', configData),
    createWidget: (widgetData) => this.post('dashboard', 'createWidget', widgetData),
    updateWidget: (widgetId, widgetData) => this.post('dashboard', 'updateWidget', { widgetId, ...widgetData }),
    deleteWidget: (widgetId) => this.post('dashboard', 'deleteWidget', widgetId)
  };
  
  // Equipment
  equipment = {
    getData: (forceRefresh = false) => this.get('equipment', 'data', forceRefresh),
    getDevices: () => this.get('equipment', 'devices'),
    getDiscovery: () => this.get('equipment', 'discovery'),
    getTopology: () => this.get('equipment', 'topology'),
    startDiscovery: (discoveryData) => this.post('equipment', 'startDiscovery', discoveryData),
    updateDevice: (deviceId, deviceData) => this.post('equipment', 'updateDevice', { deviceId, ...deviceData }),
    deleteDevice: (deviceId) => this.post('equipment', 'deleteDevice', deviceId),
    runNetworkScan: (scanParams) => this.post('equipment', 'runNetworkScan', scanParams)
  };
  
  // GNS3
  gns3 = {
    getData: (forceRefresh = false) => this.get('gns3', 'data', forceRefresh),
    getProjects: () => this.get('gns3', 'projects'),
    getServers: () => this.get('gns3', 'servers'),
    getNodes: () => this.get('gns3', 'nodes'),
    createProject: (projectData) => this.post('gns3', 'createProject', projectData),
    updateProject: (projectId, projectData) => this.post('gns3', 'updateProject', { projectId, ...projectData }),
    deleteProject: (projectId) => this.post('gns3', 'deleteProject', projectId),
    startProject: (projectId) => this.post('gns3', 'startProject', projectId),
    stopProject: (projectId) => this.post('gns3', 'stopProject', projectId),
    closeProject: (projectId) => this.post('gns3', 'closeProject', projectId),
    startNode: (nodeId) => this.post('gns3', 'startNode', nodeId),
    stopNode: (nodeId) => this.post('gns3', 'stopNode', nodeId),
    suspendNode: (nodeId) => this.post('gns3', 'suspendNode', nodeId),
    reloadNode: (nodeId) => this.post('gns3', 'reloadNode', nodeId),
    createServer: (serverData) => this.post('gns3', 'createServer', serverData),
    updateServer: (serverId, serverData) => this.post('gns3', 'updateServer', { serverId, ...serverData }),
    deleteServer: (serverId) => this.post('gns3', 'deleteServer', serverId),
    testServer: (serverId) => this.post('gns3', 'testServer', serverId)
  };
  
  // Monitoring
  monitoring = {
    getData: (forceRefresh = false) => this.get('monitoring', 'data', forceRefresh),
    getAlerts: () => this.get('monitoring', 'alerts'),
    getMetrics: () => this.get('monitoring', 'metrics'),
    getNotifications: () => this.get('monitoring', 'notifications'),
    getRealtimeMetrics: () => this.get('monitoring', 'realtimeMetrics'),
    getSystemStatus: () => this.get('monitoring', 'systemStatus'),
    createAlert: (alertData) => this.post('monitoring', 'createAlert', alertData),
    acknowledgeAlert: (alertId) => this.post('monitoring', 'acknowledgeAlert', alertId),
    resolveAlert: (alertId) => this.post('monitoring', 'resolveAlert', alertId),
    createThreshold: (thresholdData) => this.post('monitoring', 'createThreshold', thresholdData),
    updateThreshold: (thresholdId, thresholdData) => this.post('monitoring', 'updateThreshold', { thresholdId, ...thresholdData }),
    testThreshold: (thresholdData) => this.post('monitoring', 'testThreshold', thresholdData),
    markNotificationRead: (notificationId) => this.post('monitoring', 'markNotificationRead', notificationId),
    markAllNotificationsRead: () => this.post('monitoring', 'markAllNotificationsRead')
  };
  
  // QoS
  qos = {
    getData: (forceRefresh = false) => this.get('qos', 'data', forceRefresh),
    getPolicies: () => this.get('qos', 'policies'),
    getTrafficClasses: () => this.get('qos', 'trafficClasses'),
    getClassifiers: () => this.get('qos', 'classifiers'),
    getInterfacePolicies: () => this.get('qos', 'interfacePolicies'),
    getStatistics: () => this.get('qos', 'statistics'),
    createPolicy: (policyData) => this.post('qos', 'createPolicy', policyData),
    updatePolicy: (policyId, policyData) => this.post('qos', 'updatePolicy', { policyId, ...policyData }),
    deletePolicy: (policyId) => this.post('qos', 'deletePolicy', policyId),
    activatePolicy: (policyId) => this.post('qos', 'activatePolicy', policyId),
    deactivatePolicy: (policyId) => this.post('qos', 'deactivatePolicy', policyId),
    createTrafficClass: (classData) => this.post('qos', 'createTrafficClass', classData),
    updateTrafficClass: (classId, classData) => this.post('qos', 'updateTrafficClass', { classId, ...classData }),
    deleteTrafficClass: (classId) => this.post('qos', 'deleteTrafficClass', classId),
    createClassifier: (classifierData) => this.post('qos', 'createClassifier', classifierData),
    updateClassifier: (classifierId, classifierData) => this.post('qos', 'updateClassifier', { classifierId, ...classifierData }),
    deleteClassifier: (classifierId) => this.post('qos', 'deleteClassifier', classifierId),
    createInterfacePolicy: (interfacePolicyData) => this.post('qos', 'createInterfacePolicy', interfacePolicyData),
    updateInterfacePolicy: (interfacePolicyId, interfacePolicyData) => this.post('qos', 'updateInterfacePolicy', { interfacePolicyId, ...interfacePolicyData }),
    deleteInterfacePolicy: (interfacePolicyId) => this.post('qos', 'deleteInterfacePolicy', interfacePolicyId)
  };

  /**
   * ===========================================
   * GESTION TEMPS RÉEL
   * ===========================================
   */
  
  startRealtime(modules = ['dashboard', 'equipment', 'gns3', 'monitoring']) {
    console.log('[ApiService] Démarrage synchronisation temps réel pour:', modules);
    return this.realtimeDataSync.start(modules);
  }
  
  stopRealtime() {
    console.log('[ApiService] Arrêt synchronisation temps réel');
    return this.realtimeDataSync.stop();
  }
  
  getRealtimeStatus() {
    return this.realtimeDataSync.getStatus();
  }

  /**
   * ===========================================
   * SYNCHRONISATION MANUELLE
   * ===========================================
   */
  
  async syncAll(forceRefresh = true) {
    console.log('[ApiService] Synchronisation manuelle de tous les modules');
    
    const modules = ['dashboard', 'equipment', 'gns3', 'monitoring', 'qos'];
    const results = await Promise.allSettled(
      modules.map(module => this.centralDataManager.syncModuleData(module))
    );
    
    return {
      success: results.every(r => r.status === 'fulfilled'),
      results: results.map((r, i) => ({
        module: modules[i],
        success: r.status === 'fulfilled',
        data: r.status === 'fulfilled' ? r.value : null,
        error: r.status === 'rejected' ? r.reason : null
      })),
      timestamp: new Date().toISOString()
    };
  }
  
  async syncModule(module, forceRefresh = true) {
    console.log(`[ApiService] Synchronisation manuelle du module: ${module}`);
    return await this.centralDataManager.syncModuleData(module);
  }

  /**
   * ===========================================
   * UTILITAIRES ET DIAGNOSTICS
   * ===========================================
   */
  
  getStats() {
    return {
      ...this.stats,
      centralDataManager: this.centralDataManager.getStats(),
      realtimeSync: this.realtimeDataSync.getStatus(),
      postCacheSize: this.postCache.size
    };
  }
  
  getHealthStatus() {
    const centralHealth = this.centralDataManager.getHealthStatus();
    const realtimeHealth = this.realtimeDataSync.getHealthStatus();
    
    return {
      healthy: centralHealth.healthy && realtimeHealth.healthy,
      services: {
        centralDataManager: centralHealth,
        realtimeSync: realtimeHealth,
        apiService: {
          healthy: this.stats.errors < 10, // Moins de 10 erreurs
          lastActivity: this.stats.lastActivity,
          requestCount: this.stats.getRequests + this.stats.postRequests
        }
      },
      overall: {
        score: (centralHealth.healthy && realtimeHealth.healthy) ? 1 : 0.5,
        lastUpdate: new Date().toISOString()
      }
    };
  }
  
  async testConnectivity() {
    console.log('[ApiService] Test de connectivité');
    return await this.centralDataManager.testConnectivity();
  }
  
  clearCaches() {
    console.log('[ApiService] Nettoyage des caches');
    this.centralDataManager.invalidateCache();
    this.postCache.clear();
  }
}

// Instance singleton
const apiService = new ApiService();

export default apiService;