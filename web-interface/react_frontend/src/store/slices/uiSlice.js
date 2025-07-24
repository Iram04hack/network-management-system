/**
 * Slice Redux pour la gestion de l'état UI
 * Interface utilisateur, thème, notifications, etc.
 */

import { createSlice, createSelector } from '@reduxjs/toolkit';

const initialState = {
  // Thème et apparence
  theme: 'light', // 'light', 'dark', 'auto'
  
  // État de connexion
  connectionStatus: 'disconnected', // 'connected', 'disconnected', 'connecting', 'error'
  apiStats: null,
  
  // Notifications et alertes
  notifications: [],
  alerts: [],
  
  // Modales et overlays
  modals: {
    createConversation: false,
    uploadDocument: false,
    settings: false,
    help: false,
  },
  
  // Sidebars et panels
  sidebars: {
    conversations: true,
    documents: false,
    search: false,
  },
  
  // Chatbot AI Assistant
  chatbot: {
    isOpen: false,
    position: 'bottom-right', // 'bottom-right', 'bottom-left', 'center'
    size: 'medium', // 'small', 'medium', 'large'
    minimized: false,
  },
  
  // Préférences utilisateur
  preferences: {
    autoSave: true,
    notifications: true,
    soundEnabled: false,
    animationsEnabled: true,
    compactMode: false,
    defaultPageSize: 20,
  },
  
  // États de chargement globaux
  globalLoading: false,
  
  // Erreurs globales
  globalError: null,
  
  // Validation des données réelles
  dataValidation: null,
  
  // Statistiques du service
  serviceStats: null,
  
  // Breadcrumbs de navigation
  breadcrumbs: [],
  
  // État de la recherche UI
  searchUI: {
    isExpanded: false,
    recentSearches: [],
    filters: {
      showAdvanced: false,
    },
  },
  
  // Performance monitoring
  performance: {
    pageLoadTime: null,
    apiResponseTimes: [],
    errorCount: 0,
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    // Thème
    setTheme: (state, action) => {
      state.theme = action.payload;
    },
    
    toggleTheme: (state) => {
      state.theme = state.theme === 'light' ? 'dark' : 'light';
    },
    
    // Connexion
    setConnectionStatus: (state, action) => {
      state.connectionStatus = action.payload;
    },
    
    setApiStats: (state, action) => {
      state.apiStats = action.payload;
    },
    
    // Notifications
    addNotification: (state, action) => {
      const notification = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        ...action.payload,
      };
      state.notifications.unshift(notification);
      
      // Garder seulement les 50 dernières notifications
      if (state.notifications.length > 50) {
        state.notifications = state.notifications.slice(0, 50);
      }
    },
    
    removeNotification: (state, action) => {
      state.notifications = state.notifications.filter(
        notif => notif.id !== action.payload
      );
    },
    
    clearNotifications: (state) => {
      state.notifications = [];
    },
    
    // Alertes
    addAlert: (state, action) => {
      const alert = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        ...action.payload,
      };
      state.alerts.push(alert);
    },
    
    removeAlert: (state, action) => {
      state.alerts = state.alerts.filter(alert => alert.id !== action.payload);
    },
    
    clearAlerts: (state) => {
      state.alerts = [];
    },
    
    // Modales
    openModal: (state, action) => {
      state.modals[action.payload] = true;
    },
    
    closeModal: (state, action) => {
      state.modals[action.payload] = false;
    },
    
    closeAllModals: (state) => {
      Object.keys(state.modals).forEach(modal => {
        state.modals[modal] = false;
      });
    },
    
    // Sidebars
    toggleSidebar: (state, action) => {
      state.sidebars[action.payload] = !state.sidebars[action.payload];
    },
    
    setSidebar: (state, action) => {
      const { sidebar, isOpen } = action.payload;
      state.sidebars[sidebar] = isOpen;
    },
    
    // Chatbot
    toggleChatbot: (state) => {
      state.chatbot.isOpen = !state.chatbot.isOpen;
    },
    
    setChatbotOpen: (state, action) => {
      state.chatbot.isOpen = action.payload;
    },
    
    setChatbotPosition: (state, action) => {
      state.chatbot.position = action.payload;
    },
    
    setChatbotSize: (state, action) => {
      state.chatbot.size = action.payload;
    },
    
    minimizeChatbot: (state) => {
      state.chatbot.minimized = true;
    },
    
    maximizeChatbot: (state) => {
      state.chatbot.minimized = false;
    },
    
    // Préférences
    setPreferences: (state, action) => {
      state.preferences = { ...state.preferences, ...action.payload };
    },
    
    resetPreferences: (state) => {
      state.preferences = initialState.preferences;
    },
    
    // États globaux
    setGlobalLoading: (state, action) => {
      state.globalLoading = action.payload;
    },
    
    setError: (state, action) => {
      state.globalError = action.payload;
      
      // Ajouter aussi comme notification d'erreur
      if (action.payload) {
        const errorNotification = {
          id: Date.now(),
          type: 'error',
          title: 'Erreur',
          message: action.payload.message || 'Une erreur est survenue',
          timestamp: new Date().toISOString(),
          autoClose: false,
        };
        state.notifications.unshift(errorNotification);
      }
    },
    
    clearError: (state) => {
      state.globalError = null;
    },
    
    // Validation des données
    setDataValidation: (state, action) => {
      state.dataValidation = action.payload;
      
      // Ajouter une notification si la validation échoue
      if (action.payload && action.payload.compliance.status !== 'COMPLIANT') {
        const validationAlert = {
          id: Date.now(),
          type: 'warning',
          title: 'Contrainte de données non respectée',
          message: `${action.payload.compliance.actual}% < ${action.payload.compliance.required}% requis`,
          timestamp: new Date().toISOString(),
        };
        state.alerts.push(validationAlert);
      }
    },
    
    // Statistiques du service
    updateServiceStats: (state, action) => {
      state.serviceStats = action.payload;
    },
    
    // Breadcrumbs
    setBreadcrumbs: (state, action) => {
      state.breadcrumbs = action.payload;
    },
    
    addBreadcrumb: (state, action) => {
      state.breadcrumbs.push(action.payload);
    },
    
    // Recherche UI
    setSearchExpanded: (state, action) => {
      state.searchUI.isExpanded = action.payload;
    },
    
    toggleSearchExpanded: (state) => {
      state.searchUI.isExpanded = !state.searchUI.isExpanded;
    },
    
    setSearchFilters: (state, action) => {
      state.searchUI.filters = { ...state.searchUI.filters, ...action.payload };
    },
    
    // Performance
    setPageLoadTime: (state, action) => {
      state.performance.pageLoadTime = action.payload;
    },
    
    addApiResponseTime: (state, action) => {
      state.performance.apiResponseTimes.push({
        endpoint: action.payload.endpoint,
        responseTime: action.payload.responseTime,
        timestamp: new Date().toISOString(),
      });
      
      // Garder seulement les 100 dernières mesures
      if (state.performance.apiResponseTimes.length > 100) {
        state.performance.apiResponseTimes = state.performance.apiResponseTimes.slice(-100);
      }
    },
    
    incrementErrorCount: (state) => {
      state.performance.errorCount += 1;
    },
    
    resetPerformanceStats: (state) => {
      state.performance = initialState.performance;
    },
  },
});

