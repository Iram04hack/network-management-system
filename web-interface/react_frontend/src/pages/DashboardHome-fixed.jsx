// DashboardHome.jsx - Page d'accueil du dashboard avec widgets drag & drop - VERSION CORRIGÉE
import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { 
  Shield, 
  Activity, 
  Clock, 
  AlertTriangle, 
  AlertCircle,
  Router,
  Server,
  Wifi,
  Globe,
  RefreshCw,
  Settings,
  TrendingUp,
  TrendingDown,
  Database,
  Users,
  Zap,
  Monitor
} from 'lucide-react';

// Import des composants dashboard
import DashboardGrid from '../components/dashboard/DashboardGrid';
import { 
  NetworkStatusWidget, 
  TrafficChartWidget, 
  AlertsListWidget, 
  SystemHealthWidget 
} from '../components/dashboard/widgets';

// Import des hooks
import { useDashboard } from '../hooks/useDashboard';
import { useTheme } from '../contexts/ThemeContext';

const DashboardHome = () => {
  const [timeRange, setTimeRange] = useState('1h');
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedCard, setExpandedCard] = useState(null);
  const [customWidgets, setCustomWidgets] = useState([]);
  
  // Hook pour le thème
  const { getThemeClasses, getThemeColor } = useTheme();
  
  // Hook dashboard principal
  const { 
    dashboards,
    widgets,
    loading: dashboardLoading,
    error: dashboardError,
    isAuthenticated,
    fetchDashboards,
    fetchWidgets,
    fetchAlerts
  } = useDashboard();

  // États pour les données additionnelles (mock pour maintenant)
  const [systemHealth, setSystemHealth] = useState({
    status: 'healthy',
    cpu: 45,
    memory: 62,
    disk: 78,
    network: 'stable'
  });

  const [networkOverview, setNetworkOverview] = useState({
    totalDevices: 24,
    onlineDevices: 22,
    offlineDevices: 2,
    alerts: 3
  });

  const [recentAlerts, setRecentAlerts] = useState([]);

  // Sauvegarder les widgets customisés
  const saveCustomWidgets = useCallback((newWidgets) => {
    setCustomWidgets(newWidgets);
    localStorage.setItem('dashboard-custom-widgets', JSON.stringify(newWidgets));
  }, []);

  // Ajouter un widget
  const addWidget = useCallback((widget) => {
    const newWidget = {
      ...widget,
      id: Date.now().toString(),
      position: { x: 0, y: 0 }
    };
    const updatedWidgets = [...customWidgets, newWidget];
    saveCustomWidgets(updatedWidgets);
  }, [customWidgets, saveCustomWidgets]);

  // Supprimer un widget
  const removeWidget = useCallback((widgetId) => {
    const updatedWidgets = customWidgets.filter(w => w.id !== widgetId);
    saveCustomWidgets(updatedWidgets);
  }, [customWidgets, saveCustomWidgets]);

  // Charger les données initiales
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        // Charger les widgets customisés depuis localStorage
        const savedCustomWidgets = localStorage.getItem('dashboard-custom-widgets');
        if (savedCustomWidgets) {
          try {
            setCustomWidgets(JSON.parse(savedCustomWidgets));
          } catch (error) {
            console.error('Erreur lors du chargement des widgets customisés:', error);
            setCustomWidgets([]);
          }
        }

        // Charger les alertes si authentifié
        if (isAuthenticated) {
          const alerts = await fetchAlerts();
          setRecentAlerts(alerts || []);
        }

        // Simulation de données pour les métriques système
        setSystemHealth(prev => ({
          ...prev,
          cpu: Math.floor(Math.random() * 100),
          memory: Math.floor(Math.random() * 100),
          disk: Math.floor(Math.random() * 100)
        }));

      } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
      }
    };

    loadInitialData();
  }, [isAuthenticated, fetchAlerts]);

  // Auto-refresh des données
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      try {
        if (isAuthenticated) {
          const alerts = await fetchAlerts();
          setRecentAlerts(alerts || []);
        }
        
        // Mise à jour des métriques simulées
        setSystemHealth(prev => ({
          ...prev,
          cpu: Math.max(0, Math.min(100, prev.cpu + (Math.random() - 0.5) * 10)),
          memory: Math.max(0, Math.min(100, prev.memory + (Math.random() - 0.5) * 8)),
          disk: Math.max(0, Math.min(100, prev.disk + (Math.random() - 0.5) * 2))
        }));
      } catch (error) {
        console.error('Erreur lors du refresh automatique:', error);
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, isAuthenticated, fetchAlerts]);

  // Fonction pour obtenir les widgets par défaut
  const getDefaultWidgets = useCallback(() => {
    return [
      {
        id: 'network-status',
        type: 'network-status',
        title: 'État Réseau',
        component: NetworkStatusWidget,
        size: { w: 6, h: 4 },
        position: { x: 0, y: 0 }
      },
      {
        id: 'traffic-chart',
        type: 'traffic-chart', 
        title: 'Trafic Réseau',
        component: TrafficChartWidget,
        size: { w: 6, h: 4 },
        position: { x: 6, y: 0 }
      },
      {
        id: 'alerts-list',
        type: 'alerts-list',
        title: 'Alertes Récentes',
        component: AlertsListWidget,
        size: { w: 6, h: 4 },
        position: { x: 0, y: 4 }
      },
      {
        id: 'system-health',
        type: 'system-health',
        title: 'Santé Système',
        component: SystemHealthWidget,
        size: { w: 6, h: 4 },
        position: { x: 6, y: 4 }
      }
    ];
  }, []);

  // Fonction de rafraîchissement manuel
  const handleRefresh = useCallback(async () => {
    try {
      if (isAuthenticated) {
        await fetchDashboards();
        await fetchWidgets();
        const alerts = await fetchAlerts();
        setRecentAlerts(alerts || []);
      }
    } catch (error) {
      console.error('Erreur lors du rafraîchissement:', error);
    }
  }, [isAuthenticated, fetchDashboards, fetchWidgets, fetchAlerts]);

  // Données mockées pour les graphiques
  const mockTrafficData = [
    { time: '00:00', upload: 45, download: 67 },
    { time: '04:00', upload: 52, download: 73 },
    { time: '08:00', upload: 78, download: 89 },
    { time: '12:00', upload: 65, download: 82 },
    { time: '16:00', upload: 58, download: 76 },
    { time: '20:00', upload: 43, download: 62 }
  ];

  return (
    <div className={`min-h-screen ${getThemeClasses('background', 'dashboard')} p-6`}>
      <div className="max-w-7xl mx-auto">
        
        {/* En-tête avec contrôles */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className={`${getThemeClasses('text', 'dashboard')} text-3xl font-bold`}>
              Tableau de Bord
            </h1>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
              Vue d'ensemble de votre infrastructure réseau
            </p>
          </div>
          
          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2">
              <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                Auto-refresh:
              </span>
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-3 py-1 rounded text-sm transition-colors ${
                  autoRefresh 
                    ? 'bg-green-600 hover:bg-green-700 text-white' 
                    : 'bg-gray-600 hover:bg-gray-700 text-white'
                }`}
              >
                {autoRefresh ? 'ON' : 'OFF'}
              </button>
            </div>
            
            <button
              onClick={handleRefresh}
              disabled={dashboardLoading}
              className={`flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors ${
                dashboardLoading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <RefreshCw className={`w-4 h-4 ${dashboardLoading ? 'animate-spin' : ''}`} />
              <span>Actualiser</span>
            </button>
          </div>
        </div>

        {/* Métriques rapides */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                  Appareils Réseau
                </p>
                <p className="text-2xl font-bold text-blue-400">
                  {networkOverview.onlineDevices}/{networkOverview.totalDevices}
                </p>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                  En ligne
                </p>
              </div>
              <Router className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                  CPU Système
                </p>
                <p className="text-2xl font-bold text-green-400">
                  {systemHealth.cpu}%
                </p>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                  Utilisation
                </p>
              </div>
              <Monitor className="w-8 h-8 text-green-400" />
            </div>
          </div>

          <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                  Mémoire
                </p>
                <p className="text-2xl font-bold text-purple-400">
                  {systemHealth.memory}%
                </p>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                  Utilisée
                </p>
              </div>
              <Database className="w-8 h-8 text-purple-400" />
            </div>
          </div>

          <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
            <div className="flex items-center justify-between">
              <div>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                  Alertes Actives
                </p>
                <p className="text-2xl font-bold text-orange-400">
                  {recentAlerts.length}
                </p>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                  Nécessitent attention
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-400" />
            </div>
          </div>
        </div>

        {/* Graphiques */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
            <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
              Trafic Réseau
            </h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={mockTrafficData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="upload" stroke="#3B82F6" strokeWidth={2} />
                <Line type="monotone" dataKey="download" stroke="#10B981" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
            <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
              Utilisation Système
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-2">
                  <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>CPU</span>
                  <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>{systemHealth.cpu}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                    style={{ width: `${systemHealth.cpu}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>Mémoire</span>
                  <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>{systemHealth.memory}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-green-600 h-2 rounded-full transition-all duration-500" 
                    style={{ width: `${systemHealth.memory}%` }}
                  ></div>
                </div>
              </div>
              
              <div>
                <div className="flex justify-between mb-2">
                  <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>Disque</span>
                  <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>{systemHealth.disk}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-purple-600 h-2 rounded-full transition-all duration-500" 
                    style={{ width: `${systemHealth.disk}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Dashboard avec widgets drag & drop */}
        <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
          <DashboardGrid
            widgets={customWidgets.length > 0 ? customWidgets : getDefaultWidgets()}
            onWidgetAdd={addWidget}
            onWidgetRemove={removeWidget}
            onWidgetUpdate={saveCustomWidgets}
          />
        </div>
      </div>
    </div>
  );
};

export default DashboardHome;