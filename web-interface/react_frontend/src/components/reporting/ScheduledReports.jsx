// ScheduledReports.jsx - Planification automatique des rapports
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Calendar, 
  Clock, 
  Play, 
  Pause, 
  Square, 
  Plus, 
  Edit, 
  Trash2, 
  Copy, 
  Mail, 
  Users, 
  Settings, 
  RefreshCw, 
  Download, 
  Upload, 
  Eye, 
  EyeOff, 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  BarChart3, 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Zap, 
  Bell, 
  Share, 
  FileText, 
  Send, 
  History, 
  Activity, 
  Server, 
  Database, 
  Network, 
  Shield, 
  Monitor, 
  Award, 
  Filter, 
  Search, 
  MoreHorizontal, 
  ChevronDown, 
  ChevronUp, 
  Info, 
  X, 
  Check, 
  Save, 
  RotateCw
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const ScheduledReports = ({ isVisible = true }) => {
  const [schedules, setSchedules] = useState([]);
  const [selectedSchedule, setSelectedSchedule] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create', 'edit', 'view', 'history'
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterFrequency, setFilterFrequency] = useState('all');
  const [sortBy, setSortBy] = useState('nextRun');
  const [sortOrder, setSortOrder] = useState('asc');
  const [loading, setLoading] = useState(false);
  const [executionHistory, setExecutionHistory] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [recipients, setRecipients] = useState([]);

  const { getThemeClasses } = useTheme();

  // Planifications mockées
  const mockSchedules = [
    {
      id: 'sched-001',
      name: 'Rapport Mensuel Infrastructure',
      description: 'Rapport complet sur l\'état de l\'infrastructure',
      template: 'Infrastructure Complete',
      frequency: 'monthly',
      dayOfMonth: 1,
      time: '08:00',
      timezone: 'Europe/Paris',
      status: 'active',
      recipients: ['admin@company.com', 'manager@company.com', 'team@company.com'],
      format: 'pdf',
      lastRun: '2024-01-01T08:00:00Z',
      nextRun: '2024-02-01T08:00:00Z',
      successRate: 98.5,
      totalRuns: 24,
      failedRuns: 0,
      avgDuration: 142, // secondes
      created: '2023-01-15T10:30:00Z',
      createdBy: 'Jean Dupont',
      lastModified: '2024-01-10T14:20:00Z',
      autoRetry: true,
      maxRetries: 3,
      notifications: {
        onSuccess: true,
        onFailure: true,
        onRetry: false
      },
      dataFilters: {
        period: '30d',
        sources: ['network', 'system', 'security']
      }
    },
    {
      id: 'sched-002',
      name: 'Analyse Sécurité Hebdomadaire',
      description: 'Surveillance des incidents et menaces',
      template: 'Security Analysis',
      frequency: 'weekly',
      dayOfWeek: 'monday',
      time: '07:30',
      timezone: 'Europe/Paris',
      status: 'active',
      recipients: ['security@company.com', 'ciso@company.com'],
      format: 'pdf',
      lastRun: '2024-01-15T07:30:00Z',
      nextRun: '2024-01-22T07:30:00Z',
      successRate: 96.2,
      totalRuns: 52,
      failedRuns: 2,
      avgDuration: 89,
      created: '2023-02-01T09:15:00Z',
      createdBy: 'Sophie Martin',
      lastModified: '2024-01-08T11:45:00Z',
      autoRetry: true,
      maxRetries: 2,
      notifications: {
        onSuccess: false,
        onFailure: true,
        onRetry: true
      },
      dataFilters: {
        period: '7d',
        sources: ['security', 'network']
      }
    },
    {
      id: 'sched-003',
      name: 'Dashboard Exécutif Quotidien',
      description: 'Métriques clés pour la direction',
      template: 'Executive Dashboard',
      frequency: 'daily',
      time: '06:00',
      timezone: 'Europe/Paris',
      status: 'active',
      recipients: ['ceo@company.com', 'cto@company.com', 'board@company.com'],
      format: 'pdf',
      lastRun: '2024-01-16T06:00:00Z',
      nextRun: '2024-01-17T06:00:00Z',
      successRate: 99.1,
      totalRuns: 365,
      failedRuns: 3,
      avgDuration: 67,
      created: '2023-01-01T00:00:00Z',
      createdBy: 'Marc Dubois',
      lastModified: '2024-01-05T16:30:00Z',
      autoRetry: true,
      maxRetries: 5,
      notifications: {
        onSuccess: false,
        onFailure: true,
        onRetry: false
      },
      dataFilters: {
        period: '24h',
        sources: ['system', 'network', 'applications']
      }
    },
    {
      id: 'sched-004',
      name: 'Inventaire Équipements Trimestriel',
      description: 'État complet du parc informatique',
      template: 'Inventory Report',
      frequency: 'quarterly',
      dayOfMonth: 15,
      time: '14:00',
      timezone: 'Europe/Paris',
      status: 'paused',
      recipients: ['inventory@company.com', 'procurement@company.com'],
      format: 'xlsx',
      lastRun: '2023-10-15T14:00:00Z',
      nextRun: '2024-01-15T14:00:00Z',
      successRate: 95.8,
      totalRuns: 12,
      failedRuns: 0,
      avgDuration: 324,
      created: '2023-01-10T12:00:00Z',
      createdBy: 'Alice Bernard',
      lastModified: '2023-12-20T09:15:00Z',
      autoRetry: false,
      maxRetries: 1,
      notifications: {
        onSuccess: true,
        onFailure: true,
        onRetry: false
      },
      dataFilters: {
        period: '90d',
        sources: ['inventory', 'system']
      }
    },
    {
      id: 'sched-005',
      name: 'Performance Applications',
      description: 'Monitoring des applications critiques',
      template: 'Application Performance',
      frequency: 'daily',
      time: '23:30',
      timezone: 'Europe/Paris',
      status: 'error',
      recipients: ['devops@company.com', 'appteam@company.com'],
      format: 'html',
      lastRun: '2024-01-15T23:30:00Z',
      nextRun: '2024-01-16T23:30:00Z',
      successRate: 87.3,
      totalRuns: 180,
      failedRuns: 23,
      avgDuration: 156,
      created: '2023-07-01T08:00:00Z',
      createdBy: 'Thomas Leroy',
      lastModified: '2024-01-12T15:45:00Z',
      autoRetry: true,
      maxRetries: 3,
      notifications: {
        onSuccess: false,
        onFailure: true,
        onRetry: true
      },
      dataFilters: {
        period: '24h',
        sources: ['applications', 'system']
      },
      lastError: 'Connexion à la base de données échouée'
    }
  ];

  // Historique d'exécution mockée
  const mockExecutionHistory = [
    {
      id: 'exec-001',
      scheduleId: 'sched-001',
      scheduleName: 'Rapport Mensuel Infrastructure',
      startTime: '2024-01-01T08:00:00Z',
      endTime: '2024-01-01T08:02:15Z',
      status: 'success',
      duration: 135,
      fileSize: '2.4 MB',
      recipients: 3,
      delivered: 3,
      errors: []
    },
    {
      id: 'exec-002',
      scheduleId: 'sched-002',
      scheduleName: 'Analyse Sécurité Hebdomadaire',
      startTime: '2024-01-15T07:30:00Z',
      endTime: '2024-01-15T07:31:28Z',
      status: 'success',
      duration: 88,
      fileSize: '1.8 MB',
      recipients: 2,
      delivered: 2,
      errors: []
    },
    {
      id: 'exec-003',
      scheduleId: 'sched-005',
      scheduleName: 'Performance Applications',
      startTime: '2024-01-15T23:30:00Z',
      endTime: '2024-01-15T23:30:45Z',
      status: 'failed',
      duration: 45,
      fileSize: null,
      recipients: 2,
      delivered: 0,
      errors: ['Connexion à la base de données échouée', 'Timeout après 30 secondes']
    },
    {
      id: 'exec-004',
      scheduleId: 'sched-003',
      scheduleName: 'Dashboard Exécutif Quotidien',
      startTime: '2024-01-16T06:00:00Z',
      endTime: '2024-01-16T06:01:07Z',
      status: 'success',
      duration: 67,
      fileSize: '890 KB',
      recipients: 3,
      delivered: 3,
      errors: []
    }
  ];

  // Templates disponibles
  const mockTemplates = [
    { id: 'tmpl-001', name: 'Infrastructure Complete', category: 'Infrastructure' },
    { id: 'tmpl-002', name: 'Security Analysis', category: 'Security' },
    { id: 'tmpl-003', name: 'Executive Dashboard', category: 'Management' },
    { id: 'tmpl-004', name: 'Inventory Report', category: 'Inventory' },
    { id: 'tmpl-005', name: 'Application Performance', category: 'Performance' }
  ];

  // Destinataires fréquents
  const mockRecipients = [
    { email: 'admin@company.com', name: 'Admin System', role: 'Administrateur' },
    { email: 'manager@company.com', name: 'Manager IT', role: 'Manager' },
    { email: 'security@company.com', name: 'Équipe Sécurité', role: 'Sécurité' },
    { email: 'ceo@company.com', name: 'CEO', role: 'Direction' },
    { email: 'cto@company.com', name: 'CTO', role: 'Direction' }
  ];

  // Initialisation
  useEffect(() => {
    setSchedules(mockSchedules);
    setExecutionHistory(mockExecutionHistory);
    setTemplates(mockTemplates);
    setRecipients(mockRecipients);
  }, []);

  // Fonctions utilitaires
  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return '#10B981';
      case 'paused': return '#F59E0B';
      case 'error': return '#EF4444';
      case 'disabled': return '#6B7280';
      default: return '#6B7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return CheckCircle;
      case 'paused': return Pause;
      case 'error': return XCircle;
      case 'disabled': return Square;
      default: return AlertTriangle;
    }
  };

  const getFrequencyLabel = (frequency, schedule) => {
    switch (frequency) {
      case 'daily': return 'Quotidien';
      case 'weekly': return `Hebdomadaire (${schedule.dayOfWeek})`;
      case 'monthly': return `Mensuel (${schedule.dayOfMonth})`;
      case 'quarterly': return `Trimestriel (${schedule.dayOfMonth})`;
      default: return 'Personnalisé';
    }
  };

  const formatDuration = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return minutes > 0 ? `${minutes}m ${remainingSeconds}s` : `${remainingSeconds}s`;
  };

  const getTimeAgo = (timestamp) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor(diff / (1000 * 60));
    
    if (days > 0) return `${days}j`;
    if (hours > 0) return `${hours}h`;
    return `${minutes}m`;
  };

  const getNextRunColor = (nextRun) => {
    const diff = new Date(nextRun).getTime() - Date.now();
    const hours = diff / (1000 * 60 * 60);
    
    if (hours < 1) return '#EF4444'; // Rouge si dans moins d'1h
    if (hours < 24) return '#F59E0B'; // Orange si dans moins de 24h
    return '#10B981'; // Vert sinon
  };

  // Filtrage et tri
  const filteredSchedules = schedules.filter(schedule => {
    const matchesSearch = searchQuery === '' || 
      schedule.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      schedule.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      schedule.template.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || schedule.status === filterStatus;
    const matchesFrequency = filterFrequency === 'all' || schedule.frequency === filterFrequency;
    
    return matchesSearch && matchesStatus && matchesFrequency;
  });

  const sortedSchedules = [...filteredSchedules].sort((a, b) => {
    let aValue, bValue;
    
    switch (sortBy) {
      case 'name':
        aValue = a.name;
        bValue = b.name;
        break;
      case 'nextRun':
        aValue = new Date(a.nextRun);
        bValue = new Date(b.nextRun);
        break;
      case 'lastRun':
        aValue = new Date(a.lastRun);
        bValue = new Date(b.lastRun);
        break;
      case 'successRate':
        aValue = a.successRate;
        bValue = b.successRate;
        break;
      default:
        return 0;
    }
    
    if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  // Actions sur les planifications
  const toggleScheduleStatus = (scheduleId) => {
    setSchedules(prev => prev.map(schedule => 
      schedule.id === scheduleId 
        ? { 
            ...schedule, 
            status: schedule.status === 'active' ? 'paused' : 'active'
          }
        : schedule
    ));
  };

  const runScheduleNow = (scheduleId) => {
    const schedule = schedules.find(s => s.id === scheduleId);
    if (!schedule) return;

    setLoading(true);
    
    // Simulation d'exécution
    setTimeout(() => {
      const newExecution = {
        id: `exec-${Date.now()}`,
        scheduleId: schedule.id,
        scheduleName: schedule.name,
        startTime: new Date().toISOString(),
        endTime: new Date(Date.now() + Math.random() * 180000).toISOString(),
        status: Math.random() > 0.1 ? 'success' : 'failed',
        duration: Math.floor(Math.random() * 300) + 30,
        fileSize: Math.random() > 0.1 ? `${(Math.random() * 5 + 0.5).toFixed(1)} MB` : null,
        recipients: schedule.recipients.length,
        delivered: Math.random() > 0.1 ? schedule.recipients.length : 0,
        errors: Math.random() > 0.1 ? [] : ['Erreur simulée lors de l\'exécution']
      };
      
      setExecutionHistory(prev => [newExecution, ...prev]);
      setLoading(false);
    }, 2000);
  };

  const duplicateSchedule = (schedule) => {
    const newSchedule = {
      ...schedule,
      id: `sched-${Date.now()}`,
      name: `${schedule.name} (Copie)`,
      status: 'paused',
      created: new Date().toISOString(),
      createdBy: 'Vous',
      totalRuns: 0,
      failedRuns: 0,
      successRate: 0
    };
    
    setSchedules(prev => [newSchedule, ...prev]);
  };

  const deleteSchedule = (scheduleId) => {
    setSchedules(prev => prev.filter(s => s.id !== scheduleId));
    setExecutionHistory(prev => prev.filter(e => e.scheduleId !== scheduleId));
  };

  // Statistiques
  const scheduleStats = {
    total: schedules.length,
    active: schedules.filter(s => s.status === 'active').length,
    paused: schedules.filter(s => s.status === 'paused').length,
    error: schedules.filter(s => s.status === 'error').length,
    avgSuccessRate: schedules.reduce((sum, s) => sum + s.successRate, 0) / schedules.length,
    totalRuns: schedules.reduce((sum, s) => sum + s.totalRuns, 0),
    failedRuns: schedules.reduce((sum, s) => sum + s.failedRuns, 0)
  };

  // Données pour graphiques
  const frequencyDistribution = [
    { name: 'Quotidien', value: schedules.filter(s => s.frequency === 'daily').length, color: '#3B82F6' },
    { name: 'Hebdomadaire', value: schedules.filter(s => s.frequency === 'weekly').length, color: '#10B981' },
    { name: 'Mensuel', value: schedules.filter(s => s.frequency === 'monthly').length, color: '#F59E0B' },
    { name: 'Trimestriel', value: schedules.filter(s => s.frequency === 'quarterly').length, color: '#8B5CF6' }
  ];

  const executionTrend = executionHistory.slice(0, 10).reverse().map((exec, index) => ({
    time: new Date(exec.startTime).toLocaleDateString(),
    success: exec.status === 'success' ? 1 : 0,
    failed: exec.status === 'failed' ? 1 : 0,
    duration: exec.duration
  }));

  // Composant des métriques principales
  const ScheduleMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total Planifications</p>
            <p className="text-2xl font-bold text-blue-400">{scheduleStats.total}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              {scheduleStats.active} actives
            </p>
          </div>
          <Calendar className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Taux de Succès</p>
            <p className="text-2xl font-bold text-green-400">{scheduleStats.avgSuccessRate.toFixed(1)}%</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              {scheduleStats.totalRuns} exécutions
            </p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Échecs</p>
            <p className="text-2xl font-bold text-red-400">{scheduleStats.failedRuns}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              {scheduleStats.error} en erreur
            </p>
          </div>
          <XCircle className="w-8 h-8 text-red-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Prochaine Exéc.</p>
            <p className="text-2xl font-bold text-purple-400">
              {(() => {
                const nextRuns = schedules.filter(s => s.status === 'active').map(s => new Date(s.nextRun));
                const nextRun = nextRuns.length > 0 ? Math.min(...nextRuns) : null;
                return nextRun ? getTimeAgo(new Date(nextRun).toISOString()) : 'N/A';
              })()}
            </p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              Prochaine planification
            </p>
          </div>
          <Clock className="w-8 h-8 text-purple-400" />
        </div>
      </div>
    </div>
  );

  // Composant des contrôles et filtres
  const ScheduleControls = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Rechercher une planification..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            />
          </div>
          
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
          >
            <option value="all">Tous les statuts</option>
            <option value="active">Actif</option>
            <option value="paused">En pause</option>
            <option value="error">En erreur</option>
            <option value="disabled">Désactivé</option>
          </select>
          
          <select
            value={filterFrequency}
            onChange={(e) => setFilterFrequency(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
          >
            <option value="all">Toutes les fréquences</option>
            <option value="daily">Quotidien</option>
            <option value="weekly">Hebdomadaire</option>
            <option value="monthly">Mensuel</option>
            <option value="quarterly">Trimestriel</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setLoading(true)}
            className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            <span>Actualiser</span>
          </button>
          
          <button
            onClick={() => {
              setSelectedSchedule(null);
              setModalMode('create');
              setShowModal(true);
            }}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Nouvelle Planification</span>
          </button>
        </div>
      </div>
    </div>
  );

  // Composant tableau des planifications
  const SchedulesTable = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden mb-6`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">
                <button
                  onClick={() => {
                    setSortBy('name');
                    setSortOrder(sortBy === 'name' && sortOrder === 'asc' ? 'desc' : 'asc');
                  }}
                  className="flex items-center space-x-1 hover:text-white"
                >
                  <span>Nom</span>
                  {sortBy === 'name' && (
                    sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                  )}
                </button>
              </th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Fréquence</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">
                <button
                  onClick={() => {
                    setSortBy('nextRun');
                    setSortOrder(sortBy === 'nextRun' && sortOrder === 'asc' ? 'desc' : 'asc');
                  }}
                  className="flex items-center space-x-1 hover:text-white"
                >
                  <span>Prochaine Exéc.</span>
                  {sortBy === 'nextRun' && (
                    sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                  )}
                </button>
              </th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">
                <button
                  onClick={() => {
                    setSortBy('successRate');
                    setSortOrder(sortBy === 'successRate' && sortOrder === 'asc' ? 'desc' : 'asc');
                  }}
                  className="flex items-center space-x-1 hover:text-white"
                >
                  <span>Performance</span>
                  {sortBy === 'successRate' && (
                    sortOrder === 'asc' ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />
                  )}
                </button>
              </th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Destinataires</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedSchedules.map(schedule => {
              const StatusIcon = getStatusIcon(schedule.status);
              
              return (
                <tr key={schedule.id} className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
                  <td className="py-3 px-4">
                    <div>
                      <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                        {schedule.name}
                      </div>
                      <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                        {schedule.template}
                      </div>
                      {schedule.lastError && (
                        <div className="text-red-400 text-xs mt-1 flex items-center space-x-1">
                          <AlertTriangle className="w-3 h-3" />
                          <span>{schedule.lastError}</span>
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <div className={`px-2 py-1 rounded text-xs ${
                        schedule.frequency === 'daily' ? 'bg-blue-900/30 text-blue-400' :
                        schedule.frequency === 'weekly' ? 'bg-green-900/30 text-green-400' :
                        schedule.frequency === 'monthly' ? 'bg-purple-900/30 text-purple-400' :
                        'bg-orange-900/30 text-orange-400'
                      }`}>
                        {getFrequencyLabel(schedule.frequency, schedule)}
                      </div>
                    </div>
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mt-1`}>
                      à {schedule.time}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <StatusIcon 
                        className="w-4 h-4" 
                        style={{ color: getStatusColor(schedule.status) }}
                      />
                      <span 
                        className="text-sm capitalize"
                        style={{ color: getStatusColor(schedule.status) }}
                      >
                        {schedule.status === 'active' ? 'Actif' :
                         schedule.status === 'paused' ? 'En pause' :
                         schedule.status === 'error' ? 'Erreur' : 'Désactivé'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div 
                      className="text-sm font-medium"
                      style={{ color: getNextRunColor(schedule.nextRun) }}
                    >
                      {new Date(schedule.nextRun).toLocaleDateString('fr-FR')}
                    </div>
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                      {new Date(schedule.nextRun).toLocaleTimeString('fr-FR', { 
                        hour: '2-digit', 
                        minute: '2-digit' 
                      })}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-700 rounded-full h-2">
                          <div 
                            className="h-2 rounded-full transition-all duration-300"
                            style={{ 
                              width: `${schedule.successRate}%`,
                              backgroundColor: schedule.successRate >= 95 ? '#10B981' : 
                                             schedule.successRate >= 80 ? '#F59E0B' : '#EF4444'
                            }}
                          />
                        </div>
                        <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                          {schedule.successRate.toFixed(1)}%
                        </span>
                      </div>
                      <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                        {schedule.totalRuns} runs • ~{formatDuration(schedule.avgDuration)}
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-1">
                      <Users className="w-4 h-4 text-gray-400" />
                      <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                        {schedule.recipients.length}
                      </span>
                    </div>
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                      {schedule.format.toUpperCase()}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-1">
                      <button
                        onClick={() => runScheduleNow(schedule.id)}
                        disabled={loading}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors disabled:opacity-50"
                        title="Exécuter maintenant"
                      >
                        <Play className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => toggleScheduleStatus(schedule.id)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title={schedule.status === 'active' ? 'Mettre en pause' : 'Activer'}
                      >
                        {schedule.status === 'active' ? 
                          <Pause className="w-4 h-4" /> : 
                          <Play className="w-4 h-4" />
                        }
                      </button>
                      
                      <button
                        onClick={() => {
                          setSelectedSchedule(schedule);
                          setModalMode('history');
                          setShowModal(true);
                        }}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Historique"
                      >
                        <History className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => {
                          setSelectedSchedule(schedule);
                          setModalMode('edit');
                          setShowModal(true);
                        }}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Modifier"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => duplicateSchedule(schedule)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Dupliquer"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      
                      <button
                        onClick={() => deleteSchedule(schedule.id)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors text-red-400"
                        title="Supprimer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );

  // Composant des graphiques
  const ScheduleCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Répartition par Fréquence
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={frequencyDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {frequencyDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Tendance des Exécutions
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={executionTrend}>
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
                dataKey="success" 
                stackId="1" 
                stroke="#10B981" 
                fill="#10B981" 
                fillOpacity={0.6}
              />
              <Area 
                type="monotone" 
                dataKey="failed" 
                stackId="1" 
                stroke="#EF4444" 
                fill="#EF4444" 
                fillOpacity={0.8}
              />
            </AreaChart>
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
            Planifications Automatiques
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Gestion et surveillance des rapports programmés
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Download className="w-4 h-4" />
            <span>Export Config</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
            <Settings className="w-4 h-4" />
            <span>Configuration</span>
          </button>
        </div>
      </div>

      <ScheduleMetrics />
      <ScheduleControls />
      <ScheduleCharts />
      <SchedulesTable />
    </div>
  );
};

export default ScheduledReports;