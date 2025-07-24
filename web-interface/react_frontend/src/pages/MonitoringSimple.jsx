// MonitoringSimple.jsx - Module de Surveillance avec variables globales API unifiées
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  Monitor, 
  AlertTriangle, 
  RefreshCw, 
  Server, 
  Database, 
  TrendingUp, 
  CheckCircle,
  AlertCircle,
  XCircle
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

// Import des variables globales API unifiées
import {
  systemMetrics,
  dockerServices,
  totalServices,
  healthyServices,
  healthPercentage,
  systemAlerts,
  totalAlerts,
  criticalAlerts,
  warningAlerts,
  systemOperational,
  overallHealth,
  lastUpdate,
  errors,
  refreshAllData
} from '../services/UnifiedApiData';

import { useTheme } from '../contexts/ThemeContext';

const MonitoringSimple = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const { getThemeClasses } = useTheme();
  
  // Force l'actualisation de l'affichage
  const [, forceUpdate] = useState({});
  const refreshComponent = useCallback(() => forceUpdate({}), []);
  
  // Actualiser le composant toutes les 3 secondes
  useEffect(() => {
    const interval = setInterval(refreshComponent, 3000);
    return () => clearInterval(interval);
  }, [refreshComponent]);
  
  // Fonction de refresh manuel
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refreshAllData();
    } catch (error) {
      console.error('Erreur lors de l\'actualisation:', error);
    }
    setIsRefreshing(false);
  }, []);
  
  // Données historiques pour les graphiques (générées depuis les métriques actuelles)
  const historicalData = React.useMemo(() => {
    const now = new Date();
    return Array.from({ length: 12 }, (_, i) => {
      const time = new Date(now.getTime() - (11 - i) * 5 * 60 * 1000);
      const variation = Math.sin((i / 11) * Math.PI * 2) * 10;
      return {
        time: time.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        cpu: Math.max(0, Math.min(100, systemMetrics.cpu.current + variation)),
        memory: Math.max(0, Math.min(100, systemMetrics.memory.current + variation * 0.8)),
        network: Math.max(0, systemMetrics.network.current + variation * 2)
      };
    });
  }, [systemMetrics]);

  const renderOverview = () => (
    <div className="space-y-6">
      
      {/* Métriques rapides */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className={`${getThemeClasses('card', 'monitoring')} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-sm font-medium`}>
                CPU Système
              </p>
              <p className="text-2xl font-bold text-blue-400">
                {systemMetrics.cpu.current}%
              </p>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-xs mt-1`}>
                Tendance: {systemMetrics.cpu.trend}
              </p>
            </div>
            <Monitor className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'monitoring')} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-sm font-medium`}>
                Mémoire
              </p>
              <p className="text-2xl font-bold text-green-400">
                {systemMetrics.memory.current}%
              </p>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-xs mt-1`}>
                Max: {systemMetrics.memory.max}%
              </p>
            </div>
            <Database className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'monitoring')} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-sm font-medium`}>
                Services Docker
              </p>
              <p className="text-2xl font-bold text-purple-400">
                {healthyServices}/{totalServices}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-xs mt-1`}>
                {healthPercentage.toFixed(1)}% sains
              </p>
            </div>
            <Server className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'monitoring')} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-sm font-medium`}>
                Alertes Actives
              </p>
              <p className="text-2xl font-bold text-orange-400">
                {totalAlerts}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-xs mt-1`}>
                {criticalAlerts} critiques
              </p>
            </div>
            <AlertTriangle className="w-8 h-8 text-orange-400" />
          </div>
        </div>
      </div>

      {/* Graphiques */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className={`${getThemeClasses('card', 'monitoring')} p-6`}>
          <h3 className={`${getThemeClasses('text', 'monitoring')} text-lg font-semibold mb-4`}>
            Métriques Système (5 min)
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="cpu" stroke="#3B82F6" strokeWidth={2} name="CPU %" />
              <Line type="monotone" dataKey="memory" stroke="#10B981" strokeWidth={2} name="RAM %" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className={`${getThemeClasses('card', 'monitoring')} p-6`}>
          <h3 className={`${getThemeClasses('text', 'monitoring')} text-lg font-semibold mb-4`}>
            État des Services
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {dockerServices.slice(0, 8).map((service, index) => (
              <div key={service.id || index} className="flex items-center justify-between p-2 bg-gray-700/30 rounded">
                <div className="flex items-center space-x-3">
                  {service.health_status === 'healthy' ? (
                    <CheckCircle className="w-4 h-4 text-green-400" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-400" />
                  )}
                  <span className="text-sm font-medium truncate">{service.name}</span>
                </div>
                <div className="text-right text-xs text-gray-400">
                  <div>CPU: {service.cpu_percent?.toFixed(1) || 0}%</div>
                  <div>RAM: {service.memory_percent?.toFixed(1) || 0}%</div>
                </div>
              </div>
            ))}
            {dockerServices.length > 8 && (
              <p className="text-gray-400 text-xs text-center">... et {dockerServices.length - 8} autres services</p>
            )}
          </div>
        </div>
      </div>

      {/* Alertes récentes */}
      <div className={`${getThemeClasses('card', 'monitoring')} p-6`}>
        <h3 className={`${getThemeClasses('text', 'monitoring')} text-lg font-semibold mb-4`}>
          Alertes Récentes
        </h3>
        <div className="space-y-3">
          {systemAlerts.length > 0 ? (
            systemAlerts.slice(0, 5).map((alert, index) => (
              <div key={alert.id || index} className="flex items-center space-x-3 p-3 bg-gray-700/30 rounded">
                <AlertTriangle className={`w-5 h-5 ${
                  alert.severity === 'critical' ? 'text-red-400' : 
                  alert.severity === 'warning' ? 'text-orange-400' : 'text-yellow-400'
                }`} />
                <div className="flex-1">
                  <p className={`${getThemeClasses('text', 'monitoring')} font-medium text-sm`}>
                    {alert.title || alert.message || `Alerte #${index + 1}`}
                  </p>
                  <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-xs`}>
                    {alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString('fr-FR') : 'Maintenant'}
                    {alert.source && <span className="ml-2 bg-gray-700 px-1 rounded">{alert.source}</span>}
                  </p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8">
              <CheckCircle className="w-12 h-12 text-green-400 mx-auto mb-3" />
              <p className={`${getThemeClasses('text', 'monitoring')} font-medium`}>
                Aucune alerte active
              </p>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-sm mt-1`}>
                Tous les systèmes fonctionnent normalement
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderAlerts = () => (
    <div className="space-y-6">
      <div className={`${getThemeClasses('card', 'monitoring')} p-6`}>
        <h3 className={`${getThemeClasses('text', 'monitoring')} text-lg font-semibold mb-4`}>
          Toutes les Alertes ({totalAlerts})
        </h3>
        <div className="space-y-3">
          {systemAlerts.map((alert, index) => (
            <div key={alert.id || index} className="flex items-start space-x-3 p-4 bg-gray-700/30 rounded-lg">
              <AlertTriangle className={`w-5 h-5 mt-1 ${
                alert.severity === 'critical' ? 'text-red-400' : 
                alert.severity === 'warning' ? 'text-orange-400' : 'text-yellow-400'
              }`} />
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className={`${getThemeClasses('text', 'monitoring')} font-medium`}>
                    {alert.title || alert.message || `Alerte #${index + 1}`}
                  </h4>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    alert.severity === 'critical' ? 'bg-red-600/20 text-red-400' :
                    alert.severity === 'warning' ? 'bg-orange-600/20 text-orange-400' :
                    'bg-yellow-600/20 text-yellow-400'
                  }`}>
                    {alert.severity}
                  </span>
                </div>
                <p className={`${getThemeClasses('textSecondary', 'monitoring')} text-sm mt-1`}>
                  {alert.equipment && <span>Équipement: {alert.equipment} • </span>}
                  {alert.timestamp ? new Date(alert.timestamp).toLocaleString('fr-FR') : 'Maintenant'}
                </p>
                {alert.source && (
                  <span className="inline-block mt-2 px-2 py-1 bg-gray-700 rounded text-xs">
                    Source: {alert.source}
                  </span>
                )}
              </div>
            </div>
          ))}
          {systemAlerts.length === 0 && (
            <div className="text-center py-12">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <p className={`${getThemeClasses('text', 'monitoring')} text-lg font-medium`}>
                Aucune alerte active
              </p>
              <p className={`${getThemeClasses('textSecondary', 'monitoring')} mt-2`}>
                Votre système fonctionne parfaitement
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className={`min-h-screen ${getThemeClasses('background', 'monitoring')} p-6`}>
      <div className="max-w-7xl mx-auto">
        
        {/* En-tête */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className={`${getThemeClasses('text', 'monitoring')} text-3xl font-bold`}>
              Monitoring Unifié
            </h1>
            <p className={`${getThemeClasses('textSecondary', 'monitoring')} mt-1`}>
              Surveillance temps réel de votre infrastructure
            </p>
          </div>
          <div className="flex items-center space-x-4">
            {/* État du système */}
            <div className="flex items-center space-x-2">
              <div className={`w-3 h-3 rounded-full ${systemOperational ? 'bg-green-400' : 'bg-red-400'} animate-pulse`}></div>
              <span className={`${getThemeClasses('textSecondary', 'monitoring')} text-sm`}>
                Système {systemOperational ? 'opérationnel' : 'en panne'}
              </span>
            </div>
            
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={`flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors ${
                isRefreshing ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Actualiser</span>
            </button>
          </div>
        </div>

        {/* Onglets */}
        <div className="flex space-x-1 mb-6 bg-gray-800/50 p-1 rounded-lg">
          {[
            { id: 'overview', label: 'Vue d\'ensemble', icon: Activity },
            { id: 'alerts', label: `Alertes (${totalAlerts})`, icon: AlertTriangle }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                  activeTab === tab.id 
                    ? 'bg-blue-600 text-white shadow-md' 
                    : `${getThemeClasses('textSecondary', 'monitoring')} hover:bg-gray-700/50 hover:text-white`
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Contenu des onglets */}
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'alerts' && renderAlerts()}

        {/* Dernière mise à jour */}
        <div className={`${getThemeClasses('card', 'monitoring')} p-4 mt-6`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className={`${getThemeClasses('textSecondary', 'monitoring')} text-sm`}>
                Dernière mise à jour:
              </span>
              <span className={`${getThemeClasses('text', 'monitoring')} text-sm`}>
                {lastUpdate.systemMetrics ? 
                  new Date(lastUpdate.systemMetrics).toLocaleTimeString('fr-FR') : 
                  'Jamais'
                }
              </span>
            </div>
            {errors.systemMetrics && (
              <span className="text-red-400 text-sm">
                Erreur: {errors.systemMetrics}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MonitoringSimple;