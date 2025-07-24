// QoSModern.jsx - Module QoS moderne avec tous les composants
import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  Gauge, 
  Activity, 
  TrendingUp, 
  Shield, 
  Settings, 
  Award, 
  Target, 
  BarChart3,
  RefreshCw,
  Download,
  Upload,
  Play,
  Pause,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Users,
  Network,
  Database,
  Monitor,
  Zap,
  Filter,
  Search,
  Calendar,
  Eye,
  Edit,
  Trash2,
  Plus,
  Copy,
  FileText,
  Bell,
  Globe,
  Router,
  Server,
  Layers,
  Signal,
  Wifi,
  Brain,
  Lightbulb
} from 'lucide-react';

import { useTheme } from '../contexts/ThemeContext';
import { 
  QoSDashboard, 
  SLAManagement, 
  PerformanceAnalysis, 
  QoSPolicies 
} from '../components/qos';

const QoSModern = () => {
  const location = useLocation();
  const { getThemeClasses } = useTheme();
  
  // État pour l'onglet actif
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30);

  // Détection de l'onglet basé sur l'URL
  useEffect(() => {
    const path = location.pathname;
    if (path.includes('/sla')) setActiveTab('sla');
    else if (path.includes('/performance')) setActiveTab('performance');
    else if (path.includes('/policies')) setActiveTab('policies');
    else setActiveTab('dashboard');
  }, [location.pathname]);

  // Configuration des onglets
  const tabs = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: Gauge,
      description: 'Vue d\'ensemble QoS',
      component: QoSDashboard
    },
    {
      id: 'policies',
      label: 'Politiques',
      icon: Shield,
      description: 'Configuration QoS',
      component: QoSPolicies
    },
    {
      id: 'sla',
      label: 'SLA',
      icon: Award,
      description: 'Accords de service',
      component: SLAManagement
    },
    {
      id: 'performance',
      label: 'Performance',
      icon: Activity,
      description: 'Analyse et diagnostics',
      component: PerformanceAnalysis
    }
  ];

  // Statistiques globales simulées
  const globalStats = {
    totalPolicies: 45,
    activePolicies: 38,
    totalBandwidth: 2000,
    usedBandwidth: 1456,
    availableBandwidth: 544,
    activeSLAs: 12,
    slaCompliance: 95.8,
    averageLatency: 15.6,
    packetLoss: 0.3,
    networkQuality: 94.2,
    activeInterfaces: 8,
    systemHealth: 'healthy'
  };

  // Refresh automatique
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setLastUpdate(new Date());
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Fonction de rafraîchissement
  const handleRefresh = () => {
    setIsLoading(true);
    // Simulation d'un appel API
    setTimeout(() => {
      setLastUpdate(new Date());
      setIsLoading(false);
    }, 1500);
  };

  // Composant de l'en-tête avec statistiques
  const QoSHeader = () => (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className={`${getThemeClasses('text', 'dashboard')} text-3xl font-bold`}>
            Qualité de Service (QoS)
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-2`}>
            Gestion et optimisation de la qualité de service réseau
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              Auto-refresh:
            </span>
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`flex items-center space-x-2 px-3 py-1 rounded text-sm transition-colors ${
                autoRefresh 
                  ? 'bg-green-600 hover:bg-green-700 text-white' 
                  : 'bg-gray-600 hover:bg-gray-700 text-white'
              }`}
            >
              {autoRefresh ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              <span>{autoRefresh ? 'ON' : 'OFF'}</span>
            </button>
            {autoRefresh && (
              <select
                value={refreshInterval}
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value={10}>10s</option>
                <option value={30}>30s</option>
                <option value={60}>1min</option>
                <option value={300}>5min</option>
              </select>
            )}
          </div>
          
          <div className="text-right">
            <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              Dernière mise à jour
            </div>
            <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
              {lastUpdate.toLocaleTimeString()}
            </div>
          </div>
          
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className={`flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors ${
              isLoading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Actualiser</span>
          </button>
          
          <button className="flex items-center space-x-2 px-4 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Settings className="w-4 h-4" />
            <span>Paramètres</span>
          </button>
        </div>
      </div>

      {/* Statistiques rapides */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-4">
        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Politiques Actives
              </p>
              <p className="text-2xl font-bold text-blue-400">
                {globalStats.activePolicies}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                / {globalStats.totalPolicies} total
              </p>
            </div>
            <Shield className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Bande Passante
              </p>
              <p className="text-2xl font-bold text-green-400">
                {globalStats.usedBandwidth}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                / {globalStats.totalBandwidth} Mbps
              </p>
            </div>
            <Gauge className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                SLA Actifs
              </p>
              <p className="text-2xl font-bold text-purple-400">
                {globalStats.activeSLAs}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                {globalStats.slaCompliance}% conformité
              </p>
            </div>
            <Award className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Latence Moyenne
              </p>
              <p className="text-2xl font-bold text-orange-400">
                {globalStats.averageLatency}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                ms
              </p>
            </div>
            <Clock className="w-8 h-8 text-orange-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Perte Paquets
              </p>
              <p className="text-2xl font-bold text-red-400">
                {globalStats.packetLoss}%
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                Très faible
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-red-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Qualité Réseau
              </p>
              <p className="text-2xl font-bold text-cyan-400">
                {globalStats.networkQuality}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                / 100
              </p>
            </div>
            <Target className="w-8 h-8 text-cyan-400" />
          </div>
        </div>
      </div>
    </div>
  );

  // Composant de navigation par onglets
  const TabNavigation = () => (
    <div className="flex space-x-1 mb-6">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center space-x-2 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <Icon className="w-4 h-4" />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );

  // Composant de statut système
  const SystemStatus = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${
            globalStats.systemHealth === 'healthy' ? 'bg-green-400' : 'bg-red-400'
          }`}></div>
          <div>
            <h3 className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
              État du système QoS
            </h3>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              {globalStats.systemHealth === 'healthy' ? 'Tous les services QoS fonctionnent normalement' : 'Problème détecté'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-6">
          <div className="text-right">
            <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              Utilisation bande passante
            </div>
            <div className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>
              {((globalStats.usedBandwidth / globalStats.totalBandwidth) * 100).toFixed(1)}%
            </div>
          </div>
          
          <div className="text-right">
            <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              Interfaces actives
            </div>
            <div className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>
              {globalStats.activeInterfaces}
            </div>
          </div>
          
          <div className="text-right">
            <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              Score qualité
            </div>
            <div className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>
              {globalStats.networkQuality}/100
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Composant de recommandations rapides
  const QuickRecommendations = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <h3 className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
            Recommandations IA
          </h3>
        </div>
        <button className="text-sm text-blue-400 hover:text-blue-300 transition-colors">
          Voir toutes
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div className="flex items-start space-x-3 p-3 bg-blue-900/20 rounded border-l-4 border-blue-500">
          <Lightbulb className="w-5 h-5 text-yellow-400 mt-0.5" />
          <div>
            <p className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
              Optimisation WiFi
            </p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
              Redistribuer le trafic wlan0 vers eth1
            </p>
          </div>
        </div>
        
        <div className="flex items-start space-x-3 p-3 bg-green-900/20 rounded border-l-4 border-green-500">
          <Lightbulb className="w-5 h-5 text-yellow-400 mt-0.5" />
          <div>
            <p className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
              Politique VoIP
            </p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
              Augmenter la priorité du trafic SIP
            </p>
          </div>
        </div>
        
        <div className="flex items-start space-x-3 p-3 bg-orange-900/20 rounded border-l-4 border-orange-500">
          <Lightbulb className="w-5 h-5 text-yellow-400 mt-0.5" />
          <div>
            <p className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
              Surveillance SLA
            </p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
              3 SLA approchent les limites
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  // Rendu du composant actif
  const renderActiveComponent = () => {
    const activeTabConfig = tabs.find(tab => tab.id === activeTab);
    const ActiveComponent = activeTabConfig.component;
    
    return (
      <div className="flex-1">
        <ActiveComponent isVisible={true} />
      </div>
    );
  };

  return (
    <div className={`min-h-screen ${getThemeClasses('background', 'dashboard')} ${getThemeClasses('text', 'dashboard')}`}>
      <div className="max-w-full mx-auto p-6">
        <QoSHeader />
        <SystemStatus />
        <QuickRecommendations />
        <TabNavigation />
        
        {/* Contenu principal */}
        <div className="space-y-6">
          {renderActiveComponent()}
        </div>
      </div>
    </div>
  );
};

export default QoSModern;