// ApiClients.jsx - Page dédiée à la gestion des clients API avec design moderne
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Settings, 
  Activity, 
  Zap, 
  AlertCircle, 
  CheckCircle, 
  XCircle, 
  RefreshCw,
  Search,
  Filter,
  Plus,
  Edit,
  Trash2,
  Play,
  Pause,
  Eye,
  Server,
  Globe,
  Shield,
  TrendingUp,
  TrendingDown,
  Clock,
  Network,
  MonitorSpeaker
} from 'lucide-react';

// Import des hooks backend pour les clients API AMÉLIORÉS
import { useTheme } from '../contexts/ThemeContext';

const ApiClients = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [viewMode, setViewMode] = useState('cards'); // 'cards' | 'table'
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [showConfig, setShowConfig] = useState(null);
  const [selectedClient, setSelectedClient] = useState(null);

  // Hook pour le thème
  const { getThemeClasses, getThemeColor } = useTheme();

  // États pour les données simulées (en attendant l'intégration backend)
  const [clients, setClients] = useState([
    {
      id: 1,
      name: 'GNS3-Server-Main',
      client_type: 'gns3',
      host: 'localhost',
      port: 3080,
      status: 'healthy',
      is_active: true,
      response_time: 45,
      last_test: new Date().toISOString(),
      test_passed: true
    },
    {
      id: 2,
      name: 'SNMP-Monitor',
      client_type: 'snmp',
      host: '192.168.1.100',
      port: 161,
      status: 'healthy',
      is_active: true,
      response_time: 23,
      last_test: new Date().toISOString(),
      test_passed: true
    },
    {
      id: 3,
      name: 'Prometheus-Metrics',
      client_type: 'prometheus',
      host: '192.168.1.110',
      port: 9090,
      status: 'unhealthy',
      is_active: true,
      response_time: null,
      last_test: new Date().toISOString(),
      test_passed: false
    },
    {
      id: 4,
      name: 'Grafana-Dashboard',
      client_type: 'grafana',
      host: '192.168.1.111',
      port: 3000,
      status: 'healthy',
      is_active: false,
      response_time: 67,
      last_test: new Date().toISOString(),
      test_passed: true
    }
  ]);
  const [loading, setLoading] = useState({
    fetch: false,
    test: false,
    update: false
  });
  const [error, setError] = useState(null);

  // Chargement initial des données (simulation)
  useEffect(() => {
    const loadClientsData = async () => {
      setLoading(prev => ({ ...prev, fetch: true }));
      
      // Simulation d'un délai de chargement
      setTimeout(() => {
        setLoading(prev => ({ ...prev, fetch: false }));
      }, 800);
    };

    loadClientsData();
  }, []);

  // Auto-refresh (simulation)
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulation de mise à jour des données
      setClients(prevClients => 
        prevClients.map(client => ({
          ...client,
          response_time: client.status === 'healthy' 
            ? Math.max(10, Math.min(100, (client.response_time || 50) + (Math.random() - 0.5) * 20))
            : null,
          last_test: new Date().toISOString()
        }))
      );
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Filtres et recherche
  const filteredClients = clients.filter(client => {
    const matchesSearch = client.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         client.client_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         client.host.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesType = filterType === 'all' || client.client_type === filterType;
    const matchesStatus = filterStatus === 'all' || client.status === filterStatus;
    
    return matchesSearch && matchesType && matchesStatus;
  });

  // Handlers
  const handleRefresh = useCallback(() => {
    setLoading(prev => ({ ...prev, fetch: true }));
    
    // Simulation de refresh
    setTimeout(() => {
      setLoading(prev => ({ ...prev, fetch: false }));
      setClients(prevClients => 
        prevClients.map(client => ({
          ...client,
          last_test: new Date().toISOString()
        }))
      );
    }, 800);
  }, []);

  const handleTestClient = async (clientId) => {
    setLoading(prev => ({ ...prev, test: true }));
    
    // Simulation de test
    setTimeout(() => {
      setLoading(prev => ({ ...prev, test: false }));
      setClients(prevClients => 
        prevClients.map(client => 
          client.id === clientId 
            ? { 
                ...client, 
                last_test: new Date().toISOString(),
                test_passed: Math.random() > 0.2, // 80% de succès
                response_time: client.status === 'healthy' ? Math.floor(Math.random() * 80) + 20 : null
              }
            : client
        )
      );
    }, 1500);
  };

  const clearError = () => {
    setError(null);
  };

  // Statistiques calculées
  const stats = {
    total: clients.length,
    active: clients.filter(c => c.is_active).length,
    healthy: clients.filter(c => c.status === 'healthy').length
  };
  const activeClients = clients.filter(c => c.is_active);
  const unhealthyClients = clients.filter(c => c.status === 'unhealthy');

  // Types de clients avec leurs configurations
  const clientTypes = {
    gns3: { name: 'GNS3', icon: Network, color: 'text-blue-500', bgColor: 'bg-blue-50 dark:bg-blue-900/20' },
    snmp: { name: 'SNMP', icon: MonitorSpeaker, color: 'text-green-500', bgColor: 'bg-green-50 dark:bg-green-900/20' },
    prometheus: { name: 'Prometheus', icon: Activity, color: 'text-orange-500', bgColor: 'bg-orange-50 dark:bg-orange-900/20' },
    grafana: { name: 'Grafana', icon: TrendingUp, color: 'text-purple-500', bgColor: 'bg-purple-50 dark:bg-purple-900/20' },
    elasticsearch: { name: 'Elasticsearch', icon: Search, color: 'text-cyan-500', bgColor: 'bg-cyan-50 dark:bg-cyan-900/20' },
    fail2ban: { name: 'Fail2Ban', icon: Shield, color: 'text-red-500', bgColor: 'bg-red-50 dark:bg-red-900/20' },
    haproxy: { name: 'HAProxy', icon: Globe, color: 'text-indigo-500', bgColor: 'bg-indigo-50 dark:bg-indigo-900/20' },
    netflow: { name: 'NetFlow', icon: Server, color: 'text-pink-500', bgColor: 'bg-pink-50 dark:bg-pink-900/20' }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'unhealthy': return <XCircle className="w-4 h-4 text-red-500" />;
      default: return <AlertCircle className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const configs = {
      healthy: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      unhealthy: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
      unknown: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
    };
    
    return configs[status] || configs.unknown;
  };

  // Rendu des cartes de clients
  const ClientCard = ({ client }) => {
    const clientConfig = clientTypes[client.client_type] || clientTypes.gns3;
    const IconComponent = clientConfig.icon;

    return (
      <div className={`${getThemeClasses('card', 'apiClients')} p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200`}>
        {/* En-tête de la carte */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${clientConfig.bgColor}`}>
              <IconComponent className={`w-5 h-5 ${clientConfig.color}`} />
            </div>
            <div>
              <h3 className={`font-semibold ${getThemeClasses('textPrimary', 'apiClients')}`}>
                {client.name}
              </h3>
              <p className={`text-sm ${getThemeClasses('textSecondary', 'apiClients')}`}>
                {clientConfig.name}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-1">
            {getStatusIcon(client.status)}
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(client.status)}`}>
              {client.status === 'healthy' ? 'Sain' : client.status === 'unhealthy' ? 'Défaillant' : 'Inconnu'}
            </span>
          </div>
        </div>

        {/* Informations de connexion */}
        <div className="space-y-2 mb-4">
          <div className="flex items-center justify-between">
            <span className={`text-sm ${getThemeClasses('textSecondary', 'apiClients')}`}>
              Adresse:
            </span>
            <span className={`text-sm font-mono ${getThemeClasses('textPrimary', 'apiClients')}`}>
              {client.host}:{client.port}
            </span>
          </div>
          
          {client.response_time && (
            <div className="flex items-center justify-between">
              <span className={`text-sm ${getThemeClasses('textSecondary', 'apiClients')}`}>
                Temps de réponse:
              </span>
              <span className={`text-sm ${getThemeClasses('textPrimary', 'apiClients')}`}>
                {client.response_time}ms
              </span>
            </div>
          )}

          {client.last_test && (
            <div className="flex items-center justify-between">
              <span className={`text-sm ${getThemeClasses('textSecondary', 'apiClients')}`}>
                Dernier test:
              </span>
              <span className={`text-sm ${getThemeClasses('textPrimary', 'apiClients')}`}>
                {new Date(client.last_test).toLocaleString()}
              </span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => handleTestClient(client.id)}
              disabled={loading.test}
              className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm font-medium transition-colors ${getThemeClasses('buttonPrimary', 'apiClients')} hover:opacity-90 disabled:opacity-50`}
            >
              <Zap className="w-4 h-4" />
              <span>Tester</span>
            </button>
            
            <button 
              onClick={() => setSelectedClient(client)}
              className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm font-medium transition-colors ${getThemeClasses('buttonSecondary', 'apiClients')} hover:opacity-90`}
            >
              <Eye className="w-4 h-4" />
              <span>Détails</span>
            </button>
          </div>
          
          <div className="flex items-center space-x-2">
            <button 
              onClick={() => setShowConfig(client)}
              className={`p-1 rounded-md transition-colors ${getThemeClasses('buttonGhost', 'apiClients')} hover:opacity-90`}
            >
              <Settings className="w-4 h-4" />
            </button>
            
            <div className={`flex items-center ${client.is_active ? 'text-green-500' : 'text-gray-400'}`}>
              {client.is_active ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* En-tête avec statistiques */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className={`${getThemeClasses('card', 'apiClients')} p-6 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${getThemeClasses('textSecondary', 'apiClients')}`}>
                Total Clients
              </p>
              <p className={`text-2xl font-bold ${getThemeClasses('textPrimary', 'apiClients')}`}>
                {stats.total || 0}
              </p>
            </div>
            <Server className={`w-8 h-8 ${getThemeClasses('textSecondary', 'apiClients')}`} />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'apiClients')} p-6 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${getThemeClasses('textSecondary', 'apiClients')}`}>
                Clients Actifs
              </p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {stats.active || 0}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'apiClients')} p-6 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${getThemeClasses('textSecondary', 'apiClients')}`}>
                Clients Sains
              </p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {stats.healthy || 0}
              </p>
            </div>
            <Activity className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'apiClients')} p-6 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${getThemeClasses('textSecondary', 'apiClients')}`}>
                Problèmes
              </p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {unhealthyClients.length}
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Alertes d'erreur */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Erreur de connexion
              </h3>
              <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                {error.message || 'Une erreur est survenue lors de la communication avec les clients API'}
              </p>
            </div>
            <button 
              onClick={clearError}
              className="ml-auto text-red-400 hover:text-red-600"
            >
              <XCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Contrôles et filtres */}
      <div className={`${getThemeClasses('card', 'apiClients')} p-6 rounded-lg`}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher clients..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${getThemeClasses('input', 'apiClients')}`}
              />
            </div>
            
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className={`px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${getThemeClasses('input', 'apiClients')}`}
            >
              <option value="all">Tous types</option>
              {Object.entries(clientTypes).map(([key, config]) => (
                <option key={key} value={key}>{config.name}</option>
              ))}
            </select>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className={`px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${getThemeClasses('input', 'apiClients')}`}
            >
              <option value="all">Tous statuts</option>
              <option value="healthy">Sains</option>
              <option value="unhealthy">Défaillants</option>
              <option value="unknown">Inconnus</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoRefresh"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="autoRefresh" className={`text-sm ${getThemeClasses('textSecondary', 'apiClients')}`}>
                Refresh auto
              </label>
            </div>
            
            <button
              onClick={handleRefresh}
              disabled={loading.fetch}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${getThemeClasses('buttonPrimary', 'apiClients')} hover:opacity-90 disabled:opacity-50`}
            >
              <RefreshCw className={`w-4 h-4 ${loading.fetch ? 'animate-spin' : ''}`} />
              <span>Actualiser</span>
            </button>
          </div>
        </div>
      </div>

      {/* Liste des clients */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading.fetch ? (
          Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className={`${getThemeClasses('card', 'apiClients')} p-6 rounded-lg animate-pulse`}>
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 bg-gray-300 dark:bg-gray-600 rounded-lg"></div>
                <div className="flex-1">
                  <div className="h-4 bg-gray-300 dark:bg-gray-600 rounded mb-2"></div>
                  <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-2/3"></div>
                </div>
              </div>
              <div className="space-y-2">
                <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded"></div>
                <div className="h-3 bg-gray-300 dark:bg-gray-600 rounded w-3/4"></div>
              </div>
            </div>
          ))
        ) : filteredClients.length > 0 ? (
          filteredClients.map(client => (
            <ClientCard key={client.id} client={client} />
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <Server className={`w-16 h-16 mx-auto ${getThemeClasses('textSecondary', 'apiClients')} mb-4`} />
            <h3 className={`text-lg font-medium ${getThemeClasses('textPrimary', 'apiClients')} mb-2`}>
              Aucun client trouvé
            </h3>
            <p className={`${getThemeClasses('textSecondary', 'apiClients')}`}>
              {searchQuery || filterType !== 'all' || filterStatus !== 'all' 
                ? 'Aucun client ne correspond aux critères de recherche'
                : 'Aucun client API configuré'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiClients;