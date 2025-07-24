/**
 * Page de test des WebSockets
 * Permet de tester les connexions temps réel et visualiser les événements
 */
import React, { useState, useEffect } from 'react';
import { WebSocketStatus, RealtimeEvents } from '../components/websocket';
import useMonitoring from '../hooks/useMonitoring';
import useGNS3 from '../hooks/useGNS3';
import useDashboard from '../hooks/useDashboard';

const WebSocketTest = () => {
  const [activeTab, setActiveTab] = useState('status');

  // Hooks avec WebSocket intégrés
  const monitoring = useMonitoring();
  const gns3 = useGNS3();
  const dashboard = useDashboard();

  // Activation automatique du temps réel pour les tests
  useEffect(() => {
    // Activer le monitoring temps réel
    monitoring.enableRealTime(true, 30000);
    
    return () => {
      // Désactiver à la fermeture
      monitoring.enableRealTime(false);
    };
  }, []);

  const tabs = [
    { id: 'status', label: 'Statut WebSocket', icon: '🔗' },
    { id: 'events', label: 'Événements', icon: '📡' },
    { id: 'monitoring', label: 'Monitoring', icon: '📊' },
    { id: 'gns3', label: 'GNS3', icon: '🔧' },
    { id: 'dashboard', label: 'Dashboard', icon: '📋' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'status':
        return <WebSocketStatus className="w-full" />;
      
      case 'events':
        return <RealtimeEvents className="w-full" />;
      
      case 'monitoring':
        return (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Monitoring WebSocket Status
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 p-4 rounded">
                  <h4 className="font-medium text-gray-700 mb-2">Connexion Monitoring</h4>
                  <div className="space-y-1 text-sm">
                    <div>État: <span className={`font-medium ${monitoring.webSocket?.monitoring.isConnected ? 'text-green-600' : 'text-red-600'}`}>
                      {monitoring.webSocket?.monitoring.connectionState || 'disconnected'}
                    </span></div>
                    <div>Messages reçus: {monitoring.webSocket?.monitoring.stats?.messagesReceived || 0}</div>
                    <div>Messages envoyés: {monitoring.webSocket?.monitoring.stats?.messagesSent || 0}</div>
                    <div>Tentatives reconnexion: {monitoring.webSocket?.monitoring.stats?.reconnectAttempts || 0}</div>
                  </div>
                </div>
                
                <div className="bg-gray-50 p-4 rounded">
                  <h4 className="font-medium text-gray-700 mb-2">Connexion Alertes</h4>
                  <div className="space-y-1 text-sm">
                    <div>État: <span className={`font-medium ${monitoring.webSocket?.alerts.isConnected ? 'text-green-600' : 'text-red-600'}`}>
                      {monitoring.webSocket?.alerts.connectionState || 'disconnected'}
                    </span></div>
                    <div>Messages reçus: {monitoring.webSocket?.alerts.stats?.messagesReceived || 0}</div>
                    <div>Messages envoyés: {monitoring.webSocket?.alerts.stats?.messagesSent || 0}</div>
                    <div>Alertes actives: {monitoring.webSocket?.alerts.alerts?.length || 0}</div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Métriques Temps Réel</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-blue-50 p-3 rounded">
                      <div className="text-sm text-gray-600">CPU</div>
                      <div className="text-xl font-bold text-blue-600">
                        {monitoring.currentCpuUsage?.toFixed(1) || 0}%
                      </div>
                    </div>
                    <div className="bg-green-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Mémoire</div>
                      <div className="text-xl font-bold text-green-600">
                        {monitoring.currentMemoryUsage?.toFixed(1) || 0}%
                      </div>
                    </div>
                    <div className="bg-purple-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Réseau</div>
                      <div className="text-xl font-bold text-purple-600">
                        {monitoring.currentNetworkUsage?.toFixed(1) || 0} MB
                      </div>
                    </div>
                    <div className="bg-orange-50 p-3 rounded">
                      <div className="text-sm text-gray-600">Disque</div>
                      <div className="text-xl font-bold text-orange-600">
                        {monitoring.currentDiskUsage?.toFixed(1) || 0}%
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Actions de Test</h4>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => monitoring.webSocket?.monitoring.actions.getMetrics()}
                      className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
                      disabled={!monitoring.webSocket?.monitoring.isConnected}
                    >
                      Demander Métriques
                    </button>
                    <button
                      onClick={() => monitoring.webSocket?.alerts.actions.getAlertDetails(1)}
                      className="px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:bg-gray-300"
                      disabled={!monitoring.webSocket?.alerts.isConnected}
                    >
                      Test Détails Alerte
                    </button>
                    <button
                      onClick={() => monitoring.fetchRealTimeMetrics()}
                      className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                    >
                      Rafraîchir via API
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      
      case 'gns3':
        return (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                GNS3 WebSocket Status
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 p-4 rounded">
                  <h4 className="font-medium text-gray-700 mb-2">Connexion GNS3</h4>
                  <div className="space-y-1 text-sm">
                    <div>État: <span className={`font-medium ${gns3.webSocket?.isConnected ? 'text-green-600' : 'text-red-600'}`}>
                      {gns3.webSocket?.connectionState || 'disconnected'}
                    </span></div>
                    <div>Messages reçus: {gns3.webSocket?.stats?.messagesReceived || 0}</div>
                    <div>Messages envoyés: {gns3.webSocket?.stats?.messagesSent || 0}</div>
                    <div>Événements GNS3: {gns3.webSocket?.gns3Events?.length || 0}</div>
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded">
                  <h4 className="font-medium text-gray-700 mb-2">Statuts Nœuds/Projets</h4>
                  <div className="space-y-1 text-sm">
                    <div>Nœuds suivis: {gns3.webSocket?.nodeStatuses?.size || 0}</div>
                    <div>Projets suivis: {gns3.webSocket?.projectStatuses?.size || 0}</div>
                    <div>Serveurs: {gns3.servers.length}</div>
                    <div>Projets: {gns3.projects.length}</div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Actions de Test</h4>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => gns3.webSocket?.actions.subscribeToEvents(['all_events'])}
                      className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300"
                      disabled={!gns3.webSocket?.isConnected}
                    >
                      S'abonner aux événements
                    </button>
                    <button
                      onClick={() => gns3.webSocket?.actions.requestTopology()}
                      className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
                      disabled={!gns3.webSocket?.isConnected}
                    >
                      Demander Topologie
                    </button>
                    <button
                      onClick={() => gns3.fetchServers()}
                      className="px-3 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
                    >
                      Rafraîchir Serveurs
                    </button>
                    <button
                      onClick={() => gns3.fetchProjects()}
                      className="px-3 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
                    >
                      Rafraîchir Projets
                    </button>
                  </div>
                </div>

                {gns3.webSocket?.gns3Events && gns3.webSocket.gns3Events.length > 0 && (
                  <div>
                    <h4 className="font-medium text-gray-700 mb-2">Derniers événements GNS3</h4>
                    <div className="space-y-2 max-h-48 overflow-y-auto">
                      {gns3.webSocket.gns3Events.slice(0, 5).map((event, index) => (
                        <div key={index} className="p-2 bg-gray-50 rounded text-sm">
                          <div className="font-medium">{event.event_type}</div>
                          <div className="text-gray-600">{JSON.stringify(event.data)}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        );
      
      case 'dashboard':
        return (
          <div className="space-y-6">
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Dashboard WebSocket Status
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="bg-gray-50 p-4 rounded">
                  <h4 className="font-medium text-gray-700 mb-2">Connexion Dashboard</h4>
                  <div className="space-y-1 text-sm">
                    <div>État: <span className={`font-medium ${dashboard.webSocket?.isConnected ? 'text-green-600' : 'text-red-600'}`}>
                      {dashboard.webSocket?.connectionState || 'disconnected'}
                    </span></div>
                    <div>Messages reçus: {dashboard.webSocket?.stats?.messagesReceived || 0}</div>
                    <div>Messages envoyés: {dashboard.webSocket?.stats?.messagesSent || 0}</div>
                  </div>
                </div>

                <div className="bg-gray-50 p-4 rounded">
                  <h4 className="font-medium text-gray-700 mb-2">Données Dashboard</h4>
                  <div className="space-y-1 text-sm">
                    <div>Auto-refresh: {dashboard.autoRefresh ? 'Activé' : 'Désactivé'}</div>
                    <div>Intervalle: {dashboard.refreshInterval / 1000}s</div>
                    <div>Dernière MAJ: {dashboard.lastUpdate ? new Date(dashboard.lastUpdate).toLocaleTimeString() : 'Jamais'}</div>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-700 mb-2">Actions de Test</h4>
                  <div className="flex flex-wrap gap-2">
                    <button
                      onClick={() => dashboard.webSocket?.actions.sendMessage({ command: 'get_dashboard' })}
                      className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
                      disabled={!dashboard.webSocket?.isConnected}
                    >
                      Demander Dashboard
                    </button>
                    <button
                      onClick={() => dashboard.webSocket?.actions.sendMessage({ command: 'get_network_overview' })}
                      className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:bg-gray-300"
                      disabled={!dashboard.webSocket?.isConnected}
                    >
                      Aperçu Réseau
                    </button>
                    <button
                      onClick={() => dashboard.webSocket?.actions.sendMessage({ command: 'get_health_metrics' })}
                      className="px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:bg-gray-300"
                      disabled={!dashboard.webSocket?.isConnected}
                    >
                      Métriques Santé
                    </button>
                    <button
                      onClick={() => dashboard.refreshAllData(true)}
                      className="px-3 py-2 bg-purple-500 text-white rounded hover:bg-purple-600"
                    >
                      Rafraîchir via API
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Test WebSocket Temps Réel
                </h1>
                <p className="text-gray-600 mt-1">
                  Interface de test pour les connexions temps réel GNS3 et monitoring
                </p>
              </div>
              <div className="flex items-center space-x-2">
                <div className="text-sm text-gray-500">
                  Backend: {window.location.protocol === 'https:' ? 'wss' : 'ws'}://localhost:8000
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Onglets */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Contenu des onglets */}
        <div className="space-y-6">
          {renderTabContent()}
        </div>
      </div>
    </div>
  );
};

export default WebSocketTest;