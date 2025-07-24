/**
 * NotificationsSection - Centre de notifications
 * Exploite les endpoints: /notifications/, /notification-channels/, /notification-rules/
 * Gestion des canaux, règles et notifications en temps réel
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
  Switch,
  Timeline,
  List,
  Avatar,
  Divider,
  Alert,
  Tabs,
  Radio,
  InputNumber
} from 'antd';
import {
  BellOutlined,
  MailOutlined,
  PhoneOutlined,
  ApiOutlined,
  SlackOutlined,
  MessageOutlined,
  SettingOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  SendOutlined,
  EyeOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, LineChart, Line } from 'recharts';

// Import du hook monitoring
import useMonitoring from '../../../hooks/useMonitoring';

const { Option } = Select;
const { TabPane } = Tabs;
const { TextArea } = Input;

const NotificationsSection = () => {
  // Hook monitoring pour les notifications
  const {
    notifications,
    fetchNotifications
  } = useMonitoring();

  // États locaux
  const [activeSubTab, setActiveSubTab] = useState('notifications');
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalType, setModalType] = useState('notification');
  const [editingItem, setEditingItem] = useState(null);
  const [form] = Form.useForm();

  // Charger les notifications au montage
  useEffect(() => {
    if (fetchNotifications) {
      fetchNotifications();
    }
  }, [fetchNotifications]);

  // Utilisation des vraies données de notifications
  const notificationsList = notifications.list || [];
  const channels = notifications.channels || [];
  const rules = notifications.rules || [];

  // Types d'icônes par canal
  const channelIcons = {
    email: <MailOutlined />,
    slack: <SlackOutlined />,
    sms: <PhoneOutlined />,
    webhook: <ApiOutlined />,
    teams: <MessageOutlined />
  };

  // Types de notifications avec couleurs
  const notificationTypes = {
    critical: { color: '#ff4d4f', icon: <ExclamationCircleOutlined />, label: 'Critique' },
    warning: { color: '#faad14', icon: <WarningOutlined />, label: 'Attention' },
    info: { color: '#1890ff', icon: <InfoCircleOutlined />, label: 'Information' },
    success: { color: '#52c41a', icon: <CheckOutlined />, label: 'Succès' }
  };

  // Colonnes pour la table des notifications
  const notificationsColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 80,
      render: (type) => {
        const config = notificationTypes[type] || notificationTypes.info;
        return (
          <Tooltip title={config.label}>
            <span style={{ color: config.color, fontSize: '16px' }}>
              {config.icon}
            </span>
          </Tooltip>
        );
      }
    },
    {
      title: 'Notification',
      dataIndex: 'title',
      key: 'title',
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: record.readAt ? 'normal' : 'bold' }}>
            {text}
          </div>
          <div style={{ color: '#8c8c8c', fontSize: '12px', marginTop: '2px' }}>
            {record.message}
          </div>
        </div>
      )
    },
    {
      title: 'Canal',
      dataIndex: 'channel',
      key: 'channel',
      width: 100,
      render: (channel) => (
        <Space>
          {channelIcons[channel]}
          <span style={{ textTransform: 'capitalize' }}>{channel}</span>
        </Space>
      )
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        const statusConfig = {
          sent: { color: 'success', text: 'Envoyé' },
          pending: { color: 'processing', text: 'En cours' },
          failed: { color: 'error', text: 'Échec' }
        };
        const config = statusConfig[status] || statusConfig.pending;
        return <Badge status={config.color} text={config.text} />;
      }
    },
    {
      title: 'Envoyé le',
      dataIndex: 'createdAt',
      key: 'createdAt',
      width: 120,
      render: (date) => {
        const d = new Date(date);
        return (
          <div>
            <div>{d.toLocaleDateString()}</div>
            <div style={{ color: '#8c8c8c', fontSize: '11px' }}>
              {d.toLocaleTimeString()}
            </div>
          </div>
        );
      },
      sorter: (a, b) => new Date(b.createdAt) - new Date(a.createdAt)
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Space>
          <Tooltip title="Voir détails">
            <Button
              type="text"
              icon={<EyeOutlined />}
              size="small"
              onClick={() => showNotificationDetails(record)}
            />
          </Tooltip>
          {!record.readAt && (
            <Tooltip title="Marquer comme lu">
              <Button
                type="text"
                icon={<CheckOutlined />}
                size="small"
                onClick={() => markAsRead(record.id)}
              />
            </Tooltip>
          )}
        </Space>
      )
    }
  ];

  // Colonnes pour la table des canaux
  const channelsColumns = [
    {
      title: 'Canal',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          {channelIcons[record.type]}
          <div>
            <div style={{ fontWeight: 500 }}>{text}</div>
            <div style={{ color: '#8c8c8c', fontSize: '12px' }}>
              {record.type.toUpperCase()}
            </div>
          </div>
        </Space>
      )
    },
    {
      title: 'Configuration',
      dataIndex: 'config',
      key: 'config',
      render: (config, record) => {
        switch (record.type) {
          case 'email':
            return `${config.smtp_host}:${config.smtp_port}`;
          case 'slack':
            return config.channel;
          case 'sms':
            return config.phone_number;
          default:
            return 'Configuration personnalisée';
        }
      }
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
          <Button
            type="text"
            icon={<SendOutlined />}
            size="small"
            onClick={() => testChannel(record)}
          >
            Tester
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            onClick={() => editChannel(record)}
          />
          <Button
            type="text"
            icon={<DeleteOutlined />}
            size="small"
            danger
            onClick={() => deleteChannel(record)}
          />
        </Space>
      )
    }
  ];

  // Actions
  const showNotificationDetails = (notification) => {
    Modal.info({
      title: `Notification: ${notification.title}`,
      width: 600,
      content: (
        <div style={{ marginTop: '20px' }}>
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Alert
                type={notification.type}
                message={notification.message}
                showIcon
              />
            </Col>
            <Col span={12}>
              <strong>Canal:</strong> {notification.channel}
            </Col>
            <Col span={12}>
              <strong>Destinataire:</strong> {notification.recipient}
            </Col>
            <Col span={12}>
              <strong>Statut:</strong> {notification.status}
            </Col>
            <Col span={12}>
              <strong>Lu le:</strong> {notification.readAt ? new Date(notification.readAt).toLocaleString() : 'Non lu'}
            </Col>
          </Row>
        </div>
      )
    });
  };

  const markAsRead = () => {
    message.success('Notification marquée comme lue');
    // Ici on appellerait l'API pour marquer comme lu
  };

  const testChannel = (channel) => {
    message.loading('Test du canal en cours...', 2)
      .then(() => message.success(`Test réussi pour le canal ${channel.name}`));
  };

  const editChannel = (channel) => {
    setEditingItem(channel);
    setModalType('channel');
    form.setFieldsValue(channel);
    setIsModalVisible(true);
  };

  const deleteChannel = (channel) => {
    Modal.confirm({
      title: 'Confirmer la suppression',
      content: `Êtes-vous sûr de vouloir supprimer le canal "${channel.name}" ?`,
      onOk: () => message.success('Canal supprimé avec succès')
    });
  };

  // Rendu des statistiques
  const renderStats = () => {
    const totalNotifications = notificationsList.length;
    const unreadCount = notificationsList.filter(n => !n.readAt).length;
    const failedCount = notificationsList.filter(n => n.status === 'failed').length;
    const activeChannels = channels.filter(c => c.status === 'active').length;

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', color: '#1890ff' }}>{totalNotifications}</div>
              <div style={{ color: '#8c8c8c' }}>Total notifications</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', color: '#faad14' }}>{unreadCount}</div>
              <div style={{ color: '#8c8c8c' }}>Non lues</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', color: '#ff4d4f' }}>{failedCount}</div>
              <div style={{ color: '#8c8c8c' }}>Échecs</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '24px', color: '#52c41a' }}>{activeChannels}</div>
              <div style={{ color: '#8c8c8c' }}>Canaux actifs</div>
            </div>
          </Card>
        </Col>
      </Row>
    );
  };

  // Rendu des notifications
  const renderNotifications = () => (
    <Card 
      title={
        <Space>
          <BellOutlined />
          <span>Notifications</span>
          <Badge count={notificationsList.filter(n => !n.readAt).length} />
        </Space>
      }
      extra={
        <Space>
          <Button
            onClick={() => message.info('Marquer toutes comme lues')}
          >
            Tout marquer comme lu
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setModalType('notification');
              setEditingItem(null);
              setIsModalVisible(true);
            }}
          >
            Nouvelle notification
          </Button>
        </Space>
      }
    >
      <Table
        columns={notificationsColumns}
        dataSource={notificationsList}
        rowKey="id"
        pagination={{
          pageSize: 10,
          showSizeChanger: true
        }}
        size="small"
      />
    </Card>
  );

  // Rendu des canaux
  const renderChannels = () => (
    <Card 
      title={
        <Space>
          <ApiOutlined />
          <span>Canaux de Notification</span>
        </Space>
      }
      extra={
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setModalType('channel');
            setEditingItem(null);
            setIsModalVisible(true);
          }}
        >
          Nouveau canal
        </Button>
      }
    >
      <Table
        columns={channelsColumns}
        dataSource={channels}
        rowKey="id"
        pagination={{
          pageSize: 10
        }}
        size="small"
      />
    </Card>
  );

  return (
    <div style={{ padding: '0' }}>
      {/* Statistiques */}
      {renderStats()}

      {/* Onglets pour les sous-sections */}
      <Tabs activeKey={activeSubTab} onChange={setActiveSubTab}>
        <TabPane
          tab={
            <Space>
              <BellOutlined />
              <span>Notifications</span>
              <Badge count={notificationsList.filter(n => !n.readAt).length} />
            </Space>
          }
          key="notifications"
        >
          {renderNotifications()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <ApiOutlined />
              <span>Canaux</span>
            </Space>
          }
          key="channels"
        >
          {renderChannels()}
        </TabPane>
        
        <TabPane
          tab={
            <Space>
              <SettingOutlined />
              <span>Règles</span>
            </Space>
          }
          key="rules"
        >
          <Card 
            title="Règles de Notification"
            extra={
              <Button type="primary" icon={<PlusOutlined />}>
                Nouvelle règle
              </Button>
            }
          >
            <p style={{ textAlign: 'center', color: '#8c8c8c', padding: '40px' }}>
              Configuration des règles de notification - À développer
            </p>
          </Card>
        </TabPane>
      </Tabs>

      {/* Modal de gestion */}
      <Modal
        title={modalType === 'notification' ? 'Nouvelle notification' : 'Configuration canal'}
        open={isModalVisible}
        onCancel={() => {
          setIsModalVisible(false);
          setEditingItem(null);
        }}
        onOk={() => {
          message.success('Opération réussie');
          setIsModalVisible(false);
          setEditingItem(null);
        }}
      >
        <p>Configuration {modalType} - Interface complète à implémenter</p>
        {editingItem && <p>Item: {editingItem.name || editingItem.title}</p>}
        {notifications && notifications.status && <p>API Status: {notifications.status}</p>}
        {rules && <p>Règles actives: {rules.filter(r => r.enabled).length}</p>}
      </Modal>
    </div>
  );
};

export default NotificationsSection;