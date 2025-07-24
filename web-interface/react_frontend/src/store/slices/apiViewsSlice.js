/**
 * Slice Redux pour la gestion des API Views
 * Intégration avec le module api_views backend - Dashboard et vues agrégées
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiViewsService from '../../services/apiViewsService';

/**
 * État initial du slice apiViews
 */
const initialState = {
  // Données des vues
  dashboard: null,
  systemOverview: null,
  networkOverview: null,
  
  // Topologie et découverte
  topologyData: null,
  discoveryStatus: null,
  activeDiscoveries: [],
  
  // Équipements
  devices: [],
  currentDevice: null,
  devicesMetadata: null,
  
  // Recherche
  searchResults: null,
  searchHistory: [],
  lastSearchQuery: '',
  
  // Monitoring
  monitoring: {
    metrics: null,
    alerts: null,
    health: null
  },
  
  // États de chargement
  loading: {
    dashboard: false,
    system: false,
    network: false,
    topology: false,
    discovery: false,
    devices: false,
    search: false,
    monitoring: false
  },
  
  // Gestion d'erreurs
  error: null,
  lastError: null,
  
  // Métadonnées et cache
  lastFetch: {
    dashboard: null,
    system: null,
    network: null,
    devices: null
  },
  
  // Filtres et tri
  filters: {
    deviceType: '',
    deviceStatus: '',
    searchType: 'all'
  },
  sorting: {
    field: 'name',
    direction: 'asc'
  }
};

/**
 * Actions asynchrones (thunks) pour les API Views
 */

