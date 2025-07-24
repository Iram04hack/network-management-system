// DeviceManagement.jsx - Composant pour la gestion CRUD des équipements réseau
import React, { useState, useCallback } from 'react';
import { 
  Plus, 
  Edit, 
  Trash2, 
  Save, 
  X, 
  Search,
  Settings,
  Wifi,
  Router,
  Server,
  Monitor,
  Network,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Eye,
  Download,
  Upload
} from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const DeviceManagement = ({ devices = [], onDeviceChange, isVisible = true }) => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  const { getThemeClasses } = useTheme();

  // Formulaire pour nouveau dispositif/édition
  const [deviceForm, setDeviceForm] = useState({
    name: '',
    ip: '',
    mac: '',
    type: 'Router',
    vendor: '',
    model: '',
    location: '',
    description: '',
    snmpCommunity: 'public',
    snmpVersion: 'v2c',
    credentials: {
      username: '',
      password: '',
      enablePassword: ''
    },
    interfaces: [],
    status: 'active'
  });

  // Types de dispositifs disponibles
  const deviceTypes = [
    { value: 'Router', label: 'Routeur', icon: Router },
    { value: 'Switch', label: 'Switch', icon: Network },
    { value: 'Server', label: 'Serveur', icon: Server },
    { value: 'AccessPoint', label: 'Point d\'accès', icon: Wifi },
    { value: 'Firewall', label: 'Pare-feu', icon: Monitor },
    { value: 'Other', label: 'Autre', icon: Network }
  ];

  // Dispositifs mockés
  const mockDevices = devices.length > 0 ? devices : [
    {
      id: 'dev-1',
      name: 'Router Principal',
      ip: '192.168.1.1',
      mac: '00:1A:2B:3C:4D:5E',
      type: 'Router',
      vendor: 'Cisco',
      model: 'ISR4331',
      location: 'Datacenter 1',
      description: 'Routeur principal du réseau',
      status: 'active',
      snmpCommunity: 'public',
      snmpVersion: 'v2c',
      lastSeen: new Date().toISOString(),
      interfaces: [
        { name: 'GigabitEthernet0/0', status: 'up', speed: '1000' },
        { name: 'GigabitEthernet0/1', status: 'up', speed: '1000' }
      ]
    },
    {
      id: 'dev-2',
      name: 'Switch Core',
      ip: '192.168.1.2',
      mac: '00:2B:3C:4D:5E:6F',
      type: 'Switch',
      vendor: 'Cisco',
      model: 'WS-C2960X',
      location: 'Datacenter 1',
      description: 'Switch principal du cœur de réseau',
      status: 'active',
      snmpCommunity: 'public',
      snmpVersion: 'v2c',
      lastSeen: new Date().toISOString(),
      interfaces: [
        { name: 'FastEthernet0/1', status: 'up', speed: '100' },
        { name: 'FastEthernet0/2', status: 'down', speed: '100' }
      ]
    }
  ];

  // Filtrage des dispositifs
  const filteredDevices = mockDevices.filter(device => {
    const matchesSearch = searchQuery === '' || 
      device.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      device.ip.includes(searchQuery) ||
      device.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
      device.location.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesType = filterType === 'all' || device.type === filterType;
    const matchesStatus = filterStatus === 'all' || device.status === filterStatus;
    
    return matchesSearch && matchesType && matchesStatus;
  });

  // Gestionnaires d'événements
  const handleAddDevice = () => {
    setDeviceForm({
      name: '',
      ip: '',
      mac: '',
      type: 'Router',
      vendor: '',
      model: '',
      location: '',
      description: '',
      snmpCommunity: 'public',
      snmpVersion: 'v2c',
      credentials: {
        username: '',
        password: '',
        enablePassword: ''
      },
      interfaces: [],
      status: 'active'
    });
    setIsAddModalOpen(true);
  };

  const handleEditDevice = (device) => {
    setSelectedDevice(device);
    setDeviceForm({
      ...device,
      credentials: device.credentials || {
        username: '',
        password: '',
        enablePassword: ''
      }
    });
    setIsEditModalOpen(true);
  };

  const handleDeleteDevice = (device) => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer ${device.name} ?`)) {
      console.log('Suppression du dispositif:', device.id);
      if (onDeviceChange) {
        onDeviceChange('delete', device.id);
      }
    }
  };

  const handleSaveDevice = () => {
    if (isAddModalOpen) {
      const newDevice = {
        ...deviceForm,
        id: `dev-${Date.now()}`,
        lastSeen: new Date().toISOString()
      };
      console.log('Ajout du dispositif:', newDevice);
      if (onDeviceChange) {
        onDeviceChange('add', newDevice);
      }
      setIsAddModalOpen(false);
    } else if (isEditModalOpen) {
      const updatedDevice = {
        ...selectedDevice,
        ...deviceForm
      };
      console.log('Modification du dispositif:', updatedDevice);
      if (onDeviceChange) {
        onDeviceChange('update', updatedDevice);
      }
      setIsEditModalOpen(false);
    }
  };

  const handleCloseModal = () => {
    setIsAddModalOpen(false);
    setIsEditModalOpen(false);
    setSelectedDevice(null);
  };

  // Composant de recherche et filtres
  const SearchAndFilters = () => (
    <div className="flex items-center space-x-4 mb-4">
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher par nom, IP, type, emplacement..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
        />
      </div>
      
      <select
        value={filterType}
        onChange={(e) => setFilterType(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les types</option>
        {deviceTypes.map(type => (
          <option key={type.value} value={type.value}>{type.label}</option>
        ))}
      </select>
      
      <select
        value={filterStatus}
        onChange={(e) => setFilterStatus(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les statuts</option>
        <option value="active">Actifs</option>
        <option value="inactive">Inactifs</option>
        <option value="warning">En alerte</option>
      </select>
      
      <button
        onClick={handleAddDevice}
        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
      >
        <Plus className="w-4 h-4" />
        <span>Ajouter</span>
      </button>
    </div>
  );

  // Tableau des dispositifs
  const DevicesTable = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Dispositif</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Réseau</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Type/Modèle</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Emplacement</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredDevices.map((device) => {
              const typeInfo = deviceTypes.find(t => t.value === device.type);
              const IconComponent = typeInfo?.icon || Network;
              
              return (
                <tr 
                  key={device.id} 
                  className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors"
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-3">
                      <IconComponent className="w-5 h-5 text-blue-400" />
                      <div>
                        <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                          {device.name}
                        </div>
                        <div className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>
                          {device.description || 'Aucune description'}
                        </div>
                      </div>
                    </div>
                  </td>
                  
                  <td className="py-3 px-4">
                    <div>
                      <div className={`${getThemeClasses('text', 'dashboard')} font-mono`}>
                        {device.ip}
                      </div>
                      <div className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')} font-mono`}>
                        {device.mac}
                      </div>
                    </div>
                  </td>
                  
                  <td className="py-3 px-4">
                    <div>
                      <div className={`${getThemeClasses('text', 'dashboard')}`}>
                        {typeInfo?.label || device.type}
                      </div>
                      <div className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>
                        {device.vendor} {device.model}
                      </div>
                    </div>
                  </td>
                  
                  <td className="py-3 px-4">
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                      {device.location}
                    </span>
                  </td>
                  
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded ${
                      device.status === 'active' 
                        ? 'bg-green-900/30 text-green-400' 
                        : device.status === 'warning'
                        ? 'bg-yellow-900/30 text-yellow-400'
                        : 'bg-red-900/30 text-red-400'
                    }`}>
                      {device.status === 'active' && <CheckCircle className="w-3 h-3 mr-1" />}
                      {device.status === 'warning' && <AlertTriangle className="w-3 h-3 mr-1" />}
                      {device.status === 'inactive' && <XCircle className="w-3 h-3 mr-1" />}
                      {device.status === 'active' ? 'Actif' : 
                       device.status === 'warning' ? 'Alerte' : 'Inactif'}
                    </span>
                  </td>
                  
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <button 
                        onClick={() => console.log('Voir détails:', device.id)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors" 
                        title="Voir détails"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => handleEditDevice(device)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors" 
                        title="Modifier"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => console.log('Configurer:', device.id)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors" 
                        title="Configurer"
                      >
                        <Settings className="w-4 h-4" />
                      </button>
                      <button 
                        onClick={() => handleDeleteDevice(device)}
                        className="p-1.5 rounded hover:bg-red-700 transition-colors text-red-400" 
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

  // Modal de formulaire (ajout/édition)
  const DeviceModal = () => {
    const isOpen = isAddModalOpen || isEditModalOpen;
    const title = isAddModalOpen ? 'Ajouter un dispositif' : 'Modifier le dispositif';
    
    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-lg shadow-2xl border border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
              {title}
            </h2>
            <button
              onClick={handleCloseModal}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Informations générales */}
            <div>
              <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-4`}>
                Informations générales
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Nom du dispositif *
                  </label>
                  <input
                    type="text"
                    value={deviceForm.name}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, name: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                    placeholder="Ex: Router-Principal"
                    required
                  />
                </div>
                
                <div>
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Type de dispositif *
                  </label>
                  <select
                    value={deviceForm.type}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, type: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                    required
                  >
                    {deviceTypes.map(type => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Adresse IP *
                  </label>
                  <input
                    type="text"
                    value={deviceForm.ip}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, ip: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                    placeholder="192.168.1.1"
                    required
                  />
                </div>
                
                <div>
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Adresse MAC
                  </label>
                  <input
                    type="text"
                    value={deviceForm.mac}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, mac: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                    placeholder="00:1A:2B:3C:4D:5E"
                  />
                </div>
                
                <div>
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Fabricant
                  </label>
                  <input
                    type="text"
                    value={deviceForm.vendor}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, vendor: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                    placeholder="Cisco"
                  />
                </div>
                
                <div>
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Modèle
                  </label>
                  <input
                    type="text"
                    value={deviceForm.model}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, model: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                    placeholder="ISR4331"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Emplacement
                  </label>
                  <input
                    type="text"
                    value={deviceForm.location}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, location: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                    placeholder="Datacenter 1, Rack A, Position 12"
                  />
                </div>
                
                <div className="md:col-span-2">
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Description
                  </label>
                  <textarea
                    value={deviceForm.description}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, description: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                    rows={3}
                    placeholder="Description du dispositif et de son rôle"
                  />
                </div>
              </div>
            </div>

            {/* Configuration SNMP */}
            <div>
              <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-4`}>
                Configuration SNMP
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Version SNMP
                  </label>
                  <select
                    value={deviceForm.snmpVersion}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, snmpVersion: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  >
                    <option value="v1">SNMP v1</option>
                    <option value="v2c">SNMP v2c</option>
                    <option value="v3">SNMP v3</option>
                  </select>
                </div>
                
                <div>
                  <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
                    Communauté SNMP
                  </label>
                  <input
                    type="text"
                    value={deviceForm.snmpCommunity}
                    onChange={(e) => setDeviceForm(prev => ({ ...prev, snmpCommunity: e.target.value }))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                    placeholder="public"
                  />
                </div>
              </div>
            </div>

            {/* Statut */}
            <div>
              <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-4`}>
                Statut
              </h3>
              <select
                value={deviceForm.status}
                onChange={(e) => setDeviceForm(prev => ({ ...prev, status: e.target.value }))}
                className="w-full md:w-48 px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
              >
                <option value="active">Actif</option>
                <option value="inactive">Inactif</option>
                <option value="warning">En alerte</option>
              </select>
            </div>
          </div>
          
          <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-700">
            <button
              onClick={handleCloseModal}
              className="px-4 py-2 text-gray-400 hover:text-white border border-gray-600 hover:border-gray-500 rounded transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={handleSaveDevice}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            >
              <Save className="w-4 h-4" />
              <span>{isAddModalOpen ? 'Ajouter' : 'Enregistrer'}</span>
            </button>
          </div>
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
            Gestion des Équipements
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            {filteredDevices.length} dispositif(s) trouvé(s)
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
        </div>
      </div>

      <SearchAndFilters />
      <DevicesTable />
      <DeviceModal />
    </div>
  );
};

export default DeviceManagement;