// ApiViews.jsx - Page dédiée aux vues API avec design moderne Tailwind
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Eye, 
  Search, 
  Filter, 
  RefreshCw, 
  Activity, 
  AlertCircle, 
  CheckCircle, 
  TrendingUp, 
  TrendingDown,
  Network,
  Server,
  Globe,
  BarChart3,
  PieChart,
  Monitor,
  Database,
  Wifi,
  Shield,
  Clock,
  Users,
  Zap,
  Settings
} from 'lucide-react';

// Import des hooks backend pour les vues API AMÉLIORÉS
import { useTheme } from '../contexts/ThemeContext';

const ApiViews = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [timeRange, setTimeRange] = useState('24h');
  const [viewMode, setViewMode] = useState('overview');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [selectedDevice, setSelectedDevice] = useState(null);

  // Hook pour le thème
  const { getThemeClasses, getThemeColor } = useTheme();

  // États pour les données simulées (en attendant l'intégration backend)
  const [dashboardOverview, setDashboardOverview] = useState(null);
  const [systemOverview, setSystemOverview] = useState({
    cpu_usage: 45,
    memory_usage: 62,
    disk_usage: 78,
    overall_status: 'healthy'
  });
  const [networkOverview, setNetworkOverview] = useState(null);
  const [devices, setDevices] = useState([
    {
      id: 1,
      name: 'Router-Core-01',
      type: 'router',
      ip_address: '192.168.1.1',
      mac_address: '00:1B:44:11:3A:B7',
      status: 'online',
      last_seen: new Date().toISOString(),
      cpu_usage: 35,
      interfaces_count: 4
    },
    {
      id: 2,
      name: 'Switch-Main-01',
      type: 'switch',
      ip_address: '192.168.1.10',
      mac_address: '00:1B:44:11:3A:C8',
      status: 'online',
      last_seen: new Date().toISOString(),
      cpu_usage: 22,
      interfaces_count: 24
    },
    {
      id: 3,
      name: 'Firewall-DMZ',
      type: 'firewall',
      ip_address: '192.168.100.1',
      mac_address: '00:1B:44:11:3A:D9',
      status: 'warning',
      last_seen: new Date().toISOString(),
      cpu_usage: 78,
      interfaces_count: 8
    }
  ]);
  const [loading, setLoading] = useState({
    fetch: false,
    overview: false,
    search: false
  });
  const [error, setError] = useState(null);

  // Chargement initial des données (simulation)
  useEffect(() => {
    const loadApiViewsData = async () => {
      setLoading(prev => ({ ...prev, fetch: true }));
      
      // Simulation d'un délai de chargement
      setTimeout(() => {
        setLoading(prev => ({ ...prev, fetch: false }));
      }, 1000);
    };

    loadApiViewsData();
  }, [timeRange]);

  // Auto-refresh (simulation)
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulation de mise à jour des données
      setDevices(prevDevices => 
        prevDevices.map(device => ({
          ...device,
          cpu_usage: Math.max(10, Math.min(90, device.cpu_usage + (Math.random() - 0.5) * 10)),
          last_seen: new Date().toISOString()
        }))
      );
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Handlers
  const handleRefresh = useCallback(() => {
    setLoading(prev => ({ ...prev, fetch: true }));
    
    // Simulation de refresh
    setTimeout(() => {
      setLoading(prev => ({ ...prev, fetch: false }));
      setDevices(prevDevices => 
        prevDevices.map(device => ({
          ...device,
          last_seen: new Date().toISOString()
        }))
      );
    }, 1000);
  }, []);

  const handleSearch = (query) => {
    setSearchQuery(query);
    // La recherche sera implementée avec le filtrage local pour l'instant
  };

  const clearError = () => {
    setError(null);
  };

  // Filtres pour les équipements
  const filteredDevices = devices?.filter(device => {
    const matchesSearch = device.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         device.type?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         device.ip_address?.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesType = filterType === 'all' || device.type === filterType;
    
    return matchesSearch && matchesType;
  }) || [];

  // Statistiques calculées
  const stats = {
    totalDevices: devices?.length || 0,
    onlineDevices: devices?.filter(d => d.status === 'online')?.length || 0,
    problematicDevices: devices?.filter(d => d.status === 'warning' || d.status === 'offline')?.length || 0,
    discoveredTopology: 12, // Simulation
    activeClients: 8, // Simulation
    systemHealth: systemOverview?.overall_status || 'unknown'
  };

  // Types de périphériques avec leurs configurations
  const deviceTypes = {
    router: { name: 'Routeurs', icon: Wifi, color: 'text-blue-500', bgColor: 'bg-blue-50 dark:bg-blue-900/20' },
    switch: { name: 'Commutateurs', icon: Network, color: 'text-green-500', bgColor: 'bg-green-50 dark:bg-green-900/20' },
    firewall: { name: 'Pare-feu', icon: Shield, color: 'text-red-500', bgColor: 'bg-red-50 dark:bg-red-900/20' },
    server: { name: 'Serveurs', icon: Server, color: 'text-purple-500', bgColor: 'bg-purple-50 dark:bg-purple-900/20' },
    wireless: { name: 'Wi-Fi', icon: Wifi, color: 'text-cyan-500', bgColor: 'bg-cyan-50 dark:bg-cyan-900/20' },
    unknown: { name: 'Inconnus', icon: Monitor, color: 'text-gray-500', bgColor: 'bg-gray-50 dark:bg-gray-900/20' }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'online': return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'offline': return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default: return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status) => {
    const configs = {
      online: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
      offline: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
      warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
      unknown: 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
    };
    
    return configs[status] || configs.unknown;
  };

  // Composant de carte d'équipement
  const DeviceCard = ({ device }) => {
    const deviceConfig = deviceTypes[device.type] || deviceTypes.unknown;
    const IconComponent = deviceConfig.icon;

    return (
      <div className={`${getThemeClasses('card', 'apiViews')} p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200`}>
        {/* En-tête de la carte */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${deviceConfig.bgColor}`}>
              <IconComponent className={`w-5 h-5 ${deviceConfig.color}`} />
            </div>
            <div>
              <h3 className={`font-semibold ${getThemeClasses('textPrimary', 'apiViews')}`}>
                {device.name || device.hostname || 'Équipement inconnu'}
              </h3>
              <p className={`text-sm ${getThemeClasses('textSecondary', 'apiViews')}`}>
                {deviceConfig.name}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-1">
            {getStatusIcon(device.status)}
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(device.status)}`}>
              {device.status === 'online' ? 'En ligne' : device.status === 'offline' ? 'Hors ligne' : 'Inconnu'}
            </span>
          </div>
        </div>

        {/* Informations détaillées */}
        <div className="space-y-2 mb-4">
          {device.ip_address && (
            <div className="flex items-center justify-between">
              <span className={`text-sm ${getThemeClasses('textSecondary', 'apiViews')}`}>
                Adresse IP:
              </span>
              <span className={`text-sm font-mono ${getThemeClasses('textPrimary', 'apiViews')}`}>
                {device.ip_address}
              </span>
            </div>
          )}
          
          {device.mac_address && (
            <div className="flex items-center justify-between">
              <span className={`text-sm ${getThemeClasses('textSecondary', 'apiViews')}`}>
                MAC:
              </span>
              <span className={`text-sm font-mono ${getThemeClasses('textPrimary', 'apiViews')}`}>
                {device.mac_address}
              </span>
            </div>
          )}

          {device.last_seen && (
            <div className="flex items-center justify-between">
              <span className={`text-sm ${getThemeClasses('textSecondary', 'apiViews')}`}>
                Dernière activité:
              </span>
              <span className={`text-sm ${getThemeClasses('textPrimary', 'apiViews')}`}>
                {new Date(device.last_seen).toLocaleString()}
              </span>
            </div>
          )}

          {device.cpu_usage !== undefined && (
            <div className="flex items-center justify-between">
              <span className={`text-sm ${getThemeClasses('textSecondary', 'apiViews')}`}>
                CPU:
              </span>
              <div className="flex items-center space-x-2">
                <div className="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
                  <div 
                    className={`h-2 rounded-full ${device.cpu_usage > 80 ? 'bg-red-500' : device.cpu_usage > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                    style={{ width: `${Math.min(device.cpu_usage, 100)}%` }}
                  ></div>
                </div>
                <span className={`text-sm ${getThemeClasses('textPrimary', 'apiViews')}`}>
                  {device.cpu_usage}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
          <button 
            onClick={() => setSelectedDevice(device)}
            className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm font-medium transition-colors ${getThemeClasses('buttonPrimary', 'apiViews')} hover:opacity-90`}
          >
            <Eye className="w-4 h-4" />
            <span>Détails</span>
          </button>
          
          <div className="flex items-center space-x-2">
            {device.interfaces_count && (
              <span className={`text-xs ${getThemeClasses('textSecondary', 'apiViews')}`}>
                {device.interfaces_count} interfaces
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* En-tête avec statistiques globales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className={`${getThemeClasses('card', 'apiViews')} p-6 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${getThemeClasses('textSecondary', 'apiViews')}`}>
                Équipements Total
              </p>
              <p className={`text-2xl font-bold ${getThemeClasses('textPrimary', 'apiViews')}`}>
                {stats.totalDevices}
              </p>
            </div>
            <Monitor className={`w-8 h-8 ${getThemeClasses('textSecondary', 'apiViews')}`} />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'apiViews')} p-6 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${getThemeClasses('textSecondary', 'apiViews')}`}>
                En Ligne
              </p>
              <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                {stats.onlineDevices}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'apiViews')} p-6 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${getThemeClasses('textSecondary', 'apiViews')}`}>
                Problèmes
              </p>
              <p className="text-2xl font-bold text-red-600 dark:text-red-400">
                {stats.problematicDevices}
              </p>
            </div>
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'apiViews')} p-6 rounded-lg`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm font-medium ${getThemeClasses('textSecondary', 'apiViews')}`}>
                Topologie
              </p>
              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {stats.discoveredTopology}
              </p>
            </div>
            <Network className="w-8 h-8 text-blue-500" />
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
                Erreur de chargement des vues API
              </h3>
              <p className="text-sm text-red-600 dark:text-red-300 mt-1">
                {error.message || 'Impossible de charger les données des vues API'}
              </p>
            </div>
            <button 
              onClick={clearError}
              className="ml-auto text-red-400 hover:text-red-600"
            >
              <CheckCircle className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Contrôles et filtres */}
      <div className={`${getThemeClasses('card', 'apiViews')} p-6 rounded-lg`}>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher équipements..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch(e.target.value)}
                className={`pl-10 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${getThemeClasses('input', 'apiViews')}`}
              />
            </div>
            
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className={`px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${getThemeClasses('input', 'apiViews')}`}
            >
              <option value="all">Tous types</option>
              {Object.entries(deviceTypes).map(([key, config]) => (
                <option key={key} value={key}>{config.name}</option>
              ))}
            </select>
            
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className={`px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${getThemeClasses('input', 'apiViews')}`}
            >
              <option value="1h">1 heure</option>
              <option value="6h">6 heures</option>
              <option value="24h">24 heures</option>
              <option value="7d">7 jours</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="autoRefreshViews"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor="autoRefreshViews" className={`text-sm ${getThemeClasses('textSecondary', 'apiViews')}`}>
                Refresh auto
              </label>
            </div>
            
            <button
              onClick={handleRefresh}
              disabled={loading.fetch || loading.overview}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${getThemeClasses('buttonPrimary', 'apiViews')} hover:opacity-90 disabled:opacity-50`}
            >
              <RefreshCw className={`w-4 h-4 ${(loading.fetch || loading.overview) ? 'animate-spin' : ''}`} />
              <span>Actualiser</span>
            </button>
          </div>
        </div>
      </div>

      {/* Vue d'ensemble système */}
      {systemOverview && (
        <div className={`${getThemeClasses('card', 'apiViews')} p-6 rounded-lg`}>
          <h2 className={`text-lg font-semibold ${getThemeClasses('textPrimary', 'apiViews')} mb-4`}>
            Vue d'Ensemble Système
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`text-sm ${getThemeClasses('textSecondary', 'apiViews')}`}>CPU</span>
                <span className={`text-sm font-medium ${getThemeClasses('textPrimary', 'apiViews')}`}>
                  {systemOverview.cpu_usage || 0}%
                </span>
              </div>
              <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
                <div 
                  className={`h-2 rounded-full ${(systemOverview.cpu_usage || 0) > 80 ? 'bg-red-500' : (systemOverview.cpu_usage || 0) > 60 ? 'bg-yellow-500' : 'bg-green-500'}`}
                  style={{ width: `${Math.min(systemOverview.cpu_usage || 0, 100)}%` }}
                ></div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`text-sm ${getThemeClasses('textSecondary', 'apiViews')}`}>Mémoire</span>
                <span className={`text-sm font-medium ${getThemeClasses('textPrimary', 'apiViews')}`}>
                  {systemOverview.memory_usage || 0}%
                </span>
              </div>
              <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
                <div 
                  className={`h-2 rounded-full ${(systemOverview.memory_usage || 0) > 85 ? 'bg-red-500' : (systemOverview.memory_usage || 0) > 70 ? 'bg-yellow-500' : 'bg-green-500'}`}
                  style={{ width: `${Math.min(systemOverview.memory_usage || 0, 100)}%` }}
                ></div>
              </div>
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className={`text-sm ${getThemeClasses('textSecondary', 'apiViews')}`}>Disque</span>
                <span className={`text-sm font-medium ${getThemeClasses('textPrimary', 'apiViews')}`}>
                  {systemOverview.disk_usage || 0}%
                </span>
              </div>
              <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full">
                <div 
                  className={`h-2 rounded-full ${(systemOverview.disk_usage || 0) > 90 ? 'bg-red-500' : (systemOverview.disk_usage || 0) > 75 ? 'bg-yellow-500' : 'bg-green-500'}`}
                  style={{ width: `${Math.min(systemOverview.disk_usage || 0, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Liste des équipements */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading.fetch ? (
          Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className={`${getThemeClasses('card', 'apiViews')} p-6 rounded-lg animate-pulse`}>
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
        ) : filteredDevices.length > 0 ? (
          filteredDevices.map((device, index) => (
            <DeviceCard key={device.id || index} device={device} />
          ))
        ) : (
          <div className="col-span-full text-center py-12">
            <Monitor className={`w-16 h-16 mx-auto ${getThemeClasses('textSecondary', 'apiViews')} mb-4`} />
            <h3 className={`text-lg font-medium ${getThemeClasses('textPrimary', 'apiViews')} mb-2`}>
              Aucun équipement trouvé
            </h3>
            <p className={`${getThemeClasses('textSecondary', 'apiViews')}`}>
              {searchQuery || filterType !== 'all' 
                ? 'Aucun équipement ne correspond aux critères de recherche'
                : 'Aucun équipement détecté par les vues API'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ApiViews;