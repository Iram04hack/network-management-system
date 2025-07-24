// SimulationMonitoring.jsx - Monitoring en temps réel des simulations GNS3
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  Play, 
  Pause, 
  Square, 
  RefreshCw, 
  Settings, 
  Eye, 
  EyeOff, 
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
  Server, 
  Database, 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Thermometer, 
  Wifi, 
  Globe, 
  Terminal, 
  Shield, 
  Target, 
  Signal, 
  BarChart3, 
  PieChart, 
  LineChart, 
  AlertCircle, 
  Bell, 
  Download, 
  Upload, 
  FileText, 
  Calendar, 
  Users, 
  Building, 
  Layers, 
  Filter, 
  Search,
  Plus,
  Edit,
  Trash2,
  Copy,
  Maximize,
  Minimize,
  Info,
  X
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ComposedChart } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const SimulationMonitoring = ({ isVisible = true, projectId = null }) => {
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
  const [selectedNodes, setSelectedNodes] = useState([]);
  const [timeRange, setTimeRange] = useState('1h');
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [showDetails, setShowDetails] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [simulationData, setSimulationData] = useState({});
  const [nodeMetrics, setNodeMetrics] = useState([]);
  const [networkMetrics, setNetworkMetrics] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const { getThemeClasses } = useTheme();

  // Données mockées des nœuds en cours de simulation
  const mockNodes = [
    {
      id: 'node-1',
      name: 'Router-Core-01',
      type: 'router',
      status: 'started',
      uptime: 7200, // 2 heures
      cpu: 34.5,
      memory: 67.8,
      interfaces: [
        { name: 'GigabitEthernet0/0', status: 'up', rxBytes: 1024000, txBytes: 892000, errors: 0 },
        { name: 'GigabitEthernet0/1', status: 'up', rxBytes: 567000, txBytes: 432000, errors: 2 },
        { name: 'Serial0/0', status: 'down', rxBytes: 0, txBytes: 0, errors: 15 }
      ],
      processes: [
        { name: 'OSPF', status: 'running', cpu: 12.3, memory: 45.6 },
        { name: 'BGP', status: 'running', cpu: 8.7, memory: 23.4 },
        { name: 'SNMP', status: 'running', cpu: 2.1, memory: 8.9 }
      ],
      temperature: 42.5,
      powerConsumption: 65.3,
      lastActivity: '2024-01-15T10:30:00Z'
    },
    {
      id: 'node-2',
      name: 'Switch-Access-01',
      type: 'switch',
      status: 'started',
      uptime: 6800,
      cpu: 18.2,
      memory: 34.5,
      interfaces: [
        { name: 'FastEthernet0/1', status: 'up', rxBytes: 345000, txBytes: 278000, errors: 0 },
        { name: 'FastEthernet0/2', status: 'up', rxBytes: 234000, txBytes: 189000, errors: 1 },
        { name: 'FastEthernet0/3', status: 'down', rxBytes: 0, txBytes: 0, errors: 5 }
      ],
      processes: [
        { name: 'STP', status: 'running', cpu: 5.4, memory: 12.3 },
        { name: 'VLAN', status: 'running', cpu: 3.2, memory: 8.7 }
      ],
      temperature: 38.2,
      powerConsumption: 45.7,
      lastActivity: '2024-01-15T10:29:00Z'
    },
    {
      id: 'node-3',
      name: 'Firewall-Edge-01',
      type: 'firewall',
      status: 'started',
      uptime: 7500,
      cpu: 45.8,
      memory: 78.3,
      interfaces: [
        { name: 'inside', status: 'up', rxBytes: 2048000, txBytes: 1567000, errors: 0 },
        { name: 'outside', status: 'up', rxBytes: 1234000, txBytes: 1890000, errors: 3 },
        { name: 'dmz', status: 'up', rxBytes: 567000, txBytes: 432000, errors: 1 }
      ],
      processes: [
        { name: 'iptables', status: 'running', cpu: 23.5, memory: 45.2 },
        { name: 'snort', status: 'running', cpu: 15.3, memory: 28.7 },
        { name: 'syslog', status: 'running', cpu: 2.8, memory: 6.4 }
      ],
      temperature: 52.1,
      powerConsumption: 89.4,
      lastActivity: '2024-01-15T10:30:00Z'
    },
    {
      id: 'node-4',
      name: 'Server-Web-01',
      type: 'server',
      status: 'stopped',
      uptime: 0,
      cpu: 0,
      memory: 0,
      interfaces: [
        { name: 'eth0', status: 'down', rxBytes: 0, txBytes: 0, errors: 0 }
      ],
      processes: [],
      temperature: 25.0,
      powerConsumption: 0,
      lastActivity: '2024-01-15T09:45:00Z'
    }
  ];

  // Données historiques pour graphiques
  const generateMetricsHistory = () => {
    const hours = timeRange === '1h' ? 12 : timeRange === '24h' ? 24 : 7;
    return Array.from({ length: hours }, (_, i) => ({
      time: timeRange === '7d' ? `J${i + 1}` : `${(new Date().getHours() - hours + i + 1 + 24) % 24}:00`,
      cpu: Math.floor(Math.random() * 60) + 20,
      memory: Math.floor(Math.random() * 40) + 40,
      network: Math.floor(Math.random() * 80) + 10,
      temperature: Math.floor(Math.random() * 20) + 35,
      power: Math.floor(Math.random() * 30) + 50,
      packets: Math.floor(Math.random() * 1000) + 500,
      errors: Math.floor(Math.random() * 10)
    }));
  };

  // Alertes mockées
  const mockAlerts = [
    {
      id: 'alert-1',
      severity: 'high',
      type: 'cpu',
      message: 'CPU élevé sur Firewall-Edge-01 (45.8%)',
      node: 'node-3',
      timestamp: '2024-01-15T10:25:00Z',
      acknowledged: false
    },
    {
      id: 'alert-2',
      severity: 'medium',
      type: 'interface',
      message: 'Interface Serial0/0 down sur Router-Core-01',
      node: 'node-1',
      timestamp: '2024-01-15T10:20:00Z',
      acknowledged: false
    },
    {
      id: 'alert-3',
      severity: 'low',
      type: 'memory',
      message: 'Utilisation mémoire élevée sur Firewall-Edge-01',
      node: 'node-3',
      timestamp: '2024-01-15T10:15:00Z',
      acknowledged: true
    },
    {
      id: 'alert-4',
      severity: 'critical',
      type: 'node',
      message: 'Nœud Server-Web-01 arrêté de manière inattendue',
      node: 'node-4',
      timestamp: '2024-01-15T09:45:00Z',
      acknowledged: false
    }
  ];

  // Statistiques globales
  const simulationStats = {
    totalNodes: 4,
    runningNodes: 3,
    stoppedNodes: 1,
    totalInterfaces: 12,
    activeInterfaces: 8,
    downInterfaces: 4,
    totalAlerts: 4,
    criticalAlerts: 1,
    acknowledgedAlerts: 1,
    avgCpu: 32.8,
    avgMemory: 60.2,
    avgTemperature: 39.5,
    totalPowerConsumption: 200.4,
    networkThroughput: 15.6, // Mbps
    packetLoss: 0.02
  };

  // Initialisation
  useEffect(() => {
    setNodeMetrics(mockNodes);
    setAlerts(mockAlerts);
    setSimulationData(simulationStats);
  }, []);

  // Simulation temps réel
  useEffect(() => {
    if (!isRealTimeEnabled || !autoRefresh) return;

    const interval = setInterval(() => {
      setNodeMetrics(prev => prev.map(node => ({
        ...node,
        cpu: node.status === 'started' ? Math.max(0, Math.min(100, node.cpu + (Math.random() - 0.5) * 10)) : 0,
        memory: node.status === 'started' ? Math.max(0, Math.min(100, node.memory + (Math.random() - 0.5) * 8)) : 0,
        temperature: node.status === 'started' ? Math.max(20, Math.min(80, node.temperature + (Math.random() - 0.5) * 5)) : 25,
        powerConsumption: node.status === 'started' ? Math.max(0, Math.min(150, node.powerConsumption + (Math.random() - 0.5) * 15)) : 0,
        lastActivity: new Date().toISOString()
      })));

      setSimulationData(prev => ({
        ...prev,
        avgCpu: Math.max(0, Math.min(100, prev.avgCpu + (Math.random() - 0.5) * 8)),
        avgMemory: Math.max(0, Math.min(100, prev.avgMemory + (Math.random() - 0.5) * 6)),
        networkThroughput: Math.max(0, Math.min(100, prev.networkThroughput + (Math.random() - 0.5) * 5)),
        packetLoss: Math.max(0, Math.min(5, prev.packetLoss + (Math.random() - 0.5) * 0.1))
      }));
    }, refreshInterval * 1000);

    return () => clearInterval(interval);
  }, [isRealTimeEnabled, autoRefresh, refreshInterval]);

  // Fonctions utilitaires
  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'started': return '#10B981';
      case 'stopped': return '#EF4444';
      case 'suspended': return '#F59E0B';
      default: return '#6B7280';
    }
  };

  const getAlertColor = (severity) => {
    switch (severity) {
      case 'critical': return '#DC2626';
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return '#6B7280';
    }
  };

  const getNodeIcon = (type) => {
    switch (type) {
      case 'router': return Router;
      case 'switch': return Network;
      case 'firewall': return Shield;
      case 'server': return Server;
      case 'host': return Monitor;
      default: return Network;
    }
  };

  // Actions
  const handleNodeAction = (nodeId, action) => {
    setNodeMetrics(prev => prev.map(node => 
      node.id === nodeId 
        ? { 
            ...node, 
            status: action === 'start' ? 'started' : 
                   action === 'stop' ? 'stopped' : 
                   action === 'suspend' ? 'suspended' : node.status,
            uptime: action === 'start' ? 0 : action === 'stop' ? 0 : node.uptime
          }
        : node
    ));
  };

  const acknowledgeAlert = (alertId) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, acknowledged: true } : alert
    ));
  };

  const dismissAlert = (alertId) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  };

  // Composant des métriques principales
  const OverviewMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Nœuds Actifs</p>
            <p className="text-2xl font-bold text-green-400">{simulationData.runningNodes}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              / {simulationData.totalNodes} total
            </p>
          </div>
          <Activity className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>CPU Moyen</p>
            <p className="text-2xl font-bold text-blue-400">{simulationData.avgCpu?.toFixed(1)}%</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              Toutes simulations
            </p>
          </div>
          <Cpu className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Débit Réseau</p>
            <p className="text-2xl font-bold text-purple-400">{simulationData.networkThroughput?.toFixed(1)}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Mbps</p>
          </div>
          <Network className="w-8 h-8 text-purple-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Alertes Actives</p>
            <p className="text-2xl font-bold text-red-400">{alerts.filter(a => !a.acknowledged).length}</p>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
              / {alerts.length} total
            </p>
          </div>
          <AlertTriangle className="w-8 h-8 text-red-400" />
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
              Intervalle:
            </span>
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
              className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value={1}>1 seconde</option>
              <option value={5}>5 secondes</option>
              <option value={10}>10 secondes</option>
              <option value={30}>30 secondes</option>
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

  // Composant des nœuds de simulation
  const NodesTable = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden mb-6`}>
      <div className="p-4 border-b border-gray-700">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Nœuds de Simulation
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Nœud</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Type</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Uptime</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">CPU</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Mémoire</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Température</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {nodeMetrics.map(node => {
              const NodeIcon = getNodeIcon(node.type);
              
              return (
                <tr key={node.id} className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-3">
                      <NodeIcon className="w-5 h-5" style={{ color: getStatusColor(node.status) }} />
                      <div>
                        <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                          {node.name}
                        </div>
                        <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                          {node.id}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('textSecondary', 'dashboard')} text-sm capitalize`}>
                    {node.type}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getStatusColor(node.status) }}
                      />
                      <span className={`${getThemeClasses('text', 'dashboard')} text-sm capitalize`}>
                        {node.status}
                      </span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} text-sm`}>
                    {node.status === 'started' ? formatUptime(node.uptime) : '-'}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-700 rounded-full h-2">
                        <div 
                          className="h-2 rounded-full"
                          style={{ 
                            width: `${node.cpu}%`,
                            backgroundColor: node.cpu > 80 ? '#EF4444' : node.cpu > 60 ? '#F59E0B' : '#10B981'
                          }}
                        />
                      </div>
                      <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                        {node.cpu.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <div className="w-16 bg-gray-700 rounded-full h-2">
                        <div 
                          className="h-2 rounded-full"
                          style={{ 
                            width: `${node.memory}%`,
                            backgroundColor: node.memory > 80 ? '#EF4444' : node.memory > 60 ? '#F59E0B' : '#10B981'
                          }}
                        />
                      </div>
                      <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                        {node.memory.toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} text-sm`}>
                    <div className="flex items-center space-x-1">
                      <Thermometer className="w-4 h-4 text-orange-400" />
                      <span>{node.temperature.toFixed(1)}°C</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-1">
                      {node.status === 'started' ? (
                        <>
                          <button
                            onClick={() => handleNodeAction(node.id, 'suspend')}
                            className="p-1 rounded hover:bg-gray-700 transition-colors"
                            title="Suspendre"
                          >
                            <Pause className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleNodeAction(node.id, 'stop')}
                            className="p-1 rounded hover:bg-gray-700 transition-colors"
                            title="Arrêter"
                          >
                            <Square className="w-4 h-4" />
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => handleNodeAction(node.id, 'start')}
                          className="p-1 rounded hover:bg-gray-700 transition-colors"
                          title="Démarrer"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => console.log('Console:', node.id)}
                        className="p-1 rounded hover:bg-gray-700 transition-colors"
                        title="Console"
                      >
                        <Terminal className="w-4 h-4" />
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
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Utilisation des Ressources
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={generateMetricsHistory()}>
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
                fill="#3B82F6" 
                fillOpacity={0.3}
                stroke="#3B82F6"
              />
              <Line 
                type="monotone" 
                dataKey="memory" 
                stroke="#10B981" 
                strokeWidth={2}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Trafic Réseau
        </h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={generateMetricsHistory()}>
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
                dataKey="packets" 
                stackId="1" 
                stroke="#8B5CF6" 
                fill="#8B5CF6" 
                fillOpacity={0.6}
              />
              <Area 
                type="monotone" 
                dataKey="errors" 
                stackId="2" 
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

  // Composant des alertes
  const AlertsPanel = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Alertes de Simulation
        </h3>
        <div className="flex items-center space-x-2">
          <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
            {alerts.filter(a => !a.acknowledged).length} non acquittées
          </span>
        </div>
      </div>
      
      <div className="space-y-3 max-h-64 overflow-y-auto">
        {alerts.map(alert => (
          <div 
            key={alert.id} 
            className={`flex items-center justify-between p-3 rounded border-l-4 ${
              alert.acknowledged ? 'bg-gray-700/30' : 'bg-gray-700/50'
            }`}
            style={{ borderLeftColor: getAlertColor(alert.severity) }}
          >
            <div className="flex items-center space-x-3">
              <AlertTriangle 
                className="w-5 h-5" 
                style={{ color: getAlertColor(alert.severity) }}
              />
              <div>
                <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                  {alert.message}
                </div>
                <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                  {new Date(alert.timestamp).toLocaleString()} - {alert.type}
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {!alert.acknowledged && (
                <button
                  onClick={() => acknowledgeAlert(alert.id)}
                  className="p-1 text-green-400 hover:bg-gray-700 rounded transition-colors"
                  title="Acquitter"
                >
                  <CheckCircle className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => dismissAlert(alert.id)}
                className="p-1 text-red-400 hover:bg-gray-700 rounded transition-colors"
                title="Supprimer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
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
            Monitoring des Simulations
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Surveillance en temps réel des simulations GNS3
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

      <OverviewMetrics />
      <MonitoringControls />
      <NodesTable />
      <PerformanceCharts />
      <AlertsPanel />
    </div>
  );
};

export default SimulationMonitoring;