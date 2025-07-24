/**
 * Slice Redux pour la gestion des documents
 * Intégration avec le service AI Assistant validé Phase 1
 * Support upload, recherche et gestion de fichiers
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import aiAssistantService from '../../services/aiAssistantService';

/**
 * État initial du slice documents
 */
const initialState = {
  // Données des documents
  items: [],
  currentDocument: null,
  
  // Résultats de recherche
  searchResults: [],
  lastSearchQuery: '',
  
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
    upload: false,
    update: false,
    delete: false,
    search: false,
  },
  
  // Gestion d'erreurs
  error: null,
  lastError: null,
  
  // Upload progress
  uploadProgress: {
    fileName: '',
    progress: 0,
    isUploading: false,
  },
  
  // Filtres et tri
  filters: {
    contentType: '',
    tags: [],
    isActive: true,
    createdAfter: null,
    createdBefore: null,
  },
  sorting: {
    field: 'created_at',
    direction: 'desc',
  },
  
  // Métadonnées
  lastFetch: null,
  lastUpdate: null,
  
  // Statistiques
  stats: {
    totalDocuments: 0,
    totalSize: 0,
    byContentType: {},
    byTags: {},
  },
};

/**
 * Actions asynchrones (thunks) pour les documents
 */

// Récupérer la liste des documents
export const fetchDocuments = createAsyncThunk(
  'documents/fetchDocuments',
  async (params = {}, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const { pagination, filters, sorting } = state.documents;
      
      const requestParams = {
        page: params.page || pagination.currentPage,
        page_size: params.pageSize || pagination.pageSize,
        ordering: params.ordering || `${sorting.direction === 'desc' ? '-' : ''}${sorting.field}`,
        ...filters,
        ...params,
      };
      
      const result = await aiAssistantService.getDocuments(requestParams);
      
      if (result.success) {
        return {
          documents: result.data.results || result.data,
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

// Upload d'un document
export const uploadDocument = createAsyncThunk(
  'documents/uploadDocument',
  async ({ documentData, file }, { dispatch, rejectWithValue }) => {
    try {
      // Configurer le callback de progression
      aiAssistantService.setUploadProgressCallback((progress, fileName) => {
        dispatch(updateUploadProgress({ progress, fileName }));
      });
      
      const result = await aiAssistantService.uploadDocument(documentData, file);
      
      if (result.success) {
        // Reset du progress
        dispatch(resetUploadProgress());
        return result.data;
      } else {
        dispatch(resetUploadProgress());
        return rejectWithValue(result.error);
      }
    } catch (error) {
      dispatch(resetUploadProgress());
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error,
      });
    }
  }
);

// Recherche dans les documents
export const searchDocuments = createAsyncThunk(
  'documents/searchDocuments',
  async ({ query, params = {} }, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.searchDocuments(query, params);
      
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

// Récupérer un document spécifique
export const fetchDocument = createAsyncThunk(
  'documents/fetchDocument',
  async (documentId, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.getDocument(documentId);
      
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

// Mettre à jour un document
export const updateDocument = createAsyncThunk(
  'documents/updateDocument',
  async ({ documentId, updateData }, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.updateDocument(documentId, updateData);
      
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

// Supprimer un document
export const deleteDocument = createAsyncThunk(
  'documents/deleteDocument',
  async (documentId, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.deleteDocument(documentId);
      
      if (result.success) {
        return { documentId };
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
 * Slice Redux pour les documents
 */
const documentsSlice = createSlice({
  name: 'documents',
  initialState,
  reducers: {
    // Actions synchrones
    setCurrentDocument: (state, action) => {
      state.currentDocument = action.payload;
    },
    
    clearCurrentDocument: (state) => {
      state.currentDocument = null;
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
    
    clearSearchResults: (state) => {
      state.searchResults = [];
      state.lastSearchQuery = '';
    },
    
    // Gestion du progress d'upload
    updateUploadProgress: (state, action) => {
      state.uploadProgress = {
        ...state.uploadProgress,
        ...action.payload,
        isUploading: true,
      };
    },
    
    resetUploadProgress: (state) => {
      state.uploadProgress = initialState.uploadProgress;
    },
    
    // Gestion d'erreurs
    clearError: (state) => {
      state.error = null;
    },
    
    // Optimistic updates
    optimisticUpdateDocument: (state, action) => {
      const { documentId, updateData } = action.payload;
      const document = state.items.find(item => item.id === documentId);
      if (document) {
        Object.assign(document, updateData);
      }
    },
    
    // Mise à jour locale d'un document
    updateDocumentLocal: (state, action) => {
      const updatedDocument = action.payload;
      const index = state.items.findIndex(item => item.id === updatedDocument.id);
      if (index !== -1) {
        state.items[index] = updatedDocument;
      }
      
      // Mettre à jour aussi le document courant si c'est le même
      if (state.currentDocument && state.currentDocument.id === updatedDocument.id) {
        state.currentDocument = updatedDocument;
      }
    },
    
    // Mise à jour des statistiques
    updateStats: (state, action) => {
      state.stats = { ...state.stats, ...action.payload };
    },
    
    // Calculer les statistiques à partir des documents
    calculateStats: (state) => {
      const stats = {
        totalDocuments: state.items.length,
        totalSize: 0,
        byContentType: {},
        byTags: {},
      };
      
      state.items.forEach(doc => {
        // Compter par type de contenu
        const contentType = doc.content_type || 'unknown';
        stats.byContentType[contentType] = (stats.byContentType[contentType] || 0) + 1;
        
        // Compter par tags
        if (doc.tags && Array.isArray(doc.tags)) {
          doc.tags.forEach(tag => {
            stats.byTags[tag] = (stats.byTags[tag] || 0) + 1;
          });
        }
        
        // Taille approximative (longueur du contenu)
        if (doc.content) {
          stats.totalSize += doc.content.length;
        }
      });
      
      state.stats = stats;
    },
  },
  
  extraReducers: (builder) => {
    // Fetch documents
    builder
      .addCase(fetchDocuments.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchDocuments.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.items = action.payload.documents;
        state.pagination = action.payload.pagination;
        state.lastFetch = new Date().toISOString();
        state.error = null;
        
        // Calculer les statistiques
        documentsSlice.caseReducers.calculateStats(state);
      })
      .addCase(fetchDocuments.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Upload document
    builder
      .addCase(uploadDocument.pending, (state) => {
        state.loading.upload = true;
        state.error = null;
      })
      .addCase(uploadDocument.fulfilled, (state, action) => {
        state.loading.upload = false;
        state.items.unshift(action.payload); // Ajouter en début de liste
        state.currentDocument = action.payload;
        state.lastUpdate = new Date().toISOString();
        state.error = null;
        
        // Calculer les statistiques
        documentsSlice.caseReducers.calculateStats(state);
      })
      .addCase(uploadDocument.rejected, (state, action) => {
        state.loading.upload = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Search documents
    builder
      .addCase(searchDocuments.pending, (state) => {
        state.loading.search = true;
        state.error = null;
      })
      .addCase(searchDocuments.fulfilled, (state, action) => {
        state.loading.search = false;
        state.searchResults = action.payload.results;
        state.lastSearchQuery = action.payload.query;
        state.error = null;
      })
      .addCase(searchDocuments.rejected, (state, action) => {
        state.loading.search = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch document
    builder
      .addCase(fetchDocument.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchDocument.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.currentDocument = action.payload;
        
        // Mettre à jour aussi dans la liste si elle existe
        const index = state.items.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        
        state.error = null;
      })
      .addCase(fetchDocument.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Update document
    builder
      .addCase(updateDocument.pending, (state) => {
        state.loading.update = true;
        state.error = null;
      })
      .addCase(updateDocument.fulfilled, (state, action) => {
        state.loading.update = false;
        
        // Mettre à jour dans la liste
        const index = state.items.findIndex(item => item.id === action.payload.id);
        if (index !== -1) {
          state.items[index] = action.payload;
        }
        
        // Mettre à jour le document courant si c'est le même
        if (state.currentDocument && state.currentDocument.id === action.payload.id) {
          state.currentDocument = action.payload;
        }
        
        state.lastUpdate = new Date().toISOString();
        state.error = null;
        
        // Calculer les statistiques
        documentsSlice.caseReducers.calculateStats(state);
      })
      .addCase(updateDocument.rejected, (state, action) => {
        state.loading.update = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Delete document
    builder
      .addCase(deleteDocument.pending, (state) => {
        state.loading.delete = true;
        state.error = null;
      })
      .addCase(deleteDocument.fulfilled, (state, action) => {
        state.loading.delete = false;
        
        // Supprimer de la liste
        state.items = state.items.filter(item => item.id !== action.payload.documentId);
        
        // Vider le document courant si c'est celui supprimé
        if (state.currentDocument && state.currentDocument.id === action.payload.documentId) {
          state.currentDocument = null;
        }
        
        // Supprimer des résultats de recherche aussi
        state.searchResults = state.searchResults.filter(
          item => item.id !== action.payload.documentId
        );
        
        state.lastUpdate = new Date().toISOString();
        state.error = null;
        
        // Calculer les statistiques
        documentsSlice.caseReducers.calculateStats(state);
      })
      .addCase(deleteDocument.rejected, (state, action) => {
        state.loading.delete = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
  },
});

// Export des actions
export const {
  setCurrentDocument,
  clearCurrentDocument,
  setFilters,
  setSorting,
  clearFilters,
  clearSearchResults,
  updateUploadProgress,
  resetUploadProgress,
  clearError,
  optimisticUpdateDocument,
  updateDocumentLocal,
  updateStats,
  calculateStats,
} = documentsSlice.actions;

// Sélecteurs
export const selectDocuments = (state) => state.documents.items;
export const selectCurrentDocument = (state) => state.documents.currentDocument;
export const selectDocumentsPagination = (state) => state.documents.pagination;
export const selectDocumentsLoading = (state) => state.documents.loading;
export const selectDocumentsError = (state) => state.documents.error;
export const selectDocumentsFilters = (state) => state.documents.filters;
export const selectDocumentsSorting = (state) => state.documents.sorting;
export const selectSearchResults = (state) => state.documents.searchResults;
export const selectLastSearchQuery = (state) => state.documents.lastSearchQuery;
export const selectUploadProgress = (state) => state.documents.uploadProgress;
export const selectDocumentsStats = (state) => state.documents.stats;

// Sélecteurs composés
export const selectDocumentById = (documentId) => (state) =>
  state.documents.items.find(item => item.id === documentId);

export const selectIsDocumentLoading = (state) =>
  Object.values(state.documents.loading).some(loading => loading);

export const selectDocumentsByTag = (tag) => (state) =>
  state.documents.items.filter(doc => 
    doc.tags && doc.tags.includes(tag)
  );

export const selectDocumentsByContentType = (contentType) => (state) =>
  state.documents.items.filter(doc => doc.content_type === contentType);

export default documentsSlice.reducer;
