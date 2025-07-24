/**
 * Service GNS3 Integration - Intégration avec le module gns3_integration backend
 * Gestion des serveurs GNS3, projets, nœuds, liens et workflows
 */

import apiClient from '../api/client.js';

/**
 * Base URLs pour le module gns3_integration
 */
const GNS3_BASE = '/api/gns3_integration/api';

/**
 * Endpoints du module gns3_integration
 */
export const GNS3_ENDPOINTS = {
  // Serveurs GNS3
  SERVERS: `${GNS3_BASE}/servers/`,
  SERVER_DETAIL: (serverId) => `${GNS3_BASE}/servers/${serverId}/`,
  SERVER_TEST: (serverId) => `${GNS3_BASE}/servers/${serverId}/test/`,
  SERVER_STATUS: (serverId) => `${GNS3_BASE}/servers/${serverId}/status/`,
  
  // Projets GNS3
  PROJECTS: `${GNS3_BASE}/projects/`,
  PROJECT_DETAIL: (projectId) => `${GNS3_BASE}/projects/${projectId}/`,
  PROJECT_START: (projectId) => `${GNS3_BASE}/projects/${projectId}/start/`,
  PROJECT_STOP: (projectId) => `${GNS3_BASE}/projects/${projectId}/stop/`,
  PROJECT_CLOSE: (projectId) => `${GNS3_BASE}/projects/${projectId}/close/`,
  PROJECT_NODES: (projectId) => `${GNS3_BASE}/projects/${projectId}/nodes/`,
  PROJECT_LINKS: (projectId) => `${GNS3_BASE}/projects/${projectId}/links/`,
  PROJECT_EXPORT: (projectId) => `${GNS3_BASE}/projects/${projectId}/export/`,
  PROJECT_IMPORT: `${GNS3_BASE}/projects/import/`,
  
  // Nœuds
  NODES: `${GNS3_BASE}/nodes/`,
  NODE_DETAIL: (nodeId) => `${GNS3_BASE}/nodes/${nodeId}/`,
  NODE_START: (nodeId) => `${GNS3_BASE}/nodes/${nodeId}/start/`,
  NODE_STOP: (nodeId) => `${GNS3_BASE}/nodes/${nodeId}/stop/`,
  NODE_SUSPEND: (nodeId) => `${GNS3_BASE}/nodes/${nodeId}/suspend/`,
  NODE_RELOAD: (nodeId) => `${GNS3_BASE}/nodes/${nodeId}/reload/`,
  
  // Liens
  LINKS: `${GNS3_BASE}/links/`,
  LINK_DETAIL: (linkId) => `${GNS3_BASE}/links/${linkId}/`,
  LINK_START: (linkId) => `${GNS3_BASE}/links/${linkId}/start/`,
  LINK_STOP: (linkId) => `${GNS3_BASE}/links/${linkId}/stop/`,
  
  // Templates
  TEMPLATES: `${GNS3_BASE}/templates/`,
  TEMPLATE_DETAIL: (templateId) => `${GNS3_BASE}/templates/${templateId}/`,
  
  // Snapshots
  SNAPSHOTS: `${GNS3_BASE}/snapshots/`,
  SNAPSHOT_DETAIL: (snapshotId) => `${GNS3_BASE}/snapshots/${snapshotId}/`,
  SNAPSHOT_RESTORE: (snapshotId) => `${GNS3_BASE}/snapshots/${snapshotId}/restore/`,
  
  // Scripts
  SCRIPTS: `${GNS3_BASE}/scripts/`,
  SCRIPT_DETAIL: (scriptId) => `${GNS3_BASE}/scripts/${scriptId}/`,
  SCRIPT_EXECUTIONS: `${GNS3_BASE}/script-executions/`,
  SCRIPT_EXECUTION_DETAIL: (executionId) => `${GNS3_BASE}/script-executions/${executionId}/`,
  
  // Workflows
  WORKFLOWS: `${GNS3_BASE}/workflows/`,
  WORKFLOW_DETAIL: (workflowId) => `${GNS3_BASE}/workflows/${workflowId}/`,
  WORKFLOW_EXECUTIONS: `${GNS3_BASE}/workflow-executions/`,
  WORKFLOW_EXECUTION_DETAIL: (executionId) => `${GNS3_BASE}/workflow-executions/${executionId}/`,
};

