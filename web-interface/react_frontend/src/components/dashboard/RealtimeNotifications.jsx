/**
 * RealtimeNotifications - Composant de notifications temps réel
 * Gère les alertes push et les notifications visuelles
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  notification,
  Badge,
  Card,
  List,
  Typography,
  Space,
  Button,
  Drawer,
  Tag,
  Avatar,
  Tooltip,
  Switch,
  Select,
  Divider,
  Empty
} from 'antd';
import {
  BellOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  InfoCircleOutlined,
  SettingOutlined,
  ClearOutlined,
  SoundOutlined,
  EyeOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { useDashboard } from '../../hooks/useDashboard';

const { Title, Text } = Typography;
const { Option } = Select;

// Configuration des types d'alertes
const ALERT_TYPES = {
  critical: {
    icon: <CloseCircleOutlined />,
    color: '#ff4d4f',
    bgColor: '#fff2f0',
    borderColor: '#ffccc7',
    label: 'Critique',
    priority: 1
  },
  warning: {
    icon: <WarningOutlined />,
    color: '#faad14',
    bgColor: '#fffbe6',
    borderColor: '#ffe58f',
    label: 'Avertissement',
    priority: 2
  },
  info: {
    icon: <InfoCircleOutlined />,
    color: '#1890ff',
    bgColor: '#f6ffed',
    borderColor: '#b7eb8f',
    label: 'Information',
    priority: 3
  },
  success: {
    icon: <CheckCircleOutlined />,
    color: '#52c41a',
    bgColor: '#f6ffed',
    borderColor: '#b7eb8f',
    label: 'Succès',
    priority: 4
  }
};

const RealtimeNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isDrawerVisible, setIsDrawerVisible] = useState(false);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [filterType, setFilterType] = useState('all');
  const [autoMarkAsRead, setAutoMarkAsRead] = useState(false);
  const webSocketRef = useRef(null);
  const audioRef = useRef(null);

  // Hook pour les appels API
  const { fetchAlerts, isAuthenticated, apiCall } = useDashboard();

  // Sons de notification
  const playNotificationSound = useCallback((type) => {
    if (!soundEnabled) return;
    
    try {
      // Utiliser l'API Web Audio pour jouer des sons
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      // Différentes fréquences selon le type d'alerte
      const frequencies = {
        critical: 800,
        warning: 600,
        info: 400,
        success: 300
      };
      
      oscillator.frequency.value = frequencies[type] || 400;
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.5);
    } catch (error) {
      console.warn('Impossible de jouer le son de notification:', error);
    }
  }, [soundEnabled]);

  // Connexion WebSocket pour les notifications temps réel
  useEffect(() => {
    if (!isAuthenticated) return;

    const connectWebSocket = () => {
      try {
        const token = localStorage.getItem('auth_token');
        const wsUrl = `ws://localhost:8000/ws/notifications/?token=${token}`;
        
        webSocketRef.current = new WebSocket(wsUrl);
        
        webSocketRef.current.onopen = () => {
          console.log('WebSocket connecté pour les notifications');
        };
        
        webSocketRef.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleNewNotification(data);
          } catch (error) {
            console.error('Erreur lors du parsing du message WebSocket:', error);
          }
        };
        
        webSocketRef.current.onclose = () => {
          console.log('WebSocket fermé, tentative de reconnexion dans 5s');
          setTimeout(connectWebSocket, 5000);
        };
        
        webSocketRef.current.onerror = (error) => {
          console.error('Erreur WebSocket:', error);
        };
      } catch (error) {
        console.error('Erreur de connexion WebSocket:', error);
      }
    };

    connectWebSocket();

    return () => {
      if (webSocketRef.current) {
        webSocketRef.current.close();
      }
    };
  }, [isAuthenticated]);

  // Gérer les nouvelles notifications
  const handleNewNotification = useCallback((notificationData) => {
    const newNotification = {
      id: `notif-${Date.now()}-${Math.random()}`,
      type: notificationData.type || 'info',
      title: notificationData.title || 'Notification',
      message: notificationData.message || '',
      source: notificationData.source || 'Système',
      timestamp: new Date().toISOString(),
      read: false,
      ...notificationData
    };

    setNotifications(prev => [newNotification, ...prev]);
    setUnreadCount(prev => prev + 1);

    // Jouer le son de notification
    playNotificationSound(newNotification.type);

    // Afficher la notification native du navigateur
    if (Notification.permission === 'granted') {
      new Notification(newNotification.title, {
        body: newNotification.message,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: newNotification.id
      });
    }

    // Afficher la notification Ant Design
    const alertConfig = ALERT_TYPES[newNotification.type] || ALERT_TYPES.info;
    
    notification.open({
      message: newNotification.title,
      description: newNotification.message,
      icon: alertConfig.icon,
      placement: 'topRight',
      duration: newNotification.type === 'critical' ? 0 : 4.5,
      style: {
        borderLeft: `4px solid ${alertConfig.color}`
      },
      onClick: () => {
        setIsDrawerVisible(true);
        markAsRead(newNotification.id);
      }
    });

    // Marquer comme lu automatiquement si activé
    if (autoMarkAsRead) {
      setTimeout(() => {
        markAsRead(newNotification.id);
      }, 3000);
    }
  }, [playNotificationSound, autoMarkAsRead]);

  // Charger les notifications initiales
  useEffect(() => {
    const loadInitialNotifications = async () => {
      try {
        const alerts = await fetchAlerts();
        if (alerts && alerts.length > 0) {
          const formattedNotifications = alerts.map(alert => ({
            id: alert.id,
            type: alert.type || 'info',
            title: alert.title || 'Alerte',
            message: alert.message || '',
            source: alert.source || 'Monitoring',
            timestamp: alert.created_at || new Date().toISOString(),
            read: alert.read || false
          }));
          
          setNotifications(formattedNotifications);
          setUnreadCount(formattedNotifications.filter(n => !n.read).length);
        }
      } catch (error) {
        console.error('Erreur lors du chargement des notifications:', error);
      }
    };

    if (isAuthenticated) {
      loadInitialNotifications();
    }
  }, [isAuthenticated, fetchAlerts]);

  // Demander la permission pour les notifications natives
  useEffect(() => {
    if (Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  // Marquer une notification comme lue
  const markAsRead = useCallback((notificationId) => {
    setNotifications(prev => prev.map(n => 
      n.id === notificationId ? { ...n, read: true } : n
    ));
    setUnreadCount(prev => Math.max(0, prev - 1));
  }, []);

  // Marquer toutes les notifications comme lues
  const markAllAsRead = useCallback(() => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    setUnreadCount(0);
  }, []);

  // Supprimer une notification
  const deleteNotification = useCallback((notificationId) => {
    setNotifications(prev => {
      const notification = prev.find(n => n.id === notificationId);
      if (notification && !notification.read) {
        setUnreadCount(count => Math.max(0, count - 1));
      }
      return prev.filter(n => n.id !== notificationId);
    });
  }, []);

  // Effacer toutes les notifications
  const clearAllNotifications = useCallback(() => {
    setNotifications([]);
    setUnreadCount(0);
  }, []);

  // Filtrer les notifications
  const filteredNotifications = notifications.filter(notification => {
    if (filterType === 'all') return true;
    if (filterType === 'unread') return !notification.read;
    return notification.type === filterType;
  });

  // Rendu d'une notification
  const renderNotification = (notification) => {
    const alertConfig = ALERT_TYPES[notification.type] || ALERT_TYPES.info;
    
    return (
      <List.Item
        key={notification.id}
        style={{
          backgroundColor: notification.read ? '#fafafa' : alertConfig.bgColor,
          border: `1px solid ${notification.read ? '#f0f0f0' : alertConfig.borderColor}`,
          marginBottom: '8px',
          borderRadius: '6px',
          padding: '12px 16px'
        }}
        actions={[
          <Tooltip title={notification.read ? 'Marquer comme non lu' : 'Marquer comme lu'}>
            <Button
              type="text"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => markAsRead(notification.id)}
              style={{ opacity: notification.read ? 0.5 : 1 }}
            />
          </Tooltip>,
          <Tooltip title="Supprimer">
            <Button
              type="text"
              size="small"
              icon={<DeleteOutlined />}
              onClick={() => deleteNotification(notification.id)}
              danger
            />
          </Tooltip>
        ]}
      >
        <List.Item.Meta
          avatar={
            <Avatar 
              icon={alertConfig.icon} 
              style={{ backgroundColor: alertConfig.color }}
            />
          }
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontWeight: notification.read ? 'normal' : 'bold' }}>
                {notification.title}
              </span>
              <Tag color={alertConfig.color} size="small">
                {alertConfig.label}
              </Tag>
              {!notification.read && (
                <Badge status="processing" />
              )}
            </div>
          }
          description={
            <div>
              <div style={{ marginBottom: '4px' }}>
                {notification.message}
              </div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                <Space>
                  <span>{notification.source}</span>
                  <span>•</span>
                  <span>{new Date(notification.timestamp).toLocaleString()}</span>
                </Space>
              </div>
            </div>
          }
        />
      </List.Item>
    );
  };

  return (
    <>
      {/* Bouton de notification avec badge */}
      <Tooltip title="Notifications">
        <Button
          type="text"
          icon={
            <Badge count={unreadCount} size="small" offset={[2, -2]}>
              <BellOutlined style={{ fontSize: '18px' }} />
            </Badge>
          }
          onClick={() => setIsDrawerVisible(true)}
          style={{ marginRight: '8px' }}
        />
      </Tooltip>

      {/* Drawer des notifications */}
      <Drawer
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>Notifications</span>
            <Space>
              <Badge count={unreadCount} showZero />
              <Button
                type="text"
                icon={<SettingOutlined />}
                onClick={() => {/* Ouvrir les paramètres */}}
              />
            </Space>
          </div>
        }
        placement="right"
        width={400}
        open={isDrawerVisible}
        onClose={() => setIsDrawerVisible(false)}
        extra={
          <Space>
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={markAllAsRead}
              disabled={unreadCount === 0}
            >
              Tout marquer comme lu
            </Button>
            <Button
              type="text"
              icon={<ClearOutlined />}
              onClick={clearAllNotifications}
              disabled={notifications.length === 0}
              danger
            >
              Effacer tout
            </Button>
          </Space>
        }
      >
        {/* Paramètres rapides */}
        <Card size="small" style={{ marginBottom: '16px' }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>Sons activés</Text>
              <Switch
                checked={soundEnabled}
                onChange={setSoundEnabled}
                size="small"
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>Auto-marquer comme lu</Text>
              <Switch
                checked={autoMarkAsRead}
                onChange={setAutoMarkAsRead}
                size="small"
              />
            </div>
          </Space>
        </Card>

        {/* Filtres */}
        <div style={{ marginBottom: '16px' }}>
          <Select
            value={filterType}
            onChange={setFilterType}
            style={{ width: '100%' }}
            size="small"
          >
            <Option value="all">Toutes les notifications</Option>
            <Option value="unread">Non lues uniquement</Option>
            <Option value="critical">Critiques</Option>
            <Option value="warning">Avertissements</Option>
            <Option value="info">Informations</Option>
            <Option value="success">Succès</Option>
          </Select>
        </div>

        <Divider />

        {/* Liste des notifications */}
        {filteredNotifications.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="Aucune notification"
          />
        ) : (
          <List
            dataSource={filteredNotifications}
            renderItem={renderNotification}
            style={{ maxHeight: 'calc(100vh - 300px)', overflow: 'auto' }}
          />
        )}
      </Drawer>
    </>
  );
};

export default RealtimeNotifications;