// Export des actions
export const {
  setTheme,
  toggleTheme,
  setConnectionStatus,
  setApiStats,
  addNotification,
  removeNotification,
  clearNotifications,
  addAlert,
  removeAlert,
  clearAlerts,
  openModal,
  closeModal,
  closeAllModals,
  toggleSidebar,
  setSidebar,
  toggleChatbot,
  setChatbotOpen,
  setChatbotPosition,
  setChatbotSize,
  minimizeChatbot,
  maximizeChatbot,
  setPreferences,
  resetPreferences,
  setGlobalLoading,
  setError,
  clearError,
  setDataValidation,
  updateServiceStats,
  setBreadcrumbs,
  addBreadcrumb,
  setSearchExpanded,
  toggleSearchExpanded,
  setSearchFilters,
  setPageLoadTime,
  addApiResponseTime,
  incrementErrorCount,
  resetPerformanceStats,
} = uiSlice.actions;

// Sélecteurs
export const selectTheme = (state) => state.ui.theme;
export const selectConnectionStatus = (state) => state.ui.connectionStatus;
export const selectApiStats = (state) => state.ui.apiStats;
export const selectNotifications = (state) => state.ui.notifications;
export const selectAlerts = (state) => state.ui.alerts;
export const selectModals = (state) => state.ui.modals;
export const selectSidebars = (state) => state.ui.sidebars;
export const selectChatbot = (state) => state.ui.chatbot;
export const selectPreferences = (state) => state.ui.preferences;
export const selectGlobalLoading = (state) => state.ui.globalLoading;
export const selectGlobalError = (state) => state.ui.globalError;
export const selectDataValidation = (state) => state.ui.dataValidation;
export const selectServiceStats = (state) => state.ui.serviceStats;
export const selectBreadcrumbs = (state) => state.ui.breadcrumbs;
export const selectSearchUI = (state) => state.ui.searchUI;
export const selectPerformance = (state) => state.ui.performance;

// Sélecteurs composés
export const selectIsModalOpen = (modalName) => (state) => 
  state.ui.modals[modalName] || false;

export const selectIsSidebarOpen = (sidebarName) => (state) => 
  state.ui.sidebars[sidebarName] || false;

// Sélecteurs mémorisés avec createSelector pour éviter les re-renders
export const selectUnreadNotifications = createSelector(
  [(state) => state.ui.notifications || []],
  (notifications) => notifications.filter(notif => !notif.read)
);

export const selectActiveAlerts = createSelector(
  [(state) => state.ui.alerts || []],
  (alerts) => alerts.filter(alert => !alert.dismissed)
);

export default uiSlice.reducer;
