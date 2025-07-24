// NetworkTopology.jsx - Composant pour la cartographie topologie réseau interactive
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Maximize2, 
  Minimize2, 
  RotateCcw, 
  ZoomIn, 
  ZoomOut, 
  Settings, 
  Eye, 
  EyeOff,
  Play,
  Pause,
  Router,
  Server,
  Wifi,
  Monitor,
  Network,
  Activity,
  AlertTriangle
} from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const NetworkTopology = ({ devices = [], connections = [], isVisible = true }) => {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);
  const animationRef = useRef(null);
  
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [selectedNode, setSelectedNode] = useState(null);
  const [isAnimating, setIsAnimating] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [layoutType, setLayoutType] = useState('force');
  
  const { getThemeClasses } = useTheme();

  // Données mockées pour la topologie
  const mockDevices = devices.length > 0 ? devices : [
    {
      id: 'router-1',
      name: 'Router Principal',
      type: 'Router',
      ip: '192.168.1.1',
      status: 'active',
      x: 400,
      y: 300,
      connections: ['switch-1', 'firewall-1']
    },
    {
      id: 'switch-1',
      name: 'Switch Core',
      type: 'Switch',
      ip: '192.168.1.2',
      status: 'active',
      x: 200,
      y: 200,
      connections: ['router-1', 'server-1', 'ap-1']
    },
    {
      id: 'firewall-1',
      name: 'Firewall',
      type: 'Firewall',
      ip: '192.168.1.100',
      status: 'active',
      x: 600,
      y: 200,
      connections: ['router-1', 'internet']
    },
    {
      id: 'server-1',
      name: 'File Server',
      type: 'Server',
      ip: '192.168.1.10',
      status: 'active',
      x: 100,
      y: 400,
      connections: ['switch-1']
    },
    {
      id: 'ap-1',
      name: 'Access Point',
      type: 'AccessPoint',
      ip: '192.168.1.50',
      status: 'warning',
      x: 300,
      y: 100,
      connections: ['switch-1']
    },
    {
      id: 'internet',
      name: 'Internet',
      type: 'Cloud',
      ip: 'External',
      status: 'active',
      x: 700,
      y: 50,
      connections: ['firewall-1']
    }
  ];

  const mockConnections = connections.length > 0 ? connections : [
    { source: 'router-1', target: 'switch-1', status: 'active', bandwidth: '1Gbps' },
    { source: 'router-1', target: 'firewall-1', status: 'active', bandwidth: '1Gbps' },
    { source: 'switch-1', target: 'server-1', status: 'active', bandwidth: '100Mbps' },
    { source: 'switch-1', target: 'ap-1', status: 'warning', bandwidth: '100Mbps' },
    { source: 'firewall-1', target: 'internet', status: 'active', bandwidth: '500Mbps' }
  ];

  // Configuration de rendu
  const nodeRadius = 25;
  const colors = {
    active: '#10B981',
    warning: '#F59E0B',
    critical: '#EF4444',
    inactive: '#6B7280',
    connection: '#3B82F6',
    connectionWarning: '#F59E0B',
    background: '#1F2937',
    text: '#F3F4F6'
  };

  // Icônes pour chaque type de dispositif
  const getDeviceIcon = (type) => {
    const iconMap = {
      Router: '🔀',
      Switch: '🔌',
      Server: '🖥️',
      AccessPoint: '📡',
      Firewall: '🛡️',
      Cloud: '☁️'
    };
    return iconMap[type] || '📱';
  };

  // Fonction de rendu du canvas
  const renderTopology = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const rect = canvas.getBoundingClientRect();
    
    // Ajuster la taille du canvas
    canvas.width = rect.width * devicePixelRatio;
    canvas.height = rect.height * devicePixelRatio;
    canvas.style.width = rect.width + 'px';
    canvas.style.height = rect.height + 'px';
    ctx.scale(devicePixelRatio, devicePixelRatio);

    // Effacer le canvas
    ctx.fillStyle = colors.background;
    ctx.fillRect(0, 0, rect.width, rect.height);

    // Appliquer les transformations
    ctx.save();
    ctx.translate(pan.x + rect.width / 2, pan.y + rect.height / 2);
    ctx.scale(zoom, zoom);
    ctx.translate(-rect.width / 2, -rect.height / 2);

    // Dessiner les connexions
    mockConnections.forEach(connection => {
      const sourceNode = mockDevices.find(d => d.id === connection.source);
      const targetNode = mockDevices.find(d => d.id === connection.target);
      
      if (sourceNode && targetNode) {
        ctx.beginPath();
        ctx.moveTo(sourceNode.x, sourceNode.y);
        ctx.lineTo(targetNode.x, targetNode.y);
        ctx.strokeStyle = connection.status === 'warning' ? colors.connectionWarning : colors.connection;
        ctx.lineWidth = 2;
        ctx.stroke();

        // Animation de flux de données
        if (isAnimating && connection.status === 'active') {
          const time = Date.now() / 1000;
          const progress = (time % 2) / 2;
          const flowX = sourceNode.x + (targetNode.x - sourceNode.x) * progress;
          const flowY = sourceNode.y + (targetNode.y - sourceNode.y) * progress;
          
          ctx.beginPath();
          ctx.arc(flowX, flowY, 3, 0, 2 * Math.PI);
          ctx.fillStyle = colors.connection;
          ctx.fill();
        }

        // Label de bande passante
        if (showLabels) {
          const midX = (sourceNode.x + targetNode.x) / 2;
          const midY = (sourceNode.y + targetNode.y) / 2;
          
          ctx.fillStyle = colors.text;
          ctx.font = '10px sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(connection.bandwidth, midX, midY - 5);
        }
      }
    });

    // Dessiner les nœuds
    mockDevices.forEach(device => {
      const color = colors[device.status] || colors.inactive;
      
      // Cercle du nœud
      ctx.beginPath();
      ctx.arc(device.x, device.y, nodeRadius, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
      
      // Bordure
      if (selectedNode?.id === device.id) {
        ctx.strokeStyle = '#FFFFFF';
        ctx.lineWidth = 3;
        ctx.stroke();
      }

      // Icône
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '16px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(getDeviceIcon(device.type), device.x, device.y);

      // Label
      if (showLabels) {
        ctx.fillStyle = colors.text;
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillText(device.name, device.x, device.y + nodeRadius + 5);
        
        ctx.font = '10px sans-serif';
        ctx.fillStyle = '#9CA3AF';
        ctx.fillText(device.ip, device.x, device.y + nodeRadius + 20);
      }
    });

    ctx.restore();
  }, [pan, zoom, selectedNode, isAnimating, showLabels, mockDevices, mockConnections]);

  // Animation loop
  useEffect(() => {
    const animate = () => {
      renderTopology();
      if (isAnimating) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };
    
    if (isAnimating) {
      animationRef.current = requestAnimationFrame(animate);
    } else {
      renderTopology();
    }
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isAnimating, renderTopology]);

  // Gestion des événements de souris
  const handleMouseDown = useCallback((e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Convertir les coordonnées avec les transformations
    const worldX = (x - rect.width / 2 - pan.x) / zoom + rect.width / 2;
    const worldY = (y - rect.height / 2 - pan.y) / zoom + rect.height / 2;
    
    // Vérifier si on clique sur un nœud
    const clickedNode = mockDevices.find(device => {
      const dx = worldX - device.x;
      const dy = worldY - device.y;
      return Math.sqrt(dx * dx + dy * dy) <= nodeRadius;
    });
    
    if (clickedNode) {
      setSelectedNode(clickedNode);
    } else {
      setSelectedNode(null);
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  }, [pan, zoom, mockDevices]);

  const handleMouseMove = useCallback((e) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  }, [isDragging, dragStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleWheel = useCallback((e) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom(prev => Math.max(0.5, Math.min(3, prev * delta)));
  }, []);

  // Contrôles de zoom
  const zoomIn = () => setZoom(prev => Math.min(3, prev * 1.2));
  const zoomOut = () => setZoom(prev => Math.max(0.5, prev / 1.2));
  const resetView = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setSelectedNode(null);
  };

  // Basculer plein écran
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  // Layouts automatiques
  const applyLayout = (type) => {
    setLayoutType(type);
    // Ici on pourrait implémenter différents algorithmes de layout
    // Pour l'instant, on garde les positions mockées
  };

  const ControlPanel = () => (
    <div className="absolute top-4 right-4 space-y-2">
      <div className={`${getThemeClasses('card', 'dashboard')} p-2`}>
        <div className="flex items-center space-x-1">
          <button
            onClick={zoomIn}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Zoom avant"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={zoomOut}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Zoom arrière"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={resetView}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Réinitialiser la vue"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={toggleFullscreen}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Plein écran"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>
      
      <div className={`${getThemeClasses('card', 'dashboard')} p-2`}>
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsAnimating(!isAnimating)}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Animation"
          >
            {isAnimating ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>
          <button
            onClick={() => setShowLabels(!showLabels)}
            className="p-2 hover:bg-gray-700 rounded transition-colors"
            title="Afficher/masquer les labels"
          >
            {showLabels ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );

  const NodeDetails = () => selectedNode && (
    <div className="absolute bottom-4 left-4">
      <div className={`${getThemeClasses('card', 'dashboard')} p-4 w-80`}>
        <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-2`}>
          {selectedNode.name}
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Type:</span>
            <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedNode.type}</span>
          </div>
          <div className="flex justify-between">
            <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>IP:</span>
            <span className={`${getThemeClasses('text', 'dashboard')} font-mono`}>{selectedNode.ip}</span>
          </div>
          <div className="flex justify-between">
            <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Statut:</span>
            <span className={`px-2 py-1 text-xs rounded ${
              selectedNode.status === 'active' ? 'bg-green-900/30 text-green-400' :
              selectedNode.status === 'warning' ? 'bg-yellow-900/30 text-yellow-400' :
              'bg-red-900/30 text-red-400'
            }`}>
              {selectedNode.status}
            </span>
          </div>
          <div className="flex justify-between">
            <span className={`${getThemeClasses('textSecondary', 'dashboard')}`}>Connexions:</span>
            <span className={`${getThemeClasses('text', 'dashboard')}`}>{selectedNode.connections?.length || 0}</span>
          </div>
        </div>
      </div>
    </div>
  );

  const TopologyStats = () => (
    <div className="absolute top-4 left-4">
      <div className={`${getThemeClasses('card', 'dashboard')} p-3`}>
        <div className="flex items-center space-x-4 text-sm">
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-green-400 rounded-full"></div>
            <span>{mockDevices.filter(d => d.status === 'active').length} Actifs</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
            <span>{mockDevices.filter(d => d.status === 'warning').length} Alertes</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-3 h-3 bg-blue-400 rounded-full"></div>
            <span>{mockConnections.length} Connexions</span>
          </div>
        </div>
      </div>
    </div>
  );

  if (!isVisible) return null;

  return (
    <div 
      ref={containerRef}
      className="relative w-full h-96 bg-gray-900 rounded-lg overflow-hidden border border-gray-700"
    >
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      />
      
      <TopologyStats />
      <ControlPanel />
      <NodeDetails />
    </div>
  );
};

export default NetworkTopology;