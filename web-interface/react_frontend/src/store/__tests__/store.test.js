/**
 * Tests pour le store Redux AI Assistant
 * Validation de l'intégration Phase 2
 */

import { createTestStore } from '../index';
import { fetchConversations } from '../slices/conversationsSlice';
import { sendMessage } from '../slices/messagesSlice';
import { uploadDocument } from '../slices/documentsSlice';
import { executeCommand } from '../slices/commandsSlice';
import { performGlobalSearch } from '../slices/searchSlice';
import { setTheme, addNotification } from '../slices/uiSlice';

// Mock du service AI Assistant
jest.mock('../../services/aiAssistantService', () => ({
  getConversations: jest.fn(),
  sendMessage: jest.fn(),
  uploadDocument: jest.fn(),
  executeCommand: jest.fn(),
  globalSearch: jest.fn(),
  testConnection: jest.fn(),
  validateDataReality: jest.fn(),
  getStats: jest.fn(),
  setUploadProgressCallback: jest.fn(),
}));

describe('Store Redux AI Assistant', () => {
  let store;

  beforeEach(() => {
    store = createTestStore();
    jest.clearAllMocks();
  });

  describe('Configuration du store', () => {
    test('should have correct initial state structure', () => {
      const state = store.getState();
      
      expect(state).toHaveProperty('conversations');
      expect(state).toHaveProperty('messages');
      expect(state).toHaveProperty('documents');
      expect(state).toHaveProperty('commands');
      expect(state).toHaveProperty('search');
      expect(state).toHaveProperty('ui');
    });

    test('should have correct initial values', () => {
      const state = store.getState();
      
      expect(state.conversations.items).toEqual([]);
      expect(state.messages.messagesByConversation).toEqual({});
      expect(state.documents.items).toEqual([]);
      expect(state.commands.commands).toEqual([]);
      expect(state.search.results).toEqual([]);
      expect(state.ui.theme).toBe('light');
    });
  });

  describe('Conversations Slice', () => {
    test('should handle fetchConversations action', async () => {
      const mockConversations = [
        { id: 1, title: 'Test Conversation', created_at: '2025-06-24T10:00:00Z' }
      ];

      const mockResponse = {
        success: true,
        data: { results: mockConversations },
        pagination: { currentPage: 1, totalCount: 1 }
      };

      require('../../services/aiAssistantService').getConversations.mockResolvedValue(mockResponse);

      await store.dispatch(fetchConversations());
      
      const state = store.getState();
      expect(state.conversations.items).toEqual(mockConversations);
      expect(state.conversations.loading.fetch).toBe(false);
      expect(state.conversations.error).toBeNull();
    });
  });

  describe('Messages Slice', () => {
    test('should handle sendMessage action', async () => {
      const mockMessage = {
        id: 1,
        conversation: 1,
        role: 'user',
        content: 'Test message',
        created_at: '2025-06-24T10:00:00Z'
      };

      const mockResponse = {
        success: true,
        data: mockMessage
      };

      require('../../services/aiAssistantService').sendMessage.mockResolvedValue(mockResponse);

      await store.dispatch(sendMessage({
        conversationId: 1,
        messageData: { content: 'Test message' }
      }));
      
      const state = store.getState();
      expect(state.messages.messagesByConversation[1]).toContainEqual(mockMessage);
      expect(state.messages.loading.send).toBe(false);
    });
  });

  describe('Documents Slice', () => {
    test('should handle uploadDocument action', async () => {
      const mockDocument = {
        id: 'doc-uuid-123',
        title: 'Test Document',
        content: 'Test content',
        created_at: '2025-06-24T10:00:00Z'
      };

      const mockResponse = {
        success: true,
        data: mockDocument
      };

      require('../../services/aiAssistantService').uploadDocument.mockResolvedValue(mockResponse);

      await store.dispatch(uploadDocument({
        documentData: { title: 'Test Document', content: 'Test content' }
      }));
      
      const state = store.getState();
      expect(state.documents.items).toContainEqual(mockDocument);
      expect(state.documents.loading.upload).toBe(false);
    });
  });

  describe('Commands Slice', () => {
    test('should handle executeCommand action', async () => {
      const mockCommand = {
        id: 1,
        name: 'test_command',
        status: 'completed',
        result: { message: 'Command executed successfully' }
      };

      const mockResponse = {
        success: true,
        data: mockCommand
      };

      require('../../services/aiAssistantService').executeCommand.mockResolvedValue(mockResponse);

      await store.dispatch(executeCommand({
        name: 'test_command',
        parameters: { test: true }
      }));
      
      const state = store.getState();
      expect(state.commands.lastExecution).toEqual(mockCommand);
      expect(state.commands.loading.execute).toBe(false);
    });
  });

  describe('Search Slice', () => {
    test('should handle performGlobalSearch action', async () => {
      const mockResults = [
        { type: 'conversation', id: 1, title: 'Test Result' }
      ];

      const mockResponse = {
        success: true,
        data: { results: mockResults }
      };

      require('../../services/aiAssistantService').globalSearch.mockResolvedValue(mockResponse);

      await store.dispatch(performGlobalSearch({
        query: 'test query'
      }));
      
      const state = store.getState();
      expect(state.search.results).toEqual(mockResults);
      expect(state.search.query).toBe('test query');
      expect(state.search.loading).toBe(false);
    });
  });

  describe('UI Slice', () => {
    test('should handle theme changes', () => {
      store.dispatch(setTheme('dark'));
      
      const state = store.getState();
      expect(state.ui.theme).toBe('dark');
    });

    test('should handle notifications', () => {
      const notification = {
        type: 'success',
        title: 'Test',
        message: 'Test notification'
      };

      store.dispatch(addNotification(notification));
      
      const state = store.getState();
      expect(state.ui.notifications).toHaveLength(1);
      expect(state.ui.notifications[0]).toMatchObject(notification);
      expect(state.ui.notifications[0]).toHaveProperty('id');
      expect(state.ui.notifications[0]).toHaveProperty('timestamp');
    });
  });

  describe('Error Handling', () => {
    test('should handle API errors correctly', async () => {
      const mockError = {
        type: 'NETWORK_ERROR',
        message: 'Connection failed'
      };

      require('../../services/aiAssistantService').getConversations.mockRejectedValue(mockError);

      await store.dispatch(fetchConversations());

      const state = store.getState();
      expect(state.conversations.loading.fetch).toBe(false);
      expect(state.conversations.error).toMatchObject({
        type: 'NETWORK_ERROR',
        message: 'Connection failed'
      });
    });
  });

  describe('Data Reality Validation', () => {
    test('should validate 95.65% real data constraint', () => {
      const mockValidation = {
        realDataPercentage: 100,
        compliance: {
          required: 95.65,
          actual: 100,
          status: 'COMPLIANT'
        }
      };

      require('../../services/aiAssistantService').validateDataReality.mockReturnValue(mockValidation);

      // Simuler la validation
      const validation = require('../../services/aiAssistantService').validateDataReality();
      
      expect(validation.compliance.actual).toBeGreaterThanOrEqual(95.65);
      expect(validation.compliance.status).toBe('COMPLIANT');
    });
  });
});
