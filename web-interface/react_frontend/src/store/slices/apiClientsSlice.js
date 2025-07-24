/**
 * Slice Redux pour la gestion des API Clients
 * Intégration avec le module api_clients backend
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import apiClientsService from '../../services/apiClientsService';

/**
 * État initial du slice apiClients
 */
const initialState = {
  // Données des clients API
  items: [],
  currentClient: null,
  
  // Santé et métriques
  health: null,
  metrics: null,
  
  // Clients spécialisés
  specializedClients: {
    gns3: null,
    snmp: null,
    prometheus: null,
    grafana: null,
    elasticsearch: null,
    netflow: null,
    haproxy: null,
    fail2ban: null
  },
  
  // États de chargement
  loading: {
    fetch: false,
    test: false,
    config: false,
    health: false,
    metrics: false,
    specialized: {}
  },
  
  // Gestion d'erreurs
  error: null,
  lastError: null,
  
  // Métadonnées
  lastFetch: null,
  lastHealthCheck: null,
  
  // Filtres et tri
  filters: {
    clientType: '',
    status: '',
    isActive: null
  },
  sorting: {
    field: 'name',
    direction: 'asc'
  }
};

/**
 * Actions asynchrones (thunks) pour les API Clients
 */

// Récupérer la liste des clients API
export const fetchApiClients = createAsyncThunk(
  'apiClients/fetchApiClients',
  async (params = {}, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const { filters, sorting } = state.apiClients;
      
      const requestParams = {
        client_type: filters.clientType || undefined,
        status: filters.status || undefined,
        is_active: filters.isActive,
        ordering: `${sorting.direction === 'desc' ? '-' : ''}${sorting.field}`,
        ...params
      };
      
      const result = await apiClientsService.getClients(requestParams);
      
      if (result.success) {
        return {
          clients: result.data,
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

// Récupérer un client spécifique
export const fetchApiClient = createAsyncThunk(
  'apiClients/fetchApiClient',
  async (clientId, { rejectWithValue }) => {
    try {
      const result = await apiClientsService.getClient(clientId);
      
      if (result.success) {
        return result.data;
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

// Tester un client API
export const testApiClient = createAsyncThunk(
  'apiClients/testApiClient',
  async ({ clientId, testParams = {} }, { rejectWithValue }) => {
    try {
      const result = await apiClientsService.testClient(clientId, testParams);
      
      if (result.success) {
        return {
          clientId,
          testResult: result.data,
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

// Mettre à jour la configuration d'un client
export const updateApiClientConfig = createAsyncThunk(
  'apiClients/updateApiClientConfig',
  async ({ clientId, configData }, { rejectWithValue }) => {
    try {
      const result = await apiClientsService.updateClientConfig(clientId, configData);
      
      if (result.success) {
        return {
          clientId,
          updatedClient: result.data,
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

// Récupérer la santé des clients
export const fetchClientsHealth = createAsyncThunk(
  'apiClients/fetchClientsHealth',
  async (_, { rejectWithValue }) => {
    try {
      const result = await apiClientsService.getClientsHealth();
      
      if (result.success) {
        return {
          health: result.data,
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

// Récupérer les métriques des clients
export const fetchClientsMetrics = createAsyncThunk(
  'apiClients/fetchClientsMetrics',
  async (timeRange = '1h', { rejectWithValue }) => {
    try {
      const result = await apiClientsService.getClientsMetrics(timeRange);
      
      if (result.success) {
        return {
          metrics: result.data,
          timeRange,
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

// Récupérer un client spécialisé
export const fetchSpecializedClient = createAsyncThunk(
  'apiClients/fetchSpecializedClient',
  async ({ clientType, params = {} }, { rejectWithValue }) => {
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
        return {
          clientType,
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

/**
 * Slice Redux pour les API Clients
 */
const apiClientsSlice = createSlice({
  name: 'apiClients',
  initialState,
  reducers: {
    // Actions synchrones
    setCurrentClient: (state, action) => {
      state.currentClient = action.payload;
    },
    
    clearCurrentClient: (state) => {
      state.currentClient = null;
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
    
    // Mise à jour locale du statut d'un client
    updateClientStatus: (state, action) => {
      const { clientId, status, testResult } = action.payload;
      const client = state.items.find(item => item.id === clientId);
      if (client) {
        client.status = status;
        if (testResult) {
          client.last_test = testResult;
          client.test_passed = testResult.success;
        }
      }
    },
    
    // Mise à jour optimiste d'un client
    optimisticUpdateClient: (state, action) => {
      const { clientId, updateData } = action.payload;
      const client = state.items.find(item => item.id === clientId);
      if (client) {
        Object.assign(client, updateData);
      }
    },
  },
  
  extraReducers: (builder) => {
    // Fetch API Clients
    builder
      .addCase(fetchApiClients.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchApiClients.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.items = action.payload.clients;
        state.lastFetch = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchApiClients.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch API Client
    builder
      .addCase(fetchApiClient.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchApiClient.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.currentClient = action.payload;
        
        // Mettre à jour aussi dans la liste si elle existe
        const index = state.items.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        
        state.error = null;
      })
      .addCase(fetchApiClient.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Test API Client
    builder
      .addCase(testApiClient.pending, (state) => {
        state.loading.test = true;
        state.error = null;
      })
      .addCase(testApiClient.fulfilled, (state, action) => {
        state.loading.test = false;
        
        const { clientId, testResult, metadata } = action.payload;
        
        // Mettre à jour le client dans la liste
        const client = state.items.find(item => item.id === clientId);
        if (client) {
          client.last_test = testResult;
          client.test_passed = metadata.testPassed;
          client.last_test_time = metadata.timestamp;
        }
        
        // Mettre à jour le client courant si c'est le même
        if (state.currentClient && state.currentClient.id === clientId) {
          state.currentClient.last_test = testResult;
          state.currentClient.test_passed = metadata.testPassed;
          state.currentClient.last_test_time = metadata.timestamp;
        }
        
        state.error = null;
      })
      .addCase(testApiClient.rejected, (state, action) => {
        state.loading.test = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Update API Client Config
    builder
      .addCase(updateApiClientConfig.pending, (state) => {
        state.loading.config = true;
        state.error = null;
      })
      .addCase(updateApiClientConfig.fulfilled, (state, action) => {
        state.loading.config = false;
        
        const { clientId, updatedClient } = action.payload;
        
        // Mettre à jour dans la liste
        const index = state.items.findIndex(item => item.id === clientId);
        if (index !== -1) {
          state.items[index] = updatedClient;
        }
        
        // Mettre à jour le client courant si c'est le même
        if (state.currentClient && state.currentClient.id === clientId) {
          state.currentClient = updatedClient;
        }
        
        state.error = null;
      })
      .addCase(updateApiClientConfig.rejected, (state, action) => {
        state.loading.config = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Clients Health
    builder
      .addCase(fetchClientsHealth.pending, (state) => {
        state.loading.health = true;
        state.error = null;
      })
      .addCase(fetchClientsHealth.fulfilled, (state, action) => {
        state.loading.health = false;
        state.health = action.payload.health;
        state.lastHealthCheck = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchClientsHealth.rejected, (state, action) => {
        state.loading.health = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Clients Metrics
    builder
      .addCase(fetchClientsMetrics.pending, (state) => {
        state.loading.metrics = true;
        state.error = null;
      })
      .addCase(fetchClientsMetrics.fulfilled, (state, action) => {
        state.loading.metrics = false;
        state.metrics = action.payload.metrics;
        state.error = null;
      })
      .addCase(fetchClientsMetrics.rejected, (state, action) => {
        state.loading.metrics = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Specialized Client
    builder
      .addCase(fetchSpecializedClient.pending, (state, action) => {
        const clientType = action.meta.arg.clientType;
        state.loading.specialized[clientType] = true;
        state.error = null;
      })
      .addCase(fetchSpecializedClient.fulfilled, (state, action) => {
        const { clientType, data } = action.payload;
        state.loading.specialized[clientType] = false;
        state.specializedClients[clientType] = data;
        state.error = null;
      })
      .addCase(fetchSpecializedClient.rejected, (state, action) => {
        const clientType = action.meta.arg.clientType;
        state.loading.specialized[clientType] = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
  },
});

// Export des actions
export const {
  setCurrentClient,
  clearCurrentClient,
  setFilters,
  setSorting,
  clearFilters,
  clearError,
  updateClientStatus,
  optimisticUpdateClient,
} = apiClientsSlice.actions;

// Sélecteurs
export const selectApiClients = (state) => state.apiClients.items;
export const selectCurrentClient = (state) => state.apiClients.currentClient;
export const selectClientsHealth = (state) => state.apiClients.health;
export const selectClientsMetrics = (state) => state.apiClients.metrics;
export const selectClientsLoading = (state) => state.apiClients.loading;
export const selectClientsError = (state) => state.apiClients.error;
export const selectClientsFilters = (state) => state.apiClients.filters;
export const selectClientsSorting = (state) => state.apiClients.sorting;
export const selectSpecializedClients = (state) => state.apiClients.specializedClients;

// Sélecteurs composés
export const selectClientById = (clientId) => (state) =>
  state.apiClients.items.find(item => item.id === clientId);

export const selectClientsByType = (clientType) => (state) =>
  state.apiClients.items.filter(item => item.client_type === clientType);

export const selectActiveClients = (state) =>
  state.apiClients.items.filter(item => item.is_active);

export const selectHealthyClients = (state) =>
  state.apiClients.items.filter(item => item.status === 'healthy');

export const selectIsClientsLoading = (state) =>
  Object.values(state.apiClients.loading || {}).some(loading => loading);

export default apiClientsSlice.reducer;