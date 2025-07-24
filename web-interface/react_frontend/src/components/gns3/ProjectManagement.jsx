// ProjectManagement.jsx - Gestion moderne des projets GNS3
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Copy, 
  Play, 
  Pause, 
  Square, 
  Eye, 
  Search, 
  Filter,
  RefreshCw,
  Download,
  Upload,
  Save,
  X,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Building,
  Users,
  Calendar,
  FileText,
  Settings,
  Activity,
  Target,
  Network,
  Router,
  Monitor,
  Database,
  Server,
  Globe,
  Wifi,
  Terminal,
  Shield,
  Bell,
  Award,
  Layers,
  Signal,
  Zap,
  HardDrive,
  Cpu,
  MemoryStick,
  Gauge,
  TrendingUp,
  TrendingDown,
  BarChart3,
  PieChart,
  LineChart
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Pie, Cell, LineChart as RechartsLineChart, Line } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const ProjectManagement = ({ isVisible = true }) => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('view'); // 'view', 'edit', 'create'
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterServer, setFilterServer] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('modified');
  const [viewMode, setViewMode] = useState('table');
  const [selectedProjects, setSelectedProjects] = useState([]);
  const [loading, setLoading] = useState(false);

  const { getThemeClasses } = useTheme();

  // Serveurs disponibles
  const servers = [
    { id: 'server-001', name: 'GNS3-Server-01', host: '192.168.1.10' },
    { id: 'server-002', name: 'GNS3-Server-02', host: '192.168.1.11' },
    { id: 'server-003', name: 'GNS3-Server-03', host: '192.168.1.12' }
  ];

  // Statuts des projets
  const projectStatuses = {
    'opened': { label: 'Ouvert', color: 'text-green-400', bgColor: 'bg-green-900/30', icon: CheckCircle },
    'closed': { label: 'Fermé', color: 'text-gray-400', bgColor: 'bg-gray-900/30', icon: XCircle },
    'loading': { label: 'Chargement', color: 'text-yellow-400', bgColor: 'bg-yellow-900/30', icon: Clock },
    'error': { label: 'Erreur', color: 'text-red-400', bgColor: 'bg-red-900/30', icon: AlertTriangle }
  };

  // Données mockées des projets
  const mockProjects = [
    {
      id: 'project-001',
      name: 'Lab Network Security',
      description: 'Laboratoire de sécurité réseau avec firewall et IDS',
      serverId: 'server-001',
      serverName: 'GNS3-Server-01',
      status: 'opened',
      nodes: 8,
      links: 12,
      templates: 5,
      snapshots: 3,
      size: 45.6, // MB
      created: '2024-01-10T09:00:00Z',
      modified: '2024-01-15T10:15:00Z',
      opened: '2024-01-15T08:30:00Z',
      author: 'admin@company.com',
      version: '2.2.44',
      autoStart: true,
      autoClose: false,
      path: '/opt/gns3/projects/lab-security',
      variables: [
        { name: 'GATEWAY_IP', value: '192.168.1.1' },
        { name: 'DNS_SERVER', value: '8.8.8.8' }
      ],
      tags: ['security', 'firewall', 'ids'],
      lastActivity: '2024-01-15T10:15:00Z',
      totalUptime: 28800, // 8 heures
      avgCpuUsage: 34.5,
      avgMemoryUsage: 56.7
    },
    {
      id: 'project-002',
      name: 'MPLS Topology',
      description: 'Topologie MPLS avec routeurs PE et CE',
      serverId: 'server-001',
      serverName: 'GNS3-Server-01',
      status: 'opened',
      nodes: 12,
      links: 18,
      templates: 3,
      snapshots: 5,
      size: 67.8,
      created: '2024-01-08T14:30:00Z',
      modified: '2024-01-15T09:45:00Z',
      opened: '2024-01-15T07:00:00Z',
      author: 'network@company.com',
      version: '2.2.44',
      autoStart: false,
      autoClose: true,
      path: '/opt/gns3/projects/mpls-topology',
      variables: [
        { name: 'AS_NUMBER', value: '65001' },
        { name: 'MPLS_LABELS', value: '100-200' }
      ],
      tags: ['mpls', 'routing', 'carrier'],
      lastActivity: '2024-01-15T09:45:00Z',
      totalUptime: 32400,
      avgCpuUsage: 45.2,
      avgMemoryUsage: 67.3
    },
    {
      id: 'project-003',
      name: 'Campus Network',
      description: 'Réseau campus avec VLAN et routage inter-VLAN',
      serverId: 'server-002',
      serverName: 'GNS3-Server-02',
      status: 'closed',
      nodes: 24,
      links: 36,
      templates: 8,
      snapshots: 2,
      size: 123.4,
      created: '2024-01-05T11:00:00Z',
      modified: '2024-01-12T16:20:00Z',
      opened: null,
      author: 'admin@company.com',
      version: '2.2.44',
      autoStart: true,
      autoClose: false,
      path: '/opt/gns3/projects/campus-network',
      variables: [
        { name: 'VLAN_BASE', value: '100' },
        { name: 'MGMT_VLAN', value: '999' }
      ],
      tags: ['campus', 'vlan', 'switching'],
      lastActivity: '2024-01-12T16:20:00Z',
      totalUptime: 0,
      avgCpuUsage: 0,
      avgMemoryUsage: 0
    },
    {
      id: 'project-004',
      name: 'WAN Simulation',
      description: 'Simulation WAN avec plusieurs sites distants',
      serverId: 'server-002',
      serverName: 'GNS3-Server-02',
      status: 'opened',
      nodes: 16,
      links: 24,
      templates: 6,
      snapshots: 7,
      size: 89.2,
      created: '2024-01-03T16:45:00Z',
      modified: '2024-01-14T14:30:00Z',
      opened: '2024-01-14T13:15:00Z',
      author: 'network@company.com',
      version: '2.2.44',
      autoStart: false,
      autoClose: false,
      path: '/opt/gns3/projects/wan-simulation',
      variables: [
        { name: 'SITE_COUNT', value: '5' },
        { name: 'WAN_PROTOCOL', value: 'OSPF' }
      ],
      tags: ['wan', 'ospf', 'multi-site'],
      lastActivity: '2024-01-14T14:30:00Z',
      totalUptime: 14400,
      avgCpuUsage: 28.9,
      avgMemoryUsage: 41.2
    },
    {
      id: 'project-005',
      name: 'SDN Lab',
      description: 'Laboratoire SDN avec OpenFlow et contrôleur',
      serverId: 'server-003',
      serverName: 'GNS3-Server-03',
      status: 'error',
      nodes: 10,
      links: 15,
      templates: 4,
      snapshots: 1,
      size: 34.7,
      created: '2024-01-02T10:30:00Z',
      modified: '2024-01-11T11:45:00Z',
      opened: null,
      author: 'sdn@company.com',
      version: '2.2.44',
      autoStart: true,
      autoClose: true,
      path: '/opt/gns3/projects/sdn-lab',
      variables: [
        { name: 'CONTROLLER_IP', value: '192.168.100.1' },
        { name: 'OPENFLOW_VERSION', value: '1.3' }
      ],
      tags: ['sdn', 'openflow', 'controller'],
      lastActivity: '2024-01-11T11:45:00Z',
      totalUptime: 0,
      avgCpuUsage: 0,
      avgMemoryUsage: 0
    }
  ];

  // Initialisation des données
  useEffect(() => {
    setProjects(mockProjects);
  }, []);

  // Filtrage et tri des projets
  const filteredProjects = projects.filter(project => {
    const matchesStatus = filterStatus === 'all' || project.status === filterStatus;
    const matchesServer = filterServer === 'all' || project.serverId === filterServer;
    const matchesSearch = searchQuery === '' || 
      project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
      project.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    return matchesStatus && matchesServer && matchesSearch;
  });

  const sortedProjects = [...filteredProjects].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.name.localeCompare(b.name);
      case 'status':
        return a.status.localeCompare(b.status);
      case 'modified':
        return new Date(b.modified) - new Date(a.modified);
      case 'created':
        return new Date(b.created) - new Date(a.created);
      case 'size':
        return b.size - a.size;
      case 'nodes':
        return b.nodes - a.nodes;
      default:
        return 0;
    }
  });

  // Statistiques des projets
  const projectStats = {
    total: projects.length,
    opened: projects.filter(p => p.status === 'opened').length,
    closed: projects.filter(p => p.status === 'closed').length,
    error: projects.filter(p => p.status === 'error').length,
    totalNodes: projects.reduce((sum, p) => sum + p.nodes, 0),
    totalSize: projects.reduce((sum, p) => sum + p.size, 0),
    avgSize: projects.reduce((sum, p) => sum + p.size, 0) / projects.length
  };

  // Données pour graphiques
  const statusDistribution = [
    { name: 'Ouverts', value: projectStats.opened, color: '#10B981' },
    { name: 'Fermés', value: projectStats.closed, color: '#6B7280' },
    { name: 'Erreurs', value: projectStats.error, color: '#EF4444' }
  ];

  const sizeDistribution = projects.map(p => ({
    name: p.name,
    size: p.size,
    nodes: p.nodes
  }));

  // Gestion des actions
  const handleCreateProject = () => {
    setSelectedProject(null);
    setModalMode('create');
    setIsModalOpen(true);
  };

  const handleEditProject = (project) => {
    setSelectedProject(project);
    setModalMode('edit');
    setIsModalOpen(true);
  };

  const handleViewProject = (project) => {
    setSelectedProject(project);
    setModalMode('view');
    setIsModalOpen(true);
  };

  const handleDeleteProject = (projectId) => {
    setProjects(prev => prev.filter(p => p.id !== projectId));
    setSelectedProjects(prev => prev.filter(id => id !== projectId));
  };

  const handleDuplicateProject = (project) => {
    const newProject = {
      ...project,
      id: `project-${Date.now()}`,
      name: `${project.name} (Copie)`,
      status: 'closed',
      created: new Date().toISOString(),
      modified: new Date().toISOString(),
      opened: null,
      snapshots: 0,
      lastActivity: new Date().toISOString(),
      totalUptime: 0,
      avgCpuUsage: 0,
      avgMemoryUsage: 0
    };
    setProjects(prev => [...prev, newProject]);
  };

  const handleProjectAction = (projectId, action) => {
    setProjects(prev => prev.map(project => 
      project.id === projectId 
        ? { 
            ...project, 
            status: action === 'open' ? 'opened' : 
                   action === 'close' ? 'closed' : 
                   action === 'stop' ? 'closed' : project.status,
            opened: action === 'open' ? new Date().toISOString() : 
                   action === 'close' ? null : project.opened,
            modified: new Date().toISOString(),
            lastActivity: new Date().toISOString()
          }
        : project
    ));
  };

  const handleBulkAction = (action) => {
    selectedProjects.forEach(projectId => {
      handleProjectAction(projectId, action);
    });
    setSelectedProjects([]);
  };

  // Fonction pour formater l'uptime
  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  // Composant des métriques
  const ProjectMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total Projets</p>
            <p className="text-2xl font-bold text-blue-400">{projectStats.total}</p>
          </div>
          <Building className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Projets Ouverts</p>
            <p className="text-2xl font-bold text-green-400">{projectStats.opened}</p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total Nœuds</p>
            <p className="text-2xl font-bold text-purple-400">{projectStats.totalNodes}</p>
          </div>
          <Network className="w-8 h-8 text-purple-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Taille Totale</p>
            <p className="text-2xl font-bold text-orange-400">{projectStats.totalSize.toFixed(1)}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>MB</p>
          </div>
          <HardDrive className="w-8 h-8 text-orange-400" />
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
          placeholder="Rechercher par nom, description, auteur, tags..."
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
        {Object.entries(projectStatuses).map(([key, status]) => (
          <option key={key} value={key}>{status.label}</option>
        ))}
      </select>
      
      <select
        value={filterServer}
        onChange={(e) => setFilterServer(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les serveurs</option>
        {servers.map(server => (
          <option key={server.id} value={server.id}>{server.name}</option>
        ))}
      </select>
      
      <select
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="modified">Dernière modification</option>
        <option value="name">Nom</option>
        <option value="status">Statut</option>
        <option value="created">Date de création</option>
        <option value="size">Taille</option>
        <option value="nodes">Nombre de nœuds</option>
      </select>
      
      <div className="flex border border-gray-600 rounded overflow-hidden">
        <button
          onClick={() => setViewMode('table')}
          className={`px-3 py-2 text-sm ${viewMode === 'table' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
        >
          Tableau
        </button>
        <button
          onClick={() => setViewMode('grid')}
          className={`px-3 py-2 text-sm ${viewMode === 'grid' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
        >
          Grille
        </button>
      </div>
    </div>
  );

  // Composant du tableau des projets
  const ProjectsTable = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden mb-6`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">
                <input
                  type="checkbox"
                  checked={selectedProjects.length === sortedProjects.length}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedProjects(sortedProjects.map(p => p.id));
                    } else {
                      setSelectedProjects([]);
                    }
                  }}
                  className="rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-500"
                />
              </th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Nom</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Serveur</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Nœuds</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Taille</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Modifié</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedProjects.map(project => {
              const statusConfig = projectStatuses[project.status];
              const StatusIcon = statusConfig.icon;
              
              return (
                <tr key={project.id} className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
                  <td className="py-3 px-4">
                    <input
                      type="checkbox"
                      checked={selectedProjects.includes(project.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedProjects(prev => [...prev, project.id]);
                        } else {
                          setSelectedProjects(prev => prev.filter(id => id !== project.id));
                        }
                      }}
                      className="rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} font-medium`}>
                    <div className="max-w-xs">
                      <div className="truncate">{project.name}</div>
                      <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs truncate`}>
                        {project.description}
                      </div>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                    {project.serverName}
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
                      <span className="font-medium">{project.nodes}</span>
                      <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                        / {project.links} liens
                      </span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {project.size.toFixed(1)} MB
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                    {new Date(project.modified).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleViewProject(project)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Voir détails"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleEditProject(project)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Modifier"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDuplicateProject(project)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Dupliquer"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                      {project.status === 'opened' ? (
                        <button
                          onClick={() => handleProjectAction(project.id, 'close')}
                          className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                          title="Fermer"
                        >
                          <Square className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => handleProjectAction(project.id, 'open')}
                          className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                          title="Ouvrir"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteProject(project.id)}
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

  // Composant de la vue grille
  const ProjectsGrid = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      {sortedProjects.map(project => {
        const statusConfig = projectStatuses[project.status];
        const StatusIcon = statusConfig.icon;
        
        return (
          <div key={project.id} className={`${getThemeClasses('card', 'dashboard')} p-4`}>
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <StatusIcon className={`w-4 h-4 ${statusConfig.color}`} />
                  <h3 className={`${getThemeClasses('text', 'dashboard')} font-medium truncate`}>
                    {project.name}
                  </h3>
                </div>
                <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm line-clamp-2`}>
                  {project.description}
                </p>
              </div>
              <input
                type="checkbox"
                checked={selectedProjects.includes(project.id)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedProjects(prev => [...prev, project.id]);
                  } else {
                    setSelectedProjects(prev => prev.filter(id => id !== project.id));
                  }
                }}
                className="rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-500"
              />
            </div>
            
            <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
              <div className="text-center">
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  Nœuds
                </div>
                <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                  {project.nodes}
                </div>
              </div>
              <div className="text-center">
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  Liens
                </div>
                <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                  {project.links}
                </div>
              </div>
              <div className="text-center">
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  Taille
                </div>
                <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                  {project.size.toFixed(1)} MB
                </div>
              </div>
            </div>
            
            <div className="flex flex-wrap gap-1 mb-3">
              {project.tags.map(tag => (
                <span key={tag} className="px-2 py-1 bg-blue-900/30 text-blue-400 text-xs rounded">
                  {tag}
                </span>
              ))}
            </div>
            
            <div className="flex items-center justify-between">
              <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                Modifié: {new Date(project.modified).toLocaleDateString()}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handleViewProject(project)}
                  className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                  title="Voir détails"
                >
                  <Eye className="w-4 h-4" />
                </button>
                {project.status === 'opened' ? (
                  <button
                    onClick={() => handleProjectAction(project.id, 'close')}
                    className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                    title="Fermer"
                  >
                    <Square className="w-4 h-4" />
                  </button>
                ) : (
                  <button
                    onClick={() => handleProjectAction(project.id, 'open')}
                    className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                    title="Ouvrir"
                  >
                    <Play className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );

  // Composant des graphiques
  const ProjectCharts = () => (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Répartition des Statuts
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

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Taille des Projets
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={sizeDistribution}>
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
              <Bar dataKey="size" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );

  // Modal de détails/édition
  const ProjectModal = () => {
    if (!isModalOpen) return null;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-lg shadow-2xl border border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
              {modalMode === 'create' ? 'Nouveau Projet' : 
               modalMode === 'edit' ? `Modifier: ${selectedProject?.name}` : 
               `Détails: ${selectedProject?.name}`}
            </h2>
            <button
              onClick={() => setIsModalOpen(false)}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {selectedProject && (
            <div className="p-6 space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                    Informations Générales
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Serveur:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedProject.serverName}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Auteur:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedProject.author}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Version:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedProject.version}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Chemin:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')} font-mono text-xs`}>
                        {selectedProject.path}
                      </span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                    Statistiques
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Nœuds:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedProject.nodes}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Liens:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedProject.links}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Templates:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedProject.templates}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Snapshots:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedProject.snapshots}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                  Variables
                </h3>
                <div className="space-y-2">
                  {selectedProject.variables.map((variable, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-700/50 rounded">
                      <span className={`${getThemeClasses('text', 'dashboard')} font-mono text-sm`}>
                        {variable.name}
                      </span>
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                        {variable.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                  Tags
                </h3>
                <div className="flex flex-wrap gap-2">
                  {selectedProject.tags.map(tag => (
                    <span key={tag} className="px-2 py-1 bg-blue-900/30 text-blue-400 text-sm rounded">
                      {tag}
                    </span>
                  ))}
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
            Gestion des Projets
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Administration des projets GNS3
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {selectedProjects.length > 0 && (
            <div className="flex items-center space-x-2 mr-4">
              <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                {selectedProjects.length} sélectionné(s)
              </span>
              <button
                onClick={() => handleBulkAction('open')}
                className="px-3 py-1 bg-green-600 hover:bg-green-700 text-white text-sm rounded transition-colors"
              >
                Ouvrir
              </button>
              <button
                onClick={() => handleBulkAction('close')}
                className="px-3 py-1 bg-gray-600 hover:bg-gray-700 text-white text-sm rounded transition-colors"
              >
                Fermer
              </button>
            </div>
          )}
          
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Download className="w-4 h-4" />
            <span>Exporter</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Upload className="w-4 h-4" />
            <span>Importer</span>
          </button>
          <button 
            onClick={handleCreateProject}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Nouveau Projet</span>
          </button>
        </div>
      </div>

      <ProjectMetrics />
      <FiltersAndSearch />
      <ProjectCharts />
      {viewMode === 'table' ? <ProjectsTable /> : <ProjectsGrid />}
      <ProjectModal />
    </div>
  );
};

export default ProjectManagement;