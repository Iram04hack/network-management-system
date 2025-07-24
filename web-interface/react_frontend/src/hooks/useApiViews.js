/**
 * Hook personnalisé pour la gestion des API Views
 * Intégration avec le module api_views backend - Dashboard et vues agrégées
 */

import { useCallback, useMemo, useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import apiViewsService from '../services/apiViewsService';

/**
 * Hook principal pour la gestion des API Views
 */
export const useApiViews = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [systemOverview, setSystemOverview] = useState(null);
  const [networkOverview, setNetworkOverview] = useState(null);
  const [topologyData, setTopologyData] = useState(null);
  const [devices, setDevices] = useState([]);
  const [currentDevice, setCurrentDevice] = useState(null);
  const [searchResults, setSearchResults] = useState(null);
  const [monitoringData, setMonitoringData] = useState(null);
  
  const [loading, setLoading] = useState({
    dashboard: false,
    system: false,
    network: false,
    topology: false,
    devices: false,
    search: false,
    monitoring: false,
    discovery: false
  });
  
  const [error, setError] = useState(null);
  const [discoveryStatus, setDiscoveryStatus] = useState(null);

  // Actions avec useCallback pour stabilité des références
  const fetchDashboardOverview = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, dashboard: true }));
    setError(null);

    try {
      const result = await apiViewsService.getDashboardOverview(params);
      if (result.success) {
        setDashboardData(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, dashboard: false }));
    }
  }, []);

  const fetchSystemOverview = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, system: true }));
    setError(null);

    try {
      const result = await apiViewsService.getSystemOverview(params);
      if (result.success) {
        setSystemOverview(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, system: false }));
    }
  }, []);

  const fetchNetworkOverview = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, network: true }));
    setError(null);

    try {
      const result = await apiViewsService.getNetworkOverview(params);
      if (result.success) {
        setNetworkOverview(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, network: false }));
    }
  }, []);

  const startTopologyDiscovery = useCallback(async (discoveryParams) => {
    setLoading(prev => ({ ...prev, discovery: true }));
    setError(null);

    try {
      const result = await apiViewsService.startTopologyDiscovery(discoveryParams);
      if (result.success) {
        setDiscoveryStatus({
          discoveryId: result.discoveryId,
          status: 'started',
          networkId: discoveryParams.network_id
        });
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, discovery: false }));
    }
  }, []);

  const getTopologyDiscoveryStatus = useCallback(async (discoveryId) => {
    setLoading(prev => ({ ...prev, topology: true }));
    setError(null);

    try {
      const result = await apiViewsService.getTopologyDiscoveryStatus(discoveryId);
      if (result.success) {
        setDiscoveryStatus(prev => ({
          ...prev,
          ...result.data,
          discoveryId: result.discoveryId
        }));
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, topology: false }));
    }
  }, []);

  const getTopologyData = useCallback(async (networkId, params = {}) => {
    setLoading(prev => ({ ...prev, topology: true }));
    setError(null);

    try {
      const result = await apiViewsService.getTopologyData(networkId, params);
      if (result.success) {
        setTopologyData(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, topology: false }));
    }
  }, []);

  const fetchDevices = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, devices: true }));
    setError(null);

    try {
      const result = await apiViewsService.getDevices(params);
      if (result.success) {
        setDevices(result.data.results || result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, devices: false }));
    }
  }, []);

  const getDevice = useCallback(async (deviceId) => {
    setLoading(prev => ({ ...prev, devices: true }));
    setError(null);

    try {
      const result = await apiViewsService.getDevice(deviceId);
      if (result.success) {
        setCurrentDevice(result.data);
        
        // Mettre à jour aussi dans la liste si elle existe
        setDevices(prev => {
          const index = prev.findIndex(device => device.id === deviceId);
          if (index !== -1) {
            const updated = [...prev];
            updated[index] = result.data;
            return updated;
          }
          return prev;
        });
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, devices: false }));
    }
  }, []);

  const performGlobalSearch = useCallback(async (query, params = {}) => {
    setLoading(prev => ({ ...prev, search: true }));
    setError(null);

    try {
      const result = await apiViewsService.globalSearch(query, params);
      if (result.success) {
        setSearchResults(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, search: false }));
    }
  }, []);

  const fetchMonitoringMetrics = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, monitoring: true }));
    setError(null);

    try {
      const result = await apiViewsService.getMonitoringMetrics(params);
      if (result.success) {
        setMonitoringData(prev => ({
          ...prev,
          metrics: result.data
        }));
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, monitoring: false }));
    }
  }, []);

  const fetchMonitoringAlerts = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, monitoring: true }));
    setError(null);

    try {
      const result = await apiViewsService.getMonitoringAlerts(params);
      if (result.success) {
        setMonitoringData(prev => ({
          ...prev,
          alerts: result.data
        }));
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, monitoring: false }));
    }
  }, []);

  // Fonctions utilitaires mémorisées
  const utils = useMemo(() => ({
    // Filtrer les appareils par type
    getDevicesByType: (deviceType) => 
      devices.filter(device => device.device_type === deviceType),
    
    // Obtenir les appareils en ligne
    getOnlineDevices: () => 
      devices.filter(device => device.status === 'online'),
    
    // Obtenir les appareils avec problèmes
    getProblematicDevices: () => 
      devices.filter(device => device.status !== 'online'),
    
    // Statistiques du système
    getSystemStats: () => ({
      devicesTotal: devices.length,
      devicesOnline: devices.filter(d => d.status === 'online').length,
      deviceTypes: [...new Set(devices.map(d => d.device_type))],
      lastUpdate: new Date().toISOString(),
      systemHealth: systemOverview?.overall_status || 'unknown',
      networkHealth: networkOverview?.health?.status || 'unknown'
    }),
    
    // Rechercher un appareil par nom ou IP
    searchDevices: (query) => 
      devices.filter(device => 
        device.name?.toLowerCase().includes(query.toLowerCase()) ||
        device.ip_address?.includes(query) ||
        device.device_type?.toLowerCase().includes(query.toLowerCase())
      ),
    
    // Obtenir les métriques de topologie
    getTopologyStats: () => topologyData ? {
      nodesCount: topologyData.nodes?.length || 0,
      edgesCount: topologyData.edges?.length || 0,
      lastUpdate: topologyData.metadata?.last_update,
      networkId: topologyData.network_id
    } : null,
    
    // Obtenir les statistiques d'alertes
    getAlertsStats: () => monitoringData?.alerts ? {
      total: monitoringData.alerts.length,
      critical: monitoringData.alerts.filter(a => a.severity === 'critical').length,
      warning: monitoringData.alerts.filter(a => a.severity === 'warning').length,
      active: monitoringData.alerts.filter(a => a.status === 'active').length
    } : null
  }), [devices, systemOverview, networkOverview, topologyData, monitoringData]);

  // Actions regroupées pour réutilisation
  const actions = useMemo(() => ({
    fetchDashboardOverview,
    fetchSystemOverview,
    fetchNetworkOverview,
    startTopologyDiscovery,
    getTopologyDiscoveryStatus,
    getTopologyData,
    fetchDevices,
    getDevice,
    performGlobalSearch,
    fetchMonitoringMetrics,
    fetchMonitoringAlerts
  }), [
    fetchDashboardOverview,
    fetchSystemOverview,
    fetchNetworkOverview,
    startTopologyDiscovery,
    getTopologyDiscoveryStatus,
    getTopologyData,
    fetchDevices,
    getDevice,
    performGlobalSearch,
    fetchMonitoringMetrics,
    fetchMonitoringAlerts
  ]);

  // Callbacks optimisés
  const refreshAllData = useCallback(async () => {
    const promises = [
      actions.fetchDashboardOverview(),
      actions.fetchSystemOverview(),
      actions.fetchNetworkOverview(),
      actions.fetchDevices()
    ];
    
    const results = await Promise.allSettled(promises);
    return results;
  }, [actions]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearCurrentDevice = useCallback(() => {
    setCurrentDevice(null);
  }, []);

  const clearSearchResults = useCallback(() => {
    setSearchResults(null);
  }, []);

  return {
    // État des données
    dashboardData,
    systemOverview,
    networkOverview,
    topologyData,
    devices,
    currentDevice,
    searchResults,
    monitoringData,
    discoveryStatus,
    
    // État de chargement et erreurs
    loading,
    error,
    isLoading: Object.values(loading).some(l => l),

    // Actions principales
    fetchDashboardOverview,
    fetchSystemOverview,
    fetchNetworkOverview,
    startTopologyDiscovery,
    getTopologyDiscoveryStatus,
    getTopologyData,
    fetchDevices,
    getDevice,
    performGlobalSearch,
    fetchMonitoringMetrics,
    fetchMonitoringAlerts,

    // Utilitaires
    ...utils,

    // Callbacks optimisés
    refreshAllData,
    clearError,
    clearCurrentDevice,
    clearSearchResults,
  };
};

