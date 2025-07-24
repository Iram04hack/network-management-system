/**
 * OverviewSection - Configuration et surveillance monitoring spécialisée
 * Conforme aux spécifications: surveillance détaillée uniquement (pas de vue d'ensemble)
 * Endpoints: /monitoring/metrics/realtime/, /monitoring/alerts/, /monitoring/history/, /monitoring/thresholds/
 * Focus: Configuration surveillance, métriques détaillées, seuils personnalisables
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Badge,
  Alert,
  Space,
  Button,
  Tooltip,
  Divider,
  Tag,
  Timeline,
  List,
  Avatar
} from 'antd';
import {
  DashboardOutlined,
  AlertOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  GlobalOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
  EyeOutlined,
  TrophyOutlined,
  SearchOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area, BarChart, Bar } from 'recharts';

// Import du hook monitoring
import useMonitoring from '../../../hooks/useMonitoring';

const OverviewSection = () => {
  // Hook monitoring pour la vue d'ensemble
  const {
    realTimeMetrics,
    alerts,
    specializedMonitoring,
    integrations,
    thresholds,
    fetchOverview,
    criticalAlertsCount,
    systemHealthy,
    currentCpuUsage,
    currentMemoryUsage,
    currentNetworkUsage,
    currentDiskUsage
  } = useMonitoring();

  // États locaux pour les données temporaires (en attendant l'API)
  const [cpuData, setCpuData] = useState([]);
  const [memoryData, setMemoryData] = useState([]);
  const [networkData, setNetworkData] = useState([]);

  // Utilisation des vraies données de l'API
  useEffect(() => {
    // Utiliser les vraies données des métriques temps réel
    if (realTimeMetrics.cpu.history && realTimeMetrics.cpu.history.length > 0) {
      setCpuData(realTimeMetrics.cpu.history.map(item => ({
        time: new Date(item.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        value: item.value
      })));
    } else {
      // Fallback avec valeur actuelle si pas d'historique
      const currentTime = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      setCpuData([{ time: currentTime, value: currentCpuUsage }]);
    }

    if (realTimeMetrics.memory.history && realTimeMetrics.memory.history.length > 0) {
      setMemoryData(realTimeMetrics.memory.history.map(item => ({
        time: new Date(item.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        value: item.value
      })));
    } else {
      const currentTime = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      setMemoryData([{ time: currentTime, value: currentMemoryUsage }]);
    }

    if (realTimeMetrics.network.history && realTimeMetrics.network.history.length > 0) {
      setNetworkData(realTimeMetrics.network.history.map(item => ({
        time: new Date(item.timestamp).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        value: item.value
      })));
    } else {
      const currentTime = new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
      setNetworkData([{ time: currentTime, value: currentNetworkUsage }]);
    }

    // Charger l'aperçu si pas encore chargé
    if (!realTimeMetrics.lastUpdate) {
      fetchOverview();
    }
  }, [realTimeMetrics, fetchOverview, currentCpuUsage, currentMemoryUsage, currentNetworkUsage]);

  // Couleurs pour les graphiques
  const COLORS = {
    primary: '#1890ff',
    success: '#52c41a',
    warning: '#faad14',
    error: '#ff4d4f',
    purple: '#722ed1',
    cyan: '#13c2c2'
  };

  // Données pour le graphique en secteurs des alertes
  const alertsDistribution = [
    { name: 'Critiques', value: criticalAlertsCount, color: COLORS.error },
    { name: 'Élevées', value: alerts.list.filter(a => a.severity === 'high').length, color: COLORS.warning },
    { name: 'Moyennes', value: alerts.list.filter(a => a.severity === 'medium').length, color: COLORS.primary },
    { name: 'Basses', value: alerts.list.filter(a => a.severity === 'low').length, color: COLORS.success }
  ].filter(item => item.value > 0);

  // Services de monitoring avec statut
  const monitoringServices = [
    { name: 'Prometheus', status: 'healthy', uptime: '99.9%', icon: <DatabaseOutlined />, color: COLORS.success },
    { name: 'Grafana', status: 'healthy', uptime: '99.7%', icon: <DashboardOutlined />, color: COLORS.success },
    { name: 'Elasticsearch', status: 'warning', uptime: '98.5%', icon: <SearchOutlined />, color: COLORS.warning },
    { name: 'Netdata', status: 'healthy', uptime: '99.8%', icon: <LineChartOutlined />, color: COLORS.success },
    { name: 'ntopng', status: 'healthy', uptime: '99.6%', icon: <GlobalOutlined />, color: COLORS.success }
  ];

  // Activité récente (simulée)
  const recentActivity = [
    {
      time: '2 min',
      type: 'alert',
      message: 'Nouvelle alerte critique sur serveur-web-01',
      icon: <AlertOutlined style={{ color: COLORS.error }} />
    },
    {
      time: '15 min',
      type: 'resolve',
      message: 'Alerte réseau résolue automatiquement',
      icon: <CheckCircleOutlined style={{ color: COLORS.success }} />
    },
    {
      time: '1h',
      type: 'maintenance',
      message: 'Maintenance planifiée démarrée sur cluster DB',
      icon: <ClockCircleOutlined style={{ color: COLORS.primary }} />
    },
    {
      time: '3h',
      type: 'deployment',
      message: 'Nouveau dashboard déployé avec succès',
      icon: <TrophyOutlined style={{ color: COLORS.success }} />
    }
  ];

  // Configuration des seuils de surveillance
  const renderThresholdConfiguration = () => (
    <Card
      title={
        <Space>
          <ExclamationCircleOutlined style={{ color: COLORS.warning }} />
          <span>Configuration des Seuils</span>
        </Space>
      }
      size="small"
      style={{ marginBottom: '24px' }}
    >
      <Row gutter={[16, 16]}>
        <Col xs={24} md={8}>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontWeight: 500, marginBottom: '8px' }}>CPU (Critique)</div>
            <Progress 
              percent={85} 
              strokeColor={COLORS.error}
              size="small"
              format={() => '85%'}
            />
            <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>Déclenche une alerte critique</div>
          </div>
        </Col>
        <Col xs={24} md={8}>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontWeight: 500, marginBottom: '8px' }}>Mémoire (Attention)</div>
            <Progress 
              percent={75} 
              strokeColor={COLORS.warning}
              size="small"
              format={() => '75%'}
            />
            <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>Déclenche une alerte d'attention</div>
          </div>
        </Col>
        <Col xs={24} md={8}>
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontWeight: 500, marginBottom: '8px' }}>Réseau (Critique)</div>
            <Progress 
              percent={90} 
              strokeColor={COLORS.error}
              size="small"
              format={() => '90%'}
            />
            <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>Déclenche une alerte critique</div>
          </div>
        </Col>
      </Row>
      <Space style={{ marginTop: '16px' }}>
        <Button type="primary" size="small">Configurer les seuils</Button>
        <Button size="small">Réinitialiser par défaut</Button>
      </Space>
    </Card>
  );

  // Rendu des métriques système
  const renderSystemMetrics = () => (
    <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
      <Col xs={24} lg={8}>
        <Card 
          title={
            <Space>
              <ThunderboltOutlined style={{ color: COLORS.warning }} />
              <span>CPU - Dernières 24h</span>
            </Space>
          }
          size="small"
        >
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={cpuData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 100]} />
              <RechartsTooltip />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke={COLORS.warning} 
                fill={COLORS.warning}
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
          <div style={{ textAlign: 'center', marginTop: '8px' }}>
            <Statistic 
              value={currentCpuUsage || cpuData[cpuData.length - 1]?.value || 0} 
              precision={1}
              suffix="%" 
              valueStyle={{ fontSize: '16px' }}
            />
          </div>
        </Card>
      </Col>
      <Col xs={24} lg={8}>
        <Card 
          title={
            <Space>
              <DatabaseOutlined style={{ color: COLORS.primary }} />
              <span>Mémoire - Dernières 24h</span>
            </Space>
          }
          size="small"
        >
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={memoryData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 100]} />
              <RechartsTooltip />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke={COLORS.primary} 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
          <div style={{ textAlign: 'center', marginTop: '8px' }}>
            <Statistic 
              value={currentMemoryUsage || memoryData[memoryData.length - 1]?.value || 0} 
              precision={1}
              suffix="%" 
              valueStyle={{ fontSize: '16px' }}
            />
          </div>
        </Card>
      </Col>
      <Col xs={24} lg={8}>
        <Card 
          title={
            <Space>
              <GlobalOutlined style={{ color: COLORS.cyan }} />
              <span>Réseau - Dernières 24h</span>
            </Space>
          }
          size="small"
        >
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={networkData.slice(-12)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 100]} />
              <RechartsTooltip />
              <Bar dataKey="value" fill={COLORS.cyan} />
            </BarChart>
          </ResponsiveContainer>
          <div style={{ textAlign: 'center', marginTop: '8px' }}>
            <Statistic 
              value={currentNetworkUsage || networkData[networkData.length - 1]?.value || 0} 
              precision={1}
              suffix=" MB" 
              valueStyle={{ fontSize: '16px' }}
            />
          </div>
        </Card>
      </Col>
    </Row>
  );

  // Historique des métriques détaillées
  const renderMetricsHistory = () => (
    <Card 
      title={
        <Space>
          <LineChartOutlined style={{ color: COLORS.primary }} />
          <span>Historique des Métriques</span>
          <Tooltip title="Conservation et analyse des données historiques">
            <Button type="text" size="small" icon={<EyeOutlined />} />
          </Tooltip>
        </Space>
      }
      size="small"
      style={{ height: '350px' }}
    >
      <Space style={{ marginBottom: '16px' }}>
        <Button size="small" type="primary">Dernière heure</Button>
        <Button size="small">Dernières 24h</Button>
        <Button size="small">7 jours</Button>
        <Button size="small">30 jours</Button>
      </Space>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={cpuData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[0, 100]} />
          <RechartsTooltip />
          <Line 
            type="monotone" 
            dataKey="value" 
            stroke={COLORS.primary} 
            strokeWidth={2}
            dot={false}
            name="CPU %"
          />
        </LineChart>
      </ResponsiveContainer>
      <div style={{ textAlign: 'center', marginTop: '8px' }}>
        <Space>
          <Button size="small">Exporter CSV</Button>
          <Button size="small">Analyser tendances</Button>
        </Space>
      </div>
    </Card>
  );

  // Surveillance temps réel spécialisée
  const renderRealTimeMonitoring = () => (
    <Card 
      title={
        <Space>
          <ThunderboltOutlined style={{ color: COLORS.success }} />
          <span>Surveillance Temps Réel</span>
          <Badge status="processing" text="Live" />
        </Space>
      }
      size="small"
      style={{ height: '350px' }}
    >
      <div style={{ marginBottom: '16px' }}>
        <Space>
          <Button size="small" type="primary">CPU</Button>
          <Button size="small">Mémoire</Button>
          <Button size="small">Réseau</Button>
          <Button size="small">Disque</Button>
        </Space>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={cpuData.slice(-10)}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[0, 100]} />
          <RechartsTooltip />
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke={COLORS.success} 
            fill={COLORS.success}
            fillOpacity={0.3}
          />
        </AreaChart>
      </ResponsiveContainer>
      <div style={{ textAlign: 'center', marginTop: '16px' }}>
        <Space>
          <Statistic 
            title="Actuel" 
            value={currentCpuUsage || cpuData[cpuData.length - 1]?.value || 0} 
            precision={1}
            suffix="%" 
            valueStyle={{ fontSize: '16px', color: COLORS.success }}
          />
          <Statistic 
            title="Moyenne" 
            value={cpuData.length > 0 ? cpuData.reduce((sum, d) => sum + d.value, 0) / cpuData.length : 0} 
            precision={1}
            suffix="%" 
            valueStyle={{ fontSize: '16px', color: COLORS.primary }}
          />
        </Space>
      </div>
    </Card>
  );

  // Configuration des alertes avancées
  const renderAlertConfiguration = () => (
    <Card 
      title={
        <Space>
          <AlertOutlined style={{ color: COLORS.error }} />
          <span>Configuration des Alertes</span>
        </Space>
      }
      size="small"
      style={{ height: '350px' }}
    >
      <div style={{ marginBottom: '16px' }}>
        <Alert
          message="Surveillance Active"
          description={`${alerts.list.filter(a => a.status === 'active').length} alertes actives détectées`}
          type={criticalAlertsCount > 0 ? 'error' : 'info'}
          showIcon
          style={{ marginBottom: '16px' }}
        />
      </div>
      <List
        size="small"
        dataSource={[
          { name: 'CPU > 85%', enabled: true, severity: 'critique' },
          { name: 'Mémoire > 75%', enabled: true, severity: 'attention' },
          { name: 'Réseau > 90%', enabled: true, severity: 'critique' },
          { name: 'Disque > 80%', enabled: false, severity: 'attention' }
        ]}
        renderItem={(rule) => (
          <List.Item>
            <Space>
              <Badge 
                status={rule.enabled ? 'success' : 'default'} 
                text={rule.name}
              />
              <Tag color={rule.severity === 'critique' ? 'red' : 'orange'}>
                {rule.severity}
              </Tag>
            </Space>
          </List.Item>
        )}
      />
      <div style={{ textAlign: 'center', marginTop: '16px' }}>
        <Space>
          <Button size="small" type="primary">Configurer règles</Button>
          <Button size="small">Tester alertes</Button>
        </Space>
      </div>
    </Card>
  );

  // Gestion des erreurs
  if (realTimeMetrics.error) {
    return (
      <Alert
        message="Erreur de chargement"
        description={realTimeMetrics.error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={fetchOverview}>
            Réessayer
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ padding: '0' }}>
      {/* Configuration des seuils de surveillance */}
      {renderThresholdConfiguration()}

      {/* Métriques système temps réel détaillées */}
      {renderSystemMetrics()}

      {/* Ligne spécialisée : Historique, Temps réel, Configuration alertes */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          {renderMetricsHistory()}
        </Col>
        <Col xs={24} lg={8}>
          {renderRealTimeMonitoring()}
        </Col>
        <Col xs={24} lg={8}>
          {renderAlertConfiguration()}
        </Col>
      </Row>
    </div>
  );
};

export default OverviewSection;