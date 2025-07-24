// ApiTestPage.jsx - Page de test du système API unifié
import React, { useState, useEffect } from 'react';
import { RefreshCw, CheckCircle, AlertTriangle, Server, Monitor, Database } from 'lucide-react';

// Import des variables globales API unifiées
import {
  projectsList,
  equipmentsList,
  totalEquipments,
  activeEquipments,
  totalProjects,
  activeNodes,
  systemMetrics,
  dockerServices,
  totalServices,
  healthyServices,
  healthPercentage,
  systemAlerts,
  totalAlerts,
  criticalAlerts,
  warningAlerts,
  devicesByType,
  devicesByVendor,
  systemOperational,
  overallHealth,
  lastUpdate,
  errors,
  refreshAllData,
  getEssentialStats,
  isDataAvailable
} from '../services/UnifiedApiData';

const ApiTestPage = () => {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  // Force l'actualisation de l'affichage
  const [, forceUpdate] = useState({});
  const refreshComponent = () => forceUpdate({});

  // Actualiser le composant toutes les 3 secondes
  useEffect(() => {
    const interval = setInterval(() => {
      refreshComponent();
      setLastRefresh(new Date());
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  // Fonction de refresh manuel
  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshAllData();
      console.log('Données actualisées avec succès');
    } catch (error) {
      console.error('Erreur lors de l\'actualisation:', error);
    }
    setIsRefreshing(false);
  };

  // Obtenir les stats essentielles
  const stats = getEssentialStats();
  const dataAvailability = isDataAvailable();

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-6xl mx-auto">
        
        {/* En-tête */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold">Test du Système API Unifié</h1>
            <p className="text-gray-400 mt-2">
              Vérification des variables globales et des données temps réel
            </p>
          </div>
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-400">
              Dernière actualisation: {lastRefresh.toLocaleTimeString('fr-FR')}
            </div>
            <button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className={`flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors ${
                isRefreshing ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              <span>Actualiser</span>
            </button>
          </div>
        </div>

        {/* Statut du système unifié */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Système Opérationnel</p>
                <p className={`text-2xl font-bold ${systemOperational ? 'text-green-400' : 'text-red-400'}`}>
                  {systemOperational ? 'OUI' : 'NON'}
                </p>
                <p className="text-gray-400 text-xs mt-1">Santé: {overallHealth}</p>
              </div>
              <CheckCircle className={`w-8 h-8 ${systemOperational ? 'text-green-400' : 'text-red-400'}`} />
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Données Disponibles</p>
                <p className="text-2xl font-bold text-blue-400">
                  {Object.values(dataAvailability).filter(Boolean).length}/6
                </p>
                <p className="text-gray-400 text-xs mt-1">Modules actifs</p>
              </div>
              <Database className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Erreurs Actives</p>
                <p className={`text-2xl font-bold ${Object.values(errors).some(Boolean) ? 'text-red-400' : 'text-green-400'}`}>
                  {Object.values(errors).filter(Boolean).length}
                </p>
                <p className="text-gray-400 text-xs mt-1">APIs en erreur</p>
              </div>
              <AlertTriangle className={`w-8 h-8 ${Object.values(errors).some(Boolean) ? 'text-red-400' : 'text-green-400'}`} />
            </div>
          </div>
        </div>

        {/* Métriques essentielles */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Équipements Total</p>
                <p className="text-2xl font-bold text-blue-400">{totalEquipments}</p>
                <p className="text-gray-400 text-xs mt-1">{activeEquipments} actifs</p>
              </div>
              <Server className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Projets GNS3</p>
                <p className="text-2xl font-bold text-cyan-400">{totalProjects}</p>
                <p className="text-gray-400 text-xs mt-1">{activeNodes} nœuds actifs</p>
              </div>
              <Monitor className="w-8 h-8 text-cyan-400" />
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">CPU Système</p>
                <p className="text-2xl font-bold text-green-400">{systemMetrics.cpu.current}%</p>
                <p className="text-gray-400 text-xs mt-1">Tendance: {systemMetrics.cpu.trend}</p>
              </div>
              <Monitor className="w-8 h-8 text-green-400" />
            </div>
          </div>

          <div className="bg-gray-800 p-6 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Alertes Actives</p>
                <p className="text-2xl font-bold text-orange-400">{totalAlerts}</p>
                <p className="text-gray-400 text-xs mt-1">{criticalAlerts} critiques</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-400" />
            </div>
          </div>
        </div>

        {/* Détails des données */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          
          {/* Projets GNS3 */}
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">Projets GNS3 ({projectsList.length})</h3>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {projectsList.length > 0 ? (
                projectsList.map((project, index) => (
                  <div key={project.id || index} className="flex items-center justify-between text-sm">
                    <span className="truncate">{project.name}</span>
                    <span className={`px-2 py-1 rounded text-xs ${
                      project.status === 'open' ? 'bg-green-600' : 'bg-gray-600'
                    }`}>
                      {project.status}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-gray-400 text-sm">Aucun projet GNS3</p>
              )}
            </div>
          </div>

          {/* Équipements réseau */}
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-4">Équipements Réseau ({equipmentsList.length})</h3>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {equipmentsList.length > 0 ? (
                equipmentsList.slice(0, 5).map((device, index) => (
                  <div key={device.id || index} className="flex items-center justify-between text-sm">
                    <div>
                      <span className="font-medium">{device.name}</span>
                      <span className="text-gray-400 ml-2">({device.device_type})</span>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      device.is_active ? 'bg-green-600' : 'bg-red-600'
                    }`}>
                      {device.is_active ? 'Actif' : 'Inactif'}
                    </span>
                  </div>
                ))
              ) : (
                <p className="text-gray-400 text-sm">Aucun équipement réseau</p>
              )}
              {equipmentsList.length > 5 && (
                <p className="text-gray-400 text-xs">... et {equipmentsList.length - 5} autres</p>
              )}
            </div>
          </div>

        </div>

        {/* Métriques système en temps réel */}
        <div className="bg-gray-800 p-6 rounded-lg mb-8">
          <h3 className="text-lg font-semibold mb-4">Métriques Système Temps Réel</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            <div>
              <div className="flex justify-between mb-2">
                <span>CPU</span>
                <span>{systemMetrics.cpu.current}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-500" 
                  style={{ width: `${systemMetrics.cpu.current}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Max: {systemMetrics.cpu.max}% | Tendance: {systemMetrics.cpu.trend}
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <span>Mémoire</span>
                <span>{systemMetrics.memory.current}%</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-green-600 h-2 rounded-full transition-all duration-500" 
                  style={{ width: `${systemMetrics.memory.current}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Max: {systemMetrics.memory.max}% | Tendance: {systemMetrics.memory.trend}
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <span>Réseau</span>
                <span>{systemMetrics.network.current} MB/s</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-purple-600 h-2 rounded-full transition-all duration-500" 
                  style={{ width: `${Math.min((systemMetrics.network.current / 100) * 100, 100)}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-400 mt-1">
                Max: {systemMetrics.network.max} MB/s | Tendance: {systemMetrics.network.trend}
              </div>
            </div>

          </div>
        </div>

        {/* Services Docker */}
        <div className="bg-gray-800 p-6 rounded-lg mb-8">
          <h3 className="text-lg font-semibold mb-4">
            Services Docker ({totalServices} total, {healthyServices} sains, {healthPercentage.toFixed(1)}%)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dockerServices.slice(0, 6).map((service, index) => (
              <div key={service.id || index} className="bg-gray-700 p-3 rounded">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium truncate">{service.name}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    service.health_status === 'healthy' ? 'bg-green-600' : 'bg-red-600'
                  }`}>
                    {service.health_status}
                  </span>
                </div>
                <div className="text-xs text-gray-400 mt-1">
                  CPU: {service.cpu_percent?.toFixed(1) || 0}% | RAM: {service.memory_percent?.toFixed(1) || 0}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* État des dernières mises à jour */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-lg font-semibold mb-4">État des Mises à Jour</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(lastUpdate).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-sm capitalize">{key.replace(/([A-Z])/g, ' $1')}</span>
                <div className="text-right">
                  <div className={`text-xs ${value ? 'text-green-400' : 'text-gray-400'}`}>
                    {value ? new Date(value).toLocaleTimeString('fr-FR') : 'Jamais'}
                  </div>
                  {errors[key] && (
                    <div className="text-xs text-red-400 mt-1">
                      Erreur: {errors[key]}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
};

export default ApiTestPage;