/**
 * UnifiedApiData.js - Service de données unifiées mockées pour le monitoring
 * Version d'urgence pour corriger la page blanche
 */

// Données mockées pour les métriques système
export const systemMetrics = {
  cpu: {
    current: Math.floor(Math.random() * 60) + 20, // 20-80%
    max: 90,
    trend: 'stable'
  },
  memory: {
    current: Math.floor(Math.random() * 40) + 30, // 30-70%
    max: 85,
    trend: 'stable'
  },
  disk: {
    current: Math.floor(Math.random() * 30) + 40, // 40-70%
    max: 90,
    trend: 'increasing'
  },
  network: {
    current: Math.floor(Math.random() * 50) + 25, // 25-75 Mbps
    max: 100,
    unit: 'Mbps'
  }
};

// Données mockées pour les services Docker
export const dockerServices = [
  {
    id: 'service-1',
    name: 'nms-api',
    health_status: 'healthy',
    cpu_percent: Math.random() * 25,
    memory_percent: Math.random() * 40,
    status: 'running'
  },
  {
    id: 'service-2',
    name: 'postgresql',
    health_status: 'healthy',
    cpu_percent: Math.random() * 15,
    memory_percent: Math.random() * 35,
    status: 'running'
  },
  {
    id: 'service-3',
    name: 'redis',
    health_status: 'healthy',
    cpu_percent: Math.random() * 10,
    memory_percent: Math.random() * 20,
    status: 'running'
  },
  {
    id: 'service-4',
    name: 'nginx',
    health_status: 'healthy',
    cpu_percent: Math.random() * 12,
    memory_percent: Math.random() * 25,
    status: 'running'
  },
  {
    id: 'service-5',
    name: 'monitoring',
    health_status: Math.random() > 0.8 ? 'unhealthy' : 'healthy',
    cpu_percent: Math.random() * 30,
    memory_percent: Math.random() * 45,
    status: 'running'
  },
  {
    id: 'service-6',
    name: 'elasticsearch',
    health_status: 'healthy',
    cpu_percent: Math.random() * 40,
    memory_percent: Math.random() * 60,
    status: 'running'
  }
];

// Calculs dérivés
export const totalServices = dockerServices.length;
export const healthyServices = dockerServices.filter(s => s.health_status === 'healthy').length;
export const healthPercentage = (healthyServices / totalServices) * 100;

// Données mockées pour les alertes
export const systemAlerts = [
  {
    id: 'alert-1',
    title: 'CPU élevé détecté',
    message: 'Utilisation CPU supérieure à 80% sur le serveur principal',
    severity: 'warning',
    timestamp: new Date(Date.now() - 300000).toISOString(), // 5 min ago
    source: 'System Monitor',
    equipment: 'srv-001'
  },
  {
    id: 'alert-2', 
    title: 'Espace disque faible',
    message: 'Partition /var à 85% de capacité',
    severity: 'critical',
    timestamp: new Date(Date.now() - 600000).toISOString(), // 10 min ago
    source: 'Disk Monitor',
    equipment: 'srv-001'
  },
  {
    id: 'alert-3',
    title: 'Service monitoring instable',
    message: 'Le service de monitoring redémarre fréquemment',
    severity: 'warning',
    timestamp: new Date(Date.now() - 900000).toISOString(), // 15 min ago
    source: 'Docker Monitor',
    equipment: 'monitoring-container'
  }
].filter(() => Math.random() > 0.3); // Afficher aléatoirement certaines alertes

export const totalAlerts = systemAlerts.length;
export const criticalAlerts = systemAlerts.filter(a => a.severity === 'critical').length;
export const warningAlerts = systemAlerts.filter(a => a.severity === 'warning').length;

// États globaux
export const systemOperational = healthPercentage > 70 && criticalAlerts < 2;
export const overallHealth = systemOperational ? 'healthy' : 'degraded';

// Dernières mises à jour
export const lastUpdate = {
  systemMetrics: new Date().toISOString(),
  dockerServices: new Date().toISOString(),
  alerts: new Date().toISOString()
};

// Erreurs (vides pour commencer)
export const errors = {
  systemMetrics: null,
  dockerServices: null,
  alerts: null
};

/**
 * Fonction pour rafraîchir toutes les données
 * En version mockée, on simule juste un délai
 */
export const refreshAllData = async () => {
  console.log('🔄 Rafraîchissement des données unifiées...');
  
  // Simuler un délai d'API
  await new Promise(resolve => setTimeout(resolve, 1000));
  
  // Mettre à jour quelques valeurs aléatoirement
  systemMetrics.cpu.current = Math.floor(Math.random() * 60) + 20;
  systemMetrics.memory.current = Math.floor(Math.random() * 40) + 30;
  systemMetrics.network.current = Math.floor(Math.random() * 50) + 25;
  
  // Mettre à jour les timestamps
  lastUpdate.systemMetrics = new Date().toISOString();
  lastUpdate.dockerServices = new Date().toISOString();
  lastUpdate.alerts = new Date().toISOString();
  
  console.log('✅ Données rafraîchies avec succès');
  return true;
};

