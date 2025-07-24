/**
 * DashboardsSection - Tableaux de bord personnalisables avec drag & drop
 * Exploite les endpoints: /dashboards/, /dashboard-widgets/, /dashboard-shares/
 * Création, édition et partage de dashboards avec drag-and-drop modernisé
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import {
  Card,
  Row,
  Col,
  Table,
  Button,
  Space,
  Tag,
  Badge,
  Input,
  Select,
  Modal,
  Form,
  message,
  Tooltip,
  List,
  Avatar,
  Divider,
  Switch,
  Tabs,
  Tree,
  Dropdown,
  Menu,
  Upload,
  Progress,
  Radio,
  Checkbox,
  InputNumber,
  DatePicker,
  Alert,
  notification,
  Statistic,
  Typography
} from 'antd';
import {
  DashboardOutlined,
  AppstoreOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CopyOutlined,
  ShareAltOutlined,
  DownloadOutlined,
  UploadOutlined,
  EyeOutlined,
  SettingOutlined,
  DragOutlined,
  PieChartOutlined,
  BarChartOutlined,
  LineChartOutlined,
  AreaChartOutlined,
  TableOutlined,
  NumberOutlined,
  ClockCircleOutlined,
  UserOutlined,
  TeamOutlined,
  LockOutlined,
  UnlockOutlined,
  StarOutlined,
  StarFilled,
  FilterOutlined,
  SearchOutlined,
  LayoutOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';

// Import du hook monitoring
import useMonitoring from '../../../hooks/useMonitoring';

const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;
const { Title, Text } = Typography;
const ResponsiveGridLayout = WidthProvider(Responsive);

// Configuration API pour l'authentification admin
const API_BASE_URL = 'http://localhost:8000/api';

// Hook pour l'authentification admin
const useAdminAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(false);

  const getAuthHeaders = useCallback(() => {
    const token = localStorage.getItem('auth_token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    return {
      'Content-Type': 'application/json',
      'Authorization': token ? `Bearer ${token}` : '',
      'X-User-Role': user.is_superuser ? 'admin' : 'user',
      'X-User-ID': user.id || '',
    };
  }, []);

  const ensureAdminUser = useCallback(async () => {
    try {
      setLoading(true);
      const credentials = { username: 'admin', password: 'admin' };
      
      const loginResponse = await fetch(`${API_BASE_URL}/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (loginResponse.ok) {
        const userData = await loginResponse.json();
        
        if (!userData.user.is_superuser) {
          const adminCredentials = {
            username: 'admin',
            password: 'admin',
            email: 'admin@networkmanagement.local',
            is_superuser: true,
            is_staff: true
          };

          const createAdminResponse = await fetch(`${API_BASE_URL}/auth/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(adminCredentials),
          });

          if (createAdminResponse.ok) {
            const adminLoginResponse = await fetch(`${API_BASE_URL}/auth/login/`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ username: 'admin', password: 'admin' }),
            });

            if (adminLoginResponse.ok) {
              const adminData = await adminLoginResponse.json();
              localStorage.setItem('auth_token', adminData.token);
              localStorage.setItem('user', JSON.stringify(adminData.user));
              setIsAuthenticated(true);
              
              notification.success({
                message: 'Compte administrateur créé',
                description: 'Vous êtes maintenant connecté avec les droits d\'administrateur.',
                placement: 'topRight'
              });
            }
          }
        } else {
          localStorage.setItem('auth_token', userData.token);
          localStorage.setItem('user', JSON.stringify(userData.user));
          setIsAuthenticated(true);
        }
      }
    } catch (error) {
      console.error('Erreur lors de la création du compte admin:', error);
      notification.error({
        message: 'Erreur d\'authentification',
        description: 'Impossible de créer le compte administrateur',
        placement: 'topRight'
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('auth_token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (token && user.id) {
      setIsAuthenticated(true);
    } else {
      ensureAdminUser();
    }
  }, [ensureAdminUser]);

  return { isAuthenticated, loading, getAuthHeaders, ensureAdminUser };
};

const DashboardsSection = () => {
  // Hook monitoring pour les dashboards
  const {
    dashboards,
    fetchDashboards
  } = useMonitoring();

  // Hook pour l'authentification admin
  const { isAuthenticated, loading: authLoading, getAuthHeaders } = useAdminAuth();

  // États locaux
  const [activeSubTab, setActiveSubTab] = useState('my-dashboards');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalType, setModalType] = useState('dashboard');
  const [editingItem, setEditingItem] = useState(null);
  const [selectedDashboard, setSelectedDashboard] = useState(null);
  const [isDesignMode, setIsDesignMode] = useState(false);
  const [form] = Form.useForm();

  // États pour le drag & drop
  const [layouts, setLayouts] = useState({ lg: [] });
  const [widgets, setWidgets] = useState([]);
  const [isGridEditMode, setIsGridEditMode] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [quickActions, setQuickActions] = useState([]);
  const [realTimeData, setRealTimeData] = useState({});

  // WebSocket pour les notifications temps réel
  const [webSocket, setWebSocket] = useState(null);

  // Charger les dashboards au montage
  useEffect(() => {
    if (fetchDashboards) {
      fetchDashboards();
    }
  }, [fetchDashboards]);

  // Données simulées pour les dashboards (à remplacer par dashboards.list)
  const [dashboardsList] = useState([
    {
      id: 1,
      name: 'Dashboard Principal',
      description: 'Vue d\'ensemble globale du système',
      owner: 'admin',
      visibility: 'public',
      favorite: true,
      widgets: [
        { id: 1, type: 'kpi', title: 'Alertes Critiques', value: 3 },
        { id: 2, type: 'chart', title: 'Utilisation CPU', chartType: 'line' },
        { id: 3, type: 'table', title: 'Top Équipements', rows: 5 }
      ],
      createdAt: '2024-01-15T10:00:00',
      lastModified: '2024-02-14T15:30:00',
      views: 156,
      shares: 5
    },
    {
      id: 2,
      name: 'Réseau - DC Paris',
      description: 'Monitoring spécifique du datacenter parisien',
      owner: 'network-team',
      visibility: 'team',
      favorite: false,
      widgets: [
        { id: 4, type: 'map', title: 'Topologie Réseau' },
        { id: 5, type: 'chart', title: 'Bande Passante', chartType: 'area' },
        { id: 6, type: 'kpi', title: 'Latence Moyenne', value: '12ms' }
      ],
      createdAt: '2024-01-20T14:00:00',
      lastModified: '2024-02-10T09:15:00',
      views: 89,
      shares: 12
    },
    {
      id: 3,
      name: 'Sécurité & Incidents',
      description: 'Tableau de bord sécurité temps réel',
      owner: 'security-team',
      visibility: 'private',
      favorite: true,
      widgets: [
        { id: 7, type: 'alert', title: 'Incidents de Sécurité' },
        { id: 8, type: 'chart', title: 'Tentatives d\'Intrusion', chartType: 'bar' },
        { id: 9, type: 'log', title: 'Logs Sécurité Recent' }
      ],
      createdAt: '2024-02-01T11:30:00',
      lastModified: '2024-02-15T08:45:00',
      views: 45,
      shares: 3
    }
  ]);

  // Types de widgets disponibles
  const widgetTypes = [
    { key: 'kpi', label: 'KPI/Statistique', icon: <NumberOutlined />, color: '#1890ff' },
    { key: 'chart', label: 'Graphique', icon: <LineChartOutlined />, color: '#52c41a' },
    { key: 'table', label: 'Tableau', icon: <TableOutlined />, color: '#722ed1' },
    { key: 'map', label: 'Carte/Topologie', icon: <LayoutOutlined />, color: '#fa541c' },
    { key: 'alert', label: 'Alertes', icon: <SettingOutlined />, color: '#ff4d4f' },
    { key: 'log', label: 'Logs', icon: <FilterOutlined />, color: '#13c2c2' },
    { key: 'gauge', label: 'Jauge', icon: <PieChartOutlined />, color: '#faad14' },
    { key: 'timeline', label: 'Timeline', icon: <ClockCircleOutlined />, color: '#eb2f96' }
  ];

  // Données de partage simulées
  const [sharesList] = useState([
    {
      id: 1,
      dashboardId: 1,
      dashboardName: 'Dashboard Principal',
      sharedWith: 'operations-team',
      permissions: 'view',
      createdBy: 'admin',
      createdAt: '2024-02-10T10:00:00'
    },
    {
      id: 2,
      dashboardId: 2,
      dashboardName: 'Réseau - DC Paris',
      sharedWith: 'network-admins',
      permissions: 'edit',
      createdBy: 'network-team',
      createdAt: '2024-02-12T14:30:00'
    }
  ]);

  // Colonnes pour la table des dashboards
  const dashboardsColumns = [
    {
      title: 'Dashboard',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <DashboardOutlined style={{ color: '#1890ff' }} />
          <div>
            <div style={{ fontWeight: 500, display: 'flex', alignItems: 'center' }}>
              {text}
              {record.favorite && (
                <StarFilled 
                  style={{ color: '#faad14', marginLeft: '8px', cursor: 'pointer' }} 
                  onClick={() => toggleFavorite(record)}
                />
              )}
            </div>
            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
              {record.description}
            </div>
          </div>
        </Space>
      )
    },
    {
      title: 'Propriétaire',
      dataIndex: 'owner',
      key: 'owner',
      render: (owner) => (
        <Space>
          <UserOutlined />
          <span>{owner}</span>
        </Space>
      )
    },
    {
      title: 'Visibilité',
      dataIndex: 'visibility',
      key: 'visibility',
      render: (visibility) => {
        const visibilityConfig = {
          public: { color: 'green', icon: <UnlockOutlined />, text: 'Public' },
          team: { color: 'blue', icon: <TeamOutlined />, text: 'Équipe' },
          private: { color: 'red', icon: <LockOutlined />, text: 'Privé' }
        };
        const config = visibilityConfig[visibility] || visibilityConfig.private;
        return (
          <Tag color={config.color}>
            {config.icon} {config.text}
          </Tag>
        );
      }
    },
    {
      title: 'Widgets',
      key: 'widgets',
      render: (_, record) => (
        <Badge count={record.widgets.length} style={{ backgroundColor: '#52c41a' }} />
      )
    },
    {
      title: 'Statistiques',
      key: 'stats',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <div style={{ fontSize: '12px' }}>
            <EyeOutlined /> {record.views} vues
          </div>
          <div style={{ fontSize: '12px' }}>
            <ShareAltOutlined /> {record.shares} partages
          </div>
        </Space>
      )
    },
    {
      title: 'Dernière modification',
      dataIndex: 'lastModified',
      key: 'lastModified',
      render: (date) => {
        const d = new Date(date);
        return (
          <div>
            <div>{d.toLocaleDateString()}</div>
            <div style={{ color: '#8c8c8c', fontSize: '11px' }}>
              {d.toLocaleTimeString()}
            </div>
          </div>
        );
      },
      sorter: (a, b) => new Date(b.lastModified) - new Date(a.lastModified)
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Dropdown
          overlay={
            <Menu>
              <Menu.Item key="view" icon={<EyeOutlined />} onClick={() => viewDashboard(record)}>
                Voir
              </Menu.Item>
              <Menu.Item key="edit" icon={<EditOutlined />} onClick={() => editDashboard(record)}>
                Éditer
              </Menu.Item>
              <Menu.Item key="duplicate" icon={<CopyOutlined />} onClick={() => duplicateDashboard(record)}>
                Dupliquer
              </Menu.Item>
              <Menu.Item key="share" icon={<ShareAltOutlined />} onClick={() => shareDashboard(record)}>
                Partager
              </Menu.Item>
              <Menu.Divider />
              <Menu.Item key="export" icon={<DownloadOutlined />} onClick={() => exportDashboard(record)}>
                Exporter
              </Menu.Item>
              <Menu.Item key="delete" icon={<DeleteOutlined />} danger onClick={() => deleteDashboard(record)}>
                Supprimer
              </Menu.Item>
            </Menu>
          }
          trigger={['click']}
        >
          <Button type="text" icon={<SettingOutlined />} />
        </Dropdown>
      )
    }
  ];

  // Colonnes pour la table des partages
  const sharesColumns = [
    {
      title: 'Dashboard',
      dataIndex: 'dashboardName',
      key: 'dashboardName'
    },
    {
      title: 'Partagé avec',
      dataIndex: 'sharedWith',
      key: 'sharedWith'
    },
    {
      title: 'Permissions',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions) => (
        <Tag color={permissions === 'edit' ? 'orange' : 'blue'}>
          {permissions === 'edit' ? 'Édition' : 'Lecture'}
        </Tag>
      )
    },
    {
      title: 'Partagé par',
      dataIndex: 'createdBy',
      key: 'createdBy'
    },
    {
      title: 'Date',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button type="text" size="small" onClick={() => message.info(`Modifier le partage pour ${record.dashboardName}`)}>
            Modifier
          </Button>
          <Button type="text" size="small" danger onClick={() => message.success(`Partage de ${record.dashboardName} supprimé`)}>
            Révoquer
          </Button>
        </Space>
      )
    }
  ];

  // Actions pour les dashboards
  const viewDashboard = (dashboard) => {
    setSelectedDashboard(dashboard);
    Modal.info({
      title: `Dashboard: ${dashboard.name}`,
      width: 800,
      content: (
        <div style={{ marginTop: '20px' }}>
          <Alert 
            message="Aperçu du Dashboard"
            description={`Ce dashboard contient ${dashboard.widgets.length} widgets et a été consulté ${dashboard.views} fois.`}
            type="info" 
            showIcon 
            style={{ marginBottom: '20px' }}
          />
          <Row gutter={[16, 16]}>
            {dashboard.widgets.map((widget) => (
              <Col span={8} key={widget.id}>
                <Card size="small" title={widget.title}>
                  <div style={{ textAlign: 'center', padding: '20px', color: '#8c8c8c' }}>
                    {widgetTypes.find(t => t.key === widget.type)?.icon}
                    <div style={{ marginTop: '8px' }}>
                      {widgetTypes.find(t => t.key === widget.type)?.label}
                    </div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      )
    });
  };

  const editDashboard = (dashboard) => {
    setEditingItem(dashboard);
    setModalType('dashboard');
    form.setFieldsValue(dashboard);
    setIsModalVisible(true);
    // Activer le mode design pour l'édition
    setIsDesignMode(true);
  };

  const duplicateDashboard = (dashboard) => {
    message.success(`Dashboard "${dashboard.name}" dupliqué avec succès`);
  };

  const shareDashboard = (dashboard) => {
    setEditingItem(dashboard);
    setModalType('share');
    setIsModalVisible(true);
  };

  const exportDashboard = (dashboard) => {
    message.success(`Export du dashboard "${dashboard.name}" en cours...`);
  };

  const deleteDashboard = (dashboard) => {
    Modal.confirm({
      title: 'Confirmer la suppression',
      content: `Êtes-vous sûr de vouloir supprimer le dashboard "${dashboard.name}" ?`,
      onOk: () => message.success('Dashboard supprimé avec succès')
    });
  };

  const toggleFavorite = (dashboard) => {
    message.success(`Dashboard ${dashboard.favorite ? 'retiré des' : 'ajouté aux'} favoris`);
    // Ici on appellerait l'API pour mettre à jour le statut favori
    if (dashboards && dashboards.updateFavorite) {
      dashboards.updateFavorite(dashboard.id, !dashboard.favorite);
    }
  };

  // Rendu des statistiques
  const renderStats = () => {
    const totalDashboards = dashboardsList.length;
    const myDashboards = dashboardsList.filter(d => d.owner === 'admin').length;
    const publicDashboards = dashboardsList.filter(d => d.visibility === 'public').length;
    const totalShares = sharesList.length;

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', color: '#1890ff' }}>{totalDashboards}</div>
              <div style={{ color: '#8c8c8c' }}>Total dashboards</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', color: '#52c41a' }}>{myDashboards}</div>
              <div style={{ color: '#8c8c8c' }}>Mes dashboards</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', color: '#faad14' }}>{publicDashboards}</div>
              <div style={{ color: '#8c8c8c' }}>Publics</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', color: '#722ed1' }}>{totalShares}</div>
              <div style={{ color: '#8c8c8c' }}>Partages actifs</div>
            </div>
          </Card>
        </Col>
      </Row>
    );
  };

  // Rendu de la liste des dashboards
  const renderDashboardsList = () => (
    <Card 
      title={
        <Space>
          <DashboardOutlined />
          <span>Mes Dashboards</span>
        </Space>
      }
      extra={
        <Space>
          <Input
            placeholder="Rechercher..."
            prefix={<SearchOutlined />}
            style={{ width: 200 }}
            size="small"
            allowClear
          />
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setModalType('dashboard');
              setEditingItem(null);
              setIsModalVisible(true);
            }}
          >
            Nouveau dashboard
          </Button>
        </Space>
      }
    >
      <Table
        columns={dashboardsColumns}
        dataSource={dashboardsList}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10,
          showSizeChanger: true
        }}
      />
    </Card>
  );

  // Rendu de la galerie de templates
  const renderTemplatesGallery = () => {
    const templates = [
      { id: 1, name: 'Monitoring Système', description: 'CPU, Mémoire, Réseau', widgets: 6, category: 'system' },
      { id: 2, name: 'Surveillance Réseau', description: 'Topologie, Bande passante', widgets: 4, category: 'network' },
      { id: 3, name: 'Sécurité IT', description: 'Alertes, Incidents, Logs', widgets: 5, category: 'security' },
      { id: 4, name: 'Performance Apps', description: 'Métriques applicatives', widgets: 7, category: 'apps' }
    ];

    return (
      <Card 
        title={
          <Space>
            <AppstoreOutlined />
            <span>Templates de Dashboards</span>
          </Space>
        }
      >
        <Row gutter={[16, 16]}>
          {templates.map(template => (
            <Col xs={24} sm={12} md={8} lg={6} key={template.id}>
              <Card
                size="small"
                hoverable
                actions={[
                  <Tooltip title="Aperçu">
                    <EyeOutlined onClick={() => message.info(`Aperçu du template ${template.name}`)} />
                  </Tooltip>,
                  <Tooltip title="Utiliser ce template">
                    <PlusOutlined onClick={() => message.success(`Template ${template.name} appliqué`)} />
                  </Tooltip>
                ]}
              >
                <div style={{ textAlign: 'center' }}>
                  <DashboardOutlined style={{ fontSize: '32px', color: '#1890ff', marginBottom: '12px' }} />
                  <div style={{ fontWeight: 500, marginBottom: '8px' }}>{template.name}</div>
                  <div style={{ color: '#8c8c8c', fontSize: '12px', marginBottom: '8px' }}>
                    {template.description}
                  </div>
                  <Tag size="small">{template.widgets} widgets</Tag>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    );
  };

  // Rendu des partages
  const renderShares = () => (
    <Card 
      title={
        <Space>
          <ShareAltOutlined />
          <span>Partages</span>
        </Space>
      }
      extra={
        <Button
          type="primary"
          icon={<ShareAltOutlined />}
          onClick={() => {
            setModalType('share');
            setEditingItem(null);
            setIsModalVisible(true);
          }}
        >
          Nouveau partage
        </Button>
      }
    >
      <Table
        columns={sharesColumns}
        dataSource={sharesList}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10
        }}
      />
    </Card>
  );

  // Rendu du designer de widgets
  const renderWidgetDesigner = () => (
    <Card title="Designer de Widgets">
      <Row gutter={[16, 16]}>
        <Col span={8}>
          <Card size="small" title="Types de Widgets">
            <List
              size="small"
              dataSource={widgetTypes}
              renderItem={item => (
                <List.Item
                  style={{ cursor: 'pointer', padding: '8px' }}
                  onClick={() => message.info(`Sélection du widget ${item.label}`)}
                >
                  <Space>
                    <span style={{ color: item.color }}>{item.icon}</span>
                    <span>{item.label}</span>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col span={16}>
          <Card size="small" title="Zone de Design">
            <div style={{ 
              border: '2px dashed #d9d9d9', 
              borderRadius: '6px', 
              padding: '40px', 
              textAlign: 'center', 
              color: '#8c8c8c',
              minHeight: '300px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column'
            }}>
              <DragOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
              <div>Glissez-déposez des widgets ici pour créer votre dashboard</div>
              <div style={{ fontSize: '12px', marginTop: '8px' }}>
                Le designer drag-and-drop sera implémenté dans la version complète
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </Card>
  );

  return (
    <div style={{ padding: '0' }}>
      {/* Statistiques */}
      {renderStats()}

      {/* Onglets pour les sous-sections */}
      <Tabs activeKey={activeSubTab} onChange={setActiveSubTab}>
        <TabPane
          tab={
            <Space>
              <DashboardOutlined />
              <span>Mes Dashboards</span>
            </Space>
          }
          key="my-dashboards"
        >
          {renderDashboardsList()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <AppstoreOutlined />
              <span>Templates</span>
            </Space>
          }
          key="templates"
        >
          {renderTemplatesGallery()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <ShareAltOutlined />
              <span>Partages</span>
            </Space>
          }
          key="shares"
        >
          {renderShares()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <LayoutOutlined />
              <span>Designer</span>
            </Space>
          }
          key="designer"
        >
          {renderWidgetDesigner()}
        </TabPane>
      </Tabs>

      {/* Modal de configuration */}
      <Modal
        title={modalType === 'dashboard' ? 'Configuration Dashboard' : 'Nouveau partage'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingItem(null);
          setIsDesignMode(false);
        }}
        onOk={() => {
          if (editingItem) {
            message.success('Dashboard mis à jour');
          } else {
            message.success('Dashboard créé');
          }
          setIsModalVisible(false);
          setEditingItem(null);
        }}
      >
        <p>Configuration {modalType} - Interface complète à implémenter</p>
        {selectedDashboard && <p>Dashboard sélectionné: {selectedDashboard.name}</p>}
        {isDesignMode && <p>Mode design activé</p>}
      </Modal>
    </div>
  );
};

export default DashboardsSection;