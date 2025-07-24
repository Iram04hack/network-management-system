// QoSDashboard.jsx - Dashboard QoS avec métriques temps réel
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  Gauge, 
  TrendingUp, 
  TrendingDown, 
  Wifi, 
  Monitor, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  RefreshCw,
  Settings,
  Filter,
  Calendar,
  BarChart3,
  PieChart,
  LineChart,
  Zap,
  Signal,
  Target,
  Globe,
  Server,
  Network,
  Router,
  Database,
  Eye,
  Play,
  Pause,
  Download,
  Upload,
  Users,
  Shield,
  Award,
  Layers
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const QoSDashboard = ({ isVisible = true }) => {
  const [realTimeMetrics, setRealTimeMetrics] = useState({});
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
  const [timeRange, setTimeRange] = useState('1h');
  const [selectedInterface, setSelectedInterface] = useState('all');
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [loading, setLoading] = useState(false);

  const { getThemeClasses } = useTheme();

  // Interfaces réseau mockées
  const networkInterfaces = [
    { id: 'eth0', name: 'Ethernet 0', type: 'ethernet', status: 'active', speed: 1000 },
    { id: 'eth1', name: 'Ethernet 1', type: 'ethernet', status: 'active', speed: 1000 },
    { id: 'eth2', name: 'Ethernet 2', type: 'ethernet', status: 'inactive', speed: 1000 },
    { id: 'wlan0', name: 'WiFi 0', type: 'wireless', status: 'active', speed: 300 }
  ];

  // Métriques temps réel mockées
  const mockMetrics = {
    totalBandwidth: 1000,
    usedBandwidth: 658,
    availableBandwidth: 342,
    totalConnections: 156,
    activeFlows: 89,
    queuedPackets: 234,
    droppedPackets: 12,
    averageLatency: 15.6,
    jitter: 2.3,
    packetLoss: 0.8,
    qualityScore: 92.5,
    priorityTraffic: 45,
    normalTraffic: 55,
    lowPriorityTraffic: 22
  };

  // Données historiques pour graphiques
  const historicalData = {
    '1h': Array.from({ length: 12 }, (_, i) => ({
      time: new Date(Date.now() - (11 - i) * 5 * 60 * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      bandwidth: Math.floor(Math.random() * 800) + 200,
      latency: Math.floor(Math.random() * 20) + 5,
      throughput: Math.floor(Math.random() * 900) + 100,
      packetLoss: Math.random() * 2,
      jitter: Math.random() * 5
    })),
    '24h': Array.from({ length: 24 }, (_, i) => ({
      time: `${i}:00`,
      bandwidth: Math.floor(Math.random() * 800) + 200,
      latency: Math.floor(Math.random() * 20) + 5,
      throughput: Math.floor(Math.random() * 900) + 100,
      packetLoss: Math.random() * 2,
      jitter: Math.random() * 5
    })),
    '7d': Array.from({ length: 7 }, (_, i) => ({
      time: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'][i],
      bandwidth: Math.floor(Math.random() * 800) + 200,
      latency: Math.floor(Math.random() * 20) + 5,
      throughput: Math.floor(Math.random() * 900) + 100,
      packetLoss: Math.random() * 2,
      jitter: Math.random() * 5
    }))
  };

  // Données de répartition du trafic
  const trafficDistribution = [
    { name: 'Voix', value: 156, color: '#3B82F6', priority: 'high' },
    { name: 'Vidéo', value: 289, color: '#10B981', priority: 'high' },
    { name: 'Données', value: 178, color: '#F59E0B', priority: 'medium' },
    { name: 'Autre', value: 67, color: '#6B7280', priority: 'low' }
  ];

  // Données de performance par interface
  const interfacePerformance = networkInterfaces.map(iface => ({
    name: iface.name,
    utilization: Math.floor(Math.random() * 80) + 10,
    speed: iface.speed,
    status: iface.status,
    packets: Math.floor(Math.random() * 10000) + 1000,
    errors: Math.floor(Math.random() * 10)
  }));

  // Simulation des données temps réel
  useEffect(() => {
    if (!isRealTimeEnabled) return;

    const interval = setInterval(() => {
      setRealTimeMetrics(prev => ({
        ...mockMetrics,
        usedBandwidth: Math.floor(Math.random() * 800) + 200,
        activeFlows: Math.floor(Math.random() * 100) + 50,
        averageLatency: Math.floor(Math.random() * 30) + 5,
        jitter: Math.random() * 5,
        packetLoss: Math.random() * 2,
        qualityScore: Math.floor(Math.random() * 20) + 80
      }));
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [isRealTimeEnabled, refreshInterval]);

  // Initialisation des données
  useEffect(() => {
    setRealTimeMetrics(mockMetrics);
  }, []);

  // Fonction de calcul du pourcentage d'utilisation
  const getUtilizationPercentage = (used, total) => {
    return total > 0 ? (used / total) * 100 : 0;
  };

  // Fonction de détermination du statut basé sur les métriques
  const getMetricStatus = (value, thresholds) => {
    if (value <= thresholds.good) return 'good';
    if (value <= thresholds.warning) return 'warning';
    return 'critical';
  };

  // Seuils pour les métriques
  const thresholds = {
    latency: { good: 20, warning: 50 },
    jitter: { good: 2, warning: 5 },
    packetLoss: { good: 1, warning: 3 },
    bandwidth: { good: 70, warning: 85 }
  };

  // Composant des métriques principales
  const MainMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
            Bande Passante
          </h3>
          <Gauge className="w-5 h-5 text-blue-400" />
        </div>
        <div className="flex items-center space-x-2 mb-2">
          <span className="text-2xl font-bold text-blue-400">
            {realTimeMetrics.usedBandwidth}
          </span>
          <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
            / {realTimeMetrics.totalBandwidth} Mbps
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${getUtilizationPercentage(realTimeMetrics.usedBandwidth, realTimeMetrics.totalBandwidth)}%` }}
          ></div>
        </div>
        <p className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
          {getUtilizationPercentage(realTimeMetrics.usedBandwidth, realTimeMetrics.totalBandwidth).toFixed(1)}% utilisé
        </p>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
            Latence Moyenne
          </h3>
          <Clock className="w-5 h-5 text-green-400" />
        </div>
        <div className="flex items-center space-x-2 mb-2">
          <span className={`text-2xl font-bold ${
            getMetricStatus(realTimeMetrics.averageLatency, thresholds.latency) === 'good' ? 'text-green-400' :
            getMetricStatus(realTimeMetrics.averageLatency, thresholds.latency) === 'warning' ? 'text-yellow-400' :
            'text-red-400'
          }`}>
            {realTimeMetrics.averageLatency}
          </span>
          <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>ms</span>
        </div>
        <div className="flex items-center space-x-1">
          {getMetricStatus(realTimeMetrics.averageLatency, thresholds.latency) === 'good' ? (
            <CheckCircle className="w-4 h-4 text-green-400" />
          ) : getMetricStatus(realTimeMetrics.averageLatency, thresholds.latency) === 'warning' ? (
            <AlertTriangle className="w-4 h-4 text-yellow-400" />
          ) : (
            <XCircle className="w-4 h-4 text-red-400" />
          )}
          <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
            {getMetricStatus(realTimeMetrics.averageLatency, thresholds.latency) === 'good' ? 'Excellent' :
             getMetricStatus(realTimeMetrics.averageLatency, thresholds.latency) === 'warning' ? 'Correct' : 'Critique'}
          </span>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
            Perte de Paquets
          </h3>
          <TrendingDown className="w-5 h-5 text-red-400" />
        </div>
        <div className="flex items-center space-x-2 mb-2">
          <span className={`text-2xl font-bold ${
            getMetricStatus(realTimeMetrics.packetLoss, thresholds.packetLoss) === 'good' ? 'text-green-400' :
            getMetricStatus(realTimeMetrics.packetLoss, thresholds.packetLoss) === 'warning' ? 'text-yellow-400' :
            'text-red-400'
          }`}>
            {realTimeMetrics.packetLoss?.toFixed(1)}
          </span>
          <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>%</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
            {realTimeMetrics.droppedPackets} paquets perdus
          </span>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
            Score Qualité
          </h3>
          <Award className="w-5 h-5 text-purple-400" />
        </div>
        <div className="flex items-center space-x-2 mb-2">
          <span className={`text-2xl font-bold ${
            realTimeMetrics.qualityScore >= 90 ? 'text-green-400' :
            realTimeMetrics.qualityScore >= 70 ? 'text-yellow-400' :
            'text-red-400'
          }`}>
            {realTimeMetrics.qualityScore?.toFixed(1)}
          </span>
          <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>/ 100</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              realTimeMetrics.qualityScore >= 90 ? 'bg-green-600' :
              realTimeMetrics.qualityScore >= 70 ? 'bg-yellow-600' :
              'bg-red-600'
            }`}
            style={{ width: `${realTimeMetrics.qualityScore}%` }}
          ></div>
        </div>
      </div>
    </div>
  );

  // Composant de contrôle du monitoring
  const MonitoringControls = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
              Monitoring temps réel
            </span>
            <button
              onClick={() => setIsRealTimeEnabled(!isRealTimeEnabled)}
              className={`flex items-center space-x-2 px-3 py-1 rounded text-sm transition-colors ${
                isRealTimeEnabled 
                  ? 'bg-red-600 hover:bg-red-700 text-white' 
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isRealTimeEnabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              <span>{isRealTimeEnabled ? 'Arrêter' : 'Démarrer'}</span>
            </button>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              Intervalle:
            </span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value={1}>1s</option>
              <option value={5}>5s</option>
              <option value={10}>10s</option>
              <option value={30}>30s</option>
            </select>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={selectedInterface}
            onChange={(e) => setSelectedInterface(e.target.value)}
            className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="all">Toutes les interfaces</option>
            {networkInterfaces.map(iface => (
              <option key={iface.id} value={iface.id}>{iface.name}</option>
            ))}
          </select>
          
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="1h">1 heure</option>
            <option value="24h">24 heures</option>
            <option value="7d">7 jours</option>
          </select>
        </div>
      </div>
    </div>
  );

  // Composant des graphiques de performance
  const PerformanceCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Utilisation Bande Passante
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={historicalData[timeRange]}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '4px',
                  color: '#fff'
                }}
              />
              <Area 
                type="monotone" 
                dataKey="bandwidth" 
                stroke="#3B82F6" 
                fill="#3B82F6" 
                fillOpacity={0.3}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Latence et Jitter
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsLineChart data={historicalData[timeRange]}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="time" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '4px',
                  color: '#fff'
                }}
              />
              <Line type="monotone" dataKey="latency" stroke="#10B981" strokeWidth={2} />
              <Line type="monotone" dataKey="jitter" stroke="#F59E0B" strokeWidth={2} />
            </RechartsLineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Répartition du Trafic
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsPieChart>
              <Pie
                data={trafficDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {trafficDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </RechartsPieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Performance Interfaces
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={interfacePerformance}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '4px',
                  color: '#fff'
                }}
              />
              <Bar dataKey="utilization" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  // Composant de statut des interfaces
  const InterfaceStatus = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
        État des Interfaces Réseau
      </h3>
      <div className="space-y-3">
        {networkInterfaces.map(iface => {
          const performance = interfacePerformance.find(p => p.name === iface.name);
          return (
            <div key={iface.id} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  {iface.type === 'ethernet' ? (
                    <Network className="w-5 h-5 text-blue-400" />
                  ) : (
                    <Wifi className="w-5 h-5 text-green-400" />
                  )}
                  <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                    {iface.name}
                  </span>
                </div>
                <div className={`w-2 h-2 rounded-full ${
                  iface.status === 'active' ? 'bg-green-400' : 'bg-red-400'
                }`}></div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Utilisation
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {performance?.utilization}%
                  </div>
                </div>
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Vitesse
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {iface.speed} Mbps
                  </div>
                </div>
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Paquets
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {performance?.packets?.toLocaleString()}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Dashboard QoS
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Surveillance de la qualité de service en temps réel
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setLoading(true)}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Actualiser</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Settings className="w-4 h-4" />
            <span>Configurer</span>
          </button>
        </div>
      </div>

      <MainMetrics />
      <MonitoringControls />
      <PerformanceCharts />
      <InterfaceStatus />
    </div>
  );
};

export default QoSDashboard;