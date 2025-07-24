// SLAManagement.jsx - Gestion des accords de niveau de service (SLA)
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Award, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock, 
  TrendingUp, 
  TrendingDown,
  Plus,
  Edit,
  Trash2,
  Eye,
  Settings,
  Filter,
  Search,
  RefreshCw,
  Calendar,
  BarChart3,
  PieChart,
  LineChart,
  Target,
  Shield,
  Activity,
  Bell,
  Users,
  Building,
  Globe,
  Server,
  Network,
  Monitor,
  Download,
  Upload,
  FileText,
  Mail,
  Phone,
  AlertCircle,
  CheckSquare,
  Square,
  Gauge,
  Zap,
  Database,
  Layers,
  Signal
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const SLAManagement = ({ isVisible = true }) => {
  const [slaAgreements, setSlaAgreements] = useState([]);
  const [selectedSLA, setSelectedSLA] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('view'); // 'view', 'edit', 'create'
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterClient, setFilterClient] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [timeRange, setTimeRange] = useState('7d');
  const [loading, setLoading] = useState(false);

  const { getThemeClasses } = useTheme();

  // Statuts SLA
  const slaStatuses = {
    'compliant': { label: 'Conforme', color: 'text-green-400', bgColor: 'bg-green-900/30', icon: CheckCircle },
    'warning': { label: 'Alerte', color: 'text-yellow-400', bgColor: 'bg-yellow-900/30', icon: AlertTriangle },
    'violation': { label: 'Violation', color: 'text-red-400', bgColor: 'bg-red-900/30', icon: XCircle },
    'unknown': { label: 'Inconnu', color: 'text-gray-400', bgColor: 'bg-gray-900/30', icon: AlertCircle }
  };

  // Types de services
  const serviceTypes = {
    'network': { label: 'Réseau', icon: Network, color: 'bg-blue-600' },
    'server': { label: 'Serveur', icon: Server, color: 'bg-green-600' },
    'application': { label: 'Application', icon: Monitor, color: 'bg-purple-600' },
    'database': { label: 'Base de données', icon: Database, color: 'bg-orange-600' }
  };

  // Données SLA mockées
  const mockSLAData = [
    {
      id: 'sla-001',
      name: 'SLA Réseau Principal',
      client: 'Département IT',
      serviceType: 'network',
      status: 'compliant',
      startDate: '2024-01-01',
      endDate: '2024-12-31',
      metrics: {
        availability: { target: 99.9, current: 99.95, unit: '%' },
        latency: { target: 20, current: 15.6, unit: 'ms' },
        throughput: { target: 1000, current: 1200, unit: 'Mbps' },
        packetLoss: { target: 0.1, current: 0.05, unit: '%' }
      },
      violations: 0,
      alerts: 2,
      lastCheck: '2024-01-15T10:30:00Z',
      description: 'Accord de niveau de service pour le réseau principal de l\'entreprise',
      contactPerson: 'admin@company.com',
      priority: 'high',
      escalationLevel: 1,
      penaltyClause: 'Réduction de 5% du coût mensuel en cas de non-respect',
      reportingFrequency: 'monthly'
    },
    {
      id: 'sla-002',
      name: 'SLA Serveurs Web',
      client: 'Service Commercial',
      serviceType: 'server',
      status: 'warning',
      startDate: '2024-01-01',
      endDate: '2024-12-31',
      metrics: {
        availability: { target: 99.5, current: 99.2, unit: '%' },
        responseTime: { target: 200, current: 180, unit: 'ms' },
        throughput: { target: 500, current: 620, unit: 'req/s' },
        errorRate: { target: 0.5, current: 0.3, unit: '%' }
      },
      violations: 1,
      alerts: 5,
      lastCheck: '2024-01-15T09:15:00Z',
      description: 'Accord pour les serveurs web de l\'application commerciale',
      contactPerson: 'commercial@company.com',
      priority: 'medium',
      escalationLevel: 2,
      penaltyClause: 'Crédit de service de 10% pour indisponibilité > 4h',
      reportingFrequency: 'weekly'
    },
    {
      id: 'sla-003',
      name: 'SLA Base de Données',
      client: 'Service Financier',
      serviceType: 'database',
      status: 'violation',
      startDate: '2024-01-01',
      endDate: '2024-12-31',
      metrics: {
        availability: { target: 99.95, current: 98.5, unit: '%' },
        queryTime: { target: 100, current: 250, unit: 'ms' },
        transactions: { target: 1000, current: 800, unit: 'tps' },
        backupSuccess: { target: 100, current: 95, unit: '%' }
      },
      violations: 3,
      alerts: 8,
      lastCheck: '2024-01-15T08:45:00Z',
      description: 'Accord pour la base de données financière critique',
      contactPerson: 'finance@company.com',
      priority: 'critical',
      escalationLevel: 3,
      penaltyClause: 'Pénalité de 20% + compensation pour pertes business',
      reportingFrequency: 'daily'
    },
    {
      id: 'sla-004',
      name: 'SLA Applications Mobile',
      client: 'Service Marketing',
      serviceType: 'application',
      status: 'compliant',
      startDate: '2024-01-01',
      endDate: '2024-12-31',
      metrics: {
        availability: { target: 99.0, current: 99.8, unit: '%' },
        loadTime: { target: 3, current: 2.1, unit: 's' },
        crashRate: { target: 0.1, current: 0.05, unit: '%' },
        userSatisfaction: { target: 4.0, current: 4.3, unit: '/5' }
      },
      violations: 0,
      alerts: 1,
      lastCheck: '2024-01-15T11:20:00Z',
      description: 'Accord pour les applications mobiles marketing',
      contactPerson: 'marketing@company.com',
      priority: 'low',
      escalationLevel: 1,
      penaltyClause: 'Remboursement partiel en cas de non-disponibilité',
      reportingFrequency: 'monthly'
    }
  ];

  // Données historiques pour les graphiques
  const generateHistoricalData = (sla) => {
    const days = timeRange === '7d' ? 7 : timeRange === '30d' ? 30 : 1;
    return Array.from({ length: days }, (_, i) => ({
      date: new Date(Date.now() - (days - 1 - i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
      availability: Math.max(95, Math.min(100, sla.metrics.availability.current + (Math.random() - 0.5) * 2)),
      performance: Math.max(80, Math.min(120, 100 + (Math.random() - 0.5) * 20)),
      violations: Math.floor(Math.random() * 3)
    }));
  };

  // Initialisation des données
  useEffect(() => {
    setSlaAgreements(mockSLAData);
  }, []);

  // Filtrage et tri des SLA
  const filteredSLAs = slaAgreements.filter(sla => {
    const matchesStatus = filterStatus === 'all' || sla.status === filterStatus;
    const matchesClient = filterClient === 'all' || sla.client === filterClient;
    const matchesSearch = searchQuery === '' || 
      sla.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sla.client.toLowerCase().includes(searchQuery.toLowerCase()) ||
      sla.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesStatus && matchesClient && matchesSearch;
  });

  const sortedSLAs = [...filteredSLAs].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.name.localeCompare(b.name);
      case 'status':
        return a.status.localeCompare(b.status);
      case 'violations':
        return b.violations - a.violations;
      case 'client':
        return a.client.localeCompare(b.client);
      default:
        return 0;
    }
  });

  // Statistiques globales
  const slaStats = {
    total: slaAgreements.length,
    compliant: slaAgreements.filter(sla => sla.status === 'compliant').length,
    warning: slaAgreements.filter(sla => sla.status === 'warning').length,
    violation: slaAgreements.filter(sla => sla.status === 'violation').length,
    totalViolations: slaAgreements.reduce((sum, sla) => sum + sla.violations, 0),
    totalAlerts: slaAgreements.reduce((sum, sla) => sum + sla.alerts, 0),
    avgAvailability: slaAgreements.reduce((sum, sla) => sum + sla.metrics.availability.current, 0) / slaAgreements.length
  };

  // Gestion des actions
  const handleCreateSLA = () => {
    setSelectedSLA(null);
    setModalMode('create');
    setIsModalOpen(true);
  };

  const handleEditSLA = (sla) => {
    setSelectedSLA(sla);
    setModalMode('edit');
    setIsModalOpen(true);
  };

  const handleViewSLA = (sla) => {
    setSelectedSLA(sla);
    setModalMode('view');
    setIsModalOpen(true);
  };

  const handleDeleteSLA = (slaId) => {
    setSlaAgreements(prev => prev.filter(sla => sla.id !== slaId));
  };

  // Composant des métriques principales
  const SLAMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total SLA</p>
            <p className="text-2xl font-bold text-blue-400">{slaStats.total}</p>
          </div>
          <Award className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Conformes</p>
            <p className="text-2xl font-bold text-green-400">{slaStats.compliant}</p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Violations</p>
            <p className="text-2xl font-bold text-red-400">{slaStats.totalViolations}</p>
          </div>
          <XCircle className="w-8 h-8 text-red-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Disponibilité Moy.</p>
            <p className="text-2xl font-bold text-purple-400">{slaStats.avgAvailability.toFixed(1)}%</p>
          </div>
          <Target className="w-8 h-8 text-purple-400" />
        </div>
      </div>
    </div>
  );

  // Composant de filtres et recherche
  const FiltersAndSearch = () => (
    <div className="flex flex-wrap items-center gap-4 mb-6">
      <div className="relative flex-1 min-w-64">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher par nom, client, description..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
        />
      </div>
      
      <select
        value={filterStatus}
        onChange={(e) => setFilterStatus(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les statuts</option>
        {Object.entries(slaStatuses).map(([key, status]) => (
          <option key={key} value={key}>{status.label}</option>
        ))}
      </select>
      
      <select
        value={filterClient}
        onChange={(e) => setFilterClient(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les clients</option>
        {Array.from(new Set(slaAgreements.map(sla => sla.client))).map(client => (
          <option key={client} value={client}>{client}</option>
        ))}
      </select>
      
      <select
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="name">Nom</option>
        <option value="status">Statut</option>
        <option value="violations">Violations</option>
        <option value="client">Client</option>
      </select>
    </div>
  );

  // Composant du tableau des SLA
  const SLATable = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden mb-6`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Nom</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Client</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Type</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Disponibilité</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Violations</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedSLAs.map(sla => {
              const statusConfig = slaStatuses[sla.status];
              const serviceConfig = serviceTypes[sla.serviceType];
              const StatusIcon = statusConfig.icon;
              const ServiceIcon = serviceConfig.icon;
              
              return (
                <tr key={sla.id} className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} font-medium`}>
                    <div className="flex items-center space-x-2">
                      <ServiceIcon className="w-4 h-4 text-blue-400" />
                      <span className="max-w-xs truncate">{sla.name}</span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                    {sla.client}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 text-xs rounded text-white ${serviceConfig.color}`}>
                      {serviceConfig.label}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <StatusIcon className={`w-4 h-4 ${statusConfig.color}`} />
                      <span className={`px-2 py-1 text-xs rounded ${statusConfig.bgColor} ${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} text-sm`}>
                    <div className="flex items-center space-x-2">
                      <span className="font-medium">{sla.metrics.availability.current}%</span>
                      <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                        / {sla.metrics.availability.target}%
                      </span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} text-sm`}>
                    <div className="flex items-center space-x-2">
                      <span className={`font-medium ${sla.violations > 0 ? 'text-red-400' : 'text-green-400'}`}>
                        {sla.violations}
                      </span>
                      {sla.alerts > 0 && (
                        <span className="px-1 py-0.5 bg-yellow-900/30 text-yellow-400 text-xs rounded">
                          {sla.alerts} alertes
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleViewSLA(sla)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Voir détails"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEditSLA(sla)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Modifier"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteSLA(sla.id)}
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

  // Composant des graphiques de performance
  const PerformanceCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
            Répartition des Statuts SLA
          </h3>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="7d">7 jours</option>
            <option value="30d">30 jours</option>
            <option value="1d">Aujourd'hui</option>
          </select>
        </div>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsPieChart>
              <Pie
                data={[
                  { name: 'Conformes', value: slaStats.compliant, color: '#10B981' },
                  { name: 'Alertes', value: slaStats.warning, color: '#F59E0B' },
                  { name: 'Violations', value: slaStats.violation, color: '#EF4444' }
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {[
                  { color: '#10B981' },
                  { color: '#F59E0B' },
                  { color: '#EF4444' }
                ].map((entry, index) => (
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
          Tendance des Violations
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={generateHistoricalData(mockSLAData[0])}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="date" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1F2937',
                  border: '1px solid #374151',
                  borderRadius: '4px',
                  color: '#fff'
                }}
              />
              <Bar dataKey="violations" fill="#EF4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  // Modal de détails/édition SLA
  const SLAModal = () => {
    if (!isModalOpen) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-lg shadow-2xl border border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
              {modalMode === 'create' ? 'Nouveau SLA' : 
               modalMode === 'edit' ? `Modifier SLA: ${selectedSLA?.name}` : 
               `Détails SLA: ${selectedSLA?.name}`}
            </h2>
            <button
              onClick={() => setIsModalOpen(false)}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </div>
          
          {selectedSLA && (
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                    Informations Générales
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Client:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedSLA.client}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Type:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{serviceTypes[selectedSLA.serviceType].label}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Priorité:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedSLA.priority}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Contact:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedSLA.contactPerson}</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                    Métriques de Performance
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(selectedSLA.metrics).map(([key, metric]) => (
                      <div key={key} className="flex items-center justify-between p-2 bg-gray-700/50 rounded">
                        <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm capitalize`}>
                          {key.replace(/([A-Z])/g, ' $1').trim()}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                            {metric.current}{metric.unit}
                          </span>
                          <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                            / {metric.target}{metric.unit}
                          </span>
                          {metric.current >= metric.target ? (
                            <CheckCircle className="w-4 h-4 text-green-400" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-400" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                  Description
                </h3>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm leading-relaxed`}>
                  {selectedSLA.description}
                </p>
              </div>
              
              <div>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                  Clause de Pénalité
                </h3>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm leading-relaxed`}>
                  {selectedSLA.penaltyClause}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Gestion des SLA
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Accords de niveau de service et conformité
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Download className="w-4 h-4" />
            <span>Rapport</span>
          </button>
          <button 
            onClick={handleCreateSLA}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Nouveau SLA</span>
          </button>
        </div>
      </div>

      <SLAMetrics />
      <FiltersAndSearch />
      <SLATable />
      <PerformanceCharts />
      <SLAModal />
    </div>
  );
};

export default SLAManagement;