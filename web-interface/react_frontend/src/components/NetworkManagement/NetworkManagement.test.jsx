/**
 * Tests d'intégration pour les composants Network Management
 * Validation du fonctionnement avec les hooks et services développés
 */

import { describe, test, expect, beforeEach, vi } from '@jest/globals';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';

// Import des composants
import {
  ApiClientsManager,
  DashboardOverview,
  GNS3ProjectManager,
  ApiViewsInterface
} from './index';

// Import des slices Redux
import apiClientsSlice from '../../store/slices/apiClientsSlice';
import apiViewsSlice from '../../store/slices/apiViewsSlice';
import dashboardSlice from '../../store/slices/dashboardSlice';
import gns3Slice from '../../store/slices/gns3Slice';

// Helper pour créer un store de test
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

// Wrapper pour les tests
const TestWrapper = ({ children, store }) => (
  <Provider store={store}>
    <BrowserRouter>
      {children}
    </BrowserRouter>
  </Provider>
);

// Mock des services API
vi.mock('../../services/apiClientsService', () => ({
  default: {
    getClients: vi.fn().mockResolvedValue({
      success: true,
      data: [
        { id: 1, name: 'GNS3 Client', client_type: 'gns3', is_active: true, status: 'healthy' }
      ]
    }),
    testClient: vi.fn().mockResolvedValue({ success: true }),
    getStats: vi.fn().mockReturnValue({ total: 1, active: 1, healthy: 1 })
  }
}));

vi.mock('../../services/dashboardService', () => ({
  default: {
    getDashboardData: vi.fn().mockResolvedValue({
      success: true,
      data: { devices: { total: 10, online: 8 } }
    }),
    getUserConfig: vi.fn().mockResolvedValue({
      success: true,
      data: { theme: 'light', layout: 'grid' }
    })
  }
}));

vi.mock('../../services/gns3Service', () => ({
  default: {
    getServers: vi.fn().mockResolvedValue({
      success: true,
      data: [
        { id: 1, name: 'GNS3 Server', host: 'localhost', port: 3080, is_active: true }
      ]
    }),
    getProjects: vi.fn().mockResolvedValue({
      success: true,
      data: [
        { id: 'proj1', name: 'Test Project', status: 'closed', server_id: 1 }
      ]
    })
  }
}));

vi.mock('../../services/apiViewsService', () => ({
  default: {
    getDashboardOverview: vi.fn().mockResolvedValue({
      success: true,
      data: { devices: { total: 15, online: 12 } }
    }),
    globalSearch: vi.fn().mockResolvedValue({
      success: true,
      data: { results: [], total: 0 }
    })
  }
}));

