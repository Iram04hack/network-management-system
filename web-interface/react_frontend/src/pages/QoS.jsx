import React, { useState, useEffect } from 'react';
import { 
  Settings, 
  Activity, 
  Network, 
  TrendingUp, 
  Shield, 
  Plus, 
  Edit, 
  Trash2, 
  Play, 
  Pause,
  Save,
  RefreshCw
} from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useTheme } from '../contexts/ThemeContext';

const QoS = () => {
  const { getThemeClasses } = useTheme();
  
  // États locaux avec données mockées
  const [activeTab, setActiveTab] = useState('policies');
  const [isLoading, setIsLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  // Données QoS mockées
  const [qosPolicies] = useState([
    {
      id: 'policy-1',
      name: 'Politique Voix',
      type: 'Voice',
      priority: 'High',
      bandwidth: '2 Mbps',
      interface: 'eth0',
      status: 'active',
      created: '2024-01-15T10:30:00Z',
      rules: 3,
      traffic_matched: '12.5 GB',
      packets_dropped: 156
    },
    {
      id: 'policy-2', 
      name: 'Politique Vidéo',
      type: 'Video',
      priority: 'Medium',
      bandwidth: '5 Mbps',
      interface: 'eth0',
      status: 'active',
      created: '2024-01-15T11:00:00Z',
      rules: 2,
      traffic_matched: '45.2 GB',
      packets_dropped: 89
    },
    {
      id: 'policy-3',
      name: 'Politique Données',
      type: 'Data',
      priority: 'Low',
      bandwidth: 'Best Effort',
      interface: 'eth1',
      status: 'inactive',
      created: '2024-01-15T14:15:00Z',
      rules: 1,
      traffic_matched: '128.7 GB',
      packets_dropped: 2341
    }
  ]);

  const [qosStats] = useState({
    totalBandwidth: '100 Mbps',
    utilizedBandwidth: '67.3 Mbps',
    availableBandwidth: '32.7 Mbps',
    totalPolicies: 3,
    activePolicies: 2,
    totalRules: 6,
    totalInterfaces: 3,
    configuredInterfaces: 2
  });

  // Données pour les graphiques
  const [trafficData] = useState([
    { time: '00:00', voice: 1.2, video: 3.8, data: 8.5 },
    { time: '04:00', voice: 0.8, video: 2.1, data: 12.3 },
    { time: '08:00', voice: 2.1, video: 4.9, data: 18.7 },
    { time: '12:00', voice: 1.9, video: 5.2, data: 22.1 },
    { time: '16:00', voice: 1.7, video: 4.1, data: 19.8 },
    { time: '20:00', voice: 1.3, video: 3.2, data: 15.6 }
  ]);

  const [bandwidthDistribution] = useState([
    { name: 'Voix', value: 15, color: '#3B82F6' },
    { name: 'Vidéo', value: 35, color: '#10B981' },
    { name: 'Données', value: 50, color: '#F59E0B' }
  ]);

  // Configuration des onglets
  const tabs = [
    {
      id: 'policies',
      label: 'Politiques QoS',
      icon: Shield,
      description: 'Gestion des politiques de qualité de service'
    },
    {
      id: 'traffic',
      label: 'Classes Trafic',
      icon: Network,
      description: 'Configuration des classes de trafic'
    },
    {
      id: 'monitoring',
      label: 'Surveillance',
      icon: Activity,
      description: 'Surveillance temps réel du trafic'
    },
    {
      id: 'statistics',
      label: 'Statistiques',
      icon: TrendingUp,
      description: 'Statistiques et analyses'
    }
  ];

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'inactive': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'High': return 'text-red-400';
      case 'Medium': return 'text-yellow-400';
      case 'Low': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  // Header avec statistiques
  const Header = () => (
    <div className="mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className={`${getThemeClasses('text', 'dashboard')} text-3xl font-bold`}>
            Quality of Service (QoS)
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Gestion de la qualité de service réseau (données simulées)
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`flex items-center space-x-2 px-3 py-2 rounded transition-colors ${
              autoRefresh 
                ? 'bg-green-600 hover:bg-green-700 text-white' 
                : 'border border-gray-600 hover:border-gray-500'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span className="text-sm">Auto-refresh</span>
          </button>
          
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <RefreshCw className="w-4 h-4" />
            <span className="text-sm">Actualiser</span>
          </button>
        </div>
      </div>

      {/* Statistiques QoS */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Network className="w-8 h-8 text-blue-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Bande Passante</p>
              <p className="text-lg font-bold text-blue-400">{qosStats.utilizedBandwidth}</p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                sur {qosStats.totalBandwidth}
              </p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Shield className="w-8 h-8 text-green-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Politiques</p>
              <p className="text-lg font-bold text-green-400">
                {qosStats.activePolicies}/{qosStats.totalPolicies}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Actives</p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <Settings className="w-8 h-8 text-purple-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Interfaces</p>
              <p className="text-lg font-bold text-purple-400">
                {qosStats.configuredInterfaces}/{qosStats.totalInterfaces}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Configurées</p>
            </div>
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center space-x-3">
            <TrendingUp className="w-8 h-8 text-orange-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Règles Totales</p>
              <p className="text-lg font-bold text-orange-400">{qosStats.totalRules}</p>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>Configurées</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Navigation par onglets
  const TabNavigation = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} mb-6`}>
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex space-x-1">
          {tabs.map(tab => {
            const TabIcon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
                  activeTab === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <TabIcon className="w-4 h-4" />
                <span className="font-medium">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>
      
      <div className="p-4">
        <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
          {tabs.find(tab => tab.id === activeTab)?.description}
        </p>
      </div>
    </div>
  );

  // Contenu des onglets
  const renderTabContent = () => {
    switch (activeTab) {
      case 'policies':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
                Politiques QoS Configurées
              </h2>
              <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
                <Plus className="w-4 h-4" />
                <span>Nouvelle Politique</span>
              </button>
            </div>
            
            <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden`}>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-700/50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Politique
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Priorité
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Bande Passante
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Statut
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {qosPolicies.map(policy => (
                      <tr key={policy.id} className="hover:bg-gray-700/30">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div>
                            <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                              {policy.name}
                            </div>
                            <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                              Interface: {policy.interface}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {policy.type}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-medium ${getPriorityColor(policy.priority)}`}>
                            {policy.priority}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          {policy.bandwidth}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`text-sm font-medium ${getStatusColor(policy.status)}`}>
                            {policy.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                          <button className="text-blue-400 hover:text-blue-300">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="text-green-400 hover:text-green-300">
                            {policy.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                          </button>
                          <button className="text-red-400 hover:text-red-300">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        );

      case 'traffic':
        return (
          <div className={`${getThemeClasses('card', 'dashboard')} p-8 text-center`}>
            <Network className="w-16 h-16 text-blue-400 mx-auto mb-4" />
            <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-2`}>
              Classes de Trafic
            </h3>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
              Configuration des classes de trafic en développement
            </p>
          </div>
        );

      case 'monitoring':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Trafic par Type
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trafficData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="voice" stroke="#3B82F6" strokeWidth={2} name="Voix" />
                    <Line type="monotone" dataKey="video" stroke="#10B981" strokeWidth={2} name="Vidéo" />
                    <Line type="monotone" dataKey="data" stroke="#F59E0B" strokeWidth={2} name="Données" />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
                  Distribution Bande Passante
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={bandwidthDistribution}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({name, value}) => `${name}: ${value}%`}
                    >
                      {bandwidthDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        );

      case 'statistics':
        return (
          <div className={`${getThemeClasses('card', 'dashboard')} p-8 text-center`}>
            <TrendingUp className="w-16 h-16 text-purple-400 mx-auto mb-4" />
            <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-2`}>
              Statistiques Avancées
            </h3>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
              Module de statistiques détaillées en développement
            </p>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="p-6 space-y-6">
      <Header />
      <TabNavigation />
      {renderTabContent()}
    </div>
  );
};

export default QoS;