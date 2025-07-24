/**
 * Hook WebSocket avancé pour données temps réel GNS3 et monitoring
 * Supporte reconnexion automatique, filtrage des événements, et gestion d'erreurs robuste
 */
import { useState, useEffect, useRef, useCallback } from 'react';

// Configuration par défaut pour les WebSockets
const DEFAULT_CONFIG = {
  autoReconnect: true,
  maxReconnectAttempts: 5,
  reconnectInterval: 3000,
  heartbeatInterval: 30000,
  connectionTimeout: 10000,
  debug: false
};

// URLs WebSocket disponibles
export const WEBSOCKET_ENDPOINTS = {
  // GNS3 WebSockets
  gns3: {
    events: '/ws/gns3/events/',
    topology: '/ws/gns3/topology/',
    nodes: '/ws/gns3/nodes/',
    module: (moduleName) => `/ws/gns3/module/${moduleName}/`,
    room: (roomName) => `/ws/gns3/events/${roomName}/`
  },
  // Monitoring WebSockets
  monitoring: {
    general: '/ws/monitoring/',
    device: (deviceId) => `/ws/monitoring/device/${deviceId}/`,
    alerts: '/ws/monitoring/alerts/',
    metrics: '/ws/monitoring/metrics/'
  },
  // Dashboard WebSockets
  dashboard: {
    general: '/ws/dashboard/',
    topology: (topologyId) => `/ws/dashboard/topology/${topologyId}/`
  }
};

/**
 * Hook WebSocket principal avec fonctionnalités avancées
 */
