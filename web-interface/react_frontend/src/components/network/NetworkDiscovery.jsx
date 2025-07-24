// NetworkDiscovery.jsx - Composant pour la découverte automatique réseau
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  Wifi, 
  Play, 
  Pause, 
  RefreshCw, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Target,
  Settings,
  Clock,
  Router,
  Server,
  Monitor,
  Network,
  Activity
} from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const NetworkDiscovery = ({ onDeviceDiscovered, isVisible = true }) => {
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanResults, setScanResults] = useState([]);
  const [scanConfig, setScanConfig] = useState({
    subnet: '192.168.1.0/24',
    scanType: 'ping',
    timeout: 1000,
    threads: 50,
    enableSNMP: true,
    snmpCommunity: 'public'
  });
  const [scanStats, setScanStats] = useState({
    hostsScanned: 0,
    devicesFound: 0,
    activeDevices: 0,
    duration: 0
  });

  const { getThemeClasses } = useTheme();

  // Simulation du scan réseau
  const simulateNetworkScan = useCallback(async () => {
    setIsScanning(true);
    setScanProgress(0);
    setScanResults([]);
    setScanStats({ hostsScanned: 0, devicesFound: 0, activeDevices: 0, duration: 0 });
    
    const startTime = Date.now();
    const totalHosts = 254; // Pour un /24
    const foundDevices = [];

    // Dispositifs mockés qui seront "découverts"
    const mockDevices = [
      {
        ip: '192.168.1.1',
        hostname: 'Gateway-Router',
        mac: '00:1A:2B:3C:4D:5E',
        vendor: 'Cisco Systems',
        deviceType: 'Router',
        status: 'active',
        responseTime: 2,
        services: ['SSH', 'HTTP', 'SNMP'],
        snmp: {
          sysName: 'Router-Principal',
          sysDescr: 'Cisco IOS Router',
          sysUptime: '45 days, 12:34:56'
        }
      },
      {
        ip: '192.168.1.2',
        hostname: 'Core-Switch',
        mac: '00:2B:3C:4D:5E:6F',
        vendor: 'Cisco Systems',
        deviceType: 'Switch',
        status: 'active',
        responseTime: 1,
        services: ['SSH', 'SNMP', 'HTTP'],
        snmp: {
          sysName: 'Switch-Core',
          sysDescr: 'Cisco Catalyst Switch',
          sysUptime: '30 days, 08:15:22'
        }
      },
      {
        ip: '192.168.1.10',
        hostname: 'File-Server',
        mac: '00:3C:4D:5E:6F:7A',
        vendor: 'Intel Corp',
        deviceType: 'Server',
        status: 'active',
        responseTime: 3,
        services: ['SSH', 'HTTP', 'SMB', 'FTP'],
        snmp: {
          sysName: 'FileServer-01',
          sysDescr: 'Ubuntu Server 20.04',
          sysUptime: '120 days, 02:45:12'
        }
      },
      {
        ip: '192.168.1.50',
        hostname: 'Wireless-AP',
        mac: '00:4D:5E:6F:7A:8B',
        vendor: 'Ubiquiti Networks',
        deviceType: 'AccessPoint',
        status: 'active',
        responseTime: 5,
        services: ['SSH', 'HTTP'],
        snmp: {
          sysName: 'UniFi-AP-Bureau',
          sysDescr: 'Ubiquiti UniFi AP',
          sysUptime: '15 days, 18:30:45'
        }
      },
      {
        ip: '192.168.1.100',
        hostname: 'Firewall',
        mac: '00:5E:6F:7A:8B:9C',
        vendor: 'pfSense',
        deviceType: 'Firewall',
        status: 'active',
        responseTime: 2,
        services: ['SSH', 'HTTPS', 'SNMP'],
        snmp: {
          sysName: 'pfSense-FW',
          sysDescr: 'pfSense Firewall',
          sysUptime: '90 days, 14:22:18'
        }
      }
    ];

    // Simulation du scan avec progression
    for (let i = 1; i <= totalHosts; i++) {
      await new Promise(resolve => setTimeout(resolve, 10)); // Délai pour simulation
      
      setScanProgress((i / totalHosts) * 100);
      setScanStats(prev => ({ 
        ...prev, 
        hostsScanned: i,
        duration: Math.round((Date.now() - startTime) / 1000)
      }));

      // "Découvrir" les dispositifs mockés
      const deviceFound = mockDevices.find(device => 
        device.ip === `192.168.1.${i}`
      );

      if (deviceFound) {
        foundDevices.push({
          ...deviceFound,
          discoveredAt: new Date().toISOString(),
          id: `device-${Date.now()}-${i}`
        });
        
        setScanResults(prev => [...prev, deviceFound]);
        setScanStats(prev => ({ 
          ...prev, 
          devicesFound: foundDevices.length,
          activeDevices: foundDevices.filter(d => d.status === 'active').length
        }));

        // Callback pour notifier la découverte
        if (onDeviceDiscovered) {
          onDeviceDiscovered(deviceFound);
        }
      }

      // Arrêter si l'utilisateur a stoppé le scan
      if (!isScanning) break;
    }

    setIsScanning(false);
    setScanProgress(100);
  }, [isScanning, onDeviceDiscovered]);

  // Démarrer/arrêter le scan
  const handleScanToggle = useCallback(() => {
    if (isScanning) {
      setIsScanning(false);
    } else {
      simulateNetworkScan();
    }
  }, [isScanning, simulateNetworkScan]);

  // Composant de configuration du scan
  const ScanConfiguration = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-3`}>
        Configuration du Scan
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Sous-réseau
          </label>
          <input
            type="text"
            value={scanConfig.subnet}
            onChange={(e) => setScanConfig(prev => ({ ...prev, subnet: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            placeholder="192.168.1.0/24"
          />
        </div>
        
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Type de scan
          </label>
          <select
            value={scanConfig.scanType}
            onChange={(e) => setScanConfig(prev => ({ ...prev, scanType: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
          >
            <option value="ping">Ping</option>
            <option value="tcp">TCP Connect</option>
            <option value="syn">SYN Scan</option>
            <option value="udp">UDP Scan</option>
          </select>
        </div>
        
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Timeout (ms)
          </label>
          <input
            type="number"
            value={scanConfig.timeout}
            onChange={(e) => setScanConfig(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            min="100"
            max="10000"
          />
        </div>
        
        <div>
          <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
            Threads
          </label>
          <input
            type="number"
            value={scanConfig.threads}
            onChange={(e) => setScanConfig(prev => ({ ...prev, threads: parseInt(e.target.value) }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            min="1"
            max="100"
          />
        </div>
        
        <div className="flex items-center">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={scanConfig.enableSNMP}
              onChange={(e) => setScanConfig(prev => ({ ...prev, enableSNMP: e.target.checked }))}
              className="form-checkbox text-blue-500"
            />
            <span className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>
              Activer SNMP
            </span>
          </label>
        </div>
        
        {scanConfig.enableSNMP && (
          <div>
            <label className={`block text-sm font-medium ${getThemeClasses('textSecondary', 'dashboard')} mb-2`}>
              Communauté SNMP
            </label>
            <input
              type="text"
              value={scanConfig.snmpCommunity}
              onChange={(e) => setScanConfig(prev => ({ ...prev, snmpCommunity: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
              placeholder="public"
            />
          </div>
        )}
      </div>
    </div>
  );

  // Composant de statistiques du scan
  const ScanStatistics = () => (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Hôtes scannés</p>
            <p className="text-2xl font-bold text-blue-400">{scanStats.hostsScanned}</p>
          </div>
          <Target className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Dispositifs trouvés</p>
            <p className="text-2xl font-bold text-green-400">{scanStats.devicesFound}</p>
          </div>
          <Network className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Actifs</p>
            <p className="text-2xl font-bold text-emerald-400">{scanStats.activeDevices}</p>
          </div>
          <CheckCircle className="w-8 h-8 text-emerald-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Durée</p>
            <p className="text-2xl font-bold text-purple-400">{scanStats.duration}s</p>
          </div>
          <Clock className="w-8 h-8 text-purple-400" />
        </div>
      </div>
    </div>
  );

  // Composant de progression du scan
  const ScanProgress = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-4`}>
      <div className="flex items-center justify-between mb-3">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          {isScanning ? 'Scan en cours...' : 'Scan terminé'}
        </h3>
        <button
          onClick={handleScanToggle}
          className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
            isScanning 
              ? 'bg-red-600 hover:bg-red-700 text-white' 
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          {isScanning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          <span>{isScanning ? 'Arrêter' : 'Démarrer'}</span>
        </button>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
            Progression
          </span>
          <span className={`${getThemeClasses('text', 'dashboard')}`}>
            {Math.round(scanProgress)}%
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              isScanning ? 'bg-blue-400' : 'bg-green-400'
            }`}
            style={{ width: `${scanProgress}%` }}
          />
        </div>
      </div>
    </div>
  );

  // Icône selon le type de dispositif
  const getDeviceIcon = (deviceType) => {
    const iconMap = {
      'Router': Router,
      'Switch': Wifi,
      'Server': Server,
      'AccessPoint': Wifi,
      'Firewall': Monitor
    };
    return iconMap[deviceType] || Network;
  };

  // Tableau des résultats
  const ScanResults = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden`}>
      <div className="p-4 border-b border-gray-700">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          Dispositifs Découverts ({scanResults.length})
        </h3>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Dispositif</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Réseau</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Services</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">SNMP</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut</th>
            </tr>
          </thead>
          <tbody>
            {scanResults.map((device, index) => {
              const IconComponent = getDeviceIcon(device.deviceType);
              
              return (
                <tr 
                  key={device.id || index} 
                  className={`border-b border-gray-700 hover:bg-gray-700/50 transition-colors`}
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-3">
                      <IconComponent className="w-5 h-5 text-blue-400" />
                      <div>
                        <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                          {device.hostname || device.ip}
                        </div>
                        <div className={`text-sm ${getThemeClasses('textSecondary', 'dashboard')}`}>
                          {device.vendor} - {device.deviceType}
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
                        {device.mac}
                      </div>
                    </div>
                  </td>
                  
                  <td className="py-3 px-4">
                    <div className="flex flex-wrap gap-1">
                      {device.services.slice(0, 3).map((service, idx) => (
                        <span 
                          key={idx}
                          className="px-2 py-1 text-xs bg-blue-900/30 text-blue-300 rounded"
                        >
                          {service}
                        </span>
                      ))}
                      {device.services.length > 3 && (
                        <span className="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded">
                          +{device.services.length - 3}
                        </span>
                      )}
                    </div>
                  </td>
                  
                  <td className="py-3 px-4">
                    {device.snmp ? (
                      <div className="space-y-1">
                        <div className={`text-sm ${getThemeClasses('text', 'dashboard')}`}>
                          {device.snmp.sysName}
                        </div>
                        <div className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                          Uptime: {device.snmp.sysUptime}
                        </div>
                      </div>
                    ) : (
                      <span className="text-gray-500 text-sm">Non disponible</span>
                    )}
                  </td>
                  
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <span className={`inline-flex items-center px-2 py-1 text-xs font-medium rounded ${
                        device.status === 'active' 
                          ? 'bg-green-900/30 text-green-400' 
                          : 'bg-red-900/30 text-red-400'
                      }`}>
                        {device.status === 'active' ? <CheckCircle className="w-3 h-3 mr-1" /> : <XCircle className="w-3 h-3 mr-1" />}
                        {device.status === 'active' ? 'Actif' : 'Inactif'}
                      </span>
                      <span className={`text-xs ${getThemeClasses('textSecondary', 'dashboard')}`}>
                        {device.responseTime}ms
                      </span>
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

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <ScanConfiguration />
      <ScanStatistics />
      <ScanProgress />
      {scanResults.length > 0 && <ScanResults />}
    </div>
  );
};

export default NetworkDiscovery;