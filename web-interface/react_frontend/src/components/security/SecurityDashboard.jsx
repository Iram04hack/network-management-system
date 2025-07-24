// SecurityDashboard.jsx - Dashboard sécurité avec détection temps réel
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Shield, 
  AlertTriangle, 
  Activity, 
  Bell, 
  Eye, 
  EyeOff,
  RefreshCw,
  Play,
  Pause,
  Settings,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  Target,
  Globe,
  Server,
  Lock,
  Unlock,
  Search,
  Filter
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const SecurityDashboard = ({ isVisible = true }) => {
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
  const [alertsFilter, setAlertsFilter] = useState('all');
  const [timeRange, setTimeRange] = useState('24h');
  const [liveAlerts, setLiveAlerts] = useState([]);
  const [securityMetrics, setSecurityMetrics] = useState({});
  const [intrusionStats, setIntrusionStats] = useState({});
  const [loading, setLoading] = useState(false);

  const { getThemeClasses } = useTheme();

  // Données mockées pour le dashboard sécurité
  const mockSecurityData = {
    metrics: {
      totalAlerts: 1247,
      criticalAlerts: 23,
      activeIncidents: 7,
      blockedThreats: 856,
      detectionRate: 94.2,
      responseTime: 2.3,
      falsePositives: 12,
      systemHealth: 'healthy'
    },
    threatTypes: [
      { name: 'Malware', value: 35, color: '#EF4444' },
      { name: 'Phishing', value: 28, color: '#F59E0B' },
      { name: 'Intrusion', value: 22, color: '#8B5CF6' },
      { name: 'DDoS', value: 10, color: '#3B82F6' },
      { name: 'Autres', value: 5, color: '#10B981' }
    ],
    alertTrends: [
      { time: '00:00', alerts: 12, blocked: 8, allowed: 4 },
      { time: '04:00', alerts: 8, blocked: 5, allowed: 3 },
      { time: '08:00', alerts: 25, blocked: 18, allowed: 7 },
      { time: '12:00', alerts: 45, blocked: 32, allowed: 13 },
      { time: '16:00', alerts: 38, blocked: 28, allowed: 10 },
      { time: '20:00', alerts: 22, blocked: 15, allowed: 7 }
    ],
    topThreats: [
      { ip: '203.0.113.1', country: 'Unknown', attempts: 156, severity: 'critical', type: 'Brute Force' },
      { ip: '198.51.100.5', country: 'CN', attempts: 89, severity: 'high', type: 'Port Scan' },
      { ip: '192.0.2.10', country: 'RU', attempts: 67, severity: 'medium', type: 'Malware' },
      { ip: '203.0.113.25', country: 'US', attempts: 45, severity: 'high', type: 'DDoS' }
    ]
  };

  // Simulation des alertes temps réel
  useEffect(() => {
    if (!isRealTimeEnabled) return;

    const interval = setInterval(() => {
      const alertTypes = ['Intrusion Detected', 'Malware Blocked', 'Suspicious Activity', 'Port Scan', 'Brute Force'];
      const severities = ['critical', 'high', 'medium', 'low'];
      const sources = ['External', '203.0.113.1', '198.51.100.5', '192.0.2.10', 'Internal'];

      const newAlert = {
        id: Date.now(),
        type: alertTypes[Math.floor(Math.random() * alertTypes.length)],
        severity: severities[Math.floor(Math.random() * severities.length)],
        source: sources[Math.floor(Math.random() * sources.length)],
        timestamp: new Date().toISOString(),
        message: `Security event detected from ${sources[Math.floor(Math.random() * sources.length)]}`,
        status: 'new'
      };

      setLiveAlerts(prev => [newAlert, ...prev.slice(0, 49)]); // Garder les 50 dernières alertes
    }, 2000 + Math.random() * 3000); // Intervalles variables

    return () => clearInterval(interval);
  }, [isRealTimeEnabled]);

  // Composant de métriques principales
  const SecurityMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
            Alertes Totales
          </h3>
          <Bell className="w-5 h-5 text-blue-400" />
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-2xl font-bold text-blue-400">
            {mockSecurityData.metrics.totalAlerts.toLocaleString()}
          </span>
          <TrendingUp className="w-4 h-4 text-green-400" />
        </div>
        <p className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
          +12% depuis hier
        </p>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
            Alertes Critiques
          </h3>
          <AlertTriangle className="w-5 h-5 text-red-400" />
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-2xl font-bold text-red-400">
            {mockSecurityData.metrics.criticalAlerts}
          </span>
          <TrendingDown className="w-4 h-4 text-red-400" />
        </div>
        <p className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
          -3% depuis hier
        </p>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
            Menaces Bloquées
          </h3>
          <Shield className="w-5 h-5 text-green-400" />
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-2xl font-bold text-green-400">
            {mockSecurityData.metrics.blockedThreats}
          </span>
          <TrendingUp className="w-4 h-4 text-green-400" />
        </div>
        <p className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
          +8% depuis hier
        </p>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between mb-2">
          <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
            Taux de Détection
          </h3>
          <Target className="w-5 h-5 text-purple-400" />
        </div>
        <div className="flex items-center space-x-2">
          <span className="text-2xl font-bold text-purple-400">
            {mockSecurityData.metrics.detectionRate}%
          </span>
          <TrendingUp className="w-4 h-4 text-green-400" />
        </div>
        <p className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
          +2.1% depuis hier
        </p>
      </div>
    </div>
  );

  // Composant d'alertes temps réel
  const RealTimeAlerts = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
            Alertes Temps Réel
          </h3>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
            {isRealTimeEnabled ? 'Surveillance active' : 'Surveillance désactivée'}
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <select
            value={alertsFilter}
            onChange={(e) => setAlertsFilter(e.target.value)}
            className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="all">Toutes</option>
            <option value="critical">Critiques</option>
            <option value="high">Élevées</option>
            <option value="medium">Moyennes</option>
          </select>
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
      </div>

      <div className="max-h-96 overflow-y-auto space-y-2">
        {liveAlerts.length > 0 ? (
          liveAlerts
            .filter(alert => alertsFilter === 'all' || alert.severity === alertsFilter)
            .map(alert => (
              <div
                key={alert.id}
                className={`flex items-center space-x-3 p-3 rounded border-l-4 ${
                  alert.severity === 'critical' ? 'border-red-500 bg-red-900/20' :
                  alert.severity === 'high' ? 'border-orange-500 bg-orange-900/20' :
                  alert.severity === 'medium' ? 'border-yellow-500 bg-yellow-900/20' :
                  'border-blue-500 bg-blue-900/20'
                } hover:bg-opacity-30 transition-colors`}
              >
                <div className={`p-2 rounded-full ${
                  alert.severity === 'critical' ? 'bg-red-500' :
                  alert.severity === 'high' ? 'bg-orange-500' :
                  alert.severity === 'medium' ? 'bg-yellow-500' :
                  'bg-blue-500'
                }`}>
                  <AlertCircle className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className={`${getThemeClasses('text', 'dashboard')} font-medium text-sm`}>
                      {alert.type}
                    </span>
                    <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                    {alert.message}
                  </p>
                </div>
              </div>
            ))
        ) : (
          <div className="text-center py-8">
            <Shield className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <p className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
              {isRealTimeEnabled ? 'En attente d\'alertes...' : 'Activez la surveillance temps réel'}
            </p>
          </div>
        )}
      </div>
    </div>
  );

  // Composant des menaces principales
  const TopThreats = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Menaces Principales
        </h3>
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="1h">1 heure</option>
          <option value="24h">24 heures</option>
          <option value="7d">7 jours</option>
          <option value="30d">30 jours</option>
        </select>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700">
              <th className={`text-left py-2 px-3 ${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                IP Source
              </th>
              <th className={`text-left py-2 px-3 ${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Pays
              </th>
              <th className={`text-left py-2 px-3 ${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Tentatives
              </th>
              <th className={`text-left py-2 px-3 ${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Type
              </th>
              <th className={`text-left py-2 px-3 ${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                Sévérité
              </th>
            </tr>
          </thead>
          <tbody>
            {mockSecurityData.topThreats.map((threat, index) => (
              <tr key={index} className={`border-b border-gray-700 hover:bg-gray-700/50 transition-colors`}>
                <td className={`py-2 px-3 ${getThemeClasses('text', 'dashboard')} font-mono text-sm`}>
                  {threat.ip}
                </td>
                <td className={`py-2 px-3 ${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                  {threat.country}
                </td>
                <td className={`py-2 px-3 ${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                  {threat.attempts}
                </td>
                <td className={`py-2 px-3 ${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                  {threat.type}
                </td>
                <td className="py-2 px-3">
                  <span className={`px-2 py-1 text-xs rounded ${
                    threat.severity === 'critical' ? 'bg-red-900/30 text-red-400' :
                    threat.severity === 'high' ? 'bg-orange-900/30 text-orange-400' :
                    'bg-yellow-900/30 text-yellow-400'
                  }`}>
                    {threat.severity}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  // Composant des graphiques
  const SecurityCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Tendances des Alertes
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockSecurityData.alertTrends}>
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
              <Line type="monotone" dataKey="alerts" stroke="#3B82F6" strokeWidth={2} />
              <Line type="monotone" dataKey="blocked" stroke="#10B981" strokeWidth={2} />
              <Line type="monotone" dataKey="allowed" stroke="#F59E0B" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Types de Menaces
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={mockSecurityData.threatTypes}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {mockSecurityData.threatTypes.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Dashboard Sécurité
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Surveillance et détection des menaces en temps réel
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

      <SecurityMetrics />

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        <RealTimeAlerts />
        <TopThreats />
      </div>

      <SecurityCharts />
    </div>
  );
};

export default SecurityDashboard;