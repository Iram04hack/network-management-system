/**
 * Hook personnalisé pour la gestion des commandes
 * Exécution et historique des commandes
 */

import { useCallback, useMemo } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { createSelector } from '@reduxjs/toolkit';
import {
  executeCommand,
  setCurrentCommand,
  clearCurrentCommand,
  clearError,
  addToHistory
} from '../store/slices/commandsSlice';

// Sélecteurs mémorisés pour éviter les re-renders
const selectCommands = createSelector(
  [(state) => state?.commands?.items],
  (items) => items || []
);

const selectCurrentCommand = createSelector(
  [(state) => state?.commands?.currentCommand],
  (currentCommand) => currentCommand || null
);

const selectLoading = createSelector(
  [(state) => state?.commands?.loading],
  (loading) => loading || false
);

const selectError = createSelector(
  [(state) => state?.commands?.error],
  (error) => error || null
);

const selectHistory = createSelector(
  [(state) => state?.commands?.history],
  (history) => history ? [...history] : []
);

const selectStats = createSelector(
  [(state) => state?.commands?.stats],
  (stats) => stats ? { ...stats } : {}
);

/**
 * Hook principal pour la gestion des commandes
 */
export const useCommands = () => {
  const dispatch = useDispatch();
  
  // Sélecteurs Redux mémorisés
  const commands = useSelector(selectCommands);
  const currentCommand = useSelector(selectCurrentCommand);
  const loading = useSelector(selectLoading);
  const error = useSelector(selectError);
  const history = useSelector(selectHistory);
  const stats = useSelector(selectStats);

  // Actions
  const executeCommandAction = useCallback((command) => {
    dispatch(executeCommand(command));
  }, [dispatch]);

  const setCurrentCommandAction = useCallback((command) => {
    dispatch(setCurrentCommand(command));
  }, [dispatch]);

  const clearCurrentCommandAction = useCallback(() => {
    dispatch(clearCurrentCommand());
  }, [dispatch]);

  const addToHistoryAction = useCallback((command) => {
    dispatch(addToHistory(command));
  }, [dispatch]);

  const clearErrorAction = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  // État dérivé
  const isLoading = useMemo(() => 
    Object.values(loading).some(loading => loading), 
    [loading]
  );

  const lastExecution = useMemo(() => 
    history.length > 0 ? history[history.length - 1] : null, 
    [history]
  );

  // Fonction pour obtenir les statistiques d'exécution
  const getExecutionStats = useCallback(() => {
    const total = history.length;
    const successful = history.filter(cmd => cmd.status === 'completed').length;
    const failed = history.filter(cmd => cmd.status === 'failed').length;
    
    return {
      total,
      successful,
      failed,
      successRate: total > 0 ? (successful / total) * 100 : 0
    };
  }, [history]);

  return {
    // État
    commands,
    currentCommand,
    loading,
    error,
    history,
    stats,
    isLoading,
    lastExecution,

    // Actions
    executeCommand: executeCommandAction,
    setCurrentCommand: setCurrentCommandAction,
    clearCurrentCommand: clearCurrentCommandAction,
    addToHistory: addToHistoryAction,
    clearError: clearErrorAction,

    // Utilitaires
    getExecutionStats,
    getHistoryByStatus: (status) => history.filter(cmd => cmd.status === status),
    getRecentExecutions: (limit = 10) => history.slice(-limit)
  };
};

// Sélecteurs supplémentaires pour useCommandExecution
const selectExecutionCommands = createSelector(
  [(state) => state?.commands?.items],
  (items) => items || []
);

const selectExecutionLoading = createSelector(
  [(state) => state?.commands?.loading],
  (loading) => loading || false
);

const selectExecutionError = createSelector(
  [(state) => state?.commands?.error],
  (error) => error || null
);

const selectLastExecution = createSelector(
  [(state) => state?.commands?.lastExecution],
  (lastExecution) => lastExecution || null
);

/**
 * Hook pour l'exécution de commandes spécifiques
 */
export const useCommandExecution = () => {
  const dispatch = useDispatch();
  
  // Sélecteurs Redux mémorisés
  const commands = useSelector(selectExecutionCommands);
  const loading = useSelector(selectExecutionLoading);
  const error = useSelector(selectExecutionError);
  const lastExecution = useSelector(selectLastExecution);
  
  const networkCommands = useMemo(() => ({
    scanNetwork: (target, portRange = '1-1000') => 
      dispatch(executeCommand({
        name: 'network_scan',
        parameters: { target, port_range: portRange },
      })),
    
    pingHost: (host) =>
      dispatch(executeCommand({
        name: 'ping',
        parameters: { host },
      })),
    
    traceRoute: (destination) => 
      dispatch(executeCommand({
        name: 'traceroute',
        parameters: { destination },
      })),
  }), [dispatch]);

  const systemCommands = useMemo(() => ({
    getSystemInfo: () => 
      dispatch(executeCommand({
        name: 'system_info',
        parameters: {},
      })),
    
    checkDiskSpace: () => 
      dispatch(executeCommand({
        name: 'disk_usage',
        parameters: {},
      })),
    
    getProcessList: () => 
      dispatch(executeCommand({
        name: 'process_list',
        parameters: {},
      })),
  }), [dispatch]);

  // Fonction pour obtenir toutes les commandes disponibles
  const getAvailableCommands = useCallback(() => {
    return [
      // Commandes réseau
      { name: 'scan', description: 'Scanner le réseau', category: 'network', syntax: 'scan <target> [port-range]' },
      { name: 'ping', description: 'Ping un hôte', category: 'network', syntax: 'ping <host>' },
      { name: 'traceroute', description: 'Tracer la route vers un hôte', category: 'network', syntax: 'traceroute <destination>' },

      // Commandes système
      { name: 'sysinfo', description: 'Informations système', category: 'system', syntax: 'sysinfo' },
      { name: 'diskspace', description: 'Espace disque', category: 'system', syntax: 'diskspace' },
      { name: 'processes', description: 'Liste des processus', category: 'system', syntax: 'processes' },

      // Commandes utilitaires
      { name: 'help', description: 'Afficher l\'aide', category: 'utility', syntax: 'help [command]' },
      { name: 'clear', description: 'Effacer le terminal', category: 'utility', syntax: 'clear' },
      { name: 'history', description: 'Historique des commandes', category: 'utility', syntax: 'history' },
    ];
  }, []);

  return {
    loading,
    error,
    lastExecution,
    networkCommands,
    systemCommands,
    getAvailableCommands,
  };
};

export default useCommands;