/**
 * Types de nœuds GNS3 disponibles
 */
export const NODE_TYPES = {
  DYNAMIPS: 'dynamips',
  IOU: 'iou',
  QEMU: 'qemu',
  VIRTUALBOX: 'virtualbox',
  VMWARE: 'vmware',
  DOCKER: 'docker',
  CLOUD: 'cloud',
  NAT: 'nat',
  ETHERNET_HUB: 'ethernet_hub',
  ETHERNET_SWITCH: 'ethernet_switch',
  FRAME_RELAY_SWITCH: 'frame_relay_switch',
  ATM_SWITCH: 'atm_switch'
};

/**
 * Statuts des projets GNS3
 */
export const PROJECT_STATUS = {
  OPENED: 'opened',
  CLOSED: 'closed',
  SUSPENDED: 'suspended'
};

/**
 * Service principal pour GNS3 Integration
 */
class GNS3Service {
  constructor() {
    this.apiClient = apiClient;
    
    // Cache pour les données fréquemment utilisées
    this.cache = new Map();
    this.cacheTimeout = 60000; // 1 minute
    
    // Statistiques du service
    this.stats = {
      totalRequests: 0,
      cacheHits: 0,
      cacheMisses: 0,
      lastRequestTime: null,
      serverConnections: 0,
      activeProjects: 0
    };
  }

  /**
   * ===========================================
   * GESTION DES SERVEURS GNS3
   * ===========================================
   */

