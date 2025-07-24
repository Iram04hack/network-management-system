/**
 * Slice Redux pour la gestion des Dashboards
 * Intégration avec le module dashboard backend - WebSocket temps réel
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import dashboardService from '../../services/dashboardService';

/**
 * État initial du slice dashboard
 */
const initialState = {
  // Configuration utilisateur
  userConfig: null,
  
  // Données du dashboard principal
  dashboardData: null,
  
  // Dashboards personnalisés
  customDashboards: [],
  currentDashboard: null,
  
  // Widgets
  widgets: [],
  
  // Données temps réel
  networkOverview: null,
  systemHealth: null,
  
  // WebSocket et temps réel
  isRealTimeEnabled: false,
  websocketStatus: 'disconnected', // 'connecting', 'connected', 'disconnected', 'error'
  lastRealTimeUpdate: null,
  
  // États de chargement
  loading: {
    dashboard: false,
    config: false,
    customDashboards: false,
    widgets: false,
    network: false,
    health: false,
    websocket: false
  },
  
  // Gestion d'erreurs
  error: null,
  lastError: null,
  
  // Métadonnées et cache
  lastFetch: {
    dashboard: null,
    config: null,
    customDashboards: null,
    widgets: null,
    network: null,
    health: null
  },
  
  // Layout et préférences
  layout: {
    theme: 'light',
    layoutType: 'grid',
    columns: 12,
    rowHeight: 100,
    margin: [10, 10],
    isDraggable: true,
    isResizable: true
  },
  
  // Filtres et tri
  filters: {
    widgetType: '',
    isActive: null,
    dashboardOwner: ''
  },
  sorting: {
    field: 'updated_at',
    direction: 'desc'
  }
};

/**
 * Actions asynchrones (thunks) pour les Dashboards
 */

