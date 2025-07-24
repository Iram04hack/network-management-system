/**
 * Slice Redux pour la gestion des commandes
 * Intégration avec le service AI Assistant validé Phase 1
 */

import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import aiAssistantService from '../../services/aiAssistantService';

const initialState = {
  commands: [],
  currentCommand: null,
  loading: {
    execute: false,
    fetch: false,
  },
  error: null,
  lastExecution: null,
  executionHistory: [],
};

// Exécuter une commande
export const executeCommand = createAsyncThunk(
  'commands/executeCommand',
  async (commandData, { rejectWithValue }) => {
    try {
      const result = await aiAssistantService.executeCommand(commandData);
      
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

const commandsSlice = createSlice({
  name: 'commands',
  initialState,
  reducers: {
    setCurrentCommand: (state, action) => {
      state.currentCommand = action.payload;
    },
    clearCurrentCommand: (state) => {
      state.currentCommand = null;
    },
    clearError: (state) => {
      state.error = null;
    },
    addToHistory: (state, action) => {
      state.executionHistory.unshift(action.payload);
      // Garder seulement les 50 dernières exécutions
      if (state.executionHistory.length > 50) {
        state.executionHistory = state.executionHistory.slice(0, 50);
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(executeCommand.pending, (state) => {
        state.loading.execute = true;
        state.error = null;
      })
      .addCase(executeCommand.fulfilled, (state, action) => {
        state.loading.execute = false;
        state.lastExecution = action.payload;
        state.executionHistory.unshift({
          ...action.payload,
          timestamp: new Date().toISOString(),
        });
        state.error = null;
      })
      .addCase(executeCommand.rejected, (state, action) => {
        state.loading.execute = false;
        state.error = action.payload;
      });
  },
});

export const { setCurrentCommand, clearCurrentCommand, clearError, addToHistory } = commandsSlice.actions;

export const selectCommands = (state) => state.commands.commands;
export const selectCurrentCommand = (state) => state.commands.currentCommand;
export const selectCommandsLoading = (state) => state.commands.loading;
export const selectCommandsError = (state) => state.commands.error;
export const selectLastExecution = (state) => state.commands.lastExecution;
export const selectExecutionHistory = (state) => state.commands.executionHistory;

export default commandsSlice.reducer;
