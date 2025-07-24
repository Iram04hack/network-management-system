/**
 * Slice Redux pour la gestion des messages
 * Intégration avec le service AI Assistant validé Phase 1
 * Support temps réel et optimistic updates
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import aiAssistantService from '../../services/aiAssistantService';

/**
 * État initial du slice messages
 */
const initialState = {
  // Messages par conversation (structure: { conversationId: [messages] })
  messagesByConversation: {},
  
  // Messages globaux (tous les messages de l'utilisateur)
  allMessages: [],
  
  // Message en cours de composition
  currentMessage: {
    content: '',
    role: 'user',
    metadata: {},
  },
  
  // États de chargement
  loading: {
    fetch: false,
    send: false,
    fetchAll: false,
  },
  
  // Gestion d'erreurs
  error: null,
  lastError: null,
  
  // Métadonnées
  lastFetch: null,
  lastSent: null,
  
  // Configuration temps réel
  realTime: {
    enabled: false,
    connected: false,
    lastHeartbeat: null,
  },
  
  // Statistiques
  stats: {
    totalMessages: 0,
    totalTokens: 0,
    averageResponseTime: 0,
  },
};

/**
 * Actions asynchrones (thunks) pour les messages
 */

// Récupérer les messages d'une conversation
export const fetchMessages = createAsyncThunk(
  'messages/fetchMessages',
  async ({ conversationId, params = {} }, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.getMessages(conversationId, params);
      
      if (result.success) {
        return {
          conversationId,
          messages: result.data.results || result.data,
          metadata: result.metadata,
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error,
      });
    }
  }
);

// Envoyer un message
export const sendMessage = createAsyncThunk(
  'messages/sendMessage',
  async ({ conversationId, messageData }, { getState, rejectWithValue }) => {
    try {
      // Enrichir le message avec des métadonnées client
      const enrichedMessage = {
        ...messageData,
        metadata: {
          clientTimestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          ...messageData.metadata,
        },
      };
      
      const result = await aiAssistantService.sendMessage(conversationId, enrichedMessage);
      
      if (result.success) {
        return {
          conversationId,
          message: result.data,
          metadata: result.metadata,
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error,
      });
    }
  }
);

// Récupérer tous les messages de l'utilisateur
export const fetchAllMessages = createAsyncThunk(
  'messages/fetchAllMessages',
  async (params = {}, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.getAllMessages(params);
      
      if (result.success) {
        return {
          messages: result.data.results || result.data,
          pagination: result.pagination,
          metadata: result.metadata,
        };
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error,
      });
    }
  }
);

// Récupérer un message spécifique
export const fetchMessage = createAsyncThunk(
  'messages/fetchMessage',
  async (messageId, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.getMessage(messageId);
      
      if (result.success) {
        return result.data;
      } else {
        return rejectWithValue(result.error);
      }
    } catch (error) {
      return rejectWithValue({
        type: 'NETWORK_ERROR',
        message: error.message,
        details: error,
      });
    }
  }
);

/**
 * Slice Redux pour les messages
 */
