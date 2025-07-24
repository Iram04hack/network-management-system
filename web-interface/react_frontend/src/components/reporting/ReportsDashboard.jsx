// ReportsDashboard.jsx - Dashboard des rapports avec analytics avancées
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  FileText, 
  Calendar, 
  Users, 
  Download, 
  Upload, 
  RefreshCw, 
  Settings, 
  Eye, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Zap, 
  Target, 
  Database, 
  Server, 
  Globe, 
  Mail, 
  Share, 
  Filter, 
  Search, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Pause, 
  Square, 
  Maximize, 
  Minimize2, 
  PieChart, 
  LineChart, 
  BarChart, 
  FileImage, 
  FileSpreadsheet, 
  Award, 
  Layers, 
  HardDrive, 
  Cpu, 
  MemoryStick, 
  Network, 
  Shield, 
  Bell, 
  Info, 
  Star, 
  Bookmark, 
  Tag, 
  Hash
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart as RechartsBarChart, Bar, PieChart as RechartsPieChart, Pie, Cell, AreaChart, Area, ComposedChart, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const ReportsDashboard = ({ isVisible = true }) => {
  const [timeRange, setTimeRange] = useState('30d');
  const [selectedMetric, setSelectedMetric] = useState('generation');
  const [isRealTime, setIsRealTime] = useState(false);
  const [dashboardData, setDashboardData] = useState({
    totalReports: 2847,
    generatedThisMonth: 423,
    scheduledActive: 24,
    storageUsed: 15.6,
    downloadCount: 8294,
    shareCount: 1567,
    avgGenerationTime: 2.4,
    successRate: 96.8,
    userEngagement: 78.2,
    costSavings: 34.5,
    automationRate: 67.3,
    errorRate: 3.2
  });
  const [reportStats, setReportStats] = useState({});
  const [trendData, setTrendData] = useState([]);
  const [popularReports, setPopularReports] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(false);

  const { getThemeClasses } = useTheme();

  // Statistiques mockées du dashboard
  const mockDashboardData = {
    totalReports: 2847,
    generatedThisMonth: 423,
    scheduledActive: 24,
    storageUsed: 15.6, // GB
    downloadCount: 8294,
    shareCount: 1567,
    avgGenerationTime: 2.4, // minutes
    successRate: 96.8,
    userEngagement: 78.2,
    costSavings: 34.5, // %
    automationRate: 67.3,
    errorRate: 3.2
  };

  // Données de tendances
  const mockTrendData = [
    { date: '2024-01-01', generated: 45, downloaded: 78, shared: 23, errors: 2, users: 12 },
    { date: '2024-01-02', generated: 52, downloaded: 89, shared: 31, errors: 1, users: 15 },
    { date: '2024-01-03', generated: 38, downloaded: 65, shared: 18, errors: 3, users: 11 },
    { date: '2024-01-04', generated: 67, downloaded: 112, shared: 45, errors: 2, users: 18 },
    { date: '2024-01-05', generated: 78, downloaded: 134, shared: 52, errors: 1, users: 22 },
    { date: '2024-01-06', generated: 56, downloaded: 98, shared: 34, errors: 4, users: 16 },
    { date: '2024-01-07', generated: 89, downloaded: 156, shared: 67, errors: 2, users: 24 },
    { date: '2024-01-08', generated: 73, downloaded: 127, shared: 43, errors: 3, users: 19 },
    { date: '2024-01-09', generated: 91, downloaded: 168, shared: 72, errors: 1, users: 26 },
    { date: '2024-01-10', generated: 64, downloaded: 111, shared: 38, errors: 2, users: 17 },
    { date: '2024-01-11', generated: 82, downloaded: 145, shared: 59, errors: 3, users: 21 },
    { date: '2024-01-12', generated: 95, downloaded: 178, shared: 81, errors: 1, users: 28 },
    { date: '2024-01-13', generated: 71, downloaded: 125, shared: 46, errors: 2, users: 18 },
    { date: '2024-01-14', generated: 88, downloaded: 152, shared: 64, errors: 4, users: 23 },
    { date: '2024-01-15', generated: 103, downloaded: 189, shared: 89, errors: 2, users: 31 }
  ];

  // Rapports populaires
  const mockPopularReports = [
    {
      id: 'rpt-001',
      name: 'Rapport Mensuel Performance',
      category: 'Performance',
      downloads: 1247,
      shares: 234,
      rating: 4.8,
      trend: 15.3,
      lastGenerated: '2024-01-15T10:30:00Z',
      avgSize: '2.4 MB',
      format: 'PDF',
      icon: BarChart3,
      color: '#3B82F6'
    },
    {
      id: 'rpt-002',
      name: 'Analyse Sécurité Hebdomadaire',
      category: 'Sécurité',
      downloads: 892,
      shares: 167,
      rating: 4.6,
      trend: -8.2,
      lastGenerated: '2024-01-15T08:00:00Z',
      avgSize: '1.8 MB',
      format: 'PDF',
      icon: Shield,
      color: '#EF4444'
    },
    {
      id: 'rpt-003',
      name: 'Inventaire Équipements',
      category: 'Inventaire',
      downloads: 567,
      shares: 89,
      rating: 4.4,
      trend: 22.7,
      lastGenerated: '2024-01-14T16:45:00Z',
      avgSize: '3.1 MB',
      format: 'Excel',
      icon: Database,
      color: '#10B981'
    },
    {
      id: 'rpt-004',
      name: 'Tableau de Bord Exécutif',
      category: 'Management',
      downloads: 423,
      shares: 145,
      rating: 4.9,
      trend: 31.5,
      lastGenerated: '2024-01-15T07:00:00Z',
      avgSize: '1.2 MB',
      format: 'PDF',
      icon: Award,
      color: '#8B5CF6'
    },
    {
      id: 'rpt-005',
      name: 'Analyse Trafic Réseau',
      category: 'Réseau',
      downloads: 345,
      shares: 78,
      rating: 4.3,
      trend: 5.8,
      lastGenerated: '2024-01-15T12:15:00Z',
      avgSize: '2.8 MB',
      format: 'PDF',
      icon: Network,
      color: '#F59E0B'
    }
  ];

  // Activités récentes
  const mockRecentActivity = [
    {
      id: 'act-001',
      type: 'generation',
      title: 'Rapport Performance généré',
      description: 'Par Jean Dupont',
      timestamp: '2024-01-15T10:30:00Z',
      icon: FileText,
      color: '#3B82F6',
      status: 'success'
    },
    {
      id: 'act-002',
      type: 'schedule',
      title: 'Planification activée',
      description: 'Rapport Sécurité Hebdomadaire',
      timestamp: '2024-01-15T09:45:00Z',
      icon: Calendar,
      color: '#10B981',
      status: 'info'
    },
    {
      id: 'act-003',
      type: 'error',
      title: 'Erreur de génération',
      description: 'Rapport Inventaire - Données insuffisantes',
      timestamp: '2024-01-15T09:15:00Z',
      icon: AlertTriangle,
      color: '#EF4444',
      status: 'error'
    },
    {
      id: 'act-004',
      type: 'share',
      title: 'Rapport partagé',
      description: 'Tableau de Bord Exécutif - 5 destinataires',
      timestamp: '2024-01-15T08:30:00Z',
      icon: Share,
      color: '#8B5CF6',
      status: 'success'
    },
    {
      id: 'act-005',
      type: 'download',
      title: 'Téléchargement multiple',
      description: '12 rapports téléchargés par l\'équipe',
      timestamp: '2024-01-15T08:00:00Z',
      icon: Download,
      color: '#06B6D4',
      status: 'info'
    }
  ];

  // Prédictions IA
  const mockPredictions = [
    {
      id: 'pred-001',
      type: 'capacity',
      title: 'Capacité de stockage',
      prediction: 'Atteindra 85% dans 45 jours',
      confidence: 89,
      impact: 'medium',
      recommendation: 'Planifier l\'archivage des anciens rapports',
      icon: HardDrive,
      color: '#F59E0B'
    },
    {
      id: 'pred-002',
      type: 'usage',
      title: 'Pic d\'utilisation',
      prediction: 'Augmentation de 35% la semaine prochaine',
      confidence: 76,
      impact: 'high',
      recommendation: 'Optimiser les ressources de génération',
      icon: TrendingUp,
      color: '#3B82F6'
    },
    {
      id: 'pred-003',
      type: 'automation',
      title: 'Opportunité d\'automatisation',
      prediction: '8 rapports manuels peuvent être automatisés',
      confidence: 94,
      impact: 'high',
      recommendation: 'Créer des planifications pour ces rapports',
      icon: Zap,
      color: '#10B981'
    }
  ];

  // Distribution des formats
  const formatDistribution = [
    { name: 'PDF', value: 65, color: '#EF4444' },
    { name: 'Excel', value: 25, color: '#10B981' },
    { name: 'CSV', value: 10, color: '#3B82F6' }
  ];

  // Distribution des catégories
  const categoryDistribution = [
    { name: 'Performance', value: 35, color: '#3B82F6' },
    { name: 'Sécurité', value: 25, color: '#EF4444' },
    { name: 'Inventaire', value: 20, color: '#10B981' },
    { name: 'Management', value: 15, color: '#8B5CF6' },
    { name: 'Réseau', value: 5, color: '#F59E0B' }
  ];

  // Initialisation
  useEffect(() => {
    setDashboardData(mockDashboardData);
    setTrendData(mockTrendData);
    setPopularReports(mockPopularReports);
    setRecentActivity(mockRecentActivity);
    setPredictions(mockPredictions);
  }, []);

  // Simulation temps réel
  useEffect(() => {
    if (!isRealTime) return;

    const interval = setInterval(() => {
      setDashboardData(prev => ({
        ...prev,
        generatedThisMonth: prev.generatedThisMonth + Math.floor(Math.random() * 3),
        downloadCount: prev.downloadCount + Math.floor(Math.random() * 5),
        shareCount: prev.shareCount + Math.floor(Math.random() * 2)
      }));
    }, 10000);

    return () => clearInterval(interval);
  }, [isRealTime]);

  // Fonctions utilitaires
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

  const getTrendIcon = (trend) => {
    return trend > 0 ? TrendingUp : TrendingDown;
  };

  const getTrendColor = (trend) => {
    return trend > 0 ? '#10B981' : '#EF4444';
  };

  // Composant des métriques principales
  const MainMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total Rapports</p>
            <p className="text-2xl font-bold text-blue-400">{formatNumber(dashboardData.totalReports)}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              +{dashboardData.generatedThisMonth} ce mois
            </p>
          </div>
          <FileText className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Téléchargements</p>
            <p className="text-2xl font-bold text-green-400">{formatNumber(dashboardData.downloadCount)}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              {formatNumber(dashboardData.shareCount)} partages
            </p>
          </div>
          <Download className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Taux de Succès</p>
            <p className="text-2xl font-bold text-purple-400">{dashboardData.successRate}%</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              {dashboardData.avgGenerationTime}min moyen
            </p>
          </div>
          <CheckCircle className="w-8 h-8 text-purple-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Automatisation</p>
            <p className="text-2xl font-bold text-orange-400">{dashboardData.automationRate}%</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              {dashboardData.scheduledActive} planifiés
            </p>
          </div>
          <Zap className="w-8 h-8 text-orange-400" />
        </div>
      </div>
    </div>
  );

  // Composant des contrôles
  const DashboardControls = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
              Période d'analyse
            </span>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="7d">7 derniers jours</option>
              <option value="30d">30 derniers jours</option>
              <option value="90d">90 derniers jours</option>
              <option value="1y">1 an</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              Métrique:
            </span>
            <select
              value={selectedMetric}
              onChange={(e) => setSelectedMetric(e.target.value)}
              className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="generation">Génération</option>
              <option value="downloads">Téléchargements</option>
              <option value="shares">Partages</option>
              <option value="users">Utilisateurs</option>
              <option value="errors">Erreurs</option>
            </select>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsRealTime(!isRealTime)}
            className={`flex items-center space-x-2 px-3 py-1 rounded text-sm transition-colors ${
              isRealTime 
                ? 'bg-green-600 hover:bg-green-700 text-white' 
                : 'border border-gray-600 hover:border-gray-500'
            }`}
          >
            {isRealTime ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span>Temps réel</span>
          </button>
          
          <button
            onClick={() => setLoading(true)}
            className="flex items-center space-x-2 px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Actualiser</span>
          </button>
        </div>
      </div>
    </div>
  );

  // Composant des graphiques analytiques
  const AnalyticsCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Tendances d'Activité
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="date" 
                stroke="#9CA3AF" 
                fontSize={12}
                tickFormatter={(value) => new Date(value).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' })}
              />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '4px',
                  color: '#fff'
                }}
                labelFormatter={(value) => new Date(value).toLocaleDateString('fr-FR')}
              />
              <Area 
                type="monotone" 
                dataKey={selectedMetric} 
                fill="#3B82F6" 
                fillOpacity={0.3}
                stroke="#3B82F6"
                strokeWidth={2}
              />
              <Line 
                type="monotone" 
                dataKey="errors" 
                stroke="#EF4444" 
                strokeWidth={2}
                dot={{ fill: '#EF4444', strokeWidth: 0, r: 3 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Distribution des Formats
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsPieChart>
              <Pie
                data={formatDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {formatDistribution.map((entry, index) => (
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
          Répartition par Catégorie
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsBarChart data={categoryDistribution}>
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
              <Bar 
                dataKey="value" 
                fill="#3B82F6"
                radius={[4, 4, 0, 0]}
              />
            </RechartsBarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Performance Système
        </h3>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                Utilisation CPU
              </span>
              <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                34.2%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: '34.2%' }}
              />
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                Mémoire
              </span>
              <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                67.8%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-300"
                style={{ width: '67.8%' }}
              />
            </div>
          </div>
          
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                Stockage ({dashboardData.storageUsed} GB)
              </span>
              <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                78.4%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-orange-500 h-2 rounded-full transition-all duration-300"
                style={{ width: '78.4%' }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Composant des rapports populaires
  const PopularReports = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Rapports Populaires
        </h3>
        <button className="text-blue-400 hover:text-blue-300 text-sm">
          Voir tous →
        </button>
      </div>
      
      <div className="space-y-3">
        {popularReports.map(report => {
          const Icon = report.icon;
          const TrendIcon = getTrendIcon(report.trend);
          
          return (
            <div key={report.id} className="flex items-center justify-between p-3 bg-gray-700/30 rounded transition-colors hover:bg-gray-700/50">
              <div className="flex items-center space-x-3">
                <div 
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${report.color}20` }}
                >
                  <Icon className="w-5 h-5" style={{ color: report.color }} />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {report.name}
                    </span>
                    <span className="px-2 py-1 bg-blue-900/30 text-blue-400 text-xs rounded">
                      {report.category}
                    </span>
                  </div>
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    {report.downloads} téléchargements • {report.shares} partages • {report.format}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="flex items-center space-x-1">
                    <Star className="w-4 h-4 text-yellow-400" />
                    <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                      {report.rating}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400">
                    {getTimeAgo(report.lastGenerated)}
                  </div>
                </div>
                
                <div className="flex items-center space-x-1">
                  <TrendIcon 
                    className="w-4 h-4" 
                    style={{ color: getTrendColor(report.trend) }}
                  />
                  <span 
                    className="text-sm font-medium"
                    style={{ color: getTrendColor(report.trend) }}
                  >
                    {Math.abs(report.trend).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Composant des prédictions IA
  const PredictionsPanel = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold flex items-center space-x-2`}>
          <Zap className="w-5 h-5 text-yellow-400" />
          <span>Prédictions IA</span>
        </h3>
        <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
          Basé sur les tendances
        </span>
      </div>
      
      <div className="space-y-3">
        {predictions.map(prediction => {
          const Icon = prediction.icon;
          
          return (
            <div key={prediction.id} className="p-4 bg-gray-700/30 rounded border-l-4" style={{ borderLeftColor: prediction.color }}>
              <div className="flex items-start space-x-3">
                <Icon className="w-5 h-5 mt-0.5" style={{ color: prediction.color }} />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {prediction.title}
                    </h4>
                    <span className="px-2 py-1 bg-gray-600 text-gray-300 text-xs rounded">
                      {prediction.confidence}% confiance
                    </span>
                  </div>
                  <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm mb-2`}>
                    {prediction.prediction}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-blue-400">
                      💡 {prediction.recommendation}
                    </span>
                    <span className={`px-2 py-1 text-xs rounded ${
                      prediction.impact === 'high' ? 'bg-red-900/30 text-red-400' :
                      prediction.impact === 'medium' ? 'bg-yellow-900/30 text-yellow-400' :
                      'bg-green-900/30 text-green-400'
                    }`}>
                      Impact {prediction.impact}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Composant des activités récentes
  const RecentActivity = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
        Activité Récente
      </h3>
      
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {recentActivity.map(activity => {
          const Icon = activity.icon;
          
          return (
            <div key={activity.id} className="flex items-center space-x-3 p-2 rounded hover:bg-gray-700/30 transition-colors">
              <div 
                className="w-8 h-8 rounded-full flex items-center justify-center"
                style={{ backgroundColor: `${activity.color}20` }}
              >
                <Icon className="w-4 h-4" style={{ color: activity.color }} />
              </div>
              <div className="flex-1">
                <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                  {activity.title}
                </div>
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  {activity.description}
                </div>
              </div>
              <div className="text-xs text-gray-400">
                {getTimeAgo(activity.timestamp)}
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
            Analytics des Rapports
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Analyse avancée et prédictions intelligentes
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Download className="w-4 h-4" />
            <span>Export Analytics</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
            <Settings className="w-4 h-4" />
            <span>Configuration</span>
          </button>
        </div>
      </div>

      <MainMetrics />
      <DashboardControls />
      <AnalyticsCharts />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <PopularReports />
          <PredictionsPanel />
        </div>
        <div>
          <RecentActivity />
        </div>
      </div>
    </div>
  );
};

export default ReportsDashboard;