  /**
   * Récupère tous les serveurs GNS3
   * GET /api/gns3_integration/api/servers/
   */
  async getServers(params = {}) {
    const cacheKey = `gns3_servers_${JSON.stringify(params)}`;
    
    if (this.isInCache(cacheKey)) {
      this.stats.cacheHits++;
      return this.getFromCache(cacheKey);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(GNS3_ENDPOINTS.SERVERS, { params });
      
      this.updateStats(startTime, true);
      
      const result = {
        success: true,
        data: response.data.results || response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalServers: response.data.count || response.data.length,
          activeServers: response.data.results ? 
            response.data.results.filter(s => s.is_active).length : 0
        }
      };
      
      this.setCache(cacheKey, result);
      this.stats.cacheMisses++;
      
      return result;
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getServers', { params });
    }
  }

  /**
   * Récupère un serveur GNS3 spécifique
   * GET /api/gns3_integration/api/servers/{id}/
   */
  async getServer(serverId) {
    if (!serverId) {
      return this.createValidationError('getServer', ['serverId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(GNS3_ENDPOINTS.SERVER_DETAIL(serverId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        serverId,
        metadata: {
          timestamp: new Date().toISOString(),
          serverUrl: `${response.data.protocol}://${response.data.host}:${response.data.port}`,
          isActive: response.data.is_active
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getServer', { serverId });
    }
  }

  /**
   * Crée un nouveau serveur GNS3
   * POST /api/gns3_integration/api/servers/
   */
  async createServer(serverData) {
    const requiredFields = ['name', 'host', 'port'];
    const validation = this.validateRequiredFields(serverData, requiredFields);
    if (!validation.isValid) {
      return this.createValidationError('createServer', validation.missingFields);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(GNS3_ENDPOINTS.SERVERS, serverData);
      
      this.updateStats(startTime, true);
      
      // Invalider le cache des serveurs
      this.clearCacheByPattern('gns3_servers_');
      
      return {
        success: true,
        data: response.data,
        serverId: response.data.id,
        metadata: {
          timestamp: new Date().toISOString(),
          serverUrl: `${serverData.protocol || 'http'}://${serverData.host}:${serverData.port}`
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'createServer', { serverData });
    }
  }

  /**
   * Met à jour un serveur GNS3
   * PUT /api/gns3_integration/api/servers/{id}/
   */
  async updateServer(serverId, serverData) {
    if (!serverId) {
      return this.createValidationError('updateServer', ['serverId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.put(GNS3_ENDPOINTS.SERVER_DETAIL(serverId), serverData);
      
      this.updateStats(startTime, true);
      
      // Invalider le cache
      this.clearCacheByPattern('gns3_servers_');
      
      return {
        success: true,
        data: response.data,
        serverId,
        metadata: {
          timestamp: new Date().toISOString(),
          updatedFields: Object.keys(serverData)
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'updateServer', { serverId, serverData });
    }
  }

  /**
   * Supprime un serveur GNS3
   * DELETE /api/gns3_integration/api/servers/{id}/
   */
  async deleteServer(serverId) {
    if (!serverId) {
      return this.createValidationError('deleteServer', ['serverId']);
    }

    try {
      const startTime = Date.now();
      await this.apiClient.delete(GNS3_ENDPOINTS.SERVER_DETAIL(serverId));
      
      this.updateStats(startTime, true);
      
      // Invalider le cache
      this.clearCacheByPattern('gns3_servers_');
      
      return {
        success: true,
        serverId,
        metadata: {
          timestamp: new Date().toISOString(),
          action: 'deleted'
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'deleteServer', { serverId });
    }
  }

  /**
   * Teste la connexion à un serveur GNS3
   * POST /api/gns3_integration/api/servers/{id}/test/
   */
  async testServer(serverId) {
    if (!serverId) {
      return this.createValidationError('testServer', ['serverId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(GNS3_ENDPOINTS.SERVER_TEST(serverId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        serverId,
        metadata: {
          timestamp: new Date().toISOString(),
          testPassed: response.data.success || false,
          responseTime: Date.now() - startTime
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'testServer', { serverId });
    }
  }

  /**
   * ===========================================
   * GESTION DES PROJETS GNS3
   * ===========================================
   */

  /**
   * Récupère tous les projets GNS3
   * GET /api/gns3_integration/api/projects/
   */
  async getProjects(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(GNS3_ENDPOINTS.PROJECTS, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data.results || response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalProjects: response.data.count || response.data.length,
          openedProjects: response.data.results ? 
            response.data.results.filter(p => p.status === 'opened').length : 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getProjects', { params });
    }
  }

  /**
   * Récupère un projet GNS3 spécifique
   * GET /api/gns3_integration/api/projects/{id}/
   */
  async getProject(projectId) {
    if (!projectId) {
      return this.createValidationError('getProject', ['projectId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(GNS3_ENDPOINTS.PROJECT_DETAIL(projectId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        projectId,
        metadata: {
          timestamp: new Date().toISOString(),
          status: response.data.status,
          nodesCount: response.data.nodes?.length || 0,
          linksCount: response.data.links?.length || 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getProject', { projectId });
    }
  }

  /**
   * Crée un nouveau projet GNS3
   * POST /api/gns3_integration/api/projects/
   */
  async createProject(projectData) {
    const requiredFields = ['name', 'server'];
    const validation = this.validateRequiredFields(projectData, requiredFields);
    if (!validation.isValid) {
      return this.createValidationError('createProject', validation.missingFields);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(GNS3_ENDPOINTS.PROJECTS, projectData);
      
      this.updateStats(startTime, true);
      this.stats.activeProjects++;
      
      return {
        success: true,
        data: response.data,
        projectId: response.data.id || response.data.project_id,
        metadata: {
          timestamp: new Date().toISOString(),
          projectName: projectData.name,
          serverId: projectData.server
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'createProject', { projectData });
    }
  }

  /**
   * Met à jour un projet GNS3
   * PUT /api/gns3_integration/api/projects/{id}/
   */
  async updateProject(projectId, projectData) {
    if (!projectId) {
      return this.createValidationError('updateProject', ['projectId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.put(GNS3_ENDPOINTS.PROJECT_DETAIL(projectId), projectData);
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        projectId,
        metadata: {
          timestamp: new Date().toISOString(),
          updatedFields: Object.keys(projectData)
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'updateProject', { projectId, projectData });
    }
  }

  /**
   * Supprime un projet GNS3
   * DELETE /api/gns3_integration/api/projects/{id}/
   */
  async deleteProject(projectId) {
    if (!projectId) {
      return this.createValidationError('deleteProject', ['projectId']);
    }

    try {
      const startTime = Date.now();
      await this.apiClient.delete(GNS3_ENDPOINTS.PROJECT_DETAIL(projectId));
      
      this.updateStats(startTime, true);
      this.stats.activeProjects = Math.max(0, this.stats.activeProjects - 1);
      
      return {
        success: true,
        projectId,
        metadata: {
          timestamp: new Date().toISOString(),
          action: 'deleted'
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'deleteProject', { projectId });
    }
  }

  /**
   * Actions sur les projets (start, stop, close)
   */
  async startProject(projectId) {
    return this._projectAction(projectId, 'start');
  }

  async stopProject(projectId) {
    return this._projectAction(projectId, 'stop');
  }

  async closeProject(projectId) {
    return this._projectAction(projectId, 'close');
  }

  async _projectAction(projectId, action) {
    if (!projectId) {
      return this.createValidationError(`${action}Project`, ['projectId']);
    }

    try {
      const startTime = Date.now();
      const endpoint = GNS3_ENDPOINTS[`PROJECT_${action.toUpperCase()}`](projectId);
      const response = await this.apiClient.post(endpoint);
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        projectId,
        action,
        metadata: {
          timestamp: new Date().toISOString(),
          newStatus: response.data.status || action
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, `${action}Project`, { projectId, action });
    }
  }

  /**
   * ===========================================
   * GESTION DES NŒUDS
   * ===========================================
   */

  /**
   * Récupère tous les nœuds
   * GET /api/gns3_integration/api/nodes/
   */
  async getNodes(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(GNS3_ENDPOINTS.NODES, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data.results || response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalNodes: response.data.count || response.data.length,
          runningNodes: response.data.results ? 
            response.data.results.filter(n => n.status === 'started').length : 0
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getNodes', { params });
    }
  }

  /**
   * Récupère les nœuds d'un projet
   * GET /api/gns3_integration/api/projects/{id}/nodes/
   */
  async getProjectNodes(projectId) {
    if (!projectId) {
      return this.createValidationError('getProjectNodes', ['projectId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(GNS3_ENDPOINTS.PROJECT_NODES(projectId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        projectId,
        metadata: {
          timestamp: new Date().toISOString(),
          nodesCount: response.data.length || 0,
          nodeTypes: [...new Set(response.data.map(n => n.node_type))]
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getProjectNodes', { projectId });
    }
  }

  /**
   * Actions sur les nœuds (start, stop, suspend, reload)
   */
  async startNode(nodeId) {
    return this._nodeAction(nodeId, 'start');
  }

  async stopNode(nodeId) {
    return this._nodeAction(nodeId, 'stop');
  }

  async suspendNode(nodeId) {
    return this._nodeAction(nodeId, 'suspend');
  }

  async reloadNode(nodeId) {
    return this._nodeAction(nodeId, 'reload');
  }

  async _nodeAction(nodeId, action) {
    if (!nodeId) {
      return this.createValidationError(`${action}Node`, ['nodeId']);
    }

    try {
      const startTime = Date.now();
      const endpoint = GNS3_ENDPOINTS[`NODE_${action.toUpperCase()}`](nodeId);
      const response = await this.apiClient.post(endpoint);
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        nodeId,
        action,
        metadata: {
          timestamp: new Date().toISOString(),
          newStatus: response.data.status || action
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, `${action}Node`, { nodeId, action });
    }
  }

  /**
   * ===========================================
   * GESTION DES SNAPSHOTS
   * ===========================================
   */

  /**
   * Récupère tous les snapshots
   * GET /api/gns3_integration/api/snapshots/
   */
  async getSnapshots(params = {}) {
    try {
      const startTime = Date.now();
      const response = await this.apiClient.get(GNS3_ENDPOINTS.SNAPSHOTS, { params });
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data.results || response.data,
        metadata: {
          timestamp: new Date().toISOString(),
          totalSnapshots: response.data.count || response.data.length
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'getSnapshots', { params });
    }
  }

  /**
   * Crée un snapshot
   * POST /api/gns3_integration/api/snapshots/
   */
  async createSnapshot(snapshotData) {
    const requiredFields = ['name', 'project'];
    const validation = this.validateRequiredFields(snapshotData, requiredFields);
    if (!validation.isValid) {
      return this.createValidationError('createSnapshot', validation.missingFields);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(GNS3_ENDPOINTS.SNAPSHOTS, snapshotData);
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        snapshotId: response.data.id,
        metadata: {
          timestamp: new Date().toISOString(),
          snapshotName: snapshotData.name,
          projectId: snapshotData.project
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'createSnapshot', { snapshotData });
    }
  }

  /**
   * Restaure un snapshot
   * POST /api/gns3_integration/api/snapshots/{id}/restore/
   */
  async restoreSnapshot(snapshotId) {
    if (!snapshotId) {
      return this.createValidationError('restoreSnapshot', ['snapshotId']);
    }

    try {
      const startTime = Date.now();
      const response = await this.apiClient.post(GNS3_ENDPOINTS.SNAPSHOT_RESTORE(snapshotId));
      
      this.updateStats(startTime, true);
      
      return {
        success: true,
        data: response.data,
        snapshotId,
        metadata: {
          timestamp: new Date().toISOString(),
          action: 'restored'
        }
      };
    } catch (error) {
      this.updateStats(Date.now(), false);
      return this.handleError(error, 'restoreSnapshot', { snapshotId });
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
    for (const key of this.cache.keys()) {
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

    // Classification des erreurs spécifiques à GNS3
    if (error.response?.status === 404) {
      errorInfo.error.type = 'GNS3_RESOURCE_NOT_FOUND';
      errorInfo.error.userMessage = 'Ressource GNS3 non trouvée.';
    } else if (error.response?.status === 409) {
      errorInfo.error.type = 'GNS3_CONFLICT';
      errorInfo.error.userMessage = 'Conflit avec l\'état actuel du projet ou serveur GNS3.';
    } else if (error.response?.status === 503) {
      errorInfo.error.type = 'GNS3_SERVER_UNAVAILABLE';
      errorInfo.error.userMessage = 'Serveur GNS3 indisponible.';
    } else if (error.response?.status >= 500) {
      errorInfo.error.type = 'GNS3_SERVER_ERROR';
      errorInfo.error.userMessage = 'Erreur serveur GNS3.';
    } else {
      errorInfo.error.type = 'GNS3_UNKNOWN_ERROR';
      errorInfo.error.userMessage = 'Erreur inattendue lors de l\'opération GNS3.';
    }

    console.error(`[GNS3 Service Error] ${operation}:`, errorInfo);
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

  /**
   * Test de connectivité
   */
  async testConnection() {
    try {
      const startTime = Date.now();
      const response = await this.getServers({ limit: 1 });
      
      return {
        success: response.success,
        responseTime: Date.now() - startTime,
        timestamp: new Date().toISOString(),
        serversAvailable: response.success ? response.data.length : 0
      };
    } catch (error) {
      return this.handleError(error, 'testConnection');
    }
  }
}

// Instance singleton du service
const gns3Service = new GNS3Service();

export default gns3Service;