// IncidentManagement.jsx - Gestion des incidents de sécurité avec workflow
import React, { useState, useEffect, useCallback } from 'react';
import { 
  AlertTriangle, 
  Clock, 
  User, 
  CheckCircle, 
  XCircle,
  Play,
  Pause,
  Edit,
  Eye,
  MessageCircle,
  Upload,
  Download,
  Search,
  Filter,
  Plus,
  ArrowRight,
  Flag,
  Calendar,
  FileText,
  Settings,
  Activity,
  AlertCircle,
  Shield,
  Target,
  Users,
  Bell
} from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const IncidentManagement = ({ isVisible = true }) => {
  const [incidents, setIncidents] = useState([]);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('created');
  const [viewMode, setViewMode] = useState('list');

  const { getThemeClasses } = useTheme();

  // États des incidents
  const incidentStatuses = {
    'new': { label: 'Nouveau', color: 'bg-blue-600', icon: Plus },
    'investigating': { label: 'En cours', color: 'bg-yellow-600', icon: Search },
    'responding': { label: 'Réponse', color: 'bg-orange-600', icon: Play },
    'resolved': { label: 'Résolu', color: 'bg-green-600', icon: CheckCircle },
    'closed': { label: 'Fermé', color: 'bg-gray-600', icon: XCircle }
  };

  // Niveaux de sévérité
  const severityLevels = {
    'critical': { label: 'Critique', color: 'text-red-400', bgColor: 'bg-red-900/30' },
    'high': { label: 'Élevée', color: 'text-orange-400', bgColor: 'bg-orange-900/30' },
    'medium': { label: 'Moyenne', color: 'text-yellow-400', bgColor: 'bg-yellow-900/30' },
    'low': { label: 'Faible', color: 'text-green-400', bgColor: 'bg-green-900/30' }
  };

  // Données mockées des incidents
  const mockIncidents = [
    {
      id: 'INC-001',
      title: 'Tentative d\'intrusion détectée',
      description: 'Tentative d\'accès non autorisé depuis l\'IP 203.0.113.15',
      severity: 'critical',
      status: 'investigating',
      assignedTo: 'admin@company.com',
      createdAt: '2024-01-15T09:30:00Z',
      updatedAt: '2024-01-15T10:15:00Z',
      source: 'IDS/IPS',
      affectedSystems: ['Web Server', 'Database'],
      actions: [
        { id: 1, type: 'created', user: 'System', timestamp: '2024-01-15T09:30:00Z', description: 'Incident créé automatiquement' },
        { id: 2, type: 'assigned', user: 'admin@company.com', timestamp: '2024-01-15T09:35:00Z', description: 'Assigné à l\'équipe sécurité' },
        { id: 3, type: 'investigating', user: 'admin@company.com', timestamp: '2024-01-15T10:15:00Z', description: 'Investigation en cours' }
      ],
      evidence: [
        { type: 'log', name: 'access.log', size: '2.1 MB', timestamp: '2024-01-15T09:30:00Z' },
        { type: 'pcap', name: 'network_capture.pcap', size: '15.3 MB', timestamp: '2024-01-15T09:30:00Z' }
      ],
      comments: [
        { id: 1, user: 'admin@company.com', timestamp: '2024-01-15T10:15:00Z', content: 'Analyse des logs en cours, source IP bloquée temporairement' }
      ]
    },
    {
      id: 'INC-002',
      title: 'Malware détecté sur workstation',
      description: 'Fichier malveillant détecté sur PC-USER-15',
      severity: 'high',
      status: 'responding',
      assignedTo: 'security@company.com',
      createdAt: '2024-01-15T08:15:00Z',
      updatedAt: '2024-01-15T11:20:00Z',
      source: 'Antivirus',
      affectedSystems: ['PC-USER-15'],
      actions: [
        { id: 1, type: 'created', user: 'Antivirus System', timestamp: '2024-01-15T08:15:00Z', description: 'Malware détecté' },
        { id: 2, type: 'investigating', user: 'security@company.com', timestamp: '2024-01-15T08:45:00Z', description: 'Analyse du fichier' },
        { id: 3, type: 'responding', user: 'security@company.com', timestamp: '2024-01-15T11:20:00Z', description: 'Isolation du poste' }
      ],
      evidence: [
        { type: 'file', name: 'malware_sample.exe', size: '1.8 MB', timestamp: '2024-01-15T08:15:00Z' }
      ],
      comments: [
        { id: 1, user: 'security@company.com', timestamp: '2024-01-15T11:20:00Z', content: 'Poste isolé du réseau, nettoyage en cours' }
      ]
    },
    {
      id: 'INC-003',
      title: 'Scan de ports suspect',
      description: 'Scan de ports détecté depuis 198.51.100.25',
      severity: 'medium',
      status: 'resolved',
      assignedTo: 'ops@company.com',
      createdAt: '2024-01-14T16:45:00Z',
      updatedAt: '2024-01-14T17:30:00Z',
      source: 'Network Monitor',
      affectedSystems: ['Firewall'],
      actions: [
        { id: 1, type: 'created', user: 'Network Monitor', timestamp: '2024-01-14T16:45:00Z', description: 'Scan détecté' },
        { id: 2, type: 'investigating', user: 'ops@company.com', timestamp: '2024-01-14T16:50:00Z', description: 'Analyse du trafic' },
        { id: 3, type: 'resolved', user: 'ops@company.com', timestamp: '2024-01-14T17:30:00Z', description: 'IP bloquée automatiquement' }
      ],
      evidence: [],
      comments: [
        { id: 1, user: 'ops@company.com', timestamp: '2024-01-14T17:30:00Z', content: 'Scan automatisé, IP ajoutée à la blacklist' }
      ]
    }
  ];

  // Initialisation des données
  useEffect(() => {
    setIncidents(mockIncidents);
  }, []);

  // Filtrage des incidents
  const filteredIncidents = incidents.filter(incident => {
    const matchesStatus = filterStatus === 'all' || incident.status === filterStatus;
    const matchesSeverity = filterSeverity === 'all' || incident.severity === filterSeverity;
    const matchesSearch = searchQuery === '' || 
      incident.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesStatus && matchesSeverity && matchesSearch;
  });

  // Tri des incidents
  const sortedIncidents = [...filteredIncidents].sort((a, b) => {
    switch (sortBy) {
      case 'created':
        return new Date(b.createdAt) - new Date(a.createdAt);
      case 'severity':
        const severityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        return severityOrder[b.severity] - severityOrder[a.severity];
      case 'status':
        return a.status.localeCompare(b.status);
      default:
        return 0;
    }
  });

  // Gestion des actions sur les incidents
  const handleStatusChange = (incidentId, newStatus) => {
    setIncidents(prev => prev.map(incident => 
      incident.id === incidentId 
        ? { 
            ...incident, 
            status: newStatus, 
            updatedAt: new Date().toISOString(),
            actions: [
              ...incident.actions,
              {
                id: incident.actions.length + 1,
                type: newStatus,
                user: 'current-user@company.com',
                timestamp: new Date().toISOString(),
                description: `Statut changé vers ${incidentStatuses[newStatus].label}`
              }
            ]
          }
        : incident
    ));
  };

  const handleAssignIncident = (incidentId, assignee) => {
    setIncidents(prev => prev.map(incident => 
      incident.id === incidentId 
        ? { 
            ...incident, 
            assignedTo: assignee,
            updatedAt: new Date().toISOString(),
            actions: [
              ...incident.actions,
              {
                id: incident.actions.length + 1,
                type: 'assigned',
                user: 'current-user@company.com',
                timestamp: new Date().toISOString(),
                description: `Assigné à ${assignee}`
              }
            ]
          }
        : incident
    ));
  };

  // Composant de filtres et recherche
  const FiltersAndSearch = () => (
    <div className="flex flex-wrap items-center gap-4 mb-6">
      <div className="relative flex-1 min-w-64">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher par titre, ID, description..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
        />
      </div>
      
      <select
        value={filterStatus}
        onChange={(e) => setFilterStatus(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les statuts</option>
        {Object.entries(incidentStatuses).map(([key, status]) => (
          <option key={key} value={key}>{status.label}</option>
        ))}
      </select>
      
      <select
        value={filterSeverity}
        onChange={(e) => setFilterSeverity(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Toutes les sévérités</option>
        {Object.entries(severityLevels).map(([key, level]) => (
          <option key={key} value={key}>{level.label}</option>
        ))}
      </select>
      
      <select
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="created">Date de création</option>
        <option value="severity">Sévérité</option>
        <option value="status">Statut</option>
      </select>
      
      <div className="flex border border-gray-600 rounded overflow-hidden">
        <button
          onClick={() => setViewMode('list')}
          className={`px-3 py-2 text-sm ${viewMode === 'list' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
        >
          Liste
        </button>
        <button
          onClick={() => setViewMode('board')}
          className={`px-3 py-2 text-sm ${viewMode === 'board' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
        >
          Tableau
        </button>
      </div>
    </div>
  );

  // Composant carte d'incident
  const IncidentCard = ({ incident }) => {
    const statusConfig = incidentStatuses[incident.status];
    const severityConfig = severityLevels[incident.severity];
    const StatusIcon = statusConfig.icon;
    
    return (
      <div 
        className={`${getThemeClasses('card', 'dashboard')} p-4 cursor-pointer hover:shadow-lg transition-all`}
        onClick={() => {
          setSelectedIncident(incident);
          setIsModalOpen(true);
        }}
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className={`px-2 py-1 text-xs font-medium rounded ${severityConfig.bgColor} ${severityConfig.color}`}>
              {severityConfig.label}
            </span>
            <span className="text-sm text-gray-400">{incident.id}</span>
          </div>
          <div className={`flex items-center space-x-1 px-2 py-1 rounded text-xs text-white ${statusConfig.color}`}>
            <StatusIcon className="w-3 h-3" />
            <span>{statusConfig.label}</span>
          </div>
        </div>
        
        <h3 className={`${getThemeClasses('text', 'dashboard')} font-medium mb-2`}>
          {incident.title}
        </h3>
        
        <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm mb-3 line-clamp-2`}>
          {incident.description}
        </p>
        
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-2">
            <User className="w-4 h-4 text-gray-400" />
            <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
              {incident.assignedTo}
            </span>
          </div>
          <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>
            {new Date(incident.createdAt).toLocaleDateString()}
          </span>
        </div>
      </div>
    );
  };

  // Vue en tableau Kanban
  const BoardView = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {Object.entries(incidentStatuses).map(([statusKey, statusConfig]) => (
        <div key={statusKey} className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <div className="flex items-center justify-between mb-4">
            <h3 className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
              {statusConfig.label}
            </h3>
            <span className={`px-2 py-1 text-xs rounded ${statusConfig.color} text-white`}>
              {sortedIncidents.filter(i => i.status === statusKey).length}
            </span>
          </div>
          
          <div className="space-y-3">
            {sortedIncidents
              .filter(incident => incident.status === statusKey)
              .map(incident => (
                <IncidentCard key={incident.id} incident={incident} />
              ))}
          </div>
        </div>
      ))}
    </div>
  );

  // Vue en liste
  const ListView = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">ID</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Titre</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Sévérité</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Assigné à</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Créé</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedIncidents.map(incident => {
              const statusConfig = incidentStatuses[incident.status];
              const severityConfig = severityLevels[incident.severity];
              const StatusIcon = statusConfig.icon;
              
              return (
                <tr key={incident.id} className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} font-mono text-sm`}>
                    {incident.id}
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} font-medium max-w-xs`}>
                    <div className="truncate">{incident.title}</div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 text-xs rounded ${severityConfig.bgColor} ${severityConfig.color}`}>
                      {severityConfig.label}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className={`flex items-center space-x-1 px-2 py-1 rounded text-xs text-white ${statusConfig.color}`}>
                      <StatusIcon className="w-3 h-3" />
                      <span>{statusConfig.label}</span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                    {incident.assignedTo}
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                    {new Date(incident.createdAt).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => {
                          setSelectedIncident(incident);
                          setIsModalOpen(true);
                        }}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Voir détails"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleStatusChange(incident.id, 'investigating')}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Prendre en charge"
                      >
                        <Play className="w-4 h-4" />
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

  // Modal de détails d'incident
  const IncidentModal = () => {
    if (!selectedIncident || !isModalOpen) return null;
    
    const statusConfig = incidentStatuses[selectedIncident.status];
    const severityConfig = severityLevels[selectedIncident.severity];
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-gray-800 rounded-lg shadow-2xl border border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between p-6 border-b border-gray-700">
            <div className="flex items-center space-x-4">
              <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
                {selectedIncident.title}
              </h2>
              <span className={`px-2 py-1 text-xs rounded ${severityConfig.bgColor} ${severityConfig.color}`}>
                {severityConfig.label}
              </span>
              <span className={`px-2 py-1 text-xs rounded text-white ${statusConfig.color}`}>
                {statusConfig.label}
              </span>
            </div>
            <button
              onClick={() => setIsModalOpen(false)}
              className="p-2 hover:bg-gray-700 rounded transition-colors"
            >
              <XCircle className="w-5 h-5" />
            </button>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Informations générales */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                  Informations
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>ID:</span>
                    <span className={`${getThemeClasses('text', 'dashboard')} font-mono`}>
                      {selectedIncident.id}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Source:</span>
                    <span className={`${getThemeClasses('text', 'dashboard')}`}>
                      {selectedIncident.source}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Assigné à:</span>
                    <span className={`${getThemeClasses('text', 'dashboard')}`}>
                      {selectedIncident.assignedTo}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Créé:</span>
                    <span className={`${getThemeClasses('text', 'dashboard')}`}>
                      {new Date(selectedIncident.createdAt).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                  Actions rapides
                </h3>
                <div className="space-y-2">
                  <select
                    value={selectedIncident.status}
                    onChange={(e) => handleStatusChange(selectedIncident.id, e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  >
                    {Object.entries(incidentStatuses).map(([key, status]) => (
                      <option key={key} value={key}>{status.label}</option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={selectedIncident.assignedTo}
                    onChange={(e) => handleAssignIncident(selectedIncident.id, e.target.value)}
                    placeholder="Assigné à..."
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>
            </div>
            
            {/* Description */}
            <div>
              <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                Description
              </h3>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm leading-relaxed`}>
                {selectedIncident.description}
              </p>
            </div>
            
            {/* Timeline des actions */}
            <div>
              <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                Timeline des actions
              </h3>
              <div className="space-y-3">
                {selectedIncident.actions.map(action => (
                  <div key={action.id} className="flex items-start space-x-3">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                          {action.description}
                        </span>
                        <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                          par {action.user}
                        </span>
                      </div>
                      <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                        {new Date(action.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Preuves */}
            {selectedIncident.evidence.length > 0 && (
              <div>
                <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-medium mb-3`}>
                  Preuves
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {selectedIncident.evidence.map((evidence, index) => (
                    <div key={index} className="flex items-center space-x-3 p-3 bg-gray-700/50 rounded">
                      <FileText className="w-5 h-5 text-blue-400" />
                      <div className="flex-1">
                        <div className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                          {evidence.name}
                        </div>
                        <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                          {evidence.size} • {new Date(evidence.timestamp).toLocaleString()}
                        </div>
                      </div>
                      <button className="p-1 hover:bg-gray-600 rounded transition-colors">
                        <Download className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Statistiques des incidents
  const IncidentStats = () => (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total</p>
            <p className="text-2xl font-bold text-blue-400">{incidents.length}</p>
          </div>
          <AlertTriangle className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Critiques</p>
            <p className="text-2xl font-bold text-red-400">
              {incidents.filter(i => i.severity === 'critical').length}
            </p>
          </div>
          <AlertCircle className="w-8 h-8 text-red-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>En cours</p>
            <p className="text-2xl font-bold text-yellow-400">
              {incidents.filter(i => ['investigating', 'responding'].includes(i.status)).length}
            </p>
          </div>
          <Activity className="w-8 h-8 text-yellow-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Résolus</p>
            <p className="text-2xl font-bold text-green-400">
              {incidents.filter(i => i.status === 'resolved').length}
            </p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
      </div>
    </div>
  );

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Gestion des Incidents
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Workflow de réponse aux incidents de sécurité
          </p>
        </div>
        
        <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
          <Plus className="w-4 h-4" />
          <span>Nouveau Incident</span>
        </button>
      </div>

      <IncidentStats />
      <FiltersAndSearch />
      
      {viewMode === 'list' ? <ListView /> : <BoardView />}
      
      <IncidentModal />
    </div>
  );
};

export default IncidentManagement;