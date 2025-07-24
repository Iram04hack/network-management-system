/**
 * Service QoS - Intégration complète avec le module QoS Management backend
 * Gestion des politiques QoS, classes de trafic, monitoring temps réel et SLA
 */

import apiClient from '../api/client.js';

/**
 * Base URLs pour le module QoS Management
 */
const QOS_BASE = '/api/qos-management';

/**
 * Endpoints du module QoS Management
 */
export const QOS_ENDPOINTS = {
  // === APIs UNIFIÉES (MODERNES) ===
  UNIFIED_STATUS: `${QOS_BASE}/unified/status/`,
  UNIFIED_QOS_DATA: `${QOS_BASE}/unified/qos-data/`,
  UNIFIED_DASHBOARD: `${QOS_BASE}/unified/dashboard/`,
  INFRASTRUCTURE_HEALTH: `${QOS_BASE}/unified/infrastructure-health/`,
  UNIFIED_ENDPOINTS: `${QOS_BASE}/unified/endpoints/`,
  INTEGRATION_STATUS: `${QOS_BASE}/unified/integration-status/`,

  // === APIs LEGACY (CRUD) ===
  // Politiques QoS
  POLICIES: `${QOS_BASE}/policies/`,
  POLICY_DETAIL: (policyId) => `${QOS_BASE}/policies/${policyId}/`,
  
  // Classes de trafic
  TRAFFIC_CLASSES: `${QOS_BASE}/traffic-classes/`,
  TRAFFIC_CLASS_DETAIL: (classId) => `${QOS_BASE}/traffic-classes/${classId}/`,
  
  // Classificateurs de trafic
  CLASSIFIERS: `${QOS_BASE}/classifiers/`,
  CLASSIFIER_DETAIL: (classifierId) => `${QOS_BASE}/classifiers/${classifierId}/`,
  
  // Politiques d'interface
  INTERFACE_POLICIES: `${QOS_BASE}/interface-policies/`,
  INTERFACE_POLICY_DETAIL: (policyId) => `${QOS_BASE}/interface-policies/${policyId}/`,
  
  // Application des politiques
  POLICY_APPLICATION: `${QOS_BASE}/policy-application/`,
  APPLY_POLICY: (policyId) => `${QOS_BASE}/policy-application/${policyId}/apply/`,
  
  // Validation des politiques
  POLICY_VALIDATION: `${QOS_BASE}/policy-validation/`,
  VALIDATE_POLICY: (policyId) => `${QOS_BASE}/policy-validation/${policyId}/validate/`,
  
  // Visualisation et configuration
  VISUALIZATION: `${QOS_BASE}/visualization/`,
  VISUALIZATION_POLICY: (policyId) => `${QOS_BASE}/visualization/${policyId}/`,
  CONFIGURATION: `${QOS_BASE}/configure/`,
  
  // CBWFQ et allocation de bande passante
  CBWFQ_CONFIG: (policyId) => `${QOS_BASE}/policies/${policyId}/cbwfq/`,
  BANDWIDTH_ALLOCATION: (policyId) => `${QOS_BASE}/policies/${policyId}/bandwidth-allocation/`,
  
  // Rapports SLA
  SLA_COMPLIANCE: (deviceId) => `${QOS_BASE}/reports/sla/${deviceId}/`,
  QOS_PERFORMANCE: `${QOS_BASE}/reports/qos/`,
  SLA_TRENDS: (deviceId) => `${QOS_BASE}/reports/sla/${deviceId}/trends/`,
};

/**
 * Types de politiques QoS disponibles
 */
export const QOS_POLICY_TYPES = {
  INPUT: 'input',
  OUTPUT: 'output',
  BIDIRECTIONAL: 'bidirectional'
};

/**
 * Stratégies QoS disponibles
 */
export const QOS_STRATEGIES = {
  FIFO: 'fifo',
  PRIORITY: 'priority',
  WFQ: 'wfq',
  CBWFQ: 'cbwfq',
  LLQ: 'llq'
};

/**
 * Actions QoS disponibles
 */
export const QOS_ACTIONS = {
  ALLOW: 'allow',
  DENY: 'deny',
  POLICE: 'police',
  SHAPE: 'shape',
  MARK: 'mark',
  PRIORITY: 'priority'
};

/**
 * Service principal pour QoS Management
 */
class QoSService {
  constructor() {
    this.apiClient = apiClient;
    
    // Cache pour les données fréquemment utilisées
    this.cache = new Map();
    this.cacheTimeout = 30000; // 30 secondes
    
    // WebSocket pour les données temps réel
    this.realtimeSocket = null;
    
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
   * APIs UNIFIÉES (MODERNES)
   * ===========================================
   */

  /**
   * Récupère le statut unifié du système QoS
   * GET /api/qos-management/unified/status/
   */
  async getUnifiedStatus() {
    const cacheKey = 'unified_qos_status';
    
    if (this.isInCache(cacheKey)) {
      this.stats.cacheHits++;
      return this.getFromCache(cacheKey);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.UNIFIED_STATUS);
      
      this.updateStats(startTime, true);
      
      const result = {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          operational: response.data.operational,
          componentsCount: Object.keys(response.data.components || {}).length,
          refreshInterval: this.cacheTimeout / 1000
        }
      };
      
      this.setCache(cacheKey, result);
      this.stats.cacheMisses++;
      
      return result;
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getUnifiedStatus');
    }
  }

  /**
   * Récupère toutes les données QoS unifiées (GNS3 + Docker)
   * GET /api/qos-management/unified/qos-data/
   */
  async getUnifiedQoSData() {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.UNIFIED_QOS_DATA);
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          sourcesCount: Object.keys(response.data.sources || {}).length,
          collectionsCount: response.data.summary?.successful_collections || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getUnifiedQoSData');
    }
  }

  /**
   * Récupère les données complètes pour le dashboard QoS
   * GET /api/qos-management/unified/dashboard/
   */
  async getDashboardData() {
    const cacheKey = 'qos_dashboard_data';
    
    if (this.isInCache(cacheKey)) {
      this.stats.cacheHits++;
      return this.getFromCache(cacheKey);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.UNIFIED_DASHBOARD);
      
      this.updateStats(startTime, true);
      
      const result = {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalPolicies: response.data.qos_overview?.total_policies || 0,
          activePolicies: response.data.qos_overview?.active_policies || 0,
          infrastructureHealth: response.data.infrastructure_health?.health_percentage || 0
        }
      };
      
      this.setCache(cacheKey, result);
      this.stats.cacheMisses++;
      
      return result;
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getDashboardData');
    }
  }

  /**
   * Récupère la santé de l'infrastructure QoS
   * GET /api/qos-management/unified/infrastructure-health/
   */
  async getInfrastructureHealth() {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.INFRASTRUCTURE_HEALTH);
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          overallHealth: response.data.overall_health,
          healthScore: response.data.health_score,
          recommendationsCount: response.data.recommendations?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getInfrastructureHealth');
    }
  }

  /**
   * Récupère le statut des intégrations GNS3 et Docker
   * GET /api/qos-management/unified/integration-status/
   */
  async getIntegrationStatus() {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.INTEGRATION_STATUS);
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          gns3Available: response.data.gns3_integration?.available || false,
          dockerAvailable: response.data.docker_integration?.available || false,
          overallStatus: response.data.integration_health?.overall_status
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getIntegrationStatus');
    }
  }

  /**
   * ===========================================
   * GESTION DES POLITIQUES QOS
   * ===========================================
   */

  /**
   * Récupère toutes les politiques QoS
   * GET /api/qos-management/policies/
   */
  async getPolicies(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.POLICIES, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data.results || response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalCount: response.data.count || response.data.length,
          currentPage: params.page || 1,
          pageSize: params.page_size || 20
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getPolicies', { params });
    }
  }

  /**
   * Récupère une politique QoS spécifique
   * GET /api/qos-management/policies/{id}/
   */
  async getPolicy(policyId) {
    if (!policyId) {
      return this.createValidationError('getPolicy', ['policyId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.POLICY_DETAIL(policyId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        policyId,
        metadata: {
          timestamp: new Date().toISOString(),
          policyType: response.data.type,
          strategy: response.data.strategy,
          isActive: response.data.is_active
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getPolicy', { policyId });
    }
  }

  /**
   * Crée une nouvelle politique QoS
   * POST /api/qos-management/policies/
   */
  async createPolicy(policyData) {
    const requiredFields = ['name', 'type', 'strategy'];
    const validation = this.validateRequiredFields(policyData, requiredFields);
    if (!validation.isValid) {
      return this.createValidationError('createPolicy', validation.missingFields);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        QOS_ENDPOINTS.POLICIES,
        policyData
      );
      
      this.updateStats(startTime, true);
      
      // Invalider le cache des politiques
      this.clearCacheByPattern('policies');
      this.clearCacheByPattern('qos_dashboard');
      
      return {
        success: true,
        data: response.data,
        policyId: response.data.id,
        metadata: {
          timestamp: new Date().toISOString(),
          name: policyData.name,
          type: policyData.type,
          strategy: policyData.strategy
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'createPolicy', { policyData });
    }
  }

  /**
   * Met à jour une politique QoS
   * PUT /api/qos-management/policies/{id}/
   */
  async updatePolicy(policyId, policyData) {
    if (!policyId) {
      return this.createValidationError('updatePolicy', ['policyId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.put(
        QOS_ENDPOINTS.POLICY_DETAIL(policyId),
        policyData
      );
      
      this.updateStats(startTime, true);
      
      // Invalider le cache
      this.clearCacheByPattern('policies');
      this.clearCacheByPattern('qos_dashboard');
      
      return {
        success: true,
        data: response.data,
        policyId,
        metadata: {
          timestamp: new Date().toISOString(),
          updatedFields: Object.keys(policyData)
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'updatePolicy', { policyId, policyData });
    }
  }

  /**
   * Supprime une politique QoS
   * DELETE /api/qos-management/policies/{id}/
   */
  async deletePolicy(policyId) {
    if (!policyId) {
      return this.createValidationError('deletePolicy', ['policyId']);
    }

    try {
      const startTime = Date.now();
      await this.apiClient.delete(QOS_ENDPOINTS.POLICY_DETAIL(policyId));
      
      this.updateStats(startTime, true);
      
      // Invalider le cache
      this.clearCacheByPattern('policies');
      this.clearCacheByPattern('qos_dashboard');
      
      return {
        success: true,
        policyId,
        metadata: {
          timestamp: new Date().toISOString(),
          action: 'deleted'
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'deletePolicy', { policyId });
    }
  }

  /**
   * ===========================================
   * GESTION DES CLASSES DE TRAFIC
   * ===========================================
   */

  /**
   * Récupère toutes les classes de trafic
   * GET /api/qos-management/traffic-classes/
   */
  async getTrafficClasses(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.TRAFFIC_CLASSES, { params });
      
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
      return this.handleError(error, 'getTrafficClasses', { params });
    }
  }

  /**
   * Crée une nouvelle classe de trafic
   * POST /api/qos-management/traffic-classes/
   */
  async createTrafficClass(classData) {
    const requiredFields = ['name', 'priority'];
    const validation = this.validateRequiredFields(classData, requiredFields);
    if (!validation.isValid) {
      return this.createValidationError('createTrafficClass', validation.missingFields);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        QOS_ENDPOINTS.TRAFFIC_CLASSES,
        classData
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        classId: response.data.id,
        metadata: {
          timestamp: new Date().toISOString(),
          name: classData.name,
          priority: classData.priority
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'createTrafficClass', { classData });
    }
  }

  /**
   * ===========================================
   * GESTION DES CLASSIFICATEURS
   * ===========================================
   */

  /**
   * Récupère tous les classificateurs
   * GET /api/qos-management/classifiers/
   */
  async getClassifiers(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.CLASSIFIERS, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data.results || response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalCount: response.data.count || response.data.length
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getClassifiers', { params });
    }
  }

  /**
   * Crée un nouveau classificateur
   * POST /api/qos-management/classifiers/
   */
  async createClassifier(classifierData) {
    const requiredFields = ['name', 'criteria'];
    const validation = this.validateRequiredFields(classifierData, requiredFields);
    if (!validation.isValid) {
      return this.createValidationError('createClassifier', validation.missingFields);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        QOS_ENDPOINTS.CLASSIFIERS,
        classifierData
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        classifierId: response.data.id,
        metadata: {
          timestamp: new Date().toISOString(),
          name: classifierData.name,
          criteriaCount: Object.keys(classifierData.criteria || {}).length
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'createClassifier', { classifierData });
    }
  }

  /**
   * ===========================================
   * POLITIQUES D'INTERFACE
   * ===========================================
   */

  /**
   * Récupère les politiques d'interface
   * GET /api/qos-management/interface-policies/
   */
  async getInterfacePolicies(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.INTERFACE_POLICIES, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data.results || response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalCount: response.data.count || response.data.length
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getInterfacePolicies', { params });
    }
  }

  /**
   * Applique une politique QoS à une interface
   * POST /api/qos-management/interface-policies/
   */
  async applyPolicyToInterface(interfaceId, policyId, direction = 'input') {
    if (!interfaceId || !policyId) {
      return this.createValidationError('applyPolicyToInterface', ['interfaceId', 'policyId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        QOS_ENDPOINTS.INTERFACE_POLICIES,
        {
          interface_id: interfaceId,
          policy_id: policyId,
          direction: direction
        }
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          interfaceId,
          policyId,
          direction
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'applyPolicyToInterface', { interfaceId, policyId, direction });
    }
  }

  /**
   * ===========================================
   * APPLICATION ET VALIDATION DES POLITIQUES
   * ===========================================
   */

  /**
   * Applique une politique QoS
   * POST /api/qos-management/policy-application/{id}/apply/
   */
  async applyPolicy(policyId, applicationData = {}) {
    if (!policyId) {
      return this.createValidationError('applyPolicy', ['policyId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        QOS_ENDPOINTS.APPLY_POLICY(policyId),
        applicationData
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        policyId,
        metadata: {
          timestamp: new Date().toISOString(),
          appliedTo: applicationData.targets || [],
          status: response.data.status
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'applyPolicy', { policyId, applicationData });
    }
  }

  /**
   * Valide une politique QoS
   * POST /api/qos-management/policy-validation/{id}/validate/
   */
  async validatePolicy(policyId, validationData = {}) {
    if (!policyId) {
      return this.createValidationError('validatePolicy', ['policyId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        QOS_ENDPOINTS.VALIDATE_POLICY(policyId),
        validationData
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        policyId,
        metadata: {
          timestamp: new Date().toISOString(),
          isValid: response.data.is_valid,
          validationRules: response.data.validation_rules?.length || 0,
          errorsCount: response.data.errors?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'validatePolicy', { policyId, validationData });
    }
  }

  /**
   * ===========================================
   * RAPPORTS SLA ET PERFORMANCE
   * ===========================================
   */

  /**
   * Récupère le rapport de conformité SLA pour un dispositif
   * GET /api/qos-management/reports/sla/{device_id}/
   */
  async getSLAComplianceReport(deviceId, params = {}) {
    if (!deviceId) {
      return this.createValidationError('getSLAComplianceReport', ['deviceId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(
        QOS_ENDPOINTS.SLA_COMPLIANCE(deviceId),
        { params }
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        deviceId,
        metadata: {
          timestamp: new Date().toISOString(),
          reportPeriod: params.period || 'last_24h',
          complianceScore: response.data.compliance_score,
          metricsCount: response.data.metrics?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getSLAComplianceReport', { deviceId, params });
    }
  }

  /**
   * Récupère le rapport de performance QoS global
   * GET /api/qos-management/reports/qos/
   */
  async getQoSPerformanceReport(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(QOS_ENDPOINTS.QOS_PERFORMANCE, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          reportPeriod: params.period || 'last_24h',
          devicesCount: response.data.devices_analyzed || 0,
          policiesCount: response.data.policies_analyzed || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getQoSPerformanceReport', { params });
    }
  }

  /**
   * ===========================================
   * CONFIGURATION AVANCÉE
   * ===========================================
   */

  /**
   * Configure CBWFQ pour une politique
   * POST /api/qos-management/policies/{id}/cbwfq/
   */
  async configureCBWFQ(policyId, cbwfqConfig) {
    if (!policyId) {
      return this.createValidationError('configureCBWFQ', ['policyId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        QOS_ENDPOINTS.CBWFQ_CONFIG(policyId),
        cbwfqConfig
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        policyId,
        metadata: {
          timestamp: new Date().toISOString(),
          bandwidth: cbwfqConfig.bandwidth,
          classesCount: cbwfqConfig.classes?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'configureCBWFQ', { policyId, cbwfqConfig });
    }
  }

  /**
   * Configure l'allocation de bande passante
   * POST /api/qos-management/policies/{id}/bandwidth-allocation/
   */
  async configureBandwidthAllocation(policyId, allocationConfig) {
    if (!policyId) {
      return this.createValidationError('configureBandwidthAllocation', ['policyId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(
        QOS_ENDPOINTS.BANDWIDTH_ALLOCATION(policyId),
        allocationConfig
      );
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        policyId,
        metadata: {
          timestamp: new Date().toISOString(),
          totalBandwidth: allocationConfig.total_bandwidth,
          allocationsCount: allocationConfig.allocations?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'configureBandwidthAllocation', { policyId, allocationConfig });
    }
  }

  /**
   * ===========================================
   * WEBSOCKET TEMPS RÉEL
   * ===========================================
   */

  /**
   * Connecte au WebSocket QoS pour les mises à jour temps réel
   */
  connectRealtimeWebSocket(callbacks = {}) {
    if (this.realtimeSocket) {
      return this.realtimeSocket;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/qos/`;

    this.realtimeSocket = new WebSocket(wsUrl);
    this.stats.websocketConnections++;

    this.realtimeSocket.onopen = () => {
      console.log('QoS Realtime WebSocket connected');
      if (callbacks.onOpen) callbacks.onOpen();
    };

    this.realtimeSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.type) {
          case 'policy_update':
            if (callbacks.onPolicyUpdate) {
              callbacks.onPolicyUpdate(data.data);
            }
            break;
          case 'performance_metrics':
            if (callbacks.onPerformanceUpdate) {
              callbacks.onPerformanceUpdate(data.data);
            }
            break;
          case 'sla_alert':
            if (callbacks.onSLAAlert) {
              callbacks.onSLAAlert(data.data);
            }
            break;
          case 'infrastructure_status':
            if (callbacks.onInfrastructureUpdate) {
              callbacks.onInfrastructureUpdate(data.data);
            }
            break;
          case 'error':
            console.error('QoS WebSocket error:', data.message);
            if (callbacks.onError) callbacks.onError(data.message);
            break;
        }
      } catch (error) {
        console.error('Error parsing QoS WebSocket message:', error);
      }
    };

    this.realtimeSocket.onclose = () => {
      console.log('QoS Realtime WebSocket disconnected');
      this.realtimeSocket = null;
      if (callbacks.onClose) callbacks.onClose();
    };

    this.realtimeSocket.onerror = (error) => {
      console.error('QoS Realtime WebSocket error:', error);
      if (callbacks.onError) callbacks.onError(error);
    };

    return this.realtimeSocket;
  }

  /**
   * Envoie une commande via WebSocket
   */
  sendRealtimeCommand(command, data = {}) {
    if (!this.realtimeSocket || this.realtimeSocket.readyState !== WebSocket.OPEN) {
      console.error('QoS Realtime WebSocket not connected');
      return false;
    }

    try {
      this.realtimeSocket.send(JSON.stringify({
        command,
        ...data
      }));
      return true;
    } catch (error) {
      console.error('Error sending QoS WebSocket command:', error);
      return false;
    }
  }

  /**
   * Déconnecte le WebSocket temps réel
   */
  disconnectRealtimeWebSocket() {
    if (this.realtimeSocket) {
      this.realtimeSocket.close();
      this.realtimeSocket = null;
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

  clearCacheByPattern(pattern) {
    for (const [key] of this.cache) {
      if (key.includes(pattern)) {
        this.cache.delete(key);
      }
    }
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

    // Classification des erreurs spécifiques au QoS
    if (error.response?.status === 404) {
      errorInfo.error.type = 'QOS_NOT_FOUND';
      errorInfo.error.userMessage = 'Politique ou ressource QoS non trouvée.';
    } else if (error.response?.status === 403) {
      errorInfo.error.type = 'QOS_ACCESS_DENIED';
      errorInfo.error.userMessage = 'Accès refusé à cette ressource QoS.';
    } else if (error.response?.status === 409) {
      errorInfo.error.type = 'QOS_CONFLICT';
      errorInfo.error.userMessage = 'Conflit lors de l\'application de la politique QoS.';
    } else if (error.response?.status >= 500) {
      errorInfo.error.type = 'QOS_SERVER_ERROR';
      errorInfo.error.userMessage = 'Erreur serveur lors de l\'opération QoS.';
    } else {
      errorInfo.error.type = 'QOS_UNKNOWN_ERROR';
      errorInfo.error.userMessage = 'Erreur inattendue lors de l\'opération QoS.';
    }

    console.error(`[QoS Service Error] ${operation}:`, errorInfo);
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
      isRealtimeConnected: this.realtimeSocket?.readyState === WebSocket.OPEN
    };
  }

  /**
   * Test de connectivité
   */
  async testConnection() {
    try {
      const startTime = Date.now();
      const response = await this.getUnifiedStatus();
      
      return {
        success: response.success,
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
const qosService = new QoSService();

export default qosService;