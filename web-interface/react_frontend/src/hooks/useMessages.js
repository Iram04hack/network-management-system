/**
 * Hook personnalisé pour la gestion des messages
 * Envoi, réception, composition et historique des messages
 */

import { useCallback, useMemo, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchMessages,
  fetchMessage,
  sendMessage,
  setCurrentMessage,
  clearCurrentMessage,
  updateCurrentMessageContent,
  clearError
} from '../store/slices/messagesSlice';

// Sélecteurs mémorisés
import { createSelector } from '@reduxjs/toolkit';

const selectMessagesState = (state) => state?.messages || {};

const selectAllMessages = createSelector(
  [selectMessagesState],
  (messagesState) => messagesState.items || []
);

const selectCurrentMessage = createSelector(
  [selectMessagesState],
  (messagesState) => messagesState.currentMessage || { content: '', role: 'user' }
);

const selectMessagesLoading = createSelector(
  [selectMessagesState],
  (messagesState) => messagesState.loading || {}
);

const selectMessagesError = createSelector(
  [selectMessagesState],
  (messagesState) => messagesState.error || null
);

const selectRealTimeStatus = createSelector(
  [selectMessagesState],
  (messagesState) => messagesState.realTimeStatus || 'disconnected'
);

const selectMessagesStats = createSelector(
  [selectMessagesState],
  (messagesState) => messagesState.stats || {}
);

/**
 * Hook principal pour la gestion des messages
 */
export const useMessages = () => {
  const dispatch = useDispatch();
  
  // Sélecteurs Redux avec gestion d'erreur
  const messages = useSelector(selectAllMessages);
  const currentMessage = useSelector(selectCurrentMessage);
  const loading = useSelector(selectMessagesLoading);
  const error = useSelector(selectMessagesError);
  const realTimeStatus = useSelector(selectRealTimeStatus);
  const stats = useSelector(selectMessagesStats);

  // Actions de base
  const actions = useMemo(() => ({
    fetchMessages: (params) => dispatch(fetchMessages(params)),
    sendMessage: (message) => dispatch(sendMessage(message)),
    setCurrentMessage: (message) => dispatch(setCurrentMessage(message)),
    clearCurrentMessage: () => dispatch(clearCurrentMessage()),
    updateCurrentMessageContent: (content) => dispatch(updateCurrentMessageContent(content)),
    clearError: () => dispatch(clearError())
  }), [dispatch]);

  // Callbacks optimisés - sortis du useMemo pour éviter les hooks conditionnels
  const refresh = useCallback((params = {}) => {
    return actions.fetchMessages(params);
  }, [actions]);
  
  // Envoyer un message rapide
  const quickSend = useCallback((content, metadata = {}) => {
    return actions.sendMessage({
      content,
      role: 'user',
      metadata: {
        timestamp: new Date().toISOString(),
        ...metadata,
      },
    });
  }, [actions]);
  
  // Composer un message
  const startComposing = useCallback((initialContent = '') => {
    actions.setCurrentMessage({
      content: initialContent,
      role: 'user',
      metadata: {
        startedAt: new Date().toISOString(),
      },
    });
  }, [actions]);
  
  // Mettre à jour le contenu en cours de composition
  const updateComposition = useCallback((content) => {
    actions.updateCurrentMessageContent(content);
  }, [actions]);
  
  // Envoyer le message en cours de composition
  const sendCurrentMessage = useCallback(() => {
    if (currentMessage.content.trim()) {
      const messageToSend = { ...currentMessage };
      actions.clearCurrentMessage();
      return actions.sendMessage(messageToSend);
    }
    return Promise.resolve();
  }, [actions, currentMessage]);
  
  // Annuler la composition
  const cancelComposition = useCallback(() => {
    actions.clearCurrentMessage();
  }, [actions]);

  // Regrouper tous les callbacks
  const callbacks = useMemo(() => ({
    refresh,
    quickSend,
    startComposing,
    updateComposition,
    sendCurrentMessage,
    cancelComposition
  }), [refresh, quickSend, startComposing, updateComposition, sendCurrentMessage, cancelComposition]);

  // Utilitaires
  const utils = useMemo(() => ({
    // Filtrer les messages par type
    filterByType: (type) => messages.filter(msg => msg.type === type),
    
    // Obtenir les messages récents
    getRecentMessages: (count = 10) => 
      messages.slice(-count).reverse(),
    
    // Rechercher dans les messages
    searchMessages: (query) => 
      messages.filter(msg => 
        msg.content.toLowerCase().includes(query.toLowerCase())
      ),
    
    // Obtenir les statistiques
    getStats: () => ({
      total: messages.length,
      unread: messages.filter(msg => !msg.read).length,
      byType: messages.reduce((acc, msg) => {
        acc[msg.type] = (acc[msg.type] || 0) + 1;
        return acc;
      }, {}),
    }),
  }), [messages]);

  // État dérivé
  const isLoading = useMemo(() => 
    Object.values(loading).some(loading => loading), 
    [loading]
  );

  const lastMessage = useMemo(() => 
    messages.length > 0 ? messages[messages.length - 1] : null, 
    [messages]
  );

  const messageCount = useMemo(() => 
    messages.length, 
    [messages]
  );

  // Gestion du temps réel
  useEffect(() => {
    // Ici on pourrait ajouter la logique WebSocket
    // pour les messages en temps réel
  }, []);

  return {
    // État
    messages,
    currentMessage,
    loading,
    error,
    realTimeStatus,
    stats,
    isLoading,
    lastMessage,
    messageCount,
    
    // Actions
    ...actions,
    
    // Utilitaires
    ...utils,
    
    // Callbacks optimisés
    ...callbacks,
  };
};

/**
 * Hook pour un message spécifique
 */
export const useMessage = (messageId) => {
  const dispatch = useDispatch();
  const allMessages = useSelector(selectAllMessages);
  const loading = useSelector(selectMessagesLoading);
  const error = useSelector(selectMessagesError);
  
  const message = useMemo(() => 
    allMessages.find(msg => msg.id === messageId), 
    [allMessages, messageId]
  );

  const actions = useMemo(() => ({
    fetch: () => dispatch(fetchMessage(messageId)),
    refresh: () => dispatch(fetchMessage(messageId)),
  }), [dispatch, messageId]);

  return {
    message,
    loading: loading[messageId] || false,
    error,
    ...actions,
  };
};

/**
 * Hook pour la composition de messages
 */
export const useMessageComposer = () => {
  const { currentMessage, updateComposition, sendCurrentMessage, cancelComposition } = useMessages();
  
  const isComposing = useMemo(() => 
    currentMessage.content.length > 0, 
    [currentMessage.content]
  );

  const canSend = useMemo(() => 
    currentMessage.content.trim().length > 0, 
    [currentMessage.content]
  );

  return {
    currentMessage,
    isComposing,
    canSend,
    updateComposition,
    sendCurrentMessage,
    cancelComposition,
  };
};

export default useMessages;
