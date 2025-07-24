import React, { useState, useEffect } from 'react';
import { 
  Table, Input, Button, Select, Card, Form, Checkbox, DatePicker, Radio, Upload, Tabs, Badge, Space, Tag, 
  Spin, message, Modal, Divider, Switch, TimePicker, Tooltip, Row, Col, Progress, Alert, List, Avatar 
} from 'antd';
import { 
  SearchOutlined, PlusOutlined, DownloadOutlined, DeleteOutlined, ReloadOutlined, MailOutlined, LinkOutlined, 
  FileTextOutlined, FilePdfOutlined, FileExcelOutlined, FileImageOutlined, UploadOutlined, EyeOutlined, 
  SettingOutlined, ClockCircleOutlined, CalendarOutlined, UserOutlined, EditOutlined, SaveOutlined,
  LineChartOutlined, BarChartOutlined, PieChartOutlined, PrinterOutlined, ShareAltOutlined, HistoryOutlined,
  PlayCircleOutlined, CopyOutlined
} from '@ant-design/icons';

const { TabPane } = Tabs;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TextArea } = Input;

const Reports = () => {
  // États principaux
  const [reports, setReports] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [activeTab, setActiveTab] = useState('generator');
  const [previewVisible, setPreviewVisible] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [modalType, setModalType] = useState('');
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  
  const [form] = Form.useForm();
  const [scheduleForm] = Form.useForm();
  
  // Configuration par défaut du générateur de rapport
  const [reportConfig, setReportConfig] = useState({
    name: 'Nouveau rapport',
    period: 'week',
    customRange: null,
    includeTraffic: true,
    includeAlerts: true,
    includeInventory: false,
    includePerformance: true,
    includeSecurity: false,
    graphType: 'line',
    colorTheme: 'blue',
    format: 'pdf',
    logo: null,
    title: 'Rapport d\'analyse réseau',
    subtitle: 'Généré automatiquement',
    description: 'Ce rapport présente une analyse détaillée des performances et de la sécurité du réseau.',
    recipients: [],
    autoSend: false
  });
  
  // Données simulées
  useEffect(() => {
    setTimeout(() => {
      setReports([
        { 
          id: '1', 
          name: 'Rapport Mensuel Juin', 
          createdAt: '2024-06-10 11:30', 
          createdBy: 'Jean Dupont', 
          status: 'completed', 
          size: '2.4 MB',
          type: 'pdf',
          period: 'Mai 2024',
          sections: ['Trafic', 'Alertes', 'Équipements', 'Performance'],
          downloads: 15,
          shared: true
        },
        { 
          id: '2', 
          name: 'Rapport Hebdomadaire', 
          createdAt: '2024-06-09 16:45', 
          createdBy: 'Sophie Bernard', 
          status: 'error', 
          size: '0 KB',
          type: 'pdf',
          period: 'Semaine 23',
          sections: ['Trafic', 'Alertes'],
          downloads: 0,
          shared: false,
          error: 'Données insuffisantes pour la période sélectionnée'
        },
        { 
          id: '3', 
          name: 'Rapport Sécurité Trimestriel', 
          createdAt: '2024-06-08 09:20', 
          createdBy: 'Marc Durand', 
          status: 'completed', 
          size: '1.8 MB',
          type: 'pdf',
          period: 'Q2 2024',
          sections: ['Alertes', 'Sécurité'],
          downloads: 8,
          shared: true
        },
        { 
          id: '4', 
          name: 'Inventaire Équipements', 
          createdAt: '2024-06-05 14:15', 
          createdBy: 'Sophie Bernard', 
          status: 'completed', 
          size: '3.2 MB',
          type: 'xlsx',
          period: 'Q2 2024',
          sections: ['Équipements'],
          downloads: 23,
          shared: false
        },
        { 
          id: '5', 
          name: 'Rapport Performance', 
          createdAt: '2024-06-01 10:30', 
          createdBy: 'Jean Dupont', 
          status: 'generating', 
          size: '0 KB',
          type: 'pdf',
          period: 'Mai 2024',
          sections: ['Trafic', 'Performance'],
          downloads: 0,
          shared: false
        },
      ]);
      
      setTemplates([
        { 
          id: '1', 
          name: 'Rapport mensuel standard', 
          sections: ['Trafic', 'Alertes', 'Équipements', 'Performance'], 
          graphType: 'line',
          colorTheme: 'blue',
          format: 'pdf',
          description: 'Template complet pour rapport mensuel',
          usageCount: 12,
          lastUsed: '2024-06-10'
        },
        { 
          id: '2', 
          name: 'Rapport sécurité', 
          sections: ['Alertes', 'Sécurité'], 
          graphType: 'bar',
          colorTheme: 'red',
          format: 'pdf',
          description: 'Focus sur les aspects sécurité',
          usageCount: 6,
          lastUsed: '2024-06-08'
        },
        { 
          id: '3', 
          name: 'Inventaire matériel', 
          sections: ['Équipements'], 
          graphType: 'pie',
          colorTheme: 'green',
          format: 'xlsx',
          description: 'Export détaillé des équipements',
          usageCount: 4,
          lastUsed: '2024-06-05'
        },
      ]);
      
      setSchedules([
        { 
          id: '1', 
          name: 'Rapport mensuel automatique', 
          frequency: 'monthly', 
          day: '1', 
          time: '08:00', 
          recipients: ['admin@example.com', 'manager@example.com'], 
          status: 'active', 
          lastRun: '2024-06-01 08:00', 
          nextRun: '2024-07-01 08:00',
          template: 'Rapport mensuel standard',
          successRate: 98
        },
        { 
          id: '2', 
          name: 'Rapport hebdomadaire équipe', 
          frequency: 'weekly', 
          day: 'Monday', 
          time: '07:30', 
          recipients: ['team@example.com'], 
          status: 'active', 
          lastRun: '2024-06-10 07:30', 
          nextRun: '2024-06-17 07:30',
          template: 'Rapport mensuel standard',
          successRate: 95
        },
        { 
          id: '3', 
          name: 'Alerte sécurité quotidienne', 
          frequency: 'daily', 
          day: 'Every day', 
          time: '23:00', 
          recipients: ['security@example.com'], 
          status: 'inactive', 
          lastRun: '2024-06-05 23:00', 
          nextRun: 'N/A',
          template: 'Rapport sécurité',
          successRate: 87
        },
      ]);
      
      setLoading(false);
    }, 1000);
  }, []);

  // Filtrage des rapports
  const filteredReports = reports.filter(report => 
    report.name.toLowerCase().includes(searchText.toLowerCase()) ||
    report.createdBy.toLowerCase().includes(searchText.toLowerCase())
  );

  // Colonnes du tableau des rapports
  const reportColumns = [
    { 
      title: 'Nom', 
      dataIndex: 'name', 
      key: 'name', 
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text, record) => (
        <div>
          <a onClick={() => handlePreviewReport(record)}>{text}</a>
          {record.shared && <LinkOutlined className="ml-2 text-blue-500" title="Partagé" />}
        </div>
      )
    },
    { 
      title: 'Type', 
      dataIndex: 'type', 
      key: 'type',
      render: (type) => (
        <div className="flex items-center">
          {type === 'pdf' && <FilePdfOutlined className="mr-1 text-red-500" />}
          {type === 'xlsx' && <FileExcelOutlined className="mr-1 text-green-500" />}
          {type === 'csv' && <FileTextOutlined className="mr-1 text-blue-500" />}
          <Tag color={type === 'pdf' ? 'red' : type === 'xlsx' ? 'green' : 'blue'}>
            {type.toUpperCase()}
          </Tag>
        </div>
      )
    },
    { 
      title: 'Statut', 
      dataIndex: 'status', 
      key: 'status',
      render: (status, record) => {
        const statusConfig = {
          completed: { status: 'success', text: 'Complété', color: 'green' },
          error: { status: 'error', text: 'Erreur', color: 'red' },
          generating: { status: 'processing', text: 'En cours', color: 'blue' }
        };
        
        const config = statusConfig[status] || statusConfig.completed;
        
        return (
          <div>
            <Badge status={config.status} text={config.text} />
            {status === 'error' && record.error && (
              <div className="text-xs text-red-500 mt-1">{record.error}</div>
            )}
          </div>
        );
      },
      sorter: (a, b) => a.status.localeCompare(b.status)
    },
    { 
      title: 'Date de création', 
      dataIndex: 'createdAt', 
      key: 'createdAt',
      sorter: (a, b) => new Date(a.createdAt) - new Date(b.createdAt),
      render: date => (
        <div>
          <div>{date.split(' ')[0]}</div>
          <div className="text-xs text-gray-500">{date.split(' ')[1]}</div>
        </div>
      )
    },
    { 
      title: 'Créé par', 
      dataIndex: 'createdBy', 
      key: 'createdBy',
      sorter: (a, b) => a.createdBy.localeCompare(b.createdBy),
      render: (creator) => (
        <div className="flex items-center">
          <Avatar size="small" className="mr-2">{creator.split(' ').map(n => n[0]).join('')}</Avatar>
          <span>{creator}</span>
        </div>
      )
    },
    { 
      title: 'Taille', 
      dataIndex: 'size', 
      key: 'size',
      sorter: (a, b) => {
        const sizeA = parseFloat(a.size);
        const sizeB = parseFloat(b.size);
        return sizeA - sizeB;
      },
      render: (size, record) => (
        <div>
          <div>{size}</div>
          {record.downloads > 0 && (
            <div className="text-xs text-gray-500">{record.downloads} téléchargements</div>
          )}
        </div>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Aperçu">
            <Button 
              icon={<EyeOutlined />} 
              size="small" 
              onClick={() => handlePreviewReport(record)} 
            />
          </Tooltip>
          <Tooltip title="Télécharger">
            <Button 
              icon={<DownloadOutlined />} 
              size="small" 
              disabled={record.status !== 'completed'}
              onClick={() => handleDownloadReport(record)} 
            />
          </Tooltip>
          <Tooltip title="Partager">
            <Button 
              icon={<ShareAltOutlined />} 
              size="small" 
              disabled={record.status !== 'completed'}
              onClick={() => handleShareReport(record)} 
            />
          </Tooltip>
          <Tooltip title="Régénérer">
            <Button 
              icon={<ReloadOutlined />} 
              size="small" 
              onClick={() => handleRegenerateReport(record)} 
            />
          </Tooltip>
          <Tooltip title="Supprimer">
            <Button 
              icon={<DeleteOutlined />} 
              size="small" 
              danger 
              onClick={() => handleDeleteReport(record)} 
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // Colonnes du tableau des planifications
  const scheduleColumns = [
    { 
      title: 'Nom', 
      dataIndex: 'name', 
      key: 'name',
      render: (text, record) => (
        <div>
          <div className="font-medium">{text}</div>
          <div className="text-xs text-gray-500">Template: {record.template}</div>
        </div>
      )
    },
    { 
      title: 'Fréquence', 
      dataIndex: 'frequency', 
      key: 'frequency',
      render: (frequency, record) => (
        <div>
          <Tag color={
            frequency === 'daily' ? 'blue' : 
            frequency === 'weekly' ? 'green' : 
            frequency === 'monthly' ? 'purple' : 'orange'
          }>
            {frequency === 'daily' ? 'Quotidien' : 
             frequency === 'weekly' ? 'Hebdomadaire' : 
             frequency === 'monthly' ? 'Mensuel' : 'Personnalisé'}
          </Tag>
          <div className="text-xs text-gray-500 mt-1">
            {record.day} à {record.time}
          </div>
        </div>
      )
    },
    { 
      title: 'Destinataires', 
      dataIndex: 'recipients', 
      key: 'recipients',
      render: recipients => (
        <div>
          {recipients.slice(0, 2).map((email, index) => (
            <Tag key={index} className="mb-1">{email}</Tag>
          ))}
          {recipients.length > 2 && (
            <Tag>+{recipients.length - 2} autres</Tag>
          )}
        </div>
      )
    },
    { 
      title: 'Statut & Performance', 
      key: 'status_performance',
      render: (_, record) => (
        <div>
          <div className="flex items-center mb-1">
            <Switch 
              checked={record.status === 'active'} 
              onChange={(checked) => handleToggleScheduleStatus(record, checked)} 
              size="small"
            />
            <span className="ml-2 text-sm">
              {record.status === 'active' ? 'Actif' : 'Inactif'}
            </span>
          </div>
          <Progress 
            percent={record.successRate} 
            size="small" 
            status={record.successRate >= 95 ? 'success' : record.successRate >= 80 ? 'normal' : 'exception'}
          />
          <div className="text-xs text-gray-500">{record.successRate}% de succès</div>
        </div>
      )
    },
    { 
      title: 'Prochaine exécution', 
      dataIndex: 'nextRun', 
      key: 'nextRun',
      render: (nextRun, record) => (
        <div>
          <div className="text-sm">{nextRun}</div>
          <div className="text-xs text-gray-500">
            Dernière: {record.lastRun}
          </div>
        </div>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="Exécuter maintenant">
            <Button 
              icon={<PlayCircleOutlined />} 
              size="small" 
              disabled={record.status !== 'active'}
              onClick={() => handleRunScheduleNow(record)} 
            />
          </Tooltip>
          <Tooltip title="Modifier">
            <Button 
              icon={<EditOutlined />} 
              size="small" 
              onClick={() => handleEditSchedule(record)} 
            />
          </Tooltip>
          <Tooltip title="Historique">
            <Button 
              icon={<HistoryOutlined />} 
              size="small" 
              onClick={() => handleViewScheduleHistory(record)} 
            />
          </Tooltip>
          <Tooltip title="Supprimer">
            <Button 
              icon={<DeleteOutlined />} 
              size="small" 
              danger 
              onClick={() => handleDeleteSchedule(record)} 
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // Fonctions de gestion des rapports
  const handlePreviewReport = (report) => {
    setSelectedReport(report);
    setPreviewVisible(true);
  };

  const handleDownloadReport = (report) => {
    message.success(`Téléchargement du rapport "${report.name}" en cours...`);
    
    // Simulation du téléchargement
    const link = document.createElement('a');
    link.href = '#';
    link.download = `${report.name}.${report.type}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Mettre à jour le compteur de téléchargements
    setReports(reports.map(r => 
      r.id === report.id ? { ...r, downloads: r.downloads + 1 } : r
    ));
  };

  const handleShareReport = (report) => {
    setModalType('share');
    setSelectedReport(report);
    setIsModalVisible(true);
  };

  const handleRegenerateReport = (report) => {
    setReports(reports.map(r => 
      r.id === report.id ? { ...r, status: 'generating' } : r
    ));
    
    message.loading(`Régénération du rapport "${report.name}" en cours...`);
    
    // Simulation de régénération avec progress bar
    let progressValue = 0;
    const progressInterval = setInterval(() => {
      progressValue += Math.random() * 20;
      if (progressValue >= 100) {
        clearInterval(progressInterval);
        setReports(reports.map(r => 
          r.id === report.id 
            ? { ...r, status: 'completed', createdAt: new Date().toLocaleString(), size: '2.1 MB' } 
            : r
        ));
        message.success(`Rapport "${report.name}" régénéré avec succès`);
      }
    }, 500);
  };

  const handleDeleteReport = (report) => {
    Modal.confirm({
      title: 'Êtes-vous sûr de vouloir supprimer ce rapport?',
      content: `Cette action supprimera définitivement le rapport "${report.name}".`,
      okText: 'Supprimer',
      okType: 'danger',
      cancelText: 'Annuler',
      onOk() {
        setReports(reports.filter(r => r.id !== report.id));
        message.success(`Rapport "${report.name}" supprimé`);
      }
    });
  };

  // Fonctions pour les planifications
  const handleAddSchedule = () => {
    setModalType('schedule');
    scheduleForm.resetFields();
    setIsModalVisible(true);
  };

  const handleEditSchedule = (schedule) => {
    setModalType('editSchedule');
    setSelectedReport(schedule);
    scheduleForm.setFieldsValue({
      name: schedule.name,
      frequency: schedule.frequency,
      day: schedule.day,
      time: schedule.time,
      recipients: schedule.recipients.join(', '),
      status: schedule.status === 'active'
    });
    setIsModalVisible(true);
  };

  const handleRunScheduleNow = (schedule) => {
    message.loading(`Exécution de la planification "${schedule.name}" en cours...`);
    
    setTimeout(() => {
      message.success(`Planification "${schedule.name}" exécutée avec succès`);
      
      // Ajouter un nouveau rapport généré
      const newReport = {
        id: String(reports.length + 1),
        name: `${schedule.name} - ${new Date().toLocaleDateString()}`,
        createdAt: new Date().toLocaleString(),
        createdBy: 'Système automatique',
        status: 'completed',
        size: '1.9 MB',
        type: 'pdf',
        period: 'Automatique',
        sections: ['Trafic', 'Alertes'],
        downloads: 0,
        shared: true
      };
      
      setReports([newReport, ...reports]);
    }, 2000);
  };

  const handleViewScheduleHistory = (schedule) => {
    setModalType('history');
    setSelectedReport(schedule);
    setIsModalVisible(true);
  };

  const handleSaveSchedule = () => {
    scheduleForm.validateFields().then(values => {
      const scheduleData = {
        name: values.name,
        frequency: values.frequency,
        day: values.day || 'Every day',
        time: values.time,
        recipients: values.recipients.split(',').map(email => email.trim()),
        status: values.status ? 'active' : 'inactive',
        template: values.template || 'Rapport mensuel standard',
        successRate: 100
      };
      
      if (modalType === 'editSchedule') {
        setSchedules(schedules.map(s => 
          s.id === selectedReport.id 
            ? { ...s, ...scheduleData, nextRun: calculateNextRun(values.frequency, values.day, values.time) }
            : s
        ));
        message.success(`Planification "${values.name}" modifiée avec succès`);
      } else {
        const newSchedule = {
          id: String(schedules.length + 1),
          ...scheduleData,
          lastRun: 'N/A',
          nextRun: calculateNextRun(values.frequency, values.day, values.time)
        };
        
        setSchedules([...schedules, newSchedule]);
        message.success(`Planification "${values.name}" créée avec succès`);
      }
      
      setIsModalVisible(false);
    });
  };

  const calculateNextRun = (frequency, day, time) => {
    const now = new Date();
    let nextRun = new Date();
    
    if (frequency === 'daily') {
      nextRun.setDate(now.getDate() + 1);
    } else if (frequency === 'weekly') {
      const dayNumber = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'].indexOf(day);
      const daysUntilNext = (dayNumber - now.getDay() + 7) % 7;
      nextRun.setDate(now.getDate() + (daysUntilNext === 0 ? 7 : daysUntilNext));
    } else if (frequency === 'monthly') {
      nextRun.setMonth(now.getMonth() + 1);
      nextRun.setDate(parseInt(day));
    }
    
    const [hours, minutes] = time.split(':');
    nextRun.setHours(parseInt(hours), parseInt(minutes), 0, 0);
    
    return nextRun.toLocaleString();
  };

  const handleToggleScheduleStatus = (schedule, checked) => {
    const newStatus = checked ? 'active' : 'inactive';
    setSchedules(schedules.map(s => 
      s.id === schedule.id 
        ? { 
            ...s, 
            status: newStatus, 
            nextRun: newStatus === 'active' 
              ? calculateNextRun(s.frequency, s.day, s.time) 
              : 'N/A' 
          } 
        : s
    ));
    message.success(`Planification "${schedule.name}" ${newStatus === 'active' ? 'activée' : 'désactivée'}`);
  };

  const handleDeleteSchedule = (schedule) => {
    Modal.confirm({
      title: 'Êtes-vous sûr de vouloir supprimer cette planification?',
      content: `Cette action supprimera définitivement la planification "${schedule.name}".`,
      okText: 'Supprimer',
      okType: 'danger',
      cancelText: 'Annuler',
      onOk() {
        setSchedules(schedules.filter(s => s.id !== schedule.id));
        message.success(`Planification "${schedule.name}" supprimée`);
      }
    });
  };

  // Fonction pour générer un rapport
  const handleGenerateReport = () => {
    setGenerating(true);
    setProgress(0);
    
    message.loading('Génération du rapport en cours...');
    
    // Simulation de génération de rapport avec progression
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + Math.random() * 15;
        if (newProgress >= 100) {
          clearInterval(progressInterval);
          
          const newReport = {
            id: String(reports.length + 1),
            name: reportConfig.name,
            createdAt: new Date().toLocaleString(),
            createdBy: 'Vous',
            status: 'completed',
            size: '2.3 MB',
            type: reportConfig.format,
            period: getPeriodLabel(reportConfig.period, reportConfig.customRange),
            sections: [
              ...(reportConfig.includeTraffic ? ['Trafic'] : []),
              ...(reportConfig.includeAlerts ? ['Alertes'] : []),
              ...(reportConfig.includeInventory ? ['Équipements'] : []),
              ...(reportConfig.includePerformance ? ['Performance'] : []),
              ...(reportConfig.includeSecurity ? ['Sécurité'] : [])
            ],
            downloads: 0,
            shared: reportConfig.autoSend
          };
          
          setReports([newReport, ...reports]);
          setSelectedReport(newReport);
          setPreviewVisible(true);
          setGenerating(false);
          setProgress(0);
          message.success('Rapport généré avec succès');
          
          return 100;
        }
        return newProgress;
      });
    }, 200);
  };

  const getPeriodLabel = (period, customRange) => {
    switch (period) {
      case 'day':
        return 'Aujourd\'hui';
      case 'week':
        return 'Cette semaine';
      case 'month':
        return 'Ce mois';
      case 'custom':
        return customRange 
          ? `${customRange[0].format('DD/MM/YYYY')} - ${customRange[1].format('DD/MM/YYYY')}`
          : 'Période personnalisée';
      default:
        return 'Période inconnue';
    }
  };

  // Fonction pour utiliser un modèle
  const handleUseTemplate = (template) => {
    setReportConfig({
      ...reportConfig,
      name: `Rapport basé sur ${template.name}`,
      includeTraffic: template.sections.includes('Trafic'),
      includeAlerts: template.sections.includes('Alertes'),
      includeInventory: template.sections.includes('Équipements'),
      includePerformance: template.sections.includes('Performance'),
      includeSecurity: template.sections.includes('Sécurité'),
      graphType: template.graphType,
      colorTheme: template.colorTheme,
      format: template.format
    });
    setActiveTab('generator');
    message.success(`Template "${template.name}" appliqué`);
  };

  // Fonction pour sauvegarder un modèle
  const handleSaveTemplate = () => {
    setModalType('template');
    form.setFieldsValue({
      templateName: `${reportConfig.name} (modèle)`,
      description: 'Nouveau modèle de rapport'
    });
    setIsModalVisible(true);
  };

  const handleSaveTemplateConfirm = () => {
    form.validateFields().then(values => {
      const newTemplate = {
        id: String(templates.length + 1),
        name: values.templateName,
        sections: [
          ...(reportConfig.includeTraffic ? ['Trafic'] : []),
          ...(reportConfig.includeAlerts ? ['Alertes'] : []),
          ...(reportConfig.includeInventory ? ['Équipements'] : []),
          ...(reportConfig.includePerformance ? ['Performance'] : []),
          ...(reportConfig.includeSecurity ? ['Sécurité'] : [])
        ],
        graphType: reportConfig.graphType,
        colorTheme: reportConfig.colorTheme,
        format: reportConfig.format,
        description: values.description,
        usageCount: 0,
        lastUsed: new Date().toISOString().split('T')[0]
      };
      
      setTemplates([...templates, newTemplate]);
      setIsModalVisible(false);
      message.success(`Modèle "${values.templateName}" sauvegardé`);
    });
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setSelectedReport(null);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Générateur de Rapports</h1>
        <div className="flex gap-2">
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={() => setActiveTab('generator')}
            className="bg-blue-600"
          >
            Nouveau rapport
          </Button>
          <Button 
            icon={<CalendarOutlined />} 
            onClick={handleAddSchedule}
          >
            Planifier
          </Button>
        </div>
      </div>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab} className="custom-dark-tabs">
        <TabPane tab="Générateur" key="generator">
          <Row gutter={24}>
            <Col span={16}>
              <Card className="bg-gray-800 border-none mb-4">
                <div className="mb-4">
                  <h3 className="text-lg font-medium mb-4">Configuration du rapport</h3>
                  
                  <Form layout="vertical">
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item label="Nom du rapport">
                          <Input 
                            value={reportConfig.name}
                            onChange={e => setReportConfig({...reportConfig, name: e.target.value})}
                            className="bg-gray-700 border-gray-600"
                          />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item label="Format de sortie">
                          <Select 
                            value={reportConfig.format}
                            onChange={format => setReportConfig({...reportConfig, format})}
                            className="w-full"
                          >
                            <Option value="pdf">PDF - Document imprimable</Option>
                            <Option value="xlsx">Excel - Données structurées</Option>
                            <Option value="csv">CSV - Export de données</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                    </Row>
                    
                    <Form.Item label="Période de rapport">
                      <Radio.Group 
                        value={reportConfig.period}
                        onChange={e => setReportConfig({...reportConfig, period: e.target.value})}
                      >
                        <Radio value="day">Aujourd&apos;hui</Radio>
                        <Radio value="week">Cette semaine</Radio>
                        <Radio value="month">Ce mois</Radio>
                        <Radio value="custom">Période personnalisée</Radio>
                      </Radio.Group>
                      
                      {reportConfig.period === 'custom' && (
                        <RangePicker 
                          className="mt-2 bg-gray-700 border-gray-600"
                          onChange={dates => setReportConfig({...reportConfig, customRange: dates})}
                        />
                      )}
                    </Form.Item>
                    
                    <Form.Item label="Sections à inclure">
                      <div className="grid grid-cols-2 gap-4">
                        <Checkbox 
                          checked={reportConfig.includeTraffic}
                          onChange={e => setReportConfig({...reportConfig, includeTraffic: e.target.checked})}
                        >
                          Analyse du trafic réseau
                        </Checkbox>
                        <Checkbox 
                          checked={reportConfig.includeAlerts}
                          onChange={e => setReportConfig({...reportConfig, includeAlerts: e.target.checked})}
                        >
                          Alertes et incidents
                        </Checkbox>
                        <Checkbox 
                          checked={reportConfig.includeInventory}
                          onChange={e => setReportConfig({...reportConfig, includeInventory: e.target.checked})}
                        >
                          Inventaire des équipements
                        </Checkbox>
                        <Checkbox 
                          checked={reportConfig.includePerformance}
                          onChange={e => setReportConfig({...reportConfig, includePerformance: e.target.checked})}
                        >
                          Performances système
                        </Checkbox>
                        <Checkbox 
                          checked={reportConfig.includeSecurity}
                          onChange={e => setReportConfig({...reportConfig, includeSecurity: e.target.checked})}
                        >
                          Analyse de sécurité
                        </Checkbox>
                      </div>
                    </Form.Item>
                    
                    <Row gutter={16}>
                      <Col span={8}>
                        <Form.Item label="Type de graphiques">
                          <Select 
                            value={reportConfig.graphType}
                            onChange={graphType => setReportConfig({...reportConfig, graphType})}
                            className="w-full"
                          >
                            <Option value="line">
                              <LineChartOutlined /> Courbes
                            </Option>
                            <Option value="bar">
                              <BarChartOutlined /> Barres
                            </Option>
                            <Option value="pie">
                              <PieChartOutlined /> Secteurs
                            </Option>
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item label="Thème de couleur">
                          <Select 
                            value={reportConfig.colorTheme}
                            onChange={colorTheme => setReportConfig({...reportConfig, colorTheme})}
                            className="w-full"
                          >
                            <Option value="blue">Bleu professionnel</Option>
                            <Option value="green">Vert entreprise</Option>
                            <Option value="red">Rouge alerte</Option>
                            <Option value="purple">Violet moderne</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item label="Options">
                          <Checkbox 
                            checked={reportConfig.autoSend}
                            onChange={e => setReportConfig({...reportConfig, autoSend: e.target.checked})}
                          >
                            Partager automatiquement
                          </Checkbox>
                        </Form.Item>
                      </Col>
                    </Row>
                  </Form>
                </div>
                
                {generating && (
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span>Génération en cours...</span>
                      <span>{Math.round(progress)}%</span>
                    </div>
                    <Progress percent={progress} status="active" />
                  </div>
                )}
                
                <div className="flex gap-2">
                  <Button 
                    type="primary" 
                    size="large"
                    icon={<FileTextOutlined />}
                    onClick={handleGenerateReport}
                    loading={generating}
                    disabled={!reportConfig.includeTraffic && !reportConfig.includeAlerts && 
                             !reportConfig.includeInventory && !reportConfig.includePerformance && 
                             !reportConfig.includeSecurity}
                  >
                    Générer le rapport
                  </Button>
                  <Button 
                    icon={<SaveOutlined />}
                    onClick={handleSaveTemplate}
                  >
                    Sauver comme modèle
                  </Button>
                </div>
              </Card>
            </Col>
            
            <Col span={8}>
              <Card title="Aperçu" className="bg-gray-800 border-none mb-4">
                <div className="space-y-3">
                  <div>
                    <strong>Nom:</strong> {reportConfig.name}
                  </div>
                  <div>
                    <strong>Période:</strong> {getPeriodLabel(reportConfig.period, reportConfig.customRange)}
                  </div>
                  <div>
                    <strong>Format:</strong> 
                    <Tag className="ml-2">{reportConfig.format.toUpperCase()}</Tag>
                  </div>
                  <div>
                    <strong>Sections:</strong>
                    <div className="mt-1">
                      {reportConfig.includeTraffic && <Tag className="mb-1">Trafic</Tag>}
                      {reportConfig.includeAlerts && <Tag className="mb-1">Alertes</Tag>}
                      {reportConfig.includeInventory && <Tag className="mb-1">Équipements</Tag>}
                      {reportConfig.includePerformance && <Tag className="mb-1">Performance</Tag>}
                      {reportConfig.includeSecurity && <Tag className="mb-1">Sécurité</Tag>}
                    </div>
                  </div>
                  <div>
                    <strong>Graphiques:</strong> 
                    <Tag className="ml-2">
                      {reportConfig.graphType === 'line' && <LineChartOutlined />}
                      {reportConfig.graphType === 'bar' && <BarChartOutlined />}
                      {reportConfig.graphType === 'pie' && <PieChartOutlined />}
                      {' '}
                      {reportConfig.graphType === 'line' ? 'Courbes' : 
                       reportConfig.graphType === 'bar' ? 'Barres' : 'Secteurs'}
                    </Tag>
                  </div>
                </div>
              </Card>
              
              <Card title="Raccourcis" className="bg-gray-800 border-none">
                <div className="space-y-2">
                  <Button 
                    block 
                    onClick={() => setReportConfig({
                      ...reportConfig, 
                      includeTraffic: true, 
                      includeAlerts: true, 
                      includePerformance: true,
                      name: 'Rapport quotidien',
                      period: 'day'
                    })}
                  >
                    Rapport quotidien
                  </Button>
                  <Button 
                    block 
                    onClick={() => setReportConfig({
                      ...reportConfig, 
                      includeAlerts: true, 
                      includeSecurity: true,
                      name: 'Rapport sécurité',
                      colorTheme: 'red'
                    })}
                  >
                    Focus sécurité
                  </Button>
                  <Button 
                    block 
                    onClick={() => setReportConfig({
                      ...reportConfig, 
                      includeInventory: true,
                      name: 'Inventaire matériel',
                      format: 'xlsx',
                      graphType: 'pie'
                    })}
                  >
                    Inventaire
                  </Button>
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>
        
        <TabPane tab="Mes rapports" key="reports">
          <div className="mb-6">
            <Row gutter={16} align="middle">
              <Col span={8}>
                <Input 
                  placeholder="Rechercher un rapport..." 
                  prefix={<SearchOutlined />} 
                  onChange={e => setSearchText(e.target.value)} 
                  className="bg-gray-800 border-gray-700"
                />
              </Col>
              <Col span={16}>
                <div className="flex justify-end gap-2">
                  <Button icon={<ReloadOutlined />}>Actualiser</Button>
                  <Button icon={<DownloadOutlined />}>Télécharger tout</Button>
                </div>
              </Col>
            </Row>
          </div>
          
          <Card className="bg-gray-800 border-none">
            <Spin spinning={loading}>
              <Table 
                columns={reportColumns} 
                dataSource={filteredReports} 
                pagination={{ pageSize: 10 }}
                className="custom-dark-table"
                rowKey="id"
              />
            </Spin>
          </Card>
        </TabPane>
        
        <TabPane tab="Modèles" key="templates">
          <div className="mb-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Modèles de rapports</h3>
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleSaveTemplate}
              >
                Créer un modèle
              </Button>
            </div>
          </div>
          
          <Row gutter={16}>
            {templates.map(template => (
              <Col key={template.id} span={8} className="mb-4">
                <Card 
                  className="bg-gray-800 border-none hover:border-blue-500 transition-colors cursor-pointer"
                  onClick={() => handleUseTemplate(template)}
                  actions={[
                    <Button 
                      key="edit"
                      type="link" 
                      icon={<EditOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        message.info('Modification de template à implémenter');
                      }}
                    >
                      Modifier
                    </Button>,
                    <Button 
                      key="use"
                      type="link" 
                      icon={<CopyOutlined />}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleUseTemplate(template);
                      }}
                    >
                      Utiliser
                    </Button>
                  ]}
                >
                  <div className="mb-3">
                    <h4 className="font-medium">{template.name}</h4>
                    <p className="text-sm text-gray-400 mt-1">{template.description}</p>
                  </div>
                  
                  <div className="mb-3">
                    <div className="text-xs text-gray-500 mb-1">Sections incluses:</div>
                    {template.sections.map(section => (
                      <Tag key={section} size="small" className="mb-1">
                        {section}
                      </Tag>
                    ))}
                  </div>
                  
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Utilisé {template.usageCount} fois</span>
                    <span>Modifié le {template.lastUsed}</span>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>
        
        <TabPane tab="Planifications" key="schedules">
          <div className="mb-6 flex justify-between items-center">
            <h3 className="text-lg font-medium">Rapports programmés</h3>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleAddSchedule}
              className="bg-blue-600"
            >
              Nouvelle planification
            </Button>
          </div>
          
          <Card className="bg-gray-800 border-none">
            <Table 
              columns={scheduleColumns} 
              dataSource={schedules} 
              pagination={{ pageSize: 10 }}
              className="custom-dark-table"
              rowKey="id"
            />
          </Card>
        </TabPane>
      </Tabs>

      <Modal
        title={`Aperçu - ${selectedReport?.name}`}
        visible={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        width={800}
        footer={[
          <Button key="download" icon={<DownloadOutlined />} onClick={() => handleDownloadReport(selectedReport)}>
            Télécharger
          </Button>,
          <Button key="share" icon={<ShareAltOutlined />} onClick={() => handleShareReport(selectedReport)}>
            Partager
          </Button>,
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            Fermer
          </Button>
        ]}
      >
        {selectedReport && (
          <div className="bg-white text-black p-6 rounded">
            <div className="text-center mb-6">
              <h1 className="text-2xl font-bold">{selectedReport.name}</h1>
              <p className="text-gray-600">Période: {selectedReport.period}</p>
              <p className="text-sm text-gray-500">Généré le {selectedReport.createdAt}</p>
            </div>
            
            <div className="grid grid-cols-2 gap-6 mb-6">
              <div className="bg-blue-50 p-4 rounded">
                <h3 className="font-bold text-blue-800">Trafic Réseau</h3>
                <div className="mt-2">
                  <div className="text-2xl font-bold text-blue-600">1.2 TB</div>
                  <div className="text-sm text-gray-600">+15% vs période précédente</div>
                </div>
              </div>
              
              <div className="bg-red-50 p-4 rounded">
                <h3 className="font-bold text-red-800">Alertes</h3>
                <div className="mt-2">
                  <div className="text-2xl font-bold text-red-600">23</div>
                  <div className="text-sm text-gray-600">5 critiques, 18 mineures</div>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded">
              <h3 className="font-bold mb-2">Sections incluses:</h3>
              <div>
                {selectedReport.sections.map(section => (
                  <Tag key={section} className="mb-1">{section}</Tag>
                ))}
              </div>
            </div>
          </div>
        )}
      </Modal>

      <Modal
        title={
          modalType === 'schedule' ? 'Nouvelle planification' :
          modalType === 'editSchedule' ? 'Modifier la planification' :
          modalType === 'template' ? 'Sauvegarder le modèle' :
          modalType === 'share' ? 'Partager le rapport' :
          modalType === 'history' ? 'Historique d\'exécution' : 'Action'
        }
        visible={isModalVisible}
        onOk={
          modalType === 'schedule' || modalType === 'editSchedule' ? handleSaveSchedule :
          modalType === 'template' ? handleSaveTemplateConfirm :
          () => setIsModalVisible(false)
        }
        onCancel={handleModalCancel}
        okText={
          modalType === 'schedule' ? 'Créer' :
          modalType === 'editSchedule' ? 'Modifier' :
          modalType === 'template' ? 'Sauvegarder' : 'OK'
        }
        width={modalType === 'history' ? 800 : 600}
      >
        {(modalType === 'schedule' || modalType === 'editSchedule') && (
          <Form form={scheduleForm} layout="vertical">
            <Form.Item name="name" label="Nom de la planification" rules={[{ required: true }]}>
              <Input placeholder="Ex: Rapport mensuel automatique" />
            </Form.Item>
            
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="frequency" label="Fréquence" rules={[{ required: true }]}>
                  <Select>
                    <Option value="daily">Quotidien</Option>
                    <Option value="weekly">Hebdomadaire</Option>
                    <Option value="monthly">Mensuel</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="time" label="Heure" rules={[{ required: true }]}>
                  <Input placeholder="08:00" />
                </Form.Item>
              </Col>
            </Row>
            
            <Form.Item name="recipients" label="Destinataires (séparés par des virgules)" rules={[{ required: true }]}>
              <TextArea rows={3} placeholder="admin@example.com, manager@example.com" />
            </Form.Item>
            
            <Form.Item name="status" valuePropName="checked">
              <Checkbox>Activer immédiatement</Checkbox>
            </Form.Item>
          </Form>
        )}
        
        {modalType === 'template' && (
          <Form form={form} layout="vertical">
            <Form.Item name="templateName" label="Nom du modèle" rules={[{ required: true }]}>
              <Input placeholder="Ex: Rapport mensuel standard" />
            </Form.Item>
            <Form.Item name="description" label="Description">
              <TextArea rows={3} placeholder="Description du modèle..." />
            </Form.Item>
          </Form>
        )}
        
        {modalType === 'share' && selectedReport && (
          <div>
            <p className="mb-4">Partager le rapport &quot;{selectedReport.name}&quot; :</p>
            <Form layout="vertical">
              <Form.Item label="Destinataires">
                <TextArea rows={3} placeholder="admin@example.com, manager@example.com" />
              </Form.Item>
              <Form.Item label="Message (optionnel)">
                <TextArea rows={2} placeholder="Message d'accompagnement..." />
              </Form.Item>
              <Form.Item>
                <Checkbox>Générer un lien de partage public</Checkbox>
              </Form.Item>
            </Form>
          </div>
        )}
        
        {modalType === 'history' && selectedReport && (
          <div>
            <p className="mb-4">Historique d&apos;exécution pour &quot;{selectedReport.name}&quot; :</p>
            <List
              dataSource={[
                { date: '2024-06-10 08:00', status: 'success', duration: '2m 15s', size: '2.1 MB' },
                { date: '2024-06-03 08:00', status: 'success', duration: '1m 58s', size: '1.9 MB' },
                { date: '2024-05-27 08:00', status: 'error', duration: '0s', error: 'Timeout de connexion' },
                { date: '2024-05-20 08:00', status: 'success', duration: '2m 32s', size: '2.3 MB' },
              ]}
              renderItem={item => (
                <List.Item>
                  <div className="w-full flex justify-between items-center">
                    <div>
                      <div className="font-medium">{item.date}</div>
                      {item.error && <div className="text-red-500 text-sm">{item.error}</div>}
                    </div>
                    <div className="text-right">
                      <Badge 
                        status={item.status === 'success' ? 'success' : 'error'} 
                        text={item.status === 'success' ? 'Succès' : 'Échec'} 
                      />
                      {item.duration && <div className="text-sm text-gray-500">{item.duration}</div>}
                      {item.size && <div className="text-sm text-gray-500">{item.size}</div>}
                    </div>
                  </div>
                </List.Item>
              )}
            />
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Reports;