/**
 * SystemDashboard - Tableau de bord système simplifié
 */

import React, { useState, useEffect } from 'react';
import { 
  Monitor, 
  Server, 
  Database, 
  Activity, 
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  TrendingUp,
  TrendingDown,
  Cpu,
  HardDrive,
  Wifi
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const SystemDashboard = () => {
  const { getThemeClasses } = useTheme();
  
  // État simulé du système
  const [systemData, setSystemData] = useState({
    cpu: { current: 42, trend: 'stable' },
    memory: { current: 68, trend: 'increasing' },
    disk: { current: 75, trend: 'stable' },
    network: { current: 23, trend: 'decreasing' },
    services: {
      total: 12,
      running: 11,
      stopped: 1,
      healthy: 10
    },
    uptime: '15 jours, 8 heures',
    lastUpdate: new Date().toISOString()
  });

  const [isAutoRefresh, setIsAutoRefresh] = useState(true);
  
  // Données pour les graphiques
  const [chartData] = useState([
    { time: '00:00', cpu: 25, memory: 60, network: 15 },
    { time: '04:00', cpu: 30, memory: 65, network: 20 },
    { time: '08:00', cpu: 45, memory: 70, network: 35 },
    { time: '12:00', cpu: 42, memory: 68, network: 23 },
    { time: '16:00', cpu: 38, memory: 66, network: 18 },
    { time: '20:00', cpu: 35, memory: 64, network: 12 }
  ]);

  // Simulation de mise à jour des données
  useEffect(() => {
    if (!isAutoRefresh) return;

    const interval = setInterval(() => {
      setSystemData(prev => ({
        ...prev,
        cpu: {
          ...prev.cpu,
          current: Math.max(0, Math.min(100, prev.cpu.current + (Math.random() - 0.5) * 10))
        },
        memory: {
          ...prev.memory,
          current: Math.max(0, Math.min(100, prev.memory.current + (Math.random() - 0.5) * 5))
        },
        network: {
          ...prev.network,
          current: Math.max(0, Math.min(100, prev.network.current + (Math.random() - 0.5) * 15))
        },
        lastUpdate: new Date().toISOString()
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, [isAutoRefresh]);

  const getStatusColor = (value) => {
    if (value >= 80) return 'text-red-400';
    if (value >= 60) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'increasing': return <TrendingUp className="w-4 h-4 text-red-400" />;
      case 'decreasing': return <TrendingDown className="w-4 h-4 text-green-400" />;
      default: return <Activity className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`${getThemeClasses('text', 'dashboard')} text-3xl font-bold`}>
            Tableau de Bord Système
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Vue d'ensemble des performances système (données simulées)
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsAutoRefresh(!isAutoRefresh)}
            className={`flex items-center space-x-2 px-3 py-2 rounded transition-colors ${
              isAutoRefresh 
                ? 'bg-green-600 hover:bg-green-700 text-white' 
                : 'border border-gray-600 hover:border-gray-500'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span className="text-sm">Auto-refresh</span>
          </button>
        </div>
      </div>

      {/* Métriques principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Cpu className="w-8 h-8 text-blue-400" />
              <div>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>CPU</p>
                <p className={`text-2xl font-bold ${getStatusColor(systemData.cpu.current)}`}>
                  {systemData.cpu.current.toFixed(1)}%
                </p>
              </div>
            </div>
            {getTrendIcon(systemData.cpu.trend)}
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${systemData.cpu.current}%` }}
            />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Database className="w-8 h-8 text-green-400" />
              <div>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Mémoire</p>
                <p className={`text-2xl font-bold ${getStatusColor(systemData.memory.current)}`}>
                  {systemData.memory.current.toFixed(1)}%
                </p>
              </div>
            </div>
            {getTrendIcon(systemData.memory.trend)}
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${systemData.memory.current}%` }}
            />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <HardDrive className="w-8 h-8 text-purple-400" />
              <div>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Disque</p>
                <p className={`text-2xl font-bold ${getStatusColor(systemData.disk.current)}`}>
                  {systemData.disk.current}%
                </p>
              </div>
            </div>
            {getTrendIcon(systemData.disk.trend)}
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-purple-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${systemData.disk.current}%` }}
            />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <Wifi className="w-8 h-8 text-orange-400" />
              <div>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Réseau</p>
                <p className={`text-2xl font-bold ${getStatusColor(systemData.network.current)}`}>
                  {systemData.network.current.toFixed(1)}%
                </p>
              </div>
            </div>
            {getTrendIcon(systemData.network.trend)}
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-orange-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${systemData.network.current}%` }}
            />
          </div>
        </div>
      </div>

      {/* Services système */}
      <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
        <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold mb-4`}>
          État des Services
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="flex items-center space-x-3 p-4 bg-gray-700/30 rounded">
            <Server className="w-8 h-8 text-blue-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total</p>
              <p className="text-lg font-bold">{systemData.services.total}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-4 bg-gray-700/30 rounded">
            <CheckCircle className="w-8 h-8 text-green-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>En marche</p>
              <p className="text-lg font-bold text-green-400">{systemData.services.running}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-4 bg-gray-700/30 rounded">
            <AlertTriangle className="w-8 h-8 text-red-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Arrêtés</p>
              <p className="text-lg font-bold text-red-400">{systemData.services.stopped}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-4 bg-gray-700/30 rounded">
            <Monitor className="w-8 h-8 text-blue-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Sains</p>
              <p className="text-lg font-bold text-blue-400">{systemData.services.healthy}</p>
            </div>
          </div>
        </div>
        
        <div className="mt-4 flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span>Uptime: {systemData.uptime}</span>
          </div>
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-5 h-5 text-blue-400" />
            <span>Dernière mise à jour: {new Date(systemData.lastUpdate).toLocaleTimeString()}</span>
          </div>
        </div>
      </div>

      {/* Graphique de performance */}
      <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
        <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold mb-4`}>
          Historique des Performances
        </h2>
        
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="cpu" stroke="#3B82F6" strokeWidth={2} name="CPU %" />
            <Line type="monotone" dataKey="memory" stroke="#10B981" strokeWidth={2} name="Mémoire %" />
            <Line type="monotone" dataKey="network" stroke="#F59E0B" strokeWidth={2} name="Réseau %" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default SystemDashboard;