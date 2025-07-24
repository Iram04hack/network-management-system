/**
 * Hook personnalisé pour la gestion de l'interface utilisateur
 * Gestion des notifications, modales, thème, et état global de l'UI
 */

import { useCallback, useMemo, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { createSelector } from '@reduxjs/toolkit';
import {
  addNotification,
  removeNotification,
  clearNotifications,
  openModal,
  closeModal,
  toggleTheme,
  setPreferences,
  setError,
  clearError,
  incrementErrorCount,
  addApiResponseTime
} from '../store/slices/uiSlice';

// Sélecteurs mémorisés
const selectUIState = (state) => state?.ui || {};

const selectNotifications = createSelector(
  [selectUIState],
  (uiState) => uiState.notifications || []
);

const selectModals = createSelector(
  [selectUIState],
  (uiState) => uiState.modals || {}
);

const selectTheme = createSelector(
  [selectUIState],
  (uiState) => uiState.theme || 'light'
);

const selectPreferences = createSelector(
  [selectUIState],
  (uiState) => uiState.preferences || {}
);

const selectUILoading = createSelector(
  [selectUIState],
  (uiState) => uiState.loading || {}
);

const selectUIError = createSelector(
  [selectUIState],
  (uiState) => uiState.error || null
);

const selectUIStats = createSelector(
  [selectUIState],
  (uiState) => uiState.stats || {}
);

/**
 * Hook principal pour la gestion de l'UI
 */
export const useUI = () => {
  const dispatch = useDispatch();
  
  // Sélecteurs Redux mémorisés
  const notifications = useSelector(selectNotifications);
  const modals = useSelector(selectModals);
  const theme = useSelector(selectTheme);
  const preferences = useSelector(selectPreferences);
  const loading = useSelector(selectUILoading);
  const error = useSelector(selectUIError);
  const stats = useSelector(selectUIStats);

  // Actions de base
  const actions = useMemo(() => ({
    addNotification: (notification) => dispatch(addNotification(notification)),
    removeNotification: (id) => dispatch(removeNotification(id)),
    clearNotifications: () => dispatch(clearNotifications()),
    openModal: (modalName) => dispatch(openModal(modalName)),
    closeModal: (modalName) => dispatch(closeModal(modalName)),
    toggleTheme: () => dispatch(toggleTheme()),
    setPreferences: (prefs) => dispatch(setPreferences(prefs)),
    setError: (error) => dispatch(setError(error)),
    clearError: () => dispatch(clearError()),
    incrementErrorCount: () => dispatch(incrementErrorCount()),
    addApiResponseTime: (endpoint, time) => dispatch(addApiResponseTime({ endpoint, time }))
  }), [dispatch]);

  // Callbacks optimisés - sortis du useMemo pour éviter les hooks conditionnels
  const showNotification = useCallback((notification, autoClose = true, delay = 5000) => {
    const id = Date.now();
    actions.addNotification({ ...notification, id });
    
    if (autoClose) {
      setTimeout(() => {
        actions.removeNotification(id);
      }, delay);
    }
    
    return id;
  }, [actions]);

  // Notification de succès
  const showSuccess = useCallback((message, title = 'Succès') => {
    const id = Date.now();
    actions.addNotification({ type: 'success', title, message, id });
    setTimeout(() => actions.removeNotification(id), 5000);
    return id;
  }, [actions]);

  // Notification d'erreur
  const showError = useCallback((message, title = 'Erreur') => {
    const id = Date.now();
    actions.addNotification({ type: 'error', title, message, id, autoClose: false });
    return id;
  }, [actions]);

  // Notification d'information
  const showInfo = useCallback((message, title = 'Information') => {
    const id = Date.now();
    actions.addNotification({ type: 'info', title, message, id });
    setTimeout(() => actions.removeNotification(id), 5000);
    return id;
  }, [actions]);

  // Notification d'avertissement
  const showWarning = useCallback((message, title = 'Avertissement') => {
    const id = Date.now();
    actions.addNotification({ type: 'warning', title, message, id });
    setTimeout(() => actions.removeNotification(id), 5000);
    return id;
  }, [actions]);
  
  // Gestion des modales avec callbacks
  const openModalWithCallback = useCallback((modalName, onOpen) => {
    actions.openModal(modalName);
    if (onOpen) onOpen();
  }, [actions]);
  
  const closeModalWithCallback = useCallback((modalName, onClose) => {
    actions.closeModal(modalName);
    if (onClose) onClose();
  }, [actions]);
  
  // Basculer le thème avec persistance
  const toggleThemeWithPersistence = useCallback(() => {
    actions.toggleTheme();
    // Le thème sera automatiquement persisté par le store
  }, [actions]);
  
  // Mettre à jour les préférences partiellement
  const updatePreference = useCallback((key, value) => {
    actions.setPreferences({ [key]: value });
  }, [actions]);
  
  // Mesurer le temps de réponse API
  const measureApiResponse = useCallback((endpoint, startTime) => {
    const responseTime = Date.now() - startTime;
    actions.addApiResponseTime(endpoint, responseTime);
    return responseTime;
  }, [actions]);
  
  // Gérer les erreurs globales
  const handleGlobalError = useCallback((error, context = '') => {
    actions.setError({
      type: 'GLOBAL_ERROR',
      message: error.message || 'Une erreur est survenue',
      context,
      timestamp: new Date().toISOString(),
    });
    actions.incrementErrorCount();
  }, [actions]);

  // Regrouper tous les callbacks
  const callbacks = useMemo(() => ({
    showNotification,
    showSuccess,
    showError,
    showInfo,
    showWarning,
    openModalWithCallback,
    closeModalWithCallback,
    toggleThemeWithPersistence,
    updatePreference,
    measureApiResponse,
    handleGlobalError
  }), [
    showNotification,
    showSuccess,
    showError,
    showInfo,
    showWarning,
    openModalWithCallback,
    closeModalWithCallback,
    toggleThemeWithPersistence,
    updatePreference,
    measureApiResponse,
    handleGlobalError
  ]);

  // État dérivé
  const isLoading = useMemo(() => 
    Object.values(loading).some(loading => loading), 
    [loading]
  );

  const hasError = useMemo(() => 
    error !== null, 
    [error]
  );

  const notificationCount = useMemo(() => 
    notifications.length, 
    [notifications]
  );

  // Détection automatique du thème système
  useEffect(() => {
    if (preferences.autoTheme) {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      const handleChange = (e) => {
        if (e.matches && theme !== 'dark') {
          actions.toggleTheme();
        } else if (!e.matches && theme !== 'light') {
          actions.toggleTheme();
        }
      };

      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    }
  }, [preferences.autoTheme, theme, actions]);

  // Nettoyage automatique des notifications anciennes
  useEffect(() => {
    const cleanup = setInterval(() => {
      const now = Date.now();
      notifications.forEach(notification => {
        if (notification.autoClose !== false && 
            notification.timestamp && 
            now - notification.timestamp > 30000) { // 30 secondes
          actions.removeNotification(notification.id);
        }
      });
    }, 5000);

    return () => clearInterval(cleanup);
  }, [notifications, actions]);

  return {
    // État
    notifications,
    modals,
    theme,
    preferences,
    loading,
    error,
    stats,
    isLoading,
    hasError,
    notificationCount,
    
    // Actions
    ...actions,
    
    // Callbacks optimisés
    ...callbacks,
  };
};

export default useUI;
