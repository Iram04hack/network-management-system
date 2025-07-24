/**
 * qosApiTest.js - Utilitaire de test pour les APIs QoS
 * 
 * Script pour tester les APIs QoS et créer des données de test
 */

import apiClient from '../api/client.js';

/**
 * Tester la connectivité des APIs QoS
 */
export const testQoSConnectivity = async () => {
  const results = {
    timestamp: new Date().toISOString(),
    endpoints: {},
    summary: { total: 0, success: 0, errors: 0 }
  };

  const endpoints = {
    policies: '/api/qos/policies/',
    trafficClasses: '/api/qos/traffic-classes/',
    classifiers: '/api/qos/classifiers/',
    interfacePolicies: '/api/qos/interface-policies/'
  };

  for (const [name, url] of Object.entries(endpoints)) {
    try {
      console.log(`[QoS Test] Testing ${name}: ${url}`);
      const response = await apiClient.get(url);
      results.endpoints[name] = {
        success: true,
        status: response.status,
        dataLength: Array.isArray(response.data) ? response.data.length : 
                   (response.data?.results?.length || 0),
        data: response.data
      };
      results.summary.success++;
    } catch (error) {
      console.error(`[QoS Test] Error testing ${name}:`, error.message);
      results.endpoints[name] = {
        success: false,
        error: error.message,
        status: error.response?.status || 'unknown'
      };
      results.summary.errors++;
    }
    results.summary.total++;
  }

  return results;
};

/**
 * Créer des données de test QoS
 */
export const createTestData = async () => {
  console.log('[QoS Test] Création de données de test QoS');
  
  const results = {
    timestamp: new Date().toISOString(),
    created: [],
    errors: []
  };

  // Données de test pour les politiques QoS
  const testPolicies = [
    {
      name: 'VoIP Haute Priorité',
      description: 'Priorité maximale pour trafic VoIP',
      interface: 'eth0',
      traffic_class: 'voice',
      qos_action: 'priority',
      bandwidth_limit: 200,
      port_range: '5060',
      protocol: 'UDP',
      is_active: true
    },
    {
      name: 'Limitation P2P',
      description: 'Limitation du trafic peer-to-peer',
      interface: 'eth1',
      traffic_class: 'bulk',
      qos_action: 'limit',
      bandwidth_limit: 100,
      port_range: '6881-6999',
      protocol: 'TCP',
      is_active: true
    },
    {
      name: 'Streaming Vidéo',
      description: 'Garantie pour streaming vidéo',
      interface: 'eth0',
      traffic_class: 'video',
      qos_action: 'priority',
      bandwidth_limit: 500,
      port_range: '80,443',
      protocol: 'TCP',
      is_active: false
    }
  ];

  // Créer les politiques de test
  for (const policy of testPolicies) {
    try {
      const response = await apiClient.post('/api/qos/policies/', policy);
      results.created.push({
        type: 'policy',
        name: policy.name,
        id: response.data.id,
        success: true
      });
      console.log(`[QoS Test] Politique créée: ${policy.name}`);
    } catch (error) {
      results.errors.push({
        type: 'policy',
        name: policy.name,
        error: error.message
      });
      console.error(`[QoS Test] Erreur création politique ${policy.name}:`, error.message);
    }
  }

  // Données de test pour les classes de trafic
  const testClasses = [
    {
      name: 'Voice Traffic',
      description: 'Traffic vocal prioritaire',
      priority: 1,
      bandwidth_guarantee: 200
    },
    {
      name: 'Video Traffic', 
      description: 'Traffic vidéo haute qualité',
      priority: 2,
      bandwidth_guarantee: 500
    },
    {
      name: 'Data Traffic',
      description: 'Traffic données standard',
      priority: 3,
      bandwidth_guarantee: 300
    }
  ];

  // Créer les classes de trafic de test
  for (const trafficClass of testClasses) {
    try {
      const response = await apiClient.post('/api/qos/traffic-classes/', trafficClass);
      results.created.push({
        type: 'traffic_class',
        name: trafficClass.name,
        id: response.data.id,
        success: true
      });
      console.log(`[QoS Test] Classe de trafic créée: ${trafficClass.name}`);
    } catch (error) {
      results.errors.push({
        type: 'traffic_class',
        name: trafficClass.name,
        error: error.message
      });
      console.error(`[QoS Test] Erreur création classe ${trafficClass.name}:`, error.message);
    }
  }

  return results;
};

