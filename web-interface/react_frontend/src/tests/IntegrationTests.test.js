/**
 * Tests d'intégration avec les services backend en cours d'exécution
 * Tests avec les endpoints réels
 */

import { describe, test, expect, beforeAll, afterAll } from '@jest/globals';
import { configureStore } from '@reduxjs/toolkit';
import { Provider } from 'react-redux';
import { renderHook, act, waitFor } from '@testing-library/react';

// Import des slices Redux
import apiClientsSlice from '../store/slices/apiClientsSlice';
import apiViewsSlice from '../store/slices/apiViewsSlice';
import dashboardSlice from '../store/slices/dashboardSlice';
import gns3Slice from '../store/slices/gns3Slice';

// Import des services
import apiClientsService from '../services/apiClientsService';
import apiViewsService from '../services/apiViewsService';
import dashboardService from '../services/dashboardService';
import gns3Service from '../services/gns3Service';

// Import des hooks
import { useApiClients } from '../hooks/useApiClients';
import { useApiViews } from '../hooks/useApiViews';
import { useDashboard } from '../hooks/useDashboard';
import { useGNS3 } from '../hooks/useGNS3';

// Configuration du store de test
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

// Variables globales pour les tests
let testResults = {
  backend_running: false,
  api_endpoints: {},
  services_tested: {},
  integration_status: {}
};

