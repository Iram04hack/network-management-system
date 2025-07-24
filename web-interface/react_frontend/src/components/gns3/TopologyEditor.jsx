// TopologyEditor.jsx - Éditeur de topologie GNS3 moderne et interactif
import React, { useState, useEffect, useRef, useCallback } from 'react';
import { 
  Plus, 
  Trash2, 
  Copy, 
  Edit, 
  Save, 
  Undo, 
  Redo, 
  ZoomIn, 
  ZoomOut, 
  Move, 
  Link, 
  Unlink, 
  Settings, 
  Play, 
  Pause, 
  Square, 
  Eye, 
  EyeOff, 
  Target, 
  Layers, 
  Grid, 
  Maximize, 
  Minimize, 
  RotateCw, 
  RefreshCw, 
  Download, 
  Upload, 
  Search, 
  Filter, 
  Router, 
  Monitor, 
  Server, 
  Wifi, 
  Network, 
  Terminal, 
  Shield, 
  Globe, 
  Database, 
  Cpu, 
  HardDrive, 
  Activity, 
  Gauge, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Info, 
  X, 
  MousePointer, 
  Hand, 
  Crosshair
} from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

const TopologyEditor = ({ isVisible = true, projectId = null, onSave = null }) => {
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [selectedNodes, setSelectedNodes] = useState([]);
  const [selectedLinks, setSelectedLinks] = useState([]);
  const [draggedNode, setDraggedNode] = useState(null);
  const [connectionMode, setConnectionMode] = useState(false);
  const [connectionStart, setConnectionStart] = useState(null);
  const [tool, setTool] = useState('select'); // 'select', 'move', 'link', 'delete'
  const [zoomLevel, setZoomLevel] = useState(100);
  const [showGrid, setShowGrid] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showPorts, setShowPorts] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [history, setHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const [templates, setTemplates] = useState([]);
  const [nodeDetailsPanel, setNodeDetailsPanel] = useState(null);
  const [linkDetailsPanel, setLinkDetailsPanel] = useState(null);
  const [snapToGrid, setSnapToGrid] = useState(true);
  const [autoLayout, setAutoLayout] = useState(false);

  const { getThemeClasses } = useTheme();
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Types de nœuds disponibles
  const nodeTypes = {
    router: { 
      icon: Router, 
      color: '#3B82F6', 
      label: 'Routeur', 
      defaultPorts: ['GigabitEthernet0/0', 'GigabitEthernet0/1', 'Serial0/0', 'Serial0/1'] 
    },
    switch: { 
      icon: Network, 
      color: '#10B981', 
      label: 'Switch', 
      defaultPorts: ['FastEthernet0/1', 'FastEthernet0/2', 'FastEthernet0/3', 'FastEthernet0/4'] 
    },
    firewall: { 
      icon: Shield, 
      color: '#EF4444', 
      label: 'Firewall', 
      defaultPorts: ['inside', 'outside', 'dmz'] 
    },
    server: { 
      icon: Server, 
      color: '#8B5CF6', 
      label: 'Serveur', 
      defaultPorts: ['eth0'] 
    },
    host: { 
      icon: Monitor, 
      color: '#F59E0B', 
      label: 'Hôte', 
      defaultPorts: ['eth0'] 
    },
    wireless: { 
      icon: Wifi, 
      color: '#06B6D4', 
      label: 'Point d\'accès', 
      defaultPorts: ['wlan0', 'eth0'] 
    },
    cloud: { 
      icon: Globe, 
      color: '#6B7280', 
      label: 'Cloud', 
      defaultPorts: ['eth0'] 
    }
  };

  // Templates mockés
  const mockTemplates = [
    { id: 'cisco-7200', name: 'Cisco 7200', type: 'router', category: 'Cisco' },
    { id: 'cisco-switch', name: 'Cisco Switch', type: 'switch', category: 'Cisco' },
    { id: 'pfsense', name: 'pfSense', type: 'firewall', category: 'Security' },
    { id: 'ubuntu-server', name: 'Ubuntu Server', type: 'server', category: 'Linux' },
    { id: 'windows-pc', name: 'Windows PC', type: 'host', category: 'Windows' },
    { id: 'cisco-ap', name: 'Cisco AP', type: 'wireless', category: 'Cisco' },
    { id: 'nat-cloud', name: 'NAT Cloud', type: 'cloud', category: 'Cloud' }
  ];

  // Nœuds mockés
  const mockNodes = [
    {
      id: 'node-1',
      name: 'Router-1',
      type: 'router',
      template: 'cisco-7200',
      x: 200,
      y: 150,
      status: 'started',
      ports: [
        { name: 'GigabitEthernet0/0', status: 'up', connected: true },
        { name: 'GigabitEthernet0/1', status: 'down', connected: false },
        { name: 'Serial0/0', status: 'up', connected: true },
        { name: 'Serial0/1', status: 'down', connected: false }
      ],
      console: 5000,
      properties: {
        platform: 'c7200',
        image: 'c7200-advipservicesk9-mz.152-4.S5.bin',
        ram: 512,
        nvram: 256,
        disk0: 64,
        disk1: 0
      }
    },
    {
      id: 'node-2',
      name: 'Switch-1',
      type: 'switch',
      template: 'cisco-switch',
      x: 400,
      y: 150,
      status: 'started',
      ports: [
        { name: 'FastEthernet0/1', status: 'up', connected: true },
        { name: 'FastEthernet0/2', status: 'up', connected: true },
        { name: 'FastEthernet0/3', status: 'down', connected: false },
        { name: 'FastEthernet0/4', status: 'down', connected: false }
      ],
      console: 5001,
      properties: {
        model: 'c3725',
        ios: 'c3725-advipservicesk9-mz.124-15.T14.bin',
        ram: 128
      }
    },
    {
      id: 'node-3',
      name: 'PC-1',
      type: 'host',
      template: 'windows-pc',
      x: 600,
      y: 150,
      status: 'stopped',
      ports: [
        { name: 'eth0', status: 'down', connected: true }
      ],
      console: 5002,
      properties: {
        os: 'Windows 10',
        ram: 2048,
        disk: 50
      }
    },
    {
      id: 'node-4',
      name: 'Firewall-1',
      type: 'firewall',
      template: 'pfsense',
      x: 200,
      y: 300,
      status: 'started',
      ports: [
        { name: 'inside', status: 'up', connected: true },
        { name: 'outside', status: 'up', connected: false },
        { name: 'dmz', status: 'down', connected: false }
      ],
      console: 5003,
      properties: {
        version: '2.6.0',
        ram: 1024,
        disk: 20
      }
    }
  ];

  // Liens mockés
  const mockLinks = [
    {
      id: 'link-1',
      source: 'node-1',
      target: 'node-2',
      sourcePort: 'GigabitEthernet0/0',
      targetPort: 'FastEthernet0/1',
      type: 'ethernet',
      status: 'up',
      properties: {
        bandwidth: '1000Mbps',
        latency: '1ms',
        loss: '0%'
      }
    },
    {
      id: 'link-2',
      source: 'node-2',
      target: 'node-3',
      sourcePort: 'FastEthernet0/2',
      targetPort: 'eth0',
      type: 'ethernet',
      status: 'up',
      properties: {
        bandwidth: '100Mbps',
        latency: '2ms',
        loss: '0%'
      }
    },
    {
      id: 'link-3',
      source: 'node-1',
      target: 'node-4',
      sourcePort: 'Serial0/0',
      targetPort: 'inside',
      type: 'serial',
      status: 'up',
      properties: {
        bandwidth: '2Mbps',
        latency: '10ms',
        loss: '0%'
      }
    }
  ];

  // Initialisation
  useEffect(() => {
    setNodes(mockNodes);
    setLinks(mockLinks);
    setTemplates(mockTemplates);
    saveToHistory();
  }, []);

  // Fonctions utilitaires
  const saveToHistory = useCallback(() => {
    const state = { nodes, links };
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(state);
    setHistory(newHistory);
    setHistoryIndex(newHistory.length - 1);
  }, [nodes, links, history, historyIndex]);

  const undo = useCallback(() => {
    if (historyIndex > 0) {
      const previousState = history[historyIndex - 1];
      setNodes(previousState.nodes);
      setLinks(previousState.links);
      setHistoryIndex(historyIndex - 1);
    }
  }, [history, historyIndex]);

  const redo = useCallback(() => {
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1];
      setNodes(nextState.nodes);
      setLinks(nextState.links);
      setHistoryIndex(historyIndex + 1);
    }
  }, [history, historyIndex]);

  const snapToGridValue = useCallback((value) => {
    if (!snapToGrid) return value;
    const gridSize = 20;
    return Math.round(value / gridSize) * gridSize;
  }, [snapToGrid]);

  const getNodeIcon = (type) => {
    return nodeTypes[type]?.icon || Router;
  };

  const getNodeColor = (type) => {
    return nodeTypes[type]?.color || '#3B82F6';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'started': return '#10B981';
      case 'stopped': return '#EF4444';
      case 'suspended': return '#F59E0B';
      default: return '#6B7280';
    }
  };

  // Gestionnaires d'événements
  const handleNodeClick = (node, event) => {
    event.stopPropagation();
    
    if (tool === 'select') {
      if (event.ctrlKey) {
        setSelectedNodes(prev => 
          prev.includes(node.id) 
            ? prev.filter(id => id !== node.id)
            : [...prev, node.id]
        );
      } else {
        setSelectedNodes([node.id]);
      }
    } else if (tool === 'link') {
      if (!connectionStart) {
        setConnectionStart(node.id);
      } else if (connectionStart !== node.id) {
        createLink(connectionStart, node.id);
        setConnectionStart(null);
      }
    } else if (tool === 'delete') {
      deleteNode(node.id);
    }
  };

  const handleCanvasClick = (event) => {
    if (tool === 'select') {
      setSelectedNodes([]);
      setSelectedLinks([]);
    } else if (tool === 'link') {
      setConnectionStart(null);
    }
  };

  const handleNodeDoubleClick = (node) => {
    setNodeDetailsPanel(node);
  };

  const handleLinkClick = (link, event) => {
    event.stopPropagation();
    
    if (tool === 'select') {
      setSelectedLinks([link.id]);
    } else if (tool === 'delete') {
      deleteLink(link.id);
    }
  };

  const handleLinkDoubleClick = (link) => {
    setLinkDetailsPanel(link);
  };

  const handleNodeDragStart = (node, event) => {
    if (tool === 'move' || tool === 'select') {
      setDraggedNode(node);
    }
  };

  const handleNodeDrag = (node, event) => {
    if (draggedNode && (tool === 'move' || tool === 'select')) {
      const rect = containerRef.current.getBoundingClientRect();
      const x = snapToGridValue(event.clientX - rect.left);
      const y = snapToGridValue(event.clientY - rect.top);
      
      setNodes(prev => prev.map(n => 
        n.id === node.id ? { ...n, x, y } : n
      ));
    }
  };

  const handleNodeDragEnd = () => {
    if (draggedNode) {
      setDraggedNode(null);
      setHasChanges(true);
    }
  };

  // Actions sur les nœuds
  const createNode = (type, template, x = 100, y = 100) => {
    const nodeType = nodeTypes[type];
    const newNode = {
      id: `node-${Date.now()}`,
      name: `${nodeType.label}-${nodes.length + 1}`,
      type,
      template,
      x: snapToGridValue(x),
      y: snapToGridValue(y),
      status: 'stopped',
      ports: nodeType.defaultPorts.map(port => ({
        name: port,
        status: 'down',
        connected: false
      })),
      console: 5000 + nodes.length,
      properties: {}
    };
    
    setNodes(prev => [...prev, newNode]);
    setHasChanges(true);
    saveToHistory();
  };

  const deleteNode = (nodeId) => {
    setNodes(prev => prev.filter(n => n.id !== nodeId));
    setLinks(prev => prev.filter(l => l.source !== nodeId && l.target !== nodeId));
    setSelectedNodes(prev => prev.filter(id => id !== nodeId));
    setHasChanges(true);
    saveToHistory();
  };

  const duplicateNode = (nodeId) => {
    const node = nodes.find(n => n.id === nodeId);
    if (node) {
      const newNode = {
        ...node,
        id: `node-${Date.now()}`,
        name: `${node.name}-Copy`,
        x: node.x + 50,
        y: node.y + 50,
        status: 'stopped',
        ports: node.ports.map(port => ({
          ...port,
          connected: false
        }))
      };
      setNodes(prev => [...prev, newNode]);
      setHasChanges(true);
      saveToHistory();
    }
  };

  const startNode = (nodeId) => {
    setNodes(prev => prev.map(n => 
      n.id === nodeId ? { ...n, status: 'started' } : n
    ));
  };

  const stopNode = (nodeId) => {
    setNodes(prev => prev.map(n => 
      n.id === nodeId ? { ...n, status: 'stopped' } : n
    ));
  };

  // Actions sur les liens
  const createLink = (sourceId, targetId) => {
    const sourceNode = nodes.find(n => n.id === sourceId);
    const targetNode = nodes.find(n => n.id === targetId);
    
    if (sourceNode && targetNode) {
      const availableSourcePort = sourceNode.ports.find(p => !p.connected);
      const availableTargetPort = targetNode.ports.find(p => !p.connected);
      
      if (availableSourcePort && availableTargetPort) {
        const newLink = {
          id: `link-${Date.now()}`,
          source: sourceId,
          target: targetId,
          sourcePort: availableSourcePort.name,
          targetPort: availableTargetPort.name,
          type: 'ethernet',
          status: 'up',
          properties: {
            bandwidth: '1000Mbps',
            latency: '1ms',
            loss: '0%'
          }
        };
        
        setLinks(prev => [...prev, newLink]);
        
        // Marquer les ports comme connectés
        setNodes(prev => prev.map(n => {
          if (n.id === sourceId) {
            return {
              ...n,
              ports: n.ports.map(p => 
                p.name === availableSourcePort.name 
                  ? { ...p, connected: true, status: 'up' }
                  : p
              )
            };
          } else if (n.id === targetId) {
            return {
              ...n,
              ports: n.ports.map(p => 
                p.name === availableTargetPort.name 
                  ? { ...p, connected: true, status: 'up' }
                  : p
              )
            };
          }
          return n;
        }));
        
        setHasChanges(true);
        saveToHistory();
      }
    }
  };

  const deleteLink = (linkId) => {
    const link = links.find(l => l.id === linkId);
    if (link) {
      setLinks(prev => prev.filter(l => l.id !== linkId));
      
      // Marquer les ports comme déconnectés
      setNodes(prev => prev.map(n => {
        if (n.id === link.source) {
          return {
            ...n,
            ports: n.ports.map(p => 
              p.name === link.sourcePort 
                ? { ...p, connected: false, status: 'down' }
                : p
            )
          };
        } else if (n.id === link.target) {
          return {
            ...n,
            ports: n.ports.map(p => 
              p.name === link.targetPort 
                ? { ...p, connected: false, status: 'down' }
                : p
            )
          };
        }
        return n;
      }));
      
      setSelectedLinks(prev => prev.filter(id => id !== linkId));
      setHasChanges(true);
      saveToHistory();
    }
  };

  // Actions de contrôle
  const handleSave = () => {
    if (onSave) {
      onSave({ nodes, links });
    }
    setHasChanges(false);
  };

  const handleZoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 25, 200));
  };

  const handleZoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 25, 25));
  };

  const handleResetZoom = () => {
    setZoomLevel(100);
  };

  // Composant barre d'outils
  const Toolbar = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-4`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          {/* Outils de sélection */}
          <div className="flex border border-gray-600 rounded overflow-hidden">
            <button
              onClick={() => setTool('select')}
              className={`p-2 ${tool === 'select' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
              title="Sélectionner"
            >
              <MousePointer className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTool('move')}
              className={`p-2 ${tool === 'move' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
              title="Déplacer"
            >
              <Hand className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTool('link')}
              className={`p-2 ${tool === 'link' ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
              title="Créer lien"
            >
              <Link className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTool('delete')}
              className={`p-2 ${tool === 'delete' ? 'bg-red-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
              title="Supprimer"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <button
              onClick={undo}
              disabled={historyIndex <= 0}
              className="p-2 bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded"
              title="Annuler"
            >
              <Undo className="w-4 h-4" />
            </button>
            <button
              onClick={redo}
              disabled={historyIndex >= history.length - 1}
              className="p-2 bg-gray-800 text-gray-300 hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed rounded"
              title="Refaire"
            >
              <Redo className="w-4 h-4" />
            </button>
          </div>

          {/* Zoom */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleZoomOut}
              className="p-2 bg-gray-800 text-gray-300 hover:bg-gray-700 rounded"
              title="Zoom arrière"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span className={`${getThemeClasses('text', 'dashboard')} text-sm px-2`}>
              {zoomLevel}%
            </span>
            <button
              onClick={handleZoomIn}
              className="p-2 bg-gray-800 text-gray-300 hover:bg-gray-700 rounded"
              title="Zoom avant"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleResetZoom}
              className="p-2 bg-gray-800 text-gray-300 hover:bg-gray-700 rounded"
              title="Zoom 100%"
            >
              <Target className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Options d'affichage */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setShowGrid(!showGrid)}
              className={`p-2 rounded ${showGrid ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
              title="Afficher la grille"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowLabels(!showLabels)}
              className={`p-2 rounded ${showLabels ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
              title="Afficher les labels"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={() => setShowPorts(!showPorts)}
              className={`p-2 rounded ${showPorts ? 'bg-blue-600 text-white' : 'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}
              title="Afficher les ports"
            >
              <Target className="w-4 h-4" />
            </button>
          </div>

          {/* Actions principales */}
          <div className="flex items-center space-x-2">
            <button
              onClick={handleSave}
              disabled={!hasChanges}
              className="flex items-center space-x-2 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              <span>Sauvegarder</span>
            </button>
            <button className="flex items-center space-x-2 px-3 py-2 border border-gray-600 hover:border-gray-500 rounded">
              <Download className="w-4 h-4" />
              <span>Exporter</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  // Composant palette de nœuds
  const NodePalette = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 mb-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-3`}>
        Palette de Nœuds
      </h3>
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2">
        {Object.entries(nodeTypes).map(([type, config]) => {
          const Icon = config.icon;
          return (
            <button
              key={type}
              onClick={() => createNode(type, mockTemplates.find(t => t.type === type)?.id)}
              className="flex flex-col items-center space-y-1 p-3 bg-gray-700/50 hover:bg-gray-700 rounded transition-colors"
              title={`Ajouter ${config.label}`}
            >
              <Icon className="w-6 h-6" style={{ color: config.color }} />
              <span className="text-xs text-gray-300">{config.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );

  // Composant canvas de topologie
  const TopologyCanvas = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4 flex-1`}>
      <div 
        ref={containerRef}
        className="relative w-full h-96 bg-gray-900 rounded border border-gray-700 overflow-hidden"
        onClick={handleCanvasClick}
        style={{ 
          backgroundImage: showGrid ? 'radial-gradient(circle, #374151 1px, transparent 1px)' : 'none',
          backgroundSize: showGrid ? '20px 20px' : 'auto',
          transform: `scale(${zoomLevel / 100})`,
          transformOrigin: 'top left'
        }}
      >
        {/* Rendu des liens */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
          {links.map(link => {
            const sourceNode = nodes.find(n => n.id === link.source);
            const targetNode = nodes.find(n => n.id === link.target);
            
            if (!sourceNode || !targetNode) return null;
            
            return (
              <line
                key={link.id}
                x1={sourceNode.x + 25}
                y1={sourceNode.y + 25}
                x2={targetNode.x + 25}
                y2={targetNode.y + 25}
                stroke={link.status === 'up' ? '#10B981' : '#EF4444'}
                strokeWidth={selectedLinks.includes(link.id) ? 3 : 2}
                strokeDasharray={link.type === 'serial' ? '5,5' : 'none'}
                className="cursor-pointer pointer-events-auto"
                onClick={(e) => handleLinkClick(link, e)}
                onDoubleClick={() => handleLinkDoubleClick(link)}
              />
            );
          })}
        </svg>

        {/* Rendu des nœuds */}
        {nodes.map(node => {
          const Icon = getNodeIcon(node.type);
          const isSelected = selectedNodes.includes(node.id);
          
          return (
            <div
              key={node.id}
              className={`absolute cursor-pointer transition-all duration-200 ${
                isSelected ? 'ring-2 ring-blue-500' : ''
              }`}
              style={{
                left: node.x,
                top: node.y,
                transform: draggedNode?.id === node.id ? 'scale(1.1)' : 'scale(1)'
              }}
              onClick={(e) => handleNodeClick(node, e)}
              onDoubleClick={() => handleNodeDoubleClick(node)}
              onMouseDown={(e) => handleNodeDragStart(node, e)}
              onMouseMove={(e) => handleNodeDrag(node, e)}
              onMouseUp={handleNodeDragEnd}
            >
              <div className="relative">
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center border-2 shadow-lg"
                  style={{
                    backgroundColor: getNodeColor(node.type),
                    borderColor: getStatusColor(node.status)
                  }}
                >
                  <Icon className="w-6 h-6 text-white" />
                </div>
                
                {/* Indicateur de statut */}
                <div 
                  className="absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-gray-900"
                  style={{ backgroundColor: getStatusColor(node.status) }}
                />
                
                {/* Label */}
                {showLabels && (
                  <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-xs text-gray-300 whitespace-nowrap">
                    {node.name}
                  </div>
                )}
                
                {/* Ports */}
                {showPorts && (
                  <div className="absolute top-full left-1/2 transform -translate-x-1/2 mt-2 bg-gray-800 rounded p-1 text-xs">
                    {node.ports.map(port => (
                      <div key={port.name} className="flex items-center space-x-1">
                        <div 
                          className="w-2 h-2 rounded-full"
                          style={{ backgroundColor: port.status === 'up' ? '#10B981' : '#EF4444' }}
                        />
                        <span className="text-gray-300">{port.name}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );

  // Composant panneau de propriétés
  const PropertiesPanel = () => (
    <div className={`${getThemeClasses('card', 'dashboard')} p-4`}>
      <h3 className={`${getThemeClasses('text', 'dashboard')} text-lg font-semibold mb-3`}>
        Propriétés
      </h3>
      
      {selectedNodes.length === 1 ? (
        <div>
          {(() => {
            const node = nodes.find(n => n.id === selectedNodes[0]);
            if (!node) return null;
            
            return (
              <div className="space-y-4">
                <div>
                  <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                    Nom
                  </label>
                  <input
                    type="text"
                    value={node.name}
                    onChange={(e) => setNodes(prev => prev.map(n => 
                      n.id === node.id ? { ...n, name: e.target.value } : n
                    ))}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  />
                </div>
                
                <div>
                  <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                    Type
                  </label>
                  <select
                    value={node.type}
                    onChange={(e) => setNodes(prev => prev.map(n => 
                      n.id === node.id ? { ...n, type: e.target.value } : n
                    ))}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  >
                    {Object.entries(nodeTypes).map(([type, config]) => (
                      <option key={type} value={type}>{config.label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                    Statut
                  </label>
                  <div className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getStatusColor(node.status) }}
                    />
                    <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                      {node.status}
                    </span>
                  </div>
                </div>
                
                <div>
                  <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                    Position
                  </label>
                  <div className="flex space-x-2">
                    <input
                      type="number"
                      value={node.x}
                      onChange={(e) => setNodes(prev => prev.map(n => 
                        n.id === node.id ? { ...n, x: parseInt(e.target.value) || 0 } : n
                      ))}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                      placeholder="X"
                    />
                    <input
                      type="number"
                      value={node.y}
                      onChange={(e) => setNodes(prev => prev.map(n => 
                        n.id === node.id ? { ...n, y: parseInt(e.target.value) || 0 } : n
                      ))}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                      placeholder="Y"
                    />
                  </div>
                </div>
                
                <div>
                  <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                    Console
                  </label>
                  <input
                    type="number"
                    value={node.console}
                    onChange={(e) => setNodes(prev => prev.map(n => 
                      n.id === node.id ? { ...n, console: parseInt(e.target.value) || 0 } : n
                    ))}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  />
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => startNode(node.id)}
                    disabled={node.status === 'started'}
                    className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Play className="w-4 h-4" />
                    <span>Start</span>
                  </button>
                  <button
                    onClick={() => stopNode(node.id)}
                    disabled={node.status === 'stopped'}
                    className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Square className="w-4 h-4" />
                    <span>Stop</span>
                  </button>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={() => duplicateNode(node.id)}
                    className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded"
                  >
                    <Copy className="w-4 h-4" />
                    <span>Dupliquer</span>
                  </button>
                  <button
                    onClick={() => deleteNode(node.id)}
                    className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Supprimer</span>
                  </button>
                </div>
              </div>
            );
          })()}
        </div>
      ) : selectedLinks.length === 1 ? (
        <div>
          {(() => {
            const link = links.find(l => l.id === selectedLinks[0]);
            if (!link) return null;
            
            return (
              <div className="space-y-4">
                <div>
                  <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                    Source
                  </label>
                  <input
                    type="text"
                    value={`${nodes.find(n => n.id === link.source)?.name} (${link.sourcePort})`}
                    disabled
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded opacity-50"
                  />
                </div>
                
                <div>
                  <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                    Destination
                  </label>
                  <input
                    type="text"
                    value={`${nodes.find(n => n.id === link.target)?.name} (${link.targetPort})`}
                    disabled
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded opacity-50"
                  />
                </div>
                
                <div>
                  <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                    Type
                  </label>
                  <select
                    value={link.type}
                    onChange={(e) => setLinks(prev => prev.map(l => 
                      l.id === link.id ? { ...l, type: e.target.value } : l
                    ))}
                    className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  >
                    <option value="ethernet">Ethernet</option>
                    <option value="serial">Série</option>
                    <option value="optical">Optique</option>
                  </select>
                </div>
                
                <div>
                  <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm block mb-1`}>
                    Statut
                  </label>
                  <div className="flex items-center space-x-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: link.status === 'up' ? '#10B981' : '#EF4444' }}
                    />
                    <span className={`${getThemeClasses('text', 'dashboard')} text-sm`}>
                      {link.status}
                    </span>
                  </div>
                </div>
                
                <button
                  onClick={() => deleteLink(link.id)}
                  className="w-full flex items-center justify-center space-x-2 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Supprimer</span>
                </button>
              </div>
            );
          })()}
        </div>
      ) : (
        <div className="text-center py-8">
          <Target className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
            Sélectionnez un nœud ou un lien pour voir ses propriétés
          </p>
        </div>
      )}
    </div>
  );

  if (!isVisible) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-2xl font-bold`}>
            Éditeur de Topologie
          </h2>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Conception et édition des topologies réseau
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          {hasChanges && (
            <span className="text-orange-400 text-sm">
              Modifications non sauvegardées
            </span>
          )}
          <div className="flex items-center space-x-2">
            <label className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
              Magnétisme grille:
            </label>
            <input
              type="checkbox"
              checked={snapToGrid}
              onChange={(e) => setSnapToGrid(e.target.checked)}
              className="rounded border-gray-600 bg-gray-800 text-blue-600 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      <Toolbar />
      <NodePalette />
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3">
          <TopologyCanvas />
        </div>
        <div className="lg:col-span-1">
          <PropertiesPanel />
        </div>
      </div>
    </div>
  );
};

export default TopologyEditor;