// Récupérer les données du dashboard principal
export const fetchDashboardData = createAsyncThunk(
  'dashboard/fetchDashboardData',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await dashboardService.getDashboardData(params);
      
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

// Récupérer la configuration utilisateur
export const fetchUserConfig = createAsyncThunk(
  'dashboard/fetchUserConfig',
  async (_, { rejectWithValue }) => {
    try {
      const result = await dashboardService.getUserConfig();
      
      if (result.success) {
        return {
          config: result.data,
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

// Mettre à jour la configuration utilisateur
export const updateUserConfig = createAsyncThunk(
  'dashboard/updateUserConfig',
  async (configData, { rejectWithValue }) => {
    try {
      const result = await dashboardService.updateUserConfig(configData);
      
      if (result.success) {
        return {
          config: result.data,
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

// Récupérer les dashboards personnalisés
export const fetchCustomDashboards = createAsyncThunk(
  'dashboard/fetchCustomDashboards',
  async (params = {}, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const { filters, sorting } = state.dashboard;
      
      const requestParams = {
        owner: filters.dashboardOwner || undefined,
        ordering: `${sorting.direction === 'desc' ? '-' : ''}${sorting.field}`,
        ...params
      };
      
      const result = await dashboardService.getCustomDashboards(requestParams);
      
      if (result.success) {
        return {
          dashboards: result.data,
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

// Récupérer un dashboard personnalisé spécifique
export const fetchCustomDashboard = createAsyncThunk(
  'dashboard/fetchCustomDashboard',
  async (dashboardId, { rejectWithValue }) => {
    try {
      const result = await dashboardService.getCustomDashboard(dashboardId);
      
      if (result.success) {
        return {
          dashboard: result.data,
          dashboardId,
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

// Créer un dashboard personnalisé
export const createCustomDashboard = createAsyncThunk(
  'dashboard/createCustomDashboard',
  async (dashboardData, { rejectWithValue }) => {
    try {
      const result = await dashboardService.createCustomDashboard(dashboardData);
      
      if (result.success) {
        return {
          dashboard: result.data,
          dashboardId: result.dashboardId,
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

// Mettre à jour un dashboard personnalisé
export const updateCustomDashboard = createAsyncThunk(
  'dashboard/updateCustomDashboard',
  async ({ dashboardId, dashboardData }, { rejectWithValue }) => {
    try {
      const result = await dashboardService.updateCustomDashboard(dashboardId, dashboardData);
      
      if (result.success) {
        return {
          dashboard: result.data,
          dashboardId,
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

// Supprimer un dashboard personnalisé
export const deleteCustomDashboard = createAsyncThunk(
  'dashboard/deleteCustomDashboard',
  async (dashboardId, { rejectWithValue }) => {
    try {
      const result = await dashboardService.deleteCustomDashboard(dashboardId);
      
      if (result.success) {
        return {
          dashboardId,
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

// Récupérer les widgets
export const fetchWidgets = createAsyncThunk(
  'dashboard/fetchWidgets',
  async (params = {}, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const { filters } = state.dashboard;
      
      const requestParams = {
        widget_type: filters.widgetType || undefined,
        is_active: filters.isActive,
        ...params
      };
      
      const result = await dashboardService.getWidgets(requestParams);
      
      if (result.success) {
        return {
          widgets: result.data,
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

// Créer un widget
export const createWidget = createAsyncThunk(
  'dashboard/createWidget',
  async (widgetData, { rejectWithValue }) => {
    try {
      const result = await dashboardService.createWidget(widgetData);
      
      if (result.success) {
        return {
          widget: result.data,
          widgetId: result.widgetId,
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

// Mettre à jour un widget
export const updateWidget = createAsyncThunk(
  'dashboard/updateWidget',
  async ({ widgetId, widgetData }, { rejectWithValue }) => {
    try {
      const result = await dashboardService.updateWidget(widgetId, widgetData);
      
      if (result.success) {
        return {
          widget: result.data,
          widgetId,
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

// Supprimer un widget
export const deleteWidget = createAsyncThunk(
  'dashboard/deleteWidget',
  async (widgetId, { rejectWithValue }) => {
    try {
      const result = await dashboardService.deleteWidget(widgetId);
      
      if (result.success) {
        return {
          widgetId,
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

// Récupérer la vue d'ensemble réseau
export const fetchNetworkOverview = createAsyncThunk(
  'dashboard/fetchNetworkOverview',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await dashboardService.getNetworkOverview(params);
      
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

// Récupérer les métriques de santé système
export const fetchSystemHealth = createAsyncThunk(
  'dashboard/fetchSystemHealth',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await dashboardService.getSystemHealth(params);
      
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

/**
 * Slice Redux pour les Dashboards
 */
const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    // Actions synchrones pour la gestion de l'état local
    setCurrentDashboard: (state, action) => {
      state.currentDashboard = action.payload;
    },
    
    clearCurrentDashboard: (state) => {
      state.currentDashboard = null;
    },
    
    setUserConfig: (state, action) => {
      state.userConfig = { ...state.userConfig, ...action.payload };
    },
    
    setLayout: (state, action) => {
      state.layout = { ...state.layout, ...action.payload };
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
    
    // WebSocket et temps réel
    setWebSocketStatus: (state, action) => {
      state.websocketStatus = action.payload;
    },
    
    setRealTimeEnabled: (state, action) => {
      state.isRealTimeEnabled = action.payload;
    },
    
    updateRealTimeData: (state, action) => {
      const { type, data } = action.payload;
      
      switch (type) {
        case 'dashboard_update':
          state.dashboardData = { ...state.dashboardData, ...data };
          break;
        case 'network_update':
          state.networkOverview = { ...state.networkOverview, ...data };
          break;
        case 'health_update':
          state.systemHealth = { ...state.systemHealth, ...data };
          break;
      }
      
      state.lastRealTimeUpdate = new Date().toISOString();
    },
    
    // Mise à jour optimiste des widgets
    optimisticUpdateWidget: (state, action) => {
      const { widgetId, updateData } = action.payload;
      const widget = state.widgets.find(w => w.id === widgetId);
      if (widget) {
        Object.assign(widget, updateData);
      }
    },
    
    // Réorganisation des widgets (drag and drop)
    reorderWidgets: (state, action) => {
      const { draggedIndex, targetIndex } = action.payload;
      const [draggedWidget] = state.widgets.splice(draggedIndex, 1);
      state.widgets.splice(targetIndex, 0, draggedWidget);
    },
    
    // Mise à jour de la position d'un widget
    updateWidgetPosition: (state, action) => {
      const { widgetId, position } = action.payload;
      const widget = state.widgets.find(w => w.id === widgetId);
      if (widget) {
        widget.position_x = position.x;
        widget.position_y = position.y;
        widget.width = position.w;
        widget.height = position.h;
      }
    },
    
    // Basculer l'état actif d'un widget
    toggleWidgetActive: (state, action) => {
      const widgetId = action.payload;
      const widget = state.widgets.find(w => w.id === widgetId);
      if (widget) {
        widget.is_active = !widget.is_active;
      }
    },
  },
  
  extraReducers: (builder) => {
    // Fetch Dashboard Data
    builder
      .addCase(fetchDashboardData.pending, (state) => {
        state.loading.dashboard = true;
        state.error = null;
      })
      .addCase(fetchDashboardData.fulfilled, (state, action) => {
        state.loading.dashboard = false;
        state.dashboardData = action.payload.data;
        state.lastFetch.dashboard = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchDashboardData.rejected, (state, action) => {
        state.loading.dashboard = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch User Config
    builder
      .addCase(fetchUserConfig.pending, (state) => {
        state.loading.config = true;
        state.error = null;
      })
      .addCase(fetchUserConfig.fulfilled, (state, action) => {
        state.loading.config = false;
        state.userConfig = action.payload.config;
        
        // Mettre à jour le layout avec les préférences utilisateur
        if (action.payload.config.theme) {
          state.layout.theme = action.payload.config.theme;
        }
        if (action.payload.config.layout) {
          state.layout.layoutType = action.payload.config.layout;
        }
        
        state.lastFetch.config = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchUserConfig.rejected, (state, action) => {
        state.loading.config = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Update User Config
    builder
      .addCase(updateUserConfig.pending, (state) => {
        state.loading.config = true;
        state.error = null;
      })
      .addCase(updateUserConfig.fulfilled, (state, action) => {
        state.loading.config = false;
        state.userConfig = action.payload.config;
        
        // Mettre à jour le layout avec les nouvelles préférences
        if (action.payload.config.theme) {
          state.layout.theme = action.payload.config.theme;
        }
        if (action.payload.config.layout) {
          state.layout.layoutType = action.payload.config.layout;
        }
        
        state.error = null;
      })
      .addCase(updateUserConfig.rejected, (state, action) => {
        state.loading.config = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Custom Dashboards
    builder
      .addCase(fetchCustomDashboards.pending, (state) => {
        state.loading.customDashboards = true;
        state.error = null;
      })
      .addCase(fetchCustomDashboards.fulfilled, (state, action) => {
        state.loading.customDashboards = false;
        state.customDashboards = action.payload.dashboards;
        state.lastFetch.customDashboards = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchCustomDashboards.rejected, (state, action) => {
        state.loading.customDashboards = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Custom Dashboard
    builder
      .addCase(fetchCustomDashboard.pending, (state) => {
        state.loading.customDashboards = true;
        state.error = null;
      })
      .addCase(fetchCustomDashboard.fulfilled, (state, action) => {
        state.loading.customDashboards = false;
        const { dashboard, dashboardId } = action.payload;
        
        state.currentDashboard = dashboard;
        
        // Mettre à jour aussi dans la liste
        const index = state.customDashboards.findIndex(d => d.id === dashboardId);
        if (index !== -1) {
          state.customDashboards[index] = dashboard;
        }
        
        state.error = null;
      })
      .addCase(fetchCustomDashboard.rejected, (state, action) => {
        state.loading.customDashboards = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Create Custom Dashboard
    builder
      .addCase(createCustomDashboard.pending, (state) => {
        state.loading.customDashboards = true;
        state.error = null;
      })
      .addCase(createCustomDashboard.fulfilled, (state, action) => {
        state.loading.customDashboards = false;
        const { dashboard } = action.payload;
        
        // Ajouter au début de la liste
        state.customDashboards.unshift(dashboard);
        
        state.error = null;
      })
      .addCase(createCustomDashboard.rejected, (state, action) => {
        state.loading.customDashboards = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Update Custom Dashboard
    builder
      .addCase(updateCustomDashboard.pending, (state) => {
        state.loading.customDashboards = true;
        state.error = null;
      })
      .addCase(updateCustomDashboard.fulfilled, (state, action) => {
        state.loading.customDashboards = false;
        const { dashboard, dashboardId } = action.payload;
        
        // Mettre à jour dans la liste
        const index = state.customDashboards.findIndex(d => d.id === dashboardId);
        if (index !== -1) {
          state.customDashboards[index] = dashboard;
        }
        
        // Mettre à jour le dashboard courant si c'est le même
        if (state.currentDashboard && state.currentDashboard.id === dashboardId) {
          state.currentDashboard = dashboard;
        }
        
        state.error = null;
      })
      .addCase(updateCustomDashboard.rejected, (state, action) => {
        state.loading.customDashboards = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Delete Custom Dashboard
    builder
      .addCase(deleteCustomDashboard.pending, (state) => {
        state.loading.customDashboards = true;
        state.error = null;
      })
      .addCase(deleteCustomDashboard.fulfilled, (state, action) => {
        state.loading.customDashboards = false;
        const { dashboardId } = action.payload;
        
        // Supprimer de la liste
        state.customDashboards = state.customDashboards.filter(d => d.id !== dashboardId);
        
        // Supprimer le dashboard courant si c'est le même
        if (state.currentDashboard && state.currentDashboard.id === dashboardId) {
          state.currentDashboard = null;
        }
        
        state.error = null;
      })
      .addCase(deleteCustomDashboard.rejected, (state, action) => {
        state.loading.customDashboards = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Widgets
    builder
      .addCase(fetchWidgets.pending, (state) => {
        state.loading.widgets = true;
        state.error = null;
      })
      .addCase(fetchWidgets.fulfilled, (state, action) => {
        state.loading.widgets = false;
        state.widgets = action.payload.widgets;
        state.lastFetch.widgets = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchWidgets.rejected, (state, action) => {
        state.loading.widgets = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Create Widget
    builder
      .addCase(createWidget.pending, (state) => {
        state.loading.widgets = true;
        state.error = null;
      })
      .addCase(createWidget.fulfilled, (state, action) => {
        state.loading.widgets = false;
        state.widgets.push(action.payload.widget);
        state.error = null;
      })
      .addCase(createWidget.rejected, (state, action) => {
        state.loading.widgets = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Update Widget
    builder
      .addCase(updateWidget.pending, (state) => {
        state.loading.widgets = true;
        state.error = null;
      })
      .addCase(updateWidget.fulfilled, (state, action) => {
        state.loading.widgets = false;
        const { widget, widgetId } = action.payload;
        
        const index = state.widgets.findIndex(w => w.id === widgetId);
        if (index !== -1) {
          state.widgets[index] = widget;
        }
        
        state.error = null;
      })
      .addCase(updateWidget.rejected, (state, action) => {
        state.loading.widgets = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Delete Widget
    builder
      .addCase(deleteWidget.pending, (state) => {
        state.loading.widgets = true;
        state.error = null;
      })
      .addCase(deleteWidget.fulfilled, (state, action) => {
        state.loading.widgets = false;
        const { widgetId } = action.payload;
        
        state.widgets = state.widgets.filter(w => w.id !== widgetId);
        state.error = null;
      })
      .addCase(deleteWidget.rejected, (state, action) => {
        state.loading.widgets = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Network Overview
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
    
    // Fetch System Health
    builder
      .addCase(fetchSystemHealth.pending, (state) => {
        state.loading.health = true;
        state.error = null;
      })
      .addCase(fetchSystemHealth.fulfilled, (state, action) => {
        state.loading.health = false;
        state.systemHealth = action.payload.data;
        state.lastFetch.health = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchSystemHealth.rejected, (state, action) => {
        state.loading.health = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
  },
});

// Export des actions
export const {
  setCurrentDashboard,
  clearCurrentDashboard,
  setUserConfig,
  setLayout,
  setFilters,
  setSorting,
  clearFilters,
  clearError,
  setWebSocketStatus,
  setRealTimeEnabled,
  updateRealTimeData,
  optimisticUpdateWidget,
  reorderWidgets,
  updateWidgetPosition,
  toggleWidgetActive,
} = dashboardSlice.actions;

// Sélecteurs
export const selectUserConfig = (state) => state.dashboard.userConfig;
export const selectDashboardData = (state) => state.dashboard.dashboardData;
export const selectCustomDashboards = (state) => state.dashboard.customDashboards;
export const selectCurrentDashboard = (state) => state.dashboard.currentDashboard;
export const selectWidgets = (state) => state.dashboard.widgets;
export const selectNetworkOverview = (state) => state.dashboard.networkOverview;
export const selectSystemHealth = (state) => state.dashboard.systemHealth;
export const selectIsRealTimeEnabled = (state) => state.dashboard.isRealTimeEnabled;
export const selectWebSocketStatus = (state) => state.dashboard.websocketStatus;
export const selectDashboardLoading = (state) => state.dashboard.loading;
export const selectDashboardError = (state) => state.dashboard.error;
export const selectDashboardLayout = (state) => state.dashboard.layout;
export const selectDashboardFilters = (state) => state.dashboard.filters;
export const selectDashboardSorting = (state) => state.dashboard.sorting;

// Sélecteurs composés
export const selectWidgetById = (widgetId) => (state) =>
  state.dashboard.widgets.find(widget => widget.id === widgetId);

export const selectWidgetsByType = (widgetType) => (state) =>
  state.dashboard.widgets.filter(widget => widget.widget_type === widgetType);

export const selectActiveWidgets = (state) =>
  state.dashboard.widgets.filter(widget => widget.is_active);

export const selectDefaultDashboards = (state) =>
  state.dashboard.customDashboards.filter(dashboard => dashboard.is_default);

export const selectPublicDashboards = (state) =>
  state.dashboard.customDashboards.filter(dashboard => dashboard.is_public);

export const selectIsDashboardLoading = (state) =>
  Object.values(state.dashboard.loading || {}).some(loading => loading);

export const selectDashboardStats = (state) => ({
  totalDashboards: state.dashboard.customDashboards.length,
  totalWidgets: state.dashboard.widgets.length,
  activeWidgets: state.dashboard.widgets.filter(w => w.is_active).length,
  defaultDashboards: state.dashboard.customDashboards.filter(d => d.is_default).length,
  publicDashboards: state.dashboard.customDashboards.filter(d => d.is_public).length,
  isRealTimeConnected: state.dashboard.isRealTimeEnabled,
  lastUpdate: state.dashboard.lastRealTimeUpdate
});

export default dashboardSlice.reducer;