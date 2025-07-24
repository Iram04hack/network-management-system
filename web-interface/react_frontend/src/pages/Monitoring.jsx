import React, { useState, useEffect } from 'react';
import { 
  Monitor, 
  Activity, 
  Server, 
  AlertTriangle, 
  TrendingUp, 
  Database,
  Cpu,
  HardDrive,
  Network,
  Shield,
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Pause,
  Save,
  RefreshCw,
  Settings,
  Clock,
  Eye,
  Bell
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { useTheme } from '../contexts/ThemeContext';

const Monitoring = () => {
  const { getThemeClasses } = useTheme();
  
  // États locaux pour la navigation et contrôles
  const [activeTab, setActiveTab] = useState('overview');
  const [isLoading, setIsLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [timeRange, setTimeRange] = useState('1h');
  
  // Données mockées pour les statistiques de monitoring selon l'architecture
  const [monitoringStats] = useState({
    totalDevices: 42,
    onlineDevices: 39,
    warningDevices: 2,
    offlineDevices: 1,
    activeAlerts: 8,
    criticalAlerts: 2,
    warningAlerts: 4,
    infoAlerts: 2,
    averageCpu: 34.5,
    averageMemory: 67.2,
    averageDisk: 45.8,
    networkThroughput: 892.4,
    systemUptime: 99.7,
    performanceIndex: 87.3
  });

  // Données mockées pour les métriques système temps réel
  const [systemMetrics] = useState({
    cpu: [
      { time: '14:00', value: 25, threshold_warning: 75, threshold_critical: 90 },
      { time: '14:15', value: 32, threshold_warning: 75, threshold_critical: 90 },
      { time: '14:30', value: 28, threshold_warning: 75, threshold_critical: 90 },
      { time: '14:45', value: 35, threshold_warning: 75, threshold_critical: 90 },
      { time: '15:00', value: 31, threshold_warning: 75, threshold_critical: 90 },
      { time: '15:15', value: 29, threshold_warning: 75, threshold_critical: 90 }
    ],
    memory: [
      { time: '14:00', value: 60, threshold_warning: 80, threshold_critical: 95 },
      { time: '14:15', value: 65, threshold_warning: 80, threshold_critical: 95 },
      { time: '14:30', value: 68, threshold_warning: 80, threshold_critical: 95 },
      { time: '14:45', value: 72, threshold_warning: 80, threshold_critical: 95 },
      { time: '15:00', value: 70, threshold_warning: 80, threshold_critical: 95 },
      { time: '15:15', value: 67, threshold_warning: 80, threshold_critical: 95 }
    ],
    network: [
      { time: '14:00', inbound: 450, outbound: 320 },
      { time: '14:15', inbound: 620, outbound: 480 },
      { time: '14:30', inbound: 890, outbound: 650 },
      { time: '14:45', inbound: 750, outbound: 580 },
      { time: '15:00', inbound: 680, outbound: 520 },
      { time: '15:15', inbound: 820, outbound: 640 }
    ],
    disk: [
      { time: '14:00', usage: 42 },
      { time: '14:15', usage: 44 },
      { time: '14:30', usage: 46 },
      { time: '14:45', usage: 45 },
      { time: '15:00', usage: 47 },
      { time: '15:15', usage: 46 }
    ]
  });

  // Alertes récentes mockées selon l'architecture
  const [monitoringAlerts] = useState([
    {
      id: 'alert-1',
      type: 'critical',
      title: 'CPU critique sur Server-DB-01',
      metric: 'CPU',
      currentValue: 94,
      threshold: 90,
      equipment: 'Server-DB-01',
      location: 'Datacenter A',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      status: 'active',
      description: 'Utilisation processeur exceptionnellement élevée détectée'
    },
    {
      id: 'alert-2', 
      type: 'warning',
      title: 'Mémoire élevée Infrastructure',
      metric: 'Memory',
      currentValue: 85,
      threshold: 80,
      equipment: 'Infrastructure-Core',
      location: 'Salle serveurs',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      status: 'acknowledged',
      description: 'Consommation mémoire au-dessus du seuil configuré'
    },
    {
      id: 'alert-3',
      type: 'warning', 
      title: 'Trafic réseau anormal',
      metric: 'Network',
      currentValue: 1650,
      threshold: 1500,
      equipment: 'Switch-Core-01',
      location: 'Réseau principal',
      timestamp: new Date(Date.now() - 900000).toISOString(),
      status: 'investigating',
      description: 'Augmentation significative du trafic réseau détectée'
    },
    {
      id: 'alert-4',
      type: 'info',
      title: 'Maintenance planifiée',
      metric: 'System',
      equipment: 'Cluster-Web',
      location: 'Production',
      timestamp: new Date(Date.now() - 1200000).toISOString(),
      status: 'scheduled',
      description: 'Redémarrage de maintenance programmé pour ce soir'
    },
    {
      id: 'alert-5',
      type: 'warning',
      title: 'Espace disque faible',
      metric: 'Disk',
      currentValue: 87,
      threshold: 85,
      equipment: 'Storage-01',
      location: 'Stockage principal',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      status: 'active',
      description: 'Espace disque disponible inférieur au seuil configuré'
    }
  ]);

  // Données pour les graphiques de distribution
  const [resourceDistribution] = useState([
    { name: 'CPU', value: 34, color: '#3B82F6' },
    { name: 'Mémoire', value: 67, color: '#10B981' },
    { name: 'Disque', value: 46, color: '#F59E0B' },
    { name: 'Réseau', value: 52, color: '#8B5CF6' }
  ]);

  // Configuration des onglets selon l'architecture
  const tabs = [
    {
      id: 'overview',
      label: 'Vue d\'ensemble',
      icon: Monitor,
      description: 'Aperçu général des métriques de surveillance système'
    },
    {
      id: 'metrics',
      label: 'Métriques',
      icon: Activity,
      description: 'Métriques détaillées de performance par composant'
    },
    {
      id: 'alerts',
      label: 'Alertes',
      icon: AlertTriangle,
      description: 'Gestion et configuration des alertes de surveillance'
    },
    {
      id: 'history',
      label: 'Historique',
      icon: TrendingUp,
      description: 'Analyse historique et tendances des métriques'
    }
  ];

  // Configuration des seuils d'alertes
  const [alertThresholds, setAlertThresholds] = useState({
    cpu: { warning: 75, critical: 90 },
    memory: { warning: 80, critical: 95 }, 
    disk: { warning: 85, critical: 95 },
    network: { warning: 1500, critical: 2000 }
  });

  // Fonctions utilitaires
  const getAlertColor = (type) => {
    switch (type) {
      case 'critical': return 'text-red-400';
      case 'warning': return 'text-yellow-400';
      case 'info': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-red-400';
      case 'acknowledged': return 'text-yellow-400';
      case 'investigating': return 'text-purple-400';
      case 'scheduled': return 'text-blue-400';
      case 'resolved': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const getMetricIcon = (metric) => {
    switch (metric?.toLowerCase()) {
      case 'cpu': return Cpu;
      case 'memory': return Database;
      case 'disk': return HardDrive;
      case 'network': return Network;
      case 'system': return Server;
      default: return Activity;
    }
  };

  // Header avec statistiques selon le modèle QoS
  const Header = () => (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className={`${getThemeClasses('text', 'dashboard')} text-3xl font-bold`}>
            Surveillance & Monitoring
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Surveillance temps réel des métriques système et infrastructure (données simulées)
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center space-x-2 px-3 py-2 rounded transition-colors ${
              autoRefresh 
                ? 'bg-green-600 hover:bg-green-700 text-white' 
                : 'border border-gray-600 hover:border-gray-500'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span className="text-sm">Auto-refresh</span>
          </button>
          
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <RefreshCw className="w-4 h-4" />
            <span className="text-sm">Actualiser</span>
          </button>
        </div>
      </div>

      {/* Statistiques de monitoring */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Server className="w-8 h-8 text-blue-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Équipements</p>
              <p className="text-lg font-bold text-blue-400">{monitoringStats.onlineDevices}/{monitoringStats.totalDevices}</p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>En ligne</p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <AlertTriangle className="w-8 h-8 text-red-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Alertes</p>
              <p className="text-lg font-bold text-red-400">
                {monitoringStats.criticalAlerts}/{monitoringStats.activeAlerts}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Critiques</p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Cpu className="w-8 h-8 text-green-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>CPU Moyen</p>
              <p className="text-lg font-bold text-green-400">{monitoringStats.averageCpu}%</p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Infrastructure</p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-purple-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Performance</p>
              <p className="text-lg font-bold text-purple-400">{monitoringStats.performanceIndex}%</p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Index global</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Navigation par onglets identique à QoS
  const TabNavigation = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} mb-6`}>
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex space-x-1">
          {tabs.map(tab => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
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
      </div>
      
      <div className="p-4">
        <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
          {tabs.find(tab => tab.id === activeTab)?.description}
        </p>
      </div>
    </div>
  );

  // Contenu des onglets
  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Métriques système temps réel */}
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Métriques Temps Réel
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={systemMetrics.cpu}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="value" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.3} name="CPU %" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Trafic réseau */}
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Trafic Réseau
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={systemMetrics.network}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="inbound" stroke="#10B981" strokeWidth={2} name="Entrant (MB/s)" />
                    <Line type="monotone" dataKey="outbound" stroke="#F59E0B" strokeWidth={2} name="Sortant (MB/s)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Distribution des ressources */}
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Utilisation des Ressources
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={resourceDistribution}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({name, value}) => `${name}: ${value}%`}
                    >
                      {resourceDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Alertes récentes */}
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Alertes Récentes
                </h3>
                <div className="space-y-3">
                  {monitoringAlerts.slice(0, 4).map(alert => {
                    const MetricIcon = getMetricIcon(alert.metric);
                    return (
                      <div key={alert.id} className="flex items-start space-x-3 p-3 bg-gray-700/30 rounded">
                        <MetricIcon className={`w-5 h-5 mt-0.5 ${getAlertColor(alert.type)}`} />
                        <div className="flex-1">
                          <div className="flex items-center justify-between">
                            <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium text-sm`}>
                              {alert.title}
                            </h4>
                            <span className={`text-xs font-medium ${getStatusColor(alert.status)}`}>
                              {alert.status}
                            </span>
                          </div>
                          <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                            {alert.equipment} - {alert.description}
                          </p>
                          <div className="flex items-center justify-between mt-2 text-xs">
                            <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
                              {alert.location}
                            </span>
                            <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
                              {new Date(alert.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        );

      case 'metrics':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Métriques CPU */}
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Utilisation CPU
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={systemMetrics.cpu}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={3} name="CPU %" />
                    <Line type="monotone" dataKey="threshold_warning" stroke="#F59E0B" strokeDasharray="5 5" strokeWidth={1} name="Seuil Warning" />
                    <Line type="monotone" dataKey="threshold_critical" stroke="#EF4444" strokeDasharray="5 5" strokeWidth={1} name="Seuil Critical" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Métriques Mémoire */}
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Utilisation Mémoire
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={systemMetrics.memory}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Line type="monotone" dataKey="value" stroke="#10B981" strokeWidth={3} name="Mémoire %" />
                    <Line type="monotone" dataKey="threshold_warning" stroke="#F59E0B" strokeDasharray="5 5" strokeWidth={1} name="Seuil Warning" />
                    <Line type="monotone" dataKey="threshold_critical" stroke="#EF4444" strokeDasharray="5 5" strokeWidth={1} name="Seuil Critical" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              {/* Métriques Disque */}
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Utilisation Disque
                </h3>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={systemMetrics.disk}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Bar dataKey="usage" fill="#F59E0B" name="Disque %" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Statistiques détaillées */}
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Statistiques Détaillées
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-3 bg-gray-700/30 rounded">
                    <div className="flex items-center space-x-3">
                      <Cpu className="w-5 h-5 text-blue-400" />
                      <span>CPU Moyen</span>
                    </div>
                    <span className="font-bold text-blue-400">{monitoringStats.averageCpu}%</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-700/30 rounded">
                    <div className="flex items-center space-x-3">
                      <Database className="w-5 h-5 text-green-400" />
                      <span>Mémoire Moyenne</span>
                    </div>
                    <span className="font-bold text-green-400">{monitoringStats.averageMemory}%</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-700/30 rounded">
                    <div className="flex items-center space-x-3">
                      <HardDrive className="w-5 h-5 text-orange-400" />
                      <span>Disque Moyen</span>
                    </div>
                    <span className="font-bold text-orange-400">{monitoringStats.averageDisk}%</span>
                  </div>
                  <div className="flex items-center justify-between p-3 bg-gray-700/30 rounded">
                    <div className="flex items-center space-x-3">
                      <Network className="w-5 h-5 text-purple-400" />
                      <span>Débit Réseau</span>
                    </div>
                    <span className="font-bold text-purple-400">{monitoringStats.networkThroughput} MB/s</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        );

      case 'alerts':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
                Alertes de Surveillance Configurées
              </h2>
              <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
                <Plus className="w-4 h-4" />
                <span>Nouvelle Alerte</span>
              </button>
            </div>
            
            {/* Configuration des seuils */}
            <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
              <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                Configuration des Seuils
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(alertThresholds).map(([metric, thresholds]) => (
                  <div key={metric} className="space-y-3 p-4 bg-gray-700/30 rounded">
                    <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium capitalize`}>
                      {metric === 'cpu' ? 'CPU' : metric === 'network' ? 'Réseau' : metric}
                    </h4>
                    <div className="space-y-2">
                      <div>
                        <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs block mb-1`}>
                          Seuil Warning ({metric === 'network' ? 'MB/s' : '%'})
                        </label>
                        <input
                          type="number"
                          value={thresholds.warning}
                          className="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                        />
                      </div>
                      <div>
                        <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs block mb-1`}>
                          Seuil Critical ({metric === 'network' ? 'MB/s' : '%'})
                        </label>
                        <input
                          type="number"
                          value={thresholds.critical}
                          className="w-full px-2 py-1 bg-gray-700 border border-gray-600 rounded text-white text-sm"
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Liste des alertes */}
            <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden`}>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700/50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Alerte
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Équipement
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Valeur
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Statut
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {monitoringAlerts.map(alert => (
                      <tr key={alert.id} className="hover:bg-gray-700/30">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-3">
                            <AlertTriangle className={`w-5 h-5 ${getAlertColor(alert.type)}`} />
                            <div>
                              <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                                {alert.title}
                              </div>
                              <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                                {alert.description}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-medium ${getAlertColor(alert.type)}`}>
                            {alert.type}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <div>
                            <div>{alert.equipment}</div>
                            <div className="text-xs text-gray-400">{alert.location}</div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {alert.currentValue && alert.threshold ? (
                            <span className={getAlertColor(alert.type)}>
                              {alert.currentValue}/{alert.threshold}
                              {alert.metric === 'Network' ? ' MB/s' : '%'}
                            </span>
                          ) : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-medium ${getStatusColor(alert.status)}`}>
                            {alert.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                          <button className="text-blue-400 hover:text-blue-300">
                            <Eye className="w-4 h-4" />
                          </button>
                          <button className="text-green-400 hover:text-green-300">
                            <Bell className="w-4 h-4" />
                          </button>
                          <button className="text-gray-400 hover:text-gray-300">
                            <Settings className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );

      case 'history':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
                Historique des Métriques
              </h2>
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="px-3 py-2 bg-gray-700 border border-gray-600 rounded text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1h">Dernière heure</option>
                <option value="6h">6 Heures</option>
                <option value="24h">24 Heures</option>
                <option value="7d">7 Jours</option>
                <option value="30d">30 Jours</option>
              </select>
            </div>

            <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
              <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                Tendances Historiques - CPU et Mémoire
              </h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={systemMetrics.cpu}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} name="CPU %" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Évolution du Trafic Réseau
                </h3>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={systemMetrics.network}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="inbound" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
                    <Area type="monotone" dataKey="outbound" stackId="1" stroke="#F59E0B" fill="#F59E0B" fillOpacity={0.6} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Statistiques de Performance
                </h3>
                <div className="space-y-4">
                  <div className="text-center p-4 bg-gray-700/30 rounded">
                    <div className="text-2xl font-bold text-blue-400 mb-1">
                      {monitoringStats.systemUptime}%
                    </div>
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                      Uptime Système
                    </div>
                  </div>
                  <div className="text-center p-4 bg-gray-700/30 rounded">
                    <div className="text-2xl font-bold text-green-400 mb-1">
                      {monitoringStats.performanceIndex}%
                    </div>
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                      Index de Performance
                    </div>
                  </div>
                  <div className="text-center p-4 bg-gray-700/30 rounded">
                    <div className="text-2xl font-bold text-purple-400 mb-1">
                      {monitoringStats.activeAlerts}
                    </div>
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                      Alertes Actives
                    </div>
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
    <div className="p-6 space-y-6">
      <Header />
      <TabNavigation />
      {renderTabContent()}
    </div>
  );
};

export default Monitoring;