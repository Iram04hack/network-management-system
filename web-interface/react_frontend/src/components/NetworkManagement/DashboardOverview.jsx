/**
 * Dashboard Overview - Vue d'ensemble temps réel du système
 * Composant principal pour le module dashboard
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Badge,
  Alert,
  Space,
  Button,
  Select,
  DatePicker,
  Tooltip,
  Divider,
  Tag,
  Timeline,
  List,
  Avatar
} from 'antd';
import {
  DashboardOutlined,
  ApiOutlined,
  CloudServerOutlined,
  SecurityScanOutlined,
  MonitorOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  SettingOutlined,
  RiseOutlined,
  FallOutlined,
  BellOutlined,
  HeartOutlined
} from '@ant-design/icons';
import { useDashboard } from '../../hooks/useDashboard';
import { useApiViews } from '../../hooks/useApiViews';

const { Option } = Select;
const { RangePicker } = DatePicker;

/**
 * Composant principal du dashboard
 */
const DashboardOverview = () => {
  const {
    dashboardData,
    userConfig,
    widgets,
    loading: dashboardLoading,
    error: dashboardError,
    fetchDashboardData,
    fetchUserConfig,
    getActiveWidgets
  } = useDashboard();

  const {
    dashboardData: apiViewsData,
    systemOverview,
    networkOverview,
    loading: apiViewsLoading,
    error: apiViewsError,
    fetchDashboardOverview,
    fetchSystemOverview,
    fetchNetworkOverview
  } = useApiViews();

  const [refreshInterval, setRefreshInterval] = useState(30); // secondes
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');

  // Auto-refresh et chargement initial
  useEffect(() => {
    loadAllData();
    
    if (autoRefresh) {
      const interval = setInterval(loadAllData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  // Charger toutes les données
  const loadAllData = async () => {
    try {
      await Promise.all([
        fetchDashboardData(),
        fetchUserConfig(),
        fetchDashboardOverview(),
        fetchSystemOverview(),
        fetchNetworkOverview()
      ]);
    } catch (error) {
      console.error('Erreur chargement dashboard:', error);
    }
  };

  // Configuration des widgets actifs
  const activeWidgets = getActiveWidgets();

  // Données système combinées
  const systemData = {
    ...systemOverview,
    ...apiViewsData,
    devices: apiViewsData?.devices || systemOverview?.devices || { total: 0, online: 0 },
    alerts: apiViewsData?.alerts || systemOverview?.alerts || { total: 0, critical: 0 },
    system: apiViewsData?.system || systemOverview?.system || { overall_status: 'unknown' }
  };

  // Statut global
  const getOverallStatus = () => {
    const healthyPercentage = systemData.devices.total > 0 
      ? (systemData.devices.online / systemData.devices.total) * 100 
      : 0;
    
    if (healthyPercentage >= 90) return { status: 'success', text: 'Excellent' };
    if (healthyPercentage >= 70) return { status: 'warning', text: 'Correct' };
    return { status: 'error', text: 'Critique' };
  };

  const overallStatus = getOverallStatus();

  // Données pour les métriques principales
  const mainMetrics = [
    {
      title: 'Équipements Totaux',
      value: systemData.devices?.total || 0,
      prefix: <CloudServerOutlined />,
      trend: '+2.5%',
      trendUp: true
    },
    {
      title: 'Équipements En Ligne',
      value: systemData.devices?.online || 0,
      prefix: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      suffix: `/ ${systemData.devices?.total || 0}`,
      trend: '+1.2%',
      trendUp: true
    },
    {
      title: 'Alertes Actives',
      value: systemData.alerts?.total || 0,
      prefix: <WarningOutlined style={{ color: '#fa8c16' }} />,
      trend: '-15%',
      trendUp: false
    },
    {
      title: 'Alertes Critiques',
      value: systemData.alerts?.critical || 0,
      prefix: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
      trend: '-8%',
      trendUp: false
    }
  ];

  // Métriques système
  const systemMetrics = [
    {
      name: 'CPU',
      value: systemData.system?.cpu_usage || 0,
      threshold: 80,
      unit: '%'
    },
    {
      name: 'Mémoire',
      value: systemData.system?.memory_usage || 0,
      threshold: 85,
      unit: '%'
    },
    {
      name: 'Disque',
      value: systemData.system?.disk_usage || 0,
      threshold: 90,
      unit: '%'
    }
  ];

  // Alertes récentes (mock data pour l'exemple)
  const recentAlerts = [
    {
      id: 1,
      type: 'warning',
      message: 'CPU élevé détecté sur Switch-Core-01',
      timestamp: '2025-01-01T21:30:00Z',
      severity: 'warning'
    },
    {
      id: 2,
      type: 'error',
      message: 'Perte de connexion Router-DMZ-02',
      timestamp: '2025-01-01T21:25:00Z',
      severity: 'critical'
    },
    {
      id: 3,
      type: 'info',
      message: 'Mise à jour firmware terminée sur AP-Floor2-03',
      timestamp: '2025-01-01T21:20:00Z',
      severity: 'info'
    }
  ];

  // Configuration des colonnes pour le tableau des équipements
  const deviceColumns = [
    {
      title: 'Équipement',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <Avatar 
            size="small" 
            icon={record.type === 'switch' ? <ApiOutlined /> : <CloudServerOutlined />}
          />
          {text}
        </Space>
      )
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => <Tag color="blue">{type.toUpperCase()}</Tag>
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Badge 
          status={status === 'online' ? 'success' : 'error'}
          text={status === 'online' ? 'En ligne' : 'Hors ligne'}
        />
      )
    },
    {
      title: 'Dernière activité',
      dataIndex: 'lastSeen',
      key: 'lastSeen'
    }
  ];

  // Données mock pour les équipements
  const mockDevices = [
    { 
      key: '1', 
      name: 'Switch-Core-01', 
      type: 'switch', 
      status: 'online', 
      lastSeen: 'Il y a 2 min' 
    },
    { 
      key: '2', 
      name: 'Router-DMZ-02', 
      type: 'router', 
      status: 'offline', 
      lastSeen: 'Il y a 5 min' 
    },
    { 
      key: '3', 
      name: 'AP-Floor2-03', 
      type: 'access_point', 
      status: 'online', 
      lastSeen: 'Il y a 1 min' 
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* En-tête avec contrôles */}
      <Card style={{ marginBottom: '16px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space>
              <DashboardOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
              <span style={{ fontSize: '20px', fontWeight: 'bold' }}>
                Dashboard Système
              </span>
              <Badge 
                status={overallStatus.status} 
                text={`Statut: ${overallStatus.text}`}
              />
            </Space>
          </Col>
          <Col>
            <Space>
              <Select
                value={refreshInterval}
                onChange={setRefreshInterval}
                style={{ width: 120 }}
              >
                <Option value={10}>10 sec</Option>
                <Option value={30}>30 sec</Option>
                <Option value={60}>1 min</Option>
                <Option value={300}>5 min</Option>
              </Select>
              
              <Select
                value={selectedTimeRange}
                onChange={setSelectedTimeRange}
                style={{ width: 100 }}
              >
                <Option value="1h">1 heure</Option>
                <Option value="6h">6 heures</Option>
                <Option value="24h">24 heures</Option>
                <Option value="7d">7 jours</Option>
              </Select>

              <Button
                type="primary"
                icon={<ReloadOutlined />}
                onClick={loadAllData}
                loading={dashboardLoading || apiViewsLoading}
              >
                Actualiser
              </Button>

              <Button icon={<SettingOutlined />}>
                Configurer
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Alertes système */}
      {(dashboardError || apiViewsError) && (
        <Alert
          message="Erreur de chargement"
          description={dashboardError?.message || apiViewsError?.message}
          type="error"
          showIcon
          closable
          style={{ marginBottom: '16px' }}
        />
      )}

      {systemData.alerts?.critical > 0 && (
        <Alert
          message={`${systemData.alerts.critical} alerte(s) critique(s) détectée(s)`}
          description="Intervention requise immédiatement"
          type="error"
          showIcon
          style={{ marginBottom: '16px' }}
        />
      )}

      {/* Métriques principales */}
      <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
        {mainMetrics.map((metric, index) => (
          <Col xs={24} sm={12} md={6} key={index}>
            <Card>
              <Statistic
                title={metric.title}
                value={metric.value}
                prefix={metric.prefix}
                suffix={metric.suffix}
                valueStyle={{ 
                  color: metric.title.includes('Alerte') ? '#cf1322' : '#3f8600' 
                }}
              />
              {metric.trend && (
                <div style={{ marginTop: '8px' }}>
                  <Space>
                    {metric.trendUp ? 
                      <RiseOutlined style={{ color: '#3f8600' }} /> :
                      <FallOutlined style={{ color: '#cf1322' }} />
                    }
                    <span style={{ 
                      fontSize: '12px',
                      color: metric.trendUp ? '#3f8600' : '#cf1322'
                    }}>
                      {metric.trend}
                    </span>
                  </Space>
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        {/* Métriques système */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <MonitorOutlined />
                Métriques Système
              </Space>
            }
            extra={<HeartOutlined style={{ color: '#52c41a' }} />}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {systemMetrics.map((metric, index) => (
                <div key={index}>
                  <Row justify="space-between">
                    <Col>{metric.name}</Col>
                    <Col>{metric.value}{metric.unit}</Col>
                  </Row>
                  <Progress
                    percent={metric.value}
                    status={
                      metric.value >= metric.threshold ? 'exception' :
                      metric.value >= metric.threshold * 0.8 ? 'active' : 'success'
                    }
                    showInfo={false}
                    strokeWidth={8}
                  />
                </div>
              ))}
            </Space>
          </Card>
        </Col>

        {/* Alertes récentes */}
        <Col xs={24} lg={12}>
          <Card
            title={
              <Space>
                <BellOutlined />
                Alertes Récentes
              </Space>
            }
            extra={
              <Badge count={systemData.alerts?.total || 0} />
            }
          >
            <List
              dataSource={recentAlerts}
              renderItem={(alert) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Avatar
                        icon={
                          alert.severity === 'critical' ? <CloseCircleOutlined /> :
                          alert.severity === 'warning' ? <WarningOutlined /> :
                          <CheckCircleOutlined />
                        }
                        style={{
                          backgroundColor:
                            alert.severity === 'critical' ? '#ff4d4f' :
                            alert.severity === 'warning' ? '#fa8c16' : '#52c41a'
                        }}
                      />
                    }
                    title={alert.message}
                    description={new Date(alert.timestamp).toLocaleString('fr-FR')}
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* Tableau des équipements */}
      <Card
        title={
          <Space>
            <CloudServerOutlined />
            État des Équipements
          </Space>
        }
        style={{ marginTop: '16px' }}
        extra={
          <Tooltip title="Voir tous les équipements">
            <Button type="link">Voir tout</Button>
          </Tooltip>
        }
      >
        <Table
          columns={deviceColumns}
          dataSource={mockDevices}
          pagination={{ pageSize: 5 }}
          size="small"
        />
      </Card>

      {/* Widgets personnalisés */}
      {activeWidgets.length > 0 && (
        <Card
          title={
            <Space>
              <DashboardOutlined />
              Widgets Personnalisés
            </Space>
          }
          style={{ marginTop: '16px' }}
        >
          <Row gutter={[16, 16]}>
            {activeWidgets.map((widget) => (
              <Col xs={24} sm={12} md={8} key={widget.id}>
                <Card 
                  size="small" 
                  title={widget.title || `Widget ${widget.widget_type}`}
                >
                  <div style={{ textAlign: 'center', padding: '20px' }}>
                    <DashboardOutlined style={{ fontSize: '32px', color: '#d9d9d9' }} />
                    <p style={{ marginTop: '8px', color: '#999' }}>
                      Widget {widget.widget_type}
                    </p>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}
    </div>
  );
};

export default DashboardOverview;