// Récupérer le dashboard overview
export const fetchDashboardOverview = createAsyncThunk(
  'apiViews/fetchDashboardOverview',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.getDashboardOverview(params);
      
      if (result.success) {
        return {
          data: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer la vue système
export const fetchSystemOverview = createAsyncThunk(
  'apiViews/fetchSystemOverview',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.getSystemOverview(params);
      
      if (result.success) {
        return {
          data: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer la vue réseau
export const fetchNetworkOverview = createAsyncThunk(
  'apiViews/fetchNetworkOverview',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.getNetworkOverview(params);
      
      if (result.success) {
        return {
          data: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Démarrer la découverte de topologie
export const startTopologyDiscovery = createAsyncThunk(
  'apiViews/startTopologyDiscovery',
  async (discoveryParams, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.startTopologyDiscovery(discoveryParams);
      
      if (result.success) {
        return {
          discoveryId: result.discoveryId,
          data: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer le statut de découverte
export const fetchTopologyDiscoveryStatus = createAsyncThunk(
  'apiViews/fetchTopologyDiscoveryStatus',
  async (discoveryId, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.getTopologyDiscoveryStatus(discoveryId);
      
      if (result.success) {
        return {
          discoveryId,
          status: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer les données de topologie
export const fetchTopologyData = createAsyncThunk(
  'apiViews/fetchTopologyData',
  async ({ networkId, params = {} }, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.getTopologyData(networkId, params);
      
      if (result.success) {
        return {
          networkId,
          data: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer les équipements
export const fetchDevices = createAsyncThunk(
  'apiViews/fetchDevices',
  async (params = {}, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const { filters, sorting } = state.apiViews;
      
      const requestParams = {
        device_type: filters.deviceType || undefined,
        status: filters.deviceStatus || undefined,
        ordering: `${sorting.direction === 'desc' ? '-' : ''}${sorting.field}`,
        ...params
      };
      
      const result = await apiViewsService.getDevices(requestParams);
      
      if (result.success) {
        return {
          devices: result.data.results || result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer un équipement spécifique
export const fetchDevice = createAsyncThunk(
  'apiViews/fetchDevice',
  async (deviceId, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.getDevice(deviceId);
      
      if (result.success) {
        return {
          deviceId,
          device: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Effectuer une recherche globale
export const performGlobalSearch = createAsyncThunk(
  'apiViews/performGlobalSearch',
  async ({ query, params = {} }, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.globalSearch(query, params);
      
      if (result.success) {
        return {
          query,
          results: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer les métriques de monitoring
export const fetchMonitoringMetrics = createAsyncThunk(
  'apiViews/fetchMonitoringMetrics',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.getMonitoringMetrics(params);
      
      if (result.success) {
        return {
          metrics: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer les alertes de monitoring
export const fetchMonitoringAlerts = createAsyncThunk(
  'apiViews/fetchMonitoringAlerts',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await apiViewsService.getMonitoringAlerts(params);
      
      if (result.success) {
        return {
          alerts: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

/**
 * Slice Redux pour les API Views
 */
const apiViewsSlice = createSlice({
  name: 'apiViews',
  initialState,
  reducers: {
    // Actions synchrones pour la gestion de l'état local
    setCurrentDevice: (state, action) => {
      state.currentDevice = action.payload;
    },
    
    clearCurrentDevice: (state) => {
      state.currentDevice = null;
    },
    
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    
    setSorting: (state, action) => {
      state.sorting = { ...state.sorting, ...action.payload };
    },
    
    clearFilters: (state) => {
      state.filters = initialState.filters;
    },
    
    clearError: (state) => {
      state.error = null;
    },
    
    clearSearchResults: (state) => {
      state.searchResults = null;
      state.lastSearchQuery = '';
    },
    
    addToSearchHistory: (state, action) => {
      const { query, timestamp } = action.payload;
      state.searchHistory.unshift({ query, timestamp });
      
      // Garder seulement les 10 dernières recherches
      if (state.searchHistory.length > 10) {
        state.searchHistory = state.searchHistory.slice(0, 10);
      }
    },
    
    updateDiscoveryStatus: (state, action) => {
      const { discoveryId, status } = action.payload;
      
      if (state.discoveryStatus && state.discoveryStatus.discoveryId === discoveryId) {
        state.discoveryStatus = { ...state.discoveryStatus, ...status };
      }
      
      // Mettre à jour aussi dans la liste des découvertes actives
      const discovery = state.activeDiscoveries.find(d => d.discoveryId === discoveryId);
      if (discovery) {
        Object.assign(discovery, status);
      }
    },
    
    addActiveDiscovery: (state, action) => {
      const discovery = action.payload;
      state.activeDiscoveries.push(discovery);
    },
    
    removeActiveDiscovery: (state, action) => {
      const discoveryId = action.payload;
      state.activeDiscoveries = state.activeDiscoveries.filter(
        d => d.discoveryId !== discoveryId
      );
    },
    
    // Mise à jour optimiste des équipements
    optimisticUpdateDevice: (state, action) => {
      const { deviceId, updateData } = action.payload;
      const device = state.devices.find(d => d.id === deviceId);
      if (device) {
        Object.assign(device, updateData);
      }
      
      if (state.currentDevice && state.currentDevice.id === deviceId) {
        Object.assign(state.currentDevice, updateData);
      }
    },
  },
  
  extraReducers: (builder) => {
    // Dashboard Overview
    builder
      .addCase(fetchDashboardOverview.pending, (state) => {
        state.loading.dashboard = true;
        state.error = null;
      })
      .addCase(fetchDashboardOverview.fulfilled, (state, action) => {
        state.loading.dashboard = false;
        state.dashboard = action.payload.data;
        state.lastFetch.dashboard = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchDashboardOverview.rejected, (state, action) => {
        state.loading.dashboard = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // System Overview
    builder
      .addCase(fetchSystemOverview.pending, (state) => {
        state.loading.system = true;
        state.error = null;
      })
      .addCase(fetchSystemOverview.fulfilled, (state, action) => {
        state.loading.system = false;
        state.systemOverview = action.payload.data;
        state.lastFetch.system = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchSystemOverview.rejected, (state, action) => {
        state.loading.system = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Network Overview
    builder
      .addCase(fetchNetworkOverview.pending, (state) => {
        state.loading.network = true;
        state.error = null;
      })
      .addCase(fetchNetworkOverview.fulfilled, (state, action) => {
        state.loading.network = false;
        state.networkOverview = action.payload.data;
        state.lastFetch.network = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchNetworkOverview.rejected, (state, action) => {
        state.loading.network = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Start Topology Discovery
    builder
      .addCase(startTopologyDiscovery.pending, (state) => {
        state.loading.discovery = true;
        state.error = null;
      })
      .addCase(startTopologyDiscovery.fulfilled, (state, action) => {
        state.loading.discovery = false;
        const { discoveryId, data, metadata } = action.payload;
        
        state.discoveryStatus = {
          discoveryId,
          status: 'started',
          networkId: metadata.networkId,
          startTime: metadata.timestamp
        };
        
        // Ajouter à la liste des découvertes actives
        state.activeDiscoveries.push({
          discoveryId,
          networkId: metadata.networkId,
          status: 'started',
          startTime: metadata.timestamp
        });
        
        state.error = null;
      })
      .addCase(startTopologyDiscovery.rejected, (state, action) => {
        state.loading.discovery = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Topology Discovery Status
    builder
      .addCase(fetchTopologyDiscoveryStatus.pending, (state) => {
        state.loading.topology = true;
        state.error = null;
      })
      .addCase(fetchTopologyDiscoveryStatus.fulfilled, (state, action) => {
        state.loading.topology = false;
        const { discoveryId, status, metadata } = action.payload;
        
        state.discoveryStatus = {
          discoveryId,
          ...status,
          lastUpdate: metadata.timestamp
        };
        
        // Mettre à jour dans les découvertes actives
        const discovery = state.activeDiscoveries.find(d => d.discoveryId === discoveryId);
        if (discovery) {
          Object.assign(discovery, status, { lastUpdate: metadata.timestamp });
        }
        
        // Supprimer de la liste si terminé
        if (status.status === 'completed' || status.status === 'failed') {
          state.activeDiscoveries = state.activeDiscoveries.filter(
            d => d.discoveryId !== discoveryId
          );
        }
        
        state.error = null;
      })
      .addCase(fetchTopologyDiscoveryStatus.rejected, (state, action) => {
        state.loading.topology = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Topology Data
    builder
      .addCase(fetchTopologyData.pending, (state) => {
        state.loading.topology = true;
        state.error = null;
      })
      .addCase(fetchTopologyData.fulfilled, (state, action) => {
        state.loading.topology = false;
        const { networkId, data, metadata } = action.payload;
        
        state.topologyData = {
          networkId,
          ...data,
          metadata: {
            ...metadata,
            lastFetch: new Date().toISOString()
          }
        };
        
        state.error = null;
      })
      .addCase(fetchTopologyData.rejected, (state, action) => {
        state.loading.topology = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Devices
    builder
      .addCase(fetchDevices.pending, (state) => {
        state.loading.devices = true;
        state.error = null;
      })
      .addCase(fetchDevices.fulfilled, (state, action) => {
        state.loading.devices = false;
        state.devices = action.payload.devices;
        state.devicesMetadata = action.payload.metadata;
        state.lastFetch.devices = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchDevices.rejected, (state, action) => {
        state.loading.devices = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Device
    builder
      .addCase(fetchDevice.pending, (state) => {
        state.loading.devices = true;
        state.error = null;
      })
      .addCase(fetchDevice.fulfilled, (state, action) => {
        state.loading.devices = false;
        const { deviceId, device } = action.payload;
        
        state.currentDevice = device;
        
        // Mettre à jour aussi dans la liste
        const index = state.devices.findIndex(d => d.id === deviceId);
        if (index !== -1) {
          state.devices[index] = device;
        }
        
        state.error = null;
      })
      .addCase(fetchDevice.rejected, (state, action) => {
        state.loading.devices = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Global Search
    builder
      .addCase(performGlobalSearch.pending, (state) => {
        state.loading.search = true;
        state.error = null;
      })
      .addCase(performGlobalSearch.fulfilled, (state, action) => {
        state.loading.search = false;
        const { query, results, metadata } = action.payload;
        
        state.searchResults = results;
        state.lastSearchQuery = query;
        
        // Ajouter à l'historique
        state.searchHistory.unshift({
          query,
          timestamp: new Date().toISOString(),
          resultsCount: metadata.resultsCount
        });
        
        // Garder seulement les 10 dernières recherches
        if (state.searchHistory.length > 10) {
          state.searchHistory = state.searchHistory.slice(0, 10);
        }
        
        state.error = null;
      })
      .addCase(performGlobalSearch.rejected, (state, action) => {
        state.loading.search = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Monitoring Metrics
    builder
      .addCase(fetchMonitoringMetrics.pending, (state) => {
        state.loading.monitoring = true;
        state.error = null;
      })
      .addCase(fetchMonitoringMetrics.fulfilled, (state, action) => {
        state.loading.monitoring = false;
        state.monitoring.metrics = action.payload.metrics;
        state.error = null;
      })
      .addCase(fetchMonitoringMetrics.rejected, (state, action) => {
        state.loading.monitoring = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Monitoring Alerts
    builder
      .addCase(fetchMonitoringAlerts.pending, (state) => {
        state.loading.monitoring = true;
        state.error = null;
      })
      .addCase(fetchMonitoringAlerts.fulfilled, (state, action) => {
        state.loading.monitoring = false;
        state.monitoring.alerts = action.payload.alerts;
        state.error = null;
      })
      .addCase(fetchMonitoringAlerts.rejected, (state, action) => {
        state.loading.monitoring = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
  },
});

// Export des actions
export const {
  setCurrentDevice,
  clearCurrentDevice,
  setFilters,
  setSorting,
  clearFilters,
  clearError,
  clearSearchResults,
  addToSearchHistory,
  updateDiscoveryStatus,
  addActiveDiscovery,
  removeActiveDiscovery,
  optimisticUpdateDevice,
} = apiViewsSlice.actions;

// Sélecteurs
export const selectDashboard = (state) => state.apiViews.dashboard;
export const selectSystemOverview = (state) => state.apiViews.systemOverview;
export const selectNetworkOverview = (state) => state.apiViews.networkOverview;
export const selectTopologyData = (state) => state.apiViews.topologyData;
export const selectDiscoveryStatus = (state) => state.apiViews.discoveryStatus;
export const selectActiveDiscoveries = (state) => state.apiViews.activeDiscoveries;
export const selectDevices = (state) => state.apiViews.devices;
export const selectCurrentDevice = (state) => state.apiViews.currentDevice;
export const selectSearchResults = (state) => state.apiViews.searchResults;
export const selectSearchHistory = (state) => state.apiViews.searchHistory;
export const selectMonitoring = (state) => state.apiViews.monitoring;
export const selectApiViewsLoading = (state) => state.apiViews.loading;
export const selectApiViewsError = (state) => state.apiViews.error;
export const selectApiViewsFilters = (state) => state.apiViews.filters;
export const selectApiViewsSorting = (state) => state.apiViews.sorting;

// Sélecteurs composés
export const selectDeviceById = (deviceId) => (state) =>
  state.apiViews.devices.find(device => device.id === deviceId);

export const selectDevicesByType = (deviceType) => (state) =>
  state.apiViews.devices.filter(device => device.device_type === deviceType);

export const selectOnlineDevices = (state) =>
  state.apiViews.devices.filter(device => device.status === 'online');

export const selectProblematicDevices = (state) =>
  state.apiViews.devices.filter(device => device.status !== 'online');

export const selectIsApiViewsLoading = (state) =>
  Object.values(state.apiViews.loading || {}).some(loading => loading);

export const selectCriticalAlerts = (state) =>
  state.apiViews.monitoring.alerts?.filter(alert => alert.severity === 'critical') || [];

export const selectActiveAlerts = (state) =>
  state.apiViews.monitoring.alerts?.filter(alert => alert.status === 'active') || [];

export default apiViewsSlice.reducer;