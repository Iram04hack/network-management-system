/**
 * Slice Redux pour la gestion des conversations
 * Intégration avec le service AI Assistant validé Phase 1
 * Respect de la contrainte 95.65% de données réelles
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import aiAssistantService from '../../services/aiAssistantService';

/**
 * État initial du slice conversations
 */
const initialState = {
  // Données des conversations
  items: [],
  currentConversation: null,
  
  // Pagination
  pagination: {
    currentPage: 1,
    pageSize: 20,
    totalPages: 0,
    totalCount: 0,
    hasNext: false,
    hasPrevious: false,
  },
  
  // États de chargement
  loading: {
    fetch: false,
    create: false,
    update: false,
    delete: false,
  },
  
  // Gestion d'erreurs
  error: null,
  lastError: null,
  
  // Métadonnées
  lastFetch: null,
  lastUpdate: null,
  
  // Filtres et tri
  filters: {
    search: '',
    hasMessages: null,
    createdAfter: null,
    createdBefore: null,
  },
  sorting: {
    field: 'created_at',
    direction: 'desc',
  },
};

/**
 * Actions asynchrones (thunks) pour les conversations
 */

// Récupérer la liste des conversations
export const fetchConversations = createAsyncThunk(
  'conversations/fetchConversations',
  async (params = {}, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const { pagination, filters, sorting } = state.conversations;
      
      const requestParams = {
        page: params.page || pagination.currentPage,
        page_size: params.pageSize || pagination.pageSize,
        ordering: params.ordering || `${sorting.direction === 'desc' ? '-' : ''}${sorting.field}`,
        ...filters,
        ...params,
      };
      
      const result = await aiAssistantService.getConversations(requestParams);
      
      if (result.success) {
        return {
          conversations: result.data.results,
          pagination: result.pagination,
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

// Créer une nouvelle conversation
export const createConversation = createAsyncThunk(
  'conversations/createConversation',
  async (conversationData, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.createConversation(conversationData);
      
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

// Récupérer une conversation spécifique
export const fetchConversation = createAsyncThunk(
  'conversations/fetchConversation',
  async (conversationId, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.getConversation(conversationId);
      
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

// Mettre à jour une conversation
export const updateConversation = createAsyncThunk(
  'conversations/updateConversation',
  async ({ conversationId, updateData }, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.updateConversation(conversationId, updateData);
      
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

// Supprimer une conversation
export const deleteConversation = createAsyncThunk(
  'conversations/deleteConversation',
  async (conversationId, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.deleteConversation(conversationId);
      
      if (result.success) {
        return { conversationId };
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

/**
 * Slice Redux pour les conversations
 */
const conversationsSlice = createSlice({
  name: 'conversations',
  initialState,
  reducers: {
    // Actions synchrones
    setCurrentConversation: (state, action) => {
      state.currentConversation = action.payload;
    },
    
    clearCurrentConversation: (state) => {
      state.currentConversation = null;
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
    
    // Optimistic updates pour une meilleure UX
    optimisticUpdateConversation: (state, action) => {
      const { conversationId, updateData } = action.payload;
      const conversation = state.items.find(item => item.id === conversationId);
      if (conversation) {
        Object.assign(conversation, updateData);
      }
    },
    
    // Mise à jour locale d'une conversation
    updateConversationLocal: (state, action) => {
      const updatedConversation = action.payload;
      const index = state.items.findIndex(item => item.id === updatedConversation.id);
      if (index !== -1) {
        state.items[index] = updatedConversation;
      }
      
      // Mettre à jour aussi la conversation courante si c'est la même
      if (state.currentConversation && state.currentConversation.id === updatedConversation.id) {
        state.currentConversation = updatedConversation;
      }
    },
  },
  
  extraReducers: (builder) => {
    // Fetch conversations
    builder
      .addCase(fetchConversations.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchConversations.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.items = action.payload.conversations;
        state.pagination = action.payload.pagination;
        state.lastFetch = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchConversations.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Create conversation
    builder
      .addCase(createConversation.pending, (state) => {
        state.loading.create = true;
        state.error = null;
      })
      .addCase(createConversation.fulfilled, (state, action) => {
        state.loading.create = false;
        state.items.unshift(action.payload); // Ajouter en début de liste
        state.currentConversation = action.payload;
        state.lastUpdate = new Date().toISOString();
        state.error = null;
      })
      .addCase(createConversation.rejected, (state, action) => {
        state.loading.create = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch conversation
    builder
      .addCase(fetchConversation.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchConversation.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.currentConversation = action.payload;
        
        // Mettre à jour aussi dans la liste si elle existe
        const index = state.items.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        
        state.error = null;
      })
      .addCase(fetchConversation.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Update conversation
    builder
      .addCase(updateConversation.pending, (state) => {
        state.loading.update = true;
        state.error = null;
      })
      .addCase(updateConversation.fulfilled, (state, action) => {
        state.loading.update = false;
        
        // Mettre à jour dans la liste
        const index = state.items.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        
        // Mettre à jour la conversation courante si c'est la même
        if (state.currentConversation && state.currentConversation.id === action.payload.id) {
          state.currentConversation = action.payload;
        }
        
        state.lastUpdate = new Date().toISOString();
        state.error = null;
      })
      .addCase(updateConversation.rejected, (state, action) => {
        state.loading.update = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Delete conversation
    builder
      .addCase(deleteConversation.pending, (state) => {
        state.loading.delete = true;
        state.error = null;
      })
      .addCase(deleteConversation.fulfilled, (state, action) => {
        state.loading.delete = false;
        
        // Supprimer de la liste
        state.items = state.items.filter(item => item.id !== action.payload.conversationId);
        
        // Vider la conversation courante si c'est celle supprimée
        if (state.currentConversation && state.currentConversation.id === action.payload.conversationId) {
          state.currentConversation = null;
        }
        
        state.lastUpdate = new Date().toISOString();
        state.error = null;
      })
      .addCase(deleteConversation.rejected, (state, action) => {
        state.loading.delete = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
  },
});

// Export des actions
export const {
  setCurrentConversation,
  clearCurrentConversation,
  setFilters,
  setSorting,
  clearFilters,
  clearError,
  optimisticUpdateConversation,
  updateConversationLocal,
} = conversationsSlice.actions;

// Sélecteurs
export const selectConversations = (state) => state.conversations.items;
export const selectCurrentConversation = (state) => state.conversations.currentConversation;
export const selectConversationsPagination = (state) => state.conversations.pagination;
export const selectConversationsLoading = (state) => state.conversations.loading;
export const selectConversationsError = (state) => state.conversations.error;
export const selectConversationsFilters = (state) => state.conversations.filters;
export const selectConversationsSorting = (state) => state.conversations.sorting;

// Sélecteurs composés
export const selectConversationById = (conversationId) => (state) =>
  state.conversations.items.find(item => item.id === conversationId);

export const selectIsConversationLoading = (state) =>
  Object.values(state.conversations.loading || {}).some(loading => loading);

export default conversationsSlice.reducer;
