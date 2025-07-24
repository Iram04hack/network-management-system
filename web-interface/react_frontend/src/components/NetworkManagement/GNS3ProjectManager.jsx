/**
 * GNS3 Project Manager - Interface de gestion des projets GNS3
 * Composant principal pour le module gns3_integration
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Row,
  Col,
  Divider,
  Alert,
  Badge,
  Tooltip,
  Progress,
  Tabs,
  Tree,
  Dropdown,
  message,
  Upload,
  Steps
} from 'antd';
import {
  ProjectOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  DeleteOutlined,
  PlusOutlined,
  DownloadOutlined,
  UploadOutlined,
  FolderOutlined,
  SettingOutlined,
  CopyOutlined,
  ReloadOutlined,
  NodeIndexOutlined,
  LinkOutlined,
  CloudServerOutlined,
  ExportOutlined,
  ImportOutlined
} from '@ant-design/icons';
import { useGNS3 } from '../../hooks/useGNS3';

const { Option } = Select;
const { confirm } = Modal;
const { TabPane } = Tabs;
const { Step } = Steps;

/**
 * Composant principal de gestion des projets GNS3
 */
const GNS3ProjectManager = () => {
  const {
    servers,
    projects,
    nodes,
    loading,
    error,
    fetchServers,
    fetchProjects,
    fetchProjectNodes,
    createProject,
    startProject,
    stopProject,
    deleteProject,
    cloneProject,
    startNode,
    stopNode,
    getProjectsByStatus,
    getRunningNodes,
    getGNS3Stats,
    clearError
  } = useGNS3();

  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' | 'import' | 'clone'
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedServer, setSelectedServer] = useState(null);
  const [activeTab, setActiveTab] = useState('projects');
  const [form] = Form.useForm();

  // Charger les données au montage
  useEffect(() => {
    loadAllData();
  }, []);

  // Charger toutes les données
  const loadAllData = async () => {
    try {
      await fetchServers();
      await fetchProjects();
    } catch (error) {
      console.error('Erreur chargement données GNS3:', error);
    }
  };

  // Charger les nœuds d'un projet
  const loadProjectNodes = async (projectId) => {
    try {
      await fetchProjectNodes(projectId);
      setSelectedProject(projectId);
    } catch (error) {
      console.error('Erreur chargement nœuds:', error);
    }
  };

  // Actions sur les projets
  const handleProjectAction = async (action, projectId) => {
    try {
      switch (action) {
        case 'start':
          await startProject(projectId);
          message.success('Projet démarré');
          break;
        case 'stop':
          await stopProject(projectId);
          message.success('Projet arrêté');
          break;
        case 'delete':
          confirm({
            title: 'Supprimer le projet',
            content: 'Êtes-vous sûr de vouloir supprimer ce projet ?',
            okText: 'Supprimer',
            okType: 'danger',
            cancelText: 'Annuler',
            onOk: async () => {
              await deleteProject(projectId);
              message.success('Projet supprimé');
            }
          });
          break;
        case 'clone':
          showModal('clone', projectId);
          break;
        default:
          break;
      }
      await fetchProjects();
    } catch (error) {
      message.error(`Erreur ${action}: ${error.message}`);
    }
  };

  // Actions sur les nœuds
  const handleNodeAction = async (action, nodeId) => {
    try {
      switch (action) {
        case 'start':
          await startNode(nodeId);
          message.success('Nœud démarré');
          break;
        case 'stop':
          await stopNode(nodeId);
          message.success('Nœud arrêté');
          break;
        default:
          break;
      }
      if (selectedProject) {
        await loadProjectNodes(selectedProject);
      }
    } catch (error) {
      message.error(`Erreur ${action}: ${error.message}`);
    }
  };

  // Ouvrir modal
  const showModal = (mode, projectId = null) => {
    setModalMode(mode);
    setIsModalVisible(true);
    
    if (mode === 'clone' && projectId) {
      const project = projects.find(p => p.id === projectId);
      if (project) {
        form.setFieldsValue({
          name: `${project.name} - Copie`,
          original_project_id: projectId
        });
      }
    } else {
      form.resetFields();
    }
  };

  // Fermer modal
  const handleModalCancel = () => {
    setIsModalVisible(false);
    form.resetFields();
  };

  // Sauvegarder projet
  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (modalMode === 'create') {
        await createProject(values);
        message.success('Projet créé avec succès');
      } else if (modalMode === 'clone') {
        await cloneProject(values.original_project_id, values);
        message.success('Projet cloné avec succès');
      }
      
      setIsModalVisible(false);
      form.resetFields();
      await fetchProjects();
    } catch (error) {
      message.error(`Erreur: ${error.message}`);
    }
  };

  // Configuration des colonnes pour les projets
  const projectColumns = [
    {
      title: 'Nom',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (text, record) => (
        <Space>
          <ProjectOutlined />
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: 'Serveur',
      dataIndex: 'server_id',
      key: 'server_id',
      width: 120,
      render: (serverId) => {
        const server = servers.find(s => s.id === serverId);
        return server ? server.name : 'Inconnu';
      }
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const config = {
          opened: { color: 'success', text: 'Ouvert' },
          closed: { color: 'default', text: 'Fermé' }
        };
        
        const statusConfig = config[status] || { color: 'warning', text: 'Inconnu' };
        
        return <Tag color={statusConfig.color}>{statusConfig.text}</Tag>;
      }
    },
    {
      title: 'Nœuds',
      key: 'nodes_count',
      width: 80,
      render: (_, record) => (
        <Badge 
          count={record.nodes_count || 0} 
          style={{ backgroundColor: '#52c41a' }}
        />
      )
    },
    {
      title: 'Créé',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => date ? new Date(date).toLocaleDateString('fr-FR') : '-'
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 250,
      render: (_, record) => (
        <Space>
          {record.status === 'closed' ? (
            <Tooltip title="Ouvrir le projet">
              <Button
                type="primary"
                size="small"
                icon={<PlayCircleOutlined />}
                onClick={() => handleProjectAction('start', record.id)}
                loading={loading.projects}
              />
            </Tooltip>
          ) : (
            <Tooltip title="Fermer le projet">
              <Button
                size="small"
                icon={<PauseCircleOutlined />}
                onClick={() => handleProjectAction('stop', record.id)}
                loading={loading.projects}
              />
            </Tooltip>
          )}
          
          <Tooltip title="Voir les nœuds">
            <Button
              size="small"
              icon={<NodeIndexOutlined />}
              onClick={() => loadProjectNodes(record.id)}
            />
          </Tooltip>
          
          <Dropdown
            menu={{
              items: [
                {
                  key: 'clone',
                  label: 'Cloner',
                  icon: <CopyOutlined />,
                  onClick: () => handleProjectAction('clone', record.id)
                },
                {
                  key: 'export',
                  label: 'Exporter',
                  icon: <ExportOutlined />
                },
                {
                  type: 'divider'
                },
                {
                  key: 'delete',
                  label: 'Supprimer',
                  icon: <DeleteOutlined />,
                  danger: true,
                  onClick: () => handleProjectAction('delete', record.id)
                }
              ]
            }}
            trigger={['click']}
          >
            <Button size="small" icon={<SettingOutlined />} />
          </Dropdown>
        </Space>
      )
    }
  ];

  // Configuration des colonnes pour les nœuds
  const nodeColumns = [
    {
      title: 'Nom',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <CloudServerOutlined />
          <span>{text}</span>
        </Space>
      )
    },
    {
      title: 'Type',
      dataIndex: 'node_type',
      key: 'node_type',
      render: (type) => <Tag color="blue">{type}</Tag>
    },
    {
      title: 'Statut',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const config = {
          started: { color: 'success', text: 'Démarré' },
          stopped: { color: 'default', text: 'Arrêté' },
          suspended: { color: 'warning', text: 'Suspendu' }
        };
        
        const statusConfig = config[status] || { color: 'warning', text: 'Inconnu' };
        
        return <Tag color={statusConfig.color}>{statusConfig.text}</Tag>;
      }
    },
    {
      title: 'Console',
      dataIndex: 'console',
      key: 'console',
      render: (console) => console || '-'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {record.status !== 'started' ? (
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleNodeAction('start', record.id)}
              loading={loading.nodes}
            >
              Démarrer
            </Button>
          ) : (
            <Button
              size="small"
              icon={<StopOutlined />}
              onClick={() => handleNodeAction('stop', record.id)}
              loading={loading.nodes}
            >
              Arrêter
            </Button>
          )}
        </Space>
      )
    }
  ];

  // Statistiques GNS3
  const stats = getGNS3Stats();
  const runningProjects = getProjectsByStatus('opened');
  const runningNodes = getRunningNodes();

  return (
    <div style={{ padding: '24px' }}>
      {/* Statistiques en en-tête */}
      <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <CloudServerOutlined 
                style={{ fontSize: '24px', color: '#1890ff', marginBottom: '8px' }} 
              />
              <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                {stats.totalServers}
              </div>
              <div style={{ color: '#666' }}>Serveurs GNS3</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <ProjectOutlined 
                style={{ fontSize: '24px', color: '#52c41a', marginBottom: '8px' }} 
              />
              <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                {stats.totalProjects}
              </div>
              <div style={{ color: '#666' }}>Projets Totaux</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <PlayCircleOutlined 
                style={{ fontSize: '24px', color: '#fa8c16', marginBottom: '8px' }} 
              />
              <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                {runningProjects.length}
              </div>
              <div style={{ color: '#666' }}>Projets Actifs</div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <NodeIndexOutlined 
                style={{ fontSize: '24px', color: '#722ed1', marginBottom: '8px' }} 
              />
              <div style={{ fontSize: '20px', fontWeight: 'bold' }}>
                {runningNodes.length}
              </div>
              <div style={{ color: '#666' }}>Nœuds Actifs</div>
            </div>
          </Card>
        </Col>
      </Row>

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

      {/* Interface principale */}
      <Card
        title={
          <Space>
            <ProjectOutlined />
            Gestionnaire GNS3
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => showModal('create')}
            >
              Nouveau Projet
            </Button>
            <Button
              icon={<ImportOutlined />}
              onClick={() => showModal('import')}
            >
              Importer
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadAllData}
              loading={loading.servers || loading.projects}
            >
              Actualiser
            </Button>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane 
            tab={
              <Space>
                <ProjectOutlined />
                Projets ({projects.length})
              </Space>
            } 
            key="projects"
          >
            <Table
              columns={projectColumns}
              dataSource={projects}
              rowKey="id"
              loading={loading.projects}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} sur ${total} projets`
              }}
              scroll={{ x: 1000 }}
            />
          </TabPane>

          <TabPane 
            tab={
              <Space>
                <NodeIndexOutlined />
                Nœuds ({nodes.length})
              </Space>
            } 
            key="nodes"
          >
            {selectedProject ? (
              <Table
                columns={nodeColumns}
                dataSource={nodes}
                rowKey="id"
                loading={loading.nodes}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true
                }}
              />
            ) : (
              <div style={{ 
                textAlign: 'center', 
                padding: '40px',
                color: '#999'
              }}>
                <NodeIndexOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                <p>Sélectionnez un projet pour voir ses nœuds</p>
              </div>
            )}
          </TabPane>

          <TabPane 
            tab={
              <Space>
                <CloudServerOutlined />
                Serveurs ({servers.length})
              </Space>
            } 
            key="servers"
          >
            <Table
              columns={[
                {
                  title: 'Nom',
                  dataIndex: 'name',
                  key: 'name'
                },
                {
                  title: 'Hôte',
                  dataIndex: 'host',
                  key: 'host'
                },
                {
                  title: 'Port',
                  dataIndex: 'port',
                  key: 'port'
                },
                {
                  title: 'Statut',
                  dataIndex: 'is_active',
                  key: 'is_active',
                  render: (isActive) => (
                    <Badge 
                      status={isActive ? 'success' : 'error'}
                      text={isActive ? 'Actif' : 'Inactif'}
                    />
                  )
                }
              ]}
              dataSource={servers}
              rowKey="id"
              loading={loading.servers}
              pagination={false}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* Modal de création/clonage */}
      <Modal
        title={
          modalMode === 'create' ? 'Nouveau Projet GNS3' :
          modalMode === 'clone' ? 'Cloner Projet' : 'Importer Projet'
        }
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={600}
        confirmLoading={loading.projects}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            auto_start: false,
            auto_close: true
          }}
        >
          <Form.Item
            label="Nom du projet"
            name="name"
            rules={[{ required: true, message: 'Le nom est obligatoire' }]}
          >
            <Input placeholder="Nom du projet" />
          </Form.Item>

          <Form.Item
            label="Serveur GNS3"
            name="server"
            rules={[{ required: true, message: 'Le serveur est obligatoire' }]}
          >
            <Select placeholder="Sélectionner un serveur">
              {servers.map(server => (
                <Option key={server.id} value={server.id}>
                  {server.name} ({server.host}:{server.port})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            label="Chemin"
            name="path"
          >
            <Input placeholder="/opt/gns3/projects/mon-projet" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Démarrage automatique"
                name="auto_start"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Fermeture automatique"
                name="auto_close"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          {modalMode === 'clone' && (
            <Form.Item name="original_project_id" hidden>
              <Input />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default GNS3ProjectManager;