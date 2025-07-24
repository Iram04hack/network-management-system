/**
 * Store Redux principal pour AI Assistant
 * Configuration avec Redux Toolkit + intégration services validés Phase 1
 * Respect de la contrainte 95.65% de données réelles
 */

import { configureStore } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';

// Import des slices
import conversationsSlice from './slices/conversationsSlice';
import messagesSlice from './slices/messagesSlice';
import documentsSlice from './slices/documentsSlice';
import commandsSlice from './slices/commandsSlice';
import searchSlice from './slices/searchSlice';
import uiSlice from './slices/uiSlice';
import apiClientsSlice from './slices/apiClientsSlice';
import apiViewsSlice from './slices/apiViewsSlice';
import dashboardSlice from './slices/dashboardSlice';
import gns3Slice from './slices/gns3Slice';

// Import du service AI Assistant validé Phase 1
import aiAssistantService from '../services/aiAssistantService';

/**
 * Configuration du store Redux avec Redux Toolkit
 */
export const store = configureStore({
  reducer: {
    // Slice UI pour l'état de l'interface (test minimal)
    ui: uiSlice,

    // Slices métier AI Assistant
    conversations: conversationsSlice,
    messages: messagesSlice,
    documents: documentsSlice,
    commands: commandsSlice,
    search: searchSlice,
    
    // Slices modules intégrés
    apiClients: apiClientsSlice,
    apiViews: apiViewsSlice,
    dashboard: dashboardSlice,
    gns3: gns3Slice,
  },

  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      // Configuration pour les données non-sérialisables (dates, etc.)
      serializableCheck: {
        ignoredActions: [
          // Actions qui peuvent contenir des dates ou objets complexes
          'conversations/createConversation/fulfilled',
          'messages/sendMessage/fulfilled',
          'documents/uploadDocument/fulfilled',
        ],
        ignoredPaths: [
          // Chemins dans le state qui peuvent contenir des données non-sérialisables
          'conversations.items.*.created_at',
          'conversations.items.*.updated_at',
          'messages.items.*.created_at',
          'documents.items.*.created_at',
          'documents.items.*.updated_at',
        ],
      },

      // Configuration pour les actions immuables
      immutableCheck: {
        warnAfter: 128, // Warn si les checks prennent plus de 128ms
      },
    }),

  // DevTools en développement uniquement
  devTools: import.meta.env.DEV,

  // État initial pour l'hydratation SSR (si nécessaire)
  preloadedState: undefined,
});

// Configuration des listeners pour RTK Query (si utilisé plus tard)
setupListeners(store.dispatch);

/**
 * Types TypeScript pour le store (si migration vers TS)
 */
export const selectConversations = (state) => state.conversations;
export const selectMessages = (state) => state.messages;
export const selectDocuments = (state) => state.documents;
export const selectCommands = (state) => state.commands;
export const selectSearch = (state) => state.search;
export const selectUI = (state) => state.ui;

/**
 * Actions globales pour l'intégration avec le service AI Assistant
 */
export const initializeStore = () => async (dispatch) => {
  try {
    // Test de connectivité avec le backend validé Phase 1
    const connectionTest = await aiAssistantService.testConnection();

    if (connectionTest.success) {
      dispatch(uiSlice.actions.setConnectionStatus('connected'));
      dispatch(uiSlice.actions.setApiStats(connectionTest));

      // Charger les données initiales si connecté
      dispatch(conversationsSlice.actions.fetchConversations());
    } else {
      dispatch(uiSlice.actions.setConnectionStatus('disconnected'));
      dispatch(uiSlice.actions.setError({
        type: 'CONNECTION_ERROR',
        message: 'Impossible de se connecter au backend AI Assistant',
        details: connectionTest
      }));
    }
  } catch (error) {
    dispatch(uiSlice.actions.setConnectionStatus('error'));
    dispatch(uiSlice.actions.setError({
      type: 'INITIALIZATION_ERROR',
      message: 'Erreur lors de l\'initialisation du store',
      details: error.message
    }));
  }
};

/**
 * Action pour valider la contrainte de données réelles (95.65%)
 */
export const validateDataReality = () => async (dispatch) => {
  try {
    const validation = aiAssistantService.validateDataReality();

    dispatch(uiSlice.actions.setDataValidation(validation));

    if (validation.compliance.actual < validation.compliance.required) {
      dispatch(uiSlice.actions.setError({
        type: 'DATA_COMPLIANCE_ERROR',
        message: `Contrainte de données réelles non respectée: ${validation.compliance.actual}% < ${validation.compliance.required}%`,
        details: validation
      }));
    }
  } catch (error) {
    dispatch(uiSlice.actions.setError({
      type: 'VALIDATION_ERROR',
      message: 'Erreur lors de la validation des données réelles',
      details: error.message
    }));
  }
};

/**
 * Utilitaires pour les tests
 */
export const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      conversations: conversationsSlice,
      messages: messagesSlice,
      documents: documentsSlice,
      commands: commandsSlice,
      search: searchSlice,
      ui: uiSlice,
    },
    preloadedState: initialState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
        immutableCheck: false,
      }),
  });
};

/**
 * Persistance du store (localStorage)
 */
export const persistStore = () => {
  const state = store.getState();

  // Sauvegarder seulement les données importantes (pas les états de loading)
  const persistedState = {
    conversations: {
      items: state.conversations.items,
      currentConversation: state.conversations.currentConversation,
    },
    ui: {
      theme: state.ui.theme,
      preferences: state.ui.preferences,
    },
  };

  try {
    localStorage.setItem('aiAssistantStore', JSON.stringify(persistedState));
  } catch (error) {
    console.warn('Failed to persist store to localStorage:', error);
  }
};

/**
 * Restauration du store depuis localStorage
 */
export const loadPersistedState = () => {
  try {
    const serializedState = localStorage.getItem('aiAssistantStore');
    if (serializedState === null) {
      return undefined;
    }

    const persistedState = JSON.parse(serializedState);

    // Valider la structure des données persistées
    if (persistedState && typeof persistedState === 'object') {
      return persistedState;
    }
  } catch (error) {
    console.warn('Failed to load persisted state from localStorage:', error);
  }

  return undefined;
};

// Sauvegarder le store à chaque changement (avec debounce)
let saveTimeout;
store.subscribe(() => {
  clearTimeout(saveTimeout);
  saveTimeout = setTimeout(persistStore, 1000); // Debounce de 1 seconde
});

export default store;