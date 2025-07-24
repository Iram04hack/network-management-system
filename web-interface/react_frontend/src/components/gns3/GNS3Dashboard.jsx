// GNS3Dashboard.jsx - Dashboard GNS3 avec monitoring avancé
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  Server, 
  Play, 
  Pause, 
  Square, 
  RefreshCw, 
  Settings, 
  Eye, 
  TrendingUp, 
  TrendingDown,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Gauge,
  Zap,
  Network,
  Router,
  Monitor,
  Database,
  Globe,
  Wifi,
  Terminal,
  Layers,
  Target,
  Signal,
  Cpu,
  HardDrive,
  MemoryStick,
  Thermometer,
  Users,
  Building,
  Calendar,
  Download,
  Upload,
  FileText,
  Shield,
  AlertCircle,
  Bell,
  Plus,
  Edit,
  Trash2,
  Copy,
  Search,
  Filter,
  BarChart3,
  PieChart,
  LineChart
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell, AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const GNS3Dashboard = ({ isVisible = true }) => {
  const [servers, setServers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [systemMetrics, setSystemMetrics] = useState({});
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
  const [selectedServer, setSelectedServer] = useState('all');
  const [timeRange, setTimeRange] = useState('1h');
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [loading, setLoading] = useState(false);

  const { getThemeClasses } = useTheme();

  // Serveurs GNS3 mockés
  const mockServers = [
    {
      id: 'server-001',
      name: 'GNS3-Server-01',
      host: '192.168.1.10',
      port: 3080,
      status: 'running',
      version: '2.2.44',
      protocol: 'http',
      uptime: 259200, // 3 jours en secondes
      cpu: 45.2,
      memory: 67.8,
      storage: 78.5,
      projects: 8,
      nodes: 24,
      templates: 156,
      lastCheck: '2024-01-15T10:30:00Z'
    },
    {
      id: 'server-002',
      name: 'GNS3-Server-02',
      host: '192.168.1.11',
      port: 3080,
      status: 'running',
      version: '2.2.44',
      protocol: 'http',
      uptime: 432000, // 5 jours en secondes
      cpu: 23.7,
      memory: 45.3,
      storage: 56.2,
      projects: 5,
      nodes: 12,
      templates: 89,
      lastCheck: '2024-01-15T10:29:00Z'
    },
    {
      id: 'server-003',
      name: 'GNS3-Server-03',
      host: '192.168.1.12',
      port: 3080,
      status: 'stopped',
      version: '2.2.44',
      protocol: 'http',
      uptime: 0,
      cpu: 0,
      memory: 0,
      storage: 89.1,
      projects: 0,
      nodes: 0,
      templates: 67,
      lastCheck: '2024-01-15T09:45:00Z'
    }
  ];

  // Projets mockés
  const mockProjects = [
    {
      id: 'project-001',
      name: 'Lab Network Security',
      serverId: 'server-001',
      status: 'opened',
      nodes: 8,
      links: 12,
      created: '2024-01-10T09:00:00Z',
      modified: '2024-01-15T10:15:00Z',
      author: 'admin@company.com',
      description: 'Laboratoire de sécurité réseau avec firewall et IDS',
      size: 45.6, // MB
      autoStart: true,
      autoClose: false
    },
    {
      id: 'project-002',
      name: 'MPLS Topology',
      serverId: 'server-001',
      status: 'opened',
      nodes: 12,
      links: 18,
      created: '2024-01-08T14:30:00Z',
      modified: '2024-01-15T09:45:00Z',
      author: 'network@company.com',
      description: 'Topologie MPLS avec routeurs PE et CE',
      size: 67.8,
      autoStart: false,
      autoClose: true
    },
    {
      id: 'project-003',
      name: 'Campus Network',
      serverId: 'server-002',
      status: 'closed',
      nodes: 24,
      links: 36,
      created: '2024-01-05T11:00:00Z',
      modified: '2024-01-12T16:20:00Z',
      author: 'admin@company.com',
      description: 'Réseau campus avec VLAN et routage inter-VLAN',
      size: 123.4,
      autoStart: true,
      autoClose: false
    }
  ];

  // Nœuds mockés
  const mockNodes = [
    {
      id: 'node-001',
      name: 'Router-1',
      type: 'router',
      projectId: 'project-001',
      serverId: 'server-001',
      status: 'started',
      template: 'Cisco 7200',
      console: 5000,
      cpu: 12.5,
      memory: 34.2,
      uptime: 3600,
      interfaces: [
        { name: 'GigabitEthernet0/0', status: 'up', ip: '192.168.1.1/24' },
        { name: 'GigabitEthernet0/1', status: 'down', ip: '10.0.0.1/30' }
      ]
    },
    {
      id: 'node-002',
      name: 'Switch-1',
      type: 'switch',
      projectId: 'project-001',
      serverId: 'server-001',
      status: 'started',
      template: 'Cisco IOS Switch',
      console: 5001,
      cpu: 8.3,
      memory: 23.7,
      uptime: 3500,
      interfaces: [
        { name: 'FastEthernet0/1', status: 'up', ip: null },
        { name: 'FastEthernet0/2', status: 'up', ip: null }
      ]
    },
    {
      id: 'node-003',
      name: 'PC-1',
      type: 'host',
      projectId: 'project-001',
      serverId: 'server-001',
      status: 'stopped',
      template: 'VPCS',
      console: 5002,
      cpu: 0,
      memory: 0,
      uptime: 0,
      interfaces: [
        { name: 'eth0', status: 'down', ip: '192.168.1.100/24' }
      ]
    }
  ];

  // Métriques système mockées
  const mockSystemMetrics = {
    totalServers: 3,
    runningServers: 2,
    totalProjects: 13,
    openProjects: 8,
    totalNodes: 56,
    runningNodes: 32,
    totalTemplates: 312,
    systemLoad: 34.6,
    memoryUsage: 56.8,
    storageUsage: 74.2,
    networkTraffic: 45.3
  };

  // Données historiques pour graphiques
  const generateHistoricalData = () => {
    const hours = timeRange === '1h' ? 12 : timeRange === '24h' ? 24 : 7;
    return Array.from({ length: hours }, (_, i) => ({
      time: timeRange === '7d' ? `J${i + 1}` : `${i}:00`,
      cpu: Math.floor(Math.random() * 60) + 20,
      memory: Math.floor(Math.random() * 40) + 40,
      storage: Math.floor(Math.random() * 20) + 70,
      nodes: Math.floor(Math.random() * 10) + 25,
      projects: Math.floor(Math.random() * 5) + 5
    }));
  };

  // Données de répartition
  const nodeTypeDistribution = [
    { name: 'Routeurs', value: 18, color: '#3B82F6' },
    { name: 'Switches', value: 14, color: '#10B981' },
    { name: 'Hôtes', value: 12, color: '#F59E0B' },
    { name: 'Firewalls', value: 8, color: '#EF4444' },
    { name: 'Autres', value: 4, color: '#6B7280' }
  ];

  const statusDistribution = [
    { name: 'Démarrés', value: 32, color: '#10B981' },
    { name: 'Arrêtés', value: 18, color: '#EF4444' },
    { name: 'Suspendus', value: 6, color: '#F59E0B' }
  ];

  // Initialisation des données
  useEffect(() => {
    setServers(mockServers);
    setProjects(mockProjects);
    setNodes(mockNodes);
    setSystemMetrics(mockSystemMetrics);
  }, []);

  // Simulation temps réel
  useEffect(() => {
    if (!isRealTimeEnabled) return;

    const interval = setInterval(() => {
      setSystemMetrics(prev => ({
        ...prev,
        systemLoad: Math.max(0, Math.min(100, prev.systemLoad + (Math.random() - 0.5) * 10)),
        memoryUsage: Math.max(0, Math.min(100, prev.memoryUsage + (Math.random() - 0.5) * 8)),
        networkTraffic: Math.max(0, Math.min(100, prev.networkTraffic + (Math.random() - 0.5) * 15))
      }));
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [isRealTimeEnabled, refreshInterval]);

  // Fonction pour formater l'uptime
  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}j ${hours}h ${minutes}m`;
  };

  // Fonction pour obtenir la couleur selon le statut
  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
      case 'started':
      case 'opened':
        return 'text-green-400';
      case 'stopped':
      case 'closed':
        return 'text-red-400';
      case 'suspended':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  // Fonction pour obtenir l'icône selon le statut
  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
      case 'started':
      case 'opened':
        return CheckCircle;
      case 'stopped':
      case 'closed':
        return XCircle;
      case 'suspended':
        return AlertTriangle;
      default:
        return AlertCircle;
    }
  };

  // Composant des métriques principales
  const SystemMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Serveurs GNS3</p>
            <p className="text-2xl font-bold text-blue-400">{systemMetrics.runningServers}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              / {systemMetrics.totalServers} total
            </p>
          </div>
          <Server className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Projets Ouverts</p>
            <p className="text-2xl font-bold text-green-400">{systemMetrics.openProjects}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              / {systemMetrics.totalProjects} total
            </p>
          </div>
          <Building className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Nœuds Actifs</p>
            <p className="text-2xl font-bold text-purple-400">{systemMetrics.runningNodes}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              / {systemMetrics.totalNodes} total
            </p>
          </div>
          <Router className="w-8 h-8 text-purple-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Charge Système</p>
            <p className="text-2xl font-bold text-orange-400">{systemMetrics.systemLoad?.toFixed(1)}%</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              CPU + Mémoire
            </p>
          </div>
          <Activity className="w-8 h-8 text-orange-400" />
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
              Serveur:
            </span>
            <select
              value={selectedServer}
              onChange={(e) => setSelectedServer(e.target.value)}
              className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="all">Tous les serveurs</option>
              {servers.map(server => (
                <option key={server.id} value={server.id}>{server.name}</option>
              ))}
            </select>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="1h">1 heure</option>
            <option value="24h">24 heures</option>
            <option value="7d">7 jours</option>
          </select>
          
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

  // Composant des serveurs
  const ServersStatus = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-6`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
        État des Serveurs GNS3
      </h3>
      <div className="space-y-3">
        {servers.map(server => {
          const StatusIcon = getStatusIcon(server.status);
          return (
            <div key={server.id} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
              <div className="flex items-center space-x-3">
                <StatusIcon className={`w-5 h-5 ${getStatusColor(server.status)}`} />
                <div>
                  <div className="flex items-center space-x-2">
                    <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {server.name}
                    </span>
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                      v{server.version}
                    </span>
                  </div>
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    {server.host}:{server.port}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-6">
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    CPU
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {server.cpu}%
                  </div>
                </div>
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Mémoire
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {server.memory}%
                  </div>
                </div>
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Projets
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {server.projects}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Uptime
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {server.status === 'running' ? formatUptime(server.uptime) : '-'}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Composant des graphiques
  const PerformanceCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Utilisation des Ressources
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={generateHistoricalData()}>
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
                dataKey="cpu" 
                stackId="1" 
                stroke="#3B82F6" 
                fill="#3B82F6" 
                fillOpacity={0.3}
              />
              <Area 
                type="monotone" 
                dataKey="memory" 
                stackId="1" 
                stroke="#10B981" 
                fill="#10B981" 
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Répartition des Nœuds
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsPieChart>
              <Pie
                data={nodeTypeDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {nodeTypeDistribution.map((entry, index) => (
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
          Activité des Projets
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={generateHistoricalData()}>
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
              <Bar dataKey="projects" fill="#8B5CF6" />
              <Bar dataKey="nodes" fill="#F59E0B" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          État des Nœuds
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RechartsPieChart>
              <Pie
                data={statusDistribution}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {statusDistribution.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </RechartsPieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  // Composant des projets actifs
  const ActiveProjects = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
        Projets Actifs
      </h3>
      <div className="space-y-3">
        {projects.filter(p => p.status === 'opened').map(project => {
          const StatusIcon = getStatusIcon(project.status);
          return (
            <div key={project.id} className="flex items-center justify-between p-3 bg-gray-700/50 rounded">
              <div className="flex items-center space-x-3">
                <StatusIcon className={`w-5 h-5 ${getStatusColor(project.status)}`} />
                <div>
                  <div className="flex items-center space-x-2">
                    <span className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                      {project.name}
                    </span>
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                      ({project.size} MB)
                    </span>
                  </div>
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    {project.description}
                  </div>
                </div>
              </div>
              
              <div className="flex items-center space-x-6">
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Nœuds
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {project.nodes}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Liens
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {project.links}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    Modifié
                  </div>
                  <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {new Date(project.modified).toLocaleDateString()}
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
            Dashboard GNS3
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Monitoring et gestion des serveurs GNS3
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Download className="w-4 h-4" />
            <span>Export</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
            <Settings className="w-4 h-4" />
            <span>Configuration</span>
          </button>
        </div>
      </div>

      <SystemMetrics />
      <MonitoringControls />
      <ServersStatus />
      <PerformanceCharts />
      <ActiveProjects />
    </div>
  );
};

export default GNS3Dashboard;