/**
 * Hook pour surveiller en temps réel la découverte de topologie
 */
export const useTopologyDiscoveryMonitor = (discoveryId, interval = 5000) => {
  const [status, setStatus] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  const startMonitoring = useCallback(() => {
    if (!discoveryId) return null;
    
    setIsMonitoring(true);
    
    const checkStatus = async () => {
      try {
        const result = await apiViewsService.getTopologyDiscoveryStatus(discoveryId);
        if (result.success) {
          setStatus(result.data);
          
          // Arrêter la surveillance si la découverte est terminée
          if (result.data.status === 'completed' || result.data.status === 'failed') {
            setIsMonitoring(false);
            return;
          }
        }
      } catch (error) {
        console.error('Error monitoring topology discovery:', error);
      }
    };

    // Première vérification immédiate
    checkStatus();
    
    // Puis surveillance périodique
    const intervalId = setInterval(checkStatus, interval);
    
    return () => {
      clearInterval(intervalId);
      setIsMonitoring(false);
    };
  }, [discoveryId, interval]);

  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false);
  }, []);

  return {
    status,
    isMonitoring,
    startMonitoring,
    stopMonitoring
  };
};

/**
 * Hook pour la surveillance des métriques en temps réel
 */
export const useRealTimeMonitoring = (interval = 30000) => {
  const [metrics, setMetrics] = useState(null);
  const [alerts, setAlerts] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  const startMonitoring = useCallback(() => {
    setIsMonitoring(true);
    
    const fetchMonitoringData = async () => {
      try {
        const [metricsResult, alertsResult] = await Promise.allSettled([
          apiViewsService.getMonitoringMetrics(),
          apiViewsService.getMonitoringAlerts()
        ]);
        
        if (metricsResult.status === 'fulfilled' && metricsResult.value.success) {
          setMetrics(metricsResult.value.data);
        }
        
        if (alertsResult.status === 'fulfilled' && alertsResult.value.success) {
          setAlerts(alertsResult.value.data);
        }
      } catch (error) {
        console.error('Error monitoring real-time data:', error);
      }
    };

    // Première récupération immédiate
    fetchMonitoringData();
    
    // Puis surveillance périodique
    const intervalId = setInterval(fetchMonitoringData, interval);
    
    return () => {
      clearInterval(intervalId);
      setIsMonitoring(false);
    };
  }, [interval]);

  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false);
  }, []);

  return {
    metrics,
    alerts,
    isMonitoring,
    startMonitoring,
    stopMonitoring
  };
};

export default useApiViews;