// NetworkSimple.jsx - Gestion réseau avec variables globales API unifiées
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Router, 
  Server, 
  Wifi, 
  RefreshCw, 
  CheckCircle,
  XCircle,
  AlertTriangle,
  Monitor,
  Activity,
  Network,
  Settings
} from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

// Import des variables globales API unifiées
import {
  projectsList,
  equipmentsList,
  totalEquipments,
  activeEquipments,
  totalProjects,
  activeNodes,
  devicesByType,
  devicesByVendor,
  lastUpdate,
  errors,
  refreshAllData
} from '../services/UnifiedApiData';

import { useTheme } from '../contexts/ThemeContext';

const NetworkSimple = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedProject, setSelectedProject] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  const { getThemeClasses } = useTheme();
  
  // Force l'actualisation de l'affichage
  const [, forceUpdate] = useState({});
  const refreshComponent = useCallback(() => forceUpdate({}), []);
  
  // Actualiser le composant toutes les 3 secondes
  useEffect(() => {
    const interval = setInterval(refreshComponent, 3000);
    return () => clearInterval(interval);
  }, [refreshComponent]);
  
  // Fonction de refresh manuel
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      await refreshAllData();
    } catch (error) {
      console.error('Erreur lors de l\'actualisation:', error);
    }
    setIsRefreshing(false);
  }, []);

  // Données pour graphiques
  const deviceTypeData = React.useMemo(() => {
    return Object.entries(devicesByType).map(([type, count]) => ({
      name: type,
      value: count
    }));
  }, [devicesByType]);

  const vendorData = React.useMemo(() => {
    return Object.entries(devicesByVendor).map(([vendor, count]) => ({
      name: vendor,
      value: count
    }));
  }, [devicesByVendor]);

  const colors = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#F97316'];

  const renderOverview = () => (
    <div className="space-y-6">
      
      {/* Métriques rapides */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className={`${getThemeClasses('card', 'network')} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'network')} text-sm font-medium`}>
                Équipements Total
              </p>
              <p className="text-2xl font-bold text-blue-400">
                {totalEquipments}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'network')} text-xs mt-1`}>
                {activeEquipments} actifs
              </p>
            </div>
            <Server className="w-8 h-8 text-blue-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'network')} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'network')} text-sm font-medium`}>
                Projets GNS3
              </p>
              <p className="text-2xl font-bold text-green-400">
                {totalProjects}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'network')} text-xs mt-1`}>
                {projectsList.filter(p => p.status === 'open').length} ouverts
              </p>
            </div>
            <Network className="w-8 h-8 text-green-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'network')} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'network')} text-sm font-medium`}>
                Nœuds GNS3
              </p>
              <p className="text-2xl font-bold text-purple-400">
                {activeNodes}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'network')} text-xs mt-1`}>
                Actifs
              </p>
            </div>
            <Router className="w-8 h-8 text-purple-400" />
          </div>
        </div>

        <div className={`${getThemeClasses('card', 'network')} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`${getThemeClasses('textSecondary', 'network')} text-sm font-medium`}>
                Types d'Équipements
              </p>
              <p className="text-2xl font-bold text-orange-400">
                {Object.keys(devicesByType).length}
              </p>
              <p className={`${getThemeClasses('textSecondary', 'network')} text-xs mt-1`}>
                Différents
              </p>
            </div>
            <Settings className="w-8 h-8 text-orange-400" />
          </div>
        </div>
      </div>

      {/* Graphiques de répartition */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className={`${getThemeClasses('card', 'network')} p-6`}>
          <h3 className={`${getThemeClasses('text', 'network')} text-lg font-semibold mb-4`}>
            Répartition par Type
          </h3>
          {deviceTypeData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={deviceTypeData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {deviceTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Aucune donnée disponible
            </div>
          )}
        </div>

        <div className={`${getThemeClasses('card', 'network')} p-6`}>
          <h3 className={`${getThemeClasses('text', 'network')} text-lg font-semibold mb-4`}>
            Répartition par Fournisseur
          </h3>
          {vendorData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={vendorData.slice(0, 6)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Aucune donnée disponible
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderEquipments = () => (
    <div className="space-y-6">
      <div className={`${getThemeClasses('card', 'network')} p-6`}>
        <h3 className={`${getThemeClasses('text', 'network')} text-lg font-semibold mb-4`}>
          Liste des Équipements ({equipmentsList.length})
        </h3>
        
        {equipmentsList.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className={`${getThemeClasses('text', 'network')} text-left py-3 px-2`}>État</th>
                  <th className={`${getThemeClasses('text', 'network')} text-left py-3 px-2`}>Nom</th>
                  <th className={`${getThemeClasses('text', 'network')} text-left py-3 px-2`}>Type</th>
                  <th className={`${getThemeClasses('text', 'network')} text-left py-3 px-2`}>IP</th>
                  <th className={`${getThemeClasses('text', 'network')} text-left py-3 px-2`}>Fabricant</th>
                  <th className={`${getThemeClasses('text', 'network')} text-left py-3 px-2`}>Modèle</th>
                </tr>
              </thead>
              <tbody>
                {equipmentsList.map((device, index) => (
                  <tr key={device.id || index} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="py-3 px-2">
                      {device.is_active ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-400" />
                      )}
                    </td>
                    <td className="py-3 px-2">
                      <div>
                        <span className={`${getThemeClasses('text', 'network')} font-medium`}>
                          {device.name}
                        </span>
                        {device.hostname && (
                          <div className={`${getThemeClasses('textSecondary', 'network')} text-xs`}>
                            {device.hostname}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className={`${getThemeClasses('text', 'network')} py-3 px-2 capitalize`}>
                      {device.device_type || 'N/A'}
                    </td>
                    <td className={`${getThemeClasses('text', 'network')} py-3 px-2 font-mono text-sm`}>
                      {device.ip_address || 'N/A'}
                    </td>
                    <td className={`${getThemeClasses('text', 'network')} py-3 px-2`}>
                      {device.manufacturer || device.vendor || 'N/A'}
                    </td>
                    <td className={`${getThemeClasses('text', 'network')} py-3 px-2`}>
                      {device.model || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <Server className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className={`${getThemeClasses('text', 'network')} text-lg font-medium`}>
              Aucun équipement trouvé
            </p>
            <p className={`${getThemeClasses('textSecondary', 'network')} mt-2`}>
              Connectez vos équipements pour les voir apparaître ici
            </p>
          </div>
        )}
      </div>
    </div>
  );

  const renderGns3Projects = () => (
    <div className="space-y-6">
      <div className={`${getThemeClasses('card', 'network')} p-6`}>
        <h3 className={`${getThemeClasses('text', 'network')} text-lg font-semibold mb-4`}>
          Projets GNS3 ({projectsList.length})
        </h3>
        
        {projectsList.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projectsList.map((project, index) => (
              <div
                key={project.id || index}
                className={`p-4 rounded-lg border transition-colors cursor-pointer ${
                  project.status === 'open' 
                    ? 'bg-green-600/20 border-green-600/30' 
                    : 'bg-gray-700/30 border-gray-700'
                } ${selectedProject?.id === project.id ? 'ring-2 ring-blue-500' : ''}`}
                onClick={() => setSelectedProject(selectedProject?.id === project.id ? null : project)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Network className={`w-5 h-5 ${project.status === 'open' ? 'text-green-400' : 'text-gray-400'}`} />
                    <div>
                      <h4 className={`${getThemeClasses('text', 'network')} font-medium`}>
                        {project.name}
                      </h4>
                      <p className={`${getThemeClasses('textSecondary', 'network')} text-xs`}>
                        {project.server_name}
                      </p>
                    </div>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    project.status === 'open' 
                      ? 'bg-green-600 text-white' 
                      : 'bg-gray-600 text-gray-200'
                  }`}>
                    {project.status}
                  </span>
                </div>
                
                <div className="mt-3 grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className={`${getThemeClasses('textSecondary', 'network')}`}>Nœuds:</span>
                    <span className={`${getThemeClasses('text', 'network')} ml-1 font-medium`}>
                      {project.nodes_count || 0}
                    </span>
                  </div>
                  <div>
                    <span className={`${getThemeClasses('textSecondary', 'network')}`}>Liens:</span>
                    <span className={`${getThemeClasses('text', 'network')} ml-1 font-medium`}>
                      {project.links_count || 0}
                    </span>
                  </div>
                </div>
                
                {project.description && (
                  <p className={`${getThemeClasses('textSecondary', 'network')} text-xs mt-2 truncate`}>
                    {project.description}
                  </p>
                )}
                
                <div className={`${getThemeClasses('textSecondary', 'network')} text-xs mt-2`}>
                  Créé: {project.created_at ? new Date(project.created_at).toLocaleDateString('fr-FR') : 'N/A'}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <Network className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className={`${getThemeClasses('text', 'network')} text-lg font-medium`}>
              Aucun projet GNS3
            </p>
            <p className={`${getThemeClasses('textSecondary', 'network')} mt-2`}>
              Créez un projet dans GNS3 pour commencer
            </p>
          </div>
        )}
      </div>
      
      {/* Détails du projet sélectionné */}
      {selectedProject && (
        <div className={`${getThemeClasses('card', 'network')} p-6`}>
          <h4 className={`${getThemeClasses('text', 'network')} text-lg font-semibold mb-4`}>
            Détails du projet: {selectedProject.name}
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h5 className={`${getThemeClasses('text', 'network')} font-medium mb-2`}>Informations générales</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className={getThemeClasses('textSecondary', 'network')}>ID:</span>
                  <span className={`${getThemeClasses('text', 'network')} font-mono`}>{selectedProject.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className={getThemeClasses('textSecondary', 'network')}>Statut:</span>
                  <span className={`${getThemeClasses('text', 'network')} font-medium`}>{selectedProject.status}</span>
                </div>
                <div className="flex justify-between">
                  <span className={getThemeClasses('textSecondary', 'network')}>Serveur:</span>
                  <span className={getThemeClasses('text', 'network')}>{selectedProject.server_name}</span>
                </div>
              </div>
            </div>
            <div>
              <h5 className={`${getThemeClasses('text', 'network')} font-medium mb-2`}>Statistiques</h5>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className={getThemeClasses('textSecondary', 'network')}>Nœuds:</span>
                  <span className={getThemeClasses('text', 'network')}>{selectedProject.nodes_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className={getThemeClasses('textSecondary', 'network')}>Liens:</span>
                  <span className={getThemeClasses('text', 'network')}>{selectedProject.links_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className={getThemeClasses('textSecondary', 'network')}>Modifié:</span>
                  <span className={getThemeClasses('text', 'network')}>
                    {selectedProject.updated_at ? new Date(selectedProject.updated_at).toLocaleString('fr-FR') : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className={`min-h-screen ${getThemeClasses('background', 'network')} p-6`}>
      <div className="max-w-7xl mx-auto">
        
        {/* En-tête */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className={`${getThemeClasses('text', 'network')} text-3xl font-bold`}>
              Gestion Réseau
            </h1>
            <p className={`${getThemeClasses('textSecondary', 'network')} mt-1`}>
              Équipements et projets GNS3
            </p>
          </div>
          
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className={`flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors ${
              isRefreshing ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Actualiser</span>
          </button>
        </div>

        {/* Onglets */}
        <div className="flex space-x-1 mb-6 bg-gray-800/50 p-1 rounded-lg">
          {[
            { id: 'overview', label: 'Vue d\'ensemble', icon: Activity },
            { id: 'equipments', label: `Équipements (${totalEquipments})`, icon: Server },
            { id: 'gns3', label: `GNS3 (${totalProjects})`, icon: Network }
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                  activeTab === tab.id 
                    ? 'bg-blue-600 text-white shadow-md' 
                    : `${getThemeClasses('textSecondary', 'network')} hover:bg-gray-700/50 hover:text-white`
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Contenu des onglets */}
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'equipments' && renderEquipments()}
        {activeTab === 'gns3' && renderGns3Projects()}

        {/* Dernière mise à jour */}
        <div className={`${getThemeClasses('card', 'network')} p-4 mt-6`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <span className={`${getThemeClasses('textSecondary', 'network')} text-sm`}>
                Dernière mise à jour:
              </span>
              <span className={`${getThemeClasses('text', 'network')} text-sm`}>
                {lastUpdate.networkDevices ? 
                  new Date(lastUpdate.networkDevices).toLocaleTimeString('fr-FR') : 
                  'Jamais'
                }
              </span>
            </div>
            {(errors.networkDevices || errors.gns3Projects) && (
              <span className="text-red-400 text-sm">
                Erreur: {errors.networkDevices || errors.gns3Projects}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default NetworkSimple;