// Données mockées pour les équipements réseau (pour NetworkSimple.jsx)
export const equipmentsList = [
  {
    id: 'eq-001',
    name: 'Router-Principal',
    type: 'router',
    vendor: 'Cisco',
    ip: '192.168.1.1',
    status: 'online',
    uptime: 99.8
  },
  {
    id: 'eq-002', 
    name: 'Switch-Core-01',
    type: 'switch',
    vendor: 'Cisco',
    ip: '192.168.1.10',
    status: 'online',
    uptime: 99.5
  },
  {
    id: 'eq-003',
    name: 'AP-Bureau-Nord',
    type: 'access_point',
    vendor: 'Ubiquiti',
    ip: '192.168.1.50',
    status: 'online',
    uptime: 98.2
  },
  {
    id: 'eq-004',
    name: 'Server-01',
    type: 'server',
    vendor: 'Dell',
    ip: '192.168.1.100',
    status: 'online',
    uptime: 99.9
  },
  {
    id: 'eq-005',
    name: 'Firewall-Edge',
    type: 'firewall',
    vendor: 'Fortinet',
    ip: '192.168.1.2',
    status: Math.random() > 0.9 ? 'offline' : 'online',
    uptime: 97.5
  }
];

export const totalEquipments = equipmentsList.length;
export const activeEquipments = equipmentsList.filter(eq => eq.status === 'online').length;

// Données mockées pour les projets GNS3
export const projectsList = [
  {
    id: 'proj-001',
    name: 'Topologie-Production',
    nodes_count: 12,
    status: 'opened',
    last_modified: new Date(Date.now() - 3600000).toISOString()
  },
  {
    id: 'proj-002',
    name: 'Test-Lab',
    nodes_count: 8,
    status: 'closed',
    last_modified: new Date(Date.now() - 7200000).toISOString()
  },
  {
    id: 'proj-003',
    name: 'Formation-Reseau',
    nodes_count: 15,
    status: 'opened',
    last_modified: new Date(Date.now() - 1800000).toISOString()
  }
];

export const totalProjects = projectsList.length;
export const activeNodes = projectsList.reduce((sum, proj) => sum + proj.nodes_count, 0);

// Données agrégées par type
export const devicesByType = [
  { name: 'Routeurs', value: equipmentsList.filter(eq => eq.type === 'router').length, color: '#3B82F6' },
  { name: 'Switches', value: equipmentsList.filter(eq => eq.type === 'switch').length, color: '#10B981' },
  { name: 'Points d\'accès', value: equipmentsList.filter(eq => eq.type === 'access_point').length, color: '#F59E0B' },
  { name: 'Serveurs', value: equipmentsList.filter(eq => eq.type === 'server').length, color: '#8B5CF6' },
  { name: 'Firewalls', value: equipmentsList.filter(eq => eq.type === 'firewall').length, color: '#EF4444' }
];

// Données agrégées par fabricant
export const devicesByVendor = [
  { name: 'Cisco', value: equipmentsList.filter(eq => eq.vendor === 'Cisco').length, color: '#1E40AF' },
  { name: 'Ubiquiti', value: equipmentsList.filter(eq => eq.vendor === 'Ubiquiti').length, color: '#059669' },
  { name: 'Dell', value: equipmentsList.filter(eq => eq.vendor === 'Dell').length, color: '#DC2626' },
  { name: 'Fortinet', value: equipmentsList.filter(eq => eq.vendor === 'Fortinet').length, color: '#7C3AED' }
];

// Fonction pour obtenir les statistiques essentielles
export const getEssentialStats = () => {
  return {
    systems: {
      totalEquipments,
      activeEquipments,
      healthPercentage: Math.round((activeEquipments / totalEquipments) * 100)
    },
    projects: {
      totalProjects,
      activeNodes
    },
    services: {
      totalServices,
      healthyServices,
      healthPercentage
    },
    alerts: {
      totalAlerts,
      criticalAlerts,
      warningAlerts
    },
    operational: systemOperational,
    lastUpdate: lastUpdate
  };
};

// Fonction pour vérifier si les données sont disponibles
export const isDataAvailable = () => {
  return {
    equipments: equipmentsList.length > 0,
    projects: projectsList.length > 0,
    services: dockerServices.length > 0,
    systemMetrics: systemMetrics && systemMetrics.cpu,
    alerts: Array.isArray(systemAlerts)
  };
};

// Export par défaut pour compatibilité
const UnifiedApiData = {
  systemMetrics,
  dockerServices,
  totalServices,
  healthyServices,
  healthPercentage,
  systemAlerts,
  totalAlerts,
  criticalAlerts,
  warningAlerts,
  systemOperational,
  overallHealth,
  lastUpdate,
  errors,
  refreshAllData,
  // Ajout des nouvelles données pour NetworkSimple
  equipmentsList,
  totalEquipments,
  activeEquipments,
  projectsList,
  totalProjects,
  activeNodes,
  devicesByType,
  devicesByVendor,
  // Ajout des nouvelles fonctions pour ApiTestPage
  getEssentialStats,
  isDataAvailable
};

export default UnifiedApiData;