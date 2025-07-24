/**
 * DashboardDesigner - Composant moderne de design de dashboard avec drag & drop
 * Implémente react-grid-layout pour une interface fluide et réactive
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Responsive, WidthProvider } from 'react-grid-layout';
import {
  Card,
  Row,
  Col,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Divider,
  message,
  Tooltip,
  Badge,
  Dropdown,
  Menu,
  Typography,
  Alert,
  Spin,
  notification
} from 'antd';
import {
  DashboardOutlined,
  PlusOutlined,
  SettingOutlined,
  DragOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  EyeOutlined,
  LayoutOutlined,
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  TableOutlined,
  NumberOutlined,
  BellOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  DatabaseOutlined,
  WarningOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

// Import du hook pour la gestion des dashboards
import { useDashboard } from '../../hooks/useDashboard';

const { Title, Text } = Typography;
const { Option } = Select;
const ResponsiveGridLayout = WidthProvider(Responsive);

// Configuration des types de widgets disponibles
const WIDGET_TYPES = [
  {
    id: 'kpi',
    name: 'KPI',
    icon: <NumberOutlined />,
    color: '#1890ff',
    defaultSize: { w: 3, h: 2 },
    description: 'Indicateurs clés de performance'
  },
  {
    id: 'chart_line',
    name: 'Graphique linéaire',
    icon: <LineChartOutlined />,
    color: '#52c41a',
    defaultSize: { w: 6, h: 4 },
    description: 'Tendances temporelles'
  },
  {
    id: 'chart_bar',
    name: 'Graphique en barres',
    icon: <BarChartOutlined />,
    color: '#722ed1',
    defaultSize: { w: 6, h: 4 },
    description: 'Comparaisons de valeurs'
  },
  {
    id: 'chart_pie',
    name: 'Graphique circulaire',
    icon: <PieChartOutlined />,
    color: '#fa541c',
    defaultSize: { w: 4, h: 4 },
    description: 'Répartitions en pourcentage'
  },
  {
    id: 'table',
    name: 'Tableau',
    icon: <TableOutlined />,
    color: '#13c2c2',
    defaultSize: { w: 8, h: 6 },
    description: 'Données tabulaires'
  },
  {
    id: 'alert',
    name: 'Alertes',
    icon: <BellOutlined />,
    color: '#ff4d4f',
    defaultSize: { w: 4, h: 3 },
    description: 'Notifications et alertes'
  },
  {
    id: 'network_map',
    name: 'Carte réseau',
    icon: <GlobalOutlined />,
    color: '#faad14',
    defaultSize: { w: 8, h: 6 },
    description: 'Topologie réseau'
  },
  {
    id: 'status',
    name: 'Statut système',
    icon: <CheckCircleOutlined />,
    color: '#52c41a',
    defaultSize: { w: 4, h: 2 },
    description: 'État des systèmes'
  }
];

// Données simulées pour les widgets
const generateMockData = (type) => {
  switch (type) {
    case 'kpi':
      return {
        value: Math.floor(Math.random() * 1000),
        unit: 'GB',
        trend: Math.random() > 0.5 ? 'up' : 'down',
        change: Math.floor(Math.random() * 20)
      };
    case 'chart_line':
      return Array.from({ length: 10 }, (_, i) => ({
        name: `${i + 1}h`,
        value: Math.floor(Math.random() * 100)
      }));
    case 'chart_bar':
      return Array.from({ length: 5 }, (_, i) => ({
        name: `Serveur ${i + 1}`,
        value: Math.floor(Math.random() * 100)
      }));
    case 'chart_pie':
      return [
        { name: 'CPU', value: 30, color: '#8884d8' },
        { name: 'Mémoire', value: 25, color: '#82ca9d' },
        { name: 'Réseau', value: 20, color: '#ffc658' },
        { name: 'Stockage', value: 25, color: '#ff7300' }
      ];
    case 'table':
      return Array.from({ length: 5 }, (_, i) => ({
        id: i + 1,
        name: `Équipement ${i + 1}`,
        status: Math.random() > 0.7 ? 'offline' : 'online',
        cpu: Math.floor(Math.random() * 100),
        memory: Math.floor(Math.random() * 100)
      }));
    case 'alert':
      return Array.from({ length: 3 }, (_, i) => ({
        id: i + 1,
        type: ['critical', 'warning', 'info'][Math.floor(Math.random() * 3)],
        message: `Alerte ${i + 1}: Problème détecté`,
        time: new Date(Date.now() - Math.random() * 3600000).toLocaleTimeString()
      }));
    default:
      return null;
  }
};

// Composant de rendu pour chaque type de widget
const WidgetRenderer = ({ type, data, title, onEdit, onDelete }) => {
  const renderContent = () => {
    switch (type) {
      case 'kpi':
        return (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <div style={{ fontSize: '36px', fontWeight: 'bold', color: '#1890ff' }}>
              {data?.value || 0}
            </div>
            <div style={{ fontSize: '14px', color: '#666' }}>
              {data?.unit || 'Units'}
            </div>
            <div style={{ fontSize: '12px', color: data?.trend === 'up' ? '#52c41a' : '#ff4d4f' }}>
              {data?.trend === 'up' ? '↑' : '↓'} {data?.change || 0}%
            </div>
          </div>
        );

      case 'chart_line':
        return (
          <div style={{ height: '200px', padding: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Line type="monotone" dataKey="value" stroke="#1890ff" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        );

      case 'chart_bar':
        return (
          <div style={{ height: '200px', padding: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="value" fill="#52c41a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        );

      case 'chart_pie':
        return (
          <div style={{ height: '200px', padding: '10px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data || []}
                  cx="50%"
                  cy="50%"
                  outerRadius={60}
                  fill="#8884d8"
                  dataKey="value"
                  label
                >
                  {(data || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        );

      case 'table':
        return (
          <div style={{ padding: '10px' }}>
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              <table style={{ width: '100%', fontSize: '12px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #f0f0f0' }}>
                    <th style={{ padding: '8px', textAlign: 'left' }}>Nom</th>
                    <th style={{ padding: '8px', textAlign: 'left' }}>Statut</th>
                    <th style={{ padding: '8px', textAlign: 'left' }}>CPU</th>
                  </tr>
                </thead>
                <tbody>
                  {(data || []).map((row) => (
                    <tr key={row.id} style={{ borderBottom: '1px solid #f9f9f9' }}>
                      <td style={{ padding: '8px' }}>{row.name}</td>
                      <td style={{ padding: '8px' }}>
                        <Badge 
                          status={row.status === 'online' ? 'success' : 'error'}
                          text={row.status}
                        />
                      </td>
                      <td style={{ padding: '8px' }}>{row.cpu}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );

      case 'alert':
        return (
          <div style={{ padding: '10px' }}>
            <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
              {(data || []).map((alert) => (
                <div key={alert.id} style={{ 
                  marginBottom: '8px', 
                  padding: '8px', 
                  borderRadius: '4px',
                  backgroundColor: alert.type === 'critical' ? '#fff2f0' : 
                                   alert.type === 'warning' ? '#fffbe6' : '#f6ffed',
                  border: `1px solid ${alert.type === 'critical' ? '#ffccc7' : 
                                      alert.type === 'warning' ? '#ffe58f' : '#b7eb8f'}`
                }}>
                  <div style={{ fontSize: '12px', fontWeight: 'bold' }}>
                    {alert.type === 'critical' ? '🔴' : alert.type === 'warning' ? '🟡' : '🟢'}
                    {alert.message}
                  </div>
                  <div style={{ fontSize: '10px', color: '#666' }}>
                    {alert.time}
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      default:
        return (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            <DatabaseOutlined style={{ fontSize: '32px', marginBottom: '8px' }} />
            <div>Widget {type}</div>
          </div>
        );
    }
  };

  return (
    <Card
      size="small"
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{title}</span>
          <Space>
            <Tooltip title="Configurer">
              <Button 
                type="text" 
                size="small" 
                icon={<SettingOutlined />}
                onClick={onEdit}
              />
            </Tooltip>
            <Tooltip title="Supprimer">
              <Button 
                type="text" 
                size="small" 
                icon={<DeleteOutlined />}
                danger
                onClick={onDelete}
              />
            </Tooltip>
          </Space>
        </div>
      }
      style={{ height: '100%' }}
      bodyStyle={{ padding: '0' }}
    >
      {renderContent()}
    </Card>
  );
};

const DashboardDesigner = ({ dashboardId, onSave, onCancel }) => {
  const [layouts, setLayouts] = useState({ lg: [] });
  const [widgets, setWidgets] = useState([]);
  const [isAddWidgetVisible, setIsAddWidgetVisible] = useState(false);
  const [editingWidget, setEditingWidget] = useState(null);
  const [isPreviewMode, setIsPreviewMode] = useState(false);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  // Hook pour la gestion des dashboards
  const { saveDashboard, loadDashboard } = useDashboard();

  // Charger le dashboard s'il existe
  useEffect(() => {
    if (dashboardId) {
      loadDashboard(dashboardId).then(dashboard => {
        if (dashboard) {
          setWidgets(dashboard.widgets || []);
          setLayouts(dashboard.layouts || { lg: [] });
        }
      });
    }
  }, [dashboardId, loadDashboard]);

  // Gérer les changements de layout
  const handleLayoutChange = useCallback((layout, layouts) => {
    setLayouts(layouts);
  }, []);

  // Ajouter un nouveau widget
  const addWidget = (widgetType) => {
    const widgetConfig = WIDGET_TYPES.find(w => w.id === widgetType);
    if (!widgetConfig) return;

    const newWidget = {
      id: `widget-${Date.now()}`,
      type: widgetType,
      title: widgetConfig.name,
      data: generateMockData(widgetType),
      config: {}
    };

    const newLayout = {
      i: newWidget.id,
      x: 0,
      y: 0,
      w: widgetConfig.defaultSize.w,
      h: widgetConfig.defaultSize.h,
      minW: 2,
      minH: 2
    };

    setWidgets(prev => [...prev, newWidget]);
    setLayouts(prev => ({
      ...prev,
      lg: [...(prev.lg || []), newLayout]
    }));
    setIsAddWidgetVisible(false);
    
    // Notification temps réel
    notification.success({
      message: 'Widget ajouté',
      description: `Le widget "${widgetConfig.name}" a été ajouté au dashboard`,
      placement: 'topRight',
      duration: 3
    });
  };

  // Éditer un widget
  const editWidget = (widget) => {
    setEditingWidget(widget);
    form.setFieldsValue({
      title: widget.title,
      refreshInterval: widget.config?.refreshInterval || 30
    });
  };

  // Supprimer un widget
  const deleteWidget = (widgetId) => {
    Modal.confirm({
      title: 'Supprimer le widget',
      content: 'Êtes-vous sûr de vouloir supprimer ce widget ?',
      okText: 'Supprimer',
      cancelText: 'Annuler',
      okType: 'danger',
      onOk: () => {
        setWidgets(prev => prev.filter(w => w.id !== widgetId));
        setLayouts(prev => ({
          ...prev,
          lg: prev.lg.filter(l => l.i !== widgetId)
        }));
        
        notification.success({
          message: 'Widget supprimé',
          description: 'Le widget a été supprimé du dashboard',
          placement: 'topRight',
          duration: 3
        });
      }
    });
  };

  // Sauvegarder le dashboard
  const handleSave = async () => {
    setLoading(true);
    try {
      const dashboardData = {
        id: dashboardId,
        widgets,
        layouts,
        lastModified: new Date().toISOString()
      };

      await saveDashboard(dashboardData);
      
      notification.success({
        message: 'Dashboard sauvegardé',
        description: 'Les modifications ont été sauvegardées avec succès',
        placement: 'topRight',
        duration: 3
      });
      
      if (onSave) onSave(dashboardData);
    } catch (error) {
      notification.error({
        message: 'Erreur de sauvegarde',
        description: 'Une erreur est survenue lors de la sauvegarde',
        placement: 'topRight',
        duration: 5
      });
    } finally {
      setLoading(false);
    }
  };

  // Barre d'outils
  const toolbar = (
    <div style={{ 
      padding: '16px', 
      borderBottom: '1px solid #f0f0f0',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      backgroundColor: '#fafafa'
    }}>
      <Space>
        <Button 
          type="primary" 
          icon={<PlusOutlined />}
          onClick={() => setIsAddWidgetVisible(true)}
        >
          Ajouter Widget
        </Button>
        <Button 
          icon={<EyeOutlined />}
          onClick={() => setIsPreviewMode(!isPreviewMode)}
        >
          {isPreviewMode ? 'Mode Édition' : 'Aperçu'}
        </Button>
      </Space>
      
      <Space>
        <Text type="secondary">
          {widgets.length} widget{widgets.length > 1 ? 's' : ''}
        </Text>
        <Button onClick={onCancel}>Annuler</Button>
        <Button 
          type="primary" 
          icon={<SaveOutlined />}
          onClick={handleSave}
          loading={loading}
        >
          Sauvegarder
        </Button>
      </Space>
    </div>
  );

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {toolbar}
      
      <div style={{ flex: 1, padding: '16px', overflow: 'auto' }}>
        {widgets.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '60px',
            color: '#666'
          }}>
            <DashboardOutlined style={{ fontSize: '64px', marginBottom: '16px' }} />
            <Title level={4} type="secondary">Dashboard vide</Title>
            <Text type="secondary">Commencez par ajouter des widgets à votre dashboard</Text>
            <br />
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={() => setIsAddWidgetVisible(true)}
              style={{ marginTop: '16px' }}
            >
              Ajouter votre premier widget
            </Button>
          </div>
        ) : (
          <ResponsiveGridLayout
            className="layout"
            layouts={layouts}
            onLayoutChange={handleLayoutChange}
            breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
            cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
            rowHeight={60}
            isDraggable={!isPreviewMode}
            isResizable={!isPreviewMode}
            margin={[16, 16]}
            containerPadding={[0, 0]}
          >
            {widgets.map((widget) => (
              <div key={widget.id}>
                <WidgetRenderer
                  type={widget.type}
                  data={widget.data}
                  title={widget.title}
                  onEdit={() => editWidget(widget)}
                  onDelete={() => deleteWidget(widget.id)}
                />
              </div>
            ))}
          </ResponsiveGridLayout>
        )}
      </div>

      {/* Modal d'ajout de widget */}
      <Modal
        title="Ajouter un widget"
        open={isAddWidgetVisible}
        onCancel={() => setIsAddWidgetVisible(false)}
        footer={null}
        width={800}
      >
        <Row gutter={[16, 16]}>
          {WIDGET_TYPES.map((widgetType) => (
            <Col xs={24} sm={12} md={8} key={widgetType.id}>
              <Card
                hoverable
                onClick={() => addWidget(widgetType.id)}
                style={{ cursor: 'pointer' }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '32px', color: widgetType.color, marginBottom: '8px' }}>
                    {widgetType.icon}
                  </div>
                  <Title level={5} style={{ marginBottom: '4px' }}>
                    {widgetType.name}
                  </Title>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {widgetType.description}
                  </Text>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Modal>

      {/* Modal d'édition de widget */}
      <Modal
        title="Configurer le widget"
        open={!!editingWidget}
        onCancel={() => setEditingWidget(null)}
        onOk={() => {
          form.validateFields().then(values => {
            setWidgets(prev => prev.map(w => 
              w.id === editingWidget.id 
                ? { ...w, title: values.title, config: { ...w.config, ...values } }
                : w
            ));
            setEditingWidget(null);
            form.resetFields();
          });
        }}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="title"
            label="Titre du widget"
            rules={[{ required: true, message: 'Le titre est requis' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="refreshInterval"
            label="Intervalle de rafraîchissement (secondes)"
          >
            <Select defaultValue={30}>
              <Option value={10}>10 secondes</Option>
              <Option value={30}>30 secondes</Option>
              <Option value={60}>1 minute</Option>
              <Option value={300}>5 minutes</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DashboardDesigner;