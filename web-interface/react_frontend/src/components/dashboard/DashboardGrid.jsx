// DashboardGrid.jsx - Grille personnalisable avec drag & drop pour widgets
import React, { useState, useEffect, useCallback } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import { Settings, Edit3, Save, X, RotateCcw, Plus } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import { 
  NetworkStatusWidget, 
  TrafficChartWidget, 
  AlertsListWidget, 
  SystemHealthWidget,
  BandwidthWidget,
  DeviceCountWidget
} from './widgets';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import '../../styles/dashboard-grid.css';

const ResponsiveGridLayout = WidthProvider(Responsive);

const DashboardGrid = ({ 
  widgets = [], 
  onLayoutChange, 
  onWidgetAdd, 
  onWidgetRemove,
  onWidgetUpdate,
  defaultLayouts = {},
  isEditable = true 
}) => {
  const [layouts, setLayouts] = useState(defaultLayouts);
  const [isEditMode, setIsEditMode] = useState(false);
  const [availableWidgets, setAvailableWidgets] = useState([]);
  const { getThemeClasses } = useTheme();

  // Widgets disponibles pour ajout
  const widgetTypes = [
    { 
      id: 'network-status', 
      name: 'Statut Réseau', 
      defaultSize: { w: 4, h: 4 },
      component: 'NetworkStatusWidget',
      mockData: {
        status: 'En ligne',
        color: 'green',
        activeDevices: 18,
        totalDevices: 20,
        trend: 'up'
      }
    },
    { 
      id: 'traffic-chart', 
      name: 'Graphique Trafic', 
      defaultSize: { w: 6, h: 4 },
      component: 'TrafficChartWidget',
      mockData: [
        { time: '14:00', upload: 45, download: 67 },
        { time: '14:15', upload: 52, download: 73 },
        { time: '14:30', upload: 38, download: 59 },
        { time: '14:45', upload: 65, download: 82 }
      ]
    },
    { 
      id: 'alerts-list', 
      name: 'Liste Alertes', 
      defaultSize: { w: 4, h: 5 },
      component: 'AlertsListWidget',
      mockData: [
        { id: 1, type: 'Connexion suspecte', niveau: 'critique', heure: '14:32' },
        { id: 2, type: 'CPU élevé', niveau: 'warning', heure: '14:15' },
        { id: 3, type: 'Disque plein', niveau: 'warning', heure: '13:45' }
      ]
    },
    { 
      id: 'system-health', 
      name: 'Santé Système', 
      defaultSize: { w: 4, h: 4 },
      component: 'SystemHealthWidget',
      mockData: {
        cpu: 45,
        memory: 62,
        disk: 78,
        uptime: '99.8%'
      }
    },
    { 
      id: 'bandwidth-usage', 
      name: 'Bande Passante', 
      defaultSize: { w: 4, h: 3 },
      component: 'BandwidthWidget',
      mockData: {
        current: 145.7,
        max: 200,
        unit: 'Mbps'
      }
    },
    { 
      id: 'device-count', 
      name: 'Appareils Connectés', 
      defaultSize: { w: 3, h: 3 },
      component: 'DeviceCountWidget',
      mockData: {
        total: 42,
        online: 38,
        offline: 4,
        new: 2
      }
    },
    {
      id: 'performance-metrics',
      name: 'Métriques Performance',
      defaultSize: { w: 4, h: 4 },
      component: 'SystemHealthWidget',
      mockData: {
        cpu: 34,
        memory: 56,
        disk: 67,
        uptime: '99.9%'
      }
    }
  ];

  // Layouts par défaut pour différentes tailles d'écran
  const getDefaultLayouts = () => {
    // Générer les layouts en fonction des widgets existants
    const widgetIds = widgets.map(w => w.id);
    
    return {
      lg: widgetIds.map((id, index) => ({
        i: id,
        x: (index % 3) * 4,
        y: Math.floor(index / 3) * 4,
        w: 4,
        h: 4
      })),
      md: widgetIds.map((id, index) => ({
        i: id,
        x: (index % 2) * 5,
        y: Math.floor(index / 2) * 4,
        w: 5,
        h: 4
      })),
      sm: widgetIds.map((id, index) => ({
        i: id,
        x: 0,
        y: index * 4,
        w: 6,
        h: 4
      }))
    };
  };

  // Charger les layouts sauvegardés ou utiliser les valeurs par défaut
  useEffect(() => {
    if (widgets.length > 0) {
      const savedLayouts = localStorage.getItem('dashboard-layouts');
      if (savedLayouts) {
        try {
          const parsedLayouts = JSON.parse(savedLayouts);
          // Vérifier que les layouts correspondent aux widgets actuels
          const currentWidgetIds = widgets.map(w => w.id);
          
          // Filtrer les layouts pour ne garder que les widgets existants
          const filteredLayouts = {};
          Object.keys(parsedLayouts).forEach(breakpoint => {
            filteredLayouts[breakpoint] = parsedLayouts[breakpoint].filter(item => 
              currentWidgetIds.includes(item.i)
            );
          });
          
          // Générer les layouts pour les nouveaux widgets
          const existingIds = filteredLayouts.lg ? filteredLayouts.lg.map(item => item.i) : [];
          const newWidgets = widgets.filter(w => !existingIds.includes(w.id));
          
          if (newWidgets.length > 0) {
            const defaultLayoutsForNew = getDefaultLayouts();
            Object.keys(filteredLayouts).forEach(breakpoint => {
              const newLayouts = defaultLayoutsForNew[breakpoint].filter(item => 
                newWidgets.map(w => w.id).includes(item.i)
              );
              filteredLayouts[breakpoint] = [...filteredLayouts[breakpoint], ...newLayouts];
            });
          }
          
          setLayouts(filteredLayouts);
          localStorage.setItem('dashboard-layouts', JSON.stringify(filteredLayouts));
        } catch (error) {
          console.error('Erreur lors du chargement des layouts:', error);
          const defaultLayouts = getDefaultLayouts();
          setLayouts(defaultLayouts);
        }
      } else {
        const defaultLayouts = getDefaultLayouts();
        setLayouts(defaultLayouts);
      }
    } else {
      // Aucun widget, layouts vides
      setLayouts({ lg: [], md: [], sm: [] });
    }
  }, [widgets]);

  // Sauvegarder les layouts
  const saveLayouts = useCallback((newLayouts) => {
    setLayouts(newLayouts);
    localStorage.setItem('dashboard-layouts', JSON.stringify(newLayouts));
    if (onLayoutChange) {
      onLayoutChange(newLayouts);
    }
  }, [onLayoutChange]);

  // Gérer les changements de layout
  const handleLayoutChange = useCallback((layout, layouts) => {
    if (isEditMode) {
      saveLayouts(layouts);
    }
  }, [isEditMode, saveLayouts]);

  // Ajouter un widget
  const handleAddWidget = (widgetType) => {
    const newWidget = {
      id: `${widgetType.id}-${Date.now()}`,
      type: widgetType.id,
      title: widgetType.name,
      component: widgetType.component,
      data: widgetType.mockData || {},
      size: widgetType.defaultSize
    };
    
    if (onWidgetAdd) {
      onWidgetAdd(newWidget);
    }
  };

  // Supprimer un widget
  const handleRemoveWidget = (widgetId) => {
    console.log('DashboardGrid: Suppression du widget', widgetId);
    
    // Appeler la fonction parent pour supprimer le widget
    if (onWidgetRemove) {
      onWidgetRemove(widgetId);
    }
    
    // Mettre à jour les layouts localement aussi
    const newLayouts = {};
    Object.keys(layouts).forEach(breakpoint => {
      if (layouts[breakpoint]) {
        newLayouts[breakpoint] = layouts[breakpoint].filter(item => item.i !== widgetId);
      }
    });
    setLayouts(newLayouts);
  };

  // Réinitialiser les layouts
  const resetLayouts = () => {
    if (widgets.length > 0) {
      const defaultLayouts = getDefaultLayouts();
      setLayouts(defaultLayouts);
      localStorage.setItem('dashboard-layouts', JSON.stringify(defaultLayouts));
      if (onLayoutChange) {
        onLayoutChange(defaultLayouts);
      }
    }
  };

  // Barre d'outils d'édition
  const EditToolbar = () => (
    <div className={`fixed top-20 right-4 z-50 ${getThemeClasses('card', 'dashboard')} p-3 shadow-lg border-l-4 border-blue-500`}>
      <div className="flex items-center space-x-3 mb-3">
        <Edit3 className="w-5 h-5 text-blue-400" />
        <h3 className={`${getThemeClasses('text', 'dashboard')} font-semibold`}>Mode Édition</h3>
      </div>
      
      <div className="space-y-2">
        <button
          onClick={() => setIsEditMode(false)}
          className="w-full flex items-center space-x-2 px-3 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
        >
          <Save className="w-4 h-4" />
          <span>Sauvegarder</span>
        </button>
        
        <button
          onClick={resetLayouts}
          className="w-full flex items-center space-x-2 px-3 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700 transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          <span>Réinitialiser</span>
        </button>
        
        <button
          onClick={() => setIsEditMode(false)}
          className="w-full flex items-center space-x-2 px-3 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
        >
          <X className="w-4 h-4" />
          <span>Annuler</span>
        </button>
      </div>

      {/* Widgets disponibles */}
      <div className="mt-4 pt-3 border-t border-gray-600">
        <h4 className={`${getThemeClasses('text', 'dashboard')} text-sm font-medium mb-2`}>
          Ajouter Widget
        </h4>
        <div className="space-y-1">
          {widgetTypes.map(widgetType => (
            <button
              key={widgetType.id}
              onClick={() => handleAddWidget(widgetType)}
              className="w-full flex items-center space-x-2 px-2 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-3 h-3" />
              <span>{widgetType.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="relative">
      {/* Bouton pour activer le mode édition */}
      {isEditable && !isEditMode && (
        <div className="flex justify-end mb-4">
          <button
            onClick={() => setIsEditMode(true)}
            className="flex items-center space-x-2 px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            <Settings className="w-4 h-4" />
            <span>Personnaliser</span>
          </button>
        </div>
      )}

      {/* Toolbar d'édition */}
      {isEditMode && <EditToolbar />}

      {/* Classes pour le mode édition */}
      <div className={`${isEditMode ? 'ring-2 ring-blue-500 ring-opacity-50 rounded-lg p-2' : ''}`}>
        <ResponsiveGridLayout
          className="layout"
          layouts={layouts}
          onLayoutChange={handleLayoutChange}
          breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
          cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
          rowHeight={80}
          isDraggable={isEditMode}
          isResizable={isEditMode}
          compactType="vertical"
          preventCollision={false}
          margin={[16, 16]}
          containerPadding={[0, 0]}
          useCSSTransforms={true}
        >
          {widgets.map((widget) => {
            // Map des composants
            const componentMap = {
              'NetworkStatusWidget': NetworkStatusWidget,
              'TrafficChartWidget': TrafficChartWidget, 
              'AlertsListWidget': AlertsListWidget,
              'SystemHealthWidget': SystemHealthWidget,
              'BandwidthWidget': BandwidthWidget,
              'DeviceCountWidget': DeviceCountWidget
            };
            
            const WidgetComponent = componentMap[widget.component] || componentMap[widget.type];
            
            return (
              <div 
                key={widget.id} 
                className={`${getThemeClasses('card', 'dashboard')} relative overflow-hidden ${
                  isEditMode ? 'ring-2 ring-blue-400 ring-opacity-30' : ''
                }`}
              >
                {/* Bouton de suppression en mode édition */}
                {isEditMode && (
                  <button
                    onClick={() => handleRemoveWidget(widget.id)}
                    className="absolute top-2 right-2 z-10 p-1 bg-red-600 text-white rounded-full hover:bg-red-700 transition-colors shadow-lg"
                  >
                    <X className="w-3 h-3" />
                  </button>
                )}
                
                {/* Titre du widget */}
                <div className="px-3 py-2 border-b border-gray-700">
                  <h4 className={`${getThemeClasses('text', 'dashboard')} font-medium text-sm`}>
                    {widget.title || widget.name || widget.type}
                  </h4>
                </div>
                
                {/* Contenu du widget */}
                <div className="h-full p-3 overflow-hidden" style={{ height: 'calc(100% - 40px)' }}>
                  {WidgetComponent ? (
                    <WidgetComponent 
                      data={widget.data || widget.mockData || {}} 
                      config={widget.config}
                      isCompact={true}
                    />
                  ) : widget.children ? (
                    widget.children
                  ) : (
                    <div className="h-full flex items-center justify-center">
                      <div className="text-center">
                        <div className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm mb-2`}>
                          Widget: {widget.type}
                        </div>
                        <div className={`${getThemeClasses('text', 'dashboard')} font-medium`}>
                          {widget.title || 'Configuration requise'}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </ResponsiveGridLayout>
      </div>

      {/* Indicateur du mode édition */}
      {isEditMode && (
        <div className="fixed bottom-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-4 py-2 rounded-full shadow-lg">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            <span className="text-sm font-medium">Mode Édition Actif</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardGrid;