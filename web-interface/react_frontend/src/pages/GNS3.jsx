import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Search, 
  Plus, 
  Play, 
  Pause, 
  Square, 
  Copy, 
  Trash2, 
  Settings, 
  Save, 
  RefreshCw, 
  ZoomIn, 
  ZoomOut, 
  Download, 
  Upload, 
  Fullscreen, 
  Eye, 
  Edit, 
  Terminal, 
  Network, 
  Router, 
  Wifi, 
  Monitor, 
  Server,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  Database,
  Link,
  Unlink,
  Eraser,
  Target,
  Layers,
  Globe
} from 'lucide-react';

// Import des hooks backend pour GNS3 AMÉLIORÉS
import { useGNS3 } from '../hooks/useGNS3';
import { useApiClients } from '../hooks/useApiClients';
import { useTheme } from '../contexts/ThemeContext';

const GNS3 = () => {
  // Hook pour le thème
  const { getThemeClasses } = useTheme();

  // Hook backend GNS3 pour données dynamiques
  const {
    servers,
    projects,
    nodes: backendNodes,
    snapshots,
    loading: gns3Loading,
    error: gns3Error,
    fetchServers,
    fetchProjects,
    fetchNodes,
    fetchProjectNodes,
    createProject,
    startProject,
    stopProject,
    deleteProject,
    startNode,
    stopNode,
    testServer,
    refreshAllData,
    getGNS3Stats,
    getActiveServers,
    getProjectsByStatus,
    getRunningNodes
  } = useGNS3();

  // Hook pour les clients API intégrés
  const {
    clients: apiClients,
    health: clientsHealth,
    fetchClients,
    fetchClientsHealth,
    getActiveClients
  } = useApiClients();

  // États principaux
  const [activeTab, setActiveTab] = useState('projects');
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('table');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000);

  // États pour l'éditeur de topologie
  const [nodes, setNodes] = useState([]);
  const [connections, setConnections] = useState([]);
  const [draggedNode, setDraggedNode] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(100);
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 400 });
  const [nodeCounter, setNodeCounter] = useState(1);

  // États des modales et UI
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState('');
  const [consoles, setConsoles] = useState([]);

  // Références
  const canvasRef = useRef(null);
  const svgRef = useRef(null);

  // Types d'équipements GNS3
  const deviceTypes = {
    router: { 
      name: 'Routeur', 
      icon: Router, 
      color: 'bg-blue-600', 
      borderColor: 'border-blue-400',
      textColor: 'text-blue-400'
    },
    switch: { 
      name: 'Switch', 
      icon: Network, 
      color: 'bg-green-600', 
      borderColor: 'border-green-400',
      textColor: 'text-green-400'
    },
    pc: { 
      name: 'PC Client', 
      icon: Monitor, 
      color: 'bg-purple-600', 
      borderColor: 'border-purple-400',
      textColor: 'text-purple-400'
    },
    firewall: { 
      name: 'Firewall', 
      icon: Target, 
      color: 'bg-red-600', 
      borderColor: 'border-red-400',
      textColor: 'text-red-400'
    },
    server: { 
      name: 'Serveur', 
      icon: Server, 
      color: 'bg-yellow-600', 
      borderColor: 'border-yellow-400',
      textColor: 'text-yellow-400'
    },
    cloud: { 
      name: 'Cloud', 
      icon: Globe, 
      color: 'bg-gray-600', 
      borderColor: 'border-gray-400',
      textColor: 'text-gray-400'
    }
  };

  // Chargement initial des données AMÉLIORÉ
  useEffect(() => {
    const loadGNS3Data = async () => {
      try {
        await Promise.allSettled([
          fetchServers(),
          fetchProjects(),
          fetchNodes(),
          fetchClients(),
          fetchClientsHealth()
        ]);
      } catch (error) {
        console.error('Erreur lors du chargement des données GNS3:', error);
      }
    };

    loadGNS3Data();
  }, []);

  // Auto-refresh NOUVEAU
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      try {
        await Promise.allSettled([
          refreshAllData(),
          fetchClientsHealth()
        ]);
      } catch (error) {
        console.error('Erreur lors du refresh automatique GNS3:', error);
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Synchronisation des nœuds backend avec l'état local
  useEffect(() => {
    if (backendNodes && Array.isArray(backendNodes)) {
      setNodes(backendNodes.map((node, index) => ({
        id: node.id || `node-${index}`,
        name: node.name || `Node-${index}`,
        type: node.node_type || 'router',
        x: node.x || Math.random() * 400,
        y: node.y || Math.random() * 300,
        ip: node.ip_address || `192.168.1.${index + 10}`,
        status: node.status || 'stopped',
        console_host: node.console_host,
        console_port: node.console_port,
        project_id: node.project_id
      })));
    }
  }, [backendNodes]);

  // Mise à jour de la taille du canvas
  useEffect(() => {
    const updateCanvasSize = () => {
      if (canvasRef.current) {
        const rect = canvasRef.current.getBoundingClientRect();
        setCanvasSize({ width: rect.width, height: rect.height });
      }
    };
    
    updateCanvasSize();
    window.addEventListener('resize', updateCanvasSize);
    return () => window.removeEventListener('resize', updateCanvasSize);
  }, [activeTab, selectedProject]);

  // Fonctions utilitaires
  const generateNodeId = () => `node_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  const generateConnectionId = () => `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Données filtrées
  const filteredProjects = projects.filter(project => 
    project.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Statistiques calculées
  const stats = getGNS3Stats();

  // Fonctions de gestion
  const handleRefreshData = useCallback(async () => {
    try {
      await refreshAllData();
    } catch (error) {
      console.error('Erreur lors du refresh manuel:', error);
    }
  }, [refreshAllData]);

  const handleOpenProject = useCallback((project) => {
    setSelectedProject(project);
    setActiveTab('editor');
    
    // Charger les nœuds du projet
    if (project.id) {
      fetchProjectNodes(project.id);
    }
    
    // Simuler l'ouverture de consoles pour ce projet
    setConsoles([
      { id: 1, name: 'Router-1', type: 'router', history: ['Router-1> show ip interface brief', 'Router-1> enable'] },
      { id: 2, name: 'Switch-1', type: 'switch', history: ['Switch-1> show vlan', 'Switch-1> enable'] },
    ]);
  }, [fetchProjectNodes]);

  const handleProjectAction = useCallback(async (project, action) => {
    try {
      let result;
      switch (action) {
        case 'start':
          result = await startProject(project.id);
          break;
        case 'stop':
          result = await stopProject(project.id);
          break;
        case 'delete':
          result = await deleteProject(project.id);
          break;
        case 'duplicate':
          // Logique de duplication
          break;
        default:
          console.log(`Action ${action} sur projet ${project.id}`);
      }
    } catch (error) {
      console.error(`Erreur lors de l'action ${action}:`, error);
    }
  }, [startProject, stopProject, deleteProject]);

  const handleNodeAction = useCallback(async (node, action) => {
    try {
      let result;
      switch (action) {
        case 'start':
          result = await startNode(node.id);
          break;
        case 'stop':
          result = await stopNode(node.id);
          break;
        case 'console':
          handleOpenConsole(node);
          break;
        default:
          console.log(`Action ${action} sur nœud ${node.id}`);
      }
    } catch (error) {
      console.error(`Erreur lors de l'action ${action}:`, error);
    }
  }, [startNode, stopNode]);

  // Fonctions pour l'éditeur de topologie
  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 10, 200));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 10, 50));
  const handleResetZoom = () => setZoomLevel(100);

  // Fonctions de drag and drop
  const handleDragStart = (deviceType, e) => {
    e.dataTransfer.setData('deviceType', deviceType);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const deviceType = e.dataTransfer.getData('deviceType');
    
    if (deviceType && canvasRef.current) {
      const rect = canvasRef.current.getBoundingClientRect();
      const x = (e.clientX - rect.left) / (zoomLevel / 100);
      const y = (e.clientY - rect.top) / (zoomLevel / 100);
      
      const newNode = {
        id: generateNodeId(),
        type: deviceType,
        x: Math.max(32, Math.min(x - 32, canvasSize.width - 64)),
        y: Math.max(32, Math.min(y - 32, canvasSize.height - 64)),
        name: `${deviceTypes[deviceType].name}-${nodeCounter}`,
        ip: `192.168.1.${nodeCounter + 10}`,
        status: 'stopped'
      };
      
      setNodes(prev => [...prev, newNode]);
      setNodeCounter(prev => prev + 1);
      setSelectedNode(newNode);
    }
  };

  // Fonctions pour les consoles
  const handleOpenConsole = (node) => {
    const existingConsole = consoles.find(c => c.name === node.name);
    if (!existingConsole) {
      const newConsole = {
        id: Date.now(),
        name: node.name,
        type: node.type,
        history: [`${node.name}> show version`, `${node.name}> enable`]
      };
      setConsoles(prev => [...prev, newConsole]);
    }
    setActiveTab('consoles');
  };

  const handleCloseConsole = (consoleId) => {
    setConsoles(consoles.filter(c => c.id !== consoleId));
  };

  // Composants d'interface
  const HeaderControls = () => (
    <div className="mb-3">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div>
          <h1 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Simulateur GNS3
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            {stats.totalProjects} projets · {stats.openedProjects} ouverts · {stats.runningNodes} nœuds actifs
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRefreshData}
            disabled={gns3Loading.servers || gns3Loading.projects}
            className={`p-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} transition-colors ${
              gns3Loading.servers || gns3Loading.projects ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            title="Actualiser les données"
          >
            <RefreshCw className={`w-5 h-5 ${gns3Loading.servers || gns3Loading.projects ? 'animate-spin' : ''}`} />
          </button>
          
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`p-2 rounded-lg transition-colors ${
              autoRefresh 
                ? 'bg-green-600 text-white' 
                : `${getThemeClasses('hover', 'dashboard')} ${getThemeClasses('textSecondary', 'dashboard')}`
            }`}
            title={autoRefresh ? 'Désactiver le refresh automatique' : 'Activer le refresh automatique'}
          >
            <Activity className="w-5 h-5" />
          </button>

          {activeTab === 'projects' && (
            <button
              onClick={() => { setModalType('create'); setShowModal(true); }}
              className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4 mr-2" />
              Nouveau projet
            </button>
          )}
        </div>
      </div>
    </div>
  );

  const SearchAndFilters = () => (
    <div className="flex items-center space-x-3 mb-2">
      <div className="relative flex-1">
        <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher un projet..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-8 pr-3 py-1.5 text-sm bg-gray-800 text-white border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
        />
      </div>
      <select
        value={viewMode}
        onChange={(e) => setViewMode(e.target.value)}
        className="px-3 py-1.5 text-sm bg-gray-800 text-white border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="table">Tableau</option>
        <option value="grid">Grille</option>
      </select>
    </div>
  );

  const StatsCards = () => (
    <div className="grid grid-cols-2 lg:grid-cols-6 gap-3 mb-4">
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Serveurs</p>
            <p className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>{stats.totalServers}</p>
          </div>
          <Database className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Projets</p>
            <p className="text-2xl font-bold text-green-400">{stats.totalProjects}</p>
          </div>
          <Layers className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Ouverts</p>
            <p className="text-2xl font-bold text-yellow-400">{stats.openedProjects}</p>
          </div>
          <Eye className="w-8 h-8 text-yellow-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Nœuds</p>
            <p className="text-2xl font-bold text-purple-400">{stats.totalNodes}</p>
          </div>
          <Network className="w-8 h-8 text-purple-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Actifs</p>
            <p className="text-2xl font-bold text-green-400">{stats.runningNodes}</p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Snapshots</p>
            <p className="text-2xl font-bold text-cyan-400">{stats.totalSnapshots}</p>
          </div>
          <Clock className="w-8 h-8 text-cyan-400" />
        </div>
      </div>
    </div>
  );

  const ProjectsView = () => (
    <div>
      {viewMode === 'table' ? (
        <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden`}>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className={`${getThemeClasses('background', 'dashboard')} border-b border-gray-600`}>
                <tr>
                  <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Nom</th>
                  <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Statut</th>
                  <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Nœuds</th>
                  <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Dernière modification</th>
                  <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredProjects.map((project) => (
                  <tr 
                    key={project.id} 
                    className={`border-b border-gray-600/50 ${getThemeClasses('hover', 'dashboard')} transition-all cursor-pointer`}
                    onClick={() => handleOpenProject(project)}
                  >
                    <td className="py-1 px-3">
                      <div>
                        <div className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>{project.name}</div>
                        <div className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>
                          {project.description || 'Aucune description'}
                        </div>
                      </div>
                    </td>
                    <td className="py-1 px-3">
                      <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded-full ${
                        project.status === 'opened' 
                          ? 'bg-green-900/30 text-green-400' 
                          : 'bg-gray-900/30 text-gray-400'
                      }`}>
                        {project.status === 'opened' ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                        {project.status === 'opened' ? 'Ouvert' : 'Fermé'}
                      </span>
                    </td>
                    <td className="py-1 px-3">
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{project.nodes_count || 0}</span>
                    </td>
                    <td className="py-1 px-3">
                      <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>
                        {project.updated_at ? new Date(project.updated_at).toLocaleDateString() : 'N/A'}
                      </span>
                    </td>
                    <td className="py-1 px-3">
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleProjectAction(project, project.status === 'opened' ? 'stop' : 'start');
                          }}
                          className={`p-1 rounded ${getThemeClasses('hover', 'dashboard')} transition-colors`}
                          title={project.status === 'opened' ? 'Arrêter' : 'Démarrer'}
                        >
                          {project.status === 'opened' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleProjectAction(project, 'duplicate');
                          }}
                          className={`p-1 rounded ${getThemeClasses('hover', 'dashboard')} transition-colors`}
                          title="Dupliquer"
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleProjectAction(project, 'delete');
                          }}
                          className={`p-1 rounded ${getThemeClasses('hover', 'dashboard')} transition-colors text-red-400 hover:text-red-300`}
                          title="Supprimer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredProjects.map((project) => (
            <div
              key={project.id}
              className={`${getThemeClasses('card', 'dashboard')} p-3 cursor-pointer transition-all hover:scale-105`}
              onClick={() => handleOpenProject(project)}
            >
              <div className="flex items-start justify-between mb-2">
                <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold text-lg`}>{project.name}</h3>
                <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                  project.status === 'opened' 
                    ? 'bg-green-900/30 text-green-400' 
                    : 'bg-gray-900/30 text-gray-400'
                }`}>
                  {project.status === 'opened' ? 'Ouvert' : 'Fermé'}
                </span>
              </div>
              
              <p className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                {project.description || 'Aucune description'}
              </p>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center">
                    <Network className="w-4 h-4 text-blue-400 mr-1" />
                    <span className={`text-sm ${getThemeClasses('text', 'dashboard')}`}>{project.nodes_count || 0} nœuds</span>
                  </div>
                </div>
                
                <div className="flex items-center space-x-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleProjectAction(project, project.status === 'opened' ? 'stop' : 'start');
                    }}
                    className={`p-1 rounded ${getThemeClasses('hover', 'dashboard')} transition-colors`}
                  >
                    {project.status === 'opened' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleProjectAction(project, 'duplicate');
                    }}
                    className={`p-1 rounded ${getThemeClasses('hover', 'dashboard')} transition-colors`}
                  >
                    <Copy className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const TopologyEditor = () => (
    <div>
      {selectedProject && (
        <>
          <div className="mb-2 flex justify-between items-center">
            <div>
              <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>{selectedProject.name}</h2>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')}`}>{selectedProject.description}</p>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={() => setIsConnecting(!isConnecting)}
                className={`flex items-center px-3 py-2 rounded-lg transition-colors ${
                  isConnecting ? 'bg-blue-600 text-white' : `${getThemeClasses('hover', 'dashboard')} ${getThemeClasses('text', 'dashboard')}`
                }`}
              >
                <Link className="w-4 h-4 mr-2" />
                {isConnecting ? 'Mode connexion' : 'Connecter'}
              </button>
              {isConnecting && (
                <button 
                  onClick={() => { setIsConnecting(false); setConnectionStart(null); }}
                  className={`flex items-center px-3 py-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} ${getThemeClasses('text', 'dashboard')} transition-colors`}
                >
                  <Unlink className="w-4 h-4 mr-2" />
                  Annuler
                </button>
              )}
              <button 
                onClick={() => { setNodes([]); setConnections([]); setSelectedNode(null); setNodeCounter(1); }}
                className="flex items-center px-3 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white transition-colors"
              >
                <Eraser className="w-4 h-4 mr-2" />
                Effacer
              </button>
              <button onClick={handleZoomIn} className={`p-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} transition-colors`}>
                <ZoomIn className="w-4 h-4" />
              </button>
              <button onClick={handleZoomOut} className={`p-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} transition-colors`}>
                <ZoomOut className="w-4 h-4" />
              </button>
              <button onClick={handleResetZoom} className={`px-3 py-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} ${getThemeClasses('text', 'dashboard')} transition-colors`}>
                {zoomLevel}%
              </button>
              <button 
                className="flex items-center px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                <Save className="w-4 h-4 mr-2" />
                Sauvegarder
              </button>
            </div>
          </div>
          
          <div className={`${getThemeClasses('card', 'dashboard')} p-2 mb-2 h-96 relative`}>
            <div 
              ref={canvasRef}
              className="w-full h-full bg-gray-900 rounded-lg relative overflow-hidden"
              style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top left' }}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
            >
              {/* Nœuds */}
              {nodes.map(node => {
                const DeviceIcon = deviceTypes[node.type]?.icon || Router;
                return (
                  <div
                    key={node.id}
                    className={`absolute w-16 h-16 rounded-lg ${deviceTypes[node.type]?.color} border-2 ${deviceTypes[node.type]?.borderColor} 
                      flex items-center justify-center cursor-move hover:brightness-110 transition-all
                      ${selectedNode?.id === node.id ? 'ring-2 ring-blue-400' : ''}
                      ${isConnecting ? 'hover:ring-2 hover:ring-green-400' : ''}`}
                    style={{ 
                      left: node.x, 
                      top: node.y, 
                      zIndex: selectedNode?.id === node.id ? 10 : 2 
                    }}
                    onClick={() => {
                      if (isConnecting) {
                        if (!connectionStart) {
                          setConnectionStart(node);
                        } else if (connectionStart.id !== node.id) {
                          const newConnection = {
                            id: generateConnectionId(),
                            from: connectionStart.id,
                            to: node.id,
                            fromPort: 'eth0',
                            toPort: 'eth0'
                          };
                          setConnections(prev => [...prev, newConnection]);
                          setConnectionStart(null);
                          setIsConnecting(false);
                        }
                      } else {
                        setSelectedNode(node);
                      }
                    }}
                    title={`${node.name} (${node.ip})`}
                  >
                    <DeviceIcon className="w-6 h-6 text-white" />
                    
                    {/* Bouton de suppression */}
                    <button
                      className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 rounded-full 
                        flex items-center justify-center text-white text-xs hover:bg-red-400"
                      onClick={(e) => {
                        e.stopPropagation();
                        setNodes(prev => prev.filter(n => n.id !== node.id));
                        setConnections(prev => prev.filter(c => c.from !== node.id && c.to !== node.id));
                        setSelectedNode(null);
                      }}
                    >
                      ×
                    </button>
                    
                    {/* Label du nœud */}
                    <div className="absolute -bottom-8 left-1/2 transform -translate-x-1/2 
                      text-xs text-white bg-gray-800 px-2 py-1 rounded whitespace-nowrap">
                      {node.name}
                    </div>
                  </div>
                );
              })}

              {/* Message d'aide */}
              {nodes.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center text-gray-500 text-center pointer-events-none">
                  <div>
                    <p className="text-lg mb-2">Éditeur de topologie GNS3</p>
                    <p className="text-sm">Glissez-déposez des équipements depuis la palette</p>
                    <p className="text-sm">Cliquez sur "Connecter" puis sur deux nœuds pour les relier</p>
                  </div>
                </div>
              )}
            </div>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-3">
            {/* Palette d'équipements */}
            <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
              <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold mb-2`}>Palette d'équipements</h3>
              <div className="space-y-3">
                {Object.entries(deviceTypes).map(([type, info]) => {
                  const Icon = info.icon;
                  return (
                    <div 
                      key={type}
                      className={`p-3 border border-gray-700 rounded-lg ${getThemeClasses('hover', 'dashboard')} cursor-move transition-colors`}
                      draggable
                      onDragStart={(e) => handleDragStart(type, e)}
                    >
                      <div className="flex items-center">
                        <div className={`w-10 h-10 rounded-lg ${info.color} border ${info.borderColor} flex items-center justify-center mr-3`}>
                          <Icon className="w-5 h-5 text-white" />
                        </div>
                        <span className={`${getThemeClasses('text', 'dashboard')}`}>{info.name}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
            
            {/* Propriétés */}
            <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
              <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold mb-2`}>Propriétés</h3>
              {selectedNode ? (
                <div className="space-y-2">
                  <div>
                    <label className={`block text-sm ${getThemeClasses('textSecondary', 'dashboard')} mb-1`}>Nom du nœud</label>
                    <input 
                      value={selectedNode.name}
                      onChange={(e) => {
                        const newName = e.target.value;
                        setNodes(prev => prev.map(node => 
                          node.id === selectedNode.id 
                            ? { ...node, name: newName }
                            : node
                        ));
                        setSelectedNode(prev => ({ ...prev, name: newName }));
                      }}
                      className={`w-full px-3 py-2 rounded-lg border ${getThemeClasses('background', 'dashboard')} ${getThemeClasses('text', 'dashboard')} border-gray-600 focus:border-blue-500 focus:outline-none`}
                    />
                  </div>
                  <div>
                    <label className={`block text-sm ${getThemeClasses('textSecondary', 'dashboard')} mb-1`}>Adresse IP</label>
                    <input 
                      value={selectedNode.ip}
                      onChange={(e) => {
                        const newIp = e.target.value;
                        setNodes(prev => prev.map(node => 
                          node.id === selectedNode.id 
                            ? { ...node, ip: newIp }
                            : node
                        ));
                        setSelectedNode(prev => ({ ...prev, ip: newIp }));
                      }}
                      className={`w-full px-3 py-2 rounded-lg border ${getThemeClasses('background', 'dashboard')} ${getThemeClasses('text', 'dashboard')} border-gray-600 focus:border-blue-500 focus:outline-none`}
                    />
                  </div>
                  <div className="pt-2">
                    <button 
                      onClick={() => handleNodeAction(selectedNode, 'console')}
                      className="w-full flex items-center justify-center px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                    >
                      <Terminal className="w-4 h-4 mr-2" />
                      Ouvrir console
                    </button>
                  </div>
                </div>
              ) : (
                <p className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Sélectionnez un nœud pour voir ses propriétés</p>
              )}
            </div>
            
            {/* Statistiques */}
            <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
              <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold mb-2`}>Statistiques</h3>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Nœuds:</span>
                  <span className={`${getThemeClasses('text', 'dashboard')}`}>{nodes.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Connexions:</span>
                  <span className={`${getThemeClasses('text', 'dashboard')}`}>{connections.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Routeurs:</span>
                  <span className={`${getThemeClasses('text', 'dashboard')}`}>{nodes.filter(n => n.type === 'router').length}</span>
                </div>
                <div className="flex justify-between">
                  <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Switches:</span>
                  <span className={`${getThemeClasses('text', 'dashboard')}`}>{nodes.filter(n => n.type === 'switch').length}</span>
                </div>
              </div>
            </div>
            
            {/* Actions rapides */}
            <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
              <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold mb-2`}>Actions rapides</h3>
              <div className="space-y-2">
                <button 
                  className="w-full flex items-center justify-center px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Démarrer tout
                </button>
                <button 
                  className="w-full flex items-center justify-center px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                >
                  <Square className="w-4 h-4 mr-2" />
                  Arrêter tout
                </button>
                <button 
                  className="w-full flex items-center justify-center px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Exporter
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const ConsolesView = () => (
    <div>
      {selectedProject && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
          {consoles.map(console => (
            <div key={console.id} className={`${getThemeClasses('card', 'dashboard')} p-3`}>
              <div className="flex items-center justify-between mb-2">
                <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>{console.name}</h3>
                <button 
                  onClick={() => handleCloseConsole(console.id)}
                  className="p-1 rounded hover:bg-red-600 transition-colors"
                >
                  <XCircle className="w-4 h-4" />
                </button>
              </div>
              
              <div className="bg-black p-3 rounded h-64 font-mono text-sm overflow-y-auto">
                {console.history.map((line, index) => (
                  <div key={index} className="text-green-400 mb-1">
                    {line}
                  </div>
                ))}
                <div className="text-green-400">
                  <span className="text-white">{console.name}{'>'}</span>
                  <span className="bg-green-400 text-black ml-1 animate-pulse">|</span>
                </div>
              </div>
              
              <div className="mt-2">
                <input
                  placeholder="Tapez votre commande..."
                  className={`w-full px-3 py-2 rounded-lg border ${getThemeClasses('background', 'dashboard')} ${getThemeClasses('text', 'dashboard')} border-gray-600 focus:border-blue-500 focus:outline-none font-mono`}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      const command = e.target.value;
                      if (command.trim()) {
                        const updatedConsoles = consoles.map(c => 
                          c.id === console.id 
                            ? { ...c, history: [...c.history, `${console.name}> ${command}`, 
                                `Output: Command '${command}' executed successfully`] }
                            : c
                        );
                        setConsoles(updatedConsoles);
                        e.target.value = '';
                      }
                    }
                  }}
                />
              </div>
            </div>
          ))}
          {consoles.length === 0 && (
            <div className="col-span-2 text-center py-8">
              <p className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Aucune console active</p>
              <p className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Ouvrez un nœud depuis l'éditeur pour démarrer une console</p>
            </div>
          )}
        </div>
      )}
    </div>
  );

  // Rendu principal
  return (
    <div className="p-3">
      <HeaderControls />
      
      {activeTab === 'projects' && (
        <>
          <SearchAndFilters />
          <StatsCards />
          <ProjectsView />
        </>
      )}
      
      {activeTab === 'editor' && (
        <TopologyEditor />
      )}
      
      {activeTab === 'consoles' && (
        <ConsolesView />
      )}

      {/* Navigation par onglets */}
      <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2">
        <div className={`${getThemeClasses('card', 'dashboard')} p-2 flex space-x-2`}>
          {[
            { key: 'projects', label: 'Projets', icon: Layers },
            { key: 'editor', label: 'Éditeur', icon: Edit, disabled: !selectedProject },
            { key: 'consoles', label: 'Consoles', icon: Terminal, disabled: !selectedProject }
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                disabled={tab.disabled}
                className={`flex items-center px-4 py-2 rounded-lg transition-colors ${
                  activeTab === tab.key
                    ? 'bg-blue-600 text-white'
                    : tab.disabled
                      ? 'opacity-50 cursor-not-allowed'
                      : `${getThemeClasses('hover', 'dashboard')} ${getThemeClasses('text', 'dashboard')}`
                }`}
              >
                <Icon className="w-4 h-4 mr-2" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default GNS3;