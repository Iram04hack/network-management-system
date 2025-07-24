// SecurityModern.jsx - Module Security moderne avec tous les composants
import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  Shield, 
  AlertTriangle, 
  Settings, 
  Eye, 
  Activity, 
  Bug, 
  FileText, 
  TrendingUp,
  Bell,
  Target,
  Lock,
  Search,
  Filter,
  RefreshCw,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Plus,
  Download,
  Upload,
  Database,
  Monitor,
  Server,
  Globe,
  Users,
  Calendar,
  BarChart3,
  PieChart,
  LineChart
} from 'lucide-react';

import { useTheme } from '../contexts/ThemeContext';
import { 
  SecurityDashboard, 
  IncidentManagement, 
  VulnerabilityAnalysis, 
  SecurityRules 
} from '../components/security';

const SecurityModern = () => {
  const location = useLocation();
  const { getThemeClasses } = useTheme();
  
  // État pour l'onglet actif
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Détection de l'onglet basé sur l'URL
  useEffect(() => {
    const path = location.pathname;
    if (path.includes('/incidents')) setActiveTab('incidents');
    else if (path.includes('/vulnerabilities')) setActiveTab('vulnerabilities');
    else if (path.includes('/rules')) setActiveTab('rules');
    else setActiveTab('dashboard');
  }, [location.pathname]);

  // Configuration des onglets
  const tabs = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: Shield,
      description: 'Vue d\'ensemble sécurité',
      component: SecurityDashboard
    },
    {
      id: 'incidents',
      label: 'Incidents',
      icon: AlertTriangle,
      description: 'Gestion des incidents',
      component: IncidentManagement
    },
    {
      id: 'vulnerabilities',
      label: 'Vulnérabilités',
      icon: Bug,
      description: 'Analyse des vulnérabilités',
      component: VulnerabilityAnalysis
    },
    {
      id: 'rules',
      label: 'Règles',
      icon: FileText,
      description: 'Règles de sécurité',
      component: SecurityRules
    }
  ];

  // Statistiques globales simulées
  const globalStats = {
    totalAlerts: 1247,
    activeIncidents: 7,
    criticalVulnerabilities: 23,
    activeRules: 156,
    detectionRate: 94.2,
    responseTime: 2.3,
    systemHealth: 'healthy'
  };

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
  const SecurityHeader = () => (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className={`${getThemeClasses('text', 'dashboard')} text-3xl font-bold`}>
            Sécurité Réseau
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-2`}>
            Surveillance et gestion de la sécurité du réseau
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4">
        <div className={`${getThemeClasses('card', 'dashboard')} p-4 lg:col-span-2`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Alertes Totales
              </p>
              <p className="text-2xl font-bold text-blue-400">
                {globalStats.totalAlerts.toLocaleString()}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                +12% cette semaine
              </p>
            </div>
            <Bell className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Incidents Actifs
              </p>
              <p className="text-2xl font-bold text-orange-400">
                {globalStats.activeIncidents}
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Vulnérabilités
              </p>
              <p className="text-2xl font-bold text-red-400">
                {globalStats.criticalVulnerabilities}
              </p>
            </div>
            <Bug className="w-8 h-8 text-red-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Règles Actives
              </p>
              <p className="text-2xl font-bold text-green-400">
                {globalStats.activeRules}
              </p>
            </div>
            <FileText className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Détection
              </p>
              <p className="text-2xl font-bold text-purple-400">
                {globalStats.detectionRate}%
              </p>
            </div>
            <Target className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Réponse
              </p>
              <p className="text-2xl font-bold text-cyan-400">
                {globalStats.responseTime}min
              </p>
            </div>
            <Clock className="w-8 h-8 text-cyan-400" />
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
              État du système de sécurité
            </h3>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              {globalStats.systemHealth === 'healthy' ? 'Tous les systèmes fonctionnent normalement' : 'Problème détecté'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              Taux de détection
            </div>
            <div className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>
              {globalStats.detectionRate}%
            </div>
          </div>
          
          <div className="text-right">
            <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              Temps de réponse moyen
            </div>
            <div className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>
              {globalStats.responseTime} min
            </div>
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
        <SecurityHeader />
        <SystemStatus />
        <TabNavigation />
        
        {/* Contenu principal */}
        <div className="space-y-6">
          {renderActiveComponent()}
        </div>
      </div>
    </div>
  );
};

export default SecurityModern;