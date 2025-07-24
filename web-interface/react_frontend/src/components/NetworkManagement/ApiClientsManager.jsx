/**
 * API Clients Manager - Interface de gestion des clients API
 * Composant principal pour le module api_clients
 */

import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Tooltip, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Switch, 
  Statistic, 
  Row, 
  Col,
  Divider,
  Alert,
  Progress,
  Badge
} from 'antd';
import {
  ApiOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
  PlusOutlined,
  SettingOutlined,
  BarChartOutlined,
  HeartOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import { useApiClients } from '../../hooks/useApiClients';

const { Option } = Select;
const { confirm } = Modal;

/**
 * Composant principal de gestion des clients API
 */
const ApiClientsManager = () => {
  const {
    clients,
    loading,
    error,
    currentClient,
    fetchClients,
    testClient,
    updateClientConfig,
    getStats,
    getActiveClients,
    getUnhealthyClients,
    clearError
  } = useApiClients();

  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' | 'edit' | 'test'
  const [form] = Form.useForm();
  const [refreshing, setRefreshing] = useState(false);

  // Charger les clients au montage
  useEffect(() => {
    handleRefresh();
  }, []);

  // Actualiser les données
  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetchClients();
    } finally {
      setRefreshing(false);
    }
  };

  // Test de connectivité d'un client
  const handleTestClient = async (clientId) => {
    try {
      await testClient(clientId);
    } catch (error) {
      console.error('Erreur test client:', error);
    }
  };

  // Ouvrir modal de configuration
  const showConfigModal = (mode, client = null) => {
    setModalMode(mode);
    setIsModalVisible(true);
    
    if (client && mode === 'edit') {
      form.setFieldsValue({
        name: client.name,
        client_type: client.client_type,
        host: client.host,
        port: client.port,
        is_active: client.is_active,
        timeout: client.timeout || 30,
        description: client.description
      });
    } else {
      form.resetFields();
    }
  };

  // Fermer modal
  const handleModalCancel = () => {
    setIsModalVisible(false);
    form.resetFields();
  };

  // Sauvegarder configuration
  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (modalMode === 'create') {
        // Logique de création (à implémenter côté service)
        console.log('Création client:', values);
      } else if (modalMode === 'edit') {
        await updateClientConfig(currentClient.id, values);
      }
      
      setIsModalVisible(false);
      form.resetFields();
      await handleRefresh();
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
    }
  };

  // Supprimer client
  const handleDeleteClient = (client) => {
    confirm({
      title: 'Supprimer le client',
      content: `Êtes-vous sûr de vouloir supprimer "${client.name}" ?`,
      okText: 'Supprimer',
      okType: 'danger',
      cancelText: 'Annuler',
      onOk: async () => {
        // Logique de suppression (à implémenter)
        console.log('Suppression client:', client.id);
        await handleRefresh();
      }
    });
  };

  // Configuration des colonnes du tableau
  const columns = [
    {
      title: 'Nom',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text, record) => (
        <Space>
          <ApiOutlined style={{ color: record.is_active ? '#52c41a' : '#d9d9d9' }} />
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: 'Type',
      dataIndex: 'client_type',
      key: 'client_type',
      width: 120,
      render: (type) => {
        const colors = {
          gns3: 'blue',
          snmp: 'green',
          prometheus: 'orange',
          grafana: 'purple',
          elasticsearch: 'cyan',
          fail2ban: 'red',
          suricata: 'magenta'
        };
        return <Tag color={colors[type] || 'default'}>{type.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Adresse',
      key: 'address',
      width: 200,
      render: (_, record) => `${record.host}:${record.port}`
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status, record) => {
        const config = {
          healthy: { color: 'success', icon: <CheckCircleOutlined />, text: 'Sain' },
          unhealthy: { color: 'error', icon: <CloseCircleOutlined />, text: 'Défaillant' },
          unknown: { color: 'warning', icon: <ExclamationCircleOutlined />, text: 'Inconnu' }
        };
        
        const statusConfig = config[status] || config.unknown;
        
        return (
          <Badge 
            status={statusConfig.color} 
            text={
              <Space>
                {statusConfig.icon}
                {statusConfig.text}
              </Space>
            }
          />
        );
      }
    },
    {
      title: 'Actif',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (isActive) => (
        <Switch 
          checked={isActive} 
          size="small" 
          disabled
        />
      )
    },
    {
      title: 'Derniers tests',
      key: 'test_info',
      width: 150,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          {record.test_passed !== undefined && (
            <Tag color={record.test_passed ? 'success' : 'error'}>
              {record.test_passed ? 'Réussi' : 'Échec'}
            </Tag>
          )}
          {record.response_time && (
            <span style={{ fontSize: '12px', color: '#666' }}>
              {record.response_time}ms
            </span>
          )}
        </Space>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Tooltip title="Tester la connexion">
            <Button
              type="primary"
              size="small"
              icon={<ThunderboltOutlined />}
              onClick={() => handleTestClient(record.id)}
              loading={loading.test}
            />
          </Tooltip>
          
          <Tooltip title="Configurer">
            <Button
              size="small"
              icon={<SettingOutlined />}
              onClick={() => showConfigModal('edit', record)}
            />
          </Tooltip>
          
          <Tooltip title="Supprimer">
            <Button
              danger
              size="small"
              icon={<CloseCircleOutlined />}
              onClick={() => handleDeleteClient(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  // Sélection des lignes
  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys
  };

  // Statistiques générales
  const stats = getStats();
  const activeClients = getActiveClients();
  const unhealthyClients = getUnhealthyClients();

  return (
    <div style={{ padding: '24px' }}>
      {/* En-tête avec statistiques */}
      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Total Clients"
              value={stats.total}
              prefix={<ApiOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Clients Actifs"
              value={stats.active}
              valueStyle={{ color: '#3f8600' }}
              prefix={<CheckCircleOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Clients Sains"
              value={stats.healthy}
              valueStyle={{ color: '#52c41a' }}
              prefix={<HeartOutlined />}
            />
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Statistic
              title="Taux de Santé"
              value={stats.total > 0 ? ((stats.healthy / stats.total) * 100).toFixed(1) : 0}
              suffix="%"
              valueStyle={{ 
                color: stats.total > 0 && (stats.healthy / stats.total) > 0.8 ? '#3f8600' : '#cf1322' 
              }}
              prefix={<BarChartOutlined />}
            />
          </Col>
        </Row>
      </Card>

      {/* Alertes */}
      {error && (
        <Alert
          message="Erreur"
          description={error.message || 'Une erreur est survenue'}
          type="error"
          showIcon
          closable
          onClose={clearError}
          style={{ marginBottom: '16px' }}
        />
      )}

      {unhealthyClients.length > 0 && (
        <Alert
          message={`${unhealthyClients.length} client(s) en défaillance`}
          description="Certains clients ne répondent pas correctement"
          type="warning"
          showIcon
          style={{ marginBottom: '16px' }}
        />
      )}

      {/* Actions globales */}
      <Card 
        title={
          <Space>
            <ApiOutlined />
            Gestion des Clients API
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => showConfigModal('create')}
            >
              Nouveau Client
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
              loading={refreshing}
            >
              Actualiser
            </Button>
          </Space>
        }
        style={{ marginBottom: '16px' }}
      >
        <Table
          columns={columns}
          dataSource={clients}
          rowKey="id"
          rowSelection={rowSelection}
          loading={loading.fetch}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} sur ${total} clients`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Modal de configuration */}
      <Modal
        title={
          modalMode === 'create' ? 'Nouveau Client API' :
          modalMode === 'edit' ? 'Modifier Client API' : 'Test Client'
        }
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={600}
        confirmLoading={loading.update}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            is_active: true,
            timeout: 30,
            port: 80
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Nom"
                name="name"
                rules={[{ required: true, message: 'Le nom est obligatoire' }]}
              >
                <Input placeholder="Nom du client" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Type"
                name="client_type"
                rules={[{ required: true, message: 'Le type est obligatoire' }]}
              >
                <Select placeholder="Sélectionner un type">
                  <Option value="gns3">GNS3</Option>
                  <Option value="snmp">SNMP</Option>
                  <Option value="prometheus">Prometheus</Option>
                  <Option value="grafana">Grafana</Option>
                  <Option value="elasticsearch">Elasticsearch</Option>
                  <Option value="fail2ban">Fail2Ban</Option>
                  <Option value="suricata">Suricata</Option>
                  <Option value="haproxy">HAProxy</Option>
                  <Option value="netdata">Netdata</Option>
                  <Option value="ntopng">ntopng</Option>
                  <Option value="netflow">NetFlow</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={16}>
              <Form.Item
                label="Hôte"
                name="host"
                rules={[{ required: true, message: "L'hôte est obligatoire" }]}
              >
                <Input placeholder="localhost ou IP" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                label="Port"
                name="port"
                rules={[
                  { required: true, message: 'Le port est obligatoire' },
                  { type: 'number', min: 1, max: 65535, message: 'Port invalide' }
                ]}
              >
                <Input type="number" placeholder="80" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="Description"
            name="description"
          >
            <Input.TextArea 
              rows={3} 
              placeholder="Description optionnelle du client"
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Timeout (secondes)"
                name="timeout"
              >
                <Input type="number" placeholder="30" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Actif"
                name="is_active"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default ApiClientsManager;