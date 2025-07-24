// ExecutiveDashboard.jsx - Tableaux de bord exécutifs pour la direction
import React, { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Users, 
  Award, 
  Target, 
  Shield, 
  Zap, 
  Activity, 
  BarChart3, 
  PieChart, 
  LineChart, 
  Globe, 
  Server, 
  Network, 
  Database, 
  Monitor, 
  Calendar, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Info, 
  Download, 
  Share, 
  Settings, 
  RefreshCw, 
  Filter, 
  Eye, 
  EyeOff, 
  Maximize, 
  Minimize2, 
  MoreHorizontal, 
  ChevronUp, 
  ChevronDown, 
  ArrowUpRight, 
  ArrowDownLeft, 
  Briefcase, 
  Building, 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Wifi, 
  Router, 
  Terminal, 
  FileText, 
  Mail, 
  Bell, 
  Star, 
  ThumbsUp, 
  ThumbsDown, 
  Layers, 
  Grid, 
  List, 
  BarChart, 
  Plus, 
  Edit, 
  Trash2, 
  Copy
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart as RechartsBarChart, Bar, PieChart as RechartsPieChart, Pie, Cell, AreaChart, Area, ComposedChart, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Treemap } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const ExecutiveDashboard = ({ isVisible = true }) => {
  const [selectedPeriod, setSelectedPeriod] = useState('quarter');
  const [selectedView, setSelectedView] = useState('overview');
  const [compactMode, setCompactMode] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [executiveData, setExecutiveData] = useState({
    systemAvailability: 99.97,
    roi: 15.8,
    securityScore: 94.2,
    costSavings: 125000,
    userSatisfaction: 88.5,
    performanceIndex: 92.3,
    complianceLevel: 96.1,
    eficiencyGain: 23.7
  });
  const [kpiTrends, setKpiTrends] = useState([]);
  const [businessMetrics, setBusinessMetrics] = useState({});
  const [riskAssessment, setRiskAssessment] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [costAnalysis, setCostAnalysis] = useState({});
  const [complianceStatus, setComplianceStatus] = useState({});
  const [loading, setLoading] = useState(false);

  const { getThemeClasses } = useTheme();

  // Données exécutives mockées
  const mockExecutiveData = {
    // KPIs Financiers
    totalCost: 2840000, // €
    costSavings: 156000, // €
    roi: 23.4, // %
    budgetUtilization: 78.2, // %
    
    // KPIs Opérationnels
    systemAvailability: 99.97, // %
    mttr: 12, // minutes
    mtbf: 2160, // heures
    incidentReduction: 34.5, // %
    
    // KPIs Sécurité
    securityScore: 94.2, // %
    threatsBlocked: 1247,
    vulnerabilities: 8,
    complianceScore: 96.8, // %
    
    // KPIs Performance
    performanceIndex: 87.3, // %
    capacityUtilization: 72.8, // %
    energyEfficiency: 23.1, // % d'amélioration
    userSatisfaction: 4.2, // /5
    
    // KPIs Stratégiques
    digitalTransformation: 67.4, // % progression
    innovationIndex: 78.9, // %
    teamProductivity: 15.6, // % amélioration
    timeToMarket: -18.3 // % réduction
  };

  // Données de tendances KPI
  const mockKpiTrends = [
    { period: 'Q1 2023', availability: 99.85, roi: 18.2, securityScore: 89.1, satisfaction: 3.8, costs: 2950000 },
    { period: 'Q2 2023', availability: 99.91, roi: 20.7, securityScore: 91.4, satisfaction: 4.0, costs: 2890000 },
    { period: 'Q3 2023', availability: 99.94, roi: 22.1, securityScore: 92.8, satisfaction: 4.1, costs: 2860000 },
    { period: 'Q4 2023', availability: 99.97, roi: 23.4, securityScore: 94.2, satisfaction: 4.2, costs: 2840000 }
  ];

  // Métriques business
  const mockBusinessMetrics = {
    revenue: {
      current: 45600000, // €
      previous: 42300000, // €
      growth: 7.8 // %
    },
    productivity: {
      current: 156.7, // indice
      previous: 135.2,
      growth: 15.9
    },
    customerSatisfaction: {
      current: 4.3, // /5
      previous: 4.0,
      growth: 7.5
    },
    marketShare: {
      current: 23.4, // %
      previous: 21.7,
      growth: 7.8
    }
  };

  // Évaluation des risques
  const mockRiskAssessment = [
    {
      id: 'risk-001',
      category: 'Cybersécurité',
      description: 'Exposition aux cybermenaces',
      level: 'medium',
      probability: 35,
      impact: 'high',
      mitigation: 'Renforcement de la sécurité en cours',
      trend: 'decreasing',
      lastUpdate: '2024-01-15T10:30:00Z'
    },
    {
      id: 'risk-002',
      category: 'Conformité',
      description: 'Évolution réglementaire RGPD',
      level: 'low',
      probability: 15,
      impact: 'medium',
      mitigation: 'Audit de conformité planifié',
      trend: 'stable',
      lastUpdate: '2024-01-14T16:45:00Z'
    },
    {
      id: 'risk-003',
      category: 'Technique',
      description: 'Obsolescence infrastructure critique',
      level: 'high',
      probability: 70,
      impact: 'high',
      mitigation: 'Plan de modernisation en cours',
      trend: 'decreasing',
      lastUpdate: '2024-01-15T09:15:00Z'
    },
    {
      id: 'risk-004',
      category: 'Opérationnel',
      description: 'Dépendance fournisseur unique',
      level: 'medium',
      probability: 45,
      impact: 'medium',
      mitigation: 'Diversification des fournisseurs',
      trend: 'stable',
      lastUpdate: '2024-01-12T11:20:00Z'
    }
  ];

  // Recommandations stratégiques
  const mockRecommendations = [
    {
      id: 'rec-001',
      priority: 'high',
      category: 'Investissement',
      title: 'Modernisation Infrastructure Cloud',
      description: 'Migration vers une architecture cloud hybride pour améliorer la scalabilité',
      impact: 'Réduction des coûts de 25% et amélioration de la résilience',
      investment: 890000,
      roi: 145,
      timeline: '18 mois',
      confidence: 92
    },
    {
      id: 'rec-002',
      priority: 'medium',
      category: 'Sécurité',
      title: 'Programme Zero Trust',
      description: 'Implémentation d\'une architecture de sécurité Zero Trust',
      impact: 'Réduction des risques de sécurité de 60%',
      investment: 340000,
      roi: 78,
      timeline: '12 mois',
      confidence: 87
    },
    {
      id: 'rec-003',
      priority: 'high',
      category: 'Automatisation',
      title: 'IA pour Opérations IT',
      description: 'Déploiement d\'outils d\'IA pour l\'automatisation des opérations',
      impact: 'Réduction du temps de résolution de 45%',
      investment: 520000,
      roi: 234,
      timeline: '15 mois',
      confidence: 89
    }
  ];

  // Analyse des coûts
  const mockCostAnalysis = {
    breakdown: [
      { category: 'Infrastructure', amount: 1420000, percentage: 50.0, trend: -3.2 },
      { category: 'Logiciels', amount: 568000, percentage: 20.0, trend: 2.1 },
      { category: 'Personnel', amount: 710000, percentage: 25.0, trend: 1.8 },
      { category: 'Maintenance', amount: 142000, percentage: 5.0, trend: -8.5 }
    ],
    yearOverYear: {
      current: 2840000,
      previous: 2950000,
      savings: 110000,
      savingsPercentage: 3.7
    },
    projections: [
      { year: '2024', projected: 2720000, optimistic: 2650000, pessimistic: 2800000 },
      { year: '2025', projected: 2590000, optimistic: 2480000, pessimistic: 2680000 },
      { year: '2026', projected: 2470000, optimistic: 2340000, pessimistic: 2580000 }
    ]
  };

  // Statut de conformité
  const mockComplianceStatus = {
    overall: 96.8,
    standards: [
      { name: 'ISO 27001', score: 98.2, status: 'compliant', lastAudit: '2023-11-15' },
      { name: 'RGPD', score: 94.7, status: 'compliant', lastAudit: '2023-12-10' },
      { name: 'SOX', score: 97.1, status: 'compliant', lastAudit: '2023-10-20' },
      { name: 'PCI DSS', score: 96.4, status: 'compliant', lastAudit: '2023-09-30' }
    ],
    gaps: [
      { area: 'Documentation', priority: 'low', impact: 'minimal' },
      { area: 'Formation personnel', priority: 'medium', impact: 'moderate' }
    ]
  };

  // Initialisation
  useEffect(() => {
    setExecutiveData(mockExecutiveData);
    setKpiTrends(mockKpiTrends);
    setBusinessMetrics(mockBusinessMetrics);
    setRiskAssessment(mockRiskAssessment);
    setRecommendations(mockRecommendations);
    setCostAnalysis(mockCostAnalysis);
    setComplianceStatus(mockComplianceStatus);
  }, []);

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // Simulation de mise à jour des données
      setExecutiveData(prev => ({
        ...prev,
        systemAvailability: Math.max(99.5, Math.min(100, prev.systemAvailability + (Math.random() - 0.5) * 0.1)),
        roi: Math.max(15, Math.min(30, prev.roi + (Math.random() - 0.5) * 2)),
        securityScore: Math.max(85, Math.min(100, prev.securityScore + (Math.random() - 0.5) * 1))
      }));
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Fonctions utilitaires
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (value, decimals = 1) => {
    if (value === undefined || value === null || isNaN(value)) return '0%';
    return `${value.toFixed(decimals)}%`;
  };

  const getTrendIcon = (value) => {
    return value > 0 ? TrendingUp : TrendingDown;
  };

  const getTrendColor = (value) => {
    return value > 0 ? '#10B981' : '#EF4444';
  };

  const getRiskColor = (level) => {
    switch (level) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return '#6B7280';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return '#6B7280';
    }
  };

  // Composant des KPIs principaux
  const ExecutiveKPIs = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Disponibilité Système</p>
            <p className="text-2xl font-bold text-green-400">
              {formatPercentage(executiveData.systemAvailability, 2)}
            </p>
            <div className="flex items-center space-x-1 mt-1">
              <TrendingUp className="w-3 h-3 text-green-400" />
              <span className="text-xs text-green-400">+0.03% vs Q3</span>
            </div>
          </div>
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>ROI IT</p>
            <p className="text-2xl font-bold text-blue-400">
              {formatPercentage(executiveData.roi)}
            </p>
            <div className="flex items-center space-x-1 mt-1">
              <TrendingUp className="w-3 h-3 text-green-400" />
              <span className="text-xs text-green-400">+1.3% vs Q3</span>
            </div>
          </div>
          <TrendingUp className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Score Sécurité</p>
            <p className="text-2xl font-bold text-purple-400">
              {formatPercentage(executiveData.securityScore)}
            </p>
            <div className="flex items-center space-x-1 mt-1">
              <TrendingUp className="w-3 h-3 text-green-400" />
              <span className="text-xs text-green-400">+1.4% vs Q3</span>
            </div>
          </div>
          <Shield className="w-8 h-8 text-purple-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Économies Réalisées</p>
            <p className="text-2xl font-bold text-orange-400">
              {formatCurrency(executiveData.costSavings)}
            </p>
            <div className="flex items-center space-x-1 mt-1">
              <TrendingUp className="w-3 h-3 text-green-400" />
              <span className="text-xs text-green-400">vs budget initial</span>
            </div>
          </div>
          <DollarSign className="w-8 h-8 text-orange-400" />
        </div>
      </div>
    </div>
  );

  // Composant des contrôles exécutifs
  const ExecutiveControls = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
              Période d'analyse
            </span>
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="quarter">Trimestre actuel</option>
              <option value="year">Année en cours</option>
              <option value="rolling">12 derniers mois</option>
              <option value="comparison">Comparaison YoY</option>
            </select>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              Vue:
            </span>
            <select
              value={selectedView}
              onChange={(e) => setSelectedView(e.target.value)}
              className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="overview">Vue d'ensemble</option>
              <option value="financial">Analyse financière</option>
              <option value="operational">Performance opérationnelle</option>
              <option value="strategic">Indicateurs stratégiques</option>
            </select>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setCompactMode(!compactMode)}
            className={`flex items-center space-x-2 px-3 py-1 rounded text-sm transition-colors ${
              compactMode 
                ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                : 'border border-gray-600 hover:border-gray-500'
            }`}
          >
            {compactMode ? <Maximize className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
            <span>{compactMode ? 'Détaillé' : 'Compact'}</span>
          </button>
          
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center space-x-2 px-3 py-1 rounded text-sm transition-colors ${
              autoRefresh 
                ? 'bg-green-600 hover:bg-green-700 text-white' 
                : 'border border-gray-600 hover:border-gray-500'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            <span>Auto-refresh</span>
          </button>
          
          <button className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
            <Download className="w-4 h-4" />
            <span>Export Exécutif</span>
          </button>
        </div>
      </div>
    </div>
  );

  // Composant des graphiques de tendances
  const TrendsCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Évolution des KPIs Clés
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={kpiTrends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="period" stroke="#9CA3AF" fontSize={12} />
              <YAxis yAxisId="left" stroke="#9CA3AF" fontSize={12} />
              <YAxis yAxisId="right" orientation="right" stroke="#9CA3AF" fontSize={12} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '4px',
                  color: '#fff'
                }}
              />
              <Bar yAxisId="left" dataKey="roi" fill="#3B82F6" name="ROI %" />
              <Line yAxisId="right" type="monotone" dataKey="availability" stroke="#10B981" strokeWidth={3} name="Disponibilité %" />
              <Line yAxisId="right" type="monotone" dataKey="securityScore" stroke="#8B5CF6" strokeWidth={2} name="Sécurité %" />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Analyse des Coûts
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={kpiTrends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="period" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '4px',
                  color: '#fff'
                }}
                formatter={(value) => [formatCurrency(value), 'Coûts']}
              />
              <Area 
                type="monotone" 
                dataKey="costs" 
                stroke="#F59E0B" 
                fill="#F59E0B" 
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  // Composant des recommandations stratégiques
  const StrategicRecommendations = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Recommandations Stratégiques
        </h3>
        <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
          Impact financier potentiel
        </span>
      </div>
      
      <div className="space-y-4">
        {recommendations.map(rec => (
          <div key={rec.id} className="p-4 bg-gray-700/30 rounded border-l-4" style={{ borderLeftColor: getPriorityColor(rec.priority) }}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <span className={`px-2 py-1 text-xs rounded ${
                    rec.priority === 'high' ? 'bg-red-900/30 text-red-400' :
                    rec.priority === 'medium' ? 'bg-yellow-900/30 text-yellow-400' :
                    'bg-green-900/30 text-green-400'
                  }`}>
                    Priorité {rec.priority === 'high' ? 'Haute' : rec.priority === 'medium' ? 'Moyenne' : 'Basse'}
                  </span>
                  <span className="px-2 py-1 bg-blue-900/30 text-blue-400 text-xs rounded">
                    {rec.category}
                  </span>
                </div>
                
                <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium mb-2`}>
                  {rec.title}
                </h4>
                
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm mb-3`}>
                  {rec.description}
                </p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs block`}>
                      Investissement
                    </span>
                    <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {formatCurrency(rec.investment)}
                    </span>
                  </div>
                  <div>
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs block`}>
                      ROI Projeté
                    </span>
                    <span className="text-green-400 font-medium">
                      {rec.roi}%
                    </span>
                  </div>
                  <div>
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs block`}>
                      Délai
                    </span>
                    <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {rec.timeline}
                    </span>
                  </div>
                  <div>
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs block`}>
                      Confiance
                    </span>
                    <span className="text-blue-400 font-medium">
                      {rec.confidence}%
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="ml-4 text-right">
                <div className="text-2xl font-bold text-green-400">
                  +{formatCurrency(rec.investment * rec.roi / 100)}
                </div>
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  Bénéfice projeté
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  // Composant d'évaluation des risques
  const RiskAssessmentPanel = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Évaluation des Risques
        </h3>
        <div className="flex items-center space-x-2">
          <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
            Dernière évaluation
          </span>
          <Clock className="w-4 h-4 text-gray-400" />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {riskAssessment.map(risk => {
          const TrendIcon = risk.trend === 'increasing' ? TrendingUp : 
                           risk.trend === 'decreasing' ? TrendingDown : 
                           Target;
          const trendColor = risk.trend === 'increasing' ? '#EF4444' : 
                            risk.trend === 'decreasing' ? '#10B981' : 
                            '#6B7280';
          
          return (
            <div key={risk.id} className="p-4 bg-gray-700/30 rounded">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center space-x-2 mb-1">
                    <span className={`px-2 py-1 text-xs rounded ${
                      risk.level === 'high' ? 'bg-red-900/30 text-red-400' :
                      risk.level === 'medium' ? 'bg-yellow-900/30 text-yellow-400' :
                      'bg-green-900/30 text-green-400'
                    }`}>
                      {risk.level === 'high' ? 'Risque Élevé' :
                       risk.level === 'medium' ? 'Risque Moyen' :
                       'Risque Faible'}
                    </span>
                    <span className="px-2 py-1 bg-gray-600 text-gray-300 text-xs rounded">
                      {risk.category}
                    </span>
                  </div>
                  <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium text-sm`}>
                    {risk.description}
                  </h4>
                </div>
                
                <div className="flex items-center space-x-1">
                  <TrendIcon className="w-4 h-4" style={{ color: trendColor }} />
                  <span className="text-xs" style={{ color: trendColor }}>
                    {risk.trend === 'increasing' ? '↗' : risk.trend === 'decreasing' ? '↘' : '→'}
                  </span>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
                    Probabilité
                  </span>
                  <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                    {risk.probability}%
                  </span>
                </div>
                
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className="h-2 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${risk.probability}%`,
                      backgroundColor: getRiskColor(risk.level)
                    }}
                  />
                </div>
                
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-2`}>
                  <strong>Atténuation:</strong> {risk.mitigation}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Composant de conformité
  const ComplianceOverview = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Conformité Réglementaire
        </h3>
        <div className="flex items-center space-x-2">
          <div className="text-2xl font-bold text-green-400">
            {formatPercentage(complianceStatus.overall)}
          </div>
          <CheckCircle className="w-5 h-5 text-green-400" />
        </div>
      </div>
      
      <div className="space-y-3">
        {complianceStatus.standards?.map(standard => (
          <div key={standard.name} className="flex items-center justify-between p-3 bg-gray-700/30 rounded">
            <div>
              <div className={`${getThemeClasses('text', 'dashboard')} font-medium text-sm`}>
                {standard.name}
              </div>
              <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                Dernier audit: {new Date(standard.lastAudit).toLocaleDateString('fr-FR')}
              </div>
            </div>
            
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <div className="text-sm font-medium text-green-400">
                  {formatPercentage(standard.score)}
                </div>
                <div className="text-xs text-green-400">
                  Conforme
                </div>
              </div>
              <CheckCircle className="w-5 h-5 text-green-400" />
            </div>
          </div>
        ))}
      </div>
      
      {complianceStatus.gaps?.length > 0 && (
        <div className="mt-4 p-3 bg-yellow-900/20 border-l-4 border-yellow-400 rounded">
          <h4 className="text-yellow-400 font-medium text-sm mb-2">
            Points d'amélioration identifiés:
          </h4>
          <ul className="text-xs space-y-1">
            {complianceStatus.gaps.map((gap, index) => (
              <li key={index} className="text-yellow-300">
                • {gap.area} (priorité: {gap.priority})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Tableau de Bord Exécutif
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Vue stratégique et indicateurs de performance pour la direction
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Share className="w-4 h-4" />
            <span>Partager</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
            <Settings className="w-4 h-4" />
            <span>Personnaliser</span>
          </button>
        </div>
      </div>

      <ExecutiveKPIs />
      <ExecutiveControls />
      <TrendsCharts />
      <StrategicRecommendations />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskAssessmentPanel />
        <ComplianceOverview />
      </div>
    </div>
  );
};

export default ExecutiveDashboard;