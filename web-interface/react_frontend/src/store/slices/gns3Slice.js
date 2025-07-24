/**
 * Slice Redux pour la gestion de GNS3 Integration
 * Intégration avec le module gns3_integration backend - Gestion projets GNS3
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import gns3Service from '../../services/gns3Service';

/**
 * État initial du slice gns3
 */
const initialState = {
  // Serveurs GNS3
  servers: [],
  currentServer: null,
  
  // Projets
  projects: [],
  currentProject: null,
  
  // Nœuds et topologie
  nodes: [],
  links: [],
  templates: [],
  
  // Snapshots
  snapshots: [],
  
  // Scripts et workflows
  scripts: [],
  workflows: [],
  scriptExecutions: [],
  workflowExecutions: [],
  
  // États de chargement
  loading: {
    servers: false,
    projects: false,
    nodes: false,
    links: false,
    templates: false,
    snapshots: false,
    scripts: false,
    workflows: false,
    action: false
  },
  
  // Gestion d'erreurs
  error: null,
  lastError: null,
  
  // Métadonnées et cache
  lastFetch: {
    servers: null,
    projects: null,
    nodes: null,
    snapshots: null
  },
  
  // États des actions en cours
  pendingActions: {
    startingProjects: [],
    stoppingProjects: [],
    startingNodes: [],
    stoppingNodes: []
  },
  
  // Filtres et tri
  filters: {
    serverStatus: '',
    projectStatus: '',
    nodeType: '',
    nodeStatus: ''
  },
  sorting: {
    field: 'name',
    direction: 'asc'
  }
};

/**
 * Actions asynchrones (thunks) pour GNS3
 */

