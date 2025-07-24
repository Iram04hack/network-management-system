/**
 * MetricsSection - Exploration interactive des métriques avec historique
 * Conforme aux spécifications: /monitoring/metrics/realtime/, /monitoring/history/
 * Fonctionnalités: Métriques temps réel, historique, conservation, analyse tendances
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
  Input,
  Select,
  Modal,
  Form,
  message,
  Tooltip,
  Statistic,
  Switch,
  Slider,
  DatePicker,
  Tabs,
  Tree,
  Checkbox,
  Radio,
  InputNumber,
  Divider,
  Alert,
  Progress
} from 'antd';
import {
  LineChartOutlined,
  DashboardOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
  SettingOutlined,
  FunctionOutlined,
  BarChartOutlined,
  AreaChartOutlined,
  PieChartOutlined,
  DotChartOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  FilterOutlined,
  SearchOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  ScatterChart, 
  Scatter,
  ComposedChart,
  Legend
} from 'recharts';

// Import du hook monitoring
import useMonitoring from '../../../hooks/useMonitoring';

const { Option } = Select;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;
const { TreeNode } = Tree;

const MetricsSection = () => {
  // Hook monitoring conforme aux spécifications
  const {
    realTimeMetrics,
    metricsHistory,
    thresholds,
    fetchRealTimeMetrics,
    fetchMetricsHistory,
    exportMetricsHistory,
    analyzeMetricsTrends
  } = useMonitoring();

  // États locaux pour l'interface avancée
  const [activeSubTab, setActiveSubTab] = useState('realtime');
  const [selectedMetrics, setSelectedMetrics] = useState(['cpu', 'memory']);
  const [chartType, setChartType] = useState('line');
  const [timeRange, setTimeRange] = useState('24h');
  const [refreshInterval, setRefreshInterval] = useState(5);
  const [isRealTime, setIsRealTime] = useState(true);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalType, setModalType] = useState('export');
  const [analysisResults, setAnalysisResults] = useState(null);
  const [retentionSettings, setRetentionSettings] = useState({
    realtime: 24, // heures
    history: 30,  // jours
    granularity: '1h'
  });
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [form] = Form.useForm();

  // Charger les métriques conformément aux spécifications
  useEffect(() => {
    fetchRealTimeMetrics();
    fetchMetricsHistory(timeRange, selectedMetrics);
  }, [fetchRealTimeMetrics, fetchMetricsHistory, timeRange]);

  // Actualisation temps réel
  useEffect(() => {
    if (isRealTime) {
      const interval = setInterval(() => {
        fetchRealTimeMetrics();
      }, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [isRealTime, refreshInterval, fetchRealTimeMetrics]);

  // Fonctions pour l'analyse des tendances
  const handleAnalyzeTrends = async () => {
    setLoadingAnalysis(true);
    try {
      const results = await analyzeMetricsTrends(timeRange);
      setAnalysisResults(results);
      message.success('Analyse des tendances terminée');
    } catch (error) {
      message.error('Erreur lors de l\'analyse des tendances');
    } finally {
      setLoadingAnalysis(false);
    }
  };

  // Fonction pour exporter l'historique
  const handleExportHistory = async (format = 'csv') => {
    try {
      await exportMetricsHistory(format, timeRange);
      message.success(`Export ${format.toUpperCase()} terminé`);
    } catch (error) {
      message.error('Erreur lors de l\'export');
    }
  };

  // Fonction pour changer la période de rétention
  const handleRetentionChange = (type, value) => {
    setRetentionSettings(prev => ({
      ...prev,
      [type]: value
    }));
  };

  // Données des métriques issues du hook (conforme aux spécifications)
  const getRealTimeMetricsData = () => {
    return [
      {
        id: 'cpu',
        name: 'cpu_usage',
        label: 'Utilisation CPU',
        unit: '%',
        category: 'system',
        device: 'system',
        type: 'gauge',
        thresholds: thresholds.active.cpu,
        enabled: true,
        current: realTimeMetrics.cpu.current,
        history: realTimeMetrics.cpu.history,
        loading: realTimeMetrics.cpu.loading
      },
      {
        id: 'memory',
        name: 'memory_usage',
        label: 'Utilisation Mémoire',
        unit: '%',
        category: 'system',
        device: 'system',
        type: 'gauge',
        thresholds: thresholds.active.memory,
        enabled: true,
        current: realTimeMetrics.memory.current,
        history: realTimeMetrics.memory.history,
        loading: realTimeMetrics.memory.loading
      },
      {
        id: 'network',
        name: 'network_usage',
        label: 'Utilisation Réseau',
        unit: '%',
        category: 'network',
        device: 'network',
        type: 'gauge',
        thresholds: thresholds.active.network,
        enabled: true,
        current: realTimeMetrics.network.current,
        history: realTimeMetrics.network.history,
        loading: realTimeMetrics.network.loading
      },
      {
        id: 'disk',
        name: 'disk_usage',
        label: 'Utilisation Disque',
        unit: '%',
        category: 'storage',
        device: 'system',
        type: 'gauge',
        thresholds: thresholds.active.disk,
        enabled: true,
        current: realTimeMetrics.disk.current,
        history: realTimeMetrics.disk.history,
        loading: realTimeMetrics.disk.loading
      }
    ];
  };

  const metricsData = getRealTimeMetricsData();

  // Catégories de métriques
  const categories = {
    system: { label: 'Système', color: '#1890ff', icon: <ThunderboltOutlined /> },
    network: { label: 'Réseau', color: '#52c41a', icon: <LineChartOutlined /> },
    storage: { label: 'Stockage', color: '#722ed1', icon: <BarChartOutlined /> },
    application: { label: 'Application', color: '#fa541c', icon: <DashboardOutlined /> },
    custom: { label: 'Personnalisé', color: '#13c2c2', icon: <FunctionOutlined /> }
  };

  // Types de graphiques
  const chartTypes = [
    { key: 'line', label: 'Ligne', icon: <LineChartOutlined /> },
    { key: 'area', label: 'Aire', icon: <AreaChartOutlined /> },
    { key: 'bar', label: 'Barres', icon: <BarChartOutlined /> },
    { key: 'scatter', label: 'Nuage', icon: <DotChartOutlined /> }
  ];

  // Colonnes pour la table des métriques
  const metricsColumns = [
    {
      title: 'Métrique',
      dataIndex: 'label',
      key: 'label',
      render: (text, record) => (
        <Space>
          <span style={{ color: categories[record.category]?.color }}>
            {categories[record.category]?.icon}
          </span>
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
              {record.name} - {record.device}
            </div>
          </div>
        </Space>
      )
    },
    {
      title: 'Catégorie',
      dataIndex: 'category',
      key: 'category',
      render: (category) => (
        <Tag color={categories[category]?.color}>
          {categories[category]?.label}
        </Tag>
      ),
      filters: Object.entries(categories).map(([key, value]) => ({
        text: value.label,
        value: key
      })),
      onFilter: (value, record) => record.category === value
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type) => (
        <Tag color={type === 'gauge' ? 'blue' : 'green'}>
          {type.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Valeur Actuelle',
      key: 'currentValue',
      render: (_, record) => {
        const currentValue = record.values[record.values.length - 1]?.value || 0;
        const { warning, critical } = record.thresholds;
        let color = '#52c41a';
        
        if (currentValue >= critical) {
          color = '#ff4d4f';
        } else if (currentValue >= warning) {
          color = '#faad14';
        }

        return (
          <div>
            <div style={{ color, fontWeight: 500 }}>
              {currentValue.toFixed(1)} {record.unit}
            </div>
            <Progress 
              percent={Math.min(100, (currentValue / critical) * 100)} 
              size="small"
              strokeColor={color}
              showInfo={false}
            />
          </div>
        );
      }
    },
    {
      title: 'Seuils',
      key: 'thresholds',
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          <div style={{ fontSize: '12px' }}>
            <span style={{ color: '#faad14' }}>⚠</span> {record.thresholds.warning}{record.unit}
          </div>
          <div style={{ fontSize: '12px' }}>
            <span style={{ color: '#ff4d4f' }}>🚨</span> {record.thresholds.critical}{record.unit}
          </div>
        </Space>
      )
    },
    {
      title: 'Statut',
      dataIndex: 'enabled',
      key: 'enabled',
      render: (enabled) => (
        <Switch 
          checked={enabled} 
          size="small"
          onChange={(checked) => toggleMetric(checked)}
        />
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="Voir graphique">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => viewMetricChart(record)}
            />
          </Tooltip>
          <Tooltip title="Configurer">
            <Button
              type="text"
              icon={<SettingOutlined />}
              size="small"
              onClick={() => configureMetric(record)}
            />
          </Tooltip>
          <Checkbox
            checked={selectedMetrics.includes(record.id)}
            onChange={(e) => handleMetricSelection(record.id, e.target.checked)}
          />
        </Space>
      )
    }
  ];

  // Gestion de la sélection des métriques
  const handleMetricSelection = (metricId, checked) => {
    if (checked) {
      setSelectedMetrics([...selectedMetrics, metricId]);
    } else {
      setSelectedMetrics(selectedMetrics.filter(id => id !== metricId));
    }
  };

  // Actions
  const toggleMetric = (enabled) => {
    message.success(`Métrique ${enabled ? 'activée' : 'désactivée'}`);
  };

  const viewMetricChart = (metric) => {
    setSelectedMetrics([metric.id]);
    setActiveSubTab('realtime');
  };

  // Fonction pour changer la plage temporelle
  const handleTimeRangeChange = (range) => {
    setTimeRange(range);
    fetchMetricsHistory(range, selectedMetrics);
  };

  // Fonction pour basculer entre temps réel et historique
  const toggleRealTimeMode = (enabled) => {
    setIsRealTime(enabled);
    if (enabled) {
      setActiveSubTab('realtime');
    } else {
      setActiveSubTab('history');
    }
  };

  const configureMetric = (metric) => {
    setModalType('thresholds');
    form.setFieldsValue({
      ...metric,
      warning: metric.thresholds.warning,
      critical: metric.thresholds.critical
    });
    setIsModalVisible(true);
  };

  // Fonction pour configurer la rétention
  const openRetentionConfig = () => {
    setModalType('retention');
    form.setFieldsValue(retentionSettings);
    setIsModalVisible(true);
  };

  // Fonction pour ouvrir l'export
  const openExportModal = () => {
    setModalType('export');
    setIsModalVisible(true);
  };

  // Rendu du graphique principal
  const renderMainChart = () => {
    const selectedMetricsData = metricsData.filter(m => selectedMetrics.includes(m.id));
    
    if (selectedMetricsData.length === 0) {
      return (
        <Card style={{ height: '400px' }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center', 
            height: '100%',
            flexDirection: 'column',
            color: '#8c8c8c'
          }}>
            <LineChartOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
            <div>Sélectionnez des métriques pour afficher le graphique</div>
          </div>
        </Card>
      );
    }

    // Préparer les données pour le graphique
    const chartData = selectedMetricsData[0].values.map((point, index) => {
      const dataPoint = {
        timestamp: point.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
      };
      
      selectedMetricsData.forEach(metric => {
        dataPoint[metric.name] = metric.values[index]?.value || 0;
      });
      
      return dataPoint;
    });

    const colors = ['#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1'];

    // Rendu selon le type de graphique
    const renderChart = () => {
      switch (chartType) {
        case 'area':
          return (
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {selectedMetricsData.map((metric, index) => (
                <Area
                  key={metric.name}
                  type="monotone"
                  dataKey={metric.name}
                  stackId="1"
                  stroke={colors[index % colors.length]}
                  fill={colors[index % colors.length]}
                  fillOpacity={0.3}
                  name={metric.label}
                />
              ))}
            </AreaChart>
          );
        
        case 'bar':
          return (
            <BarChart data={chartData.slice(-12)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {selectedMetricsData.map((metric, index) => (
                <Bar
                  key={metric.name}
                  dataKey={metric.name}
                  fill={colors[index % colors.length]}
                  name={metric.label}
                />
              ))}
            </BarChart>
          );
        
        case 'scatter':
          return (
            <ScatterChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {selectedMetricsData.map((metric, index) => (
                <Scatter
                  key={metric.name}
                  dataKey={metric.name}
                  fill={colors[index % colors.length]}
                  name={metric.label}
                />
              ))}
            </ScatterChart>
          );
        
        default: // line
          return (
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <RechartsTooltip />
              <Legend />
              {selectedMetricsData.map((metric, index) => (
                <Line
                  key={metric.name}
                  type="monotone"
                  dataKey={metric.name}
                  stroke={colors[index % colors.length]}
                  strokeWidth={2}
                  dot={false}
                  name={metric.label}
                />
              ))}
            </LineChart>
          );
      }
    };

    return (
      <Card 
        title={
          <Space>
            <LineChartOutlined />
            <span>Graphique des Métriques</span>
            <Tag color="blue">{selectedMetricsData.length} sélectionnée(s)</Tag>
          </Space>
        }
        extra={
          <Space>
            <Select
              value={chartType}
              onChange={setChartType}
              style={{ width: 120 }}
              size="small"
            >
              {chartTypes.map(type => (
                <Option key={type.key} value={type.key}>
                  <Space>
                    {type.icon}
                    {type.label}
                  </Space>
                </Option>
              ))}
            </Select>
            <Select
              value={timeRange}
              onChange={setTimeRange}
              style={{ width: 100 }}
              size="small"
            >
              <Option value="1h">1 heure</Option>
              <Option value="6h">6 heures</Option>
              <Option value="24h">24 heures</Option>
              <Option value="7d">7 jours</Option>
            </Select>
            <Button
              icon={<DownloadOutlined />}
              size="small"
              onClick={() => message.info('Export en cours...')}
            >
              Export
            </Button>
          </Space>
        }
        style={{ height: '500px' }}
      >
        <ResponsiveContainer width="100%" height={400}>
          {renderChart()}
        </ResponsiveContainer>
      </Card>
    );
  };

  // Rendu des statistiques avec données temps réel
  const renderStats = () => {
    const totalMetrics = metricsData.length;
    const activeMetrics = metricsData.filter(m => m.enabled).length;
    const warningMetrics = metricsData.filter(m => {
      const { warning, critical } = m.thresholds;
      return m.current >= warning && m.current < critical;
    }).length;
    const criticalMetrics = metricsData.filter(m => {
      const { critical } = m.thresholds;
      return m.current >= critical;
    }).length;

    const lastUpdate = realTimeMetrics.lastUpdate 
      ? new Date(realTimeMetrics.lastUpdate).toLocaleTimeString()
      : 'Jamais';

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Métriques"
              value={totalMetrics}
              prefix={<DashboardOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '8px' }}>
              Dernière MAJ: {lastUpdate}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Actives"
              value={activeMetrics}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '8px' }}>
              Surveillance temps réel
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Attention"
              value={warningMetrics}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
            <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '8px' }}>
              Seuils d'alerte atteints
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Critiques"
              value={criticalMetrics}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
            <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '8px' }}>
              Intervention requise
            </div>
          </Card>
        </Col>
      </Row>
    );
  };

  // Rendu de l'explorateur de métriques
  const renderMetricsExplorer = () => (
    <div>
      {/* Graphique principal */}
      {renderMainChart()}
      
      {/* Contrôles temps réel */}
      <Card size="small" style={{ marginTop: '16px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <Space>
              <span>Temps réel:</span>
              <Switch
                checked={isRealTime}
                onChange={setIsRealTime}
                size="small"
              />
              {isRealTime && (
                <Select
                  value={refreshInterval}
                  onChange={setRefreshInterval}
                  style={{ width: 100 }}
                  size="small"
                >
                  <Option value={10}>10s</Option>
                  <Option value={30}>30s</Option>
                  <Option value={60}>1m</Option>
                </Select>
              )}
            </Space>
          </Col>
          <Col xs={24} sm={8}>
            <Space>
              <span>Métriques sélectionnées:</span>
              <Tag color="blue">{selectedMetrics.length}</Tag>
              <Button
                size="small"
                onClick={() => setSelectedMetrics([])}
                disabled={selectedMetrics.length === 0}
              >
                Effacer
              </Button>
            </Space>
          </Col>
          <Col xs={24} sm={8}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              size="small"
              onClick={() => {
                setModalType('metric');
                setIsModalVisible(true);
              }}
            >
              Nouvelle métrique
            </Button>
          </Col>
        </Row>
      </Card>
    </div>
  );

  // Rendu de la liste des métriques
  const renderMetricsList = () => (
    <Card 
      title={
        <Space>
          <FunctionOutlined />
          <span>Métriques Disponibles</span>
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
              setModalType('metric');
              setIsModalVisible(true);
            }}
          >
            Nouvelle métrique
          </Button>
        </Space>
      }
    >
      <Table
        columns={metricsColumns}
        dataSource={metricsData}
        rowKey="id"
        size="small"
        pagination={{
          pageSize: 10,
          showSizeChanger: true
        }}
      />
    </Card>
  );

  return (
    <div style={{ padding: '0' }}>
      {/* Statistiques */}
      {renderStats()}

      {/* Onglets pour les sous-sections conformes aux spécifications */}
      <Tabs activeKey={activeSubTab} onChange={setActiveSubTab}>
        <TabPane
          tab={
            <Space>
              <ThunderboltOutlined />
              <span>Temps Réel</span>
              {isRealTime && <Tag color="green" size="small">LIVE</Tag>}
            </Space>
          }
          key="realtime"
        >
          {renderRealTimeMetrics()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <ClockCircleOutlined />
              <span>Historique</span>
            </Space>
          }
          key="history"
        >
          {renderMetricsHistory()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <FunctionOutlined />
              <span>Métriques</span>
            </Space>
          }
          key="metrics"
        >
          {renderMetricsList()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <SettingOutlined />
              <span>Conservation</span>
            </Space>
          }
          key="retention"
        >
          {renderRetentionSettings()}
        </TabPane>
      </Tabs>

      {/* Modal de configuration avancée */}
      <Modal
        title={`Configuration ${modalType}`}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        onOk={() => {
          message.success('Configuration sauvegardée');
          setIsModalVisible(false);
        }}
        width={modalType === 'export' ? 600 : 800}
      >
        {modalType === 'export' && renderExportModal()}
        {modalType === 'thresholds' && renderThresholdsModal()}
        {modalType === 'retention' && renderRetentionModal()}
        {modalType === 'analysis' && renderAnalysisModal()}
      </Modal>
    </div>
  );

  // ===============================
  // NOUVEAUX COMPOSANTS CONFORMES AUX SPÉCIFICATIONS
  // ===============================

  // Rendu des métriques temps réel
  function renderRealTimeMetrics() {
    return (
      <div>
        <Card
          title={
            <Space>
              <ThunderboltOutlined style={{ color: '#52c41a' }} />
              <span>Surveillance Temps Réel</span>
              {isRealTime && <Tag color="green">LIVE</Tag>}
            </Space>
          }
          extra={
            <Space>
              <Switch
                checked={isRealTime}
                onChange={toggleRealTimeMode}
                checkedChildren="Live"
                unCheckedChildren="Pause"
              />
              <Select
                value={refreshInterval}
                onChange={setRefreshInterval}
                style={{ width: 80 }}
                size="small"
                disabled={!isRealTime}
              >
                <Option value={5}>5s</Option>
                <Option value={10}>10s</Option>
                <Option value={30}>30s</Option>
              </Select>
            </Space>
          }
        >
          <Row gutter={[16, 16]}>
            {metricsData.map((metric) => (
              <Col xs={24} sm={12} lg={6} key={metric.id}>
                <Card
                  size="small"
                  title={metric.label}
                  style={{ textAlign: 'center' }}
                >
                  <Statistic
                    value={metric.current}
                    precision={1}
                    suffix={metric.unit}
                    valueStyle={{
                      color: metric.current >= metric.thresholds.critical
                        ? '#ff4d4f'
                        : metric.current >= metric.thresholds.warning
                          ? '#faad14'
                          : '#52c41a'
                    }}
                  />
                  <Progress
                    percent={Math.min(100, (metric.current / metric.thresholds.critical) * 100)}
                    strokeColor={metric.current >= metric.thresholds.critical
                      ? '#ff4d4f'
                      : metric.current >= metric.thresholds.warning
                        ? '#faad14'
                        : '#52c41a'
                    }
                    size="small"
                    showInfo={false}
                    style={{ marginTop: '8px' }}
                  />
                  <div style={{ fontSize: '12px', color: '#8c8c8c', marginTop: '4px' }}>
                    Seuil: {metric.thresholds.warning}{metric.unit} / {metric.thresholds.critical}{metric.unit}
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>

        <Card
          title="Graphiques Temps Réel"
          style={{ marginTop: '16px' }}
          extra={
            <Space>
              <Checkbox.Group
                options={metricsData.map(m => ({ label: m.label, value: m.id }))}
                value={selectedMetrics}
                onChange={setSelectedMetrics}
              />
            </Space>
          }
        >
          {renderMainChart()}
        </Card>
      </div>
    );
  }

  // Rendu de l'historique des métriques
  function renderMetricsHistory() {
    return (
      <div>
        <Card
          title={
            <Space>
              <ClockCircleOutlined style={{ color: '#1890ff' }} />
              <span>Historique des Métriques</span>
            </Space>
          }
          extra={
            <Space>
              <Select
                value={timeRange}
                onChange={handleTimeRangeChange}
                style={{ width: 120 }}
              >
                <Option value="1h">Dernière heure</Option>
                <Option value="24h">24 heures</Option>
                <Option value="7d">7 jours</Option>
                <Option value="30d">30 jours</Option>
              </Select>
              <Button
                icon={<DownloadOutlined />}
                onClick={openExportModal}
              >
                Exporter
              </Button>
              <Button
                icon={<BarChartOutlined />}
                onClick={handleAnalyzeTrends}
                loading={loadingAnalysis}
              >
                Analyser
              </Button>
            </Space>
          }
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={16}>
              <Card size="small" title="Graphique Historique">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={metricsHistory.data}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="timestamp" />
                    <YAxis />
                    <RechartsTooltip />
                    <Legend />
                    {selectedMetrics.map((metricId, index) => {
                      const metric = metricsData.find(m => m.id === metricId);
                      return (
                        <Line
                          key={metricId}
                          type="monotone"
                          dataKey={metricId}
                          stroke={['#1890ff', '#52c41a', '#faad14', '#ff4d4f'][index % 4]}
                          name={metric?.label || metricId}
                          strokeWidth={2}
                          dot={false}
                        />
                      );
                    })}
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card size="small" title="Statistiques">
                <div style={{ padding: '16px' }}>
                  <div style={{ marginBottom: '16px' }}>
                    <strong>Période:</strong> {timeRange}
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <strong>Granularité:</strong> {retentionSettings.granularity}
                  </div>
                  <div style={{ marginBottom: '16px' }}>
                    <strong>Points de données:</strong> {metricsHistory.data.length}
                  </div>
                  <Button
                    type="primary"
                    block
                    onClick={() => {
                      setModalType('analysis');
                      setIsModalVisible(true);
                    }}
                  >
                    Analyse détaillée
                  </Button>
                </div>
              </Card>
            </Col>
          </Row>
        </Card>
      </div>
    );
  }

  // Rendu des paramètres de rétention
  function renderRetentionSettings() {
    return (
      <div>
        <Card
          title={
            <Space>
              <SettingOutlined style={{ color: '#722ed1' }} />
              <span>Conservation des Données</span>
            </Space>
          }
          extra={
            <Button
              type="primary"
              onClick={openRetentionConfig}
            >
              Configurer
            </Button>
          }
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
              <Card size="small" title="Données Temps Réel">
                <Statistic
                  value={retentionSettings.realtime}
                  suffix="heures"
                  valueStyle={{ color: '#1890ff' }}
                />
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#8c8c8c' }}>
                  Conservation des métriques temps réel
                </div>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card size="small" title="Historique">
                <Statistic
                  value={retentionSettings.history}
                  suffix="jours"
                  valueStyle={{ color: '#52c41a' }}
                />
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#8c8c8c' }}>
                  Conservation de l'historique
                </div>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card size="small" title="Granularité">
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#faad14' }}>
                  {retentionSettings.granularity}
                </div>
                <div style={{ marginTop: '8px', fontSize: '12px', color: '#8c8c8c' }}>
                  Intervalle d'agrégation
                </div>
              </Card>
            </Col>
          </Row>

          <Alert
            message="Politique de Rétention"
            description="Les données sont automatiquement archivées et supprimées selon les périodes configurées. Les données temps réel sont conservées pendant 24 heures, l'historique pendant 30 jours."
            type="info"
            showIcon
            style={{ marginTop: '16px' }}
          />
        </Card>
      </div>
    );
  }

  // Rendu des modals
  function renderExportModal() {
    return (
      <div>
        <h4>Exporter l'Historique des Métriques</h4>
        <Form layout="vertical">
          <Form.Item label="Format d'export">
            <Radio.Group defaultValue="csv">
              <Radio value="csv">CSV</Radio>
              <Radio value="json">JSON</Radio>
              <Radio value="xlsx">Excel</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item label="Période">
            <Select defaultValue={timeRange} style={{ width: '100%' }}>
              <Option value="1h">Dernière heure</Option>
              <Option value="24h">24 heures</Option>
              <Option value="7d">7 jours</Option>
              <Option value="30d">30 jours</Option>
            </Select>
          </Form.Item>
          <Form.Item label="Métriques">
            <Checkbox.Group
              options={metricsData.map(m => ({ label: m.label, value: m.id }))}
              value={selectedMetrics}
              onChange={setSelectedMetrics}
            />
          </Form.Item>
        </Form>
      </div>
    );
  }

  function renderThresholdsModal() {
    return (
      <div>
        <h4>Configuration des Seuils</h4>
        <Form form={form} layout="vertical">
          <Form.Item label="Métrique" name="label">
            <Input disabled />
          </Form.Item>
          <Form.Item label="Seuil d'attention" name="warning">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="Seuil critique" name="critical">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </div>
    );
  }

  function renderRetentionModal() {
    return (
      <div>
        <h4>Configuration de la Rétention</h4>
        <Form form={form} layout="vertical">
          <Form.Item label="Rétention temps réel (heures)" name="realtime">
            <Slider min={1} max={168} />
          </Form.Item>
          <Form.Item label="Rétention historique (jours)" name="history">
            <Slider min={1} max={365} />
          </Form.Item>
          <Form.Item label="Granularité" name="granularity">
            <Select>
              <Option value="1m">1 minute</Option>
              <Option value="5m">5 minutes</Option>
              <Option value="1h">1 heure</Option>
              <Option value="1d">1 jour</Option>
            </Select>
          </Form.Item>
        </Form>
      </div>
    );
  }

  function renderAnalysisModal() {
    return (
      <div>
        <h4>Analyse des Tendances</h4>
        {analysisResults ? (
          <div>
            <Alert
              message="Analyse Terminée"
              description="L'analyse des tendances a été effectuée avec succès."
              type="success"
              showIcon
              style={{ marginBottom: '16px' }}
            />
            <pre style={{ background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
              {JSON.stringify(analysisResults, null, 2)}
            </pre>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Button
              type="primary"
              onClick={handleAnalyzeTrends}
              loading={loadingAnalysis}
            >
              Lancer l'analyse
            </Button>
          </div>
        )}
      </div>
    );
  }
};

export default MetricsSection;