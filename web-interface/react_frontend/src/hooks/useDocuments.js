/**
 * Hook personnalisé pour la gestion des documents - VERSION CORRIGÉE
 * Upload, recherche et gestion de fichiers
 */

import { useCallback, useMemo, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fetchDocuments,
  uploadDocument,
  searchDocuments,
  fetchDocument,
  updateDocument,
  deleteDocument,
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
  calculateStats,
  selectDocuments,
  selectCurrentDocument,
  selectDocumentsPagination,
  selectDocumentsLoading,
  selectDocumentsError,
  selectDocumentsFilters,
  selectDocumentsSorting,
  selectSearchResults,
  selectLastSearchQuery,
  selectUploadProgress,
  selectDocumentsStats
} from '../store/slices/documentsSlice';

const useDocuments = (options = {}) => {
  const dispatch = useDispatch();
  const [dragOver, setDragOver] = useState(false);

  // Sélecteurs Redux
  const documents = useSelector(selectDocuments);
  const currentDocument = useSelector(selectCurrentDocument);
  const pagination = useSelector(selectDocumentsPagination);
  const loading = useSelector(selectDocumentsLoading);
  const error = useSelector(selectDocumentsError);
  const filters = useSelector(selectDocumentsFilters);
  const sorting = useSelector(selectDocumentsSorting);
  const searchResults = useSelector(selectSearchResults);
  const lastSearchQuery = useSelector(selectLastSearchQuery);
  const uploadProgress = useSelector(selectUploadProgress);
  const stats = useSelector(selectDocumentsStats);

  // Actions avec useCallback pour stabilité des références
  const fetchDocuments = useCallback((params) => {
    return dispatch(fetchDocuments(params));
  }, [dispatch]);

  const uploadDocument = useCallback((documentData, file) => {
    return dispatch(uploadDocument({ documentData, file }));
  }, [dispatch]);

  const searchDocuments = useCallback((query, params) => {
    return dispatch(searchDocuments({ query, ...params }));
  }, [dispatch]);

  const fetchDocument = useCallback((id) => {
    return dispatch(fetchDocument(id));
  }, [dispatch]);

  const updateDocument = useCallback((id, data) => {
    return dispatch(updateDocument({ id, data }));
  }, [dispatch]);

  const deleteDocument = useCallback((id) => {
    return dispatch(deleteDocument(id));
  }, [dispatch]);

  const setCurrentDocument = useCallback((document) => {
    return dispatch(setCurrentDocument(document));
  }, [dispatch]);

  const clearCurrentDocument = useCallback(() => {
    return dispatch(clearCurrentDocument());
  }, [dispatch]);

  const setFilters = useCallback((filters) => {
    return dispatch(setFilters(filters));
  }, [dispatch]);

  const setSorting = useCallback((sorting) => {
    return dispatch(setSorting(sorting));
  }, [dispatch]);

  const clearFilters = useCallback(() => {
    return dispatch(clearFilters());
  }, [dispatch]);

  const clearSearchResults = useCallback(() => {
    return dispatch(clearSearchResults());
  }, [dispatch]);

  const updateUploadProgress = useCallback((progress) => {
    return dispatch(updateUploadProgress(progress));
  }, [dispatch]);

  const resetUploadProgress = useCallback(() => {
    return dispatch(resetUploadProgress());
  }, [dispatch]);

  const clearError = useCallback(() => {
    return dispatch(clearError());
  }, [dispatch]);

  const optimisticUpdateDocument = useCallback((id, data) => {
    return dispatch(optimisticUpdateDocument({ id, data }));
  }, [dispatch]);

  const updateDocumentLocal = useCallback((id, data) => {
    return dispatch(updateDocumentLocal({ id, data }));
  }, [dispatch]);

  const calculateStats = useCallback(() => {
    return dispatch(calculateStats());
  }, [dispatch]);

  // Utilitaires
  const utils = useMemo(() => ({
    validateFile: (file) => {
      const errors = [];
      const maxSize = 10 * 1024 * 1024; // 10MB
      const allowedTypes = ['application/pdf', 'text/plain', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      
      if (file.size > maxSize) {
        errors.push('Fichier trop volumineux (max 10MB)');
      }
      
      if (!allowedTypes.includes(file.type)) {
        errors.push('Type de fichier non supporté');
      }
      
      return {
        isValid: errors.length === 0,
        errors
      };
    },
    
    formatFileSize: (bytes) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
  }), [documents, filters, sorting]);

  // Callbacks optimisés - sortis du useMemo pour éviter les hooks conditionnels
  const refresh = useCallback((params = {}) => {
    return fetchDocuments(params);
  }, [fetchDocuments]);
  
  const uploadWithValidation = useCallback(async (documentData, file) => {
    const validation = utils.validateFile(file);
    if (!validation.isValid) {
      throw new Error(`Validation échouée: ${validation.errors.join(', ')}`);
    }
    return uploadDocument(documentData, file);
  }, [uploadDocument, utils]);
  
  const uploadMultiple = useCallback(async (files, baseDocumentData = {}) => {
    const results = [];
    for (const file of files) {
      try {
        const validation = utils.validateFile(file);
        if (!validation.isValid) {
          throw new Error(`Validation échouée: ${validation.errors.join(', ')}`);
        }

        const documentData = {
          ...baseDocumentData,
          title: file.name,
          content_type: file.type,
        };
        const result = await uploadDocument(documentData, file);
        results.push({ file: file.name, success: true, result });
      } catch (error) {
        results.push({ file: file.name, success: false, error: error.message });
      }
    }
    return results;
  }, [uploadDocument, utils]);
  
  const searchWithHistory = useCallback((query, params = {}) => {
    if (query.trim()) {
      return searchDocuments(query, params);
    }
  }, [searchDocuments]);
  
  const deleteWithConfirmation = useCallback(async (documentId, confirmCallback) => {
    if (confirmCallback && !confirmCallback()) {
      return { cancelled: true };
    }
    return deleteDocument(documentId);
  }, [deleteDocument]);
  
  const goToPage = useCallback((page) => {
    fetchDocuments({ page });
  }, [fetchDocuments]);

  const nextPage = useCallback(() => {
    if (pagination.hasNext) {
      fetchDocuments({ page: pagination.currentPage + 1 });
    }
  }, [fetchDocuments, pagination]);

  const previousPage = useCallback(() => {
    if (pagination.hasPrevious) {
      fetchDocuments({ page: pagination.currentPage - 1 });
    }
  }, [fetchDocuments, pagination]);
  
  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setDragOver(true);
  }, []);
  
  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
  }, []);
  
  const handleDrop = useCallback(async (e) => {
    e.preventDefault();
    setDragOver(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      const results = [];
      for (const file of files) {
        try {
          const validation = utils.validateFile(file);
          if (!validation.isValid) {
            throw new Error(`Validation échouée: ${validation.errors.join(', ')}`);
          }
          const documentData = {
            title: file.name,
            content_type: file.type,
          };
          const result = await uploadDocument(documentData, file);
          results.push({ file: file.name, success: true, result });
        } catch (error) {
          results.push({ file: file.name, success: false, error: error.message });
        }
      }
      return results;
    }
  }, [uploadDocument, utils]);

  // Regrouper tous les callbacks
  const callbacks = useMemo(() => ({
    refresh,
    uploadWithValidation,
    uploadMultiple,
    searchWithHistory,
    deleteWithConfirmation,
    goToPage,
    nextPage,
    previousPage,
    handleDragOver,
    handleDragLeave,
    handleDrop
  }), [refresh, uploadWithValidation, uploadMultiple, searchWithHistory, deleteWithConfirmation, goToPage, nextPage, previousPage, handleDragOver, handleDragLeave, handleDrop]);

  return {
    // État
    documents,
    currentDocument,
    pagination,
    loading,
    error,
    filters,
    sorting,
    searchResults,
    lastSearchQuery,
    uploadProgress,
    stats,
    isLoading: loading.fetch || loading.upload || loading.search,
    dragOver,
    
    // Actions stables avec useCallback
    fetchDocuments,
    uploadDocument,
    searchDocuments,
    fetchDocument,
    updateDocument,
    deleteDocument,
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
    calculateStats,
    
    // Callbacks optimisés
    ...callbacks,
    
    // Utilitaires
    ...utils,
    
    // Méthodes de commodité
    hasDocuments: documents.length > 0,
    hasError: !!error,
    hasFilters: Object.keys(filters).length > 0,
    canGoNext: pagination.hasNext,
    canGoPrevious: pagination.hasPrevious,
    totalPages: pagination.totalPages,
    currentPage: pagination.currentPage,
    totalDocuments: pagination.totalItems,
    
    // Statistiques calculées
    getStats: () => stats,
    getFilteredDocuments: () => documents.filter(doc => {
      if (filters.search) {
        return doc.title.toLowerCase().includes(filters.search.toLowerCase()) ||
               doc.content?.toLowerCase().includes(filters.search.toLowerCase());
      }
      return true;
    }),
    
    // Gestion d'erreur
    clearError,

    // Reset
    reset: () => {
      clearFilters();
      clearSearchResults();
      clearCurrentDocument();
      resetUploadProgress();
      clearError();
    }
  };
};

export default useDocuments;