// Récupérer les serveurs GNS3
export const fetchServers = createAsyncThunk(
  'gns3/fetchServers',
  async (params = {}, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const { filters, sorting } = state.gns3;
      
      const requestParams = {
        is_active: filters.serverStatus === 'active' ? true : filters.serverStatus === 'inactive' ? false : undefined,
        ordering: `${sorting.direction === 'desc' ? '-' : ''}${sorting.field}`,
        ...params
      };
      
      const result = await gns3Service.getServers(requestParams);
      
      if (result.success) {
        return {
          servers: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer un serveur spécifique
export const fetchServer = createAsyncThunk(
  'gns3/fetchServer',
  async (serverId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.getServer(serverId);
      
      if (result.success) {
        return {
          server: result.data,
          serverId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Créer un serveur
export const createServer = createAsyncThunk(
  'gns3/createServer',
  async (serverData, { rejectWithValue }) => {
    try {
      const result = await gns3Service.createServer(serverData);
      
      if (result.success) {
        return {
          server: result.data,
          serverId: result.serverId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Mettre à jour un serveur
export const updateServer = createAsyncThunk(
  'gns3/updateServer',
  async ({ serverId, serverData }, { rejectWithValue }) => {
    try {
      const result = await gns3Service.updateServer(serverId, serverData);
      
      if (result.success) {
        return {
          server: result.data,
          serverId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Supprimer un serveur
export const deleteServer = createAsyncThunk(
  'gns3/deleteServer',
  async (serverId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.deleteServer(serverId);
      
      if (result.success) {
        return {
          serverId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Tester un serveur
export const testServer = createAsyncThunk(
  'gns3/testServer',
  async (serverId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.testServer(serverId);
      
      if (result.success) {
        return {
          serverId,
          testResult: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer les projets
export const fetchProjects = createAsyncThunk(
  'gns3/fetchProjects',
  async (params = {}, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const { filters, sorting } = state.gns3;
      
      const requestParams = {
        status: filters.projectStatus || undefined,
        ordering: `${sorting.direction === 'desc' ? '-' : ''}${sorting.field}`,
        ...params
      };
      
      const result = await gns3Service.getProjects(requestParams);
      
      if (result.success) {
        return {
          projects: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer un projet spécifique
export const fetchProject = createAsyncThunk(
  'gns3/fetchProject',
  async (projectId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.getProject(projectId);
      
      if (result.success) {
        return {
          project: result.data,
          projectId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Créer un projet
export const createProject = createAsyncThunk(
  'gns3/createProject',
  async (projectData, { rejectWithValue }) => {
    try {
      const result = await gns3Service.createProject(projectData);
      
      if (result.success) {
        return {
          project: result.data,
          projectId: result.projectId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Mettre à jour un projet
export const updateProject = createAsyncThunk(
  'gns3/updateProject',
  async ({ projectId, projectData }, { rejectWithValue }) => {
    try {
      const result = await gns3Service.updateProject(projectId, projectData);
      
      if (result.success) {
        return {
          project: result.data,
          projectId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Supprimer un projet
export const deleteProject = createAsyncThunk(
  'gns3/deleteProject',
  async (projectId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.deleteProject(projectId);
      
      if (result.success) {
        return {
          projectId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Actions sur les projets
export const startProject = createAsyncThunk(
  'gns3/startProject',
  async (projectId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.startProject(projectId);
      
      if (result.success) {
        return {
          projectId,
          action: 'start',
          newStatus: result.metadata.newStatus,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

export const stopProject = createAsyncThunk(
  'gns3/stopProject',
  async (projectId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.stopProject(projectId);
      
      if (result.success) {
        return {
          projectId,
          action: 'stop',
          newStatus: result.metadata.newStatus,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

export const closeProject = createAsyncThunk(
  'gns3/closeProject',
  async (projectId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.closeProject(projectId);
      
      if (result.success) {
        return {
          projectId,
          action: 'close',
          newStatus: result.metadata.newStatus,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer les nœuds
export const fetchNodes = createAsyncThunk(
  'gns3/fetchNodes',
  async (params = {}, { getState, rejectWithValue }) => {
    try {
      const state = getState();
      const { filters, sorting } = state.gns3;
      
      const requestParams = {
        node_type: filters.nodeType || undefined,
        status: filters.nodeStatus || undefined,
        ordering: `${sorting.direction === 'desc' ? '-' : ''}${sorting.field}`,
        ...params
      };
      
      const result = await gns3Service.getNodes(requestParams);
      
      if (result.success) {
        return {
          nodes: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer les nœuds d'un projet
export const fetchProjectNodes = createAsyncThunk(
  'gns3/fetchProjectNodes',
  async (projectId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.getProjectNodes(projectId);
      
      if (result.success) {
        return {
          nodes: result.data,
          projectId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Actions sur les nœuds
export const startNode = createAsyncThunk(
  'gns3/startNode',
  async (nodeId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.startNode(nodeId);
      
      if (result.success) {
        return {
          nodeId,
          action: 'start',
          newStatus: result.metadata.newStatus,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

export const stopNode = createAsyncThunk(
  'gns3/stopNode',
  async (nodeId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.stopNode(nodeId);
      
      if (result.success) {
        return {
          nodeId,
          action: 'stop',
          newStatus: result.metadata.newStatus,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Récupérer les snapshots
export const fetchSnapshots = createAsyncThunk(
  'gns3/fetchSnapshots',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await gns3Service.getSnapshots(params);
      
      if (result.success) {
        return {
          snapshots: result.data,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Créer un snapshot
export const createSnapshot = createAsyncThunk(
  'gns3/createSnapshot',
  async (snapshotData, { rejectWithValue }) => {
    try {
      const result = await gns3Service.createSnapshot(snapshotData);
      
      if (result.success) {
        return {
          snapshot: result.data,
          snapshotId: result.snapshotId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

// Restaurer un snapshot
export const restoreSnapshot = createAsyncThunk(
  'gns3/restoreSnapshot',
  async (snapshotId, { rejectWithValue }) => {
    try {
      const result = await gns3Service.restoreSnapshot(snapshotId);
      
      if (result.success) {
        return {
          snapshotId,
          metadata: result.metadata
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error
      });
    }
  }
);

/**
 * Slice Redux pour GNS3
 */
const gns3Slice = createSlice({
  name: 'gns3',
  initialState,
  reducers: {
    // Actions synchrones pour la gestion de l'état local
    setCurrentServer: (state, action) => {
      state.currentServer = action.payload;
    },
    
    clearCurrentServer: (state) => {
      state.currentServer = null;
    },
    
    setCurrentProject: (state, action) => {
      state.currentProject = action.payload;
    },
    
    clearCurrentProject: (state) => {
      state.currentProject = null;
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
    
    // Gestion des actions en attente
    addPendingAction: (state, action) => {
      const { type, id } = action.payload;
      if (state.pendingActions[type] && !state.pendingActions[type].includes(id)) {
        state.pendingActions[type].push(id);
      }
    },
    
    removePendingAction: (state, action) => {
      const { type, id } = action.payload;
      if (state.pendingActions[type]) {
        state.pendingActions[type] = state.pendingActions[type].filter(item => item !== id);
      }
    },
    
    clearPendingActions: (state) => {
      state.pendingActions = initialState.pendingActions;
    },
    
    // Mise à jour optimiste des états
    optimisticUpdateServer: (state, action) => {
      const { serverId, updateData } = action.payload;
      const server = state.servers.find(s => s.id === serverId);
      if (server) {
        Object.assign(server, updateData);
      }
      
      if (state.currentServer && state.currentServer.id === serverId) {
        Object.assign(state.currentServer, updateData);
      }
    },
    
    optimisticUpdateProject: (state, action) => {
      const { projectId, updateData } = action.payload;
      const project = state.projects.find(p => p.id === projectId);
      if (project) {
        Object.assign(project, updateData);
      }
      
      if (state.currentProject && state.currentProject.id === projectId) {
        Object.assign(state.currentProject, updateData);
      }
    },
    
    optimisticUpdateNode: (state, action) => {
      const { nodeId, updateData } = action.payload;
      const node = state.nodes.find(n => n.id === nodeId);
      if (node) {
        Object.assign(node, updateData);
      }
    },
  },
  
  extraReducers: (builder) => {
    // Fetch Servers
    builder
      .addCase(fetchServers.pending, (state) => {
        state.loading.servers = true;
        state.error = null;
      })
      .addCase(fetchServers.fulfilled, (state, action) => {
        state.loading.servers = false;
        state.servers = action.payload.servers;
        state.lastFetch.servers = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchServers.rejected, (state, action) => {
        state.loading.servers = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Server
    builder
      .addCase(fetchServer.pending, (state) => {
        state.loading.servers = true;
        state.error = null;
      })
      .addCase(fetchServer.fulfilled, (state, action) => {
        state.loading.servers = false;
        const { server, serverId } = action.payload;
        
        state.currentServer = server;
        
        // Mettre à jour aussi dans la liste
        const index = state.servers.findIndex(s => s.id === serverId);
        if (index !== -1) {
          state.servers[index] = server;
        }
        
        state.error = null;
      })
      .addCase(fetchServer.rejected, (state, action) => {
        state.loading.servers = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Create Server
    builder
      .addCase(createServer.pending, (state) => {
        state.loading.servers = true;
        state.error = null;
      })
      .addCase(createServer.fulfilled, (state, action) => {
        state.loading.servers = false;
        state.servers.unshift(action.payload.server);
        state.error = null;
      })
      .addCase(createServer.rejected, (state, action) => {
        state.loading.servers = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Update Server
    builder
      .addCase(updateServer.pending, (state) => {
        state.loading.servers = true;
        state.error = null;
      })
      .addCase(updateServer.fulfilled, (state, action) => {
        state.loading.servers = false;
        const { server, serverId } = action.payload;
        
        const index = state.servers.findIndex(s => s.id === serverId);
        if (index !== -1) {
          state.servers[index] = server;
        }
        
        if (state.currentServer && state.currentServer.id === serverId) {
          state.currentServer = server;
        }
        
        state.error = null;
      })
      .addCase(updateServer.rejected, (state, action) => {
        state.loading.servers = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Delete Server
    builder
      .addCase(deleteServer.pending, (state) => {
        state.loading.servers = true;
        state.error = null;
      })
      .addCase(deleteServer.fulfilled, (state, action) => {
        state.loading.servers = false;
        const { serverId } = action.payload;
        
        state.servers = state.servers.filter(s => s.id !== serverId);
        
        if (state.currentServer && state.currentServer.id === serverId) {
          state.currentServer = null;
        }
        
        state.error = null;
      })
      .addCase(deleteServer.rejected, (state, action) => {
        state.loading.servers = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Test Server
    builder
      .addCase(testServer.pending, (state, action) => {
        state.loading.action = true;
        state.error = null;
        
        // Ajouter à la liste des actions en attente
        const serverId = action.meta.arg;
        if (!state.pendingActions.testingServers) {
          state.pendingActions.testingServers = [];
        }
        if (!state.pendingActions.testingServers.includes(serverId)) {
          state.pendingActions.testingServers.push(serverId);
        }
      })
      .addCase(testServer.fulfilled, (state, action) => {
        state.loading.action = false;
        const { serverId, testResult, metadata } = action.payload;
        
        // Mettre à jour le serveur avec le résultat du test
        const server = state.servers.find(s => s.id === serverId);
        if (server) {
          server.last_test = testResult;
          server.test_passed = metadata.testPassed;
          server.last_test_time = metadata.timestamp;
        }
        
        // Supprimer de la liste des actions en attente
        if (state.pendingActions.testingServers) {
          state.pendingActions.testingServers = state.pendingActions.testingServers.filter(id => id !== serverId);
        }
        
        state.error = null;
      })
      .addCase(testServer.rejected, (state, action) => {
        state.loading.action = false;
        const serverId = action.meta.arg;
        
        // Supprimer de la liste des actions en attente
        if (state.pendingActions.testingServers) {
          state.pendingActions.testingServers = state.pendingActions.testingServers.filter(id => id !== serverId);
        }
        
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Projects
    builder
      .addCase(fetchProjects.pending, (state) => {
        state.loading.projects = true;
        state.error = null;
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.loading.projects = false;
        state.projects = action.payload.projects;
        state.lastFetch.projects = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.loading.projects = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Project
    builder
      .addCase(fetchProject.pending, (state) => {
        state.loading.projects = true;
        state.error = null;
      })
      .addCase(fetchProject.fulfilled, (state, action) => {
        state.loading.projects = false;
        const { project, projectId } = action.payload;
        
        state.currentProject = project;
        
        // Mettre à jour aussi dans la liste
        const index = state.projects.findIndex(p => p.id === projectId);
        if (index !== -1) {
          state.projects[index] = project;
        }
        
        state.error = null;
      })
      .addCase(fetchProject.rejected, (state, action) => {
        state.loading.projects = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Create Project
    builder
      .addCase(createProject.pending, (state) => {
        state.loading.projects = true;
        state.error = null;
      })
      .addCase(createProject.fulfilled, (state, action) => {
        state.loading.projects = false;
        state.projects.unshift(action.payload.project);
        state.error = null;
      })
      .addCase(createProject.rejected, (state, action) => {
        state.loading.projects = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Update Project
    builder
      .addCase(updateProject.pending, (state) => {
        state.loading.projects = true;
        state.error = null;
      })
      .addCase(updateProject.fulfilled, (state, action) => {
        state.loading.projects = false;
        const { project, projectId } = action.payload;
        
        const index = state.projects.findIndex(p => p.id === projectId);
        if (index !== -1) {
          state.projects[index] = project;
        }
        
        if (state.currentProject && state.currentProject.id === projectId) {
          state.currentProject = project;
        }
        
        state.error = null;
      })
      .addCase(updateProject.rejected, (state, action) => {
        state.loading.projects = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Delete Project
    builder
      .addCase(deleteProject.pending, (state) => {
        state.loading.projects = true;
        state.error = null;
      })
      .addCase(deleteProject.fulfilled, (state, action) => {
        state.loading.projects = false;
        const { projectId } = action.payload;
        
        state.projects = state.projects.filter(p => p.id !== projectId);
        
        if (state.currentProject && state.currentProject.id === projectId) {
          state.currentProject = null;
        }
        
        state.error = null;
      })
      .addCase(deleteProject.rejected, (state, action) => {
        state.loading.projects = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Project Actions (start, stop, close)
    builder
      .addCase(startProject.pending, (state, action) => {
        state.loading.action = true;
        const projectId = action.meta.arg;
        state.pendingActions.startingProjects.push(projectId);
      })
      .addCase(startProject.fulfilled, (state, action) => {
        state.loading.action = false;
        const { projectId, newStatus } = action.payload;
        
        // Mettre à jour le statut du projet
        const project = state.projects.find(p => p.id === projectId);
        if (project) {
          project.status = newStatus;
        }
        
        if (state.currentProject && state.currentProject.id === projectId) {
          state.currentProject.status = newStatus;
        }
        
        // Supprimer de la liste des actions en attente
        state.pendingActions.startingProjects = state.pendingActions.startingProjects.filter(id => id !== projectId);
        
        state.error = null;
      })
      .addCase(startProject.rejected, (state, action) => {
        state.loading.action = false;
        const projectId = action.meta.arg;
        state.pendingActions.startingProjects = state.pendingActions.startingProjects.filter(id => id !== projectId);
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Similar patterns for stopProject and closeProject...
    builder
      .addCase(stopProject.pending, (state, action) => {
        state.loading.action = true;
        const projectId = action.meta.arg;
        state.pendingActions.stoppingProjects.push(projectId);
      })
      .addCase(stopProject.fulfilled, (state, action) => {
        state.loading.action = false;
        const { projectId, newStatus } = action.payload;
        
        const project = state.projects.find(p => p.id === projectId);
        if (project) {
          project.status = newStatus;
        }
        
        if (state.currentProject && state.currentProject.id === projectId) {
          state.currentProject.status = newStatus;
        }
        
        state.pendingActions.stoppingProjects = state.pendingActions.stoppingProjects.filter(id => id !== projectId);
        state.error = null;
      })
      .addCase(stopProject.rejected, (state, action) => {
        state.loading.action = false;
        const projectId = action.meta.arg;
        state.pendingActions.stoppingProjects = state.pendingActions.stoppingProjects.filter(id => id !== projectId);
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Nodes
    builder
      .addCase(fetchNodes.pending, (state) => {
        state.loading.nodes = true;
        state.error = null;
      })
      .addCase(fetchNodes.fulfilled, (state, action) => {
        state.loading.nodes = false;
        state.nodes = action.payload.nodes;
        state.lastFetch.nodes = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchNodes.rejected, (state, action) => {
        state.loading.nodes = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Project Nodes
    builder
      .addCase(fetchProjectNodes.pending, (state) => {
        state.loading.nodes = true;
        state.error = null;
      })
      .addCase(fetchProjectNodes.fulfilled, (state, action) => {
        state.loading.nodes = false;
        state.nodes = action.payload.nodes;
        state.error = null;
      })
      .addCase(fetchProjectNodes.rejected, (state, action) => {
        state.loading.nodes = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Node Actions
    builder
      .addCase(startNode.pending, (state, action) => {
        state.loading.action = true;
        const nodeId = action.meta.arg;
        state.pendingActions.startingNodes.push(nodeId);
      })
      .addCase(startNode.fulfilled, (state, action) => {
        state.loading.action = false;
        const { nodeId, newStatus } = action.payload;
        
        const node = state.nodes.find(n => n.id === nodeId);
        if (node) {
          node.status = newStatus;
        }
        
        state.pendingActions.startingNodes = state.pendingActions.startingNodes.filter(id => id !== nodeId);
        state.error = null;
      })
      .addCase(startNode.rejected, (state, action) => {
        state.loading.action = false;
        const nodeId = action.meta.arg;
        state.pendingActions.startingNodes = state.pendingActions.startingNodes.filter(id => id !== nodeId);
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    builder
      .addCase(stopNode.pending, (state, action) => {
        state.loading.action = true;
        const nodeId = action.meta.arg;
        state.pendingActions.stoppingNodes.push(nodeId);
      })
      .addCase(stopNode.fulfilled, (state, action) => {
        state.loading.action = false;
        const { nodeId, newStatus } = action.payload;
        
        const node = state.nodes.find(n => n.id === nodeId);
        if (node) {
          node.status = newStatus;
        }
        
        state.pendingActions.stoppingNodes = state.pendingActions.stoppingNodes.filter(id => id !== nodeId);
        state.error = null;
      })
      .addCase(stopNode.rejected, (state, action) => {
        state.loading.action = false;
        const nodeId = action.meta.arg;
        state.pendingActions.stoppingNodes = state.pendingActions.stoppingNodes.filter(id => id !== nodeId);
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch Snapshots
    builder
      .addCase(fetchSnapshots.pending, (state) => {
        state.loading.snapshots = true;
        state.error = null;
      })
      .addCase(fetchSnapshots.fulfilled, (state, action) => {
        state.loading.snapshots = false;
        state.snapshots = action.payload.snapshots;
        state.lastFetch.snapshots = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchSnapshots.rejected, (state, action) => {
        state.loading.snapshots = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Create Snapshot
    builder
      .addCase(createSnapshot.pending, (state) => {
        state.loading.snapshots = true;
        state.error = null;
      })
      .addCase(createSnapshot.fulfilled, (state, action) => {
        state.loading.snapshots = false;
        state.snapshots.unshift(action.payload.snapshot);
        state.error = null;
      })
      .addCase(createSnapshot.rejected, (state, action) => {
        state.loading.snapshots = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Restore Snapshot
    builder
      .addCase(restoreSnapshot.pending, (state) => {
        state.loading.action = true;
        state.error = null;
      })
      .addCase(restoreSnapshot.fulfilled, (state, action) => {
        state.loading.action = false;
        state.error = null;
      })
      .addCase(restoreSnapshot.rejected, (state, action) => {
        state.loading.action = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
  },
});

// Export des actions
export const {
  setCurrentServer,
  clearCurrentServer,
  setCurrentProject,
  clearCurrentProject,
  setFilters,
  setSorting,
  clearFilters,
  clearError,
  addPendingAction,
  removePendingAction,
  clearPendingActions,
  optimisticUpdateServer,
  optimisticUpdateProject,
  optimisticUpdateNode,
} = gns3Slice.actions;

// Sélecteurs
export const selectServers = (state) => state.gns3.servers;
export const selectCurrentServer = (state) => state.gns3.currentServer;
export const selectProjects = (state) => state.gns3.projects;
export const selectCurrentProject = (state) => state.gns3.currentProject;
export const selectNodes = (state) => state.gns3.nodes;
export const selectLinks = (state) => state.gns3.links;
export const selectTemplates = (state) => state.gns3.templates;
export const selectSnapshots = (state) => state.gns3.snapshots;
export const selectGNS3Loading = (state) => state.gns3.loading;
export const selectGNS3Error = (state) => state.gns3.error;
export const selectPendingActions = (state) => state.gns3.pendingActions;
export const selectGNS3Filters = (state) => state.gns3.filters;
export const selectGNS3Sorting = (state) => state.gns3.sorting;

// Sélecteurs composés
export const selectServerById = (serverId) => (state) =>
  state.gns3.servers.find(server => server.id === serverId);

export const selectProjectById = (projectId) => (state) =>
  state.gns3.projects.find(project => project.id === projectId);

export const selectNodeById = (nodeId) => (state) =>
  state.gns3.nodes.find(node => node.id === nodeId);

export const selectActiveServers = (state) =>
  state.gns3.servers.filter(server => server.is_active);

export const selectOpenedProjects = (state) =>
  state.gns3.projects.filter(project => project.status === 'opened');

export const selectRunningNodes = (state) =>
  state.gns3.nodes.filter(node => node.status === 'started');

export const selectNodesByType = (nodeType) => (state) =>
  state.gns3.nodes.filter(node => node.node_type === nodeType);

export const selectIsGNS3Loading = (state) =>
  Object.values(state.gns3.loading || {}).some(loading => loading);

export const selectGNS3Stats = (state) => ({
  totalServers: state.gns3.servers.length,
  activeServers: state.gns3.servers.filter(s => s.is_active).length,
  totalProjects: state.gns3.projects.length,
  openedProjects: state.gns3.projects.filter(p => p.status === 'opened').length,
  totalNodes: state.gns3.nodes.length,
  runningNodes: state.gns3.nodes.filter(n => n.status === 'started').length,
  totalSnapshots: state.gns3.snapshots.length
});

export default gns3Slice.reducer;