// ReportingModern.jsx - Interface Reporting moderne intégrée
import React, { useState, useEffect, useRef } from 'react';
import { 
  BarChart3, 
  FileText, 
  Calendar, 
  Award, 
  TrendingUp, 
  TrendingDown, 
  Download, 
  Upload, 
  Settings, 
  RefreshCw, 
  Bell, 
  Search, 
  Filter, 
  Plus, 
  Eye, 
  Target, 
  Zap, 
  DollarSign, 
  Users, 
  Shield, 
  Activity, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  Building, 
  Database, 
  Server, 
  Network, 
  Monitor, 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Globe, 
  Wifi, 
  Router, 
  Terminal, 
  Mail, 
  Share, 
  Link, 
  Edit, 
  Trash2, 
  Copy, 
  Play, 
  Pause, 
  Square, 
  Maximize, 
  Minimize2, 
  Info, 
  Star, 
  Bookmark, 
  Tag, 
  Hash, 
  Layers
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { useTheme } from '../contexts/ThemeContext';

// Import des composants Reporting modernes
import { 
  ReportsDashboard, 
  CustomReports, 
  ScheduledReports, 
  ExecutiveDashboard 
} from '../components/reporting';

const ReportingModern = () => {
  const [activeTab, setActiveTab] = useState('analytics');
  const [globalStats, setGlobalStats] = useState({
    totalReports: 2847,
    generatedThisMonth: 423,
    scheduledActive: 24,
    downloadCount: 8294,
    shareCount: 1567,
    storageUsed: 15.6,
    avgGenerationTime: 2.4,
    successRate: 96.8,
    userEngagement: 78.2,
    costSavings: 34.5,
    automationRate: 67.3,
    executiveUsers: 12,
    lastUpdate: new Date().toISOString()
  });
  const [recommendations, setRecommendations] = useState([]);
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [notifications, setNotifications] = useState([]);
  const [systemStatus, setSystemStatus] = useState('operational');
  const [searchQuery, setSearchQuery] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [compactMode, setCompactMode] = useState(false);
  const [recentActivity, setRecentActivity] = useState([]);

  const { getThemeClasses } = useTheme();
  const autoRefreshRef = useRef(null);

  // Configuration des onglets avec les nouveaux composants
  const tabs = [
    {
      id: 'analytics',
      label: 'Analytics',
      icon: BarChart3,
      component: ReportsDashboard,
      description: 'Analyses avancées et métriques des rapports'
    },
    {
      id: 'generator',
      label: 'Générateur',
      icon: FileText,
      component: CustomReports,
      description: 'Création de rapports personnalisés'
    },
    {
      id: 'schedules',
      label: 'Planifications',
      icon: Calendar,
      component: ScheduledReports,
      description: 'Automatisation et planification des rapports'
    },
    {
      id: 'executive',
      label: 'Exécutif',
      icon: Award,
      component: ExecutiveDashboard,
      description: 'Tableaux de bord pour la direction'
    }
  ];

  // Statistiques globales mockées
  const mockGlobalStats = {
    totalReports: 2847,
    generatedThisMonth: 423,
    scheduledActive: 24,
    downloadCount: 8294,
    shareCount: 1567,
    storageUsed: 15.6, // GB
    avgGenerationTime: 2.4, // minutes
    successRate: 96.8,
    userEngagement: 78.2,
    costSavings: 34.5, // %
    automationRate: 67.3,
    executiveUsers: 12,
    lastUpdate: new Date().toISOString()
  };

  // Recommandations mockées avec IA
  const mockRecommendations = [
    {
      id: 'rec-1',
      type: 'efficiency',
      priority: 'high',
      title: 'Optimisation automatisation',
      message: '8 rapports manuels peuvent être automatisés, économisant 15h/semaine.',
      action: 'Automatiser',
      icon: Zap,
      color: '#F59E0B',
      savings: 'Économie: 15h/semaine'
    },
    {
      id: 'rec-2',
      type: 'storage',
      priority: 'medium',
      title: 'Gestion du stockage',
      message: 'Stockage à 78%. Planifier l\'archivage des rapports anciens.',
      action: 'Planifier',
      icon: Database,
      color: '#3B82F6',
      savings: 'Libère: 5.2 GB'
    },
    {
      id: 'rec-3',
      type: 'engagement',
      priority: 'low',
      title: 'Amélioration engagement',
      message: 'Templates interactifs recommandés pour augmenter l\'engagement.',
      action: 'Implémenter',
      icon: TrendingUp,
      color: '#10B981',
      savings: 'Impact: +25% engagement'
    }
  ];

  // Notifications mockées
  const mockNotifications = [
    {
      id: 'notif-1',
      type: 'success',
      title: 'Rapport généré avec succès',
      message: 'Rapport Exécutif Mensuel - 3 destinataires',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      read: false
    },
    {
      id: 'notif-2',
      type: 'warning',
      title: 'Planification en retard',
      message: 'Rapport Sécurité Hebdomadaire - Échec génération',
      timestamp: new Date(Date.now() - 900000).toISOString(),
      read: false
    },
    {
      id: 'notif-3',
      type: 'info',
      title: 'Nouvelle fonctionnalité',
      message: 'Templates IA maintenant disponibles',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      read: true
    }
  ];

  // Activité récente mockée
  const mockRecentActivity = [
    {
      id: 'act-1',
      type: 'report_generated',
      user: 'Jean Dupont',
      action: 'a généré le rapport',
      target: 'Infrastructure Mensuel',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      icon: FileText,
      color: '#3B82F6'
    },
    {
      id: 'act-2',
      type: 'schedule_created',
      user: 'Sophie Martin',
      action: 'a créé une planification',
      target: 'Analyse Performance Quotidienne',
      timestamp: new Date(Date.now() - 3600000).toISOString(),
      icon: Calendar,
      color: '#10B981'
    },
    {
      id: 'act-3',
      type: 'template_modified',
      user: 'Marc Dubois',
      action: 'a modifié le template',
      target: 'Dashboard Exécutif',
      timestamp: new Date(Date.now() - 7200000).toISOString(),
      icon: Edit,
      color: '#8B5CF6'
    },
    {
      id: 'act-4',
      type: 'report_shared',
      user: 'Alice Bernard',
      action: 'a partagé',
      target: 'Rapport Sécurité avec 5 personnes',
      timestamp: new Date(Date.now() - 10800000).toISOString(),
      icon: Share,
      color: '#06B6D4'
    }
  ];

  // Initialisation
  useEffect(() => {
    setRecommendations(mockRecommendations);
    setNotifications(mockNotifications);
    setRecentActivity(mockRecentActivity);
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (isAutoRefresh) {
      autoRefreshRef.current = setInterval(() => {
        // Simulation de mise à jour des données
        setGlobalStats(prev => ({
          ...prev,
          generatedThisMonth: prev.generatedThisMonth + Math.floor(Math.random() * 3),
          downloadCount: prev.downloadCount + Math.floor(Math.random() * 8),
          shareCount: prev.shareCount + Math.floor(Math.random() * 3),
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

  const formatNumber = (num) => {
    if (num === undefined || num === null || isNaN(num)) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const getTimeAgo = (timestamp) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) return `${days}j`;
    if (hours > 0) return `${hours}h`;
    return `${minutes}m`;
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
            Reporting & Analytics
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Plateforme complète de génération et analyse de rapports
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
            <FileText className="w-8 h-8 text-blue-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Total Rapports</p>
              <p className="text-lg font-bold text-blue-400">
                {formatNumber(globalStats.totalReports)}
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Calendar className="w-8 h-8 text-green-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Planifications</p>
              <p className="text-lg font-bold text-green-400">
                {globalStats.scheduledActive}
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Download className="w-8 h-8 text-purple-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Téléchargements</p>
              <p className="text-lg font-bold text-purple-400">
                {formatNumber(globalStats.downloadCount)}
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <CheckCircle className="w-8 h-8 text-orange-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Taux de Succès</p>
              <p className="text-lg font-bold text-orange-400">
                {globalStats.successRate}%
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Zap className="w-8 h-8 text-red-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Automatisation</p>
              <p className="text-lg font-bold text-red-400">
                {globalStats.automationRate}%
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Database className="w-8 h-8 text-cyan-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Stockage</p>
              <p className="text-lg font-bold text-cyan-400">
                {globalStats.storageUsed} GB
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
          <span>Recommandations Intelligentes</span>
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
                    <div className="flex items-center justify-between mt-3">
                      <button 
                        className="text-xs px-2 py-1 rounded transition-colors"
                        style={{ backgroundColor: `${rec.color}20`, color: rec.color }}
                      >
                        {rec.action} →
                      </button>
                      <span className="text-xs text-green-400 font-medium">
                        {rec.savings}
                      </span>
                    </div>
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

  // Composant d'activité récente (sidebar)
  const RecentActivitySidebar = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
        Activité Récente
      </h3>
      
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {recentActivity.map(activity => {
          const Icon = activity.icon;
          
          return (
            <div key={activity.id} className="flex items-start space-x-3 p-2 rounded hover:bg-gray-700/30 transition-colors">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center mt-0.5"
                style={{ backgroundColor: `${activity.color}20` }}
              >
                <Icon className="w-4 h-4" style={{ color: activity.color }} />
              </div>
              <div className="flex-1 min-w-0">
                <div className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                  <span className="font-medium">{activity.user}</span>
                  <span className="mx-1">{activity.action}</span>
                  <span className="font-medium">{activity.target}</span>
                </div>
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  {getTimeAgo(activity.timestamp)}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      <div className="mt-4 pt-3 border-t border-gray-700">
        <button className="w-full text-blue-400 hover:text-blue-300 text-sm transition-colors">
          Voir toute l'activité →
        </button>
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
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <ActiveComponent />
        </div>
        <div className="lg:col-span-1">
          <RecentActivitySidebar />
        </div>
      </div>
    </div>
  );
};

export default ReportingModern;