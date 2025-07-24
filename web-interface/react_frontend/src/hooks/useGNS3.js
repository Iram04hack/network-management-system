/**
 * Hook personnalisé pour la gestion de GNS3 Integration
 * Intégration avec le module gns3_integration backend - Gestion projets GNS3
 */

import { useCallback, useMemo, useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import gns3Service from '../services/gns3Service';
import { useGNS3WebSocket } from './useWebSocket.js';

/**
 * Hook principal pour la gestion de GNS3
 */
export const useGNS3 = () => {
  const [servers, setServers] = useState([]);
  const [currentServer, setCurrentServer] = useState(null);
  const [projects, setProjects] = useState([]);
  const [currentProject, setCurrentProject] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [snapshots, setSnapshots] = useState([]);
  
  const [loading, setLoading] = useState({
    servers: false,
    projects: false,
    nodes: false,
    links: false,
    templates: false,
    snapshots: false,
    action: false
  });
  
  const [error, setError] = useState(null);

  // WebSocket pour les événements GNS3 temps réel
  const gns3WS = useGNS3WebSocket('events', {
    autoReconnect: true,
    debug: false,
    onMessage: (data) => {
      handleGNS3RealtimeEvent(data);
    },
    onOpen: () => {
      console.log('GNS3 WebSocket connecté');
      // S'abonner aux événements nécessaires
      gns3WS.subscribeToEvents(['node_status', 'topology_changes', 'project_events']);
    },
    onError: (error) => {
      console.error('Erreur GNS3 WebSocket:', error);
    }
  });

  // Gestionnaire des événements GNS3 temps réel
  const handleGNS3RealtimeEvent = useCallback((data) => {
    const { type, event_data } = data;

    if (type === 'gns3_event' && event_data) {
      const { event_type, data: eventData } = event_data;

      switch (event_type) {
        case 'node.started':
        case 'node.stopped':
        case 'node.suspended':
          // Mise à jour du statut des nœuds
          if (eventData?.node_id) {
            const newStatus = event_type.split('.')[1];
            setNodes(prev => prev.map(node =>
              node.id === eventData.node_id
                ? { ...node, status: newStatus, lastUpdate: new Date().toISOString() }
                : node
            ));
          }
          break;

        case 'project.opened':
        case 'project.closed':
          // Mise à jour du statut des projets
          if (eventData?.project_id) {
            const newStatus = event_type.split('.')[1];
            setProjects(prev => prev.map(project =>
              project.id === eventData.project_id
                ? { ...project, status: newStatus, lastUpdate: new Date().toISOString() }
                : project
            ));

            if (currentProject && currentProject.id === eventData.project_id) {
              setCurrentProject(prev => ({ ...prev, status: newStatus }));
            }
          }
          break;

        case 'node.created':
        case 'node.deleted':
        case 'node.updated':
          // Rechargement des nœuds pour les changements de topologie
          if (currentProject) {
            fetchProjectNodes(currentProject.id);
          }
          break;

        case 'topology.changed':
          // Rechargement de la topologie complète
          if (eventData?.topology) {
            // Mise à jour de la topologie si nécessaire
            gns3WS.requestTopology();
          }
          break;

        case 'project.created':
        case 'project.deleted':
          // Rechargement de la liste des projets
          fetchProjects();
          break;
      }
    } else if (type === 'topology_response') {
      // Réponse à une demande de topologie
      if (data.data) {
        // Traitement des données de topologie
        console.log('Topologie mise à jour:', data.data);
      }
    }
  }, [currentProject, fetchProjectNodes, fetchProjects]);

  // Actions avec useCallback pour stabilité des références
  const fetchServers = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, servers: true }));
    setError(null);

    try {
      const result = await gns3Service.getServers(params);
      if (result.success) {
        setServers(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, servers: false }));
    }
  }, []);

  const getServer = useCallback(async (serverId) => {
    setLoading(prev => ({ ...prev, servers: true }));
    setError(null);

    try {
      const result = await gns3Service.getServer(serverId);
      if (result.success) {
        setCurrentServer(result.data);
        
        // Mettre à jour aussi dans la liste si elle existe
        setServers(prev => {
          const index = prev.findIndex(server => server.id === serverId);
          if (index !== -1) {
            const updated = [...prev];
            updated[index] = result.data;
            return updated;
          }
          return prev;
        });
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, servers: false }));
    }
  }, []);

  const createServer = useCallback(async (serverData) => {
    setLoading(prev => ({ ...prev, servers: true }));
    setError(null);

    try {
      const result = await gns3Service.createServer(serverData);
      if (result.success) {
        // Ajouter le nouveau serveur à la liste
        setServers(prev => [result.data, ...prev]);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, servers: false }));
    }
  }, []);

  const updateServer = useCallback(async (serverId, serverData) => {
    setLoading(prev => ({ ...prev, servers: true }));
    setError(null);

    try {
      const result = await gns3Service.updateServer(serverId, serverData);
      if (result.success) {
        // Mettre à jour dans la liste
        setServers(prev => prev.map(server => 
          server.id === serverId 
            ? { ...server, ...result.data }
            : server
        ));
        
        if (currentServer && currentServer.id === serverId) {
          setCurrentServer({ ...currentServer, ...result.data });
        }
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, servers: false }));
    }
  }, [currentServer]);

  const deleteServer = useCallback(async (serverId) => {
    setLoading(prev => ({ ...prev, servers: true }));
    setError(null);

    try {
      const result = await gns3Service.deleteServer(serverId);
      if (result.success) {
        // Supprimer de la liste
        setServers(prev => prev.filter(server => server.id !== serverId));
        
        if (currentServer && currentServer.id === serverId) {
          setCurrentServer(null);
        }
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, servers: false }));
    }
  }, [currentServer]);

  const testServer = useCallback(async (serverId) => {
    setLoading(prev => ({ ...prev, action: true }));
    setError(null);

    try {
      const result = await gns3Service.testServer(serverId);
      if (result.success) {
        // Mettre à jour le statut du serveur après le test
        setServers(prev => prev.map(server => 
          server.id === serverId 
            ? { ...server, last_test: result.data, test_passed: result.metadata.testPassed }
            : server
        ));
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  }, []);

  const fetchProjects = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, projects: true }));
    setError(null);

    try {
      const result = await gns3Service.getProjects(params);
      if (result.success) {
        setProjects(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, projects: false }));
    }
  }, []);

  const getProject = useCallback(async (projectId) => {
    setLoading(prev => ({ ...prev, projects: true }));
    setError(null);

    try {
      const result = await gns3Service.getProject(projectId);
      if (result.success) {
        setCurrentProject(result.data);
        
        // Mettre à jour aussi dans la liste si elle existe
        setProjects(prev => {
          const index = prev.findIndex(project => project.id === projectId);
          if (index !== -1) {
            const updated = [...prev];
            updated[index] = result.data;
            return updated;
          }
          return prev;
        });
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, projects: false }));
    }
  }, []);

  const createProject = useCallback(async (projectData) => {
    setLoading(prev => ({ ...prev, projects: true }));
    setError(null);

    try {
      const result = await gns3Service.createProject(projectData);
      if (result.success) {
        // Ajouter le nouveau projet à la liste
        setProjects(prev => [result.data, ...prev]);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, projects: false }));
    }
  }, []);

  const updateProject = useCallback(async (projectId, projectData) => {
    setLoading(prev => ({ ...prev, projects: true }));
    setError(null);

    try {
      const result = await gns3Service.updateProject(projectId, projectData);
      if (result.success) {
        // Mettre à jour dans la liste
        setProjects(prev => prev.map(project => 
          project.id === projectId 
            ? { ...project, ...result.data }
            : project
        ));
        
        if (currentProject && currentProject.id === projectId) {
          setCurrentProject({ ...currentProject, ...result.data });
        }
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, projects: false }));
    }
  }, [currentProject]);

  const deleteProject = useCallback(async (projectId) => {
    setLoading(prev => ({ ...prev, projects: true }));
    setError(null);

    try {
      const result = await gns3Service.deleteProject(projectId);
      if (result.success) {
        // Supprimer de la liste
        setProjects(prev => prev.filter(project => project.id !== projectId));
        
        if (currentProject && currentProject.id === projectId) {
          setCurrentProject(null);
        }
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, projects: false }));
    }
  }, [currentProject]);

  // Actions sur les projets
  const startProject = useCallback(async (projectId) => {
    return await _projectAction(projectId, 'start');
  }, []);

  const stopProject = useCallback(async (projectId) => {
    return await _projectAction(projectId, 'stop');
  }, []);

  const closeProject = useCallback(async (projectId) => {
    return await _projectAction(projectId, 'close');
  }, []);

  const _projectAction = useCallback(async (projectId, action) => {
    setLoading(prev => ({ ...prev, action: true }));
    setError(null);

    try {
      const result = await gns3Service[`${action}Project`](projectId);
      if (result.success) {
        // Mettre à jour le statut du projet
        setProjects(prev => prev.map(project => 
          project.id === projectId 
            ? { ...project, status: result.metadata.newStatus }
            : project
        ));
        
        if (currentProject && currentProject.id === projectId) {
          setCurrentProject({ ...currentProject, status: result.metadata.newStatus });
        }
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  }, [currentProject]);

  const fetchNodes = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, nodes: true }));
    setError(null);

    try {
      const result = await gns3Service.getNodes(params);
      if (result.success) {
        setNodes(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, nodes: false }));
    }
  }, []);

  const fetchProjectNodes = useCallback(async (projectId) => {
    setLoading(prev => ({ ...prev, nodes: true }));
    setError(null);

    try {
      const result = await gns3Service.getProjectNodes(projectId);
      if (result.success) {
        setNodes(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, nodes: false }));
    }
  }, []);

  // Actions sur les nœuds
  const startNode = useCallback(async (nodeId) => {
    return await _nodeAction(nodeId, 'start');
  }, []);

  const stopNode = useCallback(async (nodeId) => {
    return await _nodeAction(nodeId, 'stop');
  }, []);

  const suspendNode = useCallback(async (nodeId) => {
    return await _nodeAction(nodeId, 'suspend');
  }, []);

  const reloadNode = useCallback(async (nodeId) => {
    return await _nodeAction(nodeId, 'reload');
  }, []);

  const _nodeAction = useCallback(async (nodeId, action) => {
    setLoading(prev => ({ ...prev, action: true }));
    setError(null);

    try {
      const result = await gns3Service[`${action}Node`](nodeId);
      if (result.success) {
        // Mettre à jour le statut du nœud
        setNodes(prev => prev.map(node => 
          node.id === nodeId 
            ? { ...node, status: result.metadata.newStatus }
            : node
        ));
        
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  }, []);

  const fetchSnapshots = useCallback(async (params = {}) => {
    setLoading(prev => ({ ...prev, snapshots: true }));
    setError(null);

    try {
      const result = await gns3Service.getSnapshots(params);
      if (result.success) {
        setSnapshots(result.data);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, snapshots: false }));
    }
  }, []);

  const createSnapshot = useCallback(async (snapshotData) => {
    setLoading(prev => ({ ...prev, snapshots: true }));
    setError(null);

    try {
      const result = await gns3Service.createSnapshot(snapshotData);
      if (result.success) {
        // Ajouter le nouveau snapshot à la liste
        setSnapshots(prev => [result.data, ...prev]);
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, snapshots: false }));
    }
  }, []);

  const restoreSnapshot = useCallback(async (snapshotId) => {
    setLoading(prev => ({ ...prev, action: true }));
    setError(null);

    try {
      const result = await gns3Service.restoreSnapshot(snapshotId);
      if (result.success) {
        return result;
      } else {
        setError(result.error);
        return result;
      }
    } catch (error) {
      const errorInfo = { type: 'NETWORK_ERROR', message: error.message };
      setError(errorInfo);
      return { success: false, error: errorInfo };
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  }, []);

  // Fonctions utilitaires mémorisées
  const utils = useMemo(() => ({
    // Filtrer les serveurs par statut
    getActiveServers: () => 
      servers.filter(server => server.is_active),
    
    // Filtrer les projets par statut
    getProjectsByStatus: (status) => 
      projects.filter(project => project.status === status),
    
    // Obtenir les projets ouverts
    getOpenedProjects: () => 
      projects.filter(project => project.status === 'opened'),
    
    // Filtrer les nœuds par type
    getNodesByType: (nodeType) => 
      nodes.filter(node => node.node_type === nodeType),
    
    // Obtenir les nœuds en cours d'exécution
    getRunningNodes: () => 
      nodes.filter(node => node.status === 'started'),
    
    // Statistiques GNS3
    getGNS3Stats: () => ({
      totalServers: servers.length,
      activeServers: servers.filter(s => s.is_active).length,
      totalProjects: projects.length,
      openedProjects: projects.filter(p => p.status === 'opened').length,
      totalNodes: nodes.length,
      runningNodes: nodes.filter(n => n.status === 'started').length,
      totalSnapshots: snapshots.length,
      lastUpdate: new Date().toISOString()
    }),
    
    // Rechercher un serveur par nom ou host
    searchServers: (query) => 
      servers.filter(server => 
        server.name.toLowerCase().includes(query.toLowerCase()) ||
        server.host.toLowerCase().includes(query.toLowerCase())
      ),
    
    // Rechercher un projet par nom
    searchProjects: (query) => 
      projects.filter(project => 
        project.name.toLowerCase().includes(query.toLowerCase())
      ),
    
    // Obtenir les informations de serveur d'un projet
    getProjectServer: (projectId) => {
      const project = projects.find(p => p.id === projectId);
      if (!project) return null;
      return servers.find(s => s.id === project.server_id);
    },
    
    // Valider les données d'un serveur
    validateServerData: (serverData) => {
      const requiredFields = ['name', 'host', 'port'];
      const errors = [];
      
      requiredFields.forEach(field => {
        if (!serverData[field]) {
          errors.push(`Champ requis: ${field}`);
        }
      });
      
      if (serverData.port && (serverData.port < 1 || serverData.port > 65535)) {
        errors.push('Le port doit être entre 1 et 65535');
      }
      
      return {
        isValid: errors.length === 0,
        errors
      };
    },
    
    // Valider les données d'un projet
    validateProjectData: (projectData) => {
      const requiredFields = ['name', 'server'];
      const errors = [];
      
      requiredFields.forEach(field => {
        if (!projectData[field]) {
          errors.push(`Champ requis: ${field}`);
        }
      });
      
      return {
        isValid: errors.length === 0,
        errors
      };
    }
  }), [servers, projects, nodes, snapshots]);

  // Actions regroupées pour réutilisation
  const actions = useMemo(() => ({
    // Serveurs
    fetchServers,
    getServer,
    createServer,
    updateServer,
    deleteServer,
    testServer,
    
    // Projets
    fetchProjects,
    getProject,
    createProject,
    updateProject,
    deleteProject,
    startProject,
    stopProject,
    closeProject,
    
    // Nœuds
    fetchNodes,
    fetchProjectNodes,
    startNode,
    stopNode,
    suspendNode,
    reloadNode,
    
    // Snapshots
    fetchSnapshots,
    createSnapshot,
    restoreSnapshot
  }), [
    fetchServers, getServer, createServer, updateServer, deleteServer, testServer,
    fetchProjects, getProject, createProject, updateProject, deleteProject,
    startProject, stopProject, closeProject,
    fetchNodes, fetchProjectNodes, startNode, stopNode, suspendNode, reloadNode,
    fetchSnapshots, createSnapshot, restoreSnapshot
  ]);

  // Callbacks optimisés
  const refreshAllData = useCallback(async () => {
    const promises = [
      actions.fetchServers(),
      actions.fetchProjects(),
      actions.fetchNodes(),
      actions.fetchSnapshots()
    ];
    
    const results = await Promise.allSettled(promises);
    return results;
  }, [actions]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearCurrentServer = useCallback(() => {
    setCurrentServer(null);
  }, []);

  const clearCurrentProject = useCallback(() => {
    setCurrentProject(null);
  }, []);

  return {
    // État des données
    servers,
    currentServer,
    projects,
    currentProject,
    nodes,
    links,
    templates,
    snapshots,
    
    // État de chargement et erreurs
    loading,
    error,
    isLoading: Object.values(loading).some(l => l),

    // WebSocket GNS3 temps réel
    webSocket: {
      isConnected: gns3WS.isConnected,
      isConnecting: gns3WS.isConnecting,
      connectionState: gns3WS.connectionState,
      error: gns3WS.error,
      stats: gns3WS.stats,
      lastMessage: gns3WS.lastMessage,
      gns3Events: gns3WS.gns3Events,
      nodeStatuses: gns3WS.nodeStatuses,
      projectStatuses: gns3WS.projectStatuses,
      topologyData: gns3WS.topologyData,
      actions: {
        connect: gns3WS.connect,
        disconnect: gns3WS.disconnect,
        reconnect: gns3WS.reconnect,
        subscribeToEvents: gns3WS.subscribeToEvents,
        unsubscribeFromEvents: gns3WS.unsubscribeFromEvents,
        requestTopology: gns3WS.requestTopology,
        performNodeAction: gns3WS.performNodeAction
      }
    },

    // Actions principales
    fetchServers,
    getServer,
    createServer,
    updateServer,
    deleteServer,
    testServer,
    fetchProjects,
    getProject,
    createProject,
    updateProject,
    deleteProject,
    startProject,
    stopProject,
    closeProject,
    fetchNodes,
    fetchProjectNodes,
    startNode,
    stopNode,
    suspendNode,
    reloadNode,
    fetchSnapshots,
    createSnapshot,
    restoreSnapshot,

    // Utilitaires
    ...utils,

    // Callbacks optimisés
    refreshAllData,
    clearError,
    clearCurrentServer,
    clearCurrentProject,
  };
};

/**
 * Hook pour la gestion d'un projet GNS3 spécifique avec suivi temps réel
 */
export const useGNS3Project = (projectId) => {
  const [projectData, setProjectData] = useState(null);
  const [projectNodes, setProjectNodes] = useState([]);
  const [projectLinks, setProjectLinks] = useState([]);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const refreshProject = useCallback(async () => {
    if (!projectId) return;

    try {
      const [projectResult, nodesResult] = await Promise.allSettled([
        gns3Service.getProject(projectId),
        gns3Service.getProjectNodes(projectId)
      ]);

      if (projectResult.status === 'fulfilled' && projectResult.value.success) {
        setProjectData(projectResult.value.data);
      }

      if (nodesResult.status === 'fulfilled' && nodesResult.value.success) {
        setProjectNodes(nodesResult.value.data);
      }

      setLastUpdate(new Date().toISOString());
    } catch (error) {
      console.error('Error refreshing project:', error);
    }
  }, [projectId]);

  const startMonitoring = useCallback((interval = 30000) => {
    if (isMonitoring) return;

    setIsMonitoring(true);
    
    // Première récupération immédiate
    refreshProject();
    
    // Puis surveillance périodique
    const intervalId = setInterval(refreshProject, interval);
    
    return () => {
      clearInterval(intervalId);
      setIsMonitoring(false);
    };
  }, [isMonitoring, refreshProject]);

  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false);
  }, []);

  return {
    projectData,
    projectNodes,
    projectLinks,
    isMonitoring,
    lastUpdate,
    refreshProject,
    startMonitoring,
    stopMonitoring
  };
};

