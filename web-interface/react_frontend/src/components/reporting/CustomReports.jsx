// CustomReports.jsx - Générateur de rapports personnalisés avec drag & drop
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { 
  Plus, 
  Trash2, 
  Copy, 
  Edit, 
  Save, 
  Download, 
  Upload, 
  Eye, 
  EyeOff, 
  Settings, 
  RefreshCw, 
  Search, 
  Filter, 
  Layers, 
  Move, 
  Target, 
  Gauge, 
  BarChart3, 
  PieChart, 
  LineChart, 
  Table, 
  Image, 
  Type, 
  Palette, 
  Layout, 
  Grid, 
  Maximize, 
  Minimize2, 
  RotateCw, 
  ZoomIn, 
  ZoomOut, 
  AlignLeft, 
  AlignCenter, 
  AlignRight, 
  Bold, 
  Italic, 
  Underline, 
  FileText, 
  File, 
  FileSpreadsheet, 
  FileImage, 
  Calendar, 
  Clock, 
  Users, 
  Database, 
  Server, 
  Network, 
  Shield, 
  Activity, 
  TrendingUp, 
  Award, 
  Bell, 
  Mail, 
  Share, 
  Link, 
  Globe, 
  Monitor, 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Wifi, 
  Router, 
  Terminal, 
  Code, 
  Play, 
  Pause, 
  Square, 
  X, 
  Check, 
  AlertTriangle, 
  Info, 
  CheckCircle, 
  XCircle
} from 'lucide-react';
import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart as RechartsPieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { useTheme } from '../../contexts/ThemeContext';

