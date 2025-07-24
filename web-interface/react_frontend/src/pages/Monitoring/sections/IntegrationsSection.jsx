/**
 * IntegrationsSection - Hub d'intégrations externes
 * Exploite les endpoints: /external/test-services/, /clients/monitoring/prometheus/
 * Gestion des intégrations avec Prometheus, Grafana, Elasticsearch, etc.
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
  List,
  Avatar,
  Divider,
  Switch,
  Tabs,
  Progress,
  Alert,
  Descriptions,
  Timeline,
  Collapse,
  Radio,
  InputNumber,
  DatePicker,
  Statistic
} from 'antd';
import {
  ApiOutlined,
  LinkOutlined,
  DisconnectOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
  SyncOutlined,
  SettingOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  CloudServerOutlined,
  DatabaseOutlined,
  LineChartOutlined,
  SearchOutlined,
  MonitorOutlined,
  GlobalOutlined,
  SecurityScanOutlined,
  FileSearchOutlined,
  ThunderboltOutlined,
  ClusterOutlined,
  BugOutlined,
  MailOutlined,
  SlackOutlined,
  PhoneOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

// Import du hook monitoring
import useMonitoring from '../../../hooks/useMonitoring';

const { Option } = Select;
const { TabPane } = Tabs;
const { Panel } = Collapse;
const { TextArea } = Input;

const IntegrationsSection = () => {
  // Hook monitoring pour les intégrations
  const {
    integrations,
    fetchIntegrations
  } = useMonitoring();

  // États locaux
  const [activeSubTab, setActiveSubTab] = useState('services');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalType, setModalType] = useState('integration');
  const [editingItem, setEditingItem] = useState(null);
  const [testingService, setTestingService] = useState(null);
  const [form] = Form.useForm();

  // Charger les intégrations au montage
  useEffect(() => {
    if (fetchIntegrations) {
      fetchIntegrations();
    }
  }, [fetchIntegrations]);

  // Services d'intégration avec leurs configurations
  const [integrationServices] = useState([
    {
      id: 1,
      name: 'Prometheus',
      type: 'metrics',
      description: 'Collecte et stockage de métriques temps réel',
      status: 'connected',
      url: 'http://prometheus.local:9090',
      version: '2.45.0',
      lastSync: '2024-02-15T10:30:00',
      health: 95,
      endpoints: [
        '/api/v1/query',
        '/api/v1/query_range',
        '/api/v1/targets'
      ],
      metrics: {
        queries_per_sec: 150,
        storage_size: '2.3GB',
        retention: '15d'
      }
    },
    {
      id: 2,
      name: 'Grafana',
      type: 'visualization',
      description: 'Dashboards et visualisations avancées',
      status: 'connected',
      url: 'http://grafana.local:3000',
      version: '10.2.3',
      lastSync: '2024-02-15T10:28:00',
      health: 98,
      endpoints: [
        '/api/dashboards',
        '/api/datasources',
        '/api/alerts'
      ],
      metrics: {
        dashboards: 12,
        users: 8,
        datasources: 3
      }
    },
    {
      id: 3,
      name: 'Elasticsearch',
      type: 'logs',
      description: 'Recherche et analyse de logs',
      status: 'warning',
      url: 'http://elasticsearch.local:9200',
      version: '8.11.0',
      lastSync: '2024-02-15T10:25:00',
      health: 78,
      endpoints: [
        '/_search',
        '/_cluster/health',
        '/_cat/indices'
      ],
      metrics: {
        indices: 15,
        documents: '2.1M',
        storage: '8.7GB'
      }
    },
    {
      id: 4,
      name: 'SNMP Agents',
      type: 'network',
      description: 'Monitoring équipements réseau via SNMP',
      status: 'connected',
      url: 'snmp://192.168.1.0/24',
      version: 'v2c/v3',
      lastSync: '2024-02-15T10:30:00',
      health: 89,
      endpoints: [
        '.1.3.6.1.2.1.1.1.0', // sysDescr
        '.1.3.6.1.2.1.1.3.0', // sysUpTime
        '.1.3.6.1.2.1.2.2.1.10' // ifInOctets
      ],
      metrics: {
        devices: 24,
        oids_monitored: 156,
        polls_per_min: 480
      }
    },
    {
      id: 5,
      name: 'Nagios Core',
      type: 'monitoring',
      description: 'Système de monitoring traditionnel',
      status: 'disconnected',
      url: 'http://nagios.local/nagios',
      version: '4.4.6',
      lastSync: '2024-02-14T15:22:00',
      health: 0,
      endpoints: [
        '/cgi-bin/status.cgi',
        '/cgi-bin/extinfo.cgi'
      ],
      metrics: {
        services: 0,
        hosts: 0,
        last_check: 'N/A'
      }
    },
    {
      id: 6,
      name: 'Zabbix Server',
      type: 'monitoring',
      description: 'Monitoring enterprise avec agents',
      status: 'error',
      url: 'http://zabbix.local/zabbix',
      version: '6.4.0',
      lastSync: '2024-02-15T09:45:00',
      health: 15,
      endpoints: [
        '/api_jsonrpc.php',
        '/history.php'
      ],
      metrics: {
        hosts: 45,
        items: 1250,
        triggers: 89
      }
    }
  ]);

  // Types d'intégrations avec icônes et couleurs
  const integrationTypes = {
    metrics: { icon: <LineChartOutlined />, color: '#1890ff', label: 'Métriques' },
    visualization: { icon: <MonitorOutlined />, color: '#52c41a', label: 'Visualisation' },
    logs: { icon: <FileSearchOutlined />, color: '#722ed1', label: 'Logs' },
    network: { icon: <GlobalOutlined />, color: '#fa541c', label: 'Réseau' },
    monitoring: { icon: <ClusterOutlined />, color: '#13c2c2', label: 'Monitoring' },
    security: { icon: <SecurityScanOutlined />, color: '#ff4d4f', label: 'Sécurité' },
    notification: { icon: <MailOutlined />, color: '#faad14', label: 'Notification' }
  };

  // Statuts de connexion
  const statusConfig = {
    connected: { color: 'success', text: 'Connecté', icon: <CheckCircleOutlined /> },
    warning: { color: 'warning', text: 'Attention', icon: <WarningOutlined /> },
    error: { color: 'error', text: 'Erreur', icon: <ExclamationCircleOutlined /> },
    disconnected: { color: 'default', text: 'Déconnecté', icon: <DisconnectOutlined /> }
  };

  // Données de tests de connectivité simulées
  const [connectivityTests] = useState([
    {
      id: 1,
      service: 'Prometheus',
      test: 'HTTP Health Check',
      status: 'success',
      responseTime: 45,
      lastRun: '2024-02-15T10:30:00',
      details: 'API accessible, métriques disponibles'
    },
    {
      id: 2,
      service: 'Grafana',
      test: 'API Authentication',
      status: 'success',
      responseTime: 78,
      lastRun: '2024-02-15T10:28:00',
      details: 'Authentification réussie, dashboards accessibles'
    },
    {
      id: 3,
      service: 'Elasticsearch',
      test: 'Cluster Health',
      status: 'warning',
      responseTime: 234,
      lastRun: '2024-02-15T10:25:00',
      details: 'Cluster yellow - réplication partielle'
    },
    {
      id: 4,
      service: 'Nagios Core',
      test: 'Service Availability',
      status: 'error',
      responseTime: 0,
      lastRun: '2024-02-14T15:22:00',
      details: 'Service inaccessible - timeout'
    }
  ]);

  // Colonnes pour la table des services
  const servicesColumns = [
    {
      title: 'Service',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <span style={{ color: integrationTypes[record.type]?.color }}>
            {integrationTypes[record.type]?.icon}
          </span>
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
              {record.description}
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
        <Tag color={integrationTypes[type]?.color}>
          {integrationTypes[type]?.label}
        </Tag>
      ),
      filters: Object.entries(integrationTypes).map(([key, value]) => ({
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
        const config = statusConfig[status] || statusConfig.disconnected;
        return <Badge status={config.color} text={config.text} />;
      }
    },
    {
      title: 'Santé',
      dataIndex: 'health',
      key: 'health',
      render: (health) => (
        <div>
          <Progress 
            percent={health} 
            size="small" 
            strokeColor={
              health >= 90 ? '#52c41a' : 
              health >= 70 ? '#faad14' : '#ff4d4f'
            }
            showInfo={false}
          />
          <div style={{ fontSize: '12px', marginTop: '2px' }}>{health}%</div>
        </div>
      ),
      sorter: (a, b) => a.health - b.health
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
      render: (version) => (
        <Tag size="small">{version}</Tag>
      )
    },
    {
      title: 'Dernière sync',
      dataIndex: 'lastSync',
      key: 'lastSync',
      render: (date) => {
        const d = new Date(date);
        return (
          <div>
            <div style={{ fontSize: '12px' }}>{d.toLocaleDateString()}</div>
            <div style={{ color: '#8c8c8c', fontSize: '11px' }}>
              {d.toLocaleTimeString()}
            </div>
          </div>
        );
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Tester la connexion">
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              size="small"
              onClick={() => testConnection(record)}
              loading={testingService === record.id}
            />
          </Tooltip>
          <Tooltip title="Synchroniser">
            <Button
              type="text"
              icon={<SyncOutlined />}
              size="small"
              onClick={() => syncService(record)}
            />
          </Tooltip>
          <Tooltip title="Configurer">
            <Button
              type="text"
              icon={<SettingOutlined />}
              size="small"
              onClick={() => configureService(record)}
            />
          </Tooltip>
          <Tooltip title="Voir détails">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => showServiceDetails(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // Colonnes pour la table des tests
  const testsColumns = [
    {
      title: 'Service',
      dataIndex: 'service',
      key: 'service'
    },
    {
      title: 'Test',
      dataIndex: 'test',
      key: 'test'
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const config = {
          success: { color: 'success', text: 'Réussi' },
          warning: { color: 'warning', text: 'Attention' },
          error: { color: 'error', text: 'Échec' }
        };
        return <Badge status={config[status]?.color} text={config[status]?.text} />;
      }
    },
    {
      title: 'Temps de réponse',
      dataIndex: 'responseTime',
      key: 'responseTime',
      render: (time) => `${time}ms`,
      sorter: (a, b) => a.responseTime - b.responseTime
    },
    {
      title: 'Dernier test',
      dataIndex: 'lastRun',
      key: 'lastRun',
      render: (date) => new Date(date).toLocaleString()
    },
    {
      title: 'Détails',
      dataIndex: 'details',
      key: 'details'
    }
  ];

  // Actions
  const testConnection = async (service) => {
    setTestingService(service.id);
    try {
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulation
      message.success(`Connexion testée avec succès pour ${service.name}`);
    } finally {
      setTestingService(null);
    }
  };

  const syncService = (service) => {
    message.loading(`Synchronisation de ${service.name}...`, 2)
      .then(() => message.success('Synchronisation terminée'));
  };

  const configureService = (service) => {
    setEditingItem(service);
    setModalType('integration');
    form.setFieldsValue(service);
    setIsModalVisible(true);
    // Utiliser les données d'intégrations si disponibles
    if (integrations && integrations.configure) {
      integrations.configure(service.id);
    }
  };

  const showServiceDetails = (service) => {
    Modal.info({
      title: `Détails - ${service.name}`,
      width: 800,
      content: (
        <div style={{ marginTop: '20px' }}>
          <Descriptions bordered size="small">
            <Descriptions.Item label="Type" span={2}>
              <Tag color={integrationTypes[service.type]?.color}>
                {integrationTypes[service.type]?.icon} {integrationTypes[service.type]?.label}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Statut">
              <Badge status={statusConfig[service.status]?.color} text={statusConfig[service.status]?.text} />
            </Descriptions.Item>
            <Descriptions.Item label="URL" span={3}>
              {service.url}
            </Descriptions.Item>
            <Descriptions.Item label="Version">
              {service.version}
            </Descriptions.Item>
            <Descriptions.Item label="Santé">
              <Progress percent={service.health} size="small" />
            </Descriptions.Item>
            <Descriptions.Item label="Dernière sync">
              {new Date(service.lastSync).toLocaleString()}
            </Descriptions.Item>
          </Descriptions>
          
          <Divider>Endpoints</Divider>
          <List
            size="small"
            dataSource={service.endpoints}
            renderItem={endpoint => (
              <List.Item>
                <code>{endpoint}</code>
              </List.Item>
            )}
          />

          <Divider>Métriques</Divider>
          <Row gutter={[16, 16]}>
            {Object.entries(service.metrics).map(([key, value]) => (
              <Col span={8} key={key}>
                <Statistic title={key.replace('_', ' ')} value={value} />
              </Col>
            ))}
          </Row>
        </div>
      )
    });
  };

  // Rendu des statistiques d'intégrations
  const renderIntegrationsStats = () => {
    const totalServices = integrationServices.length;
    const connectedServices = integrationServices.filter(s => s.status === 'connected').length;
    const warningServices = integrationServices.filter(s => s.status === 'warning').length;
    const errorServices = integrationServices.filter(s => s.status === 'error' || s.status === 'disconnected').length;

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Services"
              value={totalServices}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Connectés"
              value={connectedServices}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Attention"
              value={warningServices}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Problèmes"
              value={errorServices}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // Rendu de la liste des services
  const renderServicesList = () => (
    <Card 
      title={
        <Space>
          <ApiOutlined />
          <span>Services d'Intégration</span>
        </Space>
      }
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => message.info('Actualisation des services...')}
          >
            Actualiser tout
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setModalType('integration');
              setEditingItem(null);
              setIsModalVisible(true);
            }}
          >
            Ajouter service
          </Button>
        </Space>
      }
    >
      <Table
        columns={servicesColumns}
        dataSource={integrationServices}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10,
          showSizeChanger: true
        }}
      />
    </Card>
  );

  // Rendu des tests de connectivité
  const renderConnectivityTests = () => (
    <Card 
      title={
        <Space>
          <PlayCircleOutlined />
          <span>Tests de Connectivité</span>
        </Space>
      }
      extra={
        <Button
          type="primary"
          icon={<PlayCircleOutlined />}
          onClick={() => message.info('Lancement de tous les tests...')}
        >
          Tester tout
        </Button>
      }
    >
      <Table
        columns={testsColumns}
        dataSource={connectivityTests}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10
        }}
      />
    </Card>
  );

  // Rendu de la configuration des intégrations
  const renderConfigurations = () => (
    <Card title="Configurations d'Intégration">
      <Collapse>
        <Panel header="Configuration Prometheus" key="prometheus">
          <Form layout="vertical">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Form.Item label="URL du serveur">
                  <Input defaultValue="http://prometheus.local:9090" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Intervalle de collecte">
                  <Select defaultValue="30s">
                    <Option value="10s">10 secondes</Option>
                    <Option value="30s">30 secondes</Option>
                    <Option value="1m">1 minute</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </Panel>
        
        <Panel header="Configuration Grafana" key="grafana">
          <Form layout="vertical">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Form.Item label="URL du serveur">
                  <Input defaultValue="http://grafana.local:3000" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Token API">
                  <Input.Password placeholder="Entrez le token API" />
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </Panel>
        
        <Panel header="Configuration SNMP" key="snmp">
          <Form layout="vertical">
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Form.Item label="Version SNMP">
                  <Select defaultValue="v2c">
                    <Option value="v1">v1</Option>
                    <Option value="v2c">v2c</Option>
                    <Option value="v3">v3</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="Community">
                  <Input defaultValue="public" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="Port">
                  <InputNumber defaultValue={161} style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            </Row>
          </Form>
        </Panel>
      </Collapse>
    </Card>
  );

  return (
    <div style={{ padding: '0' }}>
      {/* Statistiques globales */}
      {renderIntegrationsStats()}

      {/* Onglets pour les sous-sections */}
      <Tabs activeKey={activeSubTab} onChange={setActiveSubTab}>
        <TabPane
          tab={
            <Space>
              <ApiOutlined />
              <span>Services</span>
            </Space>
          }
          key="services"
        >
          {renderServicesList()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <PlayCircleOutlined />
              <span>Tests</span>
              <Badge count={connectivityTests.filter(t => t.status === 'error').length} />
            </Space>
          }
          key="tests"
        >
          {renderConnectivityTests()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <SettingOutlined />
              <span>Configuration</span>
            </Space>
          }
          key="config"
        >
          {renderConfigurations()}
        </TabPane>
      </Tabs>

      {/* Modal de configuration */}
      <Modal
        title={`Configuration ${modalType}`}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingItem(null);
        }}
        onOk={() => {
          if (editingItem) {
            message.success('Configuration mise à jour');
          }
          setIsModalVisible(false);
          setEditingItem(null);
        }}
      >
        <p>Configuration {modalType} - Interface complète à implémenter</p>
        {editingItem && <p>Service: {editingItem.name}</p>}
      </Modal>
    </div>
  );
};

export default IntegrationsSection;