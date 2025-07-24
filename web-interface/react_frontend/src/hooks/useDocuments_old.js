/**
 * Hook personnalisé pour la gestion des documents
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
  selectDocumentsStats,
  selectDocumentById,
  selectIsDocumentLoading,
  selectDocumentsByTag,
  selectDocumentsByContentType,
} from '../store/slices/documentsSlice';

/**
 * Hook principal pour la gestion des documents
 */
export const useDocuments = () => {
  const dispatch = useDispatch();
  const [dragOver, setDragOver] = useState(false);
  
  // Sélecteurs Redux avec gestion d'erreur
  const documents = useSelector((state) => state?.documents?.items || []);
  const currentDocument = useSelector((state) => state?.documents?.currentDocument || null);
  const pagination = useSelector((state) => state?.documents?.pagination || {});
  const loading = useSelector((state) => state?.documents?.loading || {});
  const error = useSelector((state) => state?.documents?.error || null);
  const filters = useSelector((state) => state?.documents?.filters || {});
  const sorting = useSelector((state) => state?.documents?.sorting || {});
  const searchResults = useSelector((state) => state?.documents?.searchResults || []);
  const lastSearchQuery = useSelector((state) => state?.documents?.lastSearchQuery || '');
  const uploadProgress = useSelector(selectUploadProgress);
  const stats = useSelector(selectDocumentsStats);
  const isLoading = useSelector(selectIsDocumentLoading);

  // Actions mémorisées
  const actions = useMemo(() => ({
    // Récupération des documents
    fetchDocuments: (params) => dispatch(fetchDocuments(params)),
    
    // Upload d'un document
    uploadDocument: (documentData, file) => dispatch(uploadDocument({ documentData, file })),
    
    // Recherche dans les documents
    searchDocuments: (query, params) => dispatch(searchDocuments({ query, params })),
    
    // Récupération d'un document spécifique
    fetchDocument: (documentId) => dispatch(fetchDocument(documentId)),
    
    // Mise à jour d'un document
    updateDocument: (documentId, updateData) => 
      dispatch(updateDocument({ documentId, updateData })),
    
    // Suppression d'un document
    deleteDocument: (documentId) => dispatch(deleteDocument(documentId)),
    
    // Gestion du document courant
    setCurrentDocument: (document) => dispatch(setCurrentDocument(document)),
    clearCurrentDocument: () => dispatch(clearCurrentDocument()),
    
    // Gestion des filtres et tri
    setFilters: (newFilters) => dispatch(setFilters(newFilters)),
    setSorting: (newSorting) => dispatch(setSorting(newSorting)),
    clearFilters: () => dispatch(clearFilters()),
    
    // Gestion de la recherche
    clearSearchResults: () => dispatch(clearSearchResults()),
    
    // Gestion d'erreurs
    clearError: () => dispatch(clearError()),
    
    // Optimistic updates
    optimisticUpdate: (documentId, updateData) => 
      dispatch(optimisticUpdateDocument({ documentId, updateData })),
    
    // Calcul des statistiques
    calculateStats: () => dispatch(calculateStats()),
  }), [dispatch]);

  // Fonctions utilitaires mémorisées
  const utils = useMemo(() => ({
    // Rechercher un document par ID
    getDocumentById: (documentId) => 
      documents.find(doc => doc.id === documentId),
    
    // Filtrer les documents par tag
    getDocumentsByTag: (tag) => 
      documents.filter(doc => doc.tags && doc.tags.includes(tag)),
    
    // Filtrer les documents par type de contenu
    getDocumentsByContentType: (contentType) => 
      documents.filter(doc => doc.content_type === contentType),
    
    // Obtenir tous les tags uniques
    getAllTags: () => {
      const allTags = documents.reduce((tags, doc) => {
        if (doc.tags && Array.isArray(doc.tags)) {
          tags.push(...doc.tags);
        }
        return tags;
      }, []);
      return [...new Set(allTags)];
    },
    
    // Obtenir tous les types de contenu uniques
    getAllContentTypes: () => {
      const contentTypes = documents.map(doc => doc.content_type).filter(Boolean);
      return [...new Set(contentTypes)];
    },
    
    // Filtrer les documents
    getFilteredDocuments: (customFilters = {}) => {
      const activeFilters = { ...filters, ...customFilters };
      return documents.filter(doc => {
        if (activeFilters.contentType && doc.content_type !== activeFilters.contentType) {
          return false;
        }
        if (activeFilters.tags.length > 0 && 
            !activeFilters.tags.some(tag => doc.tags && doc.tags.includes(tag))) {
          return false;
        }
        if (activeFilters.isActive !== null && doc.is_active !== activeFilters.isActive) {
          return false;
        }
        if (activeFilters.createdAfter && new Date(doc.created_at) < new Date(activeFilters.createdAfter)) {
          return false;
        }
        if (activeFilters.createdBefore && new Date(doc.created_at) > new Date(activeFilters.createdBefore)) {
          return false;
        }
        return true;
      });
    },
    
    // Trier les documents
    getSortedDocuments: (documentsToSort = documents) => {
      const { field, direction } = sorting;
      return [...documentsToSort].sort((a, b) => {
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
    
    // Valider un fichier avant upload
    validateFile: (file) => {
      const errors = [];
      const maxSize = 10 * 1024 * 1024; // 10MB
      const allowedTypes = [
        'text/plain',
        'text/markdown',
        'application/pdf',
        'application/json',
        'text/csv',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ];
      
      if (file.size > maxSize) {
        errors.push(`Fichier trop volumineux (max: ${maxSize / 1024 / 1024}MB)`);
      }
      
      if (!allowedTypes.includes(file.type)) {
        errors.push(`Type de fichier non supporté: ${file.type}`);
      }
      
      return {
        isValid: errors.length === 0,
        errors,
      };
    },
    
    // Formater la taille de fichier
    formatFileSize: (bytes) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
  }), [documents, filters, sorting]);

  // Callbacks optimisés
  const callbacks = useMemo(() => ({
    // Rafraîchir les documents
    refresh: useCallback((params = {}) => {
      return actions.fetchDocuments(params);
    }, [actions]),
    
    // Upload avec validation
    uploadWithValidation: useCallback(async (documentData, file) => {
      const validation = utils.validateFile(file);
      if (!validation.isValid) {
        throw new Error(`Validation échouée: ${validation.errors.join(', ')}`);
      }
      return actions.uploadDocument(documentData, file);
    }, [actions, utils]),
    
    // Upload multiple
    uploadMultiple: useCallback(async (files, baseDocumentData = {}) => {
      const results = [];
      for (const file of files) {
        try {
          // Validation directe
          const validation = utils.validateFile(file);
          if (!validation.isValid) {
            throw new Error(`Validation échouée: ${validation.errors.join(', ')}`);
          }

          const documentData = {
            ...baseDocumentData,
            title: file.name,
            content_type: file.type,
          };
          const result = await actions.uploadDocument(documentData, file);
          results.push({ file: file.name, success: true, result });
        } catch (error) {
          results.push({ file: file.name, success: false, error: error.message });
        }
      }
      return results;
    }, [actions, utils]),
    
    // Recherche avec historique
    searchWithHistory: useCallback((query, params = {}) => {
      if (query.trim()) {
        return actions.searchDocuments(query, params);
      }
    }, [actions]),
    
    // Supprimer avec confirmation
    deleteWithConfirmation: useCallback(async (documentId, confirmCallback) => {
      if (confirmCallback && !confirmCallback()) {
        return { cancelled: true };
      }
      return actions.deleteDocument(documentId);
    }, [actions]),
    
    // Pagination
    goToPage: useCallback((page) => {
      actions.fetchDocuments({ page });
    }, [actions]),
    
    nextPage: useCallback(() => {
      if (pagination.hasNext) {
        actions.fetchDocuments({ page: pagination.currentPage + 1 });
      }
    }, [actions, pagination]),
    
    previousPage: useCallback(() => {
      if (pagination.hasPrevious) {
        actions.fetchDocuments({ page: pagination.currentPage - 1 });
      }
    }, [actions, pagination]),
    
    // Gestion du drag & drop
    handleDragOver: useCallback((e) => {
      e.preventDefault();
      setDragOver(true);
    }, []),
    
    handleDragLeave: useCallback((e) => {
      e.preventDefault();
      setDragOver(false);
    }, []),
    
    handleDrop: useCallback(async (e) => {
      e.preventDefault();
      setDragOver(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        // Utiliser directement uploadMultiple au lieu de callbacks.uploadMultiple
        const results = [];
        for (const file of files) {
          try {
            const documentData = {
              title: file.name,
              content_type: file.type,
            };
            const result = await actions.uploadDocument(documentData, file);
            results.push({ file: file.name, success: true, result });
          } catch (error) {
            results.push({ file: file.name, success: false, error: error.message });
          }
        }
        return results;
      }
    }, [actions]),
  }), [actions, utils, pagination]);

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
    isLoading,
    dragOver,
    
    // Actions
    ...actions,
    
    // Utilitaires
    ...utils,
    
    // Callbacks optimisés
    ...callbacks,
  };
};

/**
 * Hook pour un document spécifique
 */
export const useDocument = (documentId) => {
  const dispatch = useDispatch();
  const document = useSelector(selectDocumentById(documentId));
  const loading = useSelector(selectDocumentsLoading);
  const error = useSelector(selectDocumentsError);

  const actions = useMemo(() => ({
    fetch: () => dispatch(fetchDocument(documentId)),
    update: (updateData) => dispatch(updateDocument({ documentId, updateData })),
    delete: () => dispatch(deleteDocument(documentId)),
    select: () => dispatch(setCurrentDocument(document)),
  }), [dispatch, documentId, document]);

  return {
    document,
    loading,
    error,
    ...actions,
  };
};

/**
 * Hook pour l'upload de documents
 */
export const useDocumentUpload = () => {
  const dispatch = useDispatch();
  const uploadProgress = useSelector((state) => state?.documents?.uploadProgress || {});
  const loading = useSelector((state) => state?.documents?.loading?.upload || false);
  const error = useSelector((state) => state?.documents?.error || null);

  const actions = useMemo(() => ({
    upload: (documentData, file) => dispatch(uploadDocument({ documentData, file })),
    resetProgress: () => dispatch(resetUploadProgress()),
    clearError: () => dispatch(clearError()),
  }), [dispatch]);

  return {
    uploadProgress,
    loading,
    error,
    ...actions,
  };
};

/**
 * Hook pour la recherche de documents
 */
export const useDocumentSearch = () => {
  const dispatch = useDispatch();
  const searchResults = useSelector(selectSearchResults);
  const lastSearchQuery = useSelector(selectLastSearchQuery);
  const loading = useSelector(state => state.documents.loading.search);
  const error = useSelector(selectDocumentsError);

  const actions = useMemo(() => ({
    search: (query, params) => dispatch(searchDocuments({ query, params })),
    clearResults: () => dispatch(clearSearchResults()),
    clearError: () => dispatch(clearError()),
  }), [dispatch]);

  return {
    searchResults,
    lastSearchQuery,
    loading,
    error,
    ...actions,
  };
};

export default useDocuments;
