// Monitoring-simple.jsx - Version simplifiée temporaire pour le debugging de navigation
import React, { useState, useEffect } from 'react';
import { 
  Monitor, 
  Activity, 
  Cpu,
  HardDrive,
  Wifi,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp,
  Server,
  Database,
  Shield,
  Bell,
  RefreshCw
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const Monitoring = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [metrics, setMetrics] = useState({
    cpu: Math.floor(Math.random() * 100),
    memory: Math.floor(Math.random() * 100),
    network: Math.floor(Math.random() * 100),
    disk: Math.floor(Math.random() * 100)
  });

  const { getThemeClasses } = useTheme();

  // Mise à jour de l'heure et métriques simulées
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
      setMetrics({
        cpu: Math.floor(Math.random() * 100),
        memory: Math.floor(Math.random() * 100),
        network: Math.floor(Math.random() * 100),
        disk: Math.floor(Math.random() * 100)
      });
    }, 2000);

    return () => clearInterval(timer);
  }, []);

  const getStatusColor = (value) => {
    if (value < 50) return 'text-green-600 bg-green-100';
    if (value < 80) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getStatusIcon = (value) => {
    if (value < 50) return <CheckCircle className="w-4 h-4" />;
    if (value < 80) return <Clock className="w-4 h-4" />;
    return <AlertTriangle className="w-4 h-4" />;
  };

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header distinctive */}
        <div className="bg-emerald-600 text-white p-6 rounded-lg shadow-lg mb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Monitor className="w-12 h-12" />
              <div>
                <h1 className="text-3xl font-bold">📊 MONITORING SYSTÈME</h1>
                <p className="text-emerald-100">Page de monitoring - Navigation vers Monitoring RÉUSSIE !</p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-emerald-100 text-sm">Surveillance en temps réel :</p>
              <p className="text-white font-mono text-lg">{currentTime.toLocaleTimeString()}</p>
            </div>
          </div>
        </div>

        {/* Métriques en temps réel */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* CPU */}
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-blue-500">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Cpu className="w-6 h-6 text-blue-600" />
                <h3 className="font-bold text-blue-700">CPU</h3>
              </div>
              {getStatusIcon(metrics.cpu)}
            </div>
            <div className="text-3xl font-bold text-blue-600 mb-2">{metrics.cpu}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                style={{ width: `${metrics.cpu}%` }}
              ></div>
            </div>
          </div>

          {/* Mémoire */}
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-green-500">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Activity className="w-6 h-6 text-green-600" />
                <h3 className="font-bold text-green-700">Mémoire</h3>
              </div>
              {getStatusIcon(metrics.memory)}
            </div>
            <div className="text-3xl font-bold text-green-600 mb-2">{metrics.memory}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-green-600 h-2 rounded-full transition-all duration-500" 
                style={{ width: `${metrics.memory}%` }}
              ></div>
            </div>
          </div>

          {/* Réseau */}
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-purple-500">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <Wifi className="w-6 h-6 text-purple-600" />
                <h3 className="font-bold text-purple-700">Réseau</h3>
              </div>
              {getStatusIcon(metrics.network)}
            </div>
            <div className="text-3xl font-bold text-purple-600 mb-2">{metrics.network}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-purple-600 h-2 rounded-full transition-all duration-500" 
                style={{ width: `${metrics.network}%` }}
              ></div>
            </div>
          </div>

          {/* Disque */}
          <div className="bg-white p-6 rounded-lg shadow border-l-4 border-orange-500">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center space-x-2">
                <HardDrive className="w-6 h-6 text-orange-600" />
                <h3 className="font-bold text-orange-700">Disque</h3>
              </div>
              {getStatusIcon(metrics.disk)}
            </div>
            <div className="text-3xl font-bold text-orange-600 mb-2">{metrics.disk}%</div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-orange-600 h-2 rounded-full transition-all duration-500" 
                style={{ width: `${metrics.disk}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* État des services */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Services système */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800 flex items-center">
                <Server className="w-5 h-5 mr-2" />
                Services Système
              </h2>
              <RefreshCw className="w-5 h-5 text-gray-400" />
            </div>
            
            <div className="space-y-3">
              {[
                { name: 'Apache', status: 'running', port: '80' },
                { name: 'MySQL', status: 'running', port: '3306' },
                { name: 'Redis', status: 'warning', port: '6379' },
                { name: 'Nginx', status: 'running', port: '443' }
              ].map((service, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      service.status === 'running' ? 'bg-green-500' : 
                      service.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}></div>
                    <span className="font-medium">{service.name}</span>
                  </div>
                  <div className="text-sm text-gray-500">Port {service.port}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Alertes récentes */}
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800 flex items-center">
                <Bell className="w-5 h-5 mr-2" />
                Alertes Récentes
              </h2>
              <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded">3</span>
            </div>
            
            <div className="space-y-3">
              {[
                { type: 'critical', message: 'CPU usage élevé sur srv-web-01', time: '5 min' },
                { type: 'warning', message: 'Espace disque faible sur srv-db-02', time: '12 min' },
                { type: 'info', message: 'Redémarrage planifié srv-backup-01', time: '1h' }
              ].map((alert, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded">
                  <AlertTriangle className={`w-5 h-5 mt-0.5 ${
                    alert.type === 'critical' ? 'text-red-500' :
                    alert.type === 'warning' ? 'text-yellow-500' : 'text-blue-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{alert.message}</p>
                    <p className="text-xs text-gray-500">Il y a {alert.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Message de test */}
        <div className="bg-emerald-100 border border-emerald-300 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-emerald-600" />
            <div>
              <p className="text-emerald-800 font-semibold">
                📊 Test de Navigation Monitoring Réussi !
              </p>
              <p className="text-emerald-600 text-sm">
                Si vous voyez cette page avec un arrière-plan ardoise et des métriques qui changent, 
                cela signifie que vous êtes bien sur la page de Monitoring.
              </p>
              <p className="text-emerald-500 text-xs mt-2 font-mono">
                Métriques mise à jour : {currentTime.toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Monitoring;