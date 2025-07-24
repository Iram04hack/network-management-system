/**
 * Configuration des tests pour AI Assistant React Frontend
 * Setup Jest et React Testing Library
 */

import '@testing-library/jest-dom';

// Configuration globale pour les tests
global.console = {
  ...console,
  // Supprimer les warnings inutiles en test
  warn: jest.fn(),
  error: jest.fn(),
};

// Mock de localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock de sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// Mock de fetch pour les tests
global.fetch = jest.fn();

// Mock de window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock de ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock de IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Configuration pour les tests avec des timers
beforeEach(() => {
  jest.clearAllMocks();
  jest.clearAllTimers();
  
  // Reset des mocks localStorage/sessionStorage
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
  
  sessionStorageMock.getItem.mockClear();
  sessionStorageMock.setItem.mockClear();
  sessionStorageMock.removeItem.mockClear();
  sessionStorageMock.clear.mockClear();
  
  // Reset du mock fetch
  fetch.mockClear();
});

// Nettoyage après chaque test
afterEach(() => {
  jest.restoreAllMocks();
});

// Configuration pour les tests asynchrones
jest.setTimeout(10000);

// Mock des modules CSS et assets sont gérés par la configuration Jest

// Utilitaires de test personnalisés
export const createMockStore = (initialState = {}) => {
  return {
    getState: jest.fn(() => initialState),
    dispatch: jest.fn(),
    subscribe: jest.fn(),
  };
};

export const createMockApiResponse = (data, success = true) => {
  return {
    success,
    data,
    error: success ? null : data,
    metadata: {
      timestamp: new Date().toISOString(),
      requestId: 'test-request-id',
    },
  };
};

// Helper pour les tests avec Redux
export const renderWithRedux = (component, { initialState = {}, store = null } = {}) => {
  const { render } = require('@testing-library/react');
  const { Provider } = require('react-redux');
  const { createTestStore } = require('./store');
  
  const testStore = store || createTestStore(initialState);
  
  return {
    ...render(
      <Provider store={testStore}>
        {component}
      </Provider>
    ),
    store: testStore,
  };
};

// Helper pour les tests avec Router
export const renderWithRouter = (component, { initialEntries = ['/'] } = {}) => {
  const { render } = require('@testing-library/react');
  const { MemoryRouter } = require('react-router-dom');
  
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      {component}
    </MemoryRouter>
  );
};

// Helper pour les tests complets (Redux + Router)
export const renderWithProviders = (
  component, 
  { 
    initialState = {}, 
    store = null, 
    initialEntries = ['/'] 
  } = {}
) => {
  const { render } = require('@testing-library/react');
  const { Provider } = require('react-redux');
  const { MemoryRouter } = require('react-router-dom');
  const { createTestStore } = require('./store');
  
  const testStore = store || createTestStore(initialState);
  
  return {
    ...render(
      <Provider store={testStore}>
        <MemoryRouter initialEntries={initialEntries}>
          {component}
        </MemoryRouter>
      </Provider>
    ),
    store: testStore,
  };
};

// Mock des services AI Assistant pour les tests
export const mockAiAssistantService = {
  getConversations: jest.fn(),
  createConversation: jest.fn(),
  getConversation: jest.fn(),
  updateConversation: jest.fn(),
  deleteConversation: jest.fn(),
  getMessages: jest.fn(),
  sendMessage: jest.fn(),
  getMessage: jest.fn(),
  getAllMessages: jest.fn(),
  getDocuments: jest.fn(),
  uploadDocument: jest.fn(),
  getDocument: jest.fn(),
  updateDocument: jest.fn(),
  deleteDocument: jest.fn(),
  searchDocuments: jest.fn(),
  executeCommand: jest.fn(),
  globalSearch: jest.fn(),
  analyzeNetwork: jest.fn(),
  testConnection: jest.fn(),
  validateDataReality: jest.fn(),
  getStats: jest.fn(),
  setUploadProgressCallback: jest.fn(),
};

// Configuration pour les tests de performance
export const measurePerformance = (testName, testFunction) => {
  return async () => {
    const startTime = performance.now();
    await testFunction();
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    console.log(`[Performance] ${testName}: ${duration.toFixed(2)}ms`);
    
    // Fail si le test prend plus de 1 seconde
    expect(duration).toBeLessThan(1000);
  };
};

// Validation de la contrainte de données réelles (95.65%)
export const validateRealDataConstraint = (testData) => {
  const realDataPercentage = testData.realDataCount / testData.totalDataCount * 100;
  expect(realDataPercentage).toBeGreaterThanOrEqual(95.65);
  return realDataPercentage;
};
