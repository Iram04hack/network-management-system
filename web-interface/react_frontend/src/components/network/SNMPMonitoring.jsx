// SNMPMonitoring.jsx - Composant pour le monitoring SNMP
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Activity, 
  Wifi, 
  RefreshCw, 
  Settings, 
  Play, 
  Pause,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Database,
  Network,
  Monitor,
  Server,
  Router,
  Eye,
  Edit
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const SNMPMonitoring = ({ devices = [], isVisible = true }) => {
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [snmpConfig, setSNMPConfig] = useState({
    version: 'v2c',
    community: 'public',
    port: 161,
    timeout: 5000,
    retries: 3,
    pollingInterval: 30000
  });
  const [monitoringData, setMonitoringData] = useState({});
  const [historicalData, setHistoricalData] = useState({});

  const { getThemeClasses } = useTheme();

  // Dispositifs mockés avec support SNMP
  const mockSNMPDevices = devices.length > 0 ? devices : [
    {
      id: 'router-1',
      name: 'Router Principal',
      ip: '192.168.1.1',
      type: 'Router',
      vendor: 'Cisco',
      model: 'ISR4331',
      snmpStatus: 'active',
      community: 'public',
      version: 'v2c',
      oids: {
        sysName: '1.3.6.1.2.1.1.5.0',
        sysUptime: '1.3.6.1.2.1.1.3.0',
        ifInOctets: '1.3.6.1.2.1.2.2.1.10',
        ifOutOctets: '1.3.6.1.2.1.2.2.1.16',
        cpuUsage: '1.3.6.1.4.1.9.9.109.1.1.1.1.7',
        memoryUsage: '1.3.6.1.4.1.9.9.48.1.1.1.5'
      }
    },
    {
      id: 'switch-1',
      name: 'Switch Core',
      ip: '192.168.1.2',
      type: 'Switch',
      vendor: 'Cisco',
      model: 'WS-C2960X',
      snmpStatus: 'active',
      community: 'public',
      version: 'v2c',
      oids: {
        sysName: '1.3.6.1.2.1.1.5.0',
        sysUptime: '1.3.6.1.2.1.1.3.0',
        ifInOctets: '1.3.6.1.2.1.2.2.1.10',
        ifOutOctets: '1.3.6.1.2.1.2.2.1.16'
      }
    },
    {
      id: 'server-1',
      name: 'File Server',
      ip: '192.168.1.10',
      type: 'Server',
      vendor: 'Ubuntu',
      model: 'Server 20.04',
      snmpStatus: 'warning',
      community: 'private',
      version: 'v3',
      oids: {
        sysName: '1.3.6.1.2.1.1.5.0',
        sysUptime: '1.3.6.1.2.1.1.3.0',
        cpuUsage: '1.3.6.1.4.1.2021.11.9.0',
        memoryUsage: '1.3.6.1.4.1.2021.4.6.0'
      }
    }
  ];

  // Données mockées pour le monitoring
  const generateMockData = useCallback((deviceId) => {
    const time = Date.now();
    return {
      timestamp: time,
      cpu: Math.random() * 80 + 10,
      memory: Math.random() * 70 + 15,
      networkIn: Math.random() * 100 + 20,
      networkOut: Math.random() * 80 + 10,
      uptime: Math.floor(Math.random() * 1000000) + 500000,
      interfaces: [
        {
          name: 'GigabitEthernet0/0',
          status: 'up',
          speed: '1000000000',
          inOctets: Math.floor(Math.random() * 1000000000),
          outOctets: Math.floor(Math.random() * 1000000000),
          inErrors: Math.floor(Math.random() * 100),
          outErrors: Math.floor(Math.random() * 100)
        },
        {
          name: 'GigabitEthernet0/1',
          status: 'up',
          speed: '1000000000',
          inOctets: Math.floor(Math.random() * 500000000),
          outOctets: Math.floor(Math.random() * 500000000),
          inErrors: Math.floor(Math.random() * 50),
          outErrors: Math.floor(Math.random() * 50)
        }
      ],
      system: {
        sysName: mockSNMPDevices.find(d => d.id === deviceId)?.name || 'Unknown',
        sysDescr: 'Cisco IOS Software',
        sysContact: 'admin@company.com',
        sysLocation: 'Datacenter 1'
      }
    };
  }, [mockSNMPDevices]);

  // Simulation du polling SNMP
  useEffect(() => {
    if (!isMonitoring) return;

    const interval = setInterval(() => {
      const newData = {};
      mockSNMPDevices.forEach(device => {
        if (device.snmpStatus === 'active') {
          newData[device.id] = generateMockData(device.id);
        }
      });
      
      setMonitoringData(newData);
      
      // Ajouter aux données historiques
      setHistoricalData(prev => {
        const updated = { ...prev };
        Object.keys(newData).forEach(deviceId => {
          if (!updated[deviceId]) updated[deviceId] = [];
          updated[deviceId].push(newData[deviceId]);
          // Garder seulement les 20 dernières mesures
          if (updated[deviceId].length > 20) {
            updated[deviceId] = updated[deviceId].slice(-20);
          }
        });
        return updated;
      });
    }, snmpConfig.pollingInterval);

    return () => clearInterval(interval);
  }, [isMonitoring, snmpConfig.pollingInterval, generateMockData, mockSNMPDevices]);

  // Démarrer/arrêter le monitoring
  const toggleMonitoring = () => {
    setIsMonitoring(!isMonitoring);
    if (!isMonitoring) {
      // Premier poll immédiat
      const initialData = {};
      mockSNMPDevices.forEach(device => {
        if (device.snmpStatus === 'active') {
          initialData[device.id] = generateMockData(device.id);
        }
      });
      setMonitoringData(initialData);
    }
  };

  // Configuration SNMP
  const SNMPConfigPanel = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-3`}>
        Configuration SNMP
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Version SNMP
          </label>
          <select
            value={snmpConfig.version}
            onChange={(e) => setSNMPConfig(prev => ({ ...prev, version: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
          >
            <option value="v1">SNMP v1</option>
            <option value="v2c">SNMP v2c</option>
            <option value="v3">SNMP v3</option>
          </select>
        </div>
        
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Communauté
          </label>
          <input
            type="text"
            value={snmpConfig.community}
            onChange={(e) => setSNMPConfig(prev => ({ ...prev, community: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            placeholder="public"
          />
        </div>
        
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Port SNMP
          </label>
          <input
            type="number"
            value={snmpConfig.port}
            onChange={(e) => setSNMPConfig(prev => ({ ...prev, port: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            min="1"
            max="65535"
          />
        </div>
        
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Timeout (ms)
          </label>
          <input
            type="number"
            value={snmpConfig.timeout}
            onChange={(e) => setSNMPConfig(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            min="1000"
            max="30000"
          />
        </div>
        
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Retries
          </label>
          <input
            type="number"
            value={snmpConfig.retries}
            onChange={(e) => setSNMPConfig(prev => ({ ...prev, retries: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            min="1"
            max="10"
          />
        </div>
        
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Intervalle (ms)
          </label>
          <input
            type="number"
            value={snmpConfig.pollingInterval}
            onChange={(e) => setSNMPConfig(prev => ({ ...prev, pollingInterval: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            min="5000"
            max="300000"
          />
        </div>
      </div>
      
      <div className="flex items-center justify-between mt-4">
        <div className="flex items-center space-x-2">
          <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>
            Monitoring: {isMonitoring ? 'Actif' : 'Inactif'}
          </span>
          {isMonitoring && (
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
          )}
        </div>
        
        <button
          onClick={toggleMonitoring}
          className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
            isMonitoring 
              ? 'bg-red-600 hover:bg-red-700 text-white' 
              : 'bg-green-600 hover:bg-green-700 text-white'
          }`}
        >
          {isMonitoring ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          <span>{isMonitoring ? 'Arrêter' : 'Démarrer'}</span>
        </button>
      </div>
    </div>
  );

  // Liste des dispositifs SNMP
  const DevicesList = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden mb-4`}>
      <div className="p-4 border-b border-gray-700">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Dispositifs SNMP ({mockSNMPDevices.length})
        </h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Dispositif</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">IP/Communauté</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut SNMP</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Métriques</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {mockSNMPDevices.map((device) => {
              const data = monitoringData[device.id];
              
              return (
                <tr 
                  key={device.id} 
                  className={`border-b border-gray-700 hover:bg-gray-700/50 transition-colors cursor-pointer ${
                    selectedDevice?.id === device.id ? 'bg-blue-900/20' : ''
                  }`}
                  onClick={() => setSelectedDevice(device)}
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-3">
                      {device.type === 'Router' && <Router className="w-5 h-5 text-blue-400" />}
                      {device.type === 'Switch' && <Network className="w-5 h-5 text-green-400" />}
                      {device.type === 'Server' && <Server className="w-5 h-5 text-purple-400" />}
                      <div>
                        <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                          {device.name}
                        </div>
                        <div className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>
                          {device.vendor} {device.model}
                        </div>
                      </div>
                    </div>
                  </td>
                  
                  <td className="py-3 px-4">
                    <div>
                      <div className={`${getThemeClasses('text', 'dashboard')} font-mono`}>
                        {device.ip}
                      </div>
                      <div className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>
                        {device.community} ({device.version})
                      </div>
                    </div>
                  </td>
                  
                  <td className="py-3 px-4">
                    <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded ${
                      device.snmpStatus === 'active' 
                        ? 'bg-green-900/30 text-green-400' 
                        : device.snmpStatus === 'warning'
                        ? 'bg-yellow-900/30 text-yellow-400'
                        : 'bg-red-900/30 text-red-400'
                    }`}>
                      {device.snmpStatus === 'active' && <CheckCircle className="w-3 h-3 mr-1" />}
                      {device.snmpStatus === 'warning' && <AlertTriangle className="w-3 h-3 mr-1" />}
                      {device.snmpStatus === 'inactive' && <XCircle className="w-3 h-3 mr-1" />}
                      {device.snmpStatus}
                    </span>
                  </td>
                  
                  <td className="py-3 px-4">
                    {data ? (
                      <div className="flex items-center space-x-4 text-sm">
                        <div className="flex items-center space-x-1">
                          <span className="text-gray-400">CPU:</span>
                          <span className={`${data.cpu > 80 ? 'text-red-400' : data.cpu > 60 ? 'text-yellow-400' : 'text-green-400'}`}>
                            {Math.round(data.cpu)}%
                          </span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <span className="text-gray-400">RAM:</span>
                          <span className={`${data.memory > 80 ? 'text-red-400' : data.memory > 60 ? 'text-yellow-400' : 'text-green-400'}`}>
                            {Math.round(data.memory)}%
                          </span>
                        </div>
                      </div>
                    ) : (
                      <span className="text-gray-500 text-sm">Pas de données</span>
                    )}
                  </td>
                  
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <button 
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors" 
                        title="Voir détails"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button 
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors" 
                        title="Configurer"
                      >
                        <Settings className="w-4 h-4" />
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

  // Graphiques de monitoring en temps réel
  const MonitoringCharts = () => {
    if (!selectedDevice || !historicalData[selectedDevice.id]) {
      return (
        <div className={`${getThemeClasses('card', 'dashboard')} p-8 text-center`}>
          <Monitor className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
            Sélectionnez un dispositif pour voir les graphiques de monitoring
          </p>
        </div>
      );
    }

    const chartData = historicalData[selectedDevice.id].map((data, index) => ({
      time: index,
      cpu: data.cpu,
      memory: data.memory,
      networkIn: data.networkIn,
      networkOut: data.networkOut
    }));

    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <h4 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-3`}>
            CPU & Mémoire
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
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
                <Line type="monotone" dataKey="cpu" stroke="#EF4444" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="memory" stroke="#F59E0B" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <h4 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-3`}>
            Trafic Réseau
          </h4>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
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
                <Line type="monotone" dataKey="networkIn" stroke="#10B981" strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="networkOut" stroke="#3B82F6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  };

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <SNMPConfigPanel />
      <DevicesList />
      <MonitoringCharts />
    </div>
  );
};

export default SNMPMonitoring;