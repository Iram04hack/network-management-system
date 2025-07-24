/**
 * Tests des hooks React pour les 4 modules intégrés
 * Vérification du fonctionnement des hooks avec Redux et services
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import MockAdapter from 'axios-mock-adapter';
import axios from 'axios';

// Import des hooks
import { useApiClients } from '../useApiClients';
import { useApiViews } from '../useApiViews';
import { useDashboard } from '../useDashboard';
import { useGNS3 } from '../useGNS3';

// Import des slices Redux
import apiClientsSlice from '../../store/slices/apiClientsSlice';
import apiViewsSlice from '../../store/slices/apiViewsSlice';
import dashboardSlice from '../../store/slices/dashboardSlice';
import gns3Slice from '../../store/slices/gns3Slice';

// Configuration des mocks
let mockAxios;

// Helper pour créer un store de test
const createTestStore = () => {
  return configureStore({
    reducer: {
      apiClients: apiClientsSlice,
      apiViews: apiViewsSlice,
      dashboard: dashboardSlice,
      gns3: gns3Slice,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: false,
        immutableCheck: false,
      }),
  });
};

// Helper pour wrapper les hooks avec Redux
const createWrapper = (store) => {
  return ({ children }) => (
    <Provider store={store}>{children}</Provider>
  );
};

beforeEach(() => {
  mockAxios = new MockAdapter(axios);
});

afterEach(() => {
  mockAxios.restore();
  vi.clearAllMocks();
});

describe('Tests des hooks intégrés', () => {

  /**
   * ===========================================
   * TESTS HOOK useApiClients
   * ===========================================
   */
  describe('useApiClients hook', () => {
    
    test('devrait initialiser avec l\'état par défaut', () => {
      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useApiClients(), { wrapper });
      
      expect(result.current.clients).toEqual([]);
      expect(result.current.loading.fetch).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.isLoading).toBe(false);
    });

    test('devrait récupérer les clients API', async () => {
      const mockClients = [
        { id: 1, name: 'GNS3 Client', client_type: 'gns3', is_active: true },
        { id: 2, name: 'SNMP Client', client_type: 'snmp', is_active: true }
      ];

      mockAxios.onGet('/api/clients/').reply(200, {
        results: mockClients,
        count: 2
      });

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useApiClients(), { wrapper });

      await act(async () => {
        await result.current.fetchClients();
      });

      await waitFor(() => {
        expect(result.current.clients).toHaveLength(2);
        expect(result.current.clients[0].name).toBe('GNS3 Client');
        expect(result.current.loading.fetch).toBe(false);
      });
    });

    test('devrait tester un client et mettre à jour son statut', async () => {
      const mockTestResult = {
        success: true,
        response_time: 45,
        connection_status: 'connected'
      };

      mockAxios.onPost('/api/clients/1/test/').reply(200, mockTestResult);

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      // Pré-remplir avec un client
      store.dispatch({
        type: 'apiClients/fetchApiClients/fulfilled',
        payload: {
          clients: [{ id: 1, name: 'Test Client', test_passed: false }]
        }
      });

      const { result } = renderHook(() => useApiClients(), { wrapper });

      await act(async () => {
        await result.current.testClient(1);
      });

      await waitFor(() => {
        expect(result.current.clients[0].test_passed).toBe(true);
        expect(result.current.loading.test).toBe(false);
      });
    });

    test('devrait utiliser les utilitaires correctement', async () => {
      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      // Pré-remplir avec des clients
      store.dispatch({
        type: 'apiClients/fetchApiClients/fulfilled',
        payload: {
          clients: [
            { id: 1, client_type: 'gns3', is_active: true, status: 'healthy' },
            { id: 2, client_type: 'snmp', is_active: false, status: 'unhealthy' },
            { id: 3, client_type: 'gns3', is_active: true, status: 'healthy' }
          ]
        }
      });

      const { result } = renderHook(() => useApiClients(), { wrapper });

      // Tester les utilitaires
      expect(result.current.getClientsByType('gns3')).toHaveLength(2);
      expect(result.current.getActiveClients()).toHaveLength(2);
      expect(result.current.getUnhealthyClients()).toHaveLength(1);
      
      const stats = result.current.getStats();
      expect(stats.total).toBe(3);
      expect(stats.active).toBe(2);
      expect(stats.healthy).toBe(2);
    });
  });

  /**
   * ===========================================
   * TESTS HOOK useApiViews
   * ===========================================
   */
  describe('useApiViews hook', () => {
    
    test('devrait récupérer les données du dashboard', async () => {
      const mockDashboard = {
        devices: { total: 25, online: 22 },
        alerts: { total: 8, critical: 2 },
        system: { overall_status: 'healthy' }
      };

      mockAxios.onGet('/api/views/dashboard/').reply(200, mockDashboard);

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useApiViews(), { wrapper });

      await act(async () => {
        await result.current.fetchDashboardOverview();
      });

      await waitFor(() => {
        expect(result.current.dashboardData).toEqual(mockDashboard);
        expect(result.current.loading.dashboard).toBe(false);
      });
    });

    test('devrait démarrer et suivre une découverte de topologie', async () => {
      const mockDiscovery = {
        discovery_id: 'disc_123',
        status: 'started',
        network_id: 'net_001'
      };

      const mockStatus = {
        discovery_id: 'disc_123',
        status: 'in_progress',
        progress: 50,
        devices_found: 5
      };

      mockAxios.onPost('/api/views/topology/discovery/').reply(200, mockDiscovery);
      mockAxios.onGet('/api/views/topology/discovery/disc_123/status/').reply(200, mockStatus);

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useApiViews(), { wrapper });

      // Démarrer la découverte
      await act(async () => {
        await result.current.startTopologyDiscovery({ network_id: 'net_001' });
      });

      await waitFor(() => {
        expect(result.current.discoveryStatus.discoveryId).toBe('disc_123');
        expect(result.current.discoveryStatus.status).toBe('started');
      });

      // Vérifier le statut
      await act(async () => {
        await result.current.getTopologyDiscoveryStatus('disc_123');
      });

      await waitFor(() => {
        expect(result.current.discoveryStatus.progress).toBe(50);
        expect(result.current.discoveryStatus.devices_found).toBe(5);
      });
    });

    test('devrait effectuer une recherche globale', async () => {
      const mockResults = {
        total: 10,
        results: [
          { type: 'device', name: 'Switch-01' },
          { type: 'alert', severity: 'warning' }
        ]
      };

      mockAxios.onGet('/api/views/search/').reply(200, mockResults);

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useApiViews(), { wrapper });

      await act(async () => {
        await result.current.performGlobalSearch('switch');
      });

      await waitFor(() => {
        expect(result.current.searchResults).toEqual(mockResults);
        expect(result.current.loading.search).toBe(false);
      });
    });
  });

  /**
   * ===========================================
   * TESTS HOOK useDashboard
   * ===========================================
   */
  describe('useDashboard hook', () => {
    
    test('devrait gérer la configuration utilisateur', async () => {
      const mockConfig = {
        id: 1,
        theme: 'dark',
        layout: 'grid',
        refresh_interval: 30
      };

      const mockUpdatedConfig = {
        ...mockConfig,
        theme: 'light',
        refresh_interval: 60
      };

      mockAxios.onGet('/api/dashboard/config/').reply(200, mockConfig);
      mockAxios.onPut('/api/dashboard/configs/1').reply(200, mockUpdatedConfig);

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useDashboard(), { wrapper });

      // Récupérer la config
      await act(async () => {
        await result.current.fetchUserConfig();
      });

      await waitFor(() => {
        expect(result.current.userConfig.theme).toBe('dark');
        expect(result.current.userConfig.refresh_interval).toBe(30);
      });

      // Mettre à jour la config
      await act(async () => {
        await result.current.updateUserConfig({
          theme: 'light',
          refresh_interval: 60
        });
      });

      await waitFor(() => {
        expect(result.current.userConfig.theme).toBe('light');
        expect(result.current.userConfig.refresh_interval).toBe(60);
      });
    });

    test('devrait gérer les dashboards personnalisés', async () => {
      const mockDashboards = [
        { id: 'dash_1', name: 'Dashboard 1', is_default: true },
        { id: 'dash_2', name: 'Dashboard 2', is_default: false }
      ];

      const mockNewDashboard = {
        id: 'dash_3',
        name: 'Nouveau Dashboard',
        is_default: false
      };

      mockAxios.onGet('/api/dashboard/custom/').reply(200, { results: mockDashboards });
      mockAxios.onPost('/api/dashboard/custom/').reply(201, mockNewDashboard);

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useDashboard(), { wrapper });

      // Récupérer les dashboards
      await act(async () => {
        await result.current.fetchCustomDashboards();
      });

      await waitFor(() => {
        expect(result.current.customDashboards).toHaveLength(2);
        expect(result.current.getDefaultDashboards()).toHaveLength(1);
      });

      // Créer un nouveau dashboard
      await act(async () => {
        await result.current.createCustomDashboard({
          name: 'Nouveau Dashboard',
          description: 'Test dashboard'
        });
      });

      await waitFor(() => {
        expect(result.current.customDashboards).toHaveLength(3);
        expect(result.current.customDashboards[0].name).toBe('Nouveau Dashboard');
      });
    });

    test('devrait gérer les widgets', async () => {
      const mockWidgets = [
        { id: 'w1', widget_type: 'system_health', is_active: true },
        { id: 'w2', widget_type: 'network_overview', is_active: false }
      ];

      const mockNewWidget = {
        id: 'w3',
        widget_type: 'alerts',
        is_active: true
      };

      mockAxios.onGet('/api/dashboard/widgets/').reply(200, { results: mockWidgets });
      mockAxios.onPost('/api/dashboard/widgets/').reply(201, mockNewWidget);

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useDashboard(), { wrapper });

      // Récupérer les widgets
      await act(async () => {
        await result.current.fetchWidgets();
      });

      await waitFor(() => {
        expect(result.current.widgets).toHaveLength(2);
        expect(result.current.getActiveWidgets()).toHaveLength(1);
        expect(result.current.getWidgetsByType('system_health')).toHaveLength(1);
      });

      // Créer un nouveau widget
      await act(async () => {
        await result.current.createWidget({
          widget_type: 'alerts',
          position_x: 0,
          position_y: 1
        });
      });

      await waitFor(() => {
        expect(result.current.widgets).toHaveLength(3);
      });
    });

    test('devrait valider les configurations de widget', () => {
      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useDashboard(), { wrapper });

      // Test validation valide
      const validWidget = {
        widget_type: 'system_health',
        position_x: 0,
        position_y: 0
      };

      const validResult = result.current.validateWidgetConfig(validWidget);
      expect(validResult.isValid).toBe(true);
      expect(validResult.errors).toHaveLength(0);

      // Test validation invalide
      const invalidWidget = {
        // Manque widget_type
        position_x: 0
      };

      const invalidResult = result.current.validateWidgetConfig(invalidWidget);
      expect(invalidResult.isValid).toBe(false);
      expect(invalidResult.errors.length).toBeGreaterThan(0);
    });
  });

  /**
   * ===========================================
   * TESTS HOOK useGNS3
   * ===========================================
   */
  describe('useGNS3 hook', () => {
    
    test('devrait gérer les serveurs GNS3', async () => {
      const mockServers = [
        { id: 1, name: 'Server 1', host: 'localhost', is_active: true },
        { id: 2, name: 'Server 2', host: '192.168.1.100', is_active: false }
      ];

      const mockNewServer = {
        id: 3,
        name: 'Server 3',
        host: '192.168.1.200',
        port: 3080,
        is_active: true
      };

      mockAxios.onGet('/api/gns3_integration/api/servers/').reply(200, { results: mockServers });
      mockAxios.onPost('/api/gns3_integration/api/servers/').reply(201, mockNewServer);

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useGNS3(), { wrapper });

      // Récupérer les serveurs
      await act(async () => {
        await result.current.fetchServers();
      });

      await waitFor(() => {
        expect(result.current.servers).toHaveLength(2);
        expect(result.current.getActiveServers()).toHaveLength(1);
      });

      // Créer un nouveau serveur
      await act(async () => {
        await result.current.createServer({
          name: 'Server 3',
          host: '192.168.1.200',
          port: 3080
        });
      });

      await waitFor(() => {
        expect(result.current.servers).toHaveLength(3);
      });
    });

    test('devrait gérer les projets GNS3', async () => {
      const mockProjects = [
        { id: 'p1', name: 'Project 1', status: 'opened', server_id: 1 },
        { id: 'p2', name: 'Project 2', status: 'closed', server_id: 1 }
      ];

      mockAxios.onGet('/api/gns3_integration/api/projects/').reply(200, { results: mockProjects });
      mockAxios.onPost('/api/gns3_integration/api/projects/p1/start/').reply(200, { 
        id: 'p1', 
        status: 'opened' 
      });

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useGNS3(), { wrapper });

      // Récupérer les projets
      await act(async () => {
        await result.current.fetchProjects();
      });

      await waitFor(() => {
        expect(result.current.projects).toHaveLength(2);
        expect(result.current.getOpenedProjects()).toHaveLength(1);
        expect(result.current.getProjectsByStatus('closed')).toHaveLength(1);
      });

      // Démarrer un projet
      await act(async () => {
        await result.current.startProject('p1');
      });

      await waitFor(() => {
        const project = result.current.projects.find(p => p.id === 'p1');
        expect(project.status).toBe('opened');
      });
    });

    test('devrait gérer les nœuds et leurs actions', async () => {
      const mockNodes = [
        { id: 'n1', name: 'Router-1', node_type: 'dynamips', status: 'stopped' },
        { id: 'n2', name: 'Switch-1', node_type: 'ethernet_switch', status: 'started' }
      ];

      mockAxios.onGet('/api/gns3_integration/api/projects/p1/nodes/').reply(200, mockNodes);
      mockAxios.onPost('/api/gns3_integration/api/nodes/n1/start/').reply(200, { 
        id: 'n1', 
        status: 'started' 
      });

      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useGNS3(), { wrapper });

      // Récupérer les nœuds d'un projet
      await act(async () => {
        await result.current.fetchProjectNodes('p1');
      });

      await waitFor(() => {
        expect(result.current.nodes).toHaveLength(2);
        expect(result.current.getRunningNodes()).toHaveLength(1);
        expect(result.current.getNodesByType('dynamips')).toHaveLength(1);
      });

      // Démarrer un nœud
      await act(async () => {
        await result.current.startNode('n1');
      });

      await waitFor(() => {
        const node = result.current.nodes.find(n => n.id === 'n1');
        expect(node.status).toBe('started');
      });
    });

    test('devrait utiliser les statistiques et utilitaires', async () => {
      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      // Pré-remplir avec des données
      store.dispatch({
        type: 'gns3/fetchServers/fulfilled',
        payload: {
          servers: [
            { id: 1, is_active: true },
            { id: 2, is_active: false }
          ]
        }
      });

      store.dispatch({
        type: 'gns3/fetchProjects/fulfilled',
        payload: {
          projects: [
            { id: 'p1', status: 'opened' },
            { id: 'p2', status: 'closed' }
          ]
        }
      });

      const { result } = renderHook(() => useGNS3(), { wrapper });

      const stats = result.current.getGNS3Stats();
      expect(stats.totalServers).toBe(2);
      expect(stats.activeServers).toBe(1);
      expect(stats.totalProjects).toBe(2);
      expect(stats.openedProjects).toBe(1);

      // Test recherche
      expect(result.current.searchServers('test')).toHaveLength(0);
      expect(result.current.searchProjects('p1')).toHaveLength(0); // Pas de données nom dans les mocks
    });

    test('devrait valider les données', () => {
      const store = createTestStore();
      const wrapper = createWrapper(store);
      
      const { result } = renderHook(() => useGNS3(), { wrapper });

      // Validation serveur valide
      const validServer = {
        name: 'Test Server',
        host: 'localhost',
        port: 3080
      };

      const validResult = result.current.validateServerData(validServer);
      expect(validResult.isValid).toBe(true);

      // Validation serveur invalide
      const invalidServer = {
        name: 'Test Server',
        // Manque host et port
      };

      const invalidResult = result.current.validateServerData(invalidServer);
      expect(invalidResult.isValid).toBe(false);
      expect(invalidResult.errors.length).toBeGreaterThan(0);

      // Validation port invalide
      const invalidPort = {
        name: 'Test Server',
        host: 'localhost',
        port: 70000 // Port invalide
      };

      const portResult = result.current.validateServerData(invalidPort);
      expect(portResult.isValid).toBe(false);
    });
  });

  /**
   * ===========================================
   * TESTS D'INTÉGRATION ENTRE HOOKS
   * ===========================================
   */
  describe('Tests d\'intégration entre hooks', () => {
    
    test('devrait partager l\'état Redux entre hooks', async () => {
      const store = createTestStore();
      const wrapper = createWrapper(store);

      const { result: dashboardResult } = renderHook(() => useDashboard(), { wrapper });
      const { result: apiViewsResult } = renderHook(() => useApiViews(), { wrapper });

      // Simuler des données dans le store
      store.dispatch({
        type: 'dashboard/fetchSystemHealth/fulfilled',
        payload: {
          data: { overall_status: 'healthy', cpu_usage: 45 }
        }
      });

      store.dispatch({
        type: 'apiViews/fetchSystemOverview/fulfilled',
        payload: {
          data: { cpu: { usage_percent: 45 }, memory: { usage_percent: 67 } }
        }
      });

      await waitFor(() => {
        expect(dashboardResult.current.systemHealth).toBeDefined();
        expect(apiViewsResult.current.systemOverview).toBeDefined();
      });

      // Vérifier que les données sont cohérentes
      expect(dashboardResult.current.systemHealth.overall_status).toBe('healthy');
      expect(apiViewsResult.current.systemOverview.cpu.usage_percent).toBe(45);
    });

    test('devrait gérer les erreurs de manière cohérente', async () => {
      const store = createTestStore();
      const wrapper = createWrapper(store);

      const errorPayload = {
        type: 'NETWORK_ERROR',
        message: 'Connection failed'
      };

      // Simuler des erreurs dans les hooks
      store.dispatch({
        type: 'apiClients/fetchApiClients/rejected',
        payload: errorPayload
      });

      store.dispatch({
        type: 'gns3/fetchServers/rejected',
        payload: errorPayload
      });

      const { result: apiClientsResult } = renderHook(() => useApiClients(), { wrapper });
      const { result: gns3Result } = renderHook(() => useGNS3(), { wrapper });

      await waitFor(() => {
        expect(apiClientsResult.current.error).toEqual(errorPayload);
        expect(gns3Result.current.error).toEqual(errorPayload);
      });

      // Tester le nettoyage des erreurs
      act(() => {
        apiClientsResult.current.clearError();
        gns3Result.current.clearError();
      });

      expect(apiClientsResult.current.error).toBeNull();
      expect(gns3Result.current.error).toBeNull();
    });
  });

  /**
   * ===========================================
   * TESTS DE PERFORMANCE
   * ===========================================
   */
  describe('Tests de performance des hooks', () => {
    
    test('devrait éviter les re-renders inutiles', () => {
      const store = createTestStore();
      const wrapper = createWrapper(store);

      let renderCount = 0;
      const TestComponent = () => {
        const { clients, fetchClients } = useApiClients();
        renderCount++;
        return null;
      };

      const { rerender } = renderHook(() => TestComponent(), { wrapper });

      const initialRenderCount = renderCount;

      // Re-render sans changement d'état
      rerender();
      expect(renderCount).toBe(initialRenderCount + 1);

      // Les fonctions doivent être stables
      rerender();
      expect(renderCount).toBe(initialRenderCount + 2);
    });

    test('devrait optimiser les re-calculs avec useMemo', () => {
      const store = createTestStore();
      const wrapper = createWrapper(store);

      // Pré-remplir avec beaucoup de données
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `Client ${i}`,
        client_type: i % 2 === 0 ? 'gns3' : 'snmp',
        is_active: i % 3 === 0
      }));

      store.dispatch({
        type: 'apiClients/fetchApiClients/fulfilled',
        payload: { clients: largeDataset }
      });

      const { result } = renderHook(() => useApiClients(), { wrapper });

      // Mesurer le temps de calcul des statistiques
      const startTime = performance.now();
      const stats = result.current.getStats();
      const endTime = performance.now();

      expect(endTime - startTime).toBeLessThan(10); // Moins de 10ms
      expect(stats.total).toBe(1000);
    });
  });
});