/**
 * Hook pour la gestion des actions en lot sur plusieurs éléments
 */
export const useGNS3Batch = () => {
  const [batchResults, setBatchResults] = useState([]);
  const [isBatchProcessing, setIsBatchProcessing] = useState(false);

  const batchStartNodes = useCallback(async (nodeIds) => {
    setIsBatchProcessing(true);
    const results = [];

    for (const nodeId of nodeIds) {
      try {
        const result = await gns3Service.startNode(nodeId);
        results.push({ nodeId, action: 'start', success: result.success, error: result.error });
      } catch (error) {
        results.push({ nodeId, action: 'start', success: false, error: error.message });
      }
    }

    setBatchResults(results);
    setIsBatchProcessing(false);
    return results;
  }, []);

  const batchStopNodes = useCallback(async (nodeIds) => {
    setIsBatchProcessing(true);
    const results = [];

    for (const nodeId of nodeIds) {
      try {
        const result = await gns3Service.stopNode(nodeId);
        results.push({ nodeId, action: 'stop', success: result.success, error: result.error });
      } catch (error) {
        results.push({ nodeId, action: 'stop', success: false, error: error.message });
      }
    }

    setBatchResults(results);
    setIsBatchProcessing(false);
    return results;
  }, []);

  const clearBatchResults = useCallback(() => {
    setBatchResults([]);
  }, []);

  return {
    batchResults,
    isBatchProcessing,
    batchStartNodes,
    batchStopNodes,
    clearBatchResults
  };
};

export default useGNS3;