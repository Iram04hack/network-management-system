/**
 * Tests d'intégration du store Redux avec les 4 modules
 * Vérification du fonctionnement des slices et de leur intégration
 */

import { describe, test, expect, beforeEach } from 'vitest';
import { configureStore } from '@reduxjs/toolkit';

// Import des slices
import apiClientsSlice, {
  fetchApiClients,
  testApiClient,
  updateApiClientConfig,
  selectApiClients,
  selectCurrentClient,
  selectActiveClients
} from '../slices/apiClientsSlice';

import apiViewsSlice, {
  fetchDashboardOverview,
  performGlobalSearch,
  startTopologyDiscovery,
  selectDashboard,
  selectSearchResults
} from '../slices/apiViewsSlice';

import dashboardSlice, {
  fetchUserConfig,
  createCustomDashboard,
  createWidget,
  selectUserConfig,
  selectCustomDashboards,
  selectActiveWidgets
} from '../slices/dashboardSlice';

import gns3Slice, {
  fetchServers,
  createProject,
  startProject,
  selectServers,
  selectOpenedProjects,
  selectGNS3Stats
} from '../slices/gns3Slice';

// Configuration du store de test
const createTestStore = (preloadedState = {}) => {
  return configureStore({
    reducer: {
      apiClients: apiClientsSlice,
      apiViews: apiViewsSlice,
      dashboard: dashboardSlice,
      gns3: gns3Slice,
    },
    preloadedState,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
        immutableCheck: false,
      }),
  });
};

