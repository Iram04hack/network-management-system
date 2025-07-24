/**
 * Composant d'affichage des événements temps réel
 * Affiche les événements GNS3, monitoring et alertes en temps réel
 */
import React, { useState, useEffect } from 'react';
import { useGNS3WebSocket, useMonitoringWebSocket, useAlertsWebSocket } from '../../hooks/useWebSocket';

const RealtimeEvents = ({ className = '' }) => {
  const [events, setEvents] = useState([]);
  const [maxEvents, setMaxEvents] = useState(50);
  const [filter, setFilter] = useState('all');
  const [isAutoScroll, setIsAutoScroll] = useState(true);

  // Connexions WebSocket
  const gns3WS = useGNS3WebSocket('events', {
    debug: false,
    autoReconnect: true,
    onMessage: (data) => addEvent('GNS3', data)
  });

  const monitoringWS = useMonitoringWebSocket('general', null, {
    debug: false,
    autoReconnect: true,
    onMessage: (data) => addEvent('Monitoring', data)
  });

  const alertsWS = useAlertsWebSocket({
    debug: false,
    autoReconnect: true,
    onMessage: (data) => addEvent('Alerts', data)
  });

  const addEvent = (source, data) => {
    const event = {
      id: Date.now() + Math.random(),
      source,
      data,
      timestamp: new Date(),
      type: data.type || 'unknown'
    };

    setEvents(prev => {
      const newEvents = [event, ...prev].slice(0, maxEvents);
      return newEvents;
    });
  };

  const filteredEvents = events.filter(event => {
    if (filter === 'all') return true;
    return event.source.toLowerCase() === filter.toLowerCase();
  });

  const getEventColor = (source) => {
    switch (source) {
      case 'GNS3':
        return 'border-l-green-500 bg-green-50';
      case 'Monitoring':
        return 'border-l-blue-500 bg-blue-50';
      case 'Alerts':
        return 'border-l-red-500 bg-red-50';
      default:
        return 'border-l-gray-500 bg-gray-50';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'gns3_event':
        return '🔧';
      case 'metrics_update':
        return '📊';
      case 'alert_notification':
        return '⚠️';
      case 'connection_established':
        return '🔗';
      case 'heartbeat_ack':
        return '💗';
      default:
        return '📝';
    }
  };

  const clearEvents = () => {
    setEvents([]);
  };

  const exportEvents = () => {
    const dataStr = JSON.stringify(filteredEvents, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `websocket-events-${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Auto-scroll vers le nouveau contenu
  useEffect(() => {
    if (isAutoScroll) {
      const container = document.getElementById('events-container');
      if (container) {
        container.scrollTop = 0;
      }
    }
  }, [events, isAutoScroll]);

  return (
    <div className={`bg-white shadow rounded-lg ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            Événements Temps Réel
          </h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">
              {filteredEvents.length} événements
            </span>
            <div className="flex space-x-1">
              <span className={`inline-block w-2 h-2 rounded-full ${gns3WS.isConnected ? 'bg-green-500' : 'bg-gray-300'}`} title="GNS3"></span>
              <span className={`inline-block w-2 h-2 rounded-full ${monitoringWS.isConnected ? 'bg-blue-500' : 'bg-gray-300'}`} title="Monitoring"></span>
              <span className={`inline-block w-2 h-2 rounded-full ${alertsWS.isConnected ? 'bg-red-500' : 'bg-gray-300'}`} title="Alerts"></span>
            </div>
          </div>
        </div>

        {/* Filtres et contrôles */}
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div>
              <label className="text-sm text-gray-700 mr-2">Filtre:</label>
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="all">Tous</option>
                <option value="gns3">GNS3</option>
                <option value="monitoring">Monitoring</option>
                <option value="alerts">Alertes</option>
              </select>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="auto-scroll"
                checked={isAutoScroll}
                onChange={(e) => setIsAutoScroll(e.target.checked)}
                className="mr-2"
              />
              <label htmlFor="auto-scroll" className="text-sm text-gray-700">
                Auto-scroll
              </label>
            </div>

            <div>
              <label className="text-sm text-gray-700 mr-2">Max:</label>
              <select
                value={maxEvents}
                onChange={(e) => setMaxEvents(parseInt(e.target.value))}
                className="text-sm border border-gray-300 rounded px-2 py-1"
              >
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
                <option value="200">200</option>
              </select>
            </div>
          </div>

          <div className="flex space-x-2">
            <button
              onClick={exportEvents}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
              disabled={filteredEvents.length === 0}
            >
              Exporter
            </button>
            <button
              onClick={clearEvents}
              className="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600"
              disabled={events.length === 0}
            >
              Vider
            </button>
          </div>
        </div>
      </div>

      {/* Liste des événements */}
      <div 
        id="events-container"
        className="max-h-96 overflow-y-auto"
      >
        {filteredEvents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <div className="text-4xl mb-2">📡</div>
            <div>Aucun événement en temps réel</div>
            <div className="text-sm mt-1">
              Les connexions WebSocket afficheront les événements ici
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {filteredEvents.map((event) => (
              <div
                key={event.id}
                className={`p-3 border-l-4 ${getEventColor(event.source)}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    <span className="text-lg">
                      {getTypeIcon(event.type)}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-medium text-gray-900">
                          {event.source}
                        </span>
                        <span className="text-sm text-gray-500">
                          {event.type}
                        </span>
                      </div>
                      <div className="text-sm text-gray-700 mb-2">
                        {event.data.message || event.data.type || 'Données reçues'}
                      </div>
                      <details className="text-xs">
                        <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                          Voir données complètes
                        </summary>
                        <pre className="mt-2 p-2 bg-gray-100 rounded overflow-x-auto text-xs">
                          {JSON.stringify(event.data, null, 2)}
                        </pre>
                      </details>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 ml-4">
                    {event.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer avec statistiques */}
      <div className="px-4 py-2 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between text-xs text-gray-600">
          <div className="flex space-x-4">
            <span>GNS3: {events.filter(e => e.source === 'GNS3').length}</span>
            <span>Monitoring: {events.filter(e => e.source === 'Monitoring').length}</span>
            <span>Alertes: {events.filter(e => e.source === 'Alerts').length}</span>
          </div>
          <div>
            Dernière mise à jour: {events.length > 0 ? events[0].timestamp.toLocaleTimeString() : 'Jamais'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealtimeEvents;