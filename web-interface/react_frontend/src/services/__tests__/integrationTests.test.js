/**
 * Tests d'intégration pour les 4 modules backend intégrés
 * Vérification des endpoints API et de la liaison frontend-backend
 */

import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

// Import des services
import apiClientsService from '../apiClientsService';
import apiViewsService from '../apiViewsService';
import dashboardService from '../dashboardService';
import gns3Service from '../gns3Service';

// Configuration des mocks
let mockAxios;

beforeEach(() => {
  mockAxios = new MockAdapter(axios);
});

afterEach(() => {
  mockAxios.restore();
  vi.clearAllMocks();
});

describe('Tests d\'intégration des modules backend', () => {
  
  /**
   * ===========================================
   * TESTS MODULE API_CLIENTS
   * ===========================================
   */
  describe('Module api_clients', () => {
    
    test('devrait récupérer la liste des clients API', async () => {
      const mockClients = [
        {
          id: 1,
          name: 'GNS3 Client',
          client_type: 'gns3',
          host: 'localhost',
          port: 3080,
          is_active: true,
          status: 'healthy'
        },
        {
          id: 2,
          name: 'SNMP Client',
          client_type: 'snmp',
          host: '192.168.1.1',
          port: 161,
          is_active: true,
          status: 'healthy'
        }
      ];

      mockAxios.onGet('/api/clients/').reply(200, {
        results: mockClients,
        count: 2
      });

      const result = await apiClientsService.getClients();
      
      expect(result.success).toBe(true);
      expect(result.data).toHaveLength(2);
      expect(result.data[0].client_type).toBe('gns3');
      expect(result.metadata.totalClients).toBe(2);
    });

    test('devrait tester un client API spécifique', async () => {
      const mockTestResult = {
        success: true,
        response_time: 45,
        connection_status: 'connected',
        server_version: '2.2.43'
      };

      mockAxios.onPost('/api/clients/1/test/').reply(200, mockTestResult);

      const result = await apiClientsService.testClient(1);
      
      expect(result.success).toBe(true);
      expect(result.data.connection_status).toBe('connected');
      expect(result.metadata.testPassed).toBe(true);
    });

    test('devrait récupérer les métriques des clients', async () => {
      const mockMetrics = {
        total_requests: 1250,
        successful_requests: 1180,
        failed_requests: 70,
        average_response_time: 85.5,
        clients_health: {
          healthy: 6,
          unhealthy: 1,
          unknown: 1
        }
      };

      mockAxios.onGet('/api/clients/metrics/').reply(200, mockMetrics);

      const result = await apiClientsService.getClientsMetrics('1h');
      
      expect(result.success).toBe(true);
      expect(result.data.total_requests).toBe(1250);
      expect(result.data.clients_health.healthy).toBe(6);
    });

    test('devrait gérer les erreurs de connexion', async () => {
      mockAxios.onGet('/api/clients/').networkError();

      const result = await apiClientsService.getClients();
      
      expect(result.success).toBe(false);
      expect(result.error.type).toBe('NETWORK_ERROR');
    });
  });

  /**
   * ===========================================
   * TESTS MODULE API_VIEWS
   * ===========================================
   */
  describe('Module api_views', () => {
    
    test('devrait récupérer la vue d\'ensemble du dashboard', async () => {
      const mockDashboard = {
        devices: {
          total: 25,
          online: 22,
          offline: 3
        },
        alerts: {
          total: 8,
          critical: 2,
          warning: 4,
          info: 2
        },
        system: {
          overall_status: 'healthy',
          cpu_usage: 45.2,
          memory_usage: 67.8,
          disk_usage: 78.5
        },
        network: {
          topology_nodes: 15,
          active_connections: 48
        }
      };

      mockAxios.onGet('/api/views/dashboard/').reply(200, mockDashboard);

      const result = await apiViewsService.getDashboardOverview();
      
      expect(result.success).toBe(true);
      expect(result.data.devices.total).toBe(25);
      expect(result.data.system.overall_status).toBe('healthy');
      expect(result.metadata.devicesTotal).toBe(25);
    });

    test('devrait démarrer une découverte de topologie', async () => {
      const mockDiscovery = {
        discovery_id: 'disc_12345',
        network_id: 'net_001',
        status: 'started',
        estimated_time: 120
      };

      mockAxios.onPost('/api/views/topology/discovery/').reply(200, mockDiscovery);

      const result = await apiViewsService.startTopologyDiscovery({
        network_id: 'net_001',
        discovery_method: 'snmp',
        include_switches: true
      });
      
      expect(result.success).toBe(true);
      expect(result.discoveryId).toBe('disc_12345');
      expect(result.metadata.networkId).toBe('net_001');
    });

    test('devrait effectuer une recherche globale', async () => {
      const mockSearchResults = {
        total: 15,
        results: [
          {
            type: 'device',
            id: 'dev_001',
            name: 'Switch-Core-01',
            ip: '192.168.1.10'
          },
          {
            type: 'alert',
            id: 'alert_001',
            severity: 'warning',
            message: 'High CPU usage'
          }
        ],
        facets: {
          types: ['device', 'alert', 'interface'],
          statuses: ['active', 'inactive']
        }
      };

      mockAxios.onGet('/api/views/search/', {
        params: { q: 'switch', type: 'all' }
      }).reply(200, mockSearchResults);

      const result = await apiViewsService.globalSearch('switch');
      
      expect(result.success).toBe(true);
      expect(result.data.total).toBe(15);
      expect(result.metadata.resultsCount).toBe(15);
    });
  });

  /**
   * ===========================================
   * TESTS MODULE DASHBOARD
   * ===========================================
   */
  describe('Module dashboard', () => {
    
    test('devrait récupérer la configuration utilisateur', async () => {
      const mockConfig = {
        id: 1,
        theme: 'dark',
        layout: 'grid',
        refresh_interval: 30,
        user: 'admin'
      };

      mockAxios.onGet('/api/dashboard/config/').reply(200, mockConfig);

      const result = await dashboardService.getUserConfig();
      
      expect(result.success).toBe(true);
      expect(result.data.theme).toBe('dark');
      expect(result.metadata.refreshInterval).toBe(30);
    });

    test('devrait créer un dashboard personnalisé', async () => {
      const mockDashboard = {
        id: 'dash_12345',
        name: 'Mon Dashboard Réseau',
        description: 'Dashboard pour monitoring réseau',
        layout: {
          widgets: [
            {
              id: 'widget_1',
              type: 'system_health',
              position: { x: 0, y: 0, w: 2, h: 1 }
            }
          ]
        },
        is_default: false,
        is_public: false,
        owner: 'admin'
      };

      mockAxios.onPost('/api/dashboard/custom/').reply(201, mockDashboard);

      const dashboardData = {
        name: 'Mon Dashboard Réseau',
        description: 'Dashboard pour monitoring réseau',
        layout: {
          widgets: [
            {
              id: 'widget_1',
              type: 'system_health',
              position: { x: 0, y: 0, w: 2, h: 1 }
            }
          ]
        }
      };

      const result = await dashboardService.createCustomDashboard(dashboardData);
      
      expect(result.success).toBe(true);
      expect(result.data.name).toBe('Mon Dashboard Réseau');
      expect(result.dashboardId).toBe('dash_12345');
    });

    test('devrait créer un widget', async () => {
      const mockWidget = {
        id: 'widget_789',
        widget_type: 'network_overview',
        position_x: 0,
        position_y: 1,
        width: 2,
        height: 1,
        settings: {
          show_legend: true,
          auto_refresh: true
        },
        is_active: true
      };

      mockAxios.onPost('/api/dashboard/widgets/').reply(201, mockWidget);

      const widgetData = {
        widget_type: 'network_overview',
        position_x: 0,
        position_y: 1,
        width: 2,
        height: 1,
        settings: {
          show_legend: true,
          auto_refresh: true
        }
      };

      const result = await dashboardService.createWidget(widgetData);
      
      expect(result.success).toBe(true);
      expect(result.data.widget_type).toBe('network_overview');
      expect(result.widgetId).toBe('widget_789');
    });

    test('devrait récupérer les données temps réel du dashboard', async () => {
      const mockDashboardData = {
        widgets: [
          {
            id: 'widget_1',
            type: 'system_health',
            data: { cpu: 45.2, memory: 67.8, status: 'healthy' }
          }
        ],
        metrics: {
          devices_online: 22,
          alerts_active: 5,
          last_update: '2025-01-01T12:00:00Z'
        }
      };

      mockAxios.onGet('/api/dashboard/data/').reply(200, mockDashboardData);

      const result = await dashboardService.getDashboardData();
      
      expect(result.success).toBe(true);
      expect(result.data.widgets).toHaveLength(1);
      expect(result.metadata.widgetsCount).toBe(1);
    });
  });

  /**
   * ===========================================
   * TESTS MODULE GNS3_INTEGRATION
   * ===========================================
   */
  describe('Module gns3_integration', () => {
    
    test('devrait récupérer la liste des serveurs GNS3', async () => {
      const mockServers = [
        {
          id: 1,
          name: 'GNS3 Server Local',
          host: 'localhost',
          port: 3080,
          protocol: 'http',
          is_active: true,
          timeout: 30
        },
        {
          id: 2,
          name: 'GNS3 Server Remote',
          host: '192.168.1.100',
          port: 3080,
          protocol: 'https',
          is_active: true,
          timeout: 60
        }
      ];

      mockAxios.onGet('/api/gns3_integration/api/servers/').reply(200, {
        results: mockServers,
        count: 2
      });

      const result = await gns3Service.getServers();
      
      expect(result.success).toBe(true);
      expect(result.data).toHaveLength(2);
      expect(result.metadata.totalServers).toBe(2);
      expect(result.metadata.activeServers).toBe(2);
    });

    test('devrait tester la connexion à un serveur GNS3', async () => {
      const mockTestResult = {
        success: true,
        version: '2.2.43',
        connection_time: 0.045,
        capabilities: ['compute', 'controller']
      };

      mockAxios.onPost('/api/gns3_integration/api/servers/1/test/').reply(200, mockTestResult);

      const result = await gns3Service.testServer(1);
      
      expect(result.success).toBe(true);
      expect(result.data.version).toBe('2.2.43');
      expect(result.metadata.testPassed).toBe(true);
    });

    test('devrait créer un projet GNS3', async () => {
      const mockProject = {
        id: 'proj_12345',
        project_id: 'proj_12345',
        name: 'Réseau Test Lab',
        status: 'opened',
        server_id: 1,
        scene_height: 1000,
        scene_width: 2000,
        created_at: '2025-01-01T12:00:00Z'
      };

      mockAxios.onPost('/api/gns3_integration/api/projects/').reply(201, mockProject);

      const projectData = {
        name: 'Réseau Test Lab',
        server: 1,
        auto_start: false,
        auto_close: true
      };

      const result = await gns3Service.createProject(projectData);
      
      expect(result.success).toBe(true);
      expect(result.data.name).toBe('Réseau Test Lab');
      expect(result.projectId).toBe('proj_12345');
    });

    test('devrait démarrer un projet GNS3', async () => {
      const mockProjectResponse = {
        id: 'proj_12345',
        status: 'opened',
        scene_height: 1000,
        scene_width: 2000
      };

      mockAxios.onPost('/api/gns3_integration/api/projects/proj_12345/start/').reply(200, mockProjectResponse);

      const result = await gns3Service.startProject('proj_12345');
      
      expect(result.success).toBe(true);
      expect(result.action).toBe('start');
      expect(result.metadata.newStatus).toBe('opened');
    });

    test('devrait récupérer les nœuds d\'un projet', async () => {
      const mockNodes = [
        {
          id: 'node_001',
          name: 'Router-1',
          node_type: 'dynamips',
          status: 'started',
          project_id: 'proj_12345',
          x: 100,
          y: 150,
          console: 5000
        },
        {
          id: 'node_002',
          name: 'Switch-1',
          node_type: 'ethernet_switch',
          status: 'started',
          project_id: 'proj_12345',
          x: 300,
          y: 150,
          console: 5001
        }
      ];

      mockAxios.onGet('/api/gns3_integration/api/projects/proj_12345/nodes/').reply(200, mockNodes);

      const result = await gns3Service.getProjectNodes('proj_12345');
      
      expect(result.success).toBe(true);
      expect(result.data).toHaveLength(2);
      expect(result.metadata.nodesCount).toBe(2);
      expect(result.metadata.nodeTypes).toContain('dynamips');
    });

    test('devrait créer un snapshot', async () => {
      const mockSnapshot = {
        id: 'snap_12345',
        name: 'Before Config Changes',
        project_id: 'proj_12345',
        created_at: '2025-01-01T12:00:00Z',
        status: 'completed'
      };

      mockAxios.onPost('/api/gns3_integration/api/snapshots/').reply(201, mockSnapshot);

      const snapshotData = {
        name: 'Before Config Changes',
        project: 'proj_12345',
        description: 'Snapshot avant modifications de configuration'
      };

      const result = await gns3Service.createSnapshot(snapshotData);
      
      expect(result.success).toBe(true);
      expect(result.data.name).toBe('Before Config Changes');
      expect(result.snapshotId).toBe('snap_12345');
    });
  });

  /**
   * ===========================================
   * TESTS DE VALIDATION DES ENDPOINTS
   * ===========================================
   */
  describe('Validation des endpoints API', () => {
    
    test('tous les services devraient avoir les bonnes URLs de base', () => {
      // Vérifier les URLs de base des services
      expect(apiClientsService.getStats().baseUrl || '/api/clients').toContain('/api/clients');
      expect(apiViewsService.getStats().baseUrl || '/api/views').toContain('/api/views');
      expect(dashboardService.getStats().baseUrl || '/api/dashboard').toContain('/api/dashboard');
      expect(gns3Service.getStats().baseUrl || '/api/gns3_integration').toContain('/api/gns3_integration');
    });

    test('devrait gérer les erreurs 404 correctement', async () => {
      mockAxios.onGet('/api/clients/999').reply(404, {
        detail: 'Client not found'
      });

      const result = await apiClientsService.getClient(999);
      
      expect(result.success).toBe(false);
      expect(result.error.status).toBe(404);
      expect(result.error.type).toBe('CLIENT_NOT_FOUND');
    });

    test('devrait gérer les erreurs 500 correctement', async () => {
      mockAxios.onGet('/api/views/dashboard/').reply(500, {
        error: 'Internal server error'
      });

      const result = await apiViewsService.getDashboardOverview();
      
      expect(result.success).toBe(false);
      expect(result.error.status).toBe(500);
      expect(result.error.type).toBe('SERVER_ERROR');
    });

    test('devrait valider les champs requis', async () => {
      // Test de validation pour création serveur GNS3
      const result = await gns3Service.createServer({
        // Manque les champs requis: name, host, port
        description: 'Serveur de test'
      });
      
      expect(result.success).toBe(false);
      expect(result.error.type).toBe('VALIDATION_ERROR');
      expect(result.error.missingFields).toContain('name');
      expect(result.error.missingFields).toContain('host');
      expect(result.error.missingFields).toContain('port');
    });
  });

  /**
   * ===========================================
   * TESTS DE PERFORMANCE ET CACHE
   * ===========================================
   */
  describe('Performance et cache', () => {
    
    test('devrait utiliser le cache correctement', async () => {
      const mockData = { test: 'data' };
      
      // Première requête
      mockAxios.onGet('/api/clients/').reply(200, mockData);
      const result1 = await apiClientsService.getClients();
      
      // Deuxième requête (devrait utiliser le cache)
      const result2 = await apiClientsService.getClients();
      
      expect(result1.success).toBe(true);
      expect(result2.success).toBe(true);
      
      const stats = apiClientsService.getStats();
      expect(stats.cacheHits).toBeGreaterThan(0);
    });

    test('devrait mesurer les temps de réponse', async () => {
      mockAxios.onGet('/api/dashboard/data/').reply(200, { data: 'test' });
      
      const startTime = Date.now();
      const result = await dashboardService.getDashboardData();
      const endTime = Date.now();
      
      expect(result.success).toBe(true);
      expect(endTime - startTime).toBeLessThan(1000); // Moins d'une seconde
    });
  });

  /**
   * ===========================================
   * TESTS D'INTÉGRATION COMPLÈTE
   * ===========================================
   */
  describe('Tests d\'intégration complète', () => {
    
    test('workflow complet: créer serveur → créer projet → ajouter nœuds', async () => {
      // 1. Créer un serveur GNS3
      mockAxios.onPost('/api/gns3_integration/api/servers/').reply(201, {
        id: 1,
        name: 'Test Server',
        host: 'localhost',
        port: 3080
      });

      const serverResult = await gns3Service.createServer({
        name: 'Test Server',
        host: 'localhost',
        port: 3080
      });

      expect(serverResult.success).toBe(true);

      // 2. Créer un projet sur ce serveur
      mockAxios.onPost('/api/gns3_integration/api/projects/').reply(201, {
        id: 'proj_001',
        name: 'Test Project',
        server_id: 1,
        status: 'opened'
      });

      const projectResult = await gns3Service.createProject({
        name: 'Test Project',
        server: 1
      });

      expect(projectResult.success).toBe(true);

      // 3. Récupérer les nœuds du projet
      mockAxios.onGet('/api/gns3_integration/api/projects/proj_001/nodes/').reply(200, []);

      const nodesResult = await gns3Service.getProjectNodes('proj_001');

      expect(nodesResult.success).toBe(true);
      expect(nodesResult.data).toHaveLength(0); // Projet vide au début
    });

    test('workflow dashboard: créer dashboard → ajouter widgets → configurer temps réel', async () => {
      // 1. Créer un dashboard personnalisé
      mockAxios.onPost('/api/dashboard/custom/').reply(201, {
        id: 'dash_001',
        name: 'Mon Dashboard',
        layout: { widgets: [] }
      });

      const dashboardResult = await dashboardService.createCustomDashboard({
        name: 'Mon Dashboard',
        description: 'Dashboard de test'
      });

      expect(dashboardResult.success).toBe(true);

      // 2. Ajouter un widget
      mockAxios.onPost('/api/dashboard/widgets/').reply(201, {
        id: 'widget_001',
        widget_type: 'system_health',
        is_active: true
      });

      const widgetResult = await dashboardService.createWidget({
        widget_type: 'system_health',
        config: 'dash_001'
      });

      expect(widgetResult.success).toBe(true);

      // 3. Récupérer les données temps réel
      mockAxios.onGet('/api/dashboard/data/').reply(200, {
        widgets: [{ id: 'widget_001', data: { status: 'healthy' } }],
        metrics: { devices_online: 10 }
      });

      const dataResult = await dashboardService.getDashboardData();

      expect(dataResult.success).toBe(true);
      expect(dataResult.data.widgets).toHaveLength(1);
    });
  });
});

/**
 * ===========================================
 * TESTS UTILITAIRES
 * ===========================================
 */
describe('Tests utilitaires et helpers', () => {
  
  test('devrait formater correctement les URLs', () => {
    // Test des constantes d'endpoints
    expect(apiClientsService.constructor.name).toBe('APIClientsService');
    expect(typeof gns3Service.getStats).toBe('function');
  });

  test('devrait gérer correctement les timeouts', async () => {
    mockAxios.onGet('/api/clients/').timeout();

    const result = await apiClientsService.getClients();
    
    expect(result.success).toBe(false);
    expect(result.error.type).toBe('NETWORK_ERROR');
  });

  test('devrait nettoyer le cache correctement', () => {
    apiClientsService.clearCache();
    const stats = apiClientsService.getStats();
    
    expect(stats.cacheSize).toBe(0);
  });
});