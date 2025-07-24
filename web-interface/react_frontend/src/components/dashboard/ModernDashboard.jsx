/**
 * ModernDashboard - Composant Dashboard modernisé avec drag & drop et fonctionnalités avancées
 * Intègre tous les composants améliorés : DashboardDesigner, RealtimeNotifications, QuickActions
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Layout,
  Card,
  Row,
  Col,
  Button,
  Space,
  Typography,
  Tabs,
  Switch,
  Tooltip,
  Badge,
  Spin,
  Alert,
  Divider,
  Statistic,
  Progress,
  Avatar,
  message,
  Modal,
  Drawer,
  InputNumber
} from 'antd';
import {
  DashboardOutlined,
  SettingOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  ReloadOutlined,
  SaveOutlined,
  PlusOutlined,
  EditOutlined,
  EyeOutlined,
  ThunderboltOutlined,
  BellOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  CloudOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  DesktopOutlined,
  MobileOutlined,
  TabletOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

// Import des composants créés
import DashboardDesigner from './DashboardDesigner';
import RealtimeNotifications from './RealtimeNotifications';
import QuickActions from './QuickActions';
import { useDashboard } from '../../hooks/useDashboard';

// Import des styles
import '../../styles/react-grid-layout.css';

const { Header, Content, Sider } = Layout;
const { Title, Text } = Typography;
const { TabPane } = Tabs;

// Données simulées pour les métriques de santé
const generateHealthMetrics = () => ({
  systemHealth: {
    cpu: Math.floor(Math.random() * 30) + 50,
    memory: Math.floor(Math.random() * 40) + 40,
    network: Math.floor(Math.random() * 20) + 80,
    storage: Math.floor(Math.random() * 25) + 60
  },
  alerts: {
    critical: Math.floor(Math.random() * 5),
    warning: Math.floor(Math.random() * 10) + 5,
    info: Math.floor(Math.random() * 15) + 10
  },
  infrastructure: {
    totalDevices: 247,
    onlineDevices: 235,
    offlineDevices: 12,
    uptime: 99.7
  },
  performance: {
    responseTime: Math.floor(Math.random() * 50) + 150,
    throughput: Math.floor(Math.random() * 1000) + 5000,
    errorRate: Math.random() * 0.5
  }
});

const ModernDashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [isDesignMode, setIsDesignMode] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [healthMetrics, setHealthMetrics] = useState(generateHealthMetrics());
  const [selectedDashboard, setSelectedDashboard] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [viewMode, setViewMode] = useState('desktop'); // desktop, tablet, mobile
  const [isSettingsVisible, setIsSettingsVisible] = useState(false);

  // Hook pour la gestion des dashboards
  const { 
    dashboards, 
    loading, 
    error, 
    isAuthenticated, 
    fetchDashboards,
    createDashboard,
    updateDashboard,
    deleteDashboard,
    ensureAdminUser
  } = useDashboard();

  // Chargement initial et authentification
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Vérifier l'authentification et créer un compte admin si nécessaire
        const credentials = { username: 'admin', password: 'admin' };
        await ensureAdminUser(credentials);
        
        // Charger les dashboards
        await fetchDashboards();
      } catch (error) {
        console.error('Erreur lors de l\'initialisation:', error);
        message.error('Erreur lors de l\'initialisation de l\'application');
      }
    };

    initializeApp();
  }, [ensureAdminUser, fetchDashboards]);

  // Actualisation automatique des métriques
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      setHealthMetrics(generateHealthMetrics());
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  // Gestion du mode plein écran
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  // Basculer le mode plein écran
  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  }, []);

  // Actualiser manuellement
  const handleRefresh = useCallback(() => {
    setHealthMetrics(generateHealthMetrics());
    fetchDashboards();
    message.success('Données actualisées');
  }, [fetchDashboards]);

  // Sauvegarder la configuration
  const handleSaveConfig = useCallback(() => {
    const config = {
      autoRefresh,
      refreshInterval,
      viewMode,
      sidebarCollapsed
    };
    
    localStorage.setItem('dashboard_config', JSON.stringify(config));
    message.success('Configuration sauvegardée');
  }, [autoRefresh, refreshInterval, viewMode, sidebarCollapsed]);

  // Charger la configuration
  useEffect(() => {
    const savedConfig = localStorage.getItem('dashboard_config');
    if (savedConfig) {
      try {
        const config = JSON.parse(savedConfig);
        setAutoRefresh(config.autoRefresh ?? true);
        setRefreshInterval(config.refreshInterval ?? 30000);
        setViewMode(config.viewMode ?? 'desktop');
        setSidebarCollapsed(config.sidebarCollapsed ?? false);
      } catch (error) {
        console.error('Erreur lors du chargement de la configuration:', error);
      }
    }
  }, []);

  // Créer un nouveau dashboard
  const handleCreateDashboard = useCallback(async () => {
    try {
      const newDashboard = await createDashboard({
        name: `Nouveau Dashboard ${Date.now()}`,
        description: 'Dashboard créé automatiquement',
        widgets: [],
        layouts: { lg: [] }
      });
      
      if (newDashboard) {
        setSelectedDashboard(newDashboard);
        setIsDesignMode(true);
        setActiveTab('designer');
      }
    } catch (error) {
      message.error('Erreur lors de la création du dashboard');
    }
  }, [createDashboard]);

  // Rendu des métriques de santé
  const renderHealthMetrics = () => {
    const { systemHealth, alerts, infrastructure, performance } = healthMetrics;

    return (
      <Row gutter={[16, 16]}>
        {/* Métriques système */}
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="CPU"
              value={systemHealth.cpu}
              precision={1}
              valueStyle={{ color: systemHealth.cpu > 80 ? '#ff4d4f' : '#52c41a' }}
              prefix={<DatabaseOutlined />}
              suffix="%"
            />
            <Progress
              percent={systemHealth.cpu}
              status={systemHealth.cpu > 80 ? 'exception' : 'success'}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Mémoire"
              value={systemHealth.memory}
              precision={1}
              valueStyle={{ color: systemHealth.memory > 85 ? '#ff4d4f' : '#52c41a' }}
              prefix={<CloudOutlined />}
              suffix="%"
            />
            <Progress
              percent={systemHealth.memory}
              status={systemHealth.memory > 85 ? 'exception' : 'success'}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Réseau"
              value={systemHealth.network}
              precision={1}
              valueStyle={{ color: systemHealth.network < 70 ? '#ff4d4f' : '#52c41a' }}
              prefix={<GlobalOutlined />}
              suffix="%"
            />
            <Progress
              percent={systemHealth.network}
              status={systemHealth.network < 70 ? 'exception' : 'success'}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>

        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Stockage"
              value={systemHealth.storage}
              precision={1}
              valueStyle={{ color: systemHealth.storage > 90 ? '#ff4d4f' : '#52c41a' }}
              prefix={<DatabaseOutlined />}
              suffix="%"
            />
            <Progress
              percent={systemHealth.storage}
              status={systemHealth.storage > 90 ? 'exception' : 'success'}
              showInfo={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // Rendu des alertes
  const renderAlerts = () => {
    const { alerts } = healthMetrics;

    return (
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Alertes Critiques"
              value={alerts.critical}
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<WarningOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Avertissements"
              value={alerts.warning}
              valueStyle={{ color: '#faad14' }}
              prefix={<BellOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Informations"
              value={alerts.info}
              valueStyle={{ color: '#1890ff' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // Rendu de l'infrastructure
  const renderInfrastructure = () => {
    const { infrastructure } = healthMetrics;

    return (
      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24} sm={12}>
          <Card title="État des équipements">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <Text strong>Total: {infrastructure.totalDevices}</Text>
                <br />
                <Text type="success">En ligne: {infrastructure.onlineDevices}</Text>
                <br />
                <Text type="danger">Hors ligne: {infrastructure.offlineDevices}</Text>
              </div>
              <div style={{ width: '120px' }}>
                <ResponsiveContainer width="100%" height={80}>
                  <PieChart>
                    <Pie
                      data={[
                        { name: 'En ligne', value: infrastructure.onlineDevices, fill: '#52c41a' },
                        { name: 'Hors ligne', value: infrastructure.offlineDevices, fill: '#ff4d4f' }
                      ]}
                      cx="50%"
                      cy="50%"
                      outerRadius={30}
                      dataKey="value"
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12}>
          <Card title="Disponibilité">
            <Statistic
              title="Temps de fonctionnement"
              value={infrastructure.uptime}
              precision={1}
              valueStyle={{ color: infrastructure.uptime > 99 ? '#52c41a' : '#faad14' }}
              prefix={infrastructure.uptime > 99 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              suffix="%"
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // Barre d'outils
  const renderToolbar = () => (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      padding: '16px 24px',
      background: '#fafafa',
      borderBottom: '1px solid #f0f0f0'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <Title level={4} style={{ margin: 0 }}>
          <DashboardOutlined style={{ marginRight: '8px' }} />
          Dashboard de Supervision
        </Title>
        <Badge status={isAuthenticated ? 'success' : 'error'} />
      </div>

      <Space>
        {/* Mode d'affichage */}
        <Tooltip title="Mode d'affichage">
          <Button.Group>
            <Button
              type={viewMode === 'desktop' ? 'primary' : 'default'}
              icon={<DesktopOutlined />}
              onClick={() => setViewMode('desktop')}
              size="small"
            />
            <Button
              type={viewMode === 'tablet' ? 'primary' : 'default'}
              icon={<TabletOutlined />}
              onClick={() => setViewMode('tablet')}
              size="small"
            />
            <Button
              type={viewMode === 'mobile' ? 'primary' : 'default'}
              icon={<MobileOutlined />}
              onClick={() => setViewMode('mobile')}
              size="small"
            />
          </Button.Group>
        </Tooltip>

        {/* Actualisation automatique */}
        <Tooltip title="Actualisation automatique">
          <Switch
            checked={autoRefresh}
            onChange={setAutoRefresh}
            checkedChildren="Auto"
            unCheckedChildren="Manuel"
            size="small"
          />
        </Tooltip>

        {/* Notifications temps réel */}
        <RealtimeNotifications />

        {/* Actions */}
        <Tooltip title="Actualiser">
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
            size="small"
          />
        </Tooltip>

        <Tooltip title="Nouveau dashboard">
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreateDashboard}
            size="small"
          />
        </Tooltip>

        <Tooltip title="Paramètres">
          <Button
            icon={<SettingOutlined />}
            onClick={() => setIsSettingsVisible(true)}
            size="small"
          />
        </Tooltip>

        <Tooltip title={isFullscreen ? 'Quitter plein écran' : 'Plein écran'}>
          <Button
            icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
            onClick={toggleFullscreen}
            size="small"
          />
        </Tooltip>
      </Space>
    </div>
  );

  // Gestion des erreurs
  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="Erreur de connexion"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={() => window.location.reload()}>
              Recharger
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Barre d'outils */}
      {renderToolbar()}

      <Layout>
        {/* Sidebar pour les actions rapides */}
        <Sider
          collapsed={sidebarCollapsed}
          onCollapse={setSidebarCollapsed}
          width={300}
          style={{
            background: '#fff',
            borderRight: '1px solid #f0f0f0'
          }}
        >
          <div style={{ padding: '16px' }}>
            <QuickActions 
              maxItems={sidebarCollapsed ? 4 : 8}
              showTitle={!sidebarCollapsed}
              compact={sidebarCollapsed}
            />
          </div>
        </Sider>

        {/* Contenu principal */}
        <Layout style={{ padding: '24px' }}>
          <Content>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin size="large" />
                <div style={{ marginTop: '16px' }}>
                  <Text>Chargement du dashboard...</Text>
                </div>
              </div>
            ) : (
              <Tabs
                activeKey={activeTab}
                onChange={setActiveTab}
                tabPosition="top"
                style={{ height: '100%' }}
                items={[
                  {
                    key: 'overview',
                    label: (
                      <span>
                        <DashboardOutlined />
                        Vue d'ensemble
                      </span>
                    ),
                    children: (
                      <div>
                        {renderHealthMetrics()}
                        {renderAlerts()}
                        {renderInfrastructure()}
                      </div>
                    )
                  },
                  {
                    key: 'designer',
                    label: (
                      <span>
                        <EditOutlined />
                        Designer
                      </span>
                    ),
                    children: (
                      <DashboardDesigner
                        dashboardId={selectedDashboard?.id}
                        onSave={(dashboard) => {
                          setSelectedDashboard(dashboard);
                          setIsDesignMode(false);
                          message.success('Dashboard sauvegardé');
                        }}
                        onCancel={() => {
                          setIsDesignMode(false);
                          setActiveTab('overview');
                        }}
                      />
                    )
                  },
                  {
                    key: 'dashboards',
                    label: (
                      <span>
                        <DashboardOutlined />
                        Mes Dashboards
                        <Badge count={dashboards.length} style={{ marginLeft: '8px' }} />
                      </span>
                    ),
                    children: (
                      <div>
                        <Alert
                          message="Gestion des dashboards"
                          description="Ici vous pouvez gérer tous vos dashboards personnalisés."
                          type="info"
                          showIcon
                          style={{ marginBottom: '16px' }}
                        />
                        {/* Intégrer ici le composant DashboardsSection existant */}
                      </div>
                    )
                  }
                ]}
              />
            )}
          </Content>
        </Layout>
      </Layout>

      {/* Drawer des paramètres */}
      <Drawer
        title="Paramètres du Dashboard"
        placement="right"
        width={400}
        open={isSettingsVisible}
        onClose={() => setIsSettingsVisible(false)}
      >
        <div style={{ padding: '16px 0' }}>
          <Title level={5}>Actualisation</Title>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <Text>Actualisation automatique</Text>
              <Switch
                checked={autoRefresh}
                onChange={setAutoRefresh}
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>Intervalle (secondes)</Text>
              <InputNumber
                min={10}
                max={300}
                value={refreshInterval / 1000}
                onChange={(value) => setRefreshInterval(value * 1000)}
                disabled={!autoRefresh}
              />
            </div>
          </div>

          <Divider />

          <Title level={5}>Interface</Title>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <Text>Sidebar réduite</Text>
              <Switch
                checked={sidebarCollapsed}
                onChange={setSidebarCollapsed}
              />
            </div>
          </div>

          <Divider />

          <div style={{ textAlign: 'center' }}>
            <Button
              type="primary"
              icon={<SaveOutlined />}
              onClick={handleSaveConfig}
            >
              Sauvegarder la configuration
            </Button>
          </div>
        </div>
      </Drawer>
    </Layout>
  );
};

export default ModernDashboard;