describe('Tests d\'intégration du store Redux', () => {

  /**
   * ===========================================
   * TESTS DE CONFIGURATION DU STORE
   * ===========================================
   */
  describe('Configuration du store', () => {
    
    test('devrait créer le store avec tous les slices', () => {
      const store = createTestStore();
      const state = store.getState();

      expect(state).toHaveProperty('apiClients');
      expect(state).toHaveProperty('apiViews');
      expect(state).toHaveProperty('dashboard');
      expect(state).toHaveProperty('gns3');
    });

    test('devrait avoir les états initiaux corrects', () => {
      const store = createTestStore();
      const state = store.getState();

      // Api Clients
      expect(state.apiClients.items).toEqual([]);
      expect(state.apiClients.loading.fetch).toBe(false);
      expect(state.apiClients.error).toBeNull();

      // Api Views
      expect(state.apiViews.dashboard).toBeNull();
      expect(state.apiViews.searchResults).toBeNull();
      expect(state.apiViews.loading.dashboard).toBe(false);

      // Dashboard
      expect(state.dashboard.customDashboards).toEqual([]);
      expect(state.dashboard.widgets).toEqual([]);
      expect(state.dashboard.loading.dashboard).toBe(false);

      // GNS3
      expect(state.gns3.servers).toEqual([]);
      expect(state.gns3.projects).toEqual([]);
      expect(state.gns3.loading.servers).toBe(false);
    });

    test('devrait gérer le state préchargé', () => {
      const preloadedState = {
        apiClients: {
          items: [{ id: 1, name: 'Test Client' }],
          loading: { fetch: false },
          error: null
        }
      };

      const store = createTestStore(preloadedState);
      const state = store.getState();

      expect(state.apiClients.items).toHaveLength(1);
      expect(state.apiClients.items[0].name).toBe('Test Client');
    });
  });

  /**
   * ===========================================
   * TESTS DES ACTIONS API CLIENTS
   * ===========================================
   */
  describe('Actions API Clients', () => {
    
    test('devrait gérer fetchApiClients correctement', () => {
      const store = createTestStore();

      // Pending
      store.dispatch({
        type: fetchApiClients.pending.type,
        meta: { requestId: 'test' }
      });

      let state = store.getState();
      expect(state.apiClients.loading.fetch).toBe(true);
      expect(state.apiClients.error).toBeNull();

      // Fulfilled
      const mockClients = [
        { id: 1, name: 'GNS3 Client', client_type: 'gns3', is_active: true },
        { id: 2, name: 'SNMP Client', client_type: 'snmp', is_active: false }
      ];

      store.dispatch({
        type: fetchApiClients.fulfilled.type,
        payload: {
          clients: mockClients,
          metadata: { totalClients: 2 }
        }
      });

      state = store.getState();
      expect(state.apiClients.loading.fetch).toBe(false);
      expect(state.apiClients.items).toEqual(mockClients);
      expect(state.apiClients.lastFetch).toBeDefined();
    });

    test('devrait gérer testApiClient et mettre à jour le statut', () => {
      const store = createTestStore({
        apiClients: {
          items: [{ id: 1, name: 'Test Client', test_passed: false }],
          loading: { test: false },
          error: null
        }
      });

      store.dispatch({
        type: testApiClient.fulfilled.type,
        payload: {
          clientId: 1,
          testResult: { success: true },
          metadata: { testPassed: true, timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      const state = store.getState();
      expect(state.apiClients.items[0].test_passed).toBe(true);
      expect(state.apiClients.items[0].last_test_time).toBe('2025-01-01T12:00:00Z');
    });
  });

  /**
   * ===========================================
   * TESTS DES ACTIONS API VIEWS
   * ===========================================
   */
  describe('Actions API Views', () => {
    
    test('devrait gérer fetchDashboardOverview', () => {
      const store = createTestStore();

      const mockDashboard = {
        devices: { total: 25, online: 22 },
        alerts: { total: 8, critical: 2 },
        system: { overall_status: 'healthy' }
      };

      store.dispatch({
        type: fetchDashboardOverview.fulfilled.type,
        payload: {
          data: mockDashboard,
          metadata: { timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      const state = store.getState();
      expect(state.apiViews.dashboard).toEqual(mockDashboard);
      expect(state.apiViews.lastFetch.dashboard).toBeDefined();
    });

    test('devrait gérer la recherche globale', () => {
      const store = createTestStore();

      const mockResults = {
        total: 10,
        results: [
          { type: 'device', name: 'Switch-01' },
          { type: 'alert', severity: 'warning' }
        ]
      };

      store.dispatch({
        type: performGlobalSearch.fulfilled.type,
        payload: {
          query: 'switch',
          results: mockResults,
          metadata: { resultsCount: 10 }
        }
      });

      const state = store.getState();
      expect(state.apiViews.searchResults).toEqual(mockResults);
      expect(state.apiViews.lastSearchQuery).toBe('switch');
      expect(state.apiViews.searchHistory).toHaveLength(1);
    });

    test('devrait gérer la découverte de topologie', () => {
      const store = createTestStore();

      // Démarrer la découverte
      store.dispatch({
        type: startTopologyDiscovery.fulfilled.type,
        payload: {
          discoveryId: 'disc_123',
          data: { status: 'started' },
          metadata: { networkId: 'net_001', timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      let state = store.getState();
      expect(state.apiViews.discoveryStatus.discoveryId).toBe('disc_123');
      expect(state.apiViews.activeDiscoveries).toHaveLength(1);

      // Mettre à jour le statut
      store.dispatch({
        type: 'apiViews/updateDiscoveryStatus',
        payload: {
          discoveryId: 'disc_123',
          status: { progress: 50, devices_found: 5 }
        }
      });

      state = store.getState();
      expect(state.apiViews.discoveryStatus.progress).toBe(50);
    });
  });

  /**
   * ===========================================
   * TESTS DES ACTIONS DASHBOARD
   * ===========================================
   */
  describe('Actions Dashboard', () => {
    
    test('devrait gérer la configuration utilisateur', () => {
      const store = createTestStore();

      const mockConfig = {
        id: 1,
        theme: 'dark',
        layout: 'grid',
        refresh_interval: 30
      };

      store.dispatch({
        type: fetchUserConfig.fulfilled.type,
        payload: {
          config: mockConfig,
          metadata: { timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      const state = store.getState();
      expect(state.dashboard.userConfig).toEqual(mockConfig);
      expect(state.dashboard.layout.theme).toBe('dark');
      expect(state.dashboard.layout.layoutType).toBe('grid');
    });

    test('devrait gérer les dashboards personnalisés', () => {
      const store = createTestStore();

      // Créer un dashboard
      const mockDashboard = {
        id: 'dash_123',
        name: 'Mon Dashboard',
        layout: { widgets: [] },
        is_default: false
      };

      store.dispatch({
        type: createCustomDashboard.fulfilled.type,
        payload: {
          dashboard: mockDashboard,
          dashboardId: 'dash_123',
          metadata: { timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      let state = store.getState();
      expect(state.dashboard.customDashboards).toHaveLength(1);
      expect(state.dashboard.customDashboards[0].name).toBe('Mon Dashboard');

      // Supprimer un dashboard
      store.dispatch({
        type: 'dashboard/deleteCustomDashboard/fulfilled',
        payload: {
          dashboardId: 'dash_123',
          metadata: { timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      state = store.getState();
      expect(state.dashboard.customDashboards).toHaveLength(0);
    });

    test('devrait gérer les widgets', () => {
      const store = createTestStore();

      // Créer un widget
      const mockWidget = {
        id: 'widget_123',
        widget_type: 'system_health',
        position_x: 0,
        position_y: 0,
        is_active: true
      };

      store.dispatch({
        type: createWidget.fulfilled.type,
        payload: {
          widget: mockWidget,
          widgetId: 'widget_123',
          metadata: { timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      let state = store.getState();
      expect(state.dashboard.widgets).toHaveLength(1);
      expect(state.dashboard.widgets[0].widget_type).toBe('system_health');

      // Basculer l'état actif
      store.dispatch({
        type: 'dashboard/toggleWidgetActive',
        payload: 'widget_123'
      });

      state = store.getState();
      expect(state.dashboard.widgets[0].is_active).toBe(false);
    });

    test('devrait gérer les mises à jour temps réel', () => {
      const store = createTestStore({
        dashboard: {
          dashboardData: { devices: { total: 20 } },
          networkOverview: { devices_count: 15 }
        }
      });

      // Mise à jour temps réel dashboard
      store.dispatch({
        type: 'dashboard/updateRealTimeData',
        payload: {
          type: 'dashboard_update',
          data: { devices: { total: 25, new_devices: 5 } }
        }
      });

      let state = store.getState();
      expect(state.dashboard.dashboardData.devices.total).toBe(25);
      expect(state.dashboard.dashboardData.devices.new_devices).toBe(5);
      expect(state.dashboard.lastRealTimeUpdate).toBeDefined();

      // Mise à jour réseau
      store.dispatch({
        type: 'dashboard/updateRealTimeData',
        payload: {
          type: 'network_update',
          data: { devices_count: 20, switches_count: 8 }
        }
      });

      state = store.getState();
      expect(state.dashboard.networkOverview.devices_count).toBe(20);
      expect(state.dashboard.networkOverview.switches_count).toBe(8);
    });
  });

  /**
   * ===========================================
   * TESTS DES ACTIONS GNS3
   * ===========================================
   */
  describe('Actions GNS3', () => {
    
    test('devrait gérer les serveurs GNS3', () => {
      const store = createTestStore();

      const mockServers = [
        { id: 1, name: 'Server 1', host: 'localhost', is_active: true },
        { id: 2, name: 'Server 2', host: '192.168.1.100', is_active: false }
      ];

      store.dispatch({
        type: fetchServers.fulfilled.type,
        payload: {
          servers: mockServers,
          metadata: { totalServers: 2, activeServers: 1 }
        }
      });

      const state = store.getState();
      expect(state.gns3.servers).toEqual(mockServers);
      expect(state.gns3.lastFetch.servers).toBeDefined();
    });

    test('devrait gérer les projets et leurs actions', () => {
      const store = createTestStore();

      // Créer un projet
      const mockProject = {
        id: 'proj_123',
        name: 'Test Project',
        status: 'closed',
        server_id: 1
      };

      store.dispatch({
        type: createProject.fulfilled.type,
        payload: {
          project: mockProject,
          projectId: 'proj_123',
          metadata: { timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      let state = store.getState();
      expect(state.gns3.projects).toHaveLength(1);
      expect(state.gns3.projects[0].status).toBe('closed');

      // Démarrer le projet
      store.dispatch({
        type: startProject.pending.type,
        meta: { arg: 'proj_123' }
      });

      state = store.getState();
      expect(state.gns3.pendingActions.startingProjects).toContain('proj_123');

      store.dispatch({
        type: startProject.fulfilled.type,
        payload: {
          projectId: 'proj_123',
          action: 'start',
          newStatus: 'opened',
          metadata: { timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      state = store.getState();
      expect(state.gns3.projects[0].status).toBe('opened');
      expect(state.gns3.pendingActions.startingProjects).not.toContain('proj_123');
    });

    test('devrait gérer les actions en attente correctement', () => {
      const store = createTestStore();

      // Ajouter une action en attente
      store.dispatch({
        type: 'gns3/addPendingAction',
        payload: { type: 'startingNodes', id: 'node_123' }
      });

      let state = store.getState();
      expect(state.gns3.pendingActions.startingNodes).toContain('node_123');

      // Supprimer l'action en attente
      store.dispatch({
        type: 'gns3/removePendingAction',
        payload: { type: 'startingNodes', id: 'node_123' }
      });

      state = store.getState();
      expect(state.gns3.pendingActions.startingNodes).not.toContain('node_123');

      // Nettoyer toutes les actions en attente
      store.dispatch({
        type: 'gns3/addPendingAction',
        payload: { type: 'startingProjects', id: 'proj_123' }
      });

      store.dispatch({
        type: 'gns3/clearPendingActions'
      });

      state = store.getState();
      expect(state.gns3.pendingActions.startingProjects).toHaveLength(0);
    });
  });

  /**
   * ===========================================
   * TESTS DES SÉLECTEURS
   * ===========================================
   */
  describe('Tests des sélecteurs', () => {
    
    test('devrait sélectionner les données API Clients correctement', () => {
      const mockState = {
        apiClients: {
          items: [
            { id: 1, client_type: 'gns3', is_active: true, status: 'healthy' },
            { id: 2, client_type: 'snmp', is_active: false, status: 'unhealthy' }
          ],
          currentClient: { id: 1, name: 'Current Client' }
        }
      };

      expect(selectApiClients(mockState)).toHaveLength(2);
      expect(selectCurrentClient(mockState).id).toBe(1);
      expect(selectActiveClients(mockState)).toHaveLength(1);
    });

    test('devrait sélectionner les données Dashboard correctement', () => {
      const mockState = {
        dashboard: {
          userConfig: { theme: 'dark', layout: 'grid' },
          customDashboards: [
            { id: 1, name: 'Dashboard 1', is_default: true },
            { id: 2, name: 'Dashboard 2', is_default: false }
          ],
          widgets: [
            { id: 1, widget_type: 'system_health', is_active: true },
            { id: 2, widget_type: 'alerts', is_active: false }
          ]
        }
      };

      expect(selectUserConfig(mockState).theme).toBe('dark');
      expect(selectCustomDashboards(mockState)).toHaveLength(2);
      expect(selectActiveWidgets(mockState)).toHaveLength(1);
    });

    test('devrait sélectionner les données GNS3 correctement', () => {
      const mockState = {
        gns3: {
          servers: [
            { id: 1, is_active: true },
            { id: 2, is_active: false }
          ],
          projects: [
            { id: 'p1', status: 'opened' },
            { id: 'p2', status: 'closed' }
          ],
          nodes: [
            { id: 'n1', status: 'started' },
            { id: 'n2', status: 'stopped' }
          ]
        }
      };

      expect(selectServers(mockState)).toHaveLength(2);
      expect(selectOpenedProjects(mockState)).toHaveLength(1);
      
      const stats = selectGNS3Stats(mockState);
      expect(stats.totalServers).toBe(2);
      expect(stats.activeServers).toBe(1);
      expect(stats.openedProjects).toBe(1);
    });
  });

  /**
   * ===========================================
   * TESTS DE GESTION DES ERREURS
   * ===========================================
   */
  describe('Gestion des erreurs', () => {
    
    test('devrait gérer les erreurs dans tous les slices', () => {
      const store = createTestStore();
      const errorPayload = {
        type: 'NETWORK_ERROR',
        message: 'Connection failed',
        status: 500
      };

      // Erreur API Clients
      store.dispatch({
        type: fetchApiClients.rejected.type,
        payload: errorPayload
      });

      let state = store.getState();
      expect(state.apiClients.error).toEqual(errorPayload);
      expect(state.apiClients.lastError).toEqual(errorPayload);
      expect(state.apiClients.loading.fetch).toBe(false);

      // Nettoyer l'erreur
      store.dispatch({
        type: 'apiClients/clearError'
      });

      state = store.getState();
      expect(state.apiClients.error).toBeNull();
    });

    test('devrait préserver l\'état lors d\'erreurs', () => {
      const initialData = [{ id: 1, name: 'Test Client' }];
      const store = createTestStore({
        apiClients: {
          items: initialData,
          loading: { fetch: false },
          error: null
        }
      });

      // Erreur lors de la mise à jour
      store.dispatch({
        type: updateApiClientConfig.rejected.type,
        payload: { type: 'UPDATE_ERROR', message: 'Update failed' }
      });

      const state = store.getState();
      expect(state.apiClients.items).toEqual(initialData); // Données préservées
      expect(state.apiClients.error.type).toBe('UPDATE_ERROR');
    });
  });

  /**
   * ===========================================
   * TESTS DE COHÉRENCE ENTRE SLICES
   * ===========================================
   */
  describe('Cohérence entre slices', () => {
    
    test('devrait maintenir la cohérence entre les modules liés', () => {
      const store = createTestStore();

      // Données GNS3 qui impactent le dashboard
      const gns3Data = {
        servers: [{ id: 1, name: 'GNS3 Server', is_active: true }],
        projects: [{ id: 'p1', name: 'Project 1', status: 'opened' }]
      };

      store.dispatch({
        type: fetchServers.fulfilled.type,
        payload: { servers: gns3Data.servers, metadata: {} }
      });

      // Dashboard qui utilise les données GNS3
      const dashboardData = {
        gns3_servers: 1,
        gns3_projects: 1,
        gns3_status: 'healthy'
      };

      store.dispatch({
        type: fetchDashboardOverview.fulfilled.type,
        payload: { data: dashboardData, metadata: {} }
      });

      const state = store.getState();
      expect(state.gns3.servers).toHaveLength(1);
      expect(state.apiViews.dashboard.gns3_servers).toBe(1);
    });

    test('devrait gérer les relations entre client API et services', () => {
      const store = createTestStore();

      // Client GNS3 dans api_clients
      const gns3Client = {
        id: 1,
        name: 'GNS3 API Client',
        client_type: 'gns3',
        host: 'localhost',
        port: 3080,
        is_active: true,
        status: 'healthy'
      };

      store.dispatch({
        type: fetchApiClients.fulfilled.type,
        payload: { clients: [gns3Client], metadata: {} }
      });

      // Serveur GNS3 correspondant
      const gns3Server = {
        id: 1,
        name: 'GNS3 Server',
        host: 'localhost',
        port: 3080,
        is_active: true
      };

      store.dispatch({
        type: fetchServers.fulfilled.type,
        payload: { servers: [gns3Server], metadata: {} }
      });

      const state = store.getState();
      
      // Vérifier la cohérence des données
      const client = state.apiClients.items[0];
      const server = state.gns3.servers[0];
      
      expect(client.host).toBe(server.host);
      expect(client.port).toBe(server.port);
    });
  });

  /**
   * ===========================================
   * TESTS DE PERFORMANCE DU STORE
   * ===========================================
   */
  describe('Performance du store', () => {
    
    test('devrait gérer efficacement de grandes quantités de données', () => {
      const store = createTestStore();

      // Générer beaucoup de données
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `Item ${i}`,
        status: i % 2 === 0 ? 'active' : 'inactive',
        metadata: { created: new Date().toISOString() }
      }));

      const startTime = performance.now();

      store.dispatch({
        type: fetchApiClients.fulfilled.type,
        payload: { clients: largeDataset, metadata: {} }
      });

      const endTime = performance.now();
      const state = store.getState();

      expect(endTime - startTime).toBeLessThan(100); // Moins de 100ms
      expect(state.apiClients.items).toHaveLength(1000);
    });

    test('devrait optimiser les mises à jour partielles', () => {
      const initialClients = Array.from({ length: 100 }, (_, i) => ({
        id: i,
        name: `Client ${i}`,
        test_passed: false
      }));

      const store = createTestStore({
        apiClients: {
          items: initialClients,
          loading: { test: false },
          error: null
        }
      });

      const startTime = performance.now();

      // Mettre à jour un seul client
      store.dispatch({
        type: testApiClient.fulfilled.type,
        payload: {
          clientId: 50,
          testResult: { success: true },
          metadata: { testPassed: true, timestamp: '2025-01-01T12:00:00Z' }
        }
      });

      const endTime = performance.now();
      const state = store.getState();

      expect(endTime - startTime).toBeLessThan(10); // Très rapide
      expect(state.apiClients.items[50].test_passed).toBe(true);
      expect(state.apiClients.items[49].test_passed).toBe(false); // Autres inchangés
    });
  });
});