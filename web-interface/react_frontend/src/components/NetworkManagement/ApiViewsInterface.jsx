/**
 * API Views Interface - Interface pour les vues agrégées
 * Composant principal pour le module api_views
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Row,
  Col,
  Tabs,
  Statistic,
  Alert,
  Badge,
  Tag,
  Progress,
  List,
  Avatar,
  Tooltip,
  Form,
  Modal,
  Steps,
  Tree,
  Timeline,
  Divider
} from 'antd';
import {
  SearchOutlined,
  EyeOutlined,
  BarChartOutlined,
  NodeIndexOutlined,
  ApartmentOutlined,
  GlobalOutlined,
  RadarChartOutlined,
  ClusterOutlined,
  ReloadOutlined,
  DownloadOutlined,
  FilterOutlined,
  SettingOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { useApiViews } from '../../hooks/useApiViews';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;
const { Step } = Steps;

/**
 * Composant principal des vues API
 */
const ApiViewsInterface = () => {
  const {
    dashboardData,
    systemOverview,
    networkOverview,
    searchResults,
    discoveryStatus,
    loading,
    error,
    fetchDashboardOverview,
    fetchSystemOverview,
    fetchNetworkOverview,
    performGlobalSearch,
    startTopologyDiscovery,
    getTopologyDiscoveryStatus,
    clearError
  } = useApiViews();

  const [activeTab, setActiveTab] = useState('overview');
  const [searchQuery, setSearchQuery] = useState('');
  const [discoveryModal, setDiscoveryModal] = useState(false);
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [form] = Form.useForm();

  // Charger les données au montage
  useEffect(() => {
    loadInitialData();
  }, []);

  // Charger toutes les données initiales
  const loadInitialData = async () => {
    try {
      await Promise.all([
        fetchDashboardOverview(),
        fetchSystemOverview(),
        fetchNetworkOverview()
      ]);
    } catch (error) {
      console.error('Erreur chargement données:', error);
    }
  };

  // Recherche globale
  const handleSearch = async (value) => {
    if (value.trim()) {
      setSearchQuery(value);
      await performGlobalSearch(value);
    }
  };

  // Démarrer découverte de topologie
  const handleStartDiscovery = async () => {
    try {
      const values = await form.validateFields();
      await startTopologyDiscovery(values);
      setDiscoveryModal(false);
      form.resetFields();
    } catch (error) {
      console.error('Erreur découverte:', error);
    }
  };

  // Données pour vue d'ensemble
  const overviewData = {
    devices: dashboardData?.devices || systemOverview?.devices || { total: 0, online: 0 },
    alerts: dashboardData?.alerts || systemOverview?.alerts || { total: 0, critical: 0 },
    network: networkOverview || { topology_nodes: 0, active_connections: 0 },
    system: systemOverview?.system || { overall_status: 'unknown' }
  };

  // Configuration des colonnes pour les résultats de recherche
  const searchColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type) => {
        const colors = {
          device: 'blue',
          interface: 'green',
          alert: 'orange',
          topology: 'purple'
        };
        return <Tag color={colors[type] || 'default'}>{type.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Nom',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          {record.type === 'device' && <NodeIndexOutlined />}
          {record.type === 'interface' && <ApartmentOutlined />}
          {record.type === 'alert' && <InfoCircleOutlined />}
          {record.type === 'topology' && <ClusterOutlined />}
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description'
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Badge 
          status={status === 'active' ? 'success' : 'default'}
          text={status === 'active' ? 'Actif' : 'Inactif'}
        />
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />}>
            Voir
          </Button>
        </Space>
      )
    }
  ];

  // Données mock pour les exemples
  const mockSearchResults = [
    {
      key: '1',
      type: 'device',
      name: 'Switch-Core-01',
      description: 'Switch principal du cœur réseau',
      status: 'active'
    },
    {
      key: '2',
      type: 'interface',
      name: 'GigabitEthernet0/1',
      description: 'Interface vers Router-DMZ',
      status: 'active'
    },
    {
      key: '3',
      type: 'alert',
      name: 'CPU élevé',
      description: 'Utilisation CPU > 80%',
      status: 'active'
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* En-tête avec recherche */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={12}>
            <Space>
              <GlobalOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
              <span style={{ fontSize: '20px', fontWeight: 'bold' }}>
                Vues API & Recherche
              </span>
            </Space>
          </Col>
          <Col xs={24} md={12}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Search
                placeholder="Recherche globale..."
                enterButton={<SearchOutlined />}
                size="large"
                onSearch={handleSearch}
                style={{ width: 300 }}
              />
              <Button
                type="primary"
                icon={<RadarChartOutlined />}
                onClick={() => setDiscoveryModal(true)}
              >
                Découverte
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Alertes */}
      {error && (
        <Alert
          message="Erreur"
          description={error.message}
          type="error"
          showIcon
          closable
          onClose={clearError}
          style={{ marginBottom: '16px' }}
        />
      )}

      {discoveryStatus.status && (
        <Alert
          message="Découverte en cours"
          description={`Progression: ${discoveryStatus.progress || 0}% - ${discoveryStatus.devices_found || 0} équipements trouvés`}
          type="info"
          showIcon
          style={{ marginBottom: '16px' }}
        />
      )}

      {/* Interface principale avec onglets */}
      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* Vue d'ensemble */}
          <TabPane 
            tab={
              <Space>
                <BarChartOutlined />
                Vue d'ensemble
              </Space>
            } 
            key="overview"
          >
            <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
              <Col xs={24} sm={6}>
                <Card>
                  <Statistic
                    title="Équipements"
                    value={overviewData.devices.total}
                    prefix={<NodeIndexOutlined />}
                    suffix={`(${overviewData.devices.online} en ligne)`}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={6}>
                <Card>
                  <Statistic
                    title="Alertes"
                    value={overviewData.alerts.total}
                    prefix={<InfoCircleOutlined />}
                    suffix={`(${overviewData.alerts.critical} critiques)`}
                    valueStyle={{ color: overviewData.alerts.critical > 0 ? '#cf1322' : '#3f8600' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={6}>
                <Card>
                  <Statistic
                    title="Nœuds Topologie"
                    value={overviewData.network.topology_nodes}
                    prefix={<ClusterOutlined />}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={6}>
                <Card>
                  <Statistic
                    title="Connexions"
                    value={overviewData.network.active_connections}
                    prefix={<ApartmentOutlined />}
                  />
                </Card>
              </Col>
            </Row>

            {/* Graphiques et métriques */}
            <Row gutter={[16, 16]}>
              <Col xs={24} lg={12}>
                <Card title="État Système" extra={<ReloadOutlined />}>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Row justify="space-between">
                        <Col>CPU</Col>
                        <Col>{overviewData.system.cpu_usage || 0}%</Col>
                      </Row>
                      <Progress 
                        percent={overviewData.system.cpu_usage || 0}
                        status={overviewData.system.cpu_usage > 80 ? 'exception' : 'success'}
                      />
                    </div>
                    <div>
                      <Row justify="space-between">
                        <Col>Mémoire</Col>
                        <Col>{overviewData.system.memory_usage || 0}%</Col>
                      </Row>
                      <Progress 
                        percent={overviewData.system.memory_usage || 0}
                        status={overviewData.system.memory_usage > 85 ? 'exception' : 'success'}
                      />
                    </div>
                    <div>
                      <Row justify="space-between">
                        <Col>Disque</Col>
                        <Col>{overviewData.system.disk_usage || 0}%</Col>
                      </Row>
                      <Progress 
                        percent={overviewData.system.disk_usage || 0}
                        status={overviewData.system.disk_usage > 90 ? 'exception' : 'success'}
                      />
                    </div>
                  </Space>
                </Card>
              </Col>

              <Col xs={24} lg={12}>
                <Card title="Activité Réseau" extra={<ApartmentOutlined />}>
                  <List
                    dataSource={[
                      {
                        title: 'Trafic entrant',
                        value: '125 Mbps',
                        trend: '+5%'
                      },
                      {
                        title: 'Trafic sortant',
                        value: '89 Mbps',
                        trend: '-2%'
                      },
                      {
                        title: 'Paquets/sec',
                        value: '15,234',
                        trend: '+12%'
                      }
                    ]}
                    renderItem={(item) => (
                      <List.Item>
                        <List.Item.Meta
                          title={item.title}
                          description={
                            <Space>
                              <span style={{ fontSize: '16px', fontWeight: 'bold' }}>
                                {item.value}
                              </span>
                              <Tag color={item.trend.startsWith('+') ? 'green' : 'red'}>
                                {item.trend}
                              </Tag>
                            </Space>
                          }
                        />
                      </List.Item>
                    )}
                  />
                </Card>
              </Col>
            </Row>
          </TabPane>

          {/* Recherche */}
          <TabPane 
            tab={
              <Space>
                <SearchOutlined />
                Recherche ({searchResults?.total || 0})
              </Space>
            } 
            key="search"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Search
                    placeholder="Terme de recherche..."
                    enterButton="Rechercher"
                    size="large"
                    onSearch={handleSearch}
                    loading={loading.search}
                  />
                </Col>
                <Col xs={24} md={12}>
                  <Space>
                    <Select
                      placeholder="Type"
                      style={{ width: 120 }}
                      allowClear
                    >
                      <Option value="device">Équipement</Option>
                      <Option value="interface">Interface</Option>
                      <Option value="alert">Alerte</Option>
                      <Option value="topology">Topologie</Option>
                    </Select>
                    <Button icon={<FilterOutlined />}>
                      Filtres
                    </Button>
                    <Button icon={<DownloadOutlined />}>
                      Exporter
                    </Button>
                  </Space>
                </Col>
              </Row>

              <Table
                columns={searchColumns}
                dataSource={searchResults?.results || mockSearchResults}
                loading={loading.search}
                pagination={{
                  total: searchResults?.total || mockSearchResults.length,
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true
                }}
              />
            </Space>
          </TabPane>

          {/* Découverte de topologie */}
          <TabPane 
            tab={
              <Space>
                <RadarChartOutlined />
                Découverte
              </Space>
            } 
            key="discovery"
          >
            <Card title="Découverte de Topologie">
              {discoveryStatus.status ? (
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Steps
                    current={
                      discoveryStatus.status === 'started' ? 0 :
                      discoveryStatus.status === 'in_progress' ? 1 :
                      discoveryStatus.status === 'completed' ? 2 : 0
                    }
                  >
                    <Step title="Initialisation" />
                    <Step title="Analyse" />
                    <Step title="Terminé" />
                  </Steps>

                  <Progress 
                    percent={discoveryStatus.progress || 0} 
                    status="active"
                  />

                  <Row gutter={16}>
                    <Col span={8}>
                      <Statistic
                        title="Équipements trouvés"
                        value={discoveryStatus.devices_found || 0}
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="Liens détectés"
                        value={discoveryStatus.links_found || 0}
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="Temps écoulé"
                        value={discoveryStatus.elapsed_time || '0:00'}
                      />
                    </Col>
                  </Row>
                </Space>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <RadarChartOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
                  <p style={{ color: '#999' }}>Aucune découverte en cours</p>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={() => setDiscoveryModal(true)}
                  >
                    Démarrer une découverte
                  </Button>
                </div>
              )}
            </Card>
          </TabPane>

          {/* Configuration */}
          <TabPane 
            tab={
              <Space>
                <SettingOutlined />
                Configuration
              </Space>
            } 
            key="config"
          >
            <Card title="Configuration des Vues">
              <Form layout="vertical">
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="Intervalle de rafraîchissement">
                      <Select defaultValue="30">
                        <Option value="10">10 secondes</Option>
                        <Option value="30">30 secondes</Option>
                        <Option value="60">1 minute</Option>
                        <Option value="300">5 minutes</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="Période par défaut">
                      <Select defaultValue="24h">
                        <Option value="1h">1 heure</Option>
                        <Option value="6h">6 heures</Option>
                        <Option value="24h">24 heures</Option>
                        <Option value="7d">7 jours</Option>
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
              </Form>
            </Card>
          </TabPane>
        </Tabs>
      </Card>

      {/* Modal de découverte */}
      <Modal
        title="Démarrer Découverte de Topologie"
        open={discoveryModal}
        onOk={handleStartDiscovery}
        onCancel={() => setDiscoveryModal(false)}
        width={600}
        confirmLoading={loading.discovery}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="Réseau à analyser"
            name="network_id"
            rules={[{ required: true, message: 'Le réseau est obligatoire' }]}
          >
            <Input placeholder="192.168.1.0/24" />
          </Form.Item>

          <Form.Item
            label="Méthode de découverte"
            name="discovery_method"
            rules={[{ required: true, message: 'La méthode est obligatoire' }]}
          >
            <Select placeholder="Sélectionner une méthode">
              <Option value="snmp">SNMP</Option>
              <Option value="ping">Ping</Option>
              <Option value="arp">Table ARP</Option>
              <Option value="lldp">LLDP</Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Timeout (sec)" name="timeout">
                <Input type="number" placeholder="30" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Threads" name="threads">
                <Input type="number" placeholder="10" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default ApiViewsInterface;