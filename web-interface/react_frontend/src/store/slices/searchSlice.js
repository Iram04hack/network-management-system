/**
 * Slice Redux pour la gestion de la recherche globale
 * Intégration avec le service AI Assistant validé Phase 1
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import aiAssistantService from '../../services/aiAssistantService';

const initialState = {
  results: [],
  query: '',
  filters: {
    type: 'all', // 'all', 'conversations', 'documents', 'messages'
    limit: 50,
  },
  loading: false,
  error: null,
  lastSearch: null,
  searchHistory: [],
  suggestions: [],
};

// Recherche globale
export const performGlobalSearch = createAsyncThunk(
  'search/performGlobalSearch',
  async ({ query, params = {} }, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const searchParams = {
        ...state.search.filters,
        ...params,
      };
      
      const result = await aiAssistantService.globalSearch(query, searchParams);
      
      if (result.success) {
        return {
          results: result.data.results || result.data,
          query,
          metadata: result.metadata,
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error,
      });
    }
  }
);

// Analyse réseau
export const performNetworkAnalysis = createAsyncThunk(
  'search/performNetworkAnalysis',
  async (analysisData, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.analyzeNetwork(analysisData);
      
      if (result.success) {
        return result.data;
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error,
      });
    }
  }
);

const searchSlice = createSlice({
  name: 'search',
  initialState,
  reducers: {
    setQuery: (state, action) => {
      state.query = action.payload;
    },
    setFilters: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearResults: (state) => {
      state.results = [];
      state.query = '';
    },
    clearError: (state) => {
      state.error = null;
    },
    addToHistory: (state, action) => {
      const { query, results } = action.payload;
      if (query.trim()) {
        state.searchHistory.unshift({
          query,
          resultsCount: results.length,
          timestamp: new Date().toISOString(),
        });
        // Garder seulement les 20 dernières recherches
        if (state.searchHistory.length > 20) {
          state.searchHistory = state.searchHistory.slice(0, 20);
        }
      }
    },
    setSuggestions: (state, action) => {
      state.suggestions = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(performGlobalSearch.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(performGlobalSearch.fulfilled, (state, action) => {
        state.loading = false;
        state.results = action.payload.results;
        state.query = action.payload.query;
        state.lastSearch = new Date().toISOString();
        state.error = null;
        
        // Ajouter à l'historique
        searchSlice.caseReducers.addToHistory(state, {
          payload: { query: action.payload.query, results: action.payload.results }
        });
      })
      .addCase(performGlobalSearch.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })
      .addCase(performNetworkAnalysis.fulfilled, (state, action) => {
        // Ajouter les résultats d'analyse réseau aux résultats de recherche
        state.results.unshift({
          type: 'network_analysis',
          id: `analysis_${Date.now()}`,
          title: `Analyse réseau: ${action.payload.target}`,
          content: action.payload,
          created_at: new Date().toISOString(),
          relevance_score: 1.0,
        });
      });
  },
});

export const { 
  setQuery, 
  setFilters, 
  clearResults, 
  clearError, 
  addToHistory, 
  setSuggestions 
} = searchSlice.actions;

export const selectSearchResults = (state) => state.search.results;
export const selectSearchQuery = (state) => state.search.query;
export const selectSearchFilters = (state) => state.search.filters;
export const selectSearchLoading = (state) => state.search.loading;
export const selectSearchError = (state) => state.search.error;
export const selectSearchHistory = (state) => state.search.searchHistory;
export const selectSearchSuggestions = (state) => state.search.suggestions;

export default searchSlice.reducer;
