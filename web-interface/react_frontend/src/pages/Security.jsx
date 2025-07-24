import React, { useState, useEffect } from 'react';
import { Table, Input, Button, Select, Badge, Card, Timeline, Tabs, Form, DatePicker, Space, Tag, Tooltip, Spin, message } from 'antd';
import { SearchOutlined, PlusOutlined, EditOutlined, DeleteOutlined, CheckCircleOutlined, StopOutlined, DownloadOutlined, ClockCircleOutlined, ExclamationCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import useSecurityUnified from '../hooks/useSecurityUnified';
// import MonacoEditor from 'react-monaco-editor'; // Temporairement désactivé

const { TabPane } = Tabs;
const { Option } = Select;
const { RangePicker } = DatePicker;

const Security = () => {
  // Hook Security unifié avec vraies APIs - PLUS DE DONNÉES MOCKÉES
  const {
    rules,
    alerts,
    vulnerabilities,
    statistics,
    summary,
    loading,
    error,
    createRule,
    updateRule,
    deleteRule,
    toggleRuleStatus,
    deployRules,
    refresh,
    clearError,
    operations
  } = useSecurityUnified();
  const [ruleTypeFilter, setRuleTypeFilter] = useState('all');
  const [ruleStatusFilter, setRuleStatusFilter] = useState('all');
  const [rulePriorityFilter, setRulePriorityFilter] = useState('all');
  const [editingRule, setEditingRule] = useState(null);
  const [editorContent, setEditorContent] = useState('');
  const [activeTab, setActiveTab] = useState('rules');
  
  // États locaux pour l'interface utilisateur
  const [searchIP, setSearchIP] = useState('');
  const [searchPort, setSearchPort] = useState('');
  const [searchProtocol, setSearchProtocol] = useState('all');
  const [searchSeverity, setSearchSeverity] = useState('all');
  const [correlationResults, setCorrelationResults] = useState([]);
  
  // ===== PLUS DE DONNÉES SIMULÉES - UTILISATION DES VRAIES APIs VIA LE HOOK =====
  // Afficher les erreurs API
  useEffect(() => {
    if (error) {
      message.error(`Erreur Security: ${error.message}`);
      // Auto-clear l'erreur après quelques secondes
      const timeout = setTimeout(() => {
        clearError();
      }, 5000);
      return () => clearTimeout(timeout);
    }
  }, [error, clearError]);

  // Log des données reçues pour debug
  useEffect(() => {
    console.log('[Security] Données reçues:', {
      rules: rules.length,
      alerts: alerts.length,
      vulnerabilities: vulnerabilities?.length || 0,
      summary
    });
  }, [rules, alerts, vulnerabilities, summary]);

  // ===== STATISTIQUES DEPUIS LES VRAIES APIs AU LIEU DES DONNÉES MOCKÉES =====
  const alertStats = {
    daily: statistics.dailyStats || [],
    attackTypes: statistics.attackTypes || [],
    detectionRate: statistics.detectionRate || 0,
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  // Filtrage des règles
  const filteredRules = rules.filter(rule => {
    return (ruleTypeFilter === 'all' || rule.type === ruleTypeFilter) &&
           (ruleStatusFilter === 'all' || 
            (ruleStatusFilter === 'active' && rule.status === 'active') ||
            (ruleStatusFilter === 'inactive' && rule.status === 'inactive')) &&
           (rulePriorityFilter === 'all' || rule.priority === rulePriorityFilter);
  });

  // ===== COLONNES DU TABLEAU ADAPTÉES AUX VRAIES DONNÉES API =====
  const ruleColumns = [
    { title: 'Nom', dataIndex: 'name', key: 'name', sorter: (a, b) => (a.name || '').localeCompare(b.name || '') },
    { 
      title: 'Type', 
      key: 'type',
      render: (_, record) => record.rule_type || record.type || 'N/A',
      sorter: (a, b) => (a.rule_type || a.type || '').localeCompare(b.rule_type || b.type || '')
    },
    { 
      title: 'Catégorie', 
      key: 'category',
      render: (_, record) => record.category || 'N/A',
      sorter: (a, b) => (a.category || '').localeCompare(b.category || '')
    },
    { 
      title: 'Action', 
      key: 'action',
      render: (_, record) => record.action || (record.is_active ? 'Autoriser' : 'Bloquer'),
      sorter: (a, b) => (a.action || '').localeCompare(b.action || '')
    },
    { 
      title: 'Description', 
      key: 'description',
      render: (_, record) => record.description || 'N/A'
    },
    { 
      title: 'Priorité', 
      key: 'priority',
      render: (_, record) => {
        const priority = record.priority || 'Moyenne';
        return (
          <Tag color={
            priority === 'Élevée' ? 'red' : 
            priority === 'Moyenne' ? 'orange' : 
            priority === 'Basse' ? 'green' : 'blue'
          }>
            {priority}
          </Tag>
        );
      },
      sorter: (a, b) => (a.priority || '').localeCompare(b.priority || '')
    },
    {
      title: 'Statut',
      key: 'status',
      render: (_, record) => {
        const isActive = record.is_active || record.status === 'active';
        return (
          <Badge 
            status={isActive ? 'success' : 'default'} 
            text={isActive ? 'Actif' : 'Inactif'} 
          />
        );
      },
      sorter: (a, b) => {
        const aStatus = a.is_active || a.status === 'active' ? 'active' : 'inactive';
        const bStatus = b.is_active || b.status === 'active' ? 'active' : 'inactive';
        return aStatus.localeCompare(bStatus);
      }
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
              onClick={() => handleEditRule(record)} 
            />
          </Tooltip>
          <Tooltip title={(record.is_active || record.status === 'active') ? 'Désactiver' : 'Activer'}>
            <Button 
              icon={(record.is_active || record.status === 'active') ? <StopOutlined /> : <CheckCircleOutlined />} 
              size="small" 
              onClick={() => handleToggleRuleStatus(record)}
              disabled={operations.updating}
            />
          </Tooltip>
          <Tooltip title="Supprimer">
            <Button 
              icon={<DeleteOutlined />} 
              size="small" 
              danger 
              onClick={() => handleDeleteRule(record)}
              disabled={operations.deleting}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // ===== FONCTIONS DE GESTION DES RÈGLES - VRAIES ACTIONS API =====
  const handleEditRule = (rule) => {
    setEditingRule(rule);
    setEditorContent(rule.content || rule.rule_content || '');
    setActiveTab('editor');
  };

  const handleToggleRuleStatus = async (rule) => {
    const newStatus = (rule.is_active || rule.status === 'active') ? false : true;
    const result = await toggleRuleStatus(rule.id, newStatus);
    
    if (result.success) {
      message.success(`Règle ${rule.name} ${newStatus ? 'activée' : 'désactivée'}`);
    } else {
      message.error(`Erreur: ${result.error}`);
    }
  };

  const handleDeleteRule = async (rule) => {
    const result = await deleteRule(rule.id);
    
    if (result.success) {
      message.success(`Règle ${rule.name} supprimée`);
    } else {
      message.error(`Erreur: ${result.error}`);
    }
  };

  const handleSaveRule = async () => {
    try {
      const ruleData = {
        name: editingRule ? editingRule.name : `Rule-${rules.length + 1}`,
        type: 'Suricata', // Par défaut
        rule_content: editorContent,
        is_active: editingRule ? (editingRule.is_active || editingRule.status === 'active') : false,
        category: editingRule?.category || 'Intrusion',
        priority: editingRule?.priority || 'Moyenne'
      };

      let result;
      if (editingRule) {
        // Mise à jour d'une règle existante
        result = await updateRule(editingRule.id, ruleData);
      } else {
        // Création d'une nouvelle règle
        result = await createRule(ruleData);
      }

      if (result.success) {
        message.success(`Règle ${ruleData.name} ${editingRule ? 'mise à jour' : 'créée'}`);
        setEditingRule(null);
        setEditorContent('');
        setActiveTab('rules');
      } else {
        message.error(`Erreur: ${result.error}`);
      }
    } catch (error) {
      message.error(`Erreur: ${error.message}`);
    }
  };

  // Fonction pour l'éditeur Monaco
  const editorDidMount = (editor) => {
    editor.focus();
  };

  const editorOptions = {
    selectOnLineNumbers: true,
    roundedSelection: false,
    readOnly: false,
    cursorStyle: 'line',
    automaticLayout: true,
    theme: 'vs-dark',
  };

  // Fonctions de recherche et corrélation
  const handleSearch = () => {
    let filtered = [...alerts];
    
    if (searchIP) {
      filtered = filtered.filter(alert => 
        alert.source.includes(searchIP) || alert.destination.includes(searchIP)
      );
    }
    
    if (searchPort) {
      filtered = filtered.filter(alert => 
        alert.port.toString().includes(searchPort)
      );
    }
    
    if (searchProtocol !== 'all') {
      filtered = filtered.filter(alert => alert.protocol === searchProtocol);
    }
    
    if (searchSeverity !== 'all') {
      filtered = filtered.filter(alert => alert.severity === searchSeverity);
    }
    
    setCorrelationResults(filtered);
    message.success(`${filtered.length} résultats trouvés`);
  };

  const handleResetSearch = () => {
    setSearchIP('');
    setSearchPort('');
    setSearchProtocol('all');
    setSearchSeverity('all');
    setCorrelationResults([]);
  };

  // Fonction pour obtenir l'icône de la timeline selon la gravité
  const getTimelineIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'high':
        return <WarningOutlined style={{ color: '#ff7a00' }} />;
      case 'medium':
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#52c41a' }} />;
    }
  };

  // Fonction pour obtenir la couleur de la timeline selon la gravité
  const getTimelineColor = (severity) => {
    switch (severity) {
      case 'critical': return 'red';
      case 'high': return 'orange';
      case 'medium': return 'yellow';
      default: return 'green';
    }
  };

  // Colonnes du tableau des alertes
  const alertColumns = [
    { title: 'Type', dataIndex: 'type', key: 'type' },
    { 
      title: 'Sévérité', 
      dataIndex: 'severity', 
      key: 'severity',
      render: severity => (
        <Tag color={
          severity === 'critical' ? 'red' : 
          severity === 'high' ? 'orange' : 
          severity === 'medium' ? 'yellow' : 'green'
        }>
          {severity.toUpperCase()}
        </Tag>
      )
    },
    { title: 'Date', dataIndex: 'date', key: 'date' },
    { title: 'Heure', dataIndex: 'time', key: 'time' },
    { title: 'Source', dataIndex: 'source', key: 'source' },
    { title: 'Destination', dataIndex: 'destination', key: 'destination' },
    { title: 'Détails', dataIndex: 'details', key: 'details' },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      
      <style jsx>{`
        .custom-timeline .ant-timeline-item-content {
          background: #374151;
          padding: 16px;
          border-radius: 8px;
          margin-left: 16px;
          border: 1px solid #4b5563;
        }
        .timeline-content h4 {
          margin: 0 0 8px 0;
        }
        .custom-timeline .ant-timeline-item-tail {
          border-left: 2px solid #4b5563;
        }
      `}</style>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab} className="custom-dark-tabs">
        <TabPane tab="Table des règles de sécurité" key="rules">
          <div className="mb-6 flex flex-wrap justify-between items-center gap-4">
            <div className="flex flex-wrap gap-4">
              <Select 
                defaultValue="all" 
                style={{ width: 150 }} 
                onChange={setRuleTypeFilter}
                className="bg-gray-800"
              >
                <Option value="all">Tous les types</Option>
                <Option value="Suricata">Suricata</Option>
                <Option value="Pare-feu">Pare-feu</Option>
                <Option value="Porticus">Porticus</Option>
              </Select>
              
              <Select 
                defaultValue="all" 
                style={{ width: 150 }} 
                onChange={setRuleStatusFilter}
                className="bg-gray-800"
              >
                <Option value="all">Tous les statuts</Option>
                <Option value="active">Actif</Option>
                <Option value="inactive">Inactif</Option>
              </Select>
              
              <Select 
                defaultValue="all" 
                style={{ width: 150 }} 
                onChange={setRulePriorityFilter}
                className="bg-gray-800"
              >
                <Option value="all">Toutes les priorités</Option>
                <Option value="Élevée">Élevée</Option>
                <Option value="Moyenne">Moyenne</Option>
                <Option value="Basse">Basse</Option>
              </Select>
            </div>
            
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={() => {
                setEditingRule(null);
                setEditorContent('');
                setActiveTab('editor');
              }}
            >
              Ajouter règle
            </Button>
          </div>
          
          <Card className="bg-gray-800 border-none">
            <Spin spinning={loading}>
              <Table 
                columns={ruleColumns} 
                dataSource={filteredRules} 
                pagination={{ pageSize: 5 }}
                className="custom-dark-table"
              />
            </Spin>
          </Card>
        </TabPane>
        
        <TabPane tab="Éditeur de règles" key="editor">
          <Card className="bg-gray-800 border-none mb-4">
            <div className="mb-4">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-medium">
                  {editingRule ? `Modifier la règle: ${editingRule.name}` : 'Nouvelle règle'}
                </h3>
                <Select 
                  defaultValue="suricata" 
                  style={{ width: 200 }} 
                  className="bg-gray-800"
                >
                  <Option value="suricata">Type: Suricata</Option>
                  <Option value="firewall">Type: Pare-feu</Option>
                  <Option value="custom">Type: Personnalisé</Option>
                </Select>
              </div>
              
              <div style={{ height: '400px', border: '1px solid #374151' }}>
                <textarea
                  className="w-full h-full bg-gray-900 text-white p-4 border-none outline-none font-mono text-sm"
                  value={editorContent}
                  onChange={(e) => setEditorContent(e.target.value)}
                  placeholder="Saisissez votre règle de sécurité ici..."
                  style={{ resize: 'none' }}
                />
              </div>
            </div>
            
            <div className="flex justify-end space-x-4">
              <Button onClick={() => setActiveTab('rules')}>Annuler</Button>
              <Button type="primary" onClick={handleSaveRule}>Enregistrer</Button>
            </div>
          </Card>
          
          <Card title="Modèles prédéfinis" className="bg-gray-800 border-none">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div 
                className="p-4 border border-gray-700 rounded-lg cursor-pointer hover:bg-gray-700"
                onClick={() => setEditorContent('alert tcp any any -> any 80 (msg: "HTTP Traffic"; content:"GET"; sid:1000001;)')}
              >
                <h4 className="font-medium mb-2">Détection de trafic HTTP</h4>
                <p className="text-gray-400 text-sm">Détecte le trafic HTTP entrant sur le port 80</p>
              </div>
              
              <div 
                className="p-4 border border-gray-700 rounded-lg cursor-pointer hover:bg-gray-700"
                onClick={() => setEditorContent('alert tcp any any -> any 22 (msg: "SSH Brute Force"; threshold: type threshold, track by_src, count 5, seconds 60; sid:1000002;)')}
              >
                <h4 className="font-medium mb-2">Détection de force brute SSH</h4>
                <p className="text-gray-400 text-sm">Détecte les tentatives répétées de connexion SSH</p>
              </div>
              
              <div 
                className="p-4 border border-gray-700 rounded-lg cursor-pointer hover:bg-gray-700"
                onClick={() => setEditorContent('iptables -A INPUT -s 192.168.1.0/24 -j DROP')}
              >
                <h4 className="font-medium mb-2">Blocage par IP</h4>
                <p className="text-gray-400 text-sm">Bloque une plage d'adresses IP spécifique</p>
              </div>
              
              <div 
                className="p-4 border border-gray-700 rounded-lg cursor-pointer hover:bg-gray-700"
                onClick={() => setEditorContent('alert tcp any any -> any any (msg: "Malware detected"; content:"malware.exe"; sid:1000004;)')}
              >
                <h4 className="font-medium mb-2">Détection de malware</h4>
                <p className="text-gray-400 text-sm">Détecte les fichiers malveillants connus</p>
              </div>
            </div>
          </Card>
        </TabPane>

        <TabPane tab="Timeline des alertes" key="timeline">
          <Card className="bg-gray-800 border-none mb-4">
            <div className="mb-4 flex justify-between items-center">
              <h3 className="text-lg font-medium">Chronologie des événements de sécurité</h3>
              <div className="flex gap-2">
                <Select 
                  defaultValue="all" 
                  style={{ width: 120 }} 
                  onChange={(value) => setSearchSeverity(value)}
                  className="bg-gray-800"
                >
                  <Option value="all">Toutes gravités</Option>
                  <Option value="critical">Critique</Option>
                  <Option value="high">Élevée</Option>
                  <Option value="medium">Moyenne</Option>
                  <Option value="low">Faible</Option>
                </Select>
                <Button icon={<DownloadOutlined />} type="primary">
                  Exporter timeline
                </Button>
              </div>
            </div>
            
            <Timeline mode="left" className="custom-timeline">
              {alerts
                .filter(alert => searchSeverity === 'all' || alert.severity === searchSeverity)
                .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
                .map(alert => (
                  <Timeline.Item
                    key={alert.key}
                    dot={getTimelineIcon(alert.severity)}
                    color={getTimelineColor(alert.severity)}
                  >
                    <div className="timeline-content">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="text-white font-medium">{alert.type}</h4>
                        <div className="flex items-center gap-2">
                          <Tag color={getTimelineColor(alert.severity)}>
                            {alert.severity.toUpperCase()}
                          </Tag>
                          <span className="text-gray-400">{alert.date} {alert.time}</span>
                        </div>
                      </div>
                      <p className="text-gray-300 mb-2">{alert.details}</p>
                      <div className="flex flex-wrap gap-4 text-sm text-gray-400">
                        <span><strong>Source:</strong> {alert.source}</span>
                        <span><strong>Destination:</strong> {alert.destination}</span>
                        <span><strong>Protocole:</strong> {alert.protocol}</span>
                        <span><strong>Port:</strong> {alert.port}</span>
                      </div>
                    </div>
                  </Timeline.Item>
                ))}
            </Timeline>
          </Card>
        </TabPane>

        <TabPane tab="Recherche et corrélation" key="search">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <Card title="Filtres de recherche" className="bg-gray-800 border-none">
                <Form layout="vertical">
                  <Form.Item label="Adresse IP">
                    <Input
                      placeholder="Ex: 192.168.1.100"
                      value={searchIP}
                      onChange={(e) => setSearchIP(e.target.value)}
                      prefix={<SearchOutlined />}
                    />
                  </Form.Item>

                  <Form.Item label="Port">
                    <Input
                      placeholder="Ex: 80, 443"
                      value={searchPort}
                      onChange={(e) => setSearchPort(e.target.value)}
                    />
                  </Form.Item>

                  <Form.Item label="Protocole">
                    <Select
                      value={searchProtocol}
                      onChange={setSearchProtocol}
                      style={{ width: '100%' }}
                    >
                      <Option value="all">Tous les protocoles</Option>
                      <Option value="TCP">TCP</Option>
                      <Option value="UDP">UDP</Option>
                      <Option value="HTTP">HTTP</Option>
                      <Option value="ICMP">ICMP</Option>
                    </Select>
                  </Form.Item>

                  <Form.Item label="Gravité">
                    <Select
                      value={searchSeverity}
                      onChange={setSearchSeverity}
                      style={{ width: '100%' }}
                    >
                      <Option value="all">Toutes les gravités</Option>
                      <Option value="critical">Critique</Option>
                      <Option value="high">Élevée</Option>
                      <Option value="medium">Moyenne</Option>
                      <Option value="low">Faible</Option>
                    </Select>
                  </Form.Item>

                  <div className="flex gap-2">
                    <Button type="primary" onClick={handleSearch} style={{ flex: 1 }}>
                      Rechercher
                    </Button>
                    <Button onClick={handleResetSearch}>
                      Réinitialiser
                    </Button>
                  </div>
                </Form>

                <div className="mt-4 p-4 bg-gray-700 rounded">
                  <h4 className="text-white mb-2">Corrélation automatique</h4>
                  <p className="text-gray-400 text-sm">
                    {correlationResults.length > 0 
                      ? `${correlationResults.length} événements corrélés trouvés`
                      : 'Aucune corrélation détectée'
                    }
                  </p>
                </div>
              </Card>
            </div>

            <div className="lg:col-span-2">
              <Card title="Résultats de la recherche" className="bg-gray-800 border-none">
                {correlationResults.length > 0 ? (
                  <Table
                    columns={[
                      { title: 'Date/Heure', dataIndex: 'timestamp', key: 'timestamp', render: (timestamp) => new Date(timestamp).toLocaleString() },
                      { title: 'Type', dataIndex: 'type', key: 'type' },
                      { 
                        title: 'Gravité', 
                        dataIndex: 'severity', 
                        key: 'severity',
                        render: severity => (
                          <Tag color={getTimelineColor(severity)}>
                            {severity.toUpperCase()}
                          </Tag>
                        )
                      },
                      { title: 'Source', dataIndex: 'source', key: 'source' },
                      { title: 'Destination', dataIndex: 'destination', key: 'destination' },
                      { title: 'Protocole', dataIndex: 'protocol', key: 'protocol' },
                      { title: 'Port', dataIndex: 'port', key: 'port' },
                      { title: 'Détails', dataIndex: 'details', key: 'details' },
                    ]}
                    dataSource={correlationResults}
                    pagination={{ pageSize: 10 }}
                    className="custom-dark-table"
                  />
                ) : (
                  <div className="text-center py-8 text-gray-400">
                    <SearchOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                    <p>Utilisez les filtres ci-contre pour rechercher dans les logs de sécurité</p>
                    <p className="text-sm">La corrélation automatique identifiera les patterns suspects</p>
                  </div>
                )}
              </Card>
            </div>
          </div>
        </TabPane>

        <TabPane tab="Alertes (tableau)" key="alerts">
          <Card className="bg-gray-800 border-none mb-4">
            <div className="mb-4 flex justify-between items-center">
              <h3 className="text-lg font-medium">Alertes de sécurité récentes</h3>
              <Button icon={<DownloadOutlined />} type="primary">
                Exporter les alertes
              </Button>
            </div>
            
            <Table 
              columns={alertColumns} 
              dataSource={alerts} 
              pagination={{ pageSize: 10 }}
              className="custom-dark-table"
            />
          </Card>
        </TabPane>

        <TabPane tab="Statistiques" key="stats">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card title="Alertes par jour" className="bg-gray-800 border-none">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={alertStats.daily}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="count" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Types d'attaques" className="bg-gray-800 border-none">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={alertStats.attackTypes}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {alertStats.attackTypes.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Taux de détection" className="bg-gray-800 border-none">
              <div className="text-center">
                <div className="text-4xl font-bold text-green-500 mb-2">
                  {alertStats.detectionRate}%
                </div>
                <p className="text-gray-400">Taux de détection des menaces</p>
              </div>
            </Card>

            <Card title="Évolution des menaces" className="bg-gray-800 border-none">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={alertStats.daily}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="count" stroke="#8884d8" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </div>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default Security;