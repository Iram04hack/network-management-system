/**
 * Hook personnalisé pour la gestion des conversations
 * Intégration avec le store Redux et optimisations React
 */

import { useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchConversations,
  createConversation,
  fetchConversation,
  updateConversation,
  deleteConversation,
  setCurrentConversation,
  clearCurrentConversation,
  setFilters,
  setSorting,
  clearFilters,
  clearError,
  optimisticUpdateConversation,
  selectConversations,
  selectCurrentConversation,
  selectConversationsPagination,
  selectConversationsLoading,
  selectConversationsError,
  selectConversationsFilters,
  selectConversationsSorting,
  selectConversationById,
  selectIsConversationLoading,
} from '../store/slices/conversationsSlice';

/**
 * Hook principal pour la gestion des conversations
 */
export const useConversations = () => {
  const dispatch = useDispatch();
  
  // Sélecteurs Redux avec gestion d'erreur
  const conversations = useSelector((state) => state?.conversations?.items || []);
  const currentConversation = useSelector((state) => state?.conversations?.currentConversation || null);
  const pagination = useSelector((state) => state?.conversations?.pagination || {});
  const loading = useSelector((state) => state?.conversations?.loading || {});
  const error = useSelector((state) => state?.conversations?.error || null);
  const filters = useSelector((state) => state?.conversations?.filters || {});
  const sorting = useSelector((state) => state?.conversations?.sorting || {});
  const isLoading = useSelector((state) => Object.values(state?.conversations?.loading || {}).some(loading => loading));

  // Actions avec useCallback pour stabilité des références
  const fetchConversations = useCallback((params) => {
    return dispatch(fetchConversations(params));
  }, [dispatch]);

  const createConversation = useCallback((conversationData) => {
    return dispatch(createConversation(conversationData));
  }, [dispatch]);

  const fetchConversation = useCallback((conversationId) => {
    return dispatch(fetchConversation(conversationId));
  }, [dispatch]);

  const updateConversation = useCallback((conversationId, updateData) => {
    return dispatch(updateConversation({ conversationId, updateData }));
  }, [dispatch]);

  const deleteConversation = useCallback((conversationId) => {
    return dispatch(deleteConversation(conversationId));
  }, [dispatch]);

  const setCurrentConversation = useCallback((conversation) => {
    return dispatch(setCurrentConversation(conversation));
  }, [dispatch]);

  const clearCurrentConversation = useCallback(() => {
    return dispatch(clearCurrentConversation());
  }, [dispatch]);

  const setFilters = useCallback((newFilters) => {
    return dispatch(setFilters(newFilters));
  }, [dispatch]);

  const setSorting = useCallback((newSorting) => {
    return dispatch(setSorting(newSorting));
  }, [dispatch]);

  const clearFilters = useCallback(() => {
    return dispatch(clearFilters());
  }, [dispatch]);

  const clearError = useCallback(() => {
    return dispatch(clearError());
  }, [dispatch]);

  const optimisticUpdate = useCallback((conversationId, updateData) => {
    return dispatch(optimisticUpdateConversation({ conversationId, updateData }));
  }, [dispatch]);

  // Fonctions utilitaires mémorisées
  const utils = useMemo(() => ({
    // Rechercher une conversation par ID
    getConversationById: (conversationId) => 
      conversations.find(conv => conv.id === conversationId),
    
    // Filtrer les conversations
    getFilteredConversations: (customFilters = {}) => {
      const activeFilters = { ...filters, ...customFilters };
      return conversations.filter(conv => {
        if (activeFilters.search && !conv.title.toLowerCase().includes(activeFilters.search.toLowerCase())) {
          return false;
        }
        if (activeFilters.hasMessages !== null && (conv.message_count > 0) !== activeFilters.hasMessages) {
          return false;
        }
        if (activeFilters.createdAfter && new Date(conv.created_at) < new Date(activeFilters.createdAfter)) {
          return false;
        }
        if (activeFilters.createdBefore && new Date(conv.created_at) > new Date(activeFilters.createdBefore)) {
          return false;
        }
        return true;
      });
    },
    
    // Trier les conversations
    getSortedConversations: (conversationsToSort = conversations) => {
      const { field, direction } = sorting;
      return [...conversationsToSort].sort((a, b) => {
        let aValue = a[field];
        let bValue = b[field];
        
        // Gestion des dates
        if (field.includes('_at')) {
          aValue = new Date(aValue);
          bValue = new Date(bValue);
        }
        
        // Gestion des chaînes
        if (typeof aValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }
        
        if (direction === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });
    },
    
    // Statistiques des conversations
    getStats: () => ({
      total: conversations.length,
      withMessages: conversations.filter(conv => conv.message_count > 0).length,
      withoutMessages: conversations.filter(conv => conv.message_count === 0).length,
      averageMessages: conversations.reduce((sum, conv) => sum + (conv.message_count || 0), 0) / conversations.length || 0,
      mostRecent: conversations.length > 0 ? 
        conversations.reduce((latest, conv) => 
          new Date(conv.created_at) > new Date(latest.created_at) ? conv : latest
        ) : null,
    }),
  }), [conversations, filters, sorting]);

  // Actions regroupées pour réutilisation dans les callbacks
  const actions = useMemo(() => ({
    fetchConversations: (params) => dispatch(fetchConversations(params)),
    createConversation: (conversationData) => dispatch(createConversation(conversationData)),
    setCurrentConversation: (conversation) => dispatch(setCurrentConversation(conversation)),
    deleteConversation: (conversationId) => dispatch(deleteConversation(conversationId)),
    setFilters: (newFilters) => dispatch(setFilters(newFilters))
  }), [dispatch]);

  // Callbacks optimisés - sortis du useMemo pour éviter les hooks conditionnels
  const refresh = useCallback((params = {}) => {
    return actions.fetchConversations(params);
  }, [actions]);

  const createAndSelect = useCallback(async (conversationData) => {
    const result = await actions.createConversation(conversationData);
    if (result.payload) {
      actions.setCurrentConversation(result.payload);
    }
    return result;
  }, [actions]);

  const deleteWithConfirmation = useCallback(async (conversationId, confirmCallback) => {
    if (confirmCallback && !confirmCallback()) {
      return { cancelled: true };
    }
    return actions.deleteConversation(conversationId);
  }, [actions]);

  const quickSearch = useCallback((searchTerm) => {
    actions.setFilters({ search: searchTerm });
  }, [actions]);

  const goToPage = useCallback((page) => {
    actions.fetchConversations({ page });
  }, [actions]);

  const nextPage = useCallback(() => {
    if (pagination.hasNext) {
      actions.fetchConversations({ page: pagination.currentPage + 1 });
    }
  }, [actions, pagination]);

  const previousPage = useCallback(() => {
    if (pagination.hasPrevious) {
      actions.fetchConversations({ page: pagination.currentPage - 1 });
    }
  }, [actions, pagination]);

  // Regrouper tous les callbacks
  const callbacks = useMemo(() => ({
    refresh,
    createAndSelect,
    deleteWithConfirmation,
    quickSearch,
    goToPage,
    nextPage,
    previousPage
  }), [refresh, createAndSelect, deleteWithConfirmation, quickSearch, goToPage, nextPage, previousPage]);

  return {
    // État
    conversations,
    currentConversation,
    pagination,
    loading,
    error,
    filters,
    sorting,
    isLoading,

    // Actions stables avec useCallback
    fetchConversations,
    createConversation,
    fetchConversation,
    updateConversation,
    deleteConversation,
    setCurrentConversation,
    clearCurrentConversation,
    setFilters,
    setSorting,
    clearFilters,
    clearError,
    optimisticUpdate,

    // Utilitaires
    ...utils,

    // Callbacks optimisés
    ...callbacks,
  };
};

/**
 * Hook pour une conversation spécifique
 */
export const useConversation = (conversationId) => {
  const dispatch = useDispatch();
  const conversation = useSelector(selectConversationById(conversationId));
  const loading = useSelector(selectConversationsLoading);
  const error = useSelector(selectConversationsError);

  const actions = useMemo(() => ({
    fetch: () => dispatch(fetchConversation(conversationId)),
    update: (updateData) => dispatch(updateConversation({ conversationId, updateData })),
    delete: () => dispatch(deleteConversation(conversationId)),
    select: () => dispatch(setCurrentConversation(conversation)),
  }), [dispatch, conversationId, conversation]);

  return {
    conversation,
    loading,
    error,
    ...actions,
  };
};

/**
 * Hook pour les statistiques des conversations
 */
export const useConversationsStats = () => {
  const conversations = useSelector(selectConversations);
  
  return useMemo(() => ({
    total: conversations.length,
    withMessages: conversations.filter(conv => conv.message_count > 0).length,
    withoutMessages: conversations.filter(conv => conv.message_count === 0).length,
    averageMessages: conversations.reduce((sum, conv) => sum + (conv.message_count || 0), 0) / conversations.length || 0,
    mostRecent: conversations.length > 0 ? 
      conversations.reduce((latest, conv) => 
        new Date(conv.created_at) > new Date(latest.created_at) ? conv : latest
      ) : null,
    oldestActive: conversations.length > 0 ? 
      conversations.reduce((oldest, conv) => 
        new Date(conv.created_at) < new Date(oldest.created_at) ? conv : oldest
      ) : null,
  }), [conversations]);
};

export default useConversations;
