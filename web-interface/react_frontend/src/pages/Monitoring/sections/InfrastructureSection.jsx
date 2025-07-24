/**
 * InfrastructureSection - Gestion de l'infrastructure et topologie réseau
 * Exploite les endpoints: /topology/, /device-checks/, /service-checks/
 * Cartographie réseau, health checks et monitoring des équipements
 */

import React, { useState, useEffect } from 'react';
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
  Progress,
  Statistic,
  Timeline,
  Divider,
  Alert,
  Spin,
  Switch,
  Tabs
} from 'antd';
import {
  ClusterOutlined,
  AppstoreOutlined,
  SafetyOutlined,
  SearchOutlined,
  SyncOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  DisconnectOutlined,
  LinkOutlined,
  CloudServerOutlined,
  GlobalOutlined,
  WifiOutlined,
  DatabaseOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, ScatterChart, Scatter, Cell } from 'recharts';

// Import du hook monitoring
import useMonitoring from '../../../hooks/useMonitoring';

const { Option } = Select;
const { TabPane } = Tabs;

const InfrastructureSection = () => {
  // Hook monitoring pour l'infrastructure
  const {
    infrastructure,
    fetchInfrastructure
  } = useMonitoring();

  // États locaux
  const [activeSubTab, setActiveSubTab] = useState('topology');
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [isMonitoring, setIsMonitoring] = useState(true);
  const [filters, setFilters] = useState({
    status: 'all',
    type: 'all',
    location: 'all'
  });

  // Types d'équipements avec icônes
  const deviceTypes = {
    router: { icon: <GlobalOutlined />, color: '#1890ff', label: 'Routeur' },
    switch: { icon: <AppstoreOutlined />, color: '#52c41a', label: 'Switch' },
    server: { icon: <CloudServerOutlined />, color: '#722ed1', label: 'Serveur' },
    firewall: { icon: <SafetyOutlined />, color: '#fa541c', label: 'Pare-feu' },
    access_point: { icon: <WifiOutlined />, color: '#13c2c2', label: 'Point d\'accès' },
    database: { icon: <DatabaseOutlined />, color: '#eb2f96', label: 'Base de données' },
    load_balancer: { icon: <ThunderboltOutlined />, color: '#faad14', label: 'Load Balancer' }
  };

  // Données simulées pour la topologie (à remplacer par infrastructure.topology.devices)
  const [topologyDevices] = useState([
    {
      id: 1,
      name: 'router-core-01',
      type: 'router',
      status: 'healthy',
      ip: '192.168.1.1',
      location: 'DC-Paris',
      uptime: '99.9%',
      lastCheck: '2024-02-15T10:30:00',
      interfaces: [
        { name: 'eth0', status: 'up', utilization: 45 },
        { name: 'eth1', status: 'up', utilization: 23 },
        { name: 'eth2', status: 'down', utilization: 0 }
      ],
      metrics: {
        cpu: 34,
        memory: 67,
        temperature: 42
      }
    },
    {
      id: 2,
      name: 'switch-access-01',
      type: 'switch',
      status: 'warning',
      ip: '192.168.1.10',
      location: 'DC-Paris',
      uptime: '98.7%',
      lastCheck: '2024-02-15T10:29:00',
      interfaces: [
        { name: 'port1', status: 'up', utilization: 78 },
        { name: 'port2', status: 'up', utilization: 12 },
        { name: 'port3', status: 'up', utilization: 89 }
      ],
      metrics: {
        cpu: 23,
        memory: 45,
        temperature: 38
      }
    },
    {
      id: 3,
      name: 'srv-web-01',
      type: 'server',
      status: 'critical',
      ip: '192.168.1.100',
      location: 'DC-Lyon',
      uptime: '95.2%',
      lastCheck: '2024-02-15T10:28:00',
      interfaces: [
        { name: 'ens33', status: 'up', utilization: 95 }
      ],
      metrics: {
        cpu: 89,
        memory: 92,
        temperature: 78
      }
    },
    {
      id: 4,
      name: 'fw-perimeter-01',
      type: 'firewall',
      status: 'healthy',
      ip: '192.168.1.2',
      location: 'DC-Paris',
      uptime: '99.8%',
      lastCheck: '2024-02-15T10:30:00',
      interfaces: [
        { name: 'outside', status: 'up', utilization: 34 },
        { name: 'inside', status: 'up', utilization: 56 }
      ],
      metrics: {
        cpu: 28,
        memory: 41,
        temperature: 35
      }
    }
  ]);

  // Health checks simulés
  const [healthChecks] = useState([
    {
      id: 1,
      device: 'router-core-01',
      check: 'SNMP Connectivity',
      status: 'passing',
      lastRun: '2024-02-15T10:30:00',
      nextRun: '2024-02-15T10:35:00',
      interval: '5m'
    },
    {
      id: 2,
      device: 'switch-access-01',
      check: 'Interface Status',
      status: 'warning',
      lastRun: '2024-02-15T10:29:00',
      nextRun: '2024-02-15T10:34:00',
      interval: '5m'
    },
    {
      id: 3,
      device: 'srv-web-01',
      check: 'HTTP Service',
      status: 'critical',
      lastRun: '2024-02-15T10:28:00',
      nextRun: '2024-02-15T10:33:00',
      interval: '1m'
    }
  ]);

  // Couleurs pour les statuts
  const statusColors = {
    healthy: '#52c41a',
    warning: '#faad14',
    critical: '#ff4d4f',
    unknown: '#8c8c8c'
  };

  // Colonnes pour la table des équipements
  const deviceColumns = [
    {
      title: 'Équipement',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <span style={{ color: deviceTypes[record.type]?.color }}>
            {deviceTypes[record.type]?.icon}
          </span>
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
              {record.ip} - {record.location}
            </div>
          </div>
        </Space>
      )
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => (
        <Tag color={deviceTypes[type]?.color}>
          {deviceTypes[type]?.label}
        </Tag>
      ),
      filters: Object.entries(deviceTypes).map(([key, value]) => ({
        text: value.label,
        value: key
      })),
      onFilter: (value, record) => record.type === value
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusConfig = {
          healthy: { color: 'success', text: 'Sain' },
          warning: { color: 'warning', text: 'Attention' },
          critical: { color: 'error', text: 'Critique' },
          unknown: { color: 'default', text: 'Inconnu' }
        };
        const config = statusConfig[status] || statusConfig.unknown;
        return <Badge status={config.color} text={config.text} />;
      },
      filters: [
        { text: 'Sain', value: 'healthy' },
        { text: 'Attention', value: 'warning' },
        { text: 'Critique', value: 'critical' },
        { text: 'Inconnu', value: 'unknown' }
      ],
      onFilter: (value, record) => record.status === value
    },
    {
      title: 'Disponibilité',
      dataIndex: 'uptime',
      key: 'uptime',
      render: (uptime, record) => (
        <div>
          <Progress 
            percent={parseFloat(uptime)} 
            size="small" 
            strokeColor={statusColors[record.status]}
            showInfo={false}
          />
          <div style={{ fontSize: '12px', marginTop: '2px' }}>{uptime}</div>
        </div>
      ),
      sorter: (a, b) => parseFloat(a.uptime) - parseFloat(b.uptime)
    },
    {
      title: 'Métriques',
      key: 'metrics',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <div style={{ fontSize: '12px' }}>
            <span style={{ color: '#8c8c8c' }}>CPU:</span> {record.metrics.cpu}%
          </div>
          <div style={{ fontSize: '12px' }}>
            <span style={{ color: '#8c8c8c' }}>MEM:</span> {record.metrics.memory}%
          </div>
          <div style={{ fontSize: '12px' }}>
            <span style={{ color: '#8c8c8c' }}>TEMP:</span> {record.metrics.temperature}°C
          </div>
        </Space>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Voir détails">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => showDeviceDetails(record)}
            />
          </Tooltip>
          <Tooltip title="Lancer vérification">
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              size="small"
              onClick={() => runHealthCheck(record)}
            />
          </Tooltip>
          <Tooltip title="Configuration">
            <Button
              type="text"
              icon={<SettingOutlined />}
              size="small"
              onClick={() => configureDevice(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // Colonnes pour la table des health checks
  const checksColumns = [
    {
      title: 'Équipement',
      dataIndex: 'device',
      key: 'device'
    },
    {
      title: 'Vérification',
      dataIndex: 'check',
      key: 'check'
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusConfig = {
          passing: { color: 'success', text: 'Réussi' },
          warning: { color: 'warning', text: 'Attention' },
          critical: { color: 'error', text: 'Échec' }
        };
        const config = statusConfig[status] || statusConfig.critical;
        return <Badge status={config.color} text={config.text} />;
      }
    },
    {
      title: 'Dernière exécution',
      dataIndex: 'lastRun',
      key: 'lastRun',
      render: (date) => new Date(date).toLocaleString()
    },
    {
      title: 'Prochaine exécution',
      dataIndex: 'nextRun',
      key: 'nextRun',
      render: (date) => new Date(date).toLocaleString()
    },
    {
      title: 'Intervalle',
      dataIndex: 'interval',
      key: 'interval'
    }
  ];

  // Charger l'infrastructure au montage
  useEffect(() => {
    if (fetchInfrastructure) {
      fetchInfrastructure();
    }
  }, [fetchInfrastructure]);

  // Actions
  const showDeviceDetails = (device) => {
    setSelectedDevice(device);
    Modal.info({
      title: `Détails - ${device.name}`,
      width: 800,
      content: (
        <div style={{ marginTop: '20px' }}>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Statistic title="CPU" value={device.metrics.cpu} suffix="%" />
                <Progress percent={device.metrics.cpu} strokeColor={statusColors[device.status]} />
              </Space>
            </Col>
            <Col span={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Statistic title="Mémoire" value={device.metrics.memory} suffix="%" />
                <Progress percent={device.metrics.memory} strokeColor={statusColors[device.status]} />
              </Space>
            </Col>
            <Col span={24}>
              <Divider>Interfaces</Divider>
              {device.interfaces.map((iface, index) => (
                <div key={index} style={{ marginBottom: '8px' }}>
                  <Space>
                    <Badge 
                      status={iface.status === 'up' ? 'success' : 'error'} 
                      text={iface.name}
                    />
                    <span>Utilisation: {iface.utilization}%</span>
                  </Space>
                </div>
              ))}
            </Col>
          </Row>
        </div>
      )
    });
  };

  const runHealthCheck = (device) => {
    message.loading('Lancement de la vérification...', 2)
      .then(() => message.success(`Vérification terminée pour ${device.name}`));
  };

  const configureDevice = (device) => {
    message.info(`Configuration de ${device.name} - Fonctionnalité à développer`);
  };

  // Rendu des statistiques d'infrastructure
  const renderInfrastructureStats = () => {
    const healthyCount = topologyDevices.filter(d => d.status === 'healthy').length;
    const warningCount = topologyDevices.filter(d => d.status === 'warning').length;
    const criticalCount = topologyDevices.filter(d => d.status === 'critical').length;
    const totalDevices = topologyDevices.length;

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Équipements"
              value={totalDevices}
              prefix={<ClusterOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Sains"
              value={healthyCount}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: statusColors.healthy }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Attention"
              value={warningCount}
              prefix={<WarningOutlined />}
              valueStyle={{ color: statusColors.warning }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Critiques"
              value={criticalCount}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: statusColors.critical }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // Rendu de la topologie (version simplifiée)
  const renderTopologyView = () => (
    <Card 
      title={
        <Space>
          <AppstoreOutlined />
          <span>Topologie Réseau</span>
          <Switch 
            checked={isMonitoring} 
            onChange={setIsMonitoring}
            size="small"
          />
          <span style={{ fontSize: '12px' }}>Monitoring temps réel</span>
        </Space>
      }
      extra={
        <Button 
          icon={<SyncOutlined />} 
          onClick={fetchInfrastructure}
          loading={infrastructure.loading}
        >
          Synchroniser
        </Button>
      }
    >
      <Table
        columns={deviceColumns}
        dataSource={topologyDevices}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true
        }}
        size="small"
      />
    </Card>
  );

  // Rendu des health checks
  const renderHealthChecks = () => (
    <Card 
      title={
        <Space>
          <SafetyOutlined />
          <span>Vérifications de Santé</span>
        </Space>
      }
      extra={
        <Button 
          icon={<PlayCircleOutlined />}
          type="primary"
          onClick={() => message.info('Lancement de toutes les vérifications...')}
        >
          Tout vérifier
        </Button>
      }
    >
      <Table
        columns={checksColumns}
        dataSource={healthChecks}
        rowKey="id"
        pagination={{
          pageSize: 10
        }}
        size="small"
      />
    </Card>
  );

  // Rendu des filtres
  const renderFilters = () => (
    <Card size="small" style={{ marginBottom: '16px' }}>
      <Row gutter={[16, 16]} align="middle">
        <Col xs={24} sm={8}>
          <Input
            placeholder="Rechercher un équipement..."
            prefix={<SearchOutlined />}
            allowClear
          />
        </Col>
        <Col xs={24} sm={4}>
          <Select
            placeholder="Statut"
            style={{ width: '100%' }}
            value={filters.status}
            onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
          >
            <Option value="all">Tous</Option>
            <Option value="healthy">Sains</Option>
            <Option value="warning">Attention</Option>
            <Option value="critical">Critiques</Option>
          </Select>
        </Col>
        <Col xs={24} sm={4}>
          <Select
            placeholder="Type"
            style={{ width: '100%' }}
            value={filters.type}
            onChange={(value) => setFilters(prev => ({ ...prev, type: value }))}
          >
            <Option value="all">Tous types</Option>
            {Object.entries(deviceTypes).map(([key, value]) => (
              <Option key={key} value={key}>{value.label}</Option>
            ))}
          </Select>
        </Col>
        <Col xs={24} sm={4}>
          <Select
            placeholder="Localisation"
            style={{ width: '100%' }}
            value={filters.location}
            onChange={(value) => setFilters(prev => ({ ...prev, location: value }))}
          >
            <Option value="all">Toutes</Option>
            <Option value="DC-Paris">DC-Paris</Option>
            <Option value="DC-Lyon">DC-Lyon</Option>
          </Select>
        </Col>
      </Row>
    </Card>
  );

  return (
    <div style={{ padding: '0' }}>
      {/* Statistiques globales */}
      {renderInfrastructureStats()}

      {/* Filtres */}
      {renderFilters()}

      {/* Affichage du device sélectionné */}
      {selectedDevice && (
        <Alert
          message={`Device sélectionné: ${selectedDevice.name}`}
          type="info"
          style={{ marginBottom: '16px' }}
          closable
          onClose={() => setSelectedDevice(null)}
        />
      )}

      {/* Onglets pour les sous-sections */}
      <Tabs activeKey={activeSubTab} onChange={setActiveSubTab}>
        <TabPane
          tab={
            <Space>
              <AppstoreOutlined />
              <span>Topologie</span>
            </Space>
          }
          key="topology"
        >
          {renderTopologyView()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <SafetyOutlined />
              <span>Health Checks</span>
              <Badge count={healthChecks.filter(c => c.status === 'critical').length} />
            </Space>
          }
          key="checks"
        >
          {renderHealthChecks()}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default InfrastructureSection;