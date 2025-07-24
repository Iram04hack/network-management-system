import React, { useState, useEffect } from 'react';
import { Table, Input, Button, Select, Badge, Card, Timeline, Tabs, Form, Space, Tag, Tooltip, Spin, message, Progress, Modal } from 'antd';
import { SearchOutlined, PlusOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined, StopOutlined, DownloadOutlined, ReloadOutlined, WifiOutlined, ShareAltOutlined, DatabaseOutlined, CloudServerOutlined, SafetyOutlined } from '@ant-design/icons';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';

const { TabPane } = Tabs;
const { Option } = Select;

const NetworkManagement = () => {
  // États locaux pour l'interface utilisateur
  const [activeTab, setActiveTab] = useState('devices');
  const [isLoading, setIsLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [deviceTypeFilter, setDeviceTypeFilter] = useState('all');
  const [deviceStatusFilter, setDeviceStatusFilter] = useState('all');
  const [discoveryInProgress, setDiscoveryInProgress] = useState(false);
  const [discoveryProgress, setDiscoveryProgress] = useState(0);
  const [editingDevice, setEditingDevice] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);

  // Données mockées pour les équipements réseau selon l'architecture
  const [networkDevices] = useState([
    {
      id: 'device-1',
      name: 'Router-Principal',
      type: 'router',
      vendor: 'Cisco',
      model: 'ISR 4331',
      ip_address: '192.168.1.1',
      mac_address: '00:1B:44:11:3A:B7',
      status: 'online',
      location: 'Salle Serveur A',
      last_seen: new Date(Date.now() - 300000).toISOString(),
      uptime: '45 jours, 12h',
      cpu_usage: 23,
      memory_usage: 45,
      interfaces: 8,
      active_interfaces: 6,
      snmp_enabled: true,
      snmp_community: 'public'
    },
    {
      id: 'device-2',
      name: 'Switch-Core-01',
      type: 'switch',
      vendor: 'HP',
      model: 'Aruba 3810M',
      ip_address: '192.168.1.10',
      mac_address: '94:57:A5:60:0F:C2',
      status: 'online',
      location: 'Salle Serveur A',
      last_seen: new Date(Date.now() - 150000).toISOString(),
      uptime: '38 jours, 8h',
      cpu_usage: 12,
      memory_usage: 38,
      interfaces: 24,
      active_interfaces: 18,
      snmp_enabled: true,
      snmp_community: 'public'
    },
    {
      id: 'device-3',
      name: 'AP-Bureau-01',
      type: 'wireless',
      vendor: 'Ubiquiti',
      model: 'UniFi AP AC Pro',
      ip_address: '192.168.1.50',
      mac_address: '24:A4:3C:9B:12:F4',
      status: 'online',
      location: 'Bureau Principal',
      last_seen: new Date(Date.now() - 60000).toISOString(),
      uptime: '12 jours, 4h',
      cpu_usage: 8,
      memory_usage: 22,
      interfaces: 2,
      active_interfaces: 2,
      connected_clients: 15,
      snmp_enabled: false
    },
    {
      id: 'device-4',
      name: 'Server-Web-01',
      type: 'server',
      vendor: 'Dell',
      model: 'PowerEdge R740',
      ip_address: '192.168.1.100',
      mac_address: '90:B1:1C:5E:2A:8C',
      status: 'warning',
      location: 'Datacenter',
      last_seen: new Date(Date.now() - 900000).toISOString(),
      uptime: '128 jours, 15h',
      cpu_usage: 78,
      memory_usage: 85,
      interfaces: 4,
      active_interfaces: 2,
      snmp_enabled: true,
      snmp_community: 'private'
    },
    {
      id: 'device-5',
      name: 'Firewall-01',
      type: 'firewall',
      vendor: 'Fortinet',
      model: 'FortiGate 100F',
      ip_address: '192.168.1.254',
      mac_address: '00:09:0F:FE:00:01',
      status: 'offline',
      location: 'DMZ',
      last_seen: new Date(Date.now() - 3600000).toISOString(),
      uptime: '0 jours, 0h',
      cpu_usage: 0,
      memory_usage: 0,
      interfaces: 10,
      active_interfaces: 0,
      snmp_enabled: false
    }
  ]);

  // Statistiques de réseau mockées selon l'architecture
  const [networkStats] = useState({
    totalDevices: 5,
    onlineDevices: 3,
    warningDevices: 1,
    offlineDevices: 1,
    totalInterfaces: 48,
    activeInterfaces: 28,
    averageCpuUsage: 24.2,
    averageMemoryUsage: 38.0,
    networkHealth: 78,
    snmpDevices: 3,
    discoveredToday: 2
  });

  // Données pour les graphiques de topologie et performance
  const [topologyStats] = useState([
    { name: 'Routeurs', count: 1, color: '#1890ff' },
    { name: 'Switches', count: 1, color: '#52c41a' },
    { name: 'Serveurs', count: 1, color: '#faad14' },
    { name: 'Points d\'accès', count: 1, color: '#13c2c2' },
    { name: 'Firewalls', count: 1, color: '#eb2f96' }
  ]);

  const [performanceData] = useState([
    { time: '14:00', cpu: 20, memory: 35, network: 450 },
    { time: '14:30', cpu: 25, memory: 40, network: 680 },
    { time: '15:00', cpu: 28, memory: 42, network: 890 },
    { time: '15:30', cpu: 24, memory: 38, network: 760 },
    { time: '16:00', cpu: 22, memory: 36, network: 650 }
  ]);

  // Données SNMP mockées
  const [snmpData] = useState([
    {
      device: 'Router-Principal',
      oid: '1.3.6.1.2.1.1.1.0',
      name: 'sysDescr',
      value: 'Cisco IOS Software, C4300 Software',
      lastUpdate: new Date().toISOString()
    },
    {
      device: 'Switch-Core-01',
      oid: '1.3.6.1.2.1.1.3.0',
      name: 'sysUpTime',
      value: '328743928',
      lastUpdate: new Date().toISOString()
    },
    {
      device: 'Server-Web-01',
      oid: '1.3.6.1.2.1.25.1.1.0',
      name: 'hrSystemUptime',
      value: '1108974532',
      lastUpdate: new Date().toISOString()
    }
  ]);

  // Filtrage des équipements
  const filteredDevices = networkDevices.filter(device => {
    const matchesSearch = device.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          device.type.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          device.vendor.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          device.ip_address.includes(searchTerm);
                          
    const matchesTypeFilter = deviceTypeFilter === 'all' || device.type === deviceTypeFilter;
    const matchesStatusFilter = deviceStatusFilter === 'all' || device.status === deviceStatusFilter;
    
    return matchesSearch && matchesTypeFilter && matchesStatusFilter;
  });

  // Fonctions utilitaires
  const getDeviceIcon = (type) => {
    switch (type) {
      case 'router': return <ShareAltOutlined style={{ color: '#1890ff' }} />;
      case 'switch': return <DatabaseOutlined style={{ color: '#52c41a' }} />;
      case 'server': return <CloudServerOutlined style={{ color: '#faad14' }} />;
      case 'wireless': return <WifiOutlined style={{ color: '#13c2c2' }} />;
      case 'firewall': return <SafetyOutlined style={{ color: '#eb2f96' }} />;
      default: return <ShareAltOutlined style={{ color: '#999' }} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'online': return 'success';
      case 'warning': return 'warning';
      case 'offline': return 'error';
      default: return 'default';
    }
  };

  // Fonction de découverte automatique
  const handleNetworkDiscovery = async () => {
    setDiscoveryInProgress(true);
    setDiscoveryProgress(0);

    // Simulation du processus de découverte
    for (let i = 0; i <= 100; i += 10) {
      setDiscoveryProgress(i);
      await new Promise(resolve => setTimeout(resolve, 200));
    }

    message.success('Découverte réseau terminée - 2 nouveaux équipements trouvés');
    setDiscoveryInProgress(false);
  };

  // Gestion des équipements
  const handleEditDevice = (device) => {
    setEditingDevice(device);
    setIsModalVisible(true);
  };

  const handleDeleteDevice = (device) => {
    Modal.confirm({
      title: 'Confirmer la suppression',
      content: `Êtes-vous sûr de vouloir supprimer l'équipement ${device.name} ?`,
      okText: 'Supprimer',
      okType: 'danger',
      cancelText: 'Annuler',
      onOk() {
        message.success(`Équipement ${device.name} supprimé`);
      },
    });
  };

  const handleToggleDevice = (device) => {
    const newStatus = device.status === 'online' ? 'offline' : 'online';
    message.success(`Équipement ${device.name} ${newStatus === 'online' ? 'activé' : 'désactivé'}`);
  };

  // Colonnes du tableau des équipements
  const deviceColumns = [
    {
      title: 'Équipement',
      key: 'device',
      render: (_, record) => (
        <Space>
          {getDeviceIcon(record.type)}
          <div>
            <div style={{ fontWeight: 'bold' }}>{record.name}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {record.vendor} {record.model}
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: type => <Tag color="blue">{type}</Tag>
    },
    {
      title: 'Adresse IP',
      dataIndex: 'ip_address',
      key: 'ip_address'
    },
    {
      title: 'Localisation',
      dataIndex: 'location',
      key: 'location'
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      render: status => <Badge status={getStatusColor(status)} text={status} />
    },
    {
      title: 'Interfaces',
      key: 'interfaces',
      render: (_, record) => `${record.active_interfaces}/${record.interfaces}`
    },
    {
      title: 'Performance',
      key: 'performance',
      render: (_, record) => (
        <div>
          <div>CPU: {record.cpu_usage}%</div>
          <div>RAM: {record.memory_usage}%</div>
        </div>
      )
    },
    {
      title: 'SNMP',
      key: 'snmp',
      render: (_, record) => (
        record.snmp_enabled ? 
        <Tag color="green">Activé</Tag> : 
        <Tag color="red">Désactivé</Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Modifier">
            <Button 
              icon={<EditOutlined />} 
              size="small" 
              onClick={() => handleEditDevice(record)} 
            />
          </Tooltip>
          <Tooltip title={record.status === 'online' ? 'Désactiver' : 'Activer'}>
            <Button 
              icon={record.status === 'online' ? <StopOutlined /> : <CheckCircleOutlined />} 
              size="small" 
              onClick={() => handleToggleDevice(record)}
            />
          </Tooltip>
          <Tooltip title="Supprimer">
            <Button 
              icon={<DeleteOutlined />} 
              size="small" 
              danger 
              onClick={() => handleDeleteDevice(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // Colonnes du tableau SNMP
  const snmpColumns = [
    { title: 'Équipement', dataIndex: 'device', key: 'device' },
    { title: 'OID', dataIndex: 'oid', key: 'oid' },
    { title: 'Nom', dataIndex: 'name', key: 'name' },
    { title: 'Valeur', dataIndex: 'value', key: 'value' },
    { 
      title: 'Dernière mise à jour', 
      dataIndex: 'lastUpdate', 
      key: 'lastUpdate',
      render: (timestamp) => new Date(timestamp).toLocaleString()
    },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      
      <style jsx>{`
        .ant-tabs-content-holder {
          background: transparent;
        }
        .ant-table {
          background: transparent;
        }
        .ant-table-thead > tr > th {
          background: #374151;
          border-color: #4b5563;
          color: #d1d5db;
        }
        .ant-table-tbody > tr > td {
          background: transparent;
          border-color: #4b5563;
          color: #d1d5db;
        }
        .ant-table-tbody > tr:hover > td {
          background: #374151 !important;
        }
        .ant-card {
          background: #1f2937;
          border-color: #4b5563;
        }
        .ant-card-head {
          background: #374151;
          border-color: #4b5563;
          color: #d1d5db;
        }
        .ant-card-head-title {
          color: #d1d5db;
        }
        .ant-card-body {
          color: #d1d5db;
        }
        .ant-tabs-tab {
          color: #9ca3af !important;
        }
        .ant-tabs-tab-active {
          color: #3b82f6 !important;
        }
        .ant-tabs-ink-bar {
          background: #3b82f6;
        }
        .ant-input {
          background: #374151;
          border-color: #4b5563;
          color: #d1d5db;
        }
        .ant-select-selector {
          background: #374151 !important;
          border-color: #4b5563 !important;
          color: #d1d5db !important;
        }
        .ant-btn {
          border-color: #4b5563;
          color: #d1d5db;
        }
        .ant-btn:not(.ant-btn-primary):hover {
          border-color: #6b7280;
          color: #f3f4f6;
        }
        .ant-progress-text {
          color: #d1d5db !important;
        }
      `}</style>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab} className="custom-dark-tabs">
        <TabPane tab="Gestion des équipements" key="devices">
          <div className="mb-6 flex flex-wrap justify-between items-center gap-4">
            <div className="flex flex-wrap gap-4">
              <Input
                placeholder="Rechercher un équipement..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                prefix={<SearchOutlined />}
                style={{ width: 250 }}
              />
              
              <Select 
                defaultValue="all" 
                style={{ width: 150 }} 
                onChange={setDeviceTypeFilter}
              >
                <Option value="all">Tous les types</Option>
                <Option value="router">Routeurs</Option>
                <Option value="switch">Switches</Option>
                <Option value="server">Serveurs</Option>
                <Option value="wireless">Points d'accès</Option>
                <Option value="firewall">Firewalls</Option>
              </Select>
              
              <Select 
                defaultValue="all" 
                style={{ width: 150 }} 
                onChange={setDeviceStatusFilter}
              >
                <Option value="all">Tous les statuts</Option>
                <Option value="online">En ligne</Option>
                <Option value="warning">Attention</Option>
                <Option value="offline">Hors ligne</Option>
              </Select>
            </div>
            
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={() => {
                setEditingDevice(null);
                setIsModalVisible(true);
              }}
            >
              Ajouter équipement
            </Button>
          </div>

          <div className="mb-6 grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card size="small">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-blue-400">{networkStats.onlineDevices}/{networkStats.totalDevices}</div>
                  <div>Équipements en ligne</div>
                </div>
                <ShareAltOutlined style={{ fontSize: '24px', color: '#3b82f6' }} />
              </div>
            </Card>

            <Card size="small">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-green-400">{networkStats.activeInterfaces}/{networkStats.totalInterfaces}</div>
                  <div>Interfaces actives</div>
                </div>
                <DatabaseOutlined style={{ fontSize: '24px', color: '#10b981' }} />
              </div>
            </Card>

            <Card size="small">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-purple-400">{networkStats.snmpDevices}</div>
                  <div>Équipements SNMP</div>
                </div>
                <CheckCircleOutlined style={{ fontSize: '24px', color: '#8b5cf6' }} />
              </div>
            </Card>

            <Card size="small">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-orange-400">{networkStats.networkHealth}%</div>
                  <div>Santé du réseau</div>
                </div>
                <SafetyOutlined style={{ fontSize: '24px', color: '#f59e0b' }} />
              </div>
            </Card>
          </div>
          
          <Card className="bg-gray-800 border-none">
            <Spin spinning={isLoading}>
              <Table 
                columns={deviceColumns} 
                dataSource={filteredDevices} 
                pagination={{ pageSize: 10 }}
                rowKey="id"
                className="custom-dark-table"
              />
            </Spin>
          </Card>
        </TabPane>

        <TabPane tab="Topologie réseau" key="topology">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card title="Visualisation de la topologie" className="bg-gray-800 border-none">
                <div className="bg-gray-700/30 rounded-lg p-8 text-center min-h-96 flex flex-col items-center justify-center">
                  <ShareAltOutlined style={{ fontSize: '48px', color: '#3b82f6', marginBottom: '16px' }} />
                  <h4 className="text-lg font-medium mb-2">Carte Réseau Interactive</h4>
                  <p className="text-gray-400 mb-4">
                    Visualisation graphique de la topologie réseau avec {networkStats.totalDevices} équipements connectés
                  </p>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center">
                      <ShareAltOutlined style={{ fontSize: '24px', color: '#1890ff', marginBottom: '8px' }} />
                      <div>Routeurs</div>
                    </div>
                    <div className="text-center">
                      <DatabaseOutlined style={{ fontSize: '24px', color: '#52c41a', marginBottom: '8px' }} />
                      <div>Switches</div>
                    </div>
                    <div className="text-center">
                      <CloudServerOutlined style={{ fontSize: '24px', color: '#faad14', marginBottom: '8px' }} />
                      <div>Serveurs</div>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            <div className="space-y-6">
              <Card title="Distribution des équipements" className="bg-gray-800 border-none">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={topologyStats}
                      cx="50%"
                      cy="50%"
                      outerRadius={60}
                      dataKey="count"
                      label={({name, count}) => `${name}: ${count}`}
                    >
                      {topologyStats.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <RechartsTooltip />
                  </PieChart>
                </ResponsiveContainer>
              </Card>

              <Card title="Performance globale" className="bg-gray-800 border-none">
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <RechartsTooltip />
                    <Line type="monotone" dataKey="cpu" stroke="#3b82f6" strokeWidth={2} name="CPU %" />
                    <Line type="monotone" dataKey="memory" stroke="#10b981" strokeWidth={2} name="Mémoire %" />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </div>
          </div>
        </TabPane>

        <TabPane tab="Découverte réseau" key="discovery">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Card className="bg-gray-800 border-none mb-4">
                <div className="mb-4 flex justify-between items-center">
                  <h3 className="text-lg font-medium">Découverte automatique d'équipements</h3>
                  <Button 
                    type="primary"
                    icon={<SearchOutlined />}
                    onClick={handleNetworkDiscovery}
                    loading={discoveryInProgress}
                  >
                    {discoveryInProgress ? 'Découverte en cours...' : 'Lancer la découverte'}
                  </Button>
                </div>
                
                {discoveryInProgress && (
                  <div className="mb-4">
                    <div className="mb-2">Progression de la découverte</div>
                    <Progress percent={discoveryProgress} />
                  </div>
                )}
                
                <div className="bg-gray-700/30 rounded-lg p-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <SearchOutlined style={{ fontSize: '32px', color: '#3b82f6', marginBottom: '12px' }} />
                      <h4 className="font-medium mb-2">Scan IP</h4>
                      <p className="text-sm text-gray-400">Découverte par plage d'adresses IP</p>
                    </div>
                    <div className="text-center">
                      <DatabaseOutlined style={{ fontSize: '32px', color: '#10b981', marginBottom: '12px' }} />
                      <h4 className="font-medium mb-2">SNMP Discovery</h4>
                      <p className="text-sm text-gray-400">Identification via protocole SNMP</p>
                    </div>
                    <div className="text-center">
                      <WifiOutlined style={{ fontSize: '32px', color: '#8b5cf6', marginBottom: '12px' }} />
                      <h4 className="font-medium mb-2">ARP Scan</h4>
                      <p className="text-sm text-gray-400">Analyse de la table ARP</p>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            <div>
              <Card title="Paramètres de découverte" className="bg-gray-800 border-none">
                <Form layout="vertical">
                  <Form.Item label="Plage IP">
                    <Input placeholder="192.168.1.0/24" />
                  </Form.Item>
                  <Form.Item label="Ports à scanner">
                    <Input placeholder="22,23,80,443,161" />
                  </Form.Item>
                  <Form.Item label="Timeout (ms)">
                    <Input placeholder="5000" />
                  </Form.Item>
                  <Form.Item label="Communauté SNMP">
                    <Input placeholder="public" />
                  </Form.Item>
                  <Form.Item>
                    <Button type="primary" block>
                      Sauvegarder la configuration
                    </Button>
                  </Form.Item>
                </Form>
              </Card>

              <Card title="Dernières découvertes" className="bg-gray-800 border-none mt-4">
                <div className="text-center p-4">
                  <div className="text-2xl font-bold text-green-400 mb-2">
                    {networkStats.discoveredToday}
                  </div>
                  <div className="text-sm text-gray-400">Équipements découverts aujourd'hui</div>
                </div>
              </Card>
            </div>
          </div>
        </TabPane>

        <TabPane tab="Monitoring SNMP" key="snmp">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Configuration SNMP" className="bg-gray-800 border-none">
              <Form layout="vertical">
                <Form.Item label="Communauté par défaut">
                  <Input defaultValue="public" />
                </Form.Item>
                <Form.Item label="Port SNMP">
                  <Input defaultValue="161" />
                </Form.Item>
                <Form.Item label="Version SNMP">
                  <Select defaultValue="v2c" style={{ width: '100%' }}>
                    <Option value="v1">Version 1</Option>
                    <Option value="v2c">Version 2c</Option>
                    <Option value="v3">Version 3</Option>
                  </Select>
                </Form.Item>
                <Form.Item label="Intervalle de polling (secondes)">
                  <Input defaultValue="300" />
                </Form.Item>
                <Form.Item>
                  <Button type="primary">Sauvegarder la configuration</Button>
                </Form.Item>
              </Form>
            </Card>

            <Card title="Équipements SNMP actifs" className="bg-gray-800 border-none">
              <div className="space-y-3">
                {networkDevices.filter(device => device.snmp_enabled).map(device => (
                  <div key={device.id} className="flex items-center justify-between p-3 bg-gray-700/30 rounded">
                    <div className="flex items-center space-x-3">
                      {getDeviceIcon(device.type)}
                      <div>
                        <div className="font-medium">{device.name}</div>
                        <div className="text-sm text-gray-400">{device.ip_address}</div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Badge status="success" />
                      <span className="text-sm">Actif</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            <div className="lg:col-span-2">
              <Card title="Données SNMP en temps réel" className="bg-gray-800 border-none">
                <Table
                  columns={snmpColumns}
                  dataSource={snmpData}
                  pagination={{ pageSize: 10 }}
                  rowKey="oid"
                  className="custom-dark-table"
                />
              </Card>
            </div>
          </div>
        </TabPane>
      </Tabs>

      {/* Modal pour ajouter/modifier un équipement */}
      <Modal
        title={editingDevice ? `Modifier ${editingDevice.name}` : "Ajouter un nouvel équipement"}
        visible={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setIsModalVisible(false)}>
            Annuler
          </Button>,
          <Button key="save" type="primary" onClick={() => {
            message.success(editingDevice ? 'Équipement modifié avec succès' : 'Nouvel équipement ajouté');
            setIsModalVisible(false);
          }}>
            {editingDevice ? 'Modifier' : 'Ajouter'}
          </Button>
        ]}
      >
        <Form layout="vertical">
          <Form.Item label="Nom de l'équipement" required>
            <Input placeholder="Nom de l'équipement" />
          </Form.Item>
          <Form.Item label="Type" required>
            <Select placeholder="Sélectionner le type">
              <Option value="router">Routeur</Option>
              <Option value="switch">Switch</Option>
              <Option value="server">Serveur</Option>
              <Option value="wireless">Point d'accès</Option>
              <Option value="firewall">Firewall</Option>
            </Select>
          </Form.Item>
          <Form.Item label="Adresse IP" required>
            <Input placeholder="192.168.1.1" />
          </Form.Item>
          <Form.Item label="Localisation">
            <Input placeholder="Salle serveur A" />
          </Form.Item>
          <Form.Item label="Fabricant">
            <Input placeholder="Cisco, HP, Dell..." />
          </Form.Item>
          <Form.Item label="Modèle">
            <Input placeholder="Modèle de l'équipement" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default NetworkManagement;