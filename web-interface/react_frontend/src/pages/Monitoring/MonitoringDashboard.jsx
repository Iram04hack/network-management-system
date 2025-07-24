/**
 * MonitoringDashboard - Module Monitoring Refactorisé
 * Exploite les 68 endpoints backend avec interface moderne et fluide
 * Architecture modulaire avec sous-sections
 */

import React, { useState } from 'react';
import { 
  Tabs, 
  Card, 
  Badge, 
  Button, 
  Space, 
  Tooltip, 
  Spin, 
  Alert,
  Switch,
  Select,
  Statistic,
  Row,
  Col
} from 'antd';
import {
  DashboardOutlined,
  AlertOutlined,
  LineChartOutlined,
  ClusterOutlined,
  AppstoreOutlined,
  BellOutlined,
  ApiOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined
} from '@ant-design/icons';

// Import du hook spécialisé
import useMonitoring from '../../hooks/useMonitoring';

// Import des sous-sections
import OverviewSection from './sections/OverviewSection';
import AlertsSection from './sections/AlertsSection';
import MetricsSection from './sections/MetricsSection';
import InfrastructureSection from './sections/InfrastructureSection';
import DashboardsSection from './sections/DashboardsSection';
import NotificationsSection from './sections/NotificationsSection';
import IntegrationsSection from './sections/IntegrationsSection';

const { TabPane } = Tabs;
const { Option } = Select;


