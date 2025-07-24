// SecurityRules.jsx - Gestion des règles de sécurité avec éditeur moderne
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Shield, 
  Play, 
  Pause, 
  Plus, 
  Edit, 
  Trash2, 
  Eye, 
  Save, 
  X, 
  Copy,
  Download,
  Upload,
  Settings,
  Filter,
  Search,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  FileText,
  Code,
  Database,
  Network,
  Server,
  Globe,
  Lock,
  Unlock,
  Terminal,
  Activity,
  Target,
  Clock,
  Calendar,
  Tag,
  Users,
  Monitor
} from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const SecurityRules = ({ isVisible = true }) => {
  const [rules, setRules] = useState([]);
  const [selectedRule, setSelectedRule] = useState(null);
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editorContent, setEditorContent] = useState('');
  const [editorMode, setEditorMode] = useState('create'); // 'create' ou 'edit'
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [activeTab, setActiveTab] = useState('list');

  const { getThemeClasses } = useTheme();

  // Types de règles
  const ruleTypes = {
    'suricata': { label: 'Suricata IDS', icon: Shield, color: 'bg-blue-600' },
    'firewall': { label: 'Pare-feu', icon: Lock, color: 'bg-red-600' },
    'snort': { label: 'Snort IDS', icon: Target, color: 'bg-green-600' },
    'custom': { label: 'Personnalisé', icon: Code, color: 'bg-purple-600' }
  };

  // Niveaux de priorité
  const priorityLevels = {
    'critical': { label: 'Critique', color: 'text-red-400', bgColor: 'bg-red-900/30' },
    'high': { label: 'Élevée', color: 'text-orange-400', bgColor: 'bg-orange-900/30' },
    'medium': { label: 'Moyenne', color: 'text-yellow-400', bgColor: 'bg-yellow-900/30' },
    'low': { label: 'Faible', color: 'text-green-400', bgColor: 'bg-green-900/30' }
  };

  // Données mockées des règles
  const mockRules = [
    {
      id: 'rule-001',
      name: 'Détection intrusion HTTP',
      type: 'suricata',
      category: 'Web Attack',
      priority: 'high',
      status: 'active',
      description: 'Détecte les tentatives d\'intrusion sur les serveurs web',
      source: 'any',
      destination: 'HTTP_SERVERS',
      action: 'alert',
      enabled: true,
      createdAt: '2024-01-10T10:00:00Z',
      updatedAt: '2024-01-15T14:30:00Z',
      author: 'admin@company.com',
      triggeredCount: 156,
      lastTriggered: '2024-01-15T12:45:00Z',
      content: `alert tcp any any -> $HTTP_SERVERS $HTTP_PORTS (msg:"HTTP malware detected"; flow:established,to_server; content:"malware.exe"; nocase; classtype:trojan-activity; sid:1000001; rev:1;)`
    },
    {
      id: 'rule-002',
      name: 'Blocage SSH brute force',
      type: 'firewall',
      category: 'Brute Force',
      priority: 'critical',
      status: 'active',
      description: 'Bloque les tentatives de force brute sur SSH',
      source: 'any',
      destination: 'SSH_SERVERS',
      action: 'drop',
      enabled: true,
      createdAt: '2024-01-08T09:15:00Z',
      updatedAt: '2024-01-14T16:20:00Z',
      author: 'security@company.com',
      triggeredCount: 89,
      lastTriggered: '2024-01-14T11:30:00Z',
      content: `iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --set --name SSH_BRUTE
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 4 --name SSH_BRUTE -j DROP`
    },
    {
      id: 'rule-003',
      name: 'Détection scan ports',
      type: 'suricata',
      category: 'Reconnaissance',
      priority: 'medium',
      status: 'active',
      description: 'Détecte les scans de ports suspects',
      source: 'any',
      destination: 'HOME_NET',
      action: 'alert',
      enabled: true,
      createdAt: '2024-01-05T14:20:00Z',
      updatedAt: '2024-01-12T10:45:00Z',
      author: 'ops@company.com',
      triggeredCount: 234,
      lastTriggered: '2024-01-12T15:20:00Z',
      content: `alert tcp any any -> $HOME_NET any (msg:"Port scan detected"; threshold: type threshold, track by_src, count 10, seconds 60; classtype:attempted-recon; sid:1000003; rev:1;)`
    },
    {
      id: 'rule-004',
      name: 'Blocage IP malveillantes',
      type: 'firewall',
      category: 'Blacklist',
      priority: 'high',
      status: 'active',
      description: 'Bloque les IP connues comme malveillantes',
      source: 'BLACKLIST_IPS',
      destination: 'any',
      action: 'reject',
      enabled: true,
      createdAt: '2024-01-03T11:10:00Z',
      updatedAt: '2024-01-10T13:25:00Z',
      author: 'admin@company.com',
      triggeredCount: 567,
      lastTriggered: '2024-01-10T09:15:00Z',
      content: `iptables -A INPUT -s 203.0.113.0/24 -j REJECT --reject-with icmp-port-unreachable
iptables -A INPUT -s 198.51.100.0/24 -j REJECT --reject-with icmp-port-unreachable`
    },
    {
      id: 'rule-005',
      name: 'Détection malware DNS',
      type: 'suricata',
      category: 'Malware',
      priority: 'critical',
      status: 'inactive',
      description: 'Détecte les requêtes DNS vers des domaines malveillants',
      source: 'HOME_NET',
      destination: 'any',
      action: 'alert',
      enabled: false,
      createdAt: '2024-01-01T08:30:00Z',
      updatedAt: '2024-01-05T12:00:00Z',
      author: 'security@company.com',
      triggeredCount: 45,
      lastTriggered: '2024-01-05T10:30:00Z',
      content: `alert dns $HOME_NET any -> any 53 (msg:"Malware DNS query detected"; dns.query; content:"malware-domain.com"; nocase; classtype:trojan-activity; sid:1000005; rev:1;)`
    }
  ];

  // Modèles de règles prédéfinis
  const ruleTemplates = {
    'http_intrusion': {
      name: 'Détection intrusion HTTP',
      type: 'suricata',
      content: `alert tcp any any -> $HTTP_SERVERS $HTTP_PORTS (msg:"HTTP intrusion attempt"; flow:established,to_server; content:"../"; nocase; classtype:web-application-attack; sid:1000000; rev:1;)`
    },
    'ssh_brute_force': {
      name: 'Protection SSH brute force',
      type: 'firewall',
      content: `iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --set --name SSH_BRUTE
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -m recent --update --seconds 60 --hitcount 4 --name SSH_BRUTE -j DROP`
    },
    'port_scan': {
      name: 'Détection scan de ports',
      type: 'suricata',
      content: `alert tcp any any -> $HOME_NET any (msg:"Port scan detected"; threshold: type threshold, track by_src, count 10, seconds 60; classtype:attempted-recon; sid:1000000; rev:1;)`
    },
    'malware_detection': {
      name: 'Détection malware',
      type: 'suricata',
      content: `alert tcp any any -> any any (msg:"Malware detected"; content:"malware.exe"; nocase; classtype:trojan-activity; sid:1000000; rev:1;)`
    },
    'ddos_protection': {
      name: 'Protection DDoS',
      type: 'firewall',
      content: `iptables -A INPUT -p tcp --syn -m limit --limit 1/s --limit-burst 3 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP`
    }
  };

  // Initialisation des données
  useEffect(() => {
    setRules(mockRules);
  }, []);

  // Filtrage des règles
  const filteredRules = rules.filter(rule => {
    const matchesType = filterType === 'all' || rule.type === filterType;
    const matchesStatus = filterStatus === 'all' || rule.status === filterStatus;
    const matchesPriority = filterPriority === 'all' || rule.priority === filterPriority;
    const matchesSearch = searchQuery === '' || 
      rule.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rule.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      rule.category.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesType && matchesStatus && matchesPriority && matchesSearch;
  });

  // Tri des règles
  const sortedRules = [...filteredRules].sort((a, b) => {
    switch (sortBy) {
      case 'name':
        return a.name.localeCompare(b.name);
      case 'priority':
        const priorityOrder = { critical: 4, high: 3, medium: 2, low: 1 };
        return priorityOrder[b.priority] - priorityOrder[a.priority];
      case 'triggered':
        return b.triggeredCount - a.triggeredCount;
      case 'updated':
        return new Date(b.updatedAt) - new Date(a.updatedAt);
      default:
        return 0;
    }
  });

  // Gestion des actions sur les règles
  const handleCreateRule = () => {
    setSelectedRule(null);
    setEditorMode('create');
    setEditorContent('');
    setIsEditorOpen(true);
  };

  const handleEditRule = (rule) => {
    setSelectedRule(rule);
    setEditorMode('edit');
    setEditorContent(rule.content);
    setIsEditorOpen(true);
  };

  const handleSaveRule = () => {
    if (editorMode === 'create') {
      const newRule = {
        id: `rule-${Date.now()}`,
        name: `Nouvelle règle ${rules.length + 1}`,
        type: 'suricata',
        category: 'Custom',
        priority: 'medium',
        status: 'active',
        description: 'Règle personnalisée',
        source: 'any',
        destination: 'any',
        action: 'alert',
        enabled: true,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        author: 'current-user@company.com',
        triggeredCount: 0,
        lastTriggered: null,
        content: editorContent
      };
      setRules(prev => [...prev, newRule]);
    } else {
      setRules(prev => prev.map(rule => 
        rule.id === selectedRule.id 
          ? { ...rule, content: editorContent, updatedAt: new Date().toISOString() }
          : rule
      ));
    }
    setIsEditorOpen(false);
    setEditorContent('');
    setSelectedRule(null);
  };

  const handleToggleRule = (ruleId) => {
    setRules(prev => prev.map(rule => 
      rule.id === ruleId 
        ? { ...rule, enabled: !rule.enabled, status: rule.enabled ? 'inactive' : 'active' }
        : rule
    ));
  };

  const handleDeleteRule = (ruleId) => {
    setRules(prev => prev.filter(rule => rule.id !== ruleId));
  };

  const handleApplyTemplate = (templateKey) => {
    const template = ruleTemplates[templateKey];
    if (template) {
      setEditorContent(template.content);
      setSelectedTemplate(templateKey);
    }
  };

  // Statistiques des règles
  const ruleStats = {
    total: rules.length,
    active: rules.filter(r => r.status === 'active').length,
    inactive: rules.filter(r => r.status === 'inactive').length,
    triggered: rules.reduce((sum, rule) => sum + rule.triggeredCount, 0)
  };

  // Composant des métriques
  const RuleMetrics = () => (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Total Règles</p>
            <p className="text-2xl font-bold text-blue-400">{ruleStats.total}</p>
          </div>
          <Shield className="w-8 h-8 text-blue-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Actives</p>
            <p className="text-2xl font-bold text-green-400">{ruleStats.active}</p>
          </div>
          <CheckCircle className="w-8 h-8 text-green-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Inactives</p>
            <p className="text-2xl font-bold text-gray-400">{ruleStats.inactive}</p>
          </div>
          <XCircle className="w-8 h-8 text-gray-400" />
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <div className="flex items-center justify-between">
          <div>
            <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Déclenchements</p>
            <p className="text-2xl font-bold text-orange-400">{ruleStats.triggered}</p>
          </div>
          <Activity className="w-8 h-8 text-orange-400" />
        </div>
      </div>
    </div>
  );

  // Composant de navigation par onglets
  const TabNavigation = () => (
    <div className="flex space-x-1 mb-6">
      <button
        onClick={() => setActiveTab('list')}
        className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
          activeTab === 'list' 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
        }`}
      >
        Liste des règles
      </button>
      <button
        onClick={() => setActiveTab('editor')}
        className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
          activeTab === 'editor' 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
        }`}
      >
        Éditeur
      </button>
      <button
        onClick={() => setActiveTab('templates')}
        className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
          activeTab === 'templates' 
            ? 'bg-blue-600 text-white' 
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
        }`}
      >
        Modèles
      </button>
    </div>
  );

  // Composant de filtres et recherche
  const FiltersAndSearch = () => (
    <div className="flex flex-wrap items-center gap-4 mb-6">
      <div className="relative flex-1 min-w-64">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher par nom, description, catégorie..."
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
        {Object.entries(ruleTypes).map(([key, type]) => (
          <option key={key} value={key}>{type.label}</option>
        ))}
      </select>
      
      <select
        value={filterStatus}
        onChange={(e) => setFilterStatus(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Tous les statuts</option>
        <option value="active">Actif</option>
        <option value="inactive">Inactif</option>
      </select>
      
      <select
        value={filterPriority}
        onChange={(e) => setFilterPriority(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="all">Toutes les priorités</option>
        {Object.entries(priorityLevels).map(([key, level]) => (
          <option key={key} value={key}>{level.label}</option>
        ))}
      </select>
      
      <select
        value={sortBy}
        onChange={(e) => setSortBy(e.target.value)}
        className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
      >
        <option value="name">Nom</option>
        <option value="priority">Priorité</option>
        <option value="triggered">Déclenchements</option>
        <option value="updated">Dernière modification</option>
      </select>
    </div>
  );

  // Composant de tableau des règles
  const RulesTable = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} overflow-hidden`}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Nom</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Type</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Catégorie</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Priorité</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Statut</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Déclenchements</th>
              <th className="text-left py-3 px-4 text-gray-300 font-medium text-sm">Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedRules.map(rule => {
              const typeConfig = ruleTypes[rule.type];
              const priorityConfig = priorityLevels[rule.priority];
              const TypeIcon = typeConfig.icon;
              
              return (
                <tr key={rule.id} className="border-b border-gray-700 hover:bg-gray-700/50 transition-colors">
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} font-medium`}>
                    <div className="flex items-center space-x-2">
                      <TypeIcon className="w-4 h-4 text-blue-400" />
                      <span className="max-w-xs truncate">{rule.name}</span>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 text-xs rounded text-white ${typeConfig.color}`}>
                      {typeConfig.label}
                    </span>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                    {rule.category}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`px-2 py-1 text-xs rounded ${priorityConfig.bgColor} ${priorityConfig.color}`}>
                      {priorityConfig.label}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${rule.enabled ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                      <span className={`text-xs ${rule.enabled ? 'text-green-400' : 'text-gray-400'}`}>
                        {rule.enabled ? 'Actif' : 'Inactif'}
                      </span>
                    </div>
                  </td>
                  <td className={`py-3 px-4 ${getThemeClasses('text', 'dashboard')} text-sm font-medium`}>
                    {rule.triggeredCount}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditRule(rule)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title="Modifier"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleToggleRule(rule.id)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors"
                        title={rule.enabled ? 'Désactiver' : 'Activer'}
                      >
                        {rule.enabled ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      </button>
                      <button
                        onClick={() => handleDeleteRule(rule.id)}
                        className="p-1.5 rounded hover:bg-gray-700 transition-colors text-red-400"
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

  // Composant d'éditeur de règles
  const RuleEditor = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
          {editorMode === 'create' ? 'Nouvelle règle' : `Modifier: ${selectedRule?.name}`}
        </h3>
        <div className="flex items-center space-x-2">
          <select
            value={selectedTemplate}
            onChange={(e) => handleApplyTemplate(e.target.value)}
            className="px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
          >
            <option value="">Choisir un modèle</option>
            {Object.entries(ruleTemplates).map(([key, template]) => (
              <option key={key} value={key}>{template.name}</option>
            ))}
          </select>
          <button
            onClick={handleSaveRule}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <Save className="w-4 h-4" />
            <span>Enregistrer</span>
          </button>
          <button
            onClick={() => setIsEditorOpen(false)}
            className="flex items-center space-x-2 px-4 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors"
          >
            <X className="w-4 h-4" />
            <span>Annuler</span>
          </button>
        </div>
      </div>
      
      <div className="mb-4">
        <textarea
          value={editorContent}
          onChange={(e) => setEditorContent(e.target.value)}
          placeholder="Saisissez votre règle de sécurité ici..."
          className="w-full h-64 p-4 bg-gray-900 border border-gray-600 rounded font-mono text-sm text-gray-100 focus:border-blue-500 focus:outline-none resize-none"
        />
      </div>
      
      <div className="text-sm text-gray-400">
        <p>Conseils :</p>
        <ul className="list-disc list-inside mt-1 space-y-1">
          <li>Utilisez des modèles prédéfinis pour commencer rapidement</li>
          <li>Testez vos règles dans un environnement de développement</li>
          <li>Documentez vos règles personnalisées avec des commentaires</li>
          <li>Vérifiez la syntaxe avant de sauvegarder</li>
        </ul>
      </div>
    </div>
  );

  // Composant des modèles de règles
  const RuleTemplates = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
        Modèles de règles prédéfinis
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(ruleTemplates).map(([key, template]) => {
          const typeConfig = ruleTypes[template.type];
          const TypeIcon = typeConfig.icon;
          
          return (
            <div 
              key={key}
              className="p-4 border border-gray-700 rounded-lg hover:bg-gray-700/50 transition-colors cursor-pointer"
              onClick={() => {
                setEditorContent(template.content);
                setActiveTab('editor');
              }}
            >
              <div className="flex items-center space-x-3 mb-2">
                <TypeIcon className="w-5 h-5 text-blue-400" />
                <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                  {template.name}
                </h4>
              </div>
              <div className="flex items-center space-x-2 mb-2">
                <span className={`px-2 py-1 text-xs rounded text-white ${typeConfig.color}`}>
                  {typeConfig.label}
                </span>
              </div>
              <div className="bg-gray-900 rounded p-3 mt-2">
                <code className="text-xs text-gray-300">
                  {template.content.split('\n')[0]}...
                </code>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Règles de Sécurité
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Gestion et édition des règles de sécurité
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
          <button 
            onClick={handleCreateRule}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            <Plus className="w-4 h-4" />
            <span>Nouvelle règle</span>
          </button>
        </div>
      </div>

      <RuleMetrics />
      <TabNavigation />
      
      {activeTab === 'list' && (
        <>
          <FiltersAndSearch />
          <RulesTable />
        </>
      )}
      
      {activeTab === 'editor' && <RuleEditor />}
      {activeTab === 'templates' && <RuleTemplates />}
    </div>
  );
};

export default SecurityRules;