/**
 * Nettoyer les données de test
 */
export const cleanupTestData = async () => {
  console.log('[QoS Test] Nettoyage des données de test');
  
  const results = {
    timestamp: new Date().toISOString(),
    deleted: [],
    errors: []
  };

  try {
    // Récupérer toutes les politiques
    const policiesResponse = await apiClient.get('/api/qos/policies/');
    const policies = policiesResponse.data.results || policiesResponse.data;

    // Supprimer les politiques de test
    for (const policy of policies) {
      if (policy.name.includes('Test') || 
          ['VoIP Haute Priorité', 'Limitation P2P', 'Streaming Vidéo'].includes(policy.name)) {
        try {
          await apiClient.delete(`/api/qos/policies/${policy.id}/`);
          results.deleted.push({
            type: 'policy',
            name: policy.name,
            id: policy.id
          });
          console.log(`[QoS Test] Politique supprimée: ${policy.name}`);
        } catch (error) {
          results.errors.push({
            type: 'policy',
            name: policy.name,
            error: error.message
          });
        }
      }
    }

    // Récupérer toutes les classes de trafic
    const classesResponse = await apiClient.get('/api/qos/traffic-classes/');
    const classes = classesResponse.data.results || classesResponse.data;

    // Supprimer les classes de test
    for (const trafficClass of classes) {
      if (['Voice Traffic', 'Video Traffic', 'Data Traffic'].includes(trafficClass.name)) {
        try {
          await apiClient.delete(`/api/qos/traffic-classes/${trafficClass.id}/`);
          results.deleted.push({
            type: 'traffic_class',
            name: trafficClass.name,
            id: trafficClass.id
          });
          console.log(`[QoS Test] Classe supprimée: ${trafficClass.name}`);
        } catch (error) {
          results.errors.push({
            type: 'traffic_class',
            name: trafficClass.name,
            error: error.message
          });
        }
      }
    }

  } catch (error) {
    console.error('[QoS Test] Erreur lors du nettoyage:', error.message);
    results.errors.push({
      type: 'cleanup',
      error: error.message
    });
  }

  return results;
};

// Fonction utilitaire pour exécuter tous les tests
export const runFullQoSTest = async () => {
  console.log('[QoS Test] Démarrage des tests complets QoS');
  
  const testResults = {
    timestamp: new Date().toISOString(),
    connectivity: null,
    dataCreation: null,
    cleanup: null,
    success: false
  };

  try {
    // 1. Test de connectivité
    console.log('[QoS Test] Phase 1: Test de connectivité');
    testResults.connectivity = await testQoSConnectivity();
    
    // 2. Création de données de test
    console.log('[QoS Test] Phase 2: Création de données de test');
    testResults.dataCreation = await createTestData();
    
    // 3. Test de récupération après création
    console.log('[QoS Test] Phase 3: Vérification des données créées');
    const postCreateConnectivity = await testQoSConnectivity();
    
    // 4. Nettoyage (optionnel)
    // testResults.cleanup = await cleanupTestData();
    
    testResults.success = testResults.connectivity.summary.success > 0;
    
    console.log('[QoS Test] Tests terminés:', testResults);
    return testResults;
    
  } catch (error) {
    console.error('[QoS Test] Erreur durant les tests:', error);
    testResults.error = error.message;
    return testResults;
  }
};

export default {
  testQoSConnectivity,
  createTestData,
  cleanupTestData,
  runFullQoSTest
};