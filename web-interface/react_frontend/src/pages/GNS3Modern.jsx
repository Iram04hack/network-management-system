// GNS3Modern.jsx - Interface GNS3 moderne intégrée
import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Server, 
  Play, 
  Pause, 
  Settings, 
  RefreshCw, 
  Download, 
  Upload, 
  Bell, 
  Search, 
  Filter, 
  Plus, 
  Eye, 
  Target, 
  Network, 
  Router, 
  Monitor, 
  Database, 
  Building, 
  Gauge, 
  BarChart3, 
  Edit, 
  Layers, 
  Globe, 
  Terminal, 
  Shield, 
  Zap, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Users, 
  Calendar, 
  FileText, 
  HardDrive, 
  Cpu, 
  MemoryStick, 
  Wifi, 
  Signal,
  Minimize2
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { useTheme } from '../contexts/ThemeContext';

// Import des composants GNS3 modernes
import { 
  GNS3Dashboard, 
  ProjectManagement, 
  TopologyEditor, 
  SimulationMonitoring 
} from '../components/gns3';

const GNS3Modern = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [globalStats, setGlobalStats] = useState({});
  const [recommendations, setRecommendations] = useState([]);
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [notifications, setNotifications] = useState([]);
  const [systemStatus, setSystemStatus] = useState('operational');
  const [selectedProject, setSelectedProject] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [compactMode, setCompactMode] = useState(false);

  const { getThemeClasses } = useTheme();
  const autoRefreshRef = useRef(null);

  // Configuration des onglets avec les nouveaux composants
  const tabs = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: Gauge,
      component: GNS3Dashboard,
      description: 'Vue d\'ensemble des serveurs et simulations'
    },
    {
      id: 'projects',
      label: 'Projets',
      icon: Building,
      component: ProjectManagement,
      description: 'Gestion des projets GNS3'
    },
    {
      id: 'topology',
      label: 'Topologie',
      icon: Network,
      component: TopologyEditor,
      description: 'Éditeur de topologie réseau'
    },
    {
      id: 'monitoring',
      label: 'Monitoring',
      icon: Activity,
      component: SimulationMonitoring,
      description: 'Surveillance des simulations'
    }
  ];

  // Statistiques globales mockées
  const mockGlobalStats = {
    totalServers: 3,
    activeServers: 2,
    totalProjects: 13,
    runningProjects: 8,
    totalNodes: 56,
    activeNodes: 32,
    totalSimulations: 5,
    runningSimulations: 3,
    systemLoad: 34.6,
    memoryUsage: 56.8,
    storageUsage: 74.2,
    networkThroughput: 245.3,
    uptime: 259200,
    lastUpdate: new Date().toISOString()
  };

  // Recommandations mockées avec IA
  const mockRecommendations = [
    {
      id: 'rec-1',
      type: 'performance',
      priority: 'high',
      title: 'Optimisation CPU détectée',
      message: 'Le serveur GNS3-Server-01 présente une utilisation CPU élevée (78%). Considérez la répartition des simulations.',
      action: 'Voir détails',
      icon: Cpu,
      color: '#F59E0B'
    },
    {
      id: 'rec-2',
      type: 'capacity',
      priority: 'medium',
      title: 'Planification capacité',
      message: 'Basé sur les tendances actuelles, vous atteindrez 90% de capacité mémoire d\'ici 2 semaines.',
      action: 'Planifier',
      icon: TrendingUp,
      color: '#3B82F6'
    },
    {
      id: 'rec-3',
      type: 'maintenance',
      priority: 'low',
      title: 'Mise à jour disponible',
      message: 'GNS3 v2.2.45 est disponible avec des améliorations de performance.',
      action: 'Télécharger',
      icon: Download,
      color: '#10B981'
    }
  ];

  // Notifications mockées
  const mockNotifications = [
    {
      id: 'notif-1',
      type: 'success',
      title: 'Simulation démarrée',
      message: 'Le projet "Lab Security" a été démarré avec succès',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      read: false
    },
    {
      id: 'notif-2',
      type: 'warning',
      title: 'Ressources limitées',
      message: 'Le serveur GNS3-Server-02 approche de ses limites de mémoire',
      timestamp: new Date(Date.now() - 900000).toISOString(),
      read: false
    },
    {
      id: 'notif-3',
      type: 'info',
      title: 'Sauvegarde terminée',
      message: 'Sauvegarde automatique des projets terminée',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      read: true
    }
  ];

  // Initialisation
  useEffect(() => {
    setGlobalStats(mockGlobalStats);
    setRecommendations(mockRecommendations);
    setNotifications(mockNotifications);
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (isAutoRefresh) {
      autoRefreshRef.current = setInterval(() => {
        // Simulation de mise à jour des données
        setGlobalStats(prev => ({
          ...prev,
          systemLoad: Math.max(0, Math.min(100, prev.systemLoad + (Math.random() - 0.5) * 10)),
          memoryUsage: Math.max(0, Math.min(100, prev.memoryUsage + (Math.random() - 0.5) * 8)),
          networkThroughput: Math.max(0, prev.networkThroughput + (Math.random() - 0.5) * 50),
          lastUpdate: new Date().toISOString()
        }));
      }, refreshInterval * 1000);

      return () => {
        if (autoRefreshRef.current) {
          clearInterval(autoRefreshRef.current);
        }
      };
    }
  }, [isAutoRefresh, refreshInterval]);

  // Fonctions utilitaires
  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    return `${days}j ${hours}h`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational': return '#10B981';
      case 'degraded': return '#F59E0B';
      case 'maintenance': return '#3B82F6';
      case 'down': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getNotificationColor = (type) => {
    switch (type) {
      case 'success': return '#10B981';
      case 'warning': return '#F59E0B';
      case 'error': return '#EF4444';
      case 'info': return '#3B82F6';
      default: return '#6B7280';
    }
  };

  // Actions
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
  };

  const handleRefresh = () => {
    setGlobalStats(prev => ({ ...prev, lastUpdate: new Date().toISOString() }));
  };

  const markNotificationAsRead = (notifId) => {
    setNotifications(prev => prev.map(n => 
      n.id === notifId ? { ...n, read: true } : n
    ));
  };

  const dismissRecommendation = (recId) => {
    setRecommendations(prev => prev.filter(r => r.id !== recId));
  };

  // Composant du header avec statistiques globales
  const Header = () => (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className={`${getThemeClasses('text', 'dashboard')} text-3xl font-bold`}>
            GNS3 Management
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Plateforme de virtualisation et simulation réseau
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Indicateur de statut système */}
          <div className="flex items-center space-x-2">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getStatusColor(systemStatus) }}
            />
            <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
              Système opérationnel
            </span>
          </div>
          
          {/* Contrôles */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsAutoRefresh(!isAutoRefresh)}
              className={`flex items-center space-x-2 px-3 py-2 rounded transition-colors ${
                isAutoRefresh 
                  ? 'bg-green-600 hover:bg-green-700 text-white' 
                  : 'border border-gray-600 hover:border-gray-500'
              }`}
            >
              {isAutoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              <span className="text-sm">Auto-refresh</span>
            </button>
            
            <button
              onClick={handleRefresh}
              className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              <span className="text-sm">Actualiser</span>
            </button>
          </div>
        </div>
      </div>

      {/* Statistiques rapides */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Server className="w-8 h-8 text-blue-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Serveurs</p>
              <p className="text-lg font-bold text-blue-400">
                {globalStats.activeServers}/{globalStats.totalServers}
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Building className="w-8 h-8 text-green-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Projets</p>
              <p className="text-lg font-bold text-green-400">
                {globalStats.runningProjects}/{globalStats.totalProjects}
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Router className="w-8 h-8 text-purple-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Nœuds</p>
              <p className="text-lg font-bold text-purple-400">
                {globalStats.activeNodes}/{globalStats.totalNodes}
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Activity className="w-8 h-8 text-orange-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>CPU Moyen</p>
              <p className="text-lg font-bold text-orange-400">
                {globalStats.systemLoad?.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <MemoryStick className="w-8 h-8 text-red-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Mémoire</p>
              <p className="text-lg font-bold text-red-400">
                {globalStats.memoryUsage?.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Clock className="w-8 h-8 text-cyan-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Uptime</p>
              <p className="text-lg font-bold text-cyan-400">
                {formatUptime(globalStats.uptime)}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Composant des recommandations IA
  const RecommendationsPanel = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold flex items-center space-x-2`}>
          <Zap className="w-5 h-5 text-yellow-400" />
          <span>Recommandations IA</span>
        </h3>
        <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
          {recommendations.length} suggestion{recommendations.length > 1 ? 's' : ''}
        </span>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {recommendations.map(rec => {
          const RecIcon = rec.icon;
          return (
            <div key={rec.id} className="relative p-4 bg-gray-700/30 rounded border-l-4" style={{ borderLeftColor: rec.color }}>
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <RecIcon className="w-5 h-5 mt-0.5" style={{ color: rec.color }} />
                  <div>
                    <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium text-sm`}>
                      {rec.title}
                    </h4>
                    <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                      {rec.message}
                    </p>
                    <button 
                      className="text-xs text-blue-400 hover:text-blue-300 mt-2"
                      style={{ color: rec.color }}
                    >
                      {rec.action} →
                    </button>
                  </div>
                </div>
                <button
                  onClick={() => dismissRecommendation(rec.id)}
                  className="text-gray-400 hover:text-gray-300 ml-2"
                >
                  ×
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Composant de navigation par onglets
  const TabNavigation = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} mb-6`}>
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex space-x-1">
          {tabs.map(tab => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <TabIcon className="w-4 h-4" />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>
        
        <div className="flex items-center space-x-4">
          {/* Barre de recherche */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none text-sm"
            />
          </div>
          
          {/* Notifications */}
          <div className="relative">
            <button className="p-2 text-gray-400 hover:text-gray-300 rounded transition-colors">
              <Bell className="w-5 h-5" />
              {notifications.filter(n => !n.read).length > 0 && (
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full text-xs"></span>
              )}
            </button>
          </div>
          
          {/* Mode compact */}
          <button
            onClick={() => setCompactMode(!compactMode)}
            className={`p-2 rounded transition-colors ${
              compactMode ? 'text-blue-400' : 'text-gray-400 hover:text-gray-300'
            }`}
            title="Mode compact"
          >
            <Minimize2 className="w-5 h-5" />
          </button>
        </div>
      </div>
      
      {/* Description de l'onglet actif */}
      <div className="p-4">
        <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
          {tabs.find(tab => tab.id === activeTab)?.description}
        </p>
      </div>
    </div>
  );

  // Rendu du composant actif
  const ActiveComponent = () => {
    const activeTabConfig = tabs.find(tab => tab.id === activeTab);
    if (!activeTabConfig) return null;
    
    const Component = activeTabConfig.component;
    return <Component isVisible={true} compactMode={compactMode} />;
  };

  return (
    <div className="p-6 space-y-6">
      <Header />
      <RecommendationsPanel />
      <TabNavigation />
      <ActiveComponent />
    </div>
  );
};

export default GNS3Modern;