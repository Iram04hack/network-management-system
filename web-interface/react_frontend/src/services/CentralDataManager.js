/**
 * CentralDataManager.js - Gestionnaire centralisé des données
 * Version d'urgence pour corriger la page blanche
 */

import { getEssentialStats, systemMetrics, equipmentsList, projectsList, systemAlerts } from './UnifiedApiData.js';

class CentralDataManager {
  constructor() {
    this.cache = new Map();
    this.lastUpdates = new Map();
    this.cacheTimeout = 30000; // 30 secondes
    
    console.log('[CentralDataManager] Service initialisé');
  }

  async getDashboardData(forceRefresh = false) {
    try {
      const stats = getEssentialStats();
      return {
        success: true,
        data: {
          system_health: {
            overall_status: stats.operational ? 'healthy' : 'warning',
            services_count: stats.services.totalServices,
            healthy_services: stats.services.healthyServices,
            cpu_usage: systemMetrics.cpu.current,
            memory_usage: systemMetrics.memory.current,
            disk_usage: systemMetrics.disk.current
          },
          network_summary: {
            total_devices: stats.systems.totalEquipments,
            online_devices: stats.systems.activeEquipments,
            health_percentage: stats.systems.healthPercentage
          },
          alerts_summary: {
            total: stats.alerts.totalAlerts,
            critical: stats.alerts.criticalAlerts,
            warning: stats.alerts.warningAlerts
          }
        },
        fromCache: false,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('[CentralDataManager] Erreur getDashboardData:', error);
      return { success: false, error: error.message };
    }
  }

  async getEquipmentData(forceRefresh = false) {
    try {
      return {
        success: true,
        data: {
          devices: equipmentsList,
          total_count: equipmentsList.length,
          online_count: equipmentsList.filter(eq => eq.status === 'online').length
        },
        fromCache: false,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('[CentralDataManager] Erreur getEquipmentData:', error);
      return { success: false, error: error.message };
    }
  }

  async getGNS3Data(forceRefresh = false) {
    try {
      return {
        success: true,
        data: {
          projects: projectsList,
          servers: [{ id: 'srv-1', name: 'GNS3 Server', status: 'running' }],
          nodes: []
        },
        fromCache: false,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('[CentralDataManager] Erreur getGNS3Data:', error);
      return { success: false, error: error.message };
    }
  }

  async getMonitoringData(forceRefresh = false) {
    try {
      return {
        success: true,
        data: {
          alerts: systemAlerts,
          metrics: [
            { name: 'cpu', value: systemMetrics.cpu.current, unit: '%' },
            { name: 'memory', value: systemMetrics.memory.current, unit: '%' },
            { name: 'disk', value: systemMetrics.disk.current, unit: '%' }
          ],
          notifications: []
        },
        fromCache: false,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('[CentralDataManager] Erreur getMonitoringData:', error);
      return { success: false, error: error.message };
    }
  }

  async getQoSData(forceRefresh = false) {
    try {
      return {
        success: true,
        data: {
          policies: [],
          trafficClasses: [],
          classifiers: [],
          interfacePolicies: [],
          statistics: []
        },
        fromCache: false,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      console.error('[CentralDataManager] Erreur getQoSData:', error);
      return { success: false, error: error.message };
    }
  }

  async syncModuleData(module) {
    console.log(`[CentralDataManager] Synchronisation du module: ${module}`);
    return { success: true, module, timestamp: new Date().toISOString() };
  }

  invalidateCache(module = null) {
    if (module) {
      this.cache.delete(module);
    } else {
      this.cache.clear();
    }
    console.log('[CentralDataManager] Cache invalidé:', module || 'tous les modules');
  }

  async testConnectivity() {
    return { success: true, message: 'Service de données mockées - toujours disponible' };
  }

  getStats() {
    return {
      cacheSize: this.cache.size,
      lastActivity: new Date().toISOString()
    };
  }

  getHealthStatus() {
    return {
      healthy: true,
      message: 'Service de données mockées fonctionnel'
    };
  }
}

const centralDataManager = new CentralDataManager();
export default centralDataManager;