export const useWebSocket = (url, options = {}) => {
  const config = { ...DEFAULT_CONFIG, ...options };
  
  // États principaux
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const [connectionState, setConnectionState] = useState('disconnected');
  const [lastMessage, setLastMessage] = useState(null);
  const [messageHistory, setMessageHistory] = useState([]);
  const [stats, setStats] = useState({
    messagesReceived: 0,
    messagesSent: 0,
    reconnectAttempts: 0,
    lastReconnect: null,
    uptime: null,
    errors: []
  });

  // Références
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const heartbeatIntervalRef = useRef(null);
  const connectionTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const connectionStartTimeRef = useRef(null);

  // Callbacks configurables
  const {
    onMessage = null,
    onOpen = null,
    onClose = null,
    onError = null,
    onReconnect = null,
    messageFilter = null
  } = options;

  /**
   * Log de debug conditionnel
   */
  const debugLog = useCallback((message, ...args) => {
    if (config.debug) {
      console.log(`[WebSocket ${url}]`, message, ...args);
    }
  }, [config.debug, url]);

  /**
   * Met à jour les statistiques
   */
  const updateStats = useCallback((update) => {
    setStats(prev => ({ ...prev, ...update }));
  }, []);

  /**
   * Nettoie les timeouts et intervals
   */
  const cleanup = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
      heartbeatIntervalRef.current = null;
    }
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }
  }, []);

  /**
   * Démarre le heartbeat pour maintenir la connexion
   */
  const startHeartbeat = useCallback(() => {
    if (config.heartbeatInterval > 0 && !heartbeatIntervalRef.current) {
      heartbeatIntervalRef.current = setInterval(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) {
          sendMessage({ type: 'heartbeat', timestamp: new Date().toISOString() });
        }
      }, config.heartbeatInterval);
    }
  }, [config.heartbeatInterval]);

  /**
   * Établit la connexion WebSocket
   */
  const connect = useCallback(() => {
    if (!url || socketRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    cleanup();
    setIsConnecting(true);
    setConnectionState('connecting');
    connectionStartTimeRef.current = Date.now();

    debugLog('Tentative de connexion...', { url, attempts: reconnectAttemptsRef.current });

    try {
      // Construction de l'URL WebSocket
      const wsUrl = url.startsWith('ws') ? url : `ws://localhost:8000${url}`;
      socketRef.current = new WebSocket(wsUrl);

      // Timeout de connexion
      connectionTimeoutRef.current = setTimeout(() => {
        if (socketRef.current?.readyState === WebSocket.CONNECTING) {
          debugLog('Timeout de connexion');
          socketRef.current.close();
          setError(new Error('Timeout de connexion WebSocket'));
          setIsConnecting(false);
          setConnectionState('error');
        }
      }, config.connectionTimeout);

      // Gestionnaire d'ouverture
      socketRef.current.onopen = (event) => {
        debugLog('Connexion établie');
        cleanup();
        setIsConnected(true);
        setIsConnecting(false);
        setError(null);
        setConnectionState('connected');
        reconnectAttemptsRef.current = 0;
        
        updateStats({
          uptime: Date.now(),
          lastReconnect: reconnectAttemptsRef.current > 0 ? new Date().toISOString() : null
        });

        startHeartbeat();
        
        if (onOpen) onOpen(event);
      };

      // Gestionnaire de messages
      socketRef.current.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          
          // Filtrage des messages si configuré
          if (messageFilter && !messageFilter(parsedData)) {
            return;
          }

          // Mise à jour des données et historique
          setData(parsedData);
          setLastMessage({
            data: parsedData,
            timestamp: new Date().toISOString(),
            raw: event.data
          });

          setMessageHistory(prev => {
            const newHistory = [parsedData, ...prev].slice(0, 100); // Garder les 100 derniers
            return newHistory;
          });

          updateStats({
            messagesReceived: stats.messagesReceived + 1
          });

          debugLog('Message reçu:', parsedData);
          
          if (onMessage) onMessage(parsedData, event);
        } catch (err) {
          debugLog('Erreur parsing message:', err, event.data);
          setData(event.data); // Garder le message brut si parsing échoue
          
          if (onMessage) onMessage(event.data, event);
        }
      };

      // Gestionnaire d'erreurs
      socketRef.current.onerror = (event) => {
        debugLog('Erreur WebSocket:', event);
        const errorObj = new Error('Erreur de connexion WebSocket');
        setError(errorObj);
        setIsConnected(false);
        setIsConnecting(false);
        setConnectionState('error');
        
        updateStats({
          errors: [...stats.errors, {
            timestamp: new Date().toISOString(),
            error: errorObj.message,
            event
          }].slice(-10) // Garder les 10 dernières erreurs
        });

        if (onError) onError(errorObj, event);
      };

      // Gestionnaire de fermeture
      socketRef.current.onclose = (event) => {
        debugLog('Connexion fermée:', { code: event.code, reason: event.reason, wasClean: event.wasClean });
        
        cleanup();
        setIsConnected(false);
        setIsConnecting(false);
        setConnectionState(event.wasClean ? 'disconnected' : 'error');

        if (onClose) onClose(event);

        // Reconnexion automatique si activée et si ce n'est pas une fermeture propre
        if (config.autoReconnect && !event.wasClean && reconnectAttemptsRef.current < config.maxReconnectAttempts) {
          const delay = Math.min(config.reconnectInterval * Math.pow(2, reconnectAttemptsRef.current), 30000);
          debugLog(`Reconnexion dans ${delay}ms (tentative ${reconnectAttemptsRef.current + 1}/${config.maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current++;
            updateStats({ reconnectAttempts: reconnectAttemptsRef.current });
            if (onReconnect) onReconnect(reconnectAttemptsRef.current);
            connect();
          }, delay);
        }
      };

    } catch (err) {
      debugLog('Erreur lors de la création du WebSocket:', err);
      setError(err);
      setIsConnecting(false);
      setConnectionState('error');
    }
  }, [url, config, debugLog, cleanup, startHeartbeat, updateStats, onOpen, onMessage, onError, onClose, onReconnect, messageFilter, stats.messagesReceived, stats.errors]);

  /**
   * Ferme la connexion WebSocket
   */
  const disconnect = useCallback(() => {
    debugLog('Fermeture manuelle de la connexion');
    cleanup();
    reconnectAttemptsRef.current = config.maxReconnectAttempts; // Empêche la reconnexion auto
    
    if (socketRef.current) {
      socketRef.current.close(1000, 'Déconnexion manuelle');
      socketRef.current = null;
    }
    
    setIsConnected(false);
    setIsConnecting(false);
    setConnectionState('disconnected');
  }, [cleanup, config.maxReconnectAttempts, debugLog]);

  /**
   * Reconnecte manuellement
   */
  const reconnect = useCallback(() => {
    debugLog('Reconnexion manuelle');
    reconnectAttemptsRef.current = 0;
    disconnect();
    setTimeout(connect, 100);
  }, [connect, disconnect, debugLog]);

  /**
   * Envoie un message via WebSocket
   */
  const sendMessage = useCallback((message) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      try {
        const msgString = typeof message === 'string' ? message : JSON.stringify(message);
        socketRef.current.send(msgString);
        
        updateStats({
          messagesSent: stats.messagesSent + 1
        });
        
        debugLog('Message envoyé:', message);
        return true;
      } catch (err) {
        debugLog('Erreur envoi message:', err);
        setError(err);
        return false;
      }
    } else {
      debugLog('WebSocket non connecté, impossible d\'envoyer le message:', message);
      return false;
    }
  }, [debugLog, updateStats, stats.messagesSent]);

  /**
   * Vide l'historique des messages
   */
  const clearMessageHistory = useCallback(() => {
    setMessageHistory([]);
  }, []);

  /**
   * Réinitialise les statistiques
   */
  const resetStats = useCallback(() => {
    setStats({
      messagesReceived: 0,
      messagesSent: 0,
      reconnectAttempts: 0,
      lastReconnect: null,
      uptime: null,
      errors: []
    });
  }, []);

  // Connexion automatique au montage
  useEffect(() => {
    if (url) {
      connect();
    }

    return () => {
      cleanup();
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [url]);

  // Nettoyage au démontage
  useEffect(() => {
    return () => {
      cleanup();
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [cleanup]);

  return {
    // États principaux
    data,
    isConnected,
    isConnecting,
    error,
    connectionState,
    lastMessage,
    messageHistory,
    stats,

    // Actions
    sendMessage,
    connect,
    disconnect,
    reconnect,
    clearMessageHistory,
    resetStats,

    // Informations de connexion
    readyState: socketRef.current?.readyState || WebSocket.CLOSED,
    url: socketRef.current?.url || null,

    // Utilitaires
    isReady: isConnected && socketRef.current?.readyState === WebSocket.OPEN
  };
};

/**
 * Hook spécialisé pour les événements GNS3
 */
export const useGNS3WebSocket = (endpoint = 'events', options = {}) => {
  const url = typeof endpoint === 'string' 
    ? WEBSOCKET_ENDPOINTS.gns3[endpoint] || endpoint
    : endpoint;

  const [gns3Events, setGns3Events] = useState([]);
  const [nodeStatuses, setNodeStatuses] = useState(new Map());
  const [projectStatuses, setProjectStatuses] = useState(new Map());
  const [topologyData, setTopologyData] = useState(null);

  const handleGNS3Message = useCallback((data) => {
    const { type, event_type, event_data } = data;

    // Traitement spécifique des événements GNS3
    if (type === 'gns3_event' && event_data) {
      setGns3Events(prev => [event_data, ...prev.slice(0, 99)]);

      // Mise à jour des statuts selon le type d'événement
      switch (event_data.event_type) {
        case 'node.started':
        case 'node.stopped':
        case 'node.suspended':
          if (event_data.data?.node_id) {
            setNodeStatuses(prev => new Map(prev.set(event_data.data.node_id, {
              status: event_data.event_type.split('.')[1],
              lastUpdate: new Date().toISOString(),
              ...event_data.data
            })));
          }
          break;

        case 'project.opened':
        case 'project.closed':
          if (event_data.data?.project_id) {
            setProjectStatuses(prev => new Map(prev.set(event_data.data.project_id, {
              status: event_data.event_type.split('.')[1],
              lastUpdate: new Date().toISOString(),
              ...event_data.data
            })));
          }
          break;

        case 'topology.changed':
          setTopologyData(event_data.data);
          break;
      }
    } else if (type === 'topology_response') {
      setTopologyData(data.data);
    }
  }, []);

  const websocket = useWebSocket(url, {
    ...options,
    onMessage: handleGNS3Message
  });

  // Actions GNS3 spécifiques
  const subscribeToEvents = useCallback((eventTypes = ['all_events']) => {
    return websocket.sendMessage({
      type: 'subscribe',
      subscriptions: eventTypes
    });
  }, [websocket]);

  const unsubscribeFromEvents = useCallback((eventTypes) => {
    return websocket.sendMessage({
      type: 'unsubscribe',
      subscriptions: eventTypes
    });
  }, [websocket]);

  const requestTopology = useCallback(() => {
    return websocket.sendMessage({
      type: 'request_topology'
    });
  }, [websocket]);

  const performNodeAction = useCallback((action, projectId, nodeId) => {
    return websocket.sendMessage({
      type: 'node_action',
      action,
      project_id: projectId,
      node_id: nodeId
    });
  }, [websocket]);

  return {
    ...websocket,
    
    // Données GNS3 spécifiques
    gns3Events,
    nodeStatuses,
    projectStatuses,
    topologyData,

    // Actions GNS3
    subscribeToEvents,
    unsubscribeFromEvents,
    requestTopology,
    performNodeAction
  };
};

/**
 * Hook spécialisé pour le monitoring
 */
export const useMonitoringWebSocket = (endpoint = 'general', deviceId = null, options = {}) => {
  const url = deviceId 
    ? WEBSOCKET_ENDPOINTS.monitoring.device(deviceId)
    : WEBSOCKET_ENDPOINTS.monitoring[endpoint] || endpoint;

  const [metrics, setMetrics] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [systemStatus, setSystemStatus] = useState(null);

  const handleMonitoringMessage = useCallback((data) => {
    const { type } = data;

    switch (type) {
      case 'metrics_update':
        setMetrics(prev => [data, ...prev.slice(0, 99)]);
        break;

      case 'alert_notification':
        setAlerts(prev => [data, ...prev.slice(0, 49)]);
        break;

      case 'global_update':
        setSystemStatus(data.stats);
        break;

      case 'device_status_update':
        // Mise à jour spécifique à un équipement
        break;
    }
  }, []);

  const websocket = useWebSocket(url, {
    ...options,
    onMessage: handleMonitoringMessage
  });

  // Actions monitoring spécifiques
  const getMetrics = useCallback((params = {}) => {
    return websocket.sendMessage({
      type: 'get_metrics',
      ...params
    });
  }, [websocket]);

  const getAlerts = useCallback((params = {}) => {
    return websocket.sendMessage({
      type: 'get_alerts',
      ...params
    });
  }, [websocket]);

  const subscribeToDevice = useCallback((deviceId) => {
    return websocket.sendMessage({
      type: 'subscribe',
      device_id: deviceId
    });
  }, [websocket]);

  return {
    ...websocket,
    
    // Données monitoring spécifiques
    metrics,
    alerts,
    systemStatus,

    // Actions monitoring
    getMetrics,
    getAlerts,
    subscribeToDevice
  };
};

/**
 * Hook spécialisé pour les alertes
 */
export const useAlertsWebSocket = (options = {}) => {
  const [alerts, setAlerts] = useState([]);
  const [alertHistory, setAlertHistory] = useState([]);

  const handleAlertMessage = useCallback((data) => {
    const { type } = data;

    switch (type) {
      case 'active_alerts':
        setAlerts(data.alerts || []);
        break;

      case 'new_alert':
        setAlerts(prev => [data.data, ...prev]);
        setAlertHistory(prev => [data.data, ...prev.slice(0, 199)]);
        break;

      case 'alert_acknowledged':
      case 'alert_dismissed':
        setAlerts(prev => prev.map(alert => 
          alert.id === data.data.alert_id 
            ? { ...alert, ...data.data }
            : alert
        ));
        break;
    }
  }, []);

  const websocket = useWebSocket(WEBSOCKET_ENDPOINTS.monitoring.alerts, {
    ...options,
    onMessage: handleAlertMessage
  });

  // Actions d'alertes spécifiques
  const acknowledgeAlert = useCallback((alertId, comment = '') => {
    return websocket.sendMessage({
      action: 'acknowledge',
      alert_id: alertId,
      comment
    });
  }, [websocket]);

  const dismissAlert = useCallback((alertId, reason = '') => {
    return websocket.sendMessage({
      action: 'dismiss',
      alert_id: alertId,
      reason
    });
  }, [websocket]);

  const getAlertDetails = useCallback((alertId) => {
    return websocket.sendMessage({
      action: 'get_details',
      alert_id: alertId
    });
  }, [websocket]);

  return {
    ...websocket,
    
    // Données d'alertes spécifiques
    alerts,
    alertHistory,

    // Actions d'alertes
    acknowledgeAlert,
    dismissAlert,
    getAlertDetails
  };
};

export default useWebSocket;