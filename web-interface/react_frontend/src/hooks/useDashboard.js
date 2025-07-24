/**
 * useDashboard - Hook pour la gestion des dashboards avec données simulées
 * Version restaurée avec données mockées selon le document d'architecture
 */

import { useState, useEffect, useCallback } from 'react';

// Hook personnalisé pour la gestion des dashboards avec données mockées
export const useDashboard = () => {
  // États principaux
  const [dashboardData, setDashboardData] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [networkSummary, setNetworkSummary] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  
  // États pour compatibilité avec l'ancien code
  const [dashboards, setDashboards] = useState([]);
  const [widgets, setWidgets] = useState([]);
  const [isAuthenticated, setIsAuthenticated] = useState(true);

  // Configuration auto-refresh
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 secondes par défaut
  
  // Données mockées pour les métriques système
  const mockSystemHealth = {
    status: 'healthy',
    cpu: 45,
    memory: 62,
    disk: 78,
    network: 'stable',
    uptime: 99.7,
    services: {
      database: 'online',
      webserver: 'online',
      monitoring: 'online'
    },
    lastUpdate: new Date().toISOString()
  };

  // Données mockées pour le résumé réseau
  const mockNetworkSummary = {
    totalDevices: 24,
    onlineDevices: 22,
    offlineDevices: 2,
    warningDevices: 1,
    totalInterfaces: 48,
    activeInterfaces: 28,
    averageCpuUsage: 24.2,
    averageMemoryUsage: 38.0,
    networkHealth: 78,
    topology: {
      nodes: 24,
      links: 45,
      lastUpdate: new Date().toISOString()
    }
  };

  // Données mockées pour les alertes
  const mockAlerts = [
    {
      id: 'alert-1',
      type: 'critical',
      title: 'CPU élevé sur Server-01',
      message: 'Utilisation CPU à 95% depuis 10 minutes',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      equipment: 'Server-01',
      status: 'active',
      severity: 'high'
    },
    {
      id: 'alert-2',
      type: 'warning',
      title: 'Mémoire limitée',
      message: 'Utilisation mémoire à 85% sur plusieurs serveurs',
      timestamp: new Date(Date.now() - 1200000).toISOString(),
      equipment: 'Infrastructure',
      status: 'acknowledged',
      severity: 'medium'
    },
    {
      id: 'alert-3',
      type: 'info',
      title: 'Maintenance programmée',
      message: 'Redémarrage planifié du switch principal',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      equipment: 'Network-Switch-01',
      status: 'scheduled',
      severity: 'low'
    }
  ];

  /**
   * Simule le chargement des données du dashboard
   */
  const fetchDashboardData = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      
      // Simulation d'un délai d'API
      await new Promise(resolve => setTimeout(resolve, 500));
      
      const mockData = {
        overview: {
          systemHealth: mockSystemHealth,
          networkSummary: mockNetworkSummary,
          alerts: mockAlerts,
          timestamp: new Date().toISOString()
        }
      };
      
      setDashboardData(mockData);
      setLastUpdate(new Date().toISOString());
      
      return { success: true, data: mockData };
      
    } catch (error) {
      console.error('Erreur lors du chargement du dashboard:', error);
      setError('Erreur de connexion au serveur');
      return { success: false, error };
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Simule le chargement des données de santé système
   */
  const fetchSystemHealth = useCallback(async (forceRefresh = false) => {
    try {
      // Simulation d'un délai d'API
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // Variation aléatoire des métriques pour simulation
      const updatedHealth = {
        ...mockSystemHealth,
        cpu: Math.max(0, Math.min(100, mockSystemHealth.cpu + (Math.random() - 0.5) * 10)),
        memory: Math.max(0, Math.min(100, mockSystemHealth.memory + (Math.random() - 0.5) * 8)),
        disk: Math.max(0, Math.min(100, mockSystemHealth.disk + (Math.random() - 0.5) * 2)),
        lastUpdate: new Date().toISOString()
      };
      
      setSystemHealth(updatedHealth);
      return { success: true, data: updatedHealth };
      
    } catch (error) {
      console.error('Erreur lors du chargement de la santé système:', error);
      return { success: false, error };
    }
  }, []);
  
  /**
   * Simule le chargement des données réseau
   */
  const fetchNetworkSummary = useCallback(async (forceRefresh = false) => {
    try {
      // Simulation d'un délai d'API
      await new Promise(resolve => setTimeout(resolve, 300));
      
      const updatedNetwork = {
        ...mockNetworkSummary,
        averageCpuUsage: Math.max(0, Math.min(100, mockNetworkSummary.averageCpuUsage + (Math.random() - 0.5) * 5)),
        averageMemoryUsage: Math.max(0, Math.min(100, mockNetworkSummary.averageMemoryUsage + (Math.random() - 0.5) * 3)),
        networkHealth: Math.max(0, Math.min(100, mockNetworkSummary.networkHealth + (Math.random() - 0.5) * 2))
      };
      
      setNetworkSummary(updatedNetwork);
      return { success: true, data: updatedNetwork };
      
    } catch (error) {
      console.error('Erreur lors du chargement du réseau:', error);
      return { success: false, error };
    }
  }, []);
  
  /**
   * Simule le chargement des alertes
   */
  const fetchAlerts = useCallback(async (forceRefresh = false) => {
    try {
      // Simulation d'un délai d'API
      await new Promise(resolve => setTimeout(resolve, 150));
      
      setAlerts(mockAlerts);
      return mockAlerts;
      
    } catch (error) {
      console.error('Erreur lors du chargement des alertes:', error);
      return [];
    }
  }, []);

  /**
   * Rafraîchit toutes les données en parallèle
   */
  const refreshAllData = useCallback(async (forceRefresh = false) => {
    try {
      setLoading(true);
      setError(null);
      
      // Exécuter toutes les requêtes en parallèle
      const [dashboardResult, healthResult, networkResult, alertsResult] = await Promise.allSettled([
        fetchDashboardData(forceRefresh),
        fetchSystemHealth(forceRefresh),
        fetchNetworkSummary(forceRefresh),
        fetchAlerts(forceRefresh)
      ]);
      
      // Vérifier les résultats
      const hasErrors = [
        dashboardResult,
        healthResult,
        networkResult,
        alertsResult
      ].some(result => result.status === 'rejected' || !result.value?.success);
      
      if (hasErrors) {
        console.warn('Certaines données n\'ont pas pu être chargées');
      }
      
      return !hasErrors;
      
    } catch (error) {
      console.error('Erreur lors du rafraîchissement:', error);
      setError('Erreur lors du rafraîchissement des données');
      return false;
    } finally {
      setLoading(false);
    }
  }, [fetchDashboardData, fetchSystemHealth, fetchNetworkSummary, fetchAlerts]);

  /**
   * Pour compatibilité avec l'ancien code - fetchDashboards
   */
  const fetchDashboards = useCallback(async () => {
    const result = await fetchDashboardData();
    if (result.success && result.data) {
      // Simuler une liste de dashboards pour compatibilité
      setDashboards([{
        id: 'main_dashboard',
        name: 'Dashboard Principal',
        data: result.data,
        last_updated: new Date().toISOString()
      }]);
    }
    return result;
  }, [fetchDashboardData]);

  /**
   * Pour compatibilité avec l'ancien code - fetchDashboard
   */
  const fetchDashboard = useCallback(async (id) => {
    if (id === 'main_dashboard' || !id) {
      const result = await fetchDashboardData();
      return result.success ? result.data : null;
    }
    return null;
  }, [fetchDashboardData]);

  /**
   * Pour compatibilité avec l'ancien code - fetchWidgets
   */
  const fetchWidgets = useCallback(async () => {
    // Les widgets sont définis localement, pas depuis l'API
    const defaultWidgets = [
      { id: 'network-status', type: 'network-status', name: 'Statut Réseau' },
      { id: 'system-health', type: 'system-health', name: 'Santé Système' },
      { id: 'alerts-list', type: 'alerts-list', name: 'Alertes Récentes' },
      { id: 'traffic-chart', type: 'traffic-chart', name: 'Graphique Trafic' }
    ];
    
    setWidgets(defaultWidgets);
    return defaultWidgets;
  }, []);

  // Fonctions stub pour compatibilité
  const createDashboard = useCallback(async (dashboardData) => {
    console.log('createDashboard avec données simulées');
    return null;
  }, []);

  const updateDashboard = useCallback(async (id, dashboardData) => {
    console.log('updateDashboard avec données simulées');
    return null;
  }, []);

  const deleteDashboard = useCallback(async (id) => {
    console.log('deleteDashboard avec données simulées');
    return false;
  }, []);

  const saveDashboard = useCallback(async (dashboardData) => {
    console.log('saveDashboard avec données simulées');
    return null;
  }, []);

  const loadDashboard = useCallback(async (id) => {
    return await fetchDashboard(id);
  }, [fetchDashboard]);

  const fetchShortcuts = useCallback(async () => {
    return [];
  }, []);

  const saveShortcuts = useCallback(async (shortcuts) => {
    return true;
  }, []);

  // Chargement initial des données
  useEffect(() => {
    refreshAllData(false);
    fetchWidgets();
  }, []);
  
  // Auto-refresh des données
  useEffect(() => {
    if (!autoRefresh || !refreshInterval) return;
    
    const interval = setInterval(() => {
      refreshAllData(false);
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, refreshAllData]);

  return {
    // États principaux
    dashboardData,
    systemHealth,
    networkSummary,
    alerts,
    loading,
    error,
    lastUpdate,
    
    // Configuration auto-refresh
    autoRefresh,
    setAutoRefresh,
    refreshInterval,
    setRefreshInterval,
    
    // Actions principales
    fetchDashboardData,
    fetchSystemHealth,
    fetchNetworkSummary,
    fetchAlerts,
    refreshAllData,
    
    // États pour compatibilité avec l'ancien code
    dashboards,
    widgets,
    isAuthenticated,

    // Actions pour compatibilité avec l'ancien code
    fetchDashboards,
    fetchDashboard,
    createDashboard,
    updateDashboard,
    deleteDashboard,
    saveDashboard,
    loadDashboard,
    fetchWidgets,
    fetchShortcuts,
    saveShortcuts
  };
};

export default useDashboard;