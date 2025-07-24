/**
 * Hook personnalisé pour la gestion des API Clients
 * Intégration avec le module api_clients backend (8 clients)
 */

import { useCallback, useMemo, useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import apiClientsService from '../services/apiClientsService';

/**
 * Hook principal pour la gestion des API Clients
 */
export const useApiClients = () => {
  const [clients, setClients] = useState([]);
  const [currentClient, setCurrentClient] = useState(null);
  const [loading, setLoading] = useState({
    fetch: false,
    test: false,
    config: false,
    health: false
  });
  const [error, setError] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [health, setHealth] = useState(null);

  // Actions avec useCallback pour stabilité des références
  const fetchClients = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, fetch: true }));
    setError(null);

    try {
      const result = await apiClientsService.getClients(params);
      if (result.success) {
        setClients(result.data);
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
      setLoading(prev => ({ ...prev, fetch: false }));
    }
  }, []);

  const getClient = useCallback(async (clientId) => {
    setLoading(prev => ({ ...prev, fetch: true }));
    setError(null);

    try {
      const result = await apiClientsService.getClient(clientId);
      if (result.success) {
        setCurrentClient(result.data);
        
        // Mettre à jour aussi dans la liste si elle existe
        setClients(prev => {
          const index = prev.findIndex(client => client.id === clientId);
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
      setLoading(prev => ({ ...prev, fetch: false }));
    }
  }, []);

  const testClient = useCallback(async (clientId, testParams = {}) => {
    setLoading(prev => ({ ...prev, test: true }));
    setError(null);

    try {
      const result = await apiClientsService.testClient(clientId, testParams);
      if (result.success) {
        // Mettre à jour le statut du client après le test
        setClients(prev => prev.map(client => 
          client.id === clientId 
            ? { ...client, last_test: result.data, test_passed: result.metadata.testPassed }
            : client
        ));
        
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
      setLoading(prev => ({ ...prev, test: false }));
    }
  }, []);

  const updateClientConfig = useCallback(async (clientId, configData) => {
    setLoading(prev => ({ ...prev, config: true }));
    setError(null);

    try {
      const result = await apiClientsService.updateClientConfig(clientId, configData);
      if (result.success) {
        // Mettre à jour la configuration du client
        setClients(prev => prev.map(client => 
          client.id === clientId 
            ? { ...client, ...result.data }
            : client
        ));
        
        if (currentClient && currentClient.id === clientId) {
          setCurrentClient({ ...currentClient, ...result.data });
        }
        
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
      setLoading(prev => ({ ...prev, config: false }));
    }
  }, [currentClient]);

  const fetchClientsHealth = useCallback(async () => {
    setLoading(prev => ({ ...prev, health: true }));
    setError(null);

    try {
      const result = await apiClientsService.getClientsHealth();
      if (result.success) {
        setHealth(result.data);
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
      setLoading(prev => ({ ...prev, health: false }));
    }
  }, []);

  const fetchClientsMetrics = useCallback(async (timeRange = '1h') => {
    setLoading(prev => ({ ...prev, fetch: true }));
    setError(null);

    try {
      const result = await apiClientsService.getClientsMetrics(timeRange);
      if (result.success) {
        setMetrics(result.data);
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
      setLoading(prev => ({ ...prev, fetch: false }));
    }
  }, []);

  // Fonctions utilitaires mémorisées
  const utils = useMemo(() => ({
    // Filtrer les clients par type
    getClientsByType: (clientType) => 
      clients.filter(client => client.client_type === clientType),
    
    // Obtenir les clients actifs
    getActiveClients: () => 
      clients.filter(client => client.is_active),
    
    // Obtenir les clients avec erreurs
    getUnhealthyClients: () => 
      clients.filter(client => client.status !== 'healthy'),
    
    // Statistiques des clients
    getStats: () => ({
      total: clients.length,
      active: clients.filter(c => c.is_active).length,
      healthy: clients.filter(c => c.status === 'healthy').length,
      types: [...new Set(clients.map(c => c.client_type))],
      lastUpdate: new Date().toISOString()
    }),
    
    // Rechercher un client par nom ou type
    searchClients: (query) => 
      clients.filter(client => 
        client.name.toLowerCase().includes(query.toLowerCase()) ||
        client.client_type.toLowerCase().includes(query.toLowerCase())
      )
  }), [clients]);

  // Actions regroupées pour réutilisation dans les callbacks
  const actions = useMemo(() => ({
    fetchClients,
    getClient,
    testClient,
    updateClientConfig,
    fetchClientsHealth,
    fetchClientsMetrics
  }), [fetchClients, getClient, testClient, updateClientConfig, fetchClientsHealth, fetchClientsMetrics]);

  // Callbacks optimisés
  const refresh = useCallback((params = {}) => {
    return actions.fetchClients(params);
  }, [actions]);

  const testAllClients = useCallback(async () => {
    const results = [];
    
    for (const client of clients) {
      const result = await actions.testClient(client.id);
      results.push({ clientId: client.id, ...result });
    }
    
    return results;
  }, [clients, actions]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearCurrentClient = useCallback(() => {
    setCurrentClient(null);
  }, []);

  return {
    // État
    clients,
    currentClient,
    loading,
    error,
    metrics,
    health,
    isLoading: Object.values(loading).some(l => l),

    // Actions
    fetchClients,
    getClient,
    testClient,
    updateClientConfig,
    fetchClientsHealth,
    fetchClientsMetrics,

    // Utilitaires
    ...utils,

    // Callbacks optimisés
    refresh,
    testAllClients,
    clearError,
    clearCurrentClient,
  };
};

/**
 * Hook pour un client spécialisé (GNS3, SNMP, etc.)
 */
export const useSpecializedClient = (clientType) => {
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSpecializedClient = useCallback(async (params = {}) => {
    setLoading(true);
    setError(null);

    try {
      let result;
      
      switch (clientType) {
        case 'gns3':
          result = await apiClientsService.getGNS3Client(params);
          break;
        case 'snmp':
          result = await apiClientsService.getSNMPClient(params);
          break;
        case 'prometheus':
          result = await apiClientsService.getPrometheusClient(params);
          break;
        default:
          throw new Error(`Client type ${clientType} not supported`);
      }

      if (result.success) {
        setClient(result.data);
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
      setLoading(false);
    }
  }, [clientType]);

  return {
    client,
    loading,
    error,
    fetchSpecializedClient,
    clearError: () => setError(null)
  };
};

/**
 * Hook pour surveiller la santé des clients en temps réel
 */
export const useClientsHealthMonitor = (interval = 30000) => {
  const [healthData, setHealthData] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  const startMonitoring = useCallback(() => {
    setIsMonitoring(true);
    
    const fetchHealth = async () => {
      try {
        const result = await apiClientsService.getClientsHealth();
        if (result.success) {
          setHealthData(result.data);
        }
      } catch (error) {
        console.error('Error monitoring clients health:', error);
      }
    };

    // Première récupération immédiate
    fetchHealth();
    
    // Puis surveillance périodique
    const intervalId = setInterval(fetchHealth, interval);
    
    return () => {
      clearInterval(intervalId);
      setIsMonitoring(false);
    };
  }, [interval]);

  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false);
  }, []);

  return {
    healthData,
    isMonitoring,
    startMonitoring,
    stopMonitoring
  };
};

export default useApiClients;