const MonitoringDashboard = () => {
  // Hook spécialisé monitoring
  const {
    // États
    realTimeMetrics,
    alerts,
    metricsHistory,
    thresholds,
    specializedMonitoring,
    dashboards,
    notifications,
    integrations,
    
    // Configuration
    realTimeEnabled,
    refreshInterval,
    
    // Actions
    refreshAll,
    enableRealTime,
    fetchAlerts,
    
    // Getters calculés
    hasActiveAlerts,
    criticalAlertsCount,
    systemHealthy,
    unreadNotificationsCount,
    isLoading
  } = useMonitoring();

  // État local pour l'onglet actif
  const [activeTab, setActiveTab] = useState('overview');
  const [refreshing, setRefreshing] = useState(false);

  // Configuration des onglets avec badges
  const tabsConfig = [
    {
      key: 'overview',
      label: 'Vue d\'ensemble',
      icon: <DashboardOutlined />,
      badge: null
    },
    {
      key: 'alerts',
      label: 'Alertes',
      icon: <AlertOutlined />,
      badge: criticalAlertsCount > 0 ? criticalAlertsCount : null,
      badgeStatus: criticalAlertsCount > 0 ? 'error' : null
    },
    {
      key: 'metrics',
      label: 'Métriques',
      icon: <LineChartOutlined />,
      badge: null
    },
    {
      key: 'infrastructure',
      label: 'Infrastructure',
      icon: <ClusterOutlined />,
      badge: !systemHealthy ? '!' : null,
      badgeStatus: !systemHealthy ? 'warning' : null
    },
    {
      key: 'dashboards',
      label: 'Tableaux de bord',
      icon: <AppstoreOutlined />,
      badge: null
    },
    {
      key: 'notifications',
      label: 'Notifications',
      icon: <BellOutlined />,
      badge: unreadNotificationsCount > 0 ? unreadNotificationsCount : null,
      badgeStatus: unreadNotificationsCount > 0 ? 'processing' : null
    },
    {
      key: 'integrations',
      label: 'Intégrations',
      icon: <ApiOutlined />,
      badge: null
    }
  ];

  // Gestion du rafraîchissement manuel
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refreshAll();
      // Rafraîchir aussi les alertes si nécessaire
      if (hasActiveAlerts) {
        await fetchAlerts();
      }
    } finally {
      setRefreshing(false);
    }
  };

  // Gestion du temps réel
  const handleRealTimeToggle = (enabled) => {
    enableRealTime(enabled, refreshInterval);
  };

  // Actions de la barre d'outils
  const renderToolbar = () => (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      marginBottom: '20px',
      padding: '0 4px'
    }}>
      {/* Indicateurs de statut global */}
      <Space size="large">
        <Statistic
          title="Alertes critiques"
          value={criticalAlertsCount}
          valueStyle={{ 
            color: criticalAlertsCount > 0 ? '#ff4d4f' : '#52c41a',
            fontSize: '18px'
          }}
        />
        <Statistic
          title="Infrastructure"
          value={systemHealthy ? 'Saine' : 'Problème'}
          valueStyle={{ 
            color: systemHealthy ? '#52c41a' : '#faad14',
            fontSize: '18px'
          }}
        />
        <Statistic
          title="Notifications"
          value={unreadNotificationsCount}
          valueStyle={{ 
            color: unreadNotificationsCount > 0 ? '#1890ff' : '#8c8c8c',
            fontSize: '18px'
          }}
        />
      </Space>

      {/* Actions */}
      <Space>
        {/* Configuration temps réel */}
        <Tooltip title={realTimeEnabled ? 'Désactiver la mise à jour temps réel' : 'Activer la mise à jour temps réel'}>
          <Space>
            {realTimeEnabled ? <PlayCircleOutlined style={{ color: '#52c41a' }} /> : <PauseCircleOutlined />}
            <Switch
              checked={realTimeEnabled}
              onChange={handleRealTimeToggle}
              size="small"
            />
            <span style={{ fontSize: '12px', color: '#8c8c8c' }}>
              Temps réel
            </span>
          </Space>
        </Tooltip>

        {/* Intervalle de rafraîchissement */}
        {realTimeEnabled && (
          <Select
            value={refreshInterval}
            onChange={(value) => enableRealTime(true, value)}
            size="small"
            style={{ width: 80 }}
          >
            <Option value={10000}>10s</Option>
            <Option value={30000}>30s</Option>
            <Option value={60000}>1m</Option>
            <Option value={300000}>5m</Option>
          </Select>
        )}

        {/* Rafraîchissement manuel */}
        <Tooltip title="Actualiser toutes les données">
          <Button
            icon={<ReloadOutlined spin={refreshing} />}
            onClick={handleRefresh}
            loading={refreshing}
            type="primary"
            size="small"
          >
            Actualiser
          </Button>
        </Tooltip>
      </Space>
    </div>
  );

  // Rendu des onglets avec badges
  const renderTabs = () => (
    <Tabs
      activeKey={activeTab}
      onChange={setActiveTab}
      type="card"
      size="large"
      tabBarStyle={{
        background: 'transparent',
        border: 'none',
        marginBottom: '0'
      }}
    >
      {tabsConfig.map(tab => (
        <TabPane
          key={tab.key}
          tab={
            <Space>
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge && (
                <Badge 
                  count={tab.badge} 
                  status={tab.badgeStatus} 
                  size="small" 
                />
              )}
            </Space>
          }
        >
          {renderTabContent(tab.key)}
        </TabPane>
      ))}
    </Tabs>
  );

  // Contenu des onglets
  const renderTabContent = (tabKey) => {
    // Loading global
    if (isLoading && activeTab === tabKey) {
      return (
        <Card>
          <div style={{ textAlign: 'center', padding: '60px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px', color: '#8c8c8c' }}>
              Chargement des données de monitoring...
            </div>
          </div>
        </Card>
      );
    }

    switch (tabKey) {
      case 'overview':
        return <OverviewSection />;

      case 'alerts':
        return <AlertsSection />;

      case 'metrics':
        return <MetricsSection />;

      case 'infrastructure':
        return <InfrastructureSection />;

      case 'dashboards':
        return <DashboardsSection />;

      case 'notifications':
        return <NotificationsSection />;

      case 'integrations':
        return <IntegrationsSection />;

      default:
        return null;
    }
  };

  // Gestion des erreurs globales
  const renderErrors = () => {
    const errors = [
      realTimeMetrics.error,
      alerts.error,
      metricsHistory.error,
      specializedMonitoring.error,
      dashboards.error,
      notifications.error,
      integrations.error
    ].filter(Boolean);

    if (errors.length === 0) return null;

    return (
      <Alert
        message="Erreurs de chargement détectées"
        description={
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            {errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        }
        type="warning"
        showIcon
        closable
        style={{ marginBottom: '20px' }}
      />
    );
  };

  return (
    <div style={{ padding: '0' }}>
      {/* Barre d'outils globale */}
      {renderToolbar()}

      {/* Affichage des erreurs */}
      {renderErrors()}

      {/* Navigation par onglets */}
      <Card 
        bordered={false}
        bodyStyle={{ padding: '0' }}
        style={{ 
          minHeight: '600px',
          background: 'transparent'
        }}
      >
        {renderTabs()}
      </Card>
    </div>
  );
};

export default MonitoringDashboard;