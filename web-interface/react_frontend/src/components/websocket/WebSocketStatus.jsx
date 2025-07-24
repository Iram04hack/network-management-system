/**
 * Composant d'affichage du statut des WebSockets
 * Permet de visualiser l'état des connexions temps réel
 */
import React, { useState, useEffect } from 'react';
import { useGNS3WebSocket, useMonitoringWebSocket, useAlertsWebSocket } from '../../hooks/useWebSocket';

const WebSocketStatus = ({ className = '' }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Connexions WebSocket pour test
  const gns3WS = useGNS3WebSocket('events', {
    debug: false,
    autoReconnect: true
  });

  const monitoringWS = useMonitoringWebSocket('general', null, {
    debug: false,
    autoReconnect: true
  });

  const alertsWS = useAlertsWebSocket({
    debug: false,
    autoReconnect: true
  });

  const getStatusColor = (connectionState) => {
    switch (connectionState) {
      case 'connected':
        return 'text-green-500';
      case 'connecting':
        return 'text-yellow-500';
      case 'error':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  const getStatusIcon = (connectionState) => {
    switch (connectionState) {
      case 'connected':
        return '●';
      case 'connecting':
        return '◐';
      case 'error':
        return '●';
      default:
        return '○';
    }
  };

  const connections = [
    {
      name: 'GNS3 Events',
      ws: gns3WS,
      description: 'Événements en temps réel GNS3'
    },
    {
      name: 'Monitoring',
      ws: monitoringWS,
      description: 'Métriques système temps réel'
    },
    {
      name: 'Alerts',
      ws: alertsWS,
      description: 'Alertes temps réel'
    }
  ];

  return (
    <div className={`bg-white shadow rounded-lg p-4 ${className}`}>
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 className="text-lg font-medium text-gray-900">
          WebSocket Status
        </h3>
        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-500">
            {connections.filter(c => c.ws.isConnected).length}/{connections.length} connectés
          </span>
          <svg 
            className={`w-5 h-5 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-3">
          {connections.map((connection, index) => (
            <div key={index} className="border rounded p-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span 
                    className={`text-lg ${getStatusColor(connection.ws.connectionState)}`}
                  >
                    {getStatusIcon(connection.ws.connectionState)}
                  </span>
                  <div>
                    <div className="font-medium text-gray-900">
                      {connection.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      {connection.description}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-sm font-medium ${getStatusColor(connection.ws.connectionState)}`}>
                    {connection.ws.connectionState}
                  </div>
                  {connection.ws.isConnected && (
                    <div className="text-xs text-gray-500">
                      {connection.ws.stats.messagesReceived} msgs
                    </div>
                  )}
                </div>
              </div>

              {connection.ws.connectionState === 'error' && connection.ws.error && (
                <div className="mt-2 p-2 bg-red-50 rounded text-sm text-red-700">
                  Erreur: {connection.ws.error.message}
                </div>
              )}

              {connection.ws.isConnected && connection.ws.lastMessage && (
                <div className="mt-2 p-2 bg-blue-50 rounded">
                  <div className="text-xs text-gray-500 mb-1">
                    Dernier message ({new Date(connection.ws.lastMessage.timestamp).toLocaleTimeString()}):
                  </div>
                  <div className="text-xs font-mono text-blue-900 max-h-20 overflow-y-auto">
                    {JSON.stringify(connection.ws.lastMessage.data, null, 2)}
                  </div>
                </div>
              )}

              <div className="mt-2 flex space-x-2">
                {!connection.ws.isConnected && !connection.ws.isConnecting && (
                  <button
                    onClick={() => connection.ws.connect()}
                    className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600"
                  >
                    Connecter
                  </button>
                )}
                {connection.ws.isConnected && (
                  <button
                    onClick={() => connection.ws.disconnect()}
                    className="px-2 py-1 text-xs bg-red-500 text-white rounded hover:bg-red-600"
                  >
                    Déconnecter
                  </button>
                )}
                {connection.ws.isConnected && (
                  <button
                    onClick={() => connection.ws.reconnect()}
                    className="px-2 py-1 text-xs bg-yellow-500 text-white rounded hover:bg-yellow-600"
                  >
                    Reconnecter
                  </button>
                )}
              </div>
            </div>
          ))}

          <div className="mt-4 p-3 bg-gray-50 rounded">
            <h4 className="font-medium text-gray-900 mb-2">Actions de test</h4>
            <div className="space-y-2">
              <button
                onClick={() => {
                  if (gns3WS.isConnected) {
                    gns3WS.subscribeToEvents(['all_events']);
                  }
                }}
                className="w-full px-3 py-2 text-sm bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300"
                disabled={!gns3WS.isConnected}
              >
                S'abonner aux événements GNS3
              </button>
              
              <button
                onClick={() => {
                  if (gns3WS.isConnected) {
                    gns3WS.requestTopology();
                  }
                }}
                className="w-full px-3 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
                disabled={!gns3WS.isConnected}
              >
                Demander topologie GNS3
              </button>

              <button
                onClick={() => {
                  if (monitoringWS.isConnected) {
                    monitoringWS.getMetrics({ 
                      device_id: null, 
                      start_time: new Date(Date.now() - 3600000).toISOString() 
                    });
                  }
                }}
                className="w-full px-3 py-2 text-sm bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-gray-300"
                disabled={!monitoringWS.isConnected}
              >
                Demander métriques monitoring
              </button>

              <button
                onClick={() => {
                  if (alertsWS.isConnected) {
                    alertsWS.getAlertDetails(1);
                  }
                }}
                className="w-full px-3 py-2 text-sm bg-orange-500 text-white rounded hover:bg-orange-600 disabled:bg-gray-300"
                disabled={!alertsWS.isConnected}
              >
                Tester détails alerte
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WebSocketStatus;