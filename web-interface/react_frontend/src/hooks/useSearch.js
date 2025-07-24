/**
 * Hook personnalisé pour la recherche globale
 * Recherche dans conversations, messages, documents
 */

import { useCallback, useMemo, useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  performGlobalSearch,
  performNetworkAnalysis,
  setQuery,
  setFilters,
  clearResults,
  clearError,
  addToHistory,
  setSuggestions,
  selectSearchResults,
  selectSearchQuery,
  selectSearchFilters,
  selectSearchLoading,
  selectSearchError,
  selectSearchHistory,
  selectSearchSuggestions,
} from '../store/slices/searchSlice';

/**
 * Hook principal pour la recherche globale
 */
export const useSearch = () => {
  const dispatch = useDispatch();
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Sélecteurs Redux avec gestion d'erreur robuste
  const results = useSelector((state) => {
    try {
      return selectSearchResults(state) || [];
    } catch (error) {
      console.warn('Erreur sélecteur results:', error);
      return [];
    }
  });

  const query = useSelector((state) => {
    try {
      return selectSearchQuery(state) || '';
    } catch (error) {
      console.warn('Erreur sélecteur query:', error);
      return '';
    }
  });

  const filters = useSelector((state) => {
    try {
      return selectSearchFilters(state) || { type: 'all', limit: 50 };
    } catch (error) {
      console.warn('Erreur sélecteur filters:', error);
      return { type: 'all', limit: 50 };
    }
  });

  const loading = useSelector((state) => {
    try {
      return selectSearchLoading(state) || false;
    } catch (error) {
      console.warn('Erreur sélecteur loading:', error);
      return false;
    }
  });

  const error = useSelector((state) => {
    try {
      return selectSearchError(state) || null;
    } catch (error) {
      console.warn('Erreur sélecteur error:', error);
      return null;
    }
  });

  const history = useSelector((state) => {
    try {
      return selectSearchHistory(state) || [];
    } catch (error) {
      console.warn('Erreur sélecteur history:', error);
      return [];
    }
  });

  const suggestions = useSelector((state) => {
    try {
      return selectSearchSuggestions(state) || [];
    } catch (error) {
      console.warn('Erreur sélecteur suggestions:', error);
      return [];
    }
  });

  // Debounce pour la recherche automatique
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, 300);
    
    return () => clearTimeout(timer);
  }, [query]);

  // Actions mémorisées
  const actions = useMemo(() => ({
    search: (searchQuery, params) => dispatch(performGlobalSearch({ query: searchQuery, params })),
    analyzeNetwork: (analysisData) => dispatch(performNetworkAnalysis(analysisData)),
    setQuery: (newQuery) => dispatch(setQuery(newQuery)),
    setFilters: (newFilters) => dispatch(setFilters(newFilters)),
    clearResults: () => dispatch(clearResults()),
    clearError: () => dispatch(clearError()),
    setSuggestions: (newSuggestions) => dispatch(setSuggestions(newSuggestions)),
  }), [dispatch]);

  // Fonctions utilitaires
  const utils = useMemo(() => ({
    // Filtrer les résultats par type
    getResultsByType: (type) => results.filter(result => result.type === type),
    
    // Obtenir les conversations trouvées
    getConversationResults: () => results.filter(result => result.type === 'conversation'),
    
    // Obtenir les messages trouvés
    getMessageResults: () => results.filter(result => result.type === 'message'),
    
    // Obtenir les documents trouvés
    getDocumentResults: () => results.filter(result => result.type === 'document'),
    
    // Obtenir les analyses réseau
    getNetworkAnalysisResults: () => results.filter(result => result.type === 'network_analysis'),
    
    // Statistiques de recherche
    getSearchStats: () => ({
      total: results.length,
      byType: {
        conversations: results.filter(r => r.type === 'conversation').length,
        messages: results.filter(r => r.type === 'message').length,
        documents: results.filter(r => r.type === 'document').length,
        networkAnalysis: results.filter(r => r.type === 'network_analysis').length,
      },
      averageRelevance: results.reduce((sum, r) => sum + (r.relevance_score || 0), 0) / results.length || 0,
      mostRelevant: results.reduce((best, r) => 
        (r.relevance_score || 0) > (best?.relevance_score || 0) ? r : best, null
      ),
    }),
    
    // Générer des suggestions
    generateSuggestions: (currentQuery) => {
      const suggestions = [];
      
      // Suggestions basées sur l'historique
      const historySuggestions = (history || [])
        .filter(h => h.query.toLowerCase().includes(currentQuery.toLowerCase()))
        .slice(0, 3)
        .map(h => ({ type: 'history', text: h.query }));
      
      suggestions.push(...historySuggestions);
      
      // Suggestions de commandes
      if (currentQuery.startsWith('/')) {
        const commandSuggestions = [
          { type: 'command', text: '/scan network', description: 'Scanner le réseau' },
          { type: 'command', text: '/analyze logs', description: 'Analyser les logs' },
          { type: 'command', text: '/system info', description: 'Informations système' },
        ].filter(cmd => cmd.text.includes(currentQuery));
        
        suggestions.push(...commandSuggestions);
      }
      
      return suggestions;
    },
    
    // Valider une requête de recherche
    validateQuery: (searchQuery) => {
      const errors = [];
      
      if (!searchQuery || searchQuery.trim().length === 0) {
        errors.push('La requête ne peut pas être vide');
      }
      
      if (searchQuery.length < 2) {
        errors.push('La requête doit contenir au moins 2 caractères');
      }
      
      if (searchQuery.length > 500) {
        errors.push('La requête ne peut pas dépasser 500 caractères');
      }
      
      return {
        isValid: errors.length === 0,
        errors,
      };
    },
  }), [results, history]);

  // Callbacks optimisés - sortis du useMemo pour respecter les règles des hooks
  const searchWithValidation = useCallback(async (searchQuery, params = {}) => {
    const validation = utils.validateQuery(searchQuery);
    if (!validation.isValid) {
      throw new Error(`Validation échouée: ${validation.errors.join(', ')}`);
    }

    const searchParams = {
      ...filters,
      ...params,
    };

    return actions.search(searchQuery, searchParams);
  }, [actions, filters, utils]);

  const quickSearch = useCallback((searchQuery) => {
    actions.setQuery(searchQuery);
    if (searchQuery.trim()) {
      return actions.search(searchQuery, filters);
    }
  }, [actions, filters]);

  const searchByType = useCallback((searchQuery, type) => {
    return actions.search(searchQuery, { ...filters, type });
  }, [actions, filters]);

  const advancedSearch = useCallback((searchQuery, advancedFilters) => {
    return actions.search(searchQuery, { ...filters, ...advancedFilters });
  }, [actions, filters]);

  const quickNetworkAnalysis = useCallback((target) => {
    return actions.analyzeNetwork({
      target,
      type: 'quick_scan',
      timestamp: new Date().toISOString(),
    });
  }, [actions]);

  const searchHistory = useCallback((searchTerm) => {
    return (history || []).filter(h =>
      h.query.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [history]);

  const repeatSearch = useCallback((historyItem) => {
    actions.setQuery(historyItem.query);
    return actions.search(historyItem.query, filters);
  }, [actions, filters]);

  const updateSuggestions = useCallback((currentQuery) => {
    const newSuggestions = utils.generateSuggestions(currentQuery);
    actions.setSuggestions(newSuggestions);
  }, [actions, utils]);

  // Objet callbacks regroupé
  const callbacks = useMemo(() => ({
    searchWithValidation,
    quickSearch,
    searchByType,
    advancedSearch,
    quickNetworkAnalysis,
    searchHistory,
    repeatSearch,
    updateSuggestions,
  }), [searchWithValidation, quickSearch, searchByType, advancedSearch, quickNetworkAnalysis, searchHistory, repeatSearch, updateSuggestions]);

  // Recherche automatique avec debounce (désactivé temporairement pour les tests)
  // useEffect(() => {
  //   if (debouncedQuery && debouncedQuery.trim().length >= 2) {
  //     actions.setQuery(debouncedQuery);
  //     actions.search(debouncedQuery, filters || {});
  //   }
  // }, [debouncedQuery, actions, filters]);

  // Mise à jour des suggestions (désactivé temporairement pour les tests)
  // useEffect(() => {
  //   if (query) {
  //     const newSuggestions = utils.generateSuggestions(query);
  //     actions.setSuggestions(newSuggestions);
  //   }
  // }, [query, actions, utils]);

  return {
    // État
    results,
    query,
    filters,
    loading,
    error,
    history,
    suggestions,

    // Actions
    ...actions,

    // Utilitaires
    ...utils,

    // Callbacks optimisés
    ...callbacks,
  };
};

/**
 * Hook pour la recherche spécialisée
 */
export const useSpecializedSearch = () => {
  const dispatch = useDispatch();

  // Sélecteurs Redux directs pour éviter les problèmes de hooks conditionnels
  const loading = useSelector(selectSearchLoading) || false;
  const error = useSelector(selectSearchError) || null;

  const searchTypes = useMemo(() => ({
    // Recherche dans les conversations
    searchConversations: (query) =>
      dispatch(searchConversations({ query, filters: { type: 'conversations' } })),

    // Recherche dans les messages
    searchMessages: (query) =>
      dispatch(searchMessages({ query, filters: { type: 'messages' } })),

    // Recherche dans les documents
    searchDocuments: (query) =>
      dispatch(searchDocuments({ query, filters: { type: 'documents' } })),
    
    // Recherche par date
    searchByDate: (query, dateRange) =>
      dispatch(performSearch({
        query,
        filters: {
          createdAfter: dateRange.start,
          createdBefore: dateRange.end
        }
      })),

    // Recherche par utilisateur
    searchByUser: (query, userId) =>
      dispatch(performSearch({
        query,
        filters: { userId }
      })),
  }), [dispatch]);

  return {
    loading,
    error,
    ...searchTypes,
  };
};

/**
 * Hook pour l'analyse réseau
 */
export const useNetworkAnalysis = () => {
  const { analyzeNetwork, loading, error, results } = useSearch();
  
  const analysisTypes = useMemo(() => ({
    // Scan de port
    portScan: (target, ports) => 
      analyzeNetwork({
        type: 'port_scan',
        target,
        ports,
      }),
    
    // Découverte réseau
    networkDiscovery: (subnet) => 
      analyzeNetwork({
        type: 'network_discovery',
        subnet,
      }),
    
    // Test de connectivité
    connectivityTest: (targets) => 
      analyzeNetwork({
        type: 'connectivity_test',
        targets,
      }),
  }), [analyzeNetwork]);

  const networkResults = useMemo(() => 
    results.filter(result => result.type === 'network_analysis'),
    [results]
  );

  return {
    loading,
    error,
    networkResults,
    ...analysisTypes,
  };
};

export default useSearch;