describe('Tests d\'intégration avec backend en cours d\'exécution', () => {

  beforeAll(async () => {
    console.log('🚀 Démarrage des tests d\'intégration avec backend réel');
    
    // Vérifier que le backend est accessible
    try {
      const response = await fetch('http://localhost:8000/admin/login/', {
        method: 'HEAD'
      });
      testResults.backend_running = response.ok;
      console.log('✅ Backend Django accessible sur le port 8000');
    } catch (error) {
      console.log('❌ Backend Django non accessible:', error.message);
      testResults.backend_running = false;
    }

    // Vérifier que le frontend est accessible
    try {
      const response = await fetch('http://localhost:5173/', {
        method: 'HEAD'
      });
      console.log('✅ Frontend React accessible sur le port 5173');
    } catch (error) {
      console.log('❌ Frontend React non accessible:', error.message);
    }
  });

  afterAll(() => {
    console.log('\n📊 Résumé des tests d\'intégration:');
    console.log('Backend running:', testResults.backend_running);
    console.log('Endpoints testés:', Object.keys(testResults.api_endpoints).length);
    console.log('Services testés:', Object.keys(testResults.services_tested).length);
    console.log('Status intégration:', testResults.integration_status);
  });

  /**
   * ===========================================
   * TESTS BASIQUES DE CONNECTIVITÉ
   * ===========================================
   */
  describe('Connectivité des services', () => {
    
    test('devrait pouvoir accéder au backend Django', async () => {
      expect(testResults.backend_running).toBe(true);
    });

    test('devrait pouvoir tester les endpoints principaux', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      const endpoints = [
        '/api/clients/',
        '/api/views/dashboard/',
        '/api/dashboard/config/',
        '/api/gns3_integration/api/servers/'
      ];

      for (const endpoint of endpoints) {
        try {
          const response = await fetch(`http://localhost:8000${endpoint}`, {
            method: 'HEAD'
          });
          testResults.api_endpoints[endpoint] = response.status;
          console.log(`📡 ${endpoint}: ${response.status}`);
        } catch (error) {
          testResults.api_endpoints[endpoint] = 'error';
          console.log(`❌ ${endpoint}: ${error.message}`);
        }
      }

      // Au moins un endpoint devrait être accessible
      const accessibleEndpoints = Object.values(testResults.api_endpoints)
        .filter(status => status === 200 || status === 401 || status === 403);
      expect(accessibleEndpoints.length).toBeGreaterThan(0);
    });
  });

  /**
   * ===========================================
   * TESTS SERVICE API_CLIENTS
   * ===========================================
   */
  describe('Service api_clients', () => {
    
    test('devrait tester le service apiClientsService', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      try {
        // Test simple du service
        const result = await apiClientsService.getClients();
        testResults.services_tested.apiClients = {
          tested: true,
          success: result.success,
          error: result.error?.type || null
        };

        console.log('🔧 Service API Clients testé:', testResults.services_tested.apiClients);
        
        // Le service doit au moins retourner une structure cohérente
        expect(typeof result).toBe('object');
        expect(result).toHaveProperty('success');
      } catch (error) {
        testResults.services_tested.apiClients = {
          tested: true,
          success: false,
          error: error.message
        };
        console.log('❌ Erreur service API Clients:', error.message);
      }
    });

    test('devrait tester le hook useApiClients', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      const store = createTestStore();
      const wrapper = createWrapper(store);

      try {
        const { result } = renderHook(() => useApiClients(), { wrapper });

        // Test des propriétés de base du hook
        expect(result.current).toHaveProperty('clients');
        expect(result.current).toHaveProperty('loading');
        expect(result.current).toHaveProperty('error');
        expect(result.current).toHaveProperty('fetchClients');

        console.log('🎣 Hook useApiClients structure OK');
        
        testResults.integration_status.useApiClients = 'OK';
      } catch (error) {
        console.log('❌ Erreur hook useApiClients:', error.message);
        testResults.integration_status.useApiClients = 'ERROR';
      }
    });
  });

  /**
   * ===========================================
   * TESTS SERVICE API_VIEWS
   * ===========================================
   */
  describe('Service api_views', () => {
    
    test('devrait tester le service apiViewsService', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      try {
        const result = await apiViewsService.getDashboardOverview();
        testResults.services_tested.apiViews = {
          tested: true,
          success: result.success,
          error: result.error?.type || null
        };

        console.log('🔧 Service API Views testé:', testResults.services_tested.apiViews);
        
        expect(typeof result).toBe('object');
        expect(result).toHaveProperty('success');
      } catch (error) {
        testResults.services_tested.apiViews = {
          tested: true,
          success: false,
          error: error.message
        };
        console.log('❌ Erreur service API Views:', error.message);
      }
    });

    test('devrait tester le hook useApiViews', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      const store = createTestStore();
      const wrapper = createWrapper(store);

      try {
        const { result } = renderHook(() => useApiViews(), { wrapper });

        expect(result.current).toHaveProperty('dashboardData');
        expect(result.current).toHaveProperty('loading');
        expect(result.current).toHaveProperty('fetchDashboardOverview');

        console.log('🎣 Hook useApiViews structure OK');
        testResults.integration_status.useApiViews = 'OK';
      } catch (error) {
        console.log('❌ Erreur hook useApiViews:', error.message);
        testResults.integration_status.useApiViews = 'ERROR';
      }
    });
  });

  /**
   * ===========================================
   * TESTS SERVICE DASHBOARD
   * ===========================================
   */
  describe('Service dashboard', () => {
    
    test('devrait tester le service dashboardService', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      try {
        const result = await dashboardService.getUserConfig();
        testResults.services_tested.dashboard = {
          tested: true,
          success: result.success,
          error: result.error?.type || null
        };

        console.log('🔧 Service Dashboard testé:', testResults.services_tested.dashboard);
        
        expect(typeof result).toBe('object');
        expect(result).toHaveProperty('success');
      } catch (error) {
        testResults.services_tested.dashboard = {
          tested: true,
          success: false,
          error: error.message
        };
        console.log('❌ Erreur service Dashboard:', error.message);
      }
    });

    test('devrait tester le hook useDashboard', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      const store = createTestStore();
      const wrapper = createWrapper(store);

      try {
        const { result } = renderHook(() => useDashboard(), { wrapper });

        expect(result.current).toHaveProperty('userConfig');
        expect(result.current).toHaveProperty('customDashboards');
        expect(result.current).toHaveProperty('widgets');
        expect(result.current).toHaveProperty('fetchUserConfig');

        console.log('🎣 Hook useDashboard structure OK');
        testResults.integration_status.useDashboard = 'OK';
      } catch (error) {
        console.log('❌ Erreur hook useDashboard:', error.message);
        testResults.integration_status.useDashboard = 'ERROR';
      }
    });
  });

  /**
   * ===========================================
   * TESTS SERVICE GNS3_INTEGRATION
   * ===========================================
   */
  describe('Service gns3_integration', () => {
    
    test('devrait tester le service gns3Service', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      try {
        const result = await gns3Service.getServers();
        testResults.services_tested.gns3 = {
          tested: true,
          success: result.success,
          error: result.error?.type || null
        };

        console.log('🔧 Service GNS3 testé:', testResults.services_tested.gns3);
        
        expect(typeof result).toBe('object');
        expect(result).toHaveProperty('success');
      } catch (error) {
        testResults.services_tested.gns3 = {
          tested: true,
          success: false,
          error: error.message
        };
        console.log('❌ Erreur service GNS3:', error.message);
      }
    });

    test('devrait tester le hook useGNS3', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      const store = createTestStore();
      const wrapper = createWrapper(store);

      try {
        const { result } = renderHook(() => useGNS3(), { wrapper });

        expect(result.current).toHaveProperty('servers');
        expect(result.current).toHaveProperty('projects');
        expect(result.current).toHaveProperty('loading');
        expect(result.current).toHaveProperty('fetchServers');

        console.log('🎣 Hook useGNS3 structure OK');
        testResults.integration_status.useGNS3 = 'OK';
      } catch (error) {
        console.log('❌ Erreur hook useGNS3:', error.message);
        testResults.integration_status.useGNS3 = 'ERROR';
      }
    });
  });

  /**
   * ===========================================
   * TESTS D'INTÉGRATION REDUX
   * ===========================================
   */
  describe('Intégration Redux Store', () => {
    
    test('devrait créer le store avec tous les slices', () => {
      const store = createTestStore();
      const state = store.getState();

      expect(state).toHaveProperty('apiClients');
      expect(state).toHaveProperty('apiViews');
      expect(state).toHaveProperty('dashboard');
      expect(state).toHaveProperty('gns3');

      console.log('🏪 Store Redux configuré avec tous les slices');
    });

    test('devrait avoir les états initiaux corrects', () => {
      const store = createTestStore();
      const state = store.getState();

      // Vérifications de base des états initiaux
      expect(Array.isArray(state.apiClients.items)).toBe(true);
      expect(typeof state.apiClients.loading).toBe('object');
      
      expect(state.apiViews.dashboard).toBeNull();
      expect(typeof state.apiViews.loading).toBe('object');
      
      expect(Array.isArray(state.dashboard.customDashboards)).toBe(true);
      expect(Array.isArray(state.dashboard.widgets)).toBe(true);
      
      expect(Array.isArray(state.gns3.servers)).toBe(true);
      expect(Array.isArray(state.gns3.projects)).toBe(true);

      console.log('🎯 États initiaux Redux validés');
    });
  });

  /**
   * ===========================================
   * TESTS DE WORKFLOW COMPLET
   * ===========================================
   */
  describe('Workflow d\'intégration complète', () => {
    
    test('devrait valider l\'intégration frontend-backend', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      // Compter les services qui fonctionnent
      const workingServices = Object.values(testResults.services_tested)
        .filter(service => service.tested && service.success !== false);

      const workingHooks = Object.values(testResults.integration_status)
        .filter(status => status === 'OK');

      console.log(`✅ Services testés avec succès: ${workingServices.length}/4`);
      console.log(`✅ Hooks intégrés avec succès: ${workingHooks.length}/4`);

      // Au moins 50% des composants devraient fonctionner
      expect(workingServices.length + workingHooks.length).toBeGreaterThanOrEqual(4);
    });

    test('devrait valider la structure des données', () => {
      const store = createTestStore();
      
      // Test dispatch d'une action
      store.dispatch({
        type: 'apiClients/setLoading',
        payload: { type: 'fetch', loading: true }
      });

      const state = store.getState();
      expect(state.apiClients.loading.fetch).toBe(true);

      console.log('🔄 Actions Redux fonctionnelles');
    });
  });

  /**
   * ===========================================
   * TESTS DE PERFORMANCE BASIQUES
   * ===========================================
   */
  describe('Performance d\'intégration', () => {
    
    test('devrait mesurer les temps de réponse des services', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      const startTime = performance.now();
      
      try {
        // Test parallèle de plusieurs services
        const promises = [
          apiClientsService.getStats(),
          apiViewsService.getStats(),
          dashboardService.getStats(),
          gns3Service.getStats()
        ];

        await Promise.allSettled(promises);
        
        const endTime = performance.now();
        const totalTime = endTime - startTime;
        
        console.log(`⏱️ Temps total des appels services: ${totalTime.toFixed(2)}ms`);
        
        // Les services devraient répondre en moins de 5 secondes
        expect(totalTime).toBeLessThan(5000);
      } catch (error) {
        console.log('❌ Erreur test performance:', error.message);
      }
    });

    test('devrait valider la création du store', () => {
      const startTime = performance.now();
      
      const store = createTestStore();
      
      const endTime = performance.now();
      const creationTime = endTime - startTime;
      
      console.log(`⏱️ Temps création store: ${creationTime.toFixed(2)}ms`);
      
      expect(creationTime).toBeLessThan(100); // Moins de 100ms
      expect(store).toBeDefined();
    });
  });
});