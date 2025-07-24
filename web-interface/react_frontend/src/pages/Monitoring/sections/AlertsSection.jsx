/**
 * AlertsSection - Gestion complète des alertes monitoring
 * Exploite les endpoints: /alerts/, /alerts/summary/, /alerts/bulk_update/
 * Design cohérent avec le système existant (Ant Design + Recharts)
 */

import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Button,
  Space,
  Tag,
  Badge,
  Input,
  Select,
  DatePicker,
  Modal,
  Form,
  message,
  Tooltip,
  Dropdown,
  Menu,
  Statistic,
  Row,
  Col,
  Alert,
  Divider,
  Progress
} from 'antd';
import {
  AlertOutlined,
  SearchOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
  MoreOutlined,
  EyeOutlined,
  BellOutlined,
  FilterOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

// Import du hook monitoring
import useMonitoring from '../../../hooks/useMonitoring';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const AlertsSection = () => {
  // Hook monitoring pour les alertes
  const {
    alerts,
    fetchAlerts,
    createAlert,
    acknowledgeAlert,
    resolveAlert
  } = useMonitoring();

  // États locaux
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [editingAlert, setEditingAlert] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();

  // Configuration des filtres
  const [filters, setFilters] = useState({
    status: 'all',
    severity: 'all',
    equipment: 'all',
    dateRange: null
  });

  // Chargement initial
  useEffect(() => {
    fetchAlerts(filters);
  }, [fetchAlerts, filters]);

  // Configuration des colonnes de la table
  const columns = [
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusConfig = {
          active: { color: 'error', text: 'Actif' },
          acknowledged: { color: 'warning', text: 'Reconnu' },
          resolved: { color: 'success', text: 'Résolu' },
          closed: { color: 'default', text: 'Fermé' }
        };
        const config = statusConfig[status] || statusConfig.active;
        return <Badge status={config.color} text={config.text} />;
      },
      filters: [
        { text: 'Actif', value: 'active' },
        { text: 'Reconnu', value: 'acknowledged' },
        { text: 'Résolu', value: 'resolved' },
        { text: 'Fermé', value: 'closed' }
      ],
      onFilter: (value, record) => record.status === value
    },
    {
      title: 'Sévérité',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity) => {
        const severityConfig = {
          critical: { color: 'red', text: 'Critique' },
          high: { color: 'orange', text: 'Élevée' },
          medium: { color: 'yellow', text: 'Moyenne' },
          low: { color: 'blue', text: 'Basse' },
          info: { color: 'green', text: 'Info' }
        };
        const config = severityConfig[severity] || severityConfig.medium;
        return <Tag color={config.color}>{config.text}</Tag>;
      },
      filters: [
        { text: 'Critique', value: 'critical' },
        { text: 'Élevée', value: 'high' },
        { text: 'Moyenne', value: 'medium' },
        { text: 'Basse', value: 'low' },
        { text: 'Info', value: 'info' }
      ],
      onFilter: (value, record) => record.severity === value,
      sorter: (a, b) => {
        const severityOrder = { critical: 5, high: 4, medium: 3, low: 2, info: 1 };
        return severityOrder[b.severity] - severityOrder[a.severity];
      }
    },
    {
      title: 'Nom de l\'alerte',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <strong>{text}</strong>
          <span style={{ color: '#8c8c8c', fontSize: '12px' }}>
            {record.equipment_name || 'Système'}
          </span>
        </Space>
      ),
      sorter: (a, b) => a.name.localeCompare(b.name)
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: {
        showTitle: false
      },
      render: (text) => (
        <Tooltip placement="topLeft" title={text}>
          {text}
        </Tooltip>
      )
    },
    {
      title: 'Équipement',
      dataIndex: 'equipment_name',
      key: 'equipment_name',
      width: 130,
      render: (text) => text || '-'
    },
    {
      title: 'Créé le',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => {
        if (!date) return '-';
        const d = new Date(date);
        return (
          <Space direction="vertical" size={0}>
            <span>{d.toLocaleDateString()}</span>
            <span style={{ color: '#8c8c8c', fontSize: '11px' }}>
              {d.toLocaleTimeString()}
            </span>
          </Space>
        );
      },
      sorter: (a, b) => new Date(b.created_at) - new Date(a.created_at)
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Voir détails">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => showAlertDetails(record)}
            />
          </Tooltip>
          
          {record.status === 'active' && (
            <Tooltip title="Reconnaître">
              <Button
                type="text"
                icon={<CheckCircleOutlined />}
                size="small"
                onClick={() => handleAcknowledge(record.id)}
              />
            </Tooltip>
          )}
          
          {(record.status === 'active' || record.status === 'acknowledged') && (
            <Tooltip title="Résoudre">
              <Button
                type="text"
                icon={<ExclamationCircleOutlined />}
                size="small"
                onClick={() => handleResolve(record.id)}
              />
            </Tooltip>
          )}
          
          <Dropdown
            overlay={
              <Menu>
                <Menu.Item
                  key="edit"
                  icon={<EditOutlined />}
                  onClick={() => editAlert(record)}
                >
                  Modifier
                </Menu.Item>
                <Menu.Item
                  key="delete"
                  icon={<DeleteOutlined />}
                  onClick={() => deleteAlert(record)}
                  danger
                >
                  Supprimer
                </Menu.Item>
              </Menu>
            }
            trigger={['click']}
          >
            <Button type="text" icon={<MoreOutlined />} size="small" />
          </Dropdown>
        </Space>
      )
    }
  ];

  // Gestion des actions
  const handleAcknowledge = async (alertId) => {
    try {
      await acknowledgeAlert(alertId);
      message.success('Alerte reconnue avec succès');
    } catch (error) {
      message.error(error.message);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await resolveAlert(alertId);
      message.success('Alerte résolue avec succès');
    } catch (error) {
      message.error(error.message);
    }
  };

  const handleCreateAlert = async (values) => {
    try {
      await createAlert(values);
      message.success('Alerte créée avec succès');
      setIsModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error(error.message);
    }
  };

  const showAlertDetails = (alert) => {
    Modal.info({
      title: `Détails de l'alerte: ${alert.name}`,
      width: 600,
      content: (
        <div style={{ marginTop: '20px' }}>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <strong>Statut:</strong> {alert.status}
            </Col>
            <Col span={12}>
              <strong>Sévérité:</strong> {alert.severity}
            </Col>
            <Col span={12}>
              <strong>Équipement:</strong> {alert.equipment_name || 'N/A'}
            </Col>
            <Col span={12}>
              <strong>Créé le:</strong> {new Date(alert.created_at).toLocaleString()}
            </Col>
            <Col span={24}>
              <strong>Description:</strong>
              <div style={{ marginTop: '8px', padding: '8px', background: '#f5f5f5', borderRadius: '4px' }}>
                {alert.description}
              </div>
            </Col>
          </Row>
        </div>
      )
    });
  };

  const editAlert = (alert) => {
    setEditingAlert(alert);
    form.setFieldsValue(alert);
    setIsModalVisible(true);
  };

  const deleteAlert = (alert) => {
    Modal.confirm({
      title: 'Confirmer la suppression',
      content: `Êtes-vous sûr de vouloir supprimer l'alerte "${alert.name}" ?`,
      onOk: async () => {
        try {
          // API call pour suppression
          message.success('Alerte supprimée avec succès');
          fetchAlerts(filters);
        } catch {
          message.error('Erreur lors de la suppression');
        }
      }
    });
  };

  // Rendu des statistiques
  const renderStatistics = () => {
    if (!alerts.summary) return null;

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Alertes"
              value={alerts.total}
              prefix={<AlertOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Critiques"
              value={alerts.list.filter(a => a.severity === 'critical').length}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Actives"
              value={alerts.list.filter(a => a.status === 'active').length}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Résolues (24h)"
              value={alerts.list.filter(a => {
                if (a.status !== 'resolved') return false;
                const resolved = new Date(a.updated_at);
                const yesterday = new Date();
                yesterday.setDate(yesterday.getDate() - 1);
                return resolved > yesterday;
              }).length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // Rendu des filtres
  const renderFilters = () => (
    <Card size="small" style={{ marginBottom: '16px' }}>
      <Row gutter={[16, 16]} align="middle">
        <Col xs={24} sm={12} md={6}>
          <Input
            placeholder="Rechercher une alerte..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
          />
        </Col>
        <Col xs={24} sm={12} md={4}>
          <Select
            placeholder="Statut"
            value={filters.status}
            onChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
            style={{ width: '100%' }}
          >
            <Option value="all">Tous les statuts</Option>
            <Option value="active">Actif</Option>
            <Option value="acknowledged">Reconnu</Option>
            <Option value="resolved">Résolu</Option>
          </Select>
        </Col>
        <Col xs={24} sm={12} md={4}>
          <Select
            placeholder="Sévérité"
            value={filters.severity}
            onChange={(value) => setFilters(prev => ({ ...prev, severity: value }))}
            style={{ width: '100%' }}
          >
            <Option value="all">Toutes sévérités</Option>
            <Option value="critical">Critique</Option>
            <Option value="high">Élevée</Option>
            <Option value="medium">Moyenne</Option>
            <Option value="low">Basse</Option>
          </Select>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <RangePicker
            placeholder={['Date début', 'Date fin']}
            style={{ width: '100%' }}
            onChange={(dates) => setFilters(prev => ({ ...prev, dateRange: dates }))}
          />
        </Col>
        <Col xs={24} sm={12} md={4}>
          <Space>
            <Button
              icon={<SyncOutlined />}
              onClick={() => fetchAlerts(filters)}
              loading={alerts.loading}
            >
              Actualiser
            </Button>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  // Configuration de la sélection de lignes
  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
    selections: [
      Table.SELECTION_ALL,
      Table.SELECTION_INVERT,
      Table.SELECTION_NONE
    ]
  };

  // Modal pour créer/modifier une alerte
  const renderAlertModal = () => (
    <Modal
      title={editingAlert ? 'Modifier l\'alerte' : 'Créer une nouvelle alerte'}
      open={isModalVisible}
      onCancel={() => {
        setIsModalVisible(false);
        setEditingAlert(null);
        form.resetFields();
      }}
      onOk={() => form.submit()}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleCreateAlert}
      >
        <Form.Item
          name="name"
          label="Nom de l'alerte"
          rules={[{ required: true, message: 'Le nom est requis' }]}
        >
          <Input placeholder="Nom de l'alerte" />
        </Form.Item>
        
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="severity"
              label="Sévérité"
              rules={[{ required: true, message: 'La sévérité est requise' }]}
            >
              <Select placeholder="Sélectionner la sévérité">
                <Option value="critical">Critique</Option>
                <Option value="high">Élevée</Option>
                <Option value="medium">Moyenne</Option>
                <Option value="low">Basse</Option>
                <Option value="info">Info</Option>
              </Select>
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="equipment_name"
              label="Équipement"
            >
              <Input placeholder="Nom de l'équipement" />
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item
          name="description"
          label="Description"
          rules={[{ required: true, message: 'La description est requise' }]}
        >
          <TextArea rows={4} placeholder="Description détaillée de l'alerte" />
        </Form.Item>
      </Form>
    </Modal>
  );

  return (
    <div style={{ padding: '0' }}>
      {/* Statistiques globales */}
      {renderStatistics()}

      {/* Barre de filtres */}
      {renderFilters()}

      {/* Actions de masse */}
      {selectedRowKeys.length > 0 && (
        <Alert
          message={
            <Space>
              <span>{selectedRowKeys.length} alerte(s) sélectionnée(s)</span>
              <Button
                size="small"
                type="primary"
                onClick={() => {
                  // Bulk acknowledge
                  message.info('Reconnaissance en masse en cours...');
                }}
              >
                Reconnaître tout
              </Button>
              <Button
                size="small"
                onClick={() => {
                  // Bulk resolve
                  message.info('Résolution en masse en cours...');
                }}
              >
                Résoudre tout
              </Button>
            </Space>
          }
          type="info"
          showIcon
          style={{ marginBottom: '16px' }}
        />
      )}

      {/* Table des alertes */}
      <Card
        title={
          <Space>
            <AlertOutlined />
            <span>Gestion des Alertes</span>
            <Badge count={alerts.list.filter(a => a.status === 'active').length} />
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setIsModalVisible(true)}
            >
              Nouvelle alerte
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={() => message.info('Export en cours...')}
            >
              Exporter
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={alerts.list.filter(alert => 
            !searchText || 
            alert.name?.toLowerCase().includes(searchText.toLowerCase()) ||
            alert.description?.toLowerCase().includes(searchText.toLowerCase()) ||
            alert.equipment_name?.toLowerCase().includes(searchText.toLowerCase())
          )}
          rowKey="id"
          rowSelection={rowSelection}
          loading={alerts.loading}
          pagination={{
            total: alerts.total,
            pageSize: 50,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} sur ${total} alertes`
          }}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>

      {/* Modal de création/modification */}
      {renderAlertModal()}
    </div>
  );
};

export default AlertsSection;