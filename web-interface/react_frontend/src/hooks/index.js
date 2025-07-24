/**
 * Export centralisé de tous les hooks personnalisés AI Assistant
 * Phase 3 - Hooks React avec intégration Redux
 */

import { useCallback, useMemo, useEffect, useRef } from 'react';
import { useDispatch } from 'react-redux';
import { addRealTimeMessage } from '../store/slices/messagesSlice';

// Hooks principaux - Exports corrects
export { default as useConversations, useConversation, useConversationsStats } from './useConversations';
export { default as useMessages, useMessage, useMessageComposer } from './useMessages';
export { default as useDocuments } from './useDocuments';
export { default as useCommands, useCommandExecution } from './useCommands';
export { default as useSearch, useSpecializedSearch, useNetworkAnalysis } from './useSearch';
export { default as useUI } from './useUI';

// Import des hooks pour les hooks composés
import useConversations from './useConversations';
import useMessages from './useMessages';
import useDocuments from './useDocuments';
import useCommands from './useCommands';
import useSearch from './useSearch';
import useUI from './useUI';

export const useAIAssistant = (conversationId = null) => {
  const conversations = useConversations();
  const messages = useMessages(conversationId);
  const documents = useDocuments();
  const commands = useCommands();
  const search = useSearch();
  const ui = useUI();

  return {
    conversations,
    messages,
    documents,
    commands,
    search,
    ui,
    
    // États globaux
    isLoading: conversations.isLoading || messages.isLoading || documents.isLoading || 
               commands.loading.execute || search.loading || ui.globalLoading,
    
    hasError: conversations.error || messages.error || documents.error || 
              commands.error || search.error || ui.globalError,
    
    // Actions rapides
    quickActions: {
      sendMessage: messages.quickSend,
      createConversation: conversations.createAndSelect,
      uploadDocument: documents.uploadWithValidation,
      executeCommand: commands.quickExecute,
      search: search.quickSearch,
      showNotification: ui.showNotification,
    },
  };
};

/**
 * Hook pour la gestion du temps réel
 */

export const useRealTime = (conversationId) => {
  const dispatch = useDispatch();
  const { setRealTimeConnected, enableRealTime, disableRealTime } = useMessages(conversationId);

  const handleRealTimeMessage = useCallback((message) => {
    dispatch(addRealTimeMessage({
      conversationId: message.conversation,
      message,
    }));
  }, [dispatch]);

  const connectRealTime = useCallback(() => {
    // Simulation de connexion WebSocket
    enableRealTime();
    setRealTimeConnected(true);
    
    // Ici on connecterait vraiment à un WebSocket
    // const ws = new WebSocket('ws://localhost:8000/ws/messages/');
    // ws.onmessage = (event) => {
    //   const message = JSON.parse(event.data);
    //   handleRealTimeMessage(message);
    // };
    
    return () => {
      setRealTimeConnected(false);
      disableRealTime();
    };
  }, [enableRealTime, disableRealTime, setRealTimeConnected, handleRealTimeMessage]);

  // DÉSACTIVÉ TEMPORAIREMENT POUR ARRÊTER LA BOUCLE
  useEffect(() => {
    console.log('🔄 useRealTime useEffect triggered:', {
      conversationId,
      connectRealTimeType: typeof connectRealTime,
      timestamp: new Date().toISOString()
    });

    // DÉSACTIVÉ TEMPORAIREMENT POUR ARRÊTER LA BOUCLE
    // if (conversationId) {
    //   const cleanup = connectRealTime();
    //   return cleanup;
    // }
  }, [conversationId, connectRealTime]);

  return {
    handleRealTimeMessage,
    connectRealTime,
  };
};

/**
 * Hook pour le monitoring des performances
 */

export const usePerformance = () => {
  const { setPageLoadTime, addApiResponseTime, getPerformanceMetrics } = useUI();
  const startTimeRef = useRef(Date.now());

  // Mesurer le temps de chargement de la page
  useEffect(() => {
    const handleLoad = () => {
      const loadTime = Date.now() - startTimeRef.current;
      setPageLoadTime(loadTime);
    };

    if (document.readyState === 'complete') {
      handleLoad();
    } else {
      window.addEventListener('load', handleLoad);
      return () => window.removeEventListener('load', handleLoad);
    }
  }, [setPageLoadTime]);

  // Fonction pour mesurer les appels API
  const measureApiCall = useCallback((endpoint, apiCall) => {
    const startTime = Date.now();
    
    return apiCall().finally(() => {
      const responseTime = Date.now() - startTime;
      addApiResponseTime(endpoint, responseTime);
    });
  }, [addApiResponseTime]);

  return {
    measureApiCall,
    getPerformanceMetrics,
  };
};

/**
 * Types de hooks disponibles pour référence
 */
export const HOOK_TYPES = {
  // Hooks de données
  DATA: {
    CONVERSATIONS: 'useConversations',
    MESSAGES: 'useMessages', 
    DOCUMENTS: 'useDocuments',
    COMMANDS: 'useCommands',
    SEARCH: 'useSearch',
  },
  
  // Hooks d'interface
  UI: {
    MAIN: 'useUI',
    NOTIFICATIONS: 'useNotifications',
    MODALS: 'useModals',
    THEME: 'useTheme',
  },
  
  // Hooks composés
  COMPOSED: {
    AI_ASSISTANT: 'useAIAssistant',
    REAL_TIME: 'useRealTime',
    PERFORMANCE: 'usePerformance',
  },
  
  // Hooks spécialisés
  SPECIALIZED: {
    CONVERSATION: 'useConversation',
    MESSAGE: 'useMessage',
    DOCUMENT: 'useDocument',
    MESSAGE_COMPOSER: 'useMessageComposer',
    DOCUMENT_UPLOAD: 'useDocumentUpload',
    DOCUMENT_SEARCH: 'useDocumentSearch',
    COMMAND_EXECUTION: 'useCommandExecution',
    SPECIALIZED_SEARCH: 'useSpecializedSearch',
    NETWORK_ANALYSIS: 'useNetworkAnalysis',
  },
};

/**
 * Configuration des hooks pour différents contextes
 */
export const HOOK_CONFIGS = {
  // Configuration pour une page de conversation
  CONVERSATION_PAGE: [
    'useConversations',
    'useMessages',
    'useMessageComposer',
    'useRealTime',
    'useUI',
  ],
  
  // Configuration pour une page de documents
  DOCUMENTS_PAGE: [
    'useDocuments',
    'useDocumentUpload',
    'useDocumentSearch',
    'useUI',
  ],
  
  // Configuration pour une page de recherche
  SEARCH_PAGE: [
    'useSearch',
    'useSpecializedSearch',
    'useNetworkAnalysis',
    'useUI',
  ],
  
  // Configuration pour le dashboard principal
  DASHBOARD: [
    'useAIAssistant',
    'usePerformance',
    'useUI',
  ],
};

/**
 * Utilitaires pour les hooks
 */
export const hookUtils = {
  // Vérifier si un hook est disponible
  isHookAvailable: (hookName) => {
    return Object.values(HOOK_TYPES).some(category => 
      Object.values(category).includes(hookName)
    );
  },
  
  // Obtenir la configuration recommandée pour une page
  getRecommendedHooks: (pageType) => {
    return HOOK_CONFIGS[pageType] || [];
  },
  
  // Obtenir tous les hooks de données
  getDataHooks: () => Object.values(HOOK_TYPES.DATA),
  
  // Obtenir tous les hooks d'interface
  getUIHooks: () => Object.values(HOOK_TYPES.UI),
};