const messagesSlice = createSlice({
  name: 'messages',
  initialState,
  reducers: {
    // Gestion du message en cours de composition
    setCurrentMessage: (state, action) => {
      state.currentMessage = { ...state.currentMessage, ...action.payload };
    },
    
    clearCurrentMessage: (state) => {
      state.currentMessage = initialState.currentMessage;
    },
    
    updateCurrentMessageContent: (state, action) => {
      state.currentMessage.content = action.payload;
    },
    
    // Optimistic updates pour une meilleure UX
    optimisticAddMessage: (state, action) => {
      const { conversationId, message } = action.payload;
      
      if (!state.messagesByConversation[conversationId]) {
        state.messagesByConversation[conversationId] = [];
      }
      
      // Ajouter le message avec un ID temporaire
      const optimisticMessage = {
        ...message,
        id: `temp_${Date.now()}`,
        created_at: new Date().toISOString(),
        status: 'sending',
      };
      
      state.messagesByConversation[conversationId].push(optimisticMessage);
    },
    
    // Mise à jour d'un message optimiste avec la réponse du serveur
    updateOptimisticMessage: (state, action) => {
      const { conversationId, tempId, serverMessage } = action.payload;
      
      if (state.messagesByConversation[conversationId]) {
        const index = state.messagesByConversation[conversationId].findIndex(
          msg => msg.id === tempId
        );
        
        if (index !== -1) {
          state.messagesByConversation[conversationId][index] = serverMessage;
        }
      }
    },
    
    // Supprimer un message optimiste en cas d'erreur
    removeOptimisticMessage: (state, action) => {
      const { conversationId, tempId } = action.payload;
      
      if (state.messagesByConversation[conversationId]) {
        state.messagesByConversation[conversationId] = 
          state.messagesByConversation[conversationId].filter(msg => msg.id !== tempId);
      }
    },
    
    // Gestion du temps réel
    setRealTimeStatus: (state, action) => {
      state.realTime = { ...state.realTime, ...action.payload };
    },
    
    updateHeartbeat: (state) => {
      state.realTime.lastHeartbeat = new Date().toISOString();
    },
    
    // Mise à jour des statistiques
    updateStats: (state, action) => {
      state.stats = { ...state.stats, ...action.payload };
    },
    
    // Gestion d'erreurs
    clearError: (state) => {
      state.error = null;
    },
    
    // Ajouter un message reçu en temps réel
    addRealTimeMessage: (state, action) => {
      const { conversationId, message } = action.payload;
      
      if (!state.messagesByConversation[conversationId]) {
        state.messagesByConversation[conversationId] = [];
      }
      
      // Vérifier que le message n'existe pas déjà
      const exists = state.messagesByConversation[conversationId].some(
        msg => msg.id === message.id
      );
      
      if (!exists) {
        state.messagesByConversation[conversationId].push(message);
        
        // Trier par date de création
        state.messagesByConversation[conversationId].sort(
          (a, b) => new Date(a.created_at) - new Date(b.created_at)
        );
      }
    },
  },
  
  extraReducers: (builder) => {
    // Fetch messages
    builder
      .addCase(fetchMessages.pending, (state) => {
        state.loading.fetch = true;
        state.error = null;
      })
      .addCase(fetchMessages.fulfilled, (state, action) => {
        state.loading.fetch = false;
        const { conversationId, messages } = action.payload;
        
        // Trier les messages par date de création
        const sortedMessages = messages.sort(
          (a, b) => new Date(a.created_at) - new Date(b.created_at)
        );
        
        state.messagesByConversation[conversationId] = sortedMessages;
        state.lastFetch = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchMessages.rejected, (state, action) => {
        state.loading.fetch = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Send message
    builder
      .addCase(sendMessage.pending, (state) => {
        state.loading.send = true;
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.loading.send = false;
        const { conversationId, message } = action.payload;
        
        if (!state.messagesByConversation[conversationId]) {
          state.messagesByConversation[conversationId] = [];
        }
        
        // Remplacer le message optimiste ou ajouter le nouveau message
        const tempMessages = state.messagesByConversation[conversationId].filter(
          msg => !msg.id.toString().startsWith('temp_')
        );
        
        tempMessages.push(message);
        
        // Trier par date de création
        state.messagesByConversation[conversationId] = tempMessages.sort(
          (a, b) => new Date(a.created_at) - new Date(b.created_at)
        );
        
        state.lastSent = new Date().toISOString();
        state.currentMessage = initialState.currentMessage;
        state.error = null;
        
        // Mettre à jour les statistiques
        state.stats.totalMessages += 1;
        if (message.token_count) {
          state.stats.totalTokens += message.token_count;
        }
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.loading.send = false;
        state.error = action.payload;
        state.lastError = action.payload;
        
        // Supprimer les messages optimistes en cas d'erreur
        Object.keys(state.messagesByConversation).forEach(conversationId => {
          state.messagesByConversation[conversationId] = 
            state.messagesByConversation[conversationId].filter(
              msg => !msg.id.toString().startsWith('temp_')
            );
        });
      });
    
    // Fetch all messages
    builder
      .addCase(fetchAllMessages.pending, (state) => {
        state.loading.fetchAll = true;
        state.error = null;
      })
      .addCase(fetchAllMessages.fulfilled, (state, action) => {
        state.loading.fetchAll = false;
        state.allMessages = action.payload.messages;
        state.error = null;
        
        // Mettre à jour les statistiques
        state.stats.totalMessages = action.payload.messages.length;
        state.stats.totalTokens = action.payload.messages.reduce(
          (total, msg) => total + (msg.token_count || 0), 0
        );
      })
      .addCase(fetchAllMessages.rejected, (state, action) => {
        state.loading.fetchAll = false;
        state.error = action.payload;
        state.lastError = action.payload;
      });
    
    // Fetch message
    builder
      .addCase(fetchMessage.fulfilled, (state, action) => {
        const message = action.payload;
        
        // Mettre à jour le message dans la conversation appropriée
        if (message.conversation) {
          const conversationId = message.conversation;
          
          if (state.messagesByConversation[conversationId]) {
            const index = state.messagesByConversation[conversationId].findIndex(
              msg => msg.id === message.id
            );
            
            if (index !== -1) {
              state.messagesByConversation[conversationId][index] = message;
            } else {
              state.messagesByConversation[conversationId].push(message);
              
              // Trier par date de création
              state.messagesByConversation[conversationId].sort(
                (a, b) => new Date(a.created_at) - new Date(b.created_at)
              );
            }
          }
        }
      });
  },
});

// Export des actions
export const {
  setCurrentMessage,
  clearCurrentMessage,
  updateCurrentMessageContent,
  optimisticAddMessage,
  updateOptimisticMessage,
  removeOptimisticMessage,
  setRealTimeStatus,
  updateHeartbeat,
  updateStats,
  clearError,
  addRealTimeMessage,
} = messagesSlice.actions;

// Sélecteurs
export const selectMessagesByConversation = (conversationId) => (state) =>
  state.messages.messagesByConversation[conversationId] || [];

export const selectAllMessages = (state) => state.messages.allMessages;
export const selectCurrentMessage = (state) => state.messages.currentMessage;
export const selectMessagesLoading = (state) => state.messages.loading;
export const selectMessagesError = (state) => state.messages.error;
export const selectRealTimeStatus = (state) => state.messages.realTime;
export const selectMessagesStats = (state) => state.messages.stats;

// Sélecteurs composés
export const selectLastMessageInConversation = (conversationId) => (state) => {
  const messages = state.messages.messagesByConversation[conversationId] || [];
  return messages.length > 0 ? messages[messages.length - 1] : null;
};

export const selectIsMessageLoading = (state) =>
  Object.values(state.messages.loading || {}).some(loading => loading);

export const selectMessageCount = (conversationId) => (state) =>
  (state.messages.messagesByConversation[conversationId] || []).length;

export default messagesSlice.reducer;
