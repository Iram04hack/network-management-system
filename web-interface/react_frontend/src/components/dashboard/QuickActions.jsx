/**
 * QuickActions - Composant de raccourcis personnalisés
 * Permet aux utilisateurs de créer et gérer des raccourcis vers les fonctionnalités critiques
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  ColorPicker,
  Row,
  Col,
  Tooltip,
  Typography,
  message,
  Dropdown,
  Menu,
  Badge,
  Avatar,
  Divider,
  Empty,
  Switch,
  InputNumber,
  List,
  Tag
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DragOutlined,
  SettingOutlined,
  StarOutlined,
  StarFilled,
  LinkOutlined,
  AppstoreOutlined,
  DashboardOutlined,
  MonitorOutlined,
  SecurityScanOutlined,
  NetworkOutlined,
  ThunderboltOutlined,
  FileTextOutlined,
  RobotOutlined,
  ToolOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  CloudOutlined,
  BugOutlined,
  ApiOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  TableOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  BellOutlined
} from '@ant-design/icons';
import { useDashboard } from '../../hooks/useDashboard';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;
const { Option } = Select;

// Configuration des icônes disponibles
const AVAILABLE_ICONS = {
  // Modules principaux
  dashboard: { icon: <DashboardOutlined />, label: 'Dashboard' },
  monitoring: { icon: <MonitorOutlined />, label: 'Monitoring' },
  security: { icon: <SecurityScanOutlined />, label: 'Sécurité' },
  network: { icon: <NetworkOutlined />, label: 'Réseau' },
  qos: { icon: <ThunderboltOutlined />, label: 'QoS' },
  reporting: { icon: <FileTextOutlined />, label: 'Rapports' },
  ai: { icon: <RobotOutlined />, label: 'IA Assistant' },
  
  // Actions communes
  settings: { icon: <SettingOutlined />, label: 'Paramètres' },
  tools: { icon: <ToolOutlined />, label: 'Outils' },
  api: { icon: <ApiOutlined />, label: 'API' },
  
  // Données et visualisations
  chart_bar: { icon: <BarChartOutlined />, label: 'Graphique en barres' },
  chart_pie: { icon: <PieChartOutlined />, label: 'Graphique circulaire' },
  chart_line: { icon: <LineChartOutlined />, label: 'Graphique linéaire' },
  table: { icon: <TableOutlined />, label: 'Tableau' },
  
  // Infrastructure
  server: { icon: <DatabaseOutlined />, label: 'Serveur' },
  cloud: { icon: <CloudOutlined />, label: 'Cloud' },
  global: { icon: <GlobalOutlined />, label: 'Global' },
  
  // Actions système
  view: { icon: <EyeOutlined />, label: 'Voir' },
  play: { icon: <PlayCircleOutlined />, label: 'Démarrer' },
  pause: { icon: <PauseCircleOutlined />, label: 'Pause' },
  reload: { icon: <ReloadOutlined />, label: 'Recharger' },
  
  // États
  warning: { icon: <WarningOutlined />, label: 'Avertissement' },
  success: { icon: <CheckCircleOutlined />, label: 'Succès' },
  alert: { icon: <BellOutlined />, label: 'Alerte' },
  bug: { icon: <BugOutlined />, label: 'Debug' }
};

// Configuration des modules et leurs actions
const MODULE_ACTIONS = {
  dashboard: [
    { key: 'view_overview', label: 'Vue d\'ensemble', path: '/dashboard' },
    { key: 'create_dashboard', label: 'Créer dashboard', path: '/dashboard/create' },
    { key: 'manage_widgets', label: 'Gérer widgets', path: '/dashboard/widgets' }
  ],
  monitoring: [
    { key: 'realtime_metrics', label: 'Métriques temps réel', path: '/monitoring' },
    { key: 'alerts', label: 'Alertes', path: '/monitoring/alerts' },
    { key: 'performance', label: 'Performance', path: '/monitoring/performance' },
    { key: 'infrastructure', label: 'Infrastructure', path: '/monitoring/infrastructure' }
  ],
  network: [
    { key: 'topology', label: 'Topologie', path: '/network/topology' },
    { key: 'devices', label: 'Équipements', path: '/network/devices' },
    { key: 'discovery', label: 'Découverte', path: '/network/discovery' }
  ],
  security: [
    { key: 'incidents', label: 'Incidents', path: '/security/incidents' },
    { key: 'rules', label: 'Règles', path: '/security/rules' },
    { key: 'vulnerabilities', label: 'Vulnérabilités', path: '/security/vulnerabilities' }
  ],
  qos: [
    { key: 'policies', label: 'Politiques', path: '/qos/policies' },
    { key: 'bandwidth', label: 'Bande passante', path: '/qos/bandwidth' },
    { key: 'sla', label: 'SLA', path: '/qos/sla' }
  ],
  reporting: [
    { key: 'generate', label: 'Générer rapport', path: '/reporting/generate' },
    { key: 'scheduled', label: 'Rapports planifiés', path: '/reporting/scheduled' },
    { key: 'analytics', label: 'Analytics', path: '/reporting/analytics' }
  ],
  ai: [
    { key: 'chat', label: 'Chat IA', path: '/ai/chat' },
    { key: 'analysis', label: 'Analyse réseau', path: '/ai/analysis' },
    { key: 'automation', label: 'Automatisation', path: '/ai/automation' }
  ]
};

// Raccourcis prédéfinis
const PRESET_SHORTCUTS = [
  {
    id: 'preset_1',
    title: 'Surveillance système',
    description: 'Métriques temps réel',
    icon: 'monitoring',
    color: '#1890ff',
    action: 'navigate',
    target: '/monitoring',
    category: 'monitoring'
  },
  {
    id: 'preset_2',
    title: 'Alertes critiques',
    description: 'Voir les alertes',
    icon: 'alert',
    color: '#ff4d4f',
    action: 'navigate',
    target: '/monitoring/alerts',
    category: 'monitoring'
  },
  {
    id: 'preset_3',
    title: 'Topologie réseau',
    description: 'Carte du réseau',
    icon: 'network',
    color: '#52c41a',
    action: 'navigate',
    target: '/network/topology',
    category: 'network'
  },
  {
    id: 'preset_4',
    title: 'Nouveau dashboard',
    description: 'Créer dashboard',
    icon: 'dashboard',
    color: '#722ed1',
    action: 'navigate',
    target: '/dashboard/create',
    category: 'dashboard'
  },
  {
    id: 'preset_5',
    title: 'Incidents sécurité',
    description: 'Gestion incidents',
    icon: 'security',
    color: '#fa541c',
    action: 'navigate',
    target: '/security/incidents',
    category: 'security'
  },
  {
    id: 'preset_6',
    title: 'Assistant IA',
    description: 'Chat intelligent',
    icon: 'ai',
    color: '#13c2c2',
    action: 'navigate',
    target: '/ai/chat',
    category: 'ai'
  }
];

const QuickActions = ({ maxItems = 8, showTitle = true, compact = false }) => {
  const [shortcuts, setShortcuts] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isPresetsVisible, setIsPresetsVisible] = useState(false);
  const [editingShortcut, setEditingShortcut] = useState(null);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  // Hook pour les appels API
  const { fetchShortcuts, saveShortcuts, isAuthenticated } = useDashboard();

  // Charger les raccourcis depuis l'API
  useEffect(() => {
    const loadShortcuts = async () => {
      if (isAuthenticated) {
        try {
          const data = await fetchShortcuts();
          setShortcuts(data || []);
        } catch (error) {
          console.error('Erreur lors du chargement des raccourcis:', error);
          // Charger les raccourcis par défaut en cas d'erreur
          setShortcuts(PRESET_SHORTCUTS.slice(0, maxItems));
        }
      }
    };

    loadShortcuts();
  }, [isAuthenticated, fetchShortcuts, maxItems]);

  // Sauvegarder les raccourcis
  const handleSaveShortcuts = useCallback(async (newShortcuts) => {
    try {
      await saveShortcuts(newShortcuts);
      setShortcuts(newShortcuts);
    } catch (error) {
      message.error('Erreur lors de la sauvegarde des raccourcis');
    }
  }, [saveShortcuts]);

  // Exécuter une action de raccourci
  const executeShortcut = useCallback((shortcut) => {
    try {
      switch (shortcut.action) {
        case 'navigate':
          navigate(shortcut.target);
          break;
        case 'api_call':
          // Appel API personnalisé
          message.info(`Exécution: ${shortcut.title}`);
          break;
        case 'command':
          // Commande système
          message.info(`Commande: ${shortcut.title}`);
          break;
        case 'external':
          // Lien externe
          window.open(shortcut.target, '_blank');
          break;
        default:
          message.warning('Action non supportée');
      }
    } catch (error) {
      message.error('Erreur lors de l\'exécution du raccourci');
    }
  }, [navigate]);

  // Ajouter un nouveau raccourci
  const addShortcut = useCallback((shortcutData) => {
    const newShortcut = {
      id: `shortcut_${Date.now()}`,
      ...shortcutData,
      createdAt: new Date().toISOString(),
      favorite: false
    };

    const newShortcuts = [...shortcuts, newShortcut];
    handleSaveShortcuts(newShortcuts);
    message.success('Raccourci ajouté avec succès');
  }, [shortcuts, handleSaveShortcuts]);

  // Modifier un raccourci
  const updateShortcut = useCallback((shortcutId, updates) => {
    const newShortcuts = shortcuts.map(s => 
      s.id === shortcutId ? { ...s, ...updates } : s
    );
    handleSaveShortcuts(newShortcuts);
    message.success('Raccourci mis à jour');
  }, [shortcuts, handleSaveShortcuts]);

  // Supprimer un raccourci
  const deleteShortcut = useCallback((shortcutId) => {
    const newShortcuts = shortcuts.filter(s => s.id !== shortcutId);
    handleSaveShortcuts(newShortcuts);
    message.success('Raccourci supprimé');
  }, [shortcuts, handleSaveShortcuts]);

  // Basculer le statut favori
  const toggleFavorite = useCallback((shortcutId) => {
    const newShortcuts = shortcuts.map(s => 
      s.id === shortcutId ? { ...s, favorite: !s.favorite } : s
    );
    handleSaveShortcuts(newShortcuts);
  }, [shortcuts, handleSaveShortcuts]);

  // Ouvrir le modal d'édition
  const openEditModal = useCallback((shortcut = null) => {
    setEditingShortcut(shortcut);
    if (shortcut) {
      form.setFieldsValue(shortcut);
    } else {
      form.resetFields();
    }
    setIsModalVisible(true);
  }, [form]);

  // Soumettre le formulaire
  const handleSubmit = useCallback(async () => {
    try {
      const values = await form.validateFields();
      
      if (editingShortcut) {
        updateShortcut(editingShortcut.id, values);
      } else {
        addShortcut(values);
      }
      
      setIsModalVisible(false);
      setEditingShortcut(null);
      form.resetFields();
    } catch (error) {
      console.error('Erreur de validation:', error);
    }
  }, [form, editingShortcut, addShortcut, updateShortcut]);

  // Ajouter un raccourci prédéfini
  const addPresetShortcut = useCallback((preset) => {
    const existingShortcut = shortcuts.find(s => s.id === preset.id);
    if (existingShortcut) {
      message.warning('Ce raccourci existe déjà');
      return;
    }
    
    addShortcut(preset);
    setIsPresetsVisible(false);
  }, [shortcuts, addShortcut]);

  // Rendu d'un raccourci
  const renderShortcut = useCallback((shortcut) => {
    const iconConfig = AVAILABLE_ICONS[shortcut.icon] || AVAILABLE_ICONS.tools;
    
    return (
      <Col xs={24} sm={12} md={8} lg={6} xl={4} key={shortcut.id}>
        <Card
          size="small"
          hoverable
          onClick={() => executeShortcut(shortcut)}
          style={{
            cursor: 'pointer',
            borderColor: shortcut.favorite ? '#faad14' : undefined,
            borderWidth: shortcut.favorite ? 2 : 1
          }}
          bodyStyle={{ padding: compact ? '8px' : '16px' }}
          actions={!compact ? [
            <Tooltip title={shortcut.favorite ? 'Retirer des favoris' : 'Ajouter aux favoris'}>
              <Button
                type="text"
                size="small"
                icon={shortcut.favorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFavorite(shortcut.id);
                }}
              />
            </Tooltip>,
            <Tooltip title="Modifier">
              <Button
                type="text"
                size="small"
                icon={<EditOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  openEditModal(shortcut);
                }}
              />
            </Tooltip>,
            <Tooltip title="Supprimer">
              <Button
                type="text"
                size="small"
                icon={<DeleteOutlined />}
                onClick={(e) => {
                  e.stopPropagation();
                  deleteShortcut(shortcut.id);
                }}
                danger
              />
            </Tooltip>
          ] : undefined}
        >
          <div style={{ textAlign: 'center' }}>
            <Avatar
              icon={iconConfig.icon}
              style={{ 
                backgroundColor: shortcut.color || '#1890ff',
                marginBottom: compact ? '4px' : '8px',
                fontSize: compact ? '16px' : '20px'
              }}
              size={compact ? 'small' : 'large'}
            />
            <div style={{ 
              fontWeight: 500, 
              fontSize: compact ? '12px' : '14px',
              marginBottom: compact ? '2px' : '4px'
            }}>
              {shortcut.title}
            </div>
            {!compact && (
              <div style={{ 
                fontSize: '12px', 
                color: '#666',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {shortcut.description}
              </div>
            )}
          </div>
        </Card>
      </Col>
    );
  }, [compact, executeShortcut, toggleFavorite, openEditModal, deleteShortcut]);

  // Raccourcis triés (favoris en premier)
  const sortedShortcuts = [...shortcuts]
    .sort((a, b) => {
      if (a.favorite && !b.favorite) return -1;
      if (!a.favorite && b.favorite) return 1;
      return 0;
    })
    .slice(0, maxItems);

  return (
    <div>
      {showTitle && (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: '16px'
        }}>
          <Title level={4} style={{ margin: 0 }}>
            Raccourcis rapides
          </Title>
          <Space>
            <Button
              size="small"
              icon={<AppstoreOutlined />}
              onClick={() => setIsPresetsVisible(true)}
            >
              Modèles
            </Button>
            <Button
              type="primary"
              size="small"
              icon={<PlusOutlined />}
              onClick={() => openEditModal()}
            >
              Nouveau
            </Button>
          </Space>
        </div>
      )}

      {sortedShortcuts.length === 0 ? (
        <Card>
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Aucun raccourci configuré"
          >
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => openEditModal()}
            >
              Créer un raccourci
            </Button>
          </Empty>
        </Card>
      ) : (
        <Row gutter={[16, 16]}>
          {sortedShortcuts.map(renderShortcut)}
        </Row>
      )}

      {/* Modal d'édition */}
      <Modal
        title={editingShortcut ? 'Modifier le raccourci' : 'Nouveau raccourci'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingShortcut(null);
          form.resetFields();
        }}
        onOk={handleSubmit}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="title"
                label="Titre"
                rules={[{ required: true, message: 'Le titre est requis' }]}
              >
                <Input placeholder="Nom du raccourci" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="description"
                label="Description"
              >
                <Input placeholder="Description du raccourci" />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="icon"
                label="Icône"
                rules={[{ required: true, message: 'L\'icône est requise' }]}
              >
                <Select placeholder="Choisir une icône">
                  {Object.entries(AVAILABLE_ICONS).map(([key, config]) => (
                    <Option key={key} value={key}>
                      <Space>
                        {config.icon}
                        {config.label}
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="color"
                label="Couleur"
              >
                <Input type="color" defaultValue="#1890ff" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="action"
                label="Action"
                rules={[{ required: true, message: 'L\'action est requise' }]}
              >
                <Select placeholder="Type d'action">
                  <Option value="navigate">Navigation</Option>
                  <Option value="api_call">Appel API</Option>
                  <Option value="command">Commande</Option>
                  <Option value="external">Lien externe</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="target"
            label="Cible"
            rules={[{ required: true, message: 'La cible est requise' }]}
          >
            <Input placeholder="URL, chemin ou commande" />
          </Form.Item>
        </Form>
      </Modal>

      {/* Modal des raccourcis prédéfinis */}
      <Modal
        title="Modèles de raccourcis"
        open={isPresetsVisible}
        onCancel={() => setIsPresetsVisible(false)}
        footer={null}
        width={800}
      >
        <Row gutter={[16, 16]}>
          {PRESET_SHORTCUTS.map(preset => (
            <Col xs={24} sm={12} md={8} key={preset.id}>
              <Card
                size="small"
                hoverable
                actions={[
                  <Button
                    type="primary"
                    size="small"
                    icon={<PlusOutlined />}
                    onClick={() => addPresetShortcut(preset)}
                  >
                    Ajouter
                  </Button>
                ]}
              >
                <div style={{ textAlign: 'center' }}>
                  <Avatar
                    icon={AVAILABLE_ICONS[preset.icon]?.icon}
                    style={{ 
                      backgroundColor: preset.color,
                      marginBottom: '8px'
                    }}
                  />
                  <div style={{ fontWeight: 500, marginBottom: '4px' }}>
                    {preset.title}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {preset.description}
                  </div>
                  <Tag size="small" style={{ marginTop: '4px' }}>
                    {preset.category}
                  </Tag>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Modal>
    </div>
  );
};

export default QuickActions;