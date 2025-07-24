// QoSPolicies.jsx - Gestion moderne des politiques QoS
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Shield, 
  Settings, 
  Plus, 
  Edit, 
  Trash2, 
  Copy, 
  Play, 
  Pause, 
  Eye, 
  Save, 
  X,
  Search,
  Filter,
  RefreshCw,
  Download,
  Upload,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  TrendingUp,
  TrendingDown,
  Activity,
  Gauge,
  Target,
  Zap,
  Network,
  Wifi,
  Server,
  Database,
  Globe,
  Router,
  Monitor,
  Layers,
  Signal,
  Users,
  Building,
  Calendar,
  FileText,
  Code,
  Terminal,
  Sliders,
  BarChart3,
  PieChart,
  LineChart
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Pie, Cell } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const QoSPolicies = ({ isVisible = true }) => {
  const [policies, setPolicies] = useState([]);
  const [selectedPolicy, setSelectedPolicy] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('view'); // 'view', 'edit', 'create'
  const [filterInterface, setFilterInterface] = useState('all');
  const [filterTrafficType, setFilterTrafficType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [isDeploying, setIsDeploying] = useState(false);
  const [deploymentProgress, setDeploymentProgress] = useState(0);
  const [activeTab, setActiveTab] = useState('list');

  const { getThemeClasses } = useTheme();

  // Interfaces réseau
  const networkInterfaces = [
    { id: 'eth0', name: 'Ethernet 0', type: 'ethernet', speed: 1000, status: 'active' },
    { id: 'eth1', name: 'Ethernet 1', type: 'ethernet', speed: 1000, status: 'active' },
    { id: 'eth2', name: 'Ethernet 2', type: 'ethernet', speed: 1000, status: 'inactive' },
    { id: 'wlan0', name: 'WiFi 0', type: 'wireless', speed: 300, status: 'active' }
  ];

  // Types de trafic
  const trafficTypes = {
    'voice': { label: 'Voix', icon: Users, color: 'bg-blue-600', priority: 'high' },
    'video': { label: 'Vidéo', icon: Monitor, color: 'bg-green-600', priority: 'high' },
    'data': { label: 'Données', icon: Database, color: 'bg-yellow-600', priority: 'medium' },
    'bulk': { label: 'Bulk', icon: Download, color: 'bg-gray-600', priority: 'low' }
  };

  // Actions QoS
  const qosActions = {
    'priority': { label: 'Prioriser', icon: TrendingUp, color: 'text-green-400' },
    'limit': { label: 'Limiter', icon: Gauge, color: 'text-orange-400' },
    'block': { label: 'Bloquer', icon: XCircle, color: 'text-red-400' },
    'mark': { label: 'Marquer', icon: Target, color: 'text-blue-400' }
  };

  // Données mockées des politiques QoS
  const mockPolicies = [
    {
      id: 'policy-001',
      name: 'VoIP Haute Priorité',
      description: 'Priorité maximale pour le trafic VoIP',
      interface: 'eth0',
      trafficType: 'voice',
      status: 'active',
      action: 'priority',
      bandwidth: 200,
      burstSize: 64,
      priority: 1,
      classifier: {
        sourceIP: '192.168.1.0/24',
        destIP: 'any',
        sourcePort: 'any',
        destPort: '5060',
        protocol: 'UDP',
        dscp: 'EF'
      },
      statistics: {
        packetsMatched: 156789,
        bytesMatched: 78945123,
        packetsDropped: 0,
        lastMatch: '2024-01-15T10:30:00Z'
      },
      createdAt: '2024-01-10T09:00:00Z',
      updatedAt: '2024-01-15T10:30:00Z',
      author: 'admin@company.com'
    },
    {
      id: 'policy-002',
      name: 'Limitation P2P',
      description: 'Limitation du trafic peer-to-peer',
      interface: 'eth1',
      trafficType: 'bulk',
      status: 'active',
      action: 'limit',
      bandwidth: 100,
      burstSize: 32,
      priority: 5,
      classifier: {
        sourceIP: 'any',
        destIP: 'any',
        sourcePort: 'any',
        destPort: '6881-6999',
        protocol: 'TCP',
        dscp: 'BE'
      },
      statistics: {
        packetsMatched: 89456,
        bytesMatched: 445678901,
        packetsDropped: 1234,
        lastMatch: '2024-01-15T10:25:00Z'
      },
      createdAt: '2024-01-08T14:00:00Z',
      updatedAt: '2024-01-14T16:20:00Z',
      author: 'network@company.com'
    },
    {
      id: 'policy-003',
      name: 'Streaming Vidéo',
      description: 'Garantie de bande passante pour streaming',
      interface: 'wlan0',
      trafficType: 'video',
      status: 'active',
      action: 'priority',
      bandwidth: 500,
      burstSize: 128,
      priority: 2,
      classifier: {
        sourceIP: 'any',
        destIP: 'any',
        sourcePort: 'any',
        destPort: '80,443',
        protocol: 'TCP',
        dscp: 'AF41'
      },
      statistics: {
        packetsMatched: 234567,
        bytesMatched: 1234567890,
        packetsDropped: 567,
        lastMatch: '2024-01-15T10:20:00Z'
      },
      createdAt: '2024-01-05T11:30:00Z',
      updatedAt: '2024-01-12T09:45:00Z',
      author: 'admin@company.com'
    },
    {
      id: 'policy-004',
      name: 'Trafic Malveillant',
      description: 'Blocage du trafic suspect',
      interface: 'eth0',
      trafficType: 'data',
      status: 'active',
      action: 'block',
      bandwidth: 0,
      burstSize: 0,
      priority: 0,
      classifier: {
        sourceIP: '203.0.113.0/24',
        destIP: 'any',
        sourcePort: 'any',
        destPort: 'any',
        protocol: 'any',
        dscp: 'BE'
      },
      statistics: {
        packetsMatched: 12345,
        bytesMatched: 6789012,
        packetsDropped: 12345,
        lastMatch: '2024-01-15T10:15:00Z'
      },
      createdAt: '2024-01-03T16:00:00Z',
      updatedAt: '2024-01-10T11:15:00Z',
      author: 'security@company.com'
    },
    {
      id: 'policy-005',
      name: 'Bureautique Standard',
      description: 'Trafic bureautique standard',
      interface: 'eth1',
      trafficType: 'data',
      status: 'inactive',
      action: 'mark',
      bandwidth: 300,
      burstSize: 64,
      priority: 3,
      classifier: {
        sourceIP: '192.168.10.0/24',
        destIP: 'any',
        sourcePort: 'any',
        destPort: '80,443,993,995',
        protocol: 'TCP',
        dscp: 'AF21'
      },
      statistics: {
        packetsMatched: 0,
        bytesMatched: 0,
        packetsDropped: 0,
        lastMatch: null
      },
      createdAt: '2024-01-01T10:00:00Z',
      updatedAt: '2024-01-05T14:30:00Z',
      author: 'admin@company.com'
    }
  ];

  // Initialisation des données
  useEffect(() => {
    setPolicies(mockPolicies);
  }, []);

  // Filtrage et tri des politiques
  const filteredPolicies = policies.filter(policy => {
    const matchesInterface = filterInterface === 'all' || policy.interface === filterInterface;
    const matchesTrafficType = filterTrafficType === 'all' || policy.trafficType === filterTrafficType;
    const matchesStatus = filterStatus === 'all' || policy.status === filterStatus;
    const matchesSearch = searchQuery === '' || 
      policy.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      policy.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesInterface && matchesTrafficType && matchesStatus && matchesSearch;
  });

  const sortedPolicies = [...filteredPolicies].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.name.localeCompare(b.name);
      case 'priority':
        return a.priority - b.priority;
      case 'bandwidth':
        return b.bandwidth - a.bandwidth;
      case 'updated':
        return new Date(b.updatedAt) - new Date(a.updatedAt);
      default:
        return 0;
    }
  });

  // Statistiques des politiques
  const policyStats = {
    total: policies.length,
    active: policies.filter(p => p.status === 'active').length,
    inactive: policies.filter(p => p.status === 'inactive').length,
    totalBandwidth: policies.reduce((sum, p) => sum + p.bandwidth, 0),
    totalPackets: policies.reduce((sum, p) => sum + p.statistics.packetsMatched, 0),
    totalDropped: policies.reduce((sum, p) => sum + p.statistics.packetsDropped, 0)
  };

  // Données pour graphiques
  const bandwidthDistribution = Object.entries(trafficTypes).map(([key, type]) => ({
    name: type.label,
    value: policies.filter(p => p.trafficType === key).reduce((sum, p) => sum + p.bandwidth, 0),
    color: type.color.replace('bg-', '#')
  }));

  const interfaceUtilization = networkInterfaces.map(iface => ({
    name: iface.name,
    allocated: policies.filter(p => p.interface === iface.id).reduce((sum, p) => sum + p.bandwidth, 0),
    capacity: iface.speed,
    utilization: (policies.filter(p => p.interface === iface.id).reduce((sum, p) => sum + p.bandwidth, 0) / iface.speed) * 100
  }));

  // Gestion des actions
  const handleCreatePolicy = () => {
    setSelectedPolicy(null);
    setModalMode('create');
    setIsModalOpen(true);
  };

  const handleEditPolicy = (policy) => {
    setSelectedPolicy(policy);
    setModalMode('edit');
    setIsModalOpen(true);
  };

  const handleViewPolicy = (policy) => {
    setSelectedPolicy(policy);
    setModalMode('view');
    setIsModalOpen(true);
  };

  const handleTogglePolicy = (policyId) => {
    setPolicies(prev => prev.map(policy => 
      policy.id === policyId 
        ? { ...policy, status: policy.status === 'active' ? 'inactive' : 'active' }
        : policy
    ));
  };

  const handleDeletePolicy = (policyId) => {
    setPolicies(prev => prev.filter(policy => policy.id !== policyId));
  };

  const handleDuplicatePolicy = (policy) => {
    const newPolicy = {
      ...policy,
      id: `policy-${Date.now()}`,
      name: `${policy.name} (Copie)`,
      status: 'inactive',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      statistics: {
        packetsMatched: 0,
        bytesMatched: 0,
        packetsDropped: 0,
        lastMatch: null
      }
    };
    setPolicies(prev => [...prev, newPolicy]);
  };

  // Simulation du déploiement
  const handleDeployPolicies = useCallback(() => {
    setIsDeploying(true);
    setDeploymentProgress(0);
    
    const interval = setInterval(() => {
      setDeploymentProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsDeploying(false);
          return 100;
        }
        return prev + Math.random() * 15;
      });
    }, 200);
  }, []);

  // Composant des métriques
  const PolicyMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total Politiques</p>
            <p className="text-2xl font-bold text-blue-400">{policyStats.total}</p>
          </div>
          <Shield className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Actives</p>
            <p className="text-2xl font-bold text-green-400">{policyStats.active}</p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Bande P. Allouée</p>
            <p className="text-2xl font-bold text-purple-400">{policyStats.totalBandwidth}</p>
          </div>
          <Gauge className="w-8 h-8 text-purple-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Paquets Traités</p>
            <p className="text-2xl font-bold text-orange-400">{policyStats.totalPackets.toLocaleString()}</p>
          </div>
          <Activity className="w-8 h-8 text-orange-400" />
        </div>
      </div>
    </div>
  );

  // Composant de navigation par onglets
  const TabNavigation = () => (
    <div className="flex space-x-1 mb-6">
      <button
        onClick={() => setActiveTab('list')}
        className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
          activeTab === 'list' 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
        }`}
      >
        Liste des politiques
      </button>
      <button
        onClick={() => setActiveTab('analytics')}
        className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
          activeTab === 'analytics' 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
        }`}
      >
        Analyse
      </button>
      <button
        onClick={() => setActiveTab('deployment')}
        className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
          activeTab === 'deployment' 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
        }`}
      >
        Déploiement
      </button>
    </div>
  );

  // Composant de contrôle de déploiement
  const DeploymentControls = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
            Déploiement des Politiques
          </h3>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
            Appliquer les politiques QoS aux interfaces réseau
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleDeployPolicies}
            disabled={isDeploying}
            className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
              isDeploying 
                ? 'bg-gray-600 cursor-not-allowed' 
                : 'bg-blue-600 hover:bg-blue-700'
            } text-white`}
          >
            <Zap className="w-4 h-4" />
            <span>{isDeploying ? 'Déploiement...' : 'Déployer'}</span>
          </button>
        </div>
      </div>
      
      {isDeploying && (
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
              Progression du déploiement
            </span>
            <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              {Math.round(deploymentProgress)}%
            </span>
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${deploymentProgress}%` }}
            ></div>
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium mb-2`}>
            Politiques à déployer
          </h4>
          <div className="space-y-2">
            {policies.filter(p => p.status === 'active').map(policy => (
              <div key={policy.id} className="flex items-center justify-between p-2 bg-gray-700/50 rounded">
                <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                  {policy.name}
                </span>
                <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  {policy.interface}
                </span>
              </div>
            ))}
          </div>
        </div>
        
        <div>
          <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium mb-2`}>
            Interfaces cibles
          </h4>
          <div className="space-y-2">
            {networkInterfaces.filter(i => i.status === 'active').map(iface => (
              <div key={iface.id} className="flex items-center justify-between p-2 bg-gray-700/50 rounded">
                <div className="flex items-center space-x-2">
                  {iface.type === 'ethernet' ? (
                    <Network className="w-4 h-4 text-blue-400" />
                  ) : (
                    <Wifi className="w-4 h-4 text-green-400" />
                  )}
                  <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                    {iface.name}
                  </span>
                </div>
                <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  {iface.speed} Mbps
                </span>
              </div>
            ))}
          </div>
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
          placeholder="Rechercher par nom, description..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
        />
      </div>
      
      <select
        value={filterInterface}
        onChange={(e) => setFilterInterface(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Toutes les interfaces</option>
        {networkInterfaces.map(iface => (
          <option key={iface.id} value={iface.id}>{iface.name}</option>
        ))}
      </select>
      
      <select
        value={filterTrafficType}
        onChange={(e) => setFilterTrafficType(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les types</option>
        {Object.entries(trafficTypes).map(([key, type]) => (
          <option key={key} value={key}>{type.label}</option>
        ))}
      </select>
      
      <select
        value={filterStatus}
        onChange={(e) => setFilterStatus(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les statuts</option>
        <option value="active">Actif</option>
        <option value="inactive">Inactif</option>
      </select>
      
      <select
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="name">Nom</option>
        <option value="priority">Priorité</option>
        <option value="bandwidth">Bande passante</option>
        <option value="updated">Dernière modification</option>
      </select>
    </div>
  );

  // Composant du tableau des politiques
  const PoliciesTable = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Nom</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Interface</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Type</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Action</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Bande P.</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Priorité</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedPolicies.map(policy => {
              const trafficConfig = trafficTypes[policy.trafficType];
              const actionConfig = qosActions[policy.action];
              const TrafficIcon = trafficConfig.icon;
              const ActionIcon = actionConfig.icon;
              
              return (
                <tr key={policy.id} className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} font-medium`}>
                    <div className="flex items-center space-x-2">
                      <TrafficIcon className="w-4 h-4 text-blue-400" />
                      <span className="max-w-xs truncate">{policy.name}</span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                    {networkInterfaces.find(i => i.id === policy.interface)?.name || policy.interface}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 text-xs rounded text-white ${trafficConfig.color}`}>
                      {trafficConfig.label}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <ActionIcon className={`w-4 h-4 ${actionConfig.color}`} />
                      <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                        {actionConfig.label}
                      </span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {policy.bandwidth} Mbps
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} text-sm`}>
                    {policy.priority}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${
                        policy.status === 'active' ? 'bg-green-400' : 'bg-gray-400'
                      }`}></div>
                      <span className={`text-xs ${
                        policy.status === 'active' ? 'text-green-400' : 'text-gray-400'
                      }`}>
                        {policy.status === 'active' ? 'Actif' : 'Inactif'}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleViewPolicy(policy)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Voir détails"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEditPolicy(policy)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Modifier"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDuplicatePolicy(policy)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Dupliquer"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleTogglePolicy(policy.id)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title={policy.status === 'active' ? 'Désactiver' : 'Activer'}
                      >
                        {policy.status === 'active' ? 
                          <Pause className="w-4 h-4" /> : 
                          <Play className="w-4 h-4" />
                        }
                      </button>
                      <button
                        onClick={() => handleDeletePolicy(policy.id)}
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

  // Composant des graphiques d'analyse
  const AnalyticsCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Répartition Bande Passante
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsPieChart>
              <Pie
                data={bandwidthDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {bandwidthDistribution.map((entry, index) => (
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
          Utilisation par Interface
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={interfaceUtilization}>
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
              <Bar dataKey="allocated" fill="#3B82F6" />
              <Bar dataKey="capacity" fill="#6B7280" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  // Modal de détails/édition
  const PolicyModal = () => {
    if (!isModalOpen) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-lg shadow-2xl border border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
              {modalMode === 'create' ? 'Nouvelle Politique' : 
               modalMode === 'edit' ? `Modifier: ${selectedPolicy?.name}` : 
               `Détails: ${selectedPolicy?.name}`}
            </h2>
            <button
              onClick={() => setIsModalOpen(false)}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {selectedPolicy && (
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                    Configuration
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                        Nom
                      </label>
                      <input
                        type="text"
                        value={selectedPolicy.name}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                        readOnly={modalMode === 'view'}
                      />
                    </div>
                    <div>
                      <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                        Interface
                      </label>
                      <select
                        value={selectedPolicy.interface}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                        disabled={modalMode === 'view'}
                      >
                        {networkInterfaces.map(iface => (
                          <option key={iface.id} value={iface.id}>{iface.name}</option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                        Bande passante (Mbps)
                      </label>
                      <input
                        type="number"
                        value={selectedPolicy.bandwidth}
                        className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                        readOnly={modalMode === 'view'}
                      />
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                    Classificateur
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>IP Source:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedPolicy.classifier.sourceIP}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>IP Destination:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedPolicy.classifier.destIP}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Port Source:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedPolicy.classifier.sourcePort}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Port Destination:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedPolicy.classifier.destPort}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Protocole:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedPolicy.classifier.protocol}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                  Statistiques
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="p-3 bg-gray-700/50 rounded">
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mb-1`}>
                      Paquets traités
                    </div>
                    <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {selectedPolicy.statistics.packetsMatched.toLocaleString()}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-700/50 rounded">
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mb-1`}>
                      Octets traités
                    </div>
                    <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {selectedPolicy.statistics.bytesMatched.toLocaleString()}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-700/50 rounded">
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mb-1`}>
                      Paquets perdus
                    </div>
                    <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {selectedPolicy.statistics.packetsDropped.toLocaleString()}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-700/50 rounded">
                    <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs mb-1`}>
                      Dernière activation
                    </div>
                    <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {selectedPolicy.statistics.lastMatch ? 
                        new Date(selectedPolicy.statistics.lastMatch).toLocaleString() : 
                        'Jamais'
                      }
                    </div>
                  </div>
                </div>
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
            Politiques QoS
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Configuration et gestion des politiques de qualité de service
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Download className="w-4 h-4" />
            <span>Exporter</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Upload className="w-4 h-4" />
            <span>Importer</span>
          </button>
          <button 
            onClick={handleCreatePolicy}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Nouvelle politique</span>
          </button>
        </div>
      </div>

      <PolicyMetrics />
      <TabNavigation />
      
      {activeTab === 'list' && (
        <>
          <FiltersAndSearch />
          <PoliciesTable />
        </>
      )}
      
      {activeTab === 'analytics' && <AnalyticsCharts />}
      {activeTab === 'deployment' && <DeploymentControls />}
      
      <PolicyModal />
    </div>
  );
};

export default QoSPolicies;