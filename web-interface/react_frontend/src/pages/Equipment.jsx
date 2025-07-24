import React, { useState, useEffect, useCallback } from 'react';
import { Wifi, Network, Calendar, Activity, RefreshCw, Search, Filter, Settings, TrendingUp, AlertTriangle, CheckCircle, XCircle, Eye, Edit, Play, Pause, MoreVertical } from 'lucide-react';

// Import des hooks backend pour les équipements AMÉLIORÉS
import { useApiViews } from '../hooks/useApiViews';
import { useApiClients } from '../hooks/useApiClients';
import { useTheme } from '../contexts/ThemeContext';

const Equipment = () => {
  const [selectedEquipment, setSelectedEquipment] = useState(null);
  const [equipments, setEquipments] = useState([]);
  const [filteredEquipments, setFilteredEquipments] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'grid' | 'topology'
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [showActions, setShowActions] = useState(null);

  // Hook pour le thème
  const { getThemeClasses, getThemeColor } = useTheme();

  // Hook backend pour les données d'équipements ENRICHI
  const { 
    searchResults,
    dashboardOverview,
    networkOverview,
    devices,
    topologyData,
    loading: apiViewsLoading,
    error: apiViewsError,
    fetchDashboardOverview,
    fetchNetworkOverview,
    fetchDevices,
    getTopologyData,
    startTopologyDiscovery,
    performGlobalSearch,
    refreshAllData,
    clearError,
    getDevicesByType,
    getOnlineDevices,
    getProblematicDevices
  } = useApiViews();

  // Hook pour les clients API (SNMP, Prometheus, etc.) ENRICHI
  const {
    clients: apiClients,
    currentClient,
    health: clientsHealth,
    loading: clientsLoading,
    error: clientsError,
    fetchClients,
    testClient,
    fetchClientsHealth,
    getActiveClients,
    getUnhealthyClients,
    updateClientConfig
  } = useApiClients();

  // Chargement initial des données AMÉLIORÉ
  useEffect(() => {
    const loadEquipmentData = async () => {
      try {
        await Promise.allSettled([
          fetchDashboardOverview(),
          fetchNetworkOverview(),
          fetchDevices(),
          fetchClients(),
          fetchClientsHealth(),
          performGlobalSearch('equipment')
        ]);
      } catch (error) {
        console.error('Erreur lors du chargement des équipements:', error);
      }
    };

    loadEquipmentData();
  }, []);

  // Auto-refresh NOUVEAU
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(async () => {
      try {
        await Promise.allSettled([
          refreshAllData(),
          fetchClientsHealth(),
          fetchDevices()
        ]);
      } catch (error) {
        console.error('Erreur lors du refresh automatique:', error);
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Fonctions de gestion NOUVELLES
  const handleRefreshData = useCallback(async () => {
    try {
      await Promise.allSettled([
        refreshAllData(),
        fetchClientsHealth(),
        fetchDevices()
      ]);
    } catch (error) {
      console.error('Erreur lors du refresh manuel:', error);
    }
  }, []);

  const handleSearchChange = useCallback((e) => {
    setSearchQuery(e.target.value);
  }, []);

  const handleFilterTypeChange = useCallback((type) => {
    setFilterType(type);
  }, []);

  const handleFilterStatusChange = useCallback((status) => {
    setFilterStatus(status);
  }, []);

  const handleEquipmentAction = useCallback(async (equipmentId, action) => {
    // Simulation d'actions sur les équipements
    console.log(`Action ${action} sur équipement ${equipmentId}`);
    setShowActions(null);
  }, []);

  // Données dynamiques des équipements ENRICHIES
  useEffect(() => {
    const backendEquipments = devices || networkOverview?.devices || dashboardOverview?.devices || searchResults?.devices || [];
    
    const formattedEquipments = backendEquipments.length > 0 
      ? backendEquipments.map((device, index) => ({
          id: device.id || `device-${index}`,
          name: device.name || device.hostname || `Device-${index}`,
          ip: device.ip_address || device.ip || '192.168.1.1',
          type: device.device_type || device.type || 'Unknown',
          status: device.status === 'online' || device.is_online ? 'Actif' : 'Inactif',
          addedDate: device.created_at ? new Date(device.created_at).toLocaleDateString() : 'Aujourd\'hui',
          interfaces: device.interfaces || [
            { name: 'eth0', status: 'Actif', speed: '1000Mbps' },
            { name: 'eth1', status: 'Actif', speed: '1000Mbps' }
          ],
          cpu: device.cpu_usage || Math.floor(Math.random() * 60),
          memory: device.memory_usage || Math.floor(Math.random() * 80),
          disk: device.disk_usage || Math.floor(Math.random() * 40),
          uptime: device.uptime || '99.8%',
          lastSeen: device.last_seen || device.updated_at || new Date().toISOString(),
          location: device.location || 'Datacenter 1',
          vendor: device.vendor || 'Unknown',
          model: device.model || 'Unknown',
          serialNumber: device.serial_number || 'N/A',
          firmwareVersion: device.firmware_version || 'N/A',
          connections: device.connections || 0,
          hasAlerts: Math.random() > 0.7 // Simulation d'alertes
        }))
      : [
          // Fallback data ENRICHIE
          { 
            id: '1', 
            name: 'Routeur-Principal', 
            ip: '192.168.1.1', 
            type: 'Router', 
            status: 'Actif', 
            addedDate: 'Aujourd\'hui',
            interfaces: [
              { name: 'GigabitEthernet0/0', status: 'Actif', speed: '1000Mbps' },
              { name: 'GigabitEthernet0/1', status: 'Actif', speed: '1000Mbps' },
              { name: 'Serial0/0/0', status: 'Inactif', speed: 'T1' }
            ],
            cpu: 15, memory: 45, disk: 23, uptime: '99.8%',
            lastSeen: new Date().toISOString(),
            location: 'Datacenter 1', vendor: 'Cisco', model: 'ISR4331',
            serialNumber: 'FDO2345G678', firmwareVersion: '16.09.04',
            connections: 5, hasAlerts: false
          },
          { 
            id: '2', 
            name: 'Switch-Core', 
            ip: '192.168.1.2', 
            type: 'Switch', 
            status: 'Actif', 
            addedDate: 'Aujourd\'hui',
            interfaces: [
              { name: 'GigabitEthernet1/0/1', status: 'Actif', speed: '1000Mbps' },
              { name: 'GigabitEthernet1/0/2', status: 'Actif', speed: '1000Mbps' }
            ],
            cpu: 8, memory: 23, disk: 15, uptime: '99.9%',
            lastSeen: new Date().toISOString(),
            location: 'Datacenter 1', vendor: 'Cisco', model: 'WS-C2960X',
            serialNumber: 'FOC1234B567', firmwareVersion: '15.2(7)E3',
            connections: 12, hasAlerts: false
          },
          { 
            id: '3', 
            name: 'Firewall-DMZ', 
            ip: '192.168.1.100', 
            type: 'Firewall', 
            status: 'Inactif', 
            addedDate: 'Hier',
            interfaces: [
              { name: 'outside', status: 'Inactif', speed: '1000Mbps' },
              { name: 'inside', status: 'Inactif', speed: '1000Mbps' }
            ],
            cpu: 0, memory: 0, disk: 0, uptime: '98.2%',
            lastSeen: new Date(Date.now() - 3600000).toISOString(),
            location: 'DMZ', vendor: 'FortiGate', model: 'FortiGate-60F',
            serialNumber: 'FG60F1234567890', firmwareVersion: '7.0.8',
            connections: 0, hasAlerts: true
          }
        ];
    
    setEquipments(formattedEquipments);
    if (!selectedEquipment && formattedEquipments.length > 0) {
      setSelectedEquipment(formattedEquipments[0]);
    }
  }, [devices, networkOverview, dashboardOverview, searchResults, selectedEquipment]);

  // Filtrage et recherche AMÉLIORÉS
  useEffect(() => {
    let filtered = [...equipments];

    // Recherche par nom, IP, type, location
    if (searchQuery) {
      filtered = filtered.filter(equipment => 
        equipment.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        equipment.ip.includes(searchQuery) ||
        equipment.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        equipment.location?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        equipment.vendor?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filtre par type
    if (filterType !== 'all') {
      filtered = filtered.filter(equipment => 
        equipment.type.toLowerCase().includes(filterType.toLowerCase())
      );
    }

    // Filtre par statut
    if (filterStatus !== 'all') {
      filtered = filtered.filter(equipment => 
        filterStatus === 'active' ? equipment.status === 'Actif' : equipment.status === 'Inactif'
      );
    }

    setFilteredEquipments(filtered);
  }, [equipments, searchQuery, filterType, filterStatus]);

  // Événements mockés
  const events = [
    { time: '14:32', type: 'Intrusion détectée', color: 'red' },
    { time: 'Switch-1', type: 'Erreur d\'interface', color: 'yellow' },
    { time: '17/04/2024', type: 'Appareil ajouté', color: 'blue' },
    { time: '16/04/2024, 23', type: 'Redémarrage', color: 'blue' }
  ];

  const historyEvents = [
    { time: '16/04/2024, 23:23', type: 'Intrusion détectée', color: 'red' },
    { time: '16/04/2024, 23:23', type: 'Erreur d\'interface', color: 'yellow' }
  ];

  // Statistiques calculées
  const stats = {
    total: equipments.length,
    active: equipments.filter(eq => eq.status === 'Actif').length,
    inactive: equipments.filter(eq => eq.status === 'Inactif').length,
    withAlerts: equipments.filter(eq => eq.hasAlerts).length,
    avgCpu: equipments.length > 0 ? Math.round(equipments.reduce((sum, eq) => sum + (eq.cpu || 0), 0) / equipments.length) : 0,
    avgMemory: equipments.length > 0 ? Math.round(equipments.reduce((sum, eq) => sum + (eq.memory || 0), 0) / equipments.length) : 0
  };

  const uniqueTypes = [...new Set(equipments.map(eq => eq.type))];
  
  // Composants NOUVEAUX
  const HeaderControls = () => (
    <div className="mb-3">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
        <div>
          <h1 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Gestion des Équipements
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            {stats.total} équipements · {stats.active} actifs · {stats.withAlerts} avec alertes
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={handleRefreshData}
            disabled={Object.values(apiViewsLoading).some(l => l)}
            className={`p-2 rounded-lg ${getThemeClasses('hover', 'dashboard')} transition-colors ${
              Object.values(apiViewsLoading).some(l => l) ? 'opacity-50 cursor-not-allowed' : ''
            }`}
            title="Actualiser les données"
          >
            <RefreshCw className={`w-5 h-5 ${Object.values(apiViewsLoading).some(l => l) ? 'animate-spin' : ''}`} />
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
          placeholder="Rechercher par nom, IP, type, emplacement..."
          value={searchQuery}
          onChange={handleSearchChange}
          className="w-full pl-8 pr-3 py-1.5 text-sm bg-gray-800 text-white border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
        />
      </div>
      <select
        value={filterType}
        onChange={(e) => handleFilterTypeChange(e.target.value)}
        className="px-2 py-1.5 text-sm bg-gray-800 text-white border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les types</option>
        {uniqueTypes.map(type => (
          <option key={type} value={type}>{type}</option>
        ))}
      </select>
      <select
        value={filterStatus}
        onChange={(e) => handleFilterStatusChange(e.target.value)}
        className="px-2 py-1.5 text-sm bg-gray-800 text-white border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les statuts</option>
        <option value="active">Actifs</option>
        <option value="inactive">Inactifs</option>
      </select>
      <div className="flex border border-gray-600 rounded overflow-hidden">
        {['table', 'grid'].map((mode) => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            className={`px-3 py-1.5 text-sm ${
              viewMode === mode
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            {mode === 'table' ? 'Tableau' : 'Grille'}
          </button>
        ))}
      </div>
    </div>
  );

  const StatsCards = () => (
    <div className="grid grid-cols-2 lg:grid-cols-6 gap-3 mb-4">
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total</p>
            <p className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>{stats.total}</p>
          </div>
          <Network className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Actifs</p>
            <p className="text-2xl font-bold text-green-400">{stats.active}</p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Inactifs</p>
            <p className="text-2xl font-bold text-red-400">{stats.inactive}</p>
          </div>
          <XCircle className="w-8 h-8 text-red-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Alertes</p>
            <p className="text-2xl font-bold text-yellow-400">{stats.withAlerts}</p>
          </div>
          <AlertTriangle className="w-8 h-8 text-yellow-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>CPU Moy</p>
            <p className={`text-2xl font-bold ${stats.avgCpu > 70 ? 'text-red-400' : stats.avgCpu > 50 ? 'text-yellow-400' : 'text-green-400'}`}>
              {stats.avgCpu}%
            </p>
          </div>
          <Activity className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>RAM Moy</p>
            <p className={`text-2xl font-bold ${stats.avgMemory > 80 ? 'text-red-400' : stats.avgMemory > 60 ? 'text-yellow-400' : 'text-green-400'}`}>
              {stats.avgMemory}%
            </p>
          </div>
          <TrendingUp className="w-8 h-8 text-purple-400" />
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-3">
      <HeaderControls />
      <SearchAndFilters />
      <StatsCards />
      
      {/* Vue principale des équipements */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-3">
        {/* Liste/Grille des équipements */}
        <div className="xl:col-span-3">
          {viewMode === 'table' ? (
            // Vue Tableau AMÉLIORÉE
            <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden`}>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className={`${getThemeClasses('background', 'dashboard')} border-b border-gray-600`}>
                    <tr>
                      <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Équipement</th>
                      <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Réseau</th>
                      <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Performance</th>
                      <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Statut</th>
                      <th className={`text-left py-0.5 px-2 ${getThemeClasses('textSecondary', 'dashboard')} font-medium text-xs`}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredEquipments.map((equipment) => (
                      <tr 
                        key={equipment.id} 
                        className={`border-b border-gray-600/50 ${getThemeClasses('hover', 'dashboard')} transition-all cursor-pointer ${
                          selectedEquipment?.id === equipment.id ? 'bg-blue-900/20 border-blue-500/50' : ''
                        }`}
                        onClick={() => setSelectedEquipment(equipment)}
                      >
                        <td className="py-0.5 px-2">
                          <div className="flex items-center space-x-2">
                            {equipment.hasAlerts && (
                              <span className="w-1.5 h-1.5 bg-red-400 rounded-full"></span>
                            )}
                            <div>
                              <div className={`${getThemeClasses('text', 'dashboard')} font-medium text-sm`}>{equipment.name}</div>
                              <div className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                                {equipment.vendor} {equipment.model}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="py-0.5 px-2">
                          <div>
                            <div className={`${getThemeClasses('text', 'dashboard')} font-mono text-sm`}>{equipment.ip}</div>
                            <div className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>{equipment.location}</div>
                          </div>
                        </td>
                        <td className="py-0.5 px-2">
                          <div className="space-y-1">
                            <div className="flex items-center justify-between text-xs">
                              <span>CPU</span>
                              <span className={`${(equipment.cpu || 0) > 80 ? 'text-red-400' : (equipment.cpu || 0) > 60 ? 'text-yellow-400' : 'text-green-400'}`}>
                                {equipment.cpu || 0}%
                              </span>
                            </div>
                            <div className="w-full bg-gray-700 rounded-full h-0.5">
                              <div 
                                className={`h-0.5 rounded-full transition-all duration-300 ${
                                  (equipment.cpu || 0) > 80 ? 'bg-red-400' : 
                                  (equipment.cpu || 0) > 60 ? 'bg-yellow-400' : 'bg-green-400'
                                }`}
                                style={{ width: `${equipment.cpu || 0}%` }}
                              />
                            </div>
                          </div>
                        </td>
                        <td className="py-0.5 px-2">
                          <span className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded ${
                            equipment.status === 'Actif' 
                              ? 'bg-green-900/30 text-green-400' 
                              : 'bg-red-900/30 text-red-400'
                          }`}>
                            {equipment.status === 'Actif' ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                            {equipment.status}
                          </span>
                        </td>
                        <td className="py-0.5 px-2">
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedEquipment(equipment);
                              }}
                              className={`p-1 rounded ${getThemeClasses('hover', 'dashboard')} transition-colors`}
                              title="Voir détails"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEquipmentAction(equipment.id, 'edit');
                              }}
                              className={`p-1 rounded ${getThemeClasses('hover', 'dashboard')} transition-colors`}
                              title="Modifier"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setShowActions(showActions === equipment.id ? null : equipment.id);
                              }}
                              className={`p-1 rounded ${getThemeClasses('hover', 'dashboard')} transition-colors`}
                              title="Plus d'actions"
                            >
                              <MoreVertical className="w-4 h-4" />
                            </button>
                          </div>
                          
                          {/* Menu d'actions */}
                          {showActions === equipment.id && (
                            <div className="absolute right-6 mt-2 w-48 bg-gray-800 rounded-lg shadow-lg border border-gray-600 z-10">
                              <div className="py-2">
                                <button
                                  onClick={() => handleEquipmentAction(equipment.id, equipment.status === 'Actif' ? 'stop' : 'start')}
                                  className="w-full text-left px-4 py-2 text-sm hover:bg-gray-700 transition-colors flex items-center"
                                >
                                  {equipment.status === 'Actif' ? (
                                    <>
                                      <Pause className="w-4 h-4 mr-2" />
                                      Arrêter
                                    </>
                                  ) : (
                                    <>
                                      <Play className="w-4 h-4 mr-2" />
                                      Démarrer
                                    </>
                                  )}
                                </button>
                                <button
                                  onClick={() => handleEquipmentAction(equipment.id, 'restart')}
                                  className="w-full text-left px-4 py-2 text-sm hover:bg-gray-700 transition-colors flex items-center"
                                >
                                  <RefreshCw className="w-4 h-4 mr-2" />
                                  Redémarrer
                                </button>
                                <button
                                  onClick={() => handleEquipmentAction(equipment.id, 'configure')}
                                  className="w-full text-left px-4 py-2 text-sm hover:bg-gray-700 transition-colors flex items-center"
                                >
                                  <Settings className="w-4 h-4 mr-2" />
                                  Configurer
                                </button>
                              </div>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            // Vue Grille NOUVELLE
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredEquipments.map((equipment) => (
                <div
                  key={equipment.id}
                  className={`${getThemeClasses('card', 'dashboard')} p-3 cursor-pointer transition-all hover:scale-105 ${
                    selectedEquipment?.id === equipment.id ? 'ring-2 ring-blue-500' : ''
                  }`}
                  onClick={() => setSelectedEquipment(equipment)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      {equipment.hasAlerts && (
                        <span className="w-2 h-2 bg-red-400 rounded-full animate-pulse"></span>
                      )}
                      <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>{equipment.name}</h3>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      equipment.status === 'Actif' 
                        ? 'bg-green-900/30 text-green-400' 
                        : 'bg-red-900/30 text-red-400'
                    }`}>
                      {equipment.status}
                    </span>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>IP:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')} font-mono`}>{equipment.ip}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Type:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{equipment.type}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Uptime:</span>
                      <span className={`${getThemeClasses('text', 'dashboard')}`}>{equipment.uptime}</span>
                    </div>
                  </div>
                  
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-xs">
                      <span>CPU</span>
                      <span className={`${(equipment.cpu || 0) > 80 ? 'text-red-400' : (equipment.cpu || 0) > 60 ? 'text-yellow-400' : 'text-green-400'}`}>
                        {equipment.cpu || 0}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-1">
                      <div 
                        className={`h-1 rounded-full transition-all duration-300 ${
                          (equipment.cpu || 0) > 80 ? 'bg-red-400' : 
                          (equipment.cpu || 0) > 60 ? 'bg-yellow-400' : 'bg-green-400'
                        }`}
                        style={{ width: `${equipment.cpu || 0}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Panneau de détail */}
        <div>
          {selectedEquipment && (
            <div>
              <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold mb-3`}>{selectedEquipment.name}</h2>
              <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
                <div className="mb-3">
                  <p className={`${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>{selectedEquipment.ip}</p>
                  
                  {/* Interfaces */}
                  {selectedEquipment.interfaces && (
                    <div className="space-y-3 mb-3">
                      {selectedEquipment.interfaces.map((intf, index) => (
                        <div key={index} className="flex items-center justify-between">
                          <span className={`${getThemeClasses('text', 'dashboard')}`}>{intf.name}</span>
                          <span className={`px-3 py-1 text-sm font-medium rounded-full ${
                            intf.status === 'Actif' 
                              ? 'bg-green-900/30 text-green-400' 
                              : 'bg-red-900/30 text-red-400'
                          }`}>
                            {intf.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Statistiques détaillées */}
                  <div className="space-y-2 mb-3">
                    <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>Performance</h3>
                    
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>CPU</span>
                          <span className={`text-sm font-medium ${(selectedEquipment.cpu || 0) > 80 ? 'text-red-400' : (selectedEquipment.cpu || 0) > 60 ? 'text-yellow-400' : 'text-green-400'}`}>
                            {selectedEquipment.cpu || 0}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-300 ${
                              (selectedEquipment.cpu || 0) > 80 ? 'bg-red-400' : 
                              (selectedEquipment.cpu || 0) > 60 ? 'bg-yellow-400' : 'bg-green-400'
                            }`}
                            style={{ width: `${selectedEquipment.cpu || 0}%` }}
                          />
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Mémoire</span>
                          <span className={`text-sm font-medium ${(selectedEquipment.memory || 0) > 80 ? 'text-red-400' : (selectedEquipment.memory || 0) > 60 ? 'text-yellow-400' : 'text-green-400'}`}>
                            {selectedEquipment.memory || 0}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-300 ${
                              (selectedEquipment.memory || 0) > 80 ? 'bg-red-400' : 
                              (selectedEquipment.memory || 0) > 60 ? 'bg-yellow-400' : 'bg-green-400'
                            }`}
                            style={{ width: `${selectedEquipment.memory || 0}%` }}
                          />
                        </div>
                      </div>
                      
                      <div>
                        <div className="flex justify-between items-center mb-1">
                          <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Disque</span>
                          <span className={`text-sm font-medium ${(selectedEquipment.disk || 0) > 80 ? 'text-red-400' : (selectedEquipment.disk || 0) > 60 ? 'text-yellow-400' : 'text-green-400'}`}>
                            {selectedEquipment.disk || 0}%
                          </span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full transition-all duration-300 ${
                              (selectedEquipment.disk || 0) > 80 ? 'bg-red-400' : 
                              (selectedEquipment.disk || 0) > 60 ? 'bg-yellow-400' : 'bg-green-400'
                            }`}
                            style={{ width: `${selectedEquipment.disk || 0}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Informations techniques */}
                  <div className="space-y-2 mb-3">
                    <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>Informations techniques</h3>
                    
                    <div className="grid grid-cols-1 gap-3">
                      <div className="flex justify-between">
                        <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Fabricant:</span>
                        <span className={`text-sm ${getThemeClasses('text', 'dashboard')}`}>{selectedEquipment.vendor}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Modèle:</span>
                        <span className={`text-sm ${getThemeClasses('text', 'dashboard')}`}>{selectedEquipment.model}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Numéro de série:</span>
                        <span className={`text-sm ${getThemeClasses('text', 'dashboard')} font-mono`}>{selectedEquipment.serialNumber}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Firmware:</span>
                        <span className={`text-sm ${getThemeClasses('text', 'dashboard')}`}>{selectedEquipment.firmwareVersion}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Emplacement:</span>
                        <span className={`text-sm ${getThemeClasses('text', 'dashboard')}`}>{selectedEquipment.location}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Connexions:</span>
                        <span className={`text-sm ${getThemeClasses('text', 'dashboard')}`}>{selectedEquipment.connections}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>Dernière activité:</span>
                        <span className={`text-sm ${getThemeClasses('text', 'dashboard')}`}>
                          {new Date(selectedEquipment.lastSeen).toLocaleString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Actions rapides */}
                  <div className="space-y-2">
                    <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>Actions rapides</h3>
                    
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={() => handleEquipmentAction(selectedEquipment.id, selectedEquipment.status === 'Actif' ? 'stop' : 'start')}
                        className={`flex items-center justify-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          selectedEquipment.status === 'Actif'
                            ? 'bg-red-600 hover:bg-red-700 text-white'
                            : 'bg-green-600 hover:bg-green-700 text-white'
                        }`}
                      >
                        {selectedEquipment.status === 'Actif' ? (
                          <>
                            <Pause className="w-4 h-4 mr-2" />
                            Arrêter
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4 mr-2" />
                            Démarrer
                          </>
                        )}
                      </button>
                      
                      <button
                        onClick={() => handleEquipmentAction(selectedEquipment.id, 'restart')}
                        className="flex items-center justify-center px-3 py-2 rounded-lg text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors"
                      >
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Redémarrer
                      </button>
                      
                      <button
                        onClick={() => handleEquipmentAction(selectedEquipment.id, 'configure')}
                        className="flex items-center justify-center px-3 py-2 rounded-lg text-sm font-medium bg-purple-600 hover:bg-purple-700 text-white transition-colors"
                      >
                        <Settings className="w-4 h-4 mr-2" />
                        Configurer
                      </button>
                      
                      <button
                        onClick={() => handleEquipmentAction(selectedEquipment.id, 'edit')}
                        className="flex items-center justify-center px-3 py-2 rounded-lg text-sm font-medium bg-gray-600 hover:bg-gray-700 text-white transition-colors"
                      >
                        <Edit className="w-4 h-4 mr-2" />
                        Modifier
                      </button>
                    </div>
                  </div>

                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Equipment;