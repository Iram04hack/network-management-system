// PerformanceAnalysis.jsx - Analyse de performance réseau avec diagnostics automatiques
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Gauge,
  Zap,
  Target,
  Search,
  Filter,
  RefreshCw,
  Settings,
  Play,
  Pause,
  Download,
  Upload,
  Eye,
  BarChart3,
  PieChart,
  LineChart,
  Brain,
  Lightbulb,
  AlertCircle,
  CheckSquare,
  Square,
  Calendar,
  Database,
  Server,
  Network,
  Wifi,
  Globe,
  Monitor,
  Router,
  Shield,
  Users,
  Signal,
  Layers,
  FileText,
  Bell,
  Award,
  Cpu,
  HardDrive,
  MemoryStick,
  Thermometer
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell, AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const PerformanceAnalysis = ({ isVisible = true }) => {
  const [isAnalysisRunning, setIsAnalysisRunning] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisResults, setAnalysisResults] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedMetric, setSelectedMetric] = useState('latency');
  const [timeRange, setTimeRange] = useState('24h');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [selectedInterface, setSelectedInterface] = useState('all');
  const [diagnosticMode, setDiagnosticMode] = useState('comprehensive');

  const { getThemeClasses } = useTheme();

  // Métriques de performance
  const performanceMetrics = {
    latency: {
      label: 'Latence',
      unit: 'ms',
      icon: Clock,
      current: 15.6,
      target: 20,
      threshold: { good: 20, warning: 50, critical: 100 }
    },
    throughput: {
      label: 'Débit',
      unit: 'Mbps',
      icon: TrendingUp,
      current: 856,
      target: 1000,
      threshold: { good: 800, warning: 600, critical: 400 }
    },
    jitter: {
      label: 'Gigue',
      unit: 'ms',
      icon: Activity,
      current: 2.3,
      target: 5,
      threshold: { good: 5, warning: 10, critical: 20 }
    },
    packetLoss: {
      label: 'Perte de paquets',
      unit: '%',
      icon: TrendingDown,
      current: 0.8,
      target: 1,
      threshold: { good: 1, warning: 3, critical: 5 }
    },
    utilization: {
      label: 'Utilisation',
      unit: '%',
      icon: Gauge,
      current: 68,
      target: 80,
      threshold: { good: 70, warning: 85, critical: 95 }
    },
    errors: {
      label: 'Erreurs',
      unit: 'pps',
      icon: AlertTriangle,
      current: 12,
      target: 0,
      threshold: { good: 10, warning: 50, critical: 100 }
    }
  };

  // Données historiques pour les graphiques
  const generateHistoricalData = (metric, hours = 24) => {
    return Array.from({ length: hours }, (_, i) => {
      const timestamp = new Date(Date.now() - (hours - 1 - i) * 60 * 60 * 1000);
      const baseValue = performanceMetrics[metric].current;
      const variation = baseValue * 0.2 * (Math.random() - 0.5);
      
      return {
        time: timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        value: Math.max(0, baseValue + variation),
        target: performanceMetrics[metric].target,
        timestamp: timestamp.toISOString()
      };
    });
  };

  // Données d'analyse de performance par interface
  const interfaceAnalysis = [
    {
      name: 'eth0',
      type: 'ethernet',
      status: 'healthy',
      utilization: 68,
      latency: 15.6,
      throughput: 856,
      errors: 12,
      quality: 92,
      issues: []
    },
    {
      name: 'eth1',
      type: 'ethernet',
      status: 'warning',
      utilization: 89,
      latency: 45.2,
      throughput: 423,
      errors: 67,
      quality: 76,
      issues: ['Utilisation élevée', 'Latence dégradée']
    },
    {
      name: 'wlan0',
      type: 'wireless',
      status: 'critical',
      utilization: 95,
      latency: 78.9,
      throughput: 156,
      errors: 234,
      quality: 45,
      issues: ['Surcharge réseau', 'Qualité signal faible', 'Nombreuses erreurs']
    },
    {
      name: 'eth2',
      type: 'ethernet',
      status: 'healthy',
      utilization: 34,
      latency: 12.3,
      throughput: 567,
      errors: 3,
      quality: 98,
      issues: []
    }
  ];

  // Recommandations automatiques
  const mockRecommendations = [
    {
      id: 'rec-001',
      type: 'optimization',
      severity: 'high',
      title: 'Optimisation du trafic WiFi',
      description: 'L\'interface wlan0 présente une surcharge critique avec 95% d\'utilisation',
      impact: 'Performance dégradée pour les clients WiFi',
      solution: 'Redistribuer le trafic vers eth1 ou augmenter la bande passante WiFi',
      estimatedGain: '+35% performance WiFi',
      priority: 1,
      category: 'network',
      automated: true
    },
    {
      id: 'rec-002',
      type: 'configuration',
      severity: 'medium',
      title: 'Ajustement des buffers réseau',
      description: 'Les buffers de réception sont sous-dimensionnés pour eth1',
      impact: 'Latence accrue et perte de paquets occasionnelle',
      solution: 'Augmenter la taille des buffers de réception de 64KB à 128KB',
      estimatedGain: '+20% réduction latence',
      priority: 2,
      category: 'configuration',
      automated: true
    },
    {
      id: 'rec-003',
      type: 'monitoring',
      severity: 'low',
      title: 'Surveillance proactive',
      description: 'Mise en place d\'alertes prédictives pour prévenir les dégradations',
      impact: 'Prévention des problèmes avant impact utilisateur',
      solution: 'Configurer des seuils d\'alerte à 80% d\'utilisation',
      estimatedGain: '+50% temps de réaction',
      priority: 3,
      category: 'monitoring',
      automated: false
    }
  ];

  // Simulation d'analyse en cours
  const runAnalysis = useCallback(() => {
    setIsAnalysisRunning(true);
    setAnalysisProgress(0);
    
    const interval = setInterval(() => {
      setAnalysisProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsAnalysisRunning(false);
          setAnalysisResults([
            { metric: 'latency', status: 'good', value: 15.6, change: -2.3 },
            { metric: 'throughput', status: 'good', value: 856, change: +45 },
            { metric: 'jitter', status: 'good', value: 2.3, change: -0.8 },
            { metric: 'packetLoss', status: 'warning', value: 0.8, change: +0.2 },
            { metric: 'utilization', status: 'warning', value: 68, change: +8 },
            { metric: 'errors', status: 'good', value: 12, change: -5 }
          ]);
          setRecommendations(mockRecommendations);
          return 100;
        }
        return prev + Math.random() * 10;
      });
    }, 300);
  }, []);

  // Initialisation
  useEffect(() => {
    setRecommendations(mockRecommendations);
  }, []);

  // Fonction pour déterminer le statut d'une métrique
  const getMetricStatus = (metric, value) => {
    const thresholds = performanceMetrics[metric].threshold;
    if (value <= thresholds.good) return 'good';
    if (value <= thresholds.warning) return 'warning';
    return 'critical';
  };

  // Fonction pour obtenir la couleur selon le statut
  const getStatusColor = (status) => {
    switch (status) {
      case 'good': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'critical': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  // Composant des métriques de performance
  const PerformanceMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      {Object.entries(performanceMetrics).map(([key, metric]) => {
        const Icon = metric.icon;
        const status = getMetricStatus(key, metric.current);
        const percentage = (metric.current / metric.target) * 100;
        
        return (
          <div key={key} className={`${getThemeClasses('card', 'dashboard')} p-4`}>
            <div className="flex items-center justify-between mb-2">
              <h3 className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm font-medium`}>
                {metric.label}
              </h3>
              <Icon className={`w-5 h-5 ${getStatusColor(status)}`} />
            </div>
            <div className="flex items-center space-x-2 mb-2">
              <span className={`text-2xl font-bold ${getStatusColor(status)}`}>
                {metric.current}
              </span>
              <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                {metric.unit}
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2 mb-2">
              <div 
                className={`h-2 rounded-full transition-all duration-300 ${
                  status === 'good' ? 'bg-green-600' :
                  status === 'warning' ? 'bg-yellow-600' :
                  'bg-red-600'
                }`}
                style={{ width: `${Math.min(100, percentage)}%` }}
              ></div>
            </div>
            <p className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
              Cible: {metric.target}{metric.unit}
            </p>
          </div>
        );
      })}
    </div>
  );

  // Composant de contrôle d'analyse
  const AnalysisControls = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-4">
          <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
            Analyse de Performance
          </h3>
          <select
            value={diagnosticMode}
            onChange={(e) => setDiagnosticMode(e.target.value)}
            className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="quick">Analyse rapide</option>
            <option value="comprehensive">Analyse complète</option>
            <option value="deep">Analyse approfondie</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={runAnalysis}
            disabled={isAnalysisRunning}
            className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
              isAnalysisRunning 
                ? 'bg-gray-600 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white`}
          >
            {isAnalysisRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span>{isAnalysisRunning ? 'Analyse en cours...' : 'Démarrer l\'analyse'}</span>
          </button>
          
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center space-x-2 px-3 py-2 rounded transition-colors ${
              autoRefresh 
                ? 'bg-green-600 hover:bg-green-700' 
                : 'bg-gray-600 hover:bg-gray-700'
            } text-white`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            <span>Auto</span>
          </button>
        </div>
      </div>
      
      {isAnalysisRunning && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
              Progression de l'analyse
            </span>
            <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              {Math.round(analysisProgress)}%
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${analysisProgress}%` }}
            ></div>
          </div>
        </div>
      )}
      
      <div className="flex items-center space-x-4">
        <select
          value={selectedInterface}
          onChange={(e) => setSelectedInterface(e.target.value)}
          className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
        >
          <option value="all">Toutes les interfaces</option>
          {interfaceAnalysis.map(iface => (
            <option key={iface.name} value={iface.name}>{iface.name}</option>
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
        
        <select
          value={selectedMetric}
          onChange={(e) => setSelectedMetric(e.target.value)}
          className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
        >
          {Object.entries(performanceMetrics).map(([key, metric]) => (
            <option key={key} value={key}>{metric.label}</option>
          ))}
        </select>
      </div>
    </div>
  );

  // Composant des graphiques de performance
  const PerformanceCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Tendance - {performanceMetrics[selectedMetric].label}
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsLineChart data={generateHistoricalData(selectedMetric)}>
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
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name={performanceMetrics[selectedMetric].label}
              />
              <Line 
                type="monotone" 
                dataKey="target" 
                stroke="#10B981" 
                strokeWidth={1}
                strokeDasharray="5 5"
                name="Cible"
              />
            </RechartsLineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Performance par Interface
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={interfaceAnalysis}>
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
              <Bar dataKey="quality" fill="#8B5CF6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  // Composant des recommandations
  const RecommendationsList = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Recommandations IA
        </h3>
        <div className="flex items-center space-x-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
            {recommendations.length} recommandations
          </span>
        </div>
      </div>
      
      <div className="space-y-4">
        {recommendations.map(rec => (
          <div key={rec.id} className="p-4 bg-gray-700/50 rounded border-l-4 border-blue-500">
            <div className="flex items-start justify-between mb-2">
              <div className="flex items-center space-x-2">
                <Lightbulb className="w-5 h-5 text-yellow-400" />
                <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                  {rec.title}
                </span>
                <span className={`px-2 py-1 text-xs rounded ${
                  rec.severity === 'high' ? 'bg-red-900/30 text-red-400' :
                  rec.severity === 'medium' ? 'bg-yellow-900/30 text-yellow-400' :
                  'bg-green-900/30 text-green-400'
                }`}>
                  {rec.severity}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {rec.automated && (
                  <span className="px-2 py-1 bg-blue-900/30 text-blue-400 text-xs rounded">
                    Auto
                  </span>
                )}
                <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  Priorité {rec.priority}
                </span>
              </div>
            </div>
            
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm mb-2`}>
              {rec.description}
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                  Impact:
                </span>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
                  {rec.impact}
                </p>
              </div>
              <div>
                <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                  Solution:
                </span>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
                  {rec.solution}
                </p>
              </div>
            </div>
            
            <div className="flex items-center justify-between mt-3">
              <span className={`text-sm ${getThemeClasses('text', 'dashboard')} font-medium`}>
                Gain estimé: {rec.estimatedGain}
              </span>
              <div className="flex items-center space-x-2">
                <button className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded transition-colors">
                  Appliquer
                </button>
                <button className="px-3 py-1 border border-gray-600 hover:border-gray-500 text-sm rounded transition-colors">
                  Ignorer
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Composant d'analyse des interfaces
  const InterfaceAnalysis = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
        Analyse détaillée des interfaces
      </h3>
      <div className="space-y-4">
        {interfaceAnalysis.map(iface => (
          <div key={iface.name} className="p-4 bg-gray-700/50 rounded">
            <div className="flex items-center justify-between mb-3">
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
                  iface.status === 'healthy' ? 'bg-green-400' :
                  iface.status === 'warning' ? 'bg-yellow-400' :
                  'bg-red-400'
                }`}></div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Score qualité
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {iface.quality}%
                  </div>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
              <div>
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  Utilisation
                </div>
                <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                  {iface.utilization}%
                </div>
              </div>
              <div>
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  Latence
                </div>
                <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                  {iface.latency}ms
                </div>
              </div>
              <div>
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  Débit
                </div>
                <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                  {iface.throughput}Mbps
                </div>
              </div>
              <div>
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  Erreurs
                </div>
                <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                  {iface.errors}
                </div>
              </div>
            </div>
            
            {iface.issues.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {iface.issues.map((issue, index) => (
                  <span key={index} className="px-2 py-1 bg-red-900/30 text-red-400 text-xs rounded">
                    {issue}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Analyse de Performance
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Diagnostics automatiques et recommandations IA
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Download className="w-4 h-4" />
            <span>Rapport</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
            <Settings className="w-4 h-4" />
            <span>Configurer</span>
          </button>
        </div>
      </div>

      <PerformanceMetrics />
      <AnalysisControls />
      <PerformanceCharts />
      <RecommendationsList />
      <InterfaceAnalysis />
    </div>
  );
};

export default PerformanceAnalysis;