describe('Tests d\'intégration Network Management', () => {

  /**
   * Tests du composant API Clients Manager
   */
  describe('ApiClientsManager', () => {
    test('devrait afficher le composant avec titre et boutons', () => {
      const store = createTestStore({
        apiClients: {
          items: [],
          loading: { fetch: false },
          error: null
        }
      });

      render(
        <TestWrapper store={store}>
          <ApiClientsManager />
        </TestWrapper>
      );

      expect(screen.getByText('Gestion des Clients API')).toBeInTheDocument();
      expect(screen.getByText('Nouveau Client')).toBeInTheDocument();
      expect(screen.getByText('Actualiser')).toBeInTheDocument();
    });

    test('devrait afficher les statistiques des clients', () => {
      const store = createTestStore({
        apiClients: {
          items: [
            { id: 1, name: 'Test Client', client_type: 'gns3', is_active: true, status: 'healthy' }
          ],
          loading: { fetch: false },
          error: null
        }
      });

      render(
        <TestWrapper store={store}>
          <ApiClientsManager />
        </TestWrapper>
      );

      expect(screen.getByText('Total Clients')).toBeInTheDocument();
      expect(screen.getByText('Clients Actifs')).toBeInTheDocument();
      expect(screen.getByText('Clients Sains')).toBeInTheDocument();
    });

    test('devrait ouvrir le modal de création de client', async () => {
      const store = createTestStore();

      render(
        <TestWrapper store={store}>
          <ApiClientsManager />
        </TestWrapper>
      );

      const newClientButton = screen.getByText('Nouveau Client');
      fireEvent.click(newClientButton);

      await waitFor(() => {
        expect(screen.getByText('Nouveau Client API')).toBeInTheDocument();
      });
    });
  });

  /**
   * Tests du composant Dashboard Overview
   */
  describe('DashboardOverview', () => {
    test('devrait afficher le dashboard avec métriques', () => {
      const store = createTestStore({
        dashboard: {
          dashboardData: { devices: { total: 10, online: 8 } },
          userConfig: { theme: 'light' },
          loading: { dashboard: false },
          error: null
        }
      });

      render(
        <TestWrapper store={store}>
          <DashboardOverview />
        </TestWrapper>
      );

      expect(screen.getByText('Dashboard Système')).toBeInTheDocument();
      expect(screen.getByText('Équipements Totaux')).toBeInTheDocument();
      expect(screen.getByText('Alertes Actives')).toBeInTheDocument();
    });

    test('devrait afficher les contrôles de configuration', () => {
      const store = createTestStore();

      render(
        <TestWrapper store={store}>
          <DashboardOverview />
        </TestWrapper>
      );

      expect(screen.getByText('Actualiser')).toBeInTheDocument();
      expect(screen.getByText('Configurer')).toBeInTheDocument();
    });

    test('devrait afficher les métriques système', () => {
      const store = createTestStore();

      render(
        <TestWrapper store={store}>
          <DashboardOverview />
        </TestWrapper>
      );

      expect(screen.getByText('Métriques Système')).toBeInTheDocument();
      expect(screen.getByText('CPU')).toBeInTheDocument();
      expect(screen.getByText('Mémoire')).toBeInTheDocument();
      expect(screen.getByText('Disque')).toBeInTheDocument();
    });
  });

  /**
   * Tests du composant GNS3 Project Manager
   */
  describe('GNS3ProjectManager', () => {
    test('devrait afficher le gestionnaire GNS3', () => {
      const store = createTestStore({
        gns3: {
          servers: [],
          projects: [],
          nodes: [],
          loading: { servers: false, projects: false },
          error: null
        }
      });

      render(
        <TestWrapper store={store}>
          <GNS3ProjectManager />
        </TestWrapper>
      );

      expect(screen.getByText('Gestionnaire GNS3')).toBeInTheDocument();
      expect(screen.getByText('Nouveau Projet')).toBeInTheDocument();
      expect(screen.getByText('Importer')).toBeInTheDocument();
    });

    test('devrait afficher les statistiques GNS3', () => {
      const store = createTestStore();

      render(
        <TestWrapper store={store}>
          <GNS3ProjectManager />
        </TestWrapper>
      );

      expect(screen.getByText('Serveurs GNS3')).toBeInTheDocument();
      expect(screen.getByText('Projets Totaux')).toBeInTheDocument();
      expect(screen.getByText('Projets Actifs')).toBeInTheDocument();
      expect(screen.getByText('Nœuds Actifs')).toBeInTheDocument();
    });

    test('devrait afficher les onglets de navigation', () => {
      const store = createTestStore();

      render(
        <TestWrapper store={store}>
          <GNS3ProjectManager />
        </TestWrapper>
      );

      expect(screen.getByText(/Projets/)).toBeInTheDocument();
      expect(screen.getByText(/Nœuds/)).toBeInTheDocument();
      expect(screen.getByText(/Serveurs/)).toBeInTheDocument();
    });
  });

  /**
   * Tests du composant API Views Interface
   */
  describe('ApiViewsInterface', () => {
    test('devrait afficher l\'interface des vues API', () => {
      const store = createTestStore({
        apiViews: {
          dashboardData: null,
          searchResults: null,
          loading: { dashboard: false, search: false },
          error: null
        }
      });

      render(
        <TestWrapper store={store}>
          <ApiViewsInterface />
        </TestWrapper>
      );

      expect(screen.getByText('Vues API & Recherche')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Recherche globale...')).toBeInTheDocument();
      expect(screen.getByText('Découverte')).toBeInTheDocument();
    });

    test('devrait afficher les onglets de navigation', () => {
      const store = createTestStore();

      render(
        <TestWrapper store={store}>
          <ApiViewsInterface />
        </TestWrapper>
      );

      expect(screen.getByText('Vue d\'ensemble')).toBeInTheDocument();
      expect(screen.getByText(/Recherche/)).toBeInTheDocument();
      expect(screen.getByText(/Découverte/)).toBeInTheDocument();
      expect(screen.getByText('Configuration')).toBeInTheDocument();
    });

    test('devrait permettre la recherche', async () => {
      const store = createTestStore();

      render(
        <TestWrapper store={store}>
          <ApiViewsInterface />
        </TestWrapper>
      );

      const searchInput = screen.getByPlaceholderText('Recherche globale...');
      fireEvent.change(searchInput, { target: { value: 'test' } });

      const searchButton = screen.getByRole('button', { name: /recherche/i });
      fireEvent.click(searchButton);

      // La recherche devrait déclencher l'action Redux
      await waitFor(() => {
        expect(searchInput.value).toBe('test');
      });
    });
  });

  /**
   * Tests d'intégration Redux
   */
  describe('Intégration Redux', () => {
    test('devrait connecter tous les composants au store Redux', () => {
      const store = createTestStore({
        apiClients: { items: [], loading: { fetch: false }, error: null },
        dashboard: { dashboardData: null, loading: { dashboard: false }, error: null },
        gns3: { servers: [], projects: [], loading: { servers: false }, error: null },
        apiViews: { dashboardData: null, loading: { dashboard: false }, error: null }
      });

      // Test que tous les composants peuvent se connecter au store
      expect(() => {
        render(
          <TestWrapper store={store}>
            <ApiClientsManager />
          </TestWrapper>
        );
      }).not.toThrow();

      expect(() => {
        render(
          <TestWrapper store={store}>
            <DashboardOverview />
          </TestWrapper>
        );
      }).not.toThrow();

      expect(() => {
        render(
          <TestWrapper store={store}>
            <GNS3ProjectManager />
          </TestWrapper>
        );
      }).not.toThrow();

      expect(() => {
        render(
          <TestWrapper store={store}>
            <ApiViewsInterface />
          </TestWrapper>
        );
      }).not.toThrow();
    });
  });

  /**
   * Tests de performance
   */
  describe('Performance', () => {
    test('devrait rendre les composants rapidement', () => {
      const store = createTestStore();

      const start = performance.now();

      render(
        <TestWrapper store={store}>
          <ApiClientsManager />
        </TestWrapper>
      );

      const end = performance.now();
      const renderTime = end - start;

      // Le rendu devrait prendre moins de 100ms
      expect(renderTime).toBeLessThan(100);
    });
  });
});