const CustomReports = ({ isVisible = true }) => {
  const [activeStep, setActiveStep] = useState(1);
  const [reportConfig, setReportConfig] = useState({
    name: 'Nouveau Rapport Personnalisé',
    description: '',
    category: 'custom',
    format: 'pdf',
    template: 'blank',
    layout: 'portrait',
    theme: 'modern',
    colorScheme: 'blue'
  });
  const [selectedComponents, setSelectedComponents] = useState([]);
  const [draggedComponent, setDraggedComponent] = useState(null);
  const [canvasComponents, setCanvasComponents] = useState([]);
  const [previewMode, setPreviewMode] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [savedReports, setSavedReports] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [dataSources, setDataSources] = useState([]);
  const [selectedDataSource, setSelectedDataSource] = useState('network');
  const [dateRange, setDateRange] = useState('7d');
  const [filters, setFilters] = useState({});

  const { getThemeClasses } = useTheme();
  const canvasRef = useRef(null);
  const dragOverRef = useRef(null);

  // Composants disponibles pour le générateur
  const availableComponents = [
    {
      id: 'header',
      name: 'En-tête',
      category: 'layout',
      icon: Type,
      description: 'Titre et informations générales',
      defaultProps: {
        title: 'Titre du Rapport',
        subtitle: 'Sous-titre',
        showDate: true,
        showLogo: true,
        alignment: 'center'
      }
    },
    {
      id: 'metrics-grid',
      name: 'Grille de Métriques',
      category: 'data',
      icon: Grid,
      description: 'Affichage des KPIs principaux',
      defaultProps: {
        metrics: ['cpu', 'memory', 'network', 'storage'],
        columns: 4,
        showTrend: true,
        showSparkline: false
      }
    },
    {
      id: 'line-chart',
      name: 'Graphique Linéaire',
      category: 'charts',
      icon: LineChart,
      description: 'Évolution temporelle des données',
      defaultProps: {
        dataKey: 'cpu',
        period: '24h',
        showGrid: true,
        smooth: true,
        color: '#3B82F6'
      }
    },
    {
      id: 'bar-chart',
      name: 'Graphique en Barres',
      category: 'charts',
      icon: BarChart3,
      description: 'Comparaison de valeurs',
      defaultProps: {
        dataKey: 'requests',
        groupBy: 'hour',
        showValues: true,
        color: '#10B981'
      }
    },
    {
      id: 'pie-chart',
      name: 'Graphique en Secteurs',
      category: 'charts',
      icon: PieChart,
      description: 'Répartition proportionnelle',
      defaultProps: {
        dataKey: 'distribution',
        showLabels: true,
        showPercentage: true,
        colors: ['#3B82F6', '#10B981', '#F59E0B', '#EF4444']
      }
    },
    {
      id: 'data-table',
      name: 'Tableau de Données',
      category: 'data',
      icon: Table,
      description: 'Données structurées en tableau',
      defaultProps: {
        columns: ['name', 'value', 'status'],
        sortable: true,
        filterable: false,
        pagination: true,
        pageSize: 10
      }
    },
    {
      id: 'alert-summary',
      name: 'Résumé des Alertes',
      category: 'data',
      icon: Bell,
      description: 'Synthèse des incidents et alertes',
      defaultProps: {
        severity: ['critical', 'high', 'medium'],
        groupBy: 'type',
        showTimeline: true,
        maxItems: 20
      }
    },
    {
      id: 'network-topology',
      name: 'Topologie Réseau',
      category: 'specialized',
      icon: Network,
      description: 'Carte du réseau et connexions',
      defaultProps: {
        showLabels: true,
        layout: 'hierarchical',
        showStatus: true,
        interactive: false
      }
    },
    {
      id: 'text-block',
      name: 'Bloc de Texte',
      category: 'layout',
      icon: FileText,
      description: 'Texte libre ou notes',
      defaultProps: {
        content: 'Votre texte ici...',
        fontSize: 'medium',
        alignment: 'left',
        formatting: []
      }
    },
    {
      id: 'image-block',
      name: 'Image',
      category: 'layout',
      icon: Image,
      description: 'Images et captures d\'écran',
      defaultProps: {
        src: null,
        caption: '',
        alignment: 'center',
        width: '100%'
      }
    },
    {
      id: 'divider',
      name: 'Séparateur',
      category: 'layout',
      icon: Minimize2,
      description: 'Ligne de séparation',
      defaultProps: {
        style: 'solid',
        thickness: 1,
        color: '#374151',
        margin: 20
      }
    },
    {
      id: 'footer',
      name: 'Pied de page',
      category: 'layout',
      icon: AlignCenter,
      description: 'Informations de fin de rapport',
      defaultProps: {
        showPageNumbers: true,
        showDate: true,
        customText: '',
        alignment: 'center'
      }
    }
  ];

  // Templates prédéfinis
  const reportTemplates = [
    {
      id: 'blank',
      name: 'Vierge',
      description: 'Commencer à partir de zéro',
      preview: '/templates/blank.png',
      components: []
    },
    {
      id: 'executive',
      name: 'Rapport Exécutif',
      description: 'Vue d\'ensemble pour la direction',
      preview: '/templates/executive.png',
      components: [
        { type: 'header', position: { x: 0, y: 0 } },
        { type: 'metrics-grid', position: { x: 0, y: 100 } },
        { type: 'line-chart', position: { x: 0, y: 250 } },
        { type: 'alert-summary', position: { x: 0, y: 450 } },
        { type: 'footer', position: { x: 0, y: 650 } }
      ]
    },
    {
      id: 'technical',
      name: 'Rapport Technique',
      description: 'Analyse détaillée pour les équipes techniques',
      preview: '/templates/technical.png',
      components: [
        { type: 'header', position: { x: 0, y: 0 } },
        { type: 'network-topology', position: { x: 0, y: 100 } },
        { type: 'data-table', position: { x: 0, y: 350 } },
        { type: 'bar-chart', position: { x: 0, y: 550 } },
        { type: 'footer', position: { x: 0, y: 750 } }
      ]
    },
    {
      id: 'performance',
      name: 'Performance',
      description: 'Focus sur les performances système',
      preview: '/templates/performance.png',
      components: [
        { type: 'header', position: { x: 0, y: 0 } },
        { type: 'metrics-grid', position: { x: 0, y: 100 } },
        { type: 'line-chart', position: { x: 0, y: 250 } },
        { type: 'pie-chart', position: { x: 0, y: 450 } },
        { type: 'text-block', position: { x: 0, y: 650 } },
        { type: 'footer', position: { x: 0, y: 750 } }
      ]
    },
    {
      id: 'security',
      name: 'Sécurité',
      description: 'Analyse des incidents et menaces',
      preview: '/templates/security.png',
      components: [
        { type: 'header', position: { x: 0, y: 0 } },
        { type: 'alert-summary', position: { x: 0, y: 100 } },
        { type: 'bar-chart', position: { x: 0, y: 300 } },
        { type: 'data-table', position: { x: 0, y: 500 } },
        { type: 'footer', position: { x: 0, y: 700 } }
      ]
    }
  ];

  // Sources de données disponibles
  const mockDataSources = [
    {
      id: 'network',
      name: 'Données Réseau',
      icon: Network,
      description: 'Métriques de performance réseau',
      fields: ['bandwidth', 'latency', 'packet_loss', 'uptime'],
      available: true
    },
    {
      id: 'system',
      name: 'Métriques Système',
      icon: Server,
      description: 'CPU, mémoire, stockage',
      fields: ['cpu_usage', 'memory_usage', 'disk_usage', 'load_average'],
      available: true
    },
    {
      id: 'security',
      name: 'Événements Sécurité',
      icon: Shield,
      description: 'Alertes et incidents de sécurité',
      fields: ['incidents', 'threats', 'vulnerabilities', 'compliance'],
      available: true
    },
    {
      id: 'applications',
      name: 'Applications',
      icon: Monitor,
      description: 'Performance des applications',
      fields: ['response_time', 'errors', 'requests', 'availability'],
      available: false
    },
    {
      id: 'users',
      name: 'Activité Utilisateurs',
      icon: Users,
      description: 'Connexions et usage',
      fields: ['logins', 'sessions', 'actions', 'locations'],
      available: true
    }
  ];

  // Rapports sauvegardés mockés
  const mockSavedReports = [
    {
      id: 'rpt-001',
      name: 'Rapport Mensuel Infrastructure',
      description: 'Vue d\'ensemble complète de l\'infrastructure',
      category: 'custom',
      template: 'executive',
      created: '2024-01-10T09:30:00Z',
      lastModified: '2024-01-15T14:20:00Z',
      components: 8,
      format: 'pdf',
      author: 'Jean Dupont'
    },
    {
      id: 'rpt-002',
      name: 'Analyse Performance Détaillée',
      description: 'Métriques avancées de performance',
      category: 'performance',
      template: 'technical',
      created: '2024-01-08T11:15:00Z',
      lastModified: '2024-01-12T16:45:00Z',
      components: 12,
      format: 'pdf',
      author: 'Sophie Martin'
    },
    {
      id: 'rpt-003',
      name: 'Tableau de Bord Sécurité',
      description: 'Surveillance continue des menaces',
      category: 'security',
      template: 'security',
      created: '2024-01-05T08:00:00Z',
      lastModified: '2024-01-14T10:30:00Z',
      components: 6,
      format: 'pdf',
      author: 'Marc Dubois'
    }
  ];

  // Initialisation
  useEffect(() => {
    setTemplates(reportTemplates);
    setSavedReports(mockSavedReports);
    setDataSources(mockDataSources);
  }, []);

  // Gestion du drag & drop
  const handleDragStart = (component) => {
    setDraggedComponent(component);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (!draggedComponent) return;

    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const newComponent = {
      id: `${draggedComponent.id}-${Date.now()}`,
      type: draggedComponent.id,
      name: draggedComponent.name,
      position: { x: Math.max(0, x - 50), y: Math.max(0, y - 25) },
      size: { width: 300, height: 200 },
      props: { ...draggedComponent.defaultProps },
      zIndex: canvasComponents.length
    };

    setCanvasComponents(prev => [...prev, newComponent]);
    setDraggedComponent(null);
  };

  // Gestion des composants
  const updateComponent = (componentId, updates) => {
    setCanvasComponents(prev => prev.map(comp => 
      comp.id === componentId ? { ...comp, ...updates } : comp
    ));
  };

  const removeComponent = (componentId) => {
    setCanvasComponents(prev => prev.filter(comp => comp.id !== componentId));
  };

  const duplicateComponent = (component) => {
    const newComponent = {
      ...component,
      id: `${component.type}-${Date.now()}`,
      position: {
        x: component.position.x + 20,
        y: component.position.y + 20
      },
      zIndex: canvasComponents.length
    };
    setCanvasComponents(prev => [...prev, newComponent]);
  };

  // Gestion des templates
  const applyTemplate = (template) => {
    if (template.id === 'blank') {
      setCanvasComponents([]);
    } else {
      const templateComponents = template.components.map((comp, index) => ({
        id: `${comp.type}-${Date.now()}-${index}`,
        type: comp.type,
        name: availableComponents.find(ac => ac.id === comp.type)?.name || 'Composant',
        position: comp.position,
        size: { width: 300, height: 200 },
        props: availableComponents.find(ac => ac.id === comp.type)?.defaultProps || {},
        zIndex: index
      }));
      setCanvasComponents(templateComponents);
    }
    setReportConfig(prev => ({ ...prev, template: template.id }));
  };

  // Génération du rapport
  const handleGenerateReport = useCallback(() => {
    setIsGenerating(true);
    setGenerationProgress(0);

    const interval = setInterval(() => {
      setGenerationProgress(prev => {
        const newProgress = prev + Math.random() * 15;
        if (newProgress >= 100) {
          clearInterval(interval);
          setIsGenerating(false);
          setGenerationProgress(0);
          
          // Simuler le téléchargement
          const link = document.createElement('a');
          link.href = '#';
          link.download = `${reportConfig.name}.${reportConfig.format}`;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          return 100;
        }
        return newProgress;
      });
    }, 200);
  }, [reportConfig]);

  // Sauvegarde du rapport
  const handleSaveReport = () => {
    const newReport = {
      id: `rpt-${Date.now()}`,
      name: reportConfig.name,
      description: reportConfig.description,
      category: reportConfig.category,
      template: reportConfig.template,
      created: new Date().toISOString(),
      lastModified: new Date().toISOString(),
      componentsCount: canvasComponents.length,
      format: reportConfig.format,
      author: 'Vous',
      config: reportConfig,
      components: canvasComponents
    };
    
    setSavedReports(prev => [newReport, ...prev]);
  };

  // Composant d'étape de configuration
  const ConfigurationStep = () => (
    <div className="space-y-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Configuration Générale
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-2`}>
              Nom du rapport
            </label>
            <input
              type="text"
              value={reportConfig.name}
              onChange={(e) => setReportConfig(prev => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
              placeholder="Nom du rapport"
            />
          </div>
          
          <div>
            <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-2`}>
              Catégorie
            </label>
            <select
              value={reportConfig.category}
              onChange={(e) => setReportConfig(prev => ({ ...prev, category: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            >
              <option value="custom">Personnalisé</option>
              <option value="performance">Performance</option>
              <option value="security">Sécurité</option>
              <option value="network">Réseau</option>
              <option value="executive">Exécutif</option>
            </select>
          </div>
          
          <div>
            <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-2`}>
              Format de sortie
            </label>
            <select
              value={reportConfig.format}
              onChange={(e) => setReportConfig(prev => ({ ...prev, format: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            >
              <option value="pdf">PDF - Document imprimable</option>
              <option value="html">HTML - Web interactif</option>
              <option value="docx">Word - Document éditable</option>
              <option value="xlsx">Excel - Données tabulaires</option>
            </select>
          </div>
          
          <div>
            <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-2`}>
              Thème
            </label>
            <select
              value={reportConfig.theme}
              onChange={(e) => setReportConfig(prev => ({ ...prev, theme: e.target.value }))}
              className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            >
              <option value="modern">Moderne</option>
              <option value="classic">Classique</option>
              <option value="minimal">Minimaliste</option>
              <option value="corporate">Corporate</option>
            </select>
          </div>
        </div>
        
        <div className="mt-4">
          <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-2`}>
            Description
          </label>
          <textarea
            value={reportConfig.description}
            onChange={(e) => setReportConfig(prev => ({ ...prev, description: e.target.value }))}
            className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
            rows={3}
            placeholder="Description du rapport..."
          />
        </div>
      </div>
    </div>
  );

  // Composant de sélection de template
  const TemplateStep = () => (
    <div className="space-y-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Choisir un Template
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map(template => (
            <div
              key={template.id}
              onClick={() => applyTemplate(template)}
              className={`cursor-pointer p-4 border-2 rounded-lg transition-all hover:border-blue-500 ${
                reportConfig.template === template.id 
                  ? 'border-blue-500 bg-blue-900/20' 
                  : 'border-gray-600 bg-gray-700/30'
              }`}
            >
              <div className="flex items-center space-x-3 mb-3">
                <Layout className="w-6 h-6 text-blue-400" />
                <div>
                  <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                    {template.name}
                  </h4>
                  <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                    {template.description}
                  </p>
                </div>
              </div>
              
              <div className="w-full h-32 bg-gray-800 rounded border-2 border-dashed border-gray-600 flex items-center justify-center">
                <span className="text-gray-500 text-sm">Aperçu du template</span>
              </div>
              
              <div className="mt-3 text-xs text-gray-400">
                {template.components.length} composants
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Composant de conception avec drag & drop
  const DesignStep = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Palette de composants */}
        <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
          <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
            Composants
          </h3>
          
          <div className="space-y-2">
            {Object.entries(
              availableComponents.reduce((acc, comp) => {
                if (!acc[comp.category]) acc[comp.category] = [];
                acc[comp.category].push(comp);
                return acc;
              }, {})
            ).map(([category, components]) => (
              <div key={category}>
                <h4 className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs uppercase font-medium mb-2`}>
                  {category}
                </h4>
                <div className="space-y-1">
                  {components.map(component => {
                    const Icon = component.icon;
                    return (
                      <div
                        key={component.id}
                        draggable
                        onDragStart={() => handleDragStart(component)}
                        className="flex items-center space-x-2 p-2 bg-gray-700/50 rounded cursor-move hover:bg-gray-700 transition-colors"
                      >
                        <Icon className="w-4 h-4 text-blue-400" />
                        <div>
                          <div className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                            {component.name}
                          </div>
                          <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-xs`}>
                            {component.description}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Canvas de conception */}
        <div className="lg:col-span-3">
          <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold`}>
                Canvas de Conception
              </h3>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setPreviewMode(!previewMode)}
                  className={`flex items-center space-x-2 px-3 py-1 rounded text-sm transition-colors ${
                    previewMode 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                      : 'border border-gray-600 hover:border-gray-500'
                  }`}
                >
                  {previewMode ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  <span>{previewMode ? 'Édition' : 'Aperçu'}</span>
                </button>
                <button
                  onClick={() => setCanvasComponents([])}
                  className="flex items-center space-x-2 px-3 py-1 border border-gray-600 hover:border-gray-500 rounded text-sm transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Vider</span>
                </button>
              </div>
            </div>
            
            <div
              ref={canvasRef}
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="relative w-full h-96 bg-gray-900 border-2 border-dashed border-gray-600 rounded overflow-hidden"
              style={{ minHeight: '500px' }}
            >
              {canvasComponents.length === 0 ? (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <Layout className="w-12 h-12 text-gray-500 mx-auto mb-2" />
                    <p className="text-gray-500">
                      Glissez-déposez des composants ici pour créer votre rapport
                    </p>
                  </div>
                </div>
              ) : (
                canvasComponents.map(component => (
                  <div
                    key={component.id}
                    className="absolute border border-blue-500 bg-blue-900/10 rounded p-2 cursor-move"
                    style={{
                      left: component.position.x,
                      top: component.position.y,
                      width: component.size.width,
                      height: component.size.height,
                      zIndex: component.zIndex
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-blue-400 font-medium">
                        {component.name}
                      </span>
                      <div className="flex items-center space-x-1">
                        <button
                          onClick={() => duplicateComponent(component)}
                          className="p-1 hover:bg-gray-700 rounded"
                          title="Dupliquer"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => removeComponent(component.id)}
                          className="p-1 hover:bg-gray-700 rounded text-red-400"
                          title="Supprimer"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                    <div className="text-xs text-gray-400 bg-gray-800 rounded p-2">
                      Composant: {component.type}
                    </div>
                  </div>
                ))
              )}
            </div>
            
            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-400">
                {canvasComponents.length} composant{canvasComponents.length > 1 ? 's' : ''} ajouté{canvasComponents.length > 1 ? 's' : ''}
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleSaveReport}
                  className="flex items-center space-x-2 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
                >
                  <Save className="w-4 h-4" />
                  <span>Sauvegarder</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Composant de génération
  const GenerateStep = () => (
    <div className="space-y-6">
      <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-4`}>
          Génération du Rapport
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium mb-3`}>
              Configuration Finale
            </h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Nom:</span>
                <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>{reportConfig.name}</span>
              </div>
              <div className="flex justify-between">
                <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Format:</span>
                <span className={`${getThemeClasses('text', 'dashboard')} text-sm uppercase`}>{reportConfig.format}</span>
              </div>
              <div className="flex justify-between">
                <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Template:</span>
                <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>{reportConfig.template}</span>
              </div>
              <div className="flex justify-between">
                <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Composants:</span>
                <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>{canvasComponents.length}</span>
              </div>
            </div>
          </div>
          
          <div>
            <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium mb-3`}>
              Options de Génération
            </h4>
            <div className="space-y-3">
              <div>
                <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                  Période des données
                </label>
                <select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                >
                  <option value="1d">Dernières 24 heures</option>
                  <option value="7d">7 derniers jours</option>
                  <option value="30d">30 derniers jours</option>
                  <option value="90d">90 derniers jours</option>
                </select>
              </div>
              
              <div>
                <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                  Source de données
                </label>
                <select
                  value={selectedDataSource}
                  onChange={(e) => setSelectedDataSource(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                >
                  {dataSources.filter(ds => ds.available).map(source => (
                    <option key={source.id} value={source.id}>{source.name}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
        
        {isGenerating && (
          <div className="mt-6">
            <div className="flex items-center justify-between mb-2">
              <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                Génération en cours...
              </span>
              <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                {Math.round(generationProgress)}%
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${generationProgress}%` }}
              />
            </div>
          </div>
        )}
        
        <div className="mt-6 flex justify-end space-x-3">
          <button
            onClick={handleGenerateReport}
            disabled={isGenerating || canvasComponents.length === 0}
            className="flex items-center space-x-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
              <RefreshCw className="w-5 h-5 animate-spin" />
            ) : (
              <Download className="w-5 h-5" />
            )}
            <span>
              {isGenerating ? 'Génération...' : 'Générer le Rapport'}
            </span>
          </button>
        </div>
      </div>
    </div>
  );

  // Navigation des étapes
  const steps = [
    { id: 1, name: 'Configuration', component: ConfigurationStep },
    { id: 2, name: 'Template', component: TemplateStep },
    { id: 3, name: 'Conception', component: DesignStep },
    { id: 4, name: 'Génération', component: GenerateStep }
  ];

  const ActiveStepComponent = steps.find(step => step.id === activeStep)?.component || ConfigurationStep;

  if (!isVisible) return null;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Générateur de Rapports
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Créez des rapports personnalisés avec notre outil drag & drop
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors">
            <Upload className="w-4 h-4" />
            <span>Importer</span>
          </button>
          <button className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors">
            <Plus className="w-4 h-4" />
            <span>Nouveau</span>
          </button>
        </div>
      </div>

      {/* Navigation des étapes */}
      <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
        <nav className="flex space-x-4">
          {steps.map((step, index) => (
            <button
              key={step.id}
              onClick={() => setActiveStep(step.id)}
              className={`flex items-center space-x-2 px-4 py-2 rounded transition-colors ${
                activeStep === step.id
                  ? 'bg-blue-600 text-white'
                  : activeStep > step.id
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <span className="flex items-center justify-center w-6 h-6 rounded-full border text-xs">
                {activeStep > step.id ? <Check className="w-4 h-4" /> : step.id}
              </span>
              <span>{step.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Contenu de l'étape active */}
      <ActiveStepComponent />

      {/* Navigation entre étapes */}
      <div className="flex justify-between">
        <button
          onClick={() => setActiveStep(prev => Math.max(1, prev - 1))}
          disabled={activeStep === 1}
          className="flex items-center space-x-2 px-4 py-2 border border-gray-600 hover:border-gray-500 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>← Précédent</span>
        </button>
        
        <button
          onClick={() => setActiveStep(prev => Math.min(4, prev + 1))}
          disabled={activeStep === 4}
          className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>Suivant →</span>
        </button>
      </div>
    </div>
  );
};

export default CustomReports;