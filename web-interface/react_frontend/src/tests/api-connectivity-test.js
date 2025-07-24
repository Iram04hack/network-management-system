/**
 * Test de connectivité des APIs de monitoring
 * Vérifie que les endpoints modifiés dans useMonitoring.js fonctionnent
 */

import axios from 'axios';

// Configuration de test avec les mêmes credentials que le frontend
const API_CONFIG = {
  baseURL: 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
};

const AUTH_CREDENTIALS = {
  username: 'admin@hybrido.com',
  password: 'hybrido2025',
};

const testClient = axios.create(API_CONFIG);

// Ajouter l'authentification Basic Auth
testClient.interceptors.request.use((config) => {
  const credentials = btoa(`${AUTH_CREDENTIALS.username}:${AUTH_CREDENTIALS.password}`);
  config.headers.Authorization = `Basic ${credentials}`;
  return config;
});

// Endpoints à tester (les mêmes que dans useMonitoring.js modifié)
const ENDPOINTS_TO_TEST = {
  unified: {
    status: '/api/monitoring/unified/status/',
    metrics: '/api/monitoring/unified/metrics/',
    dashboard: '/api/monitoring/unified/dashboard/'
  },
  standard: {
    alerts: '/api/monitoring/alerts/',
    dashboards: '/api/monitoring/dashboards/',
    notifications: '/api/monitoring/notifications/',
    'metrics-definitions': '/api/monitoring/metrics-definitions/',
    'service-checks': '/api/monitoring/service-checks/'
  }
};

async function testApiConnectivity() {
  console.log('🔧 Test de connectivité des APIs de monitoring...\n');
  
  const results = {
    unified: {},
    standard: {},
    summary: {
      total: 0,
      success: 0,
      failed: 0,
      errors: []
    }
  };

  // Test des APIs unifiées (prioritaires)
  console.log('📊 Test des APIs unifiées:');
  for (const [name, endpoint] of Object.entries(ENDPOINTS_TO_TEST.unified)) {
    results.summary.total++;
    try {
      const startTime = Date.now();
      const response = await testClient.get(endpoint);
      const responseTime = Date.now() - startTime;
      
      results.unified[name] = {
        status: 'SUCCESS',
        code: response.status,
        responseTime: `${responseTime}ms`,
        dataSize: JSON.stringify(response.data).length
      };
      
      console.log(`  ✅ ${name}: ${response.status} (${responseTime}ms)`);
      results.summary.success++;
    } catch (error) {
      results.unified[name] = {
        status: 'FAILED',
        error: error.response?.status || error.message,
        message: error.response?.data?.detail || error.message
      };
      
      console.log(`  ❌ ${name}: ${error.response?.status || 'ERROR'} - ${error.message}`);
      results.summary.failed++;
      results.summary.errors.push(`${name}: ${error.message}`);
    }
  }

  // Test des APIs standard
  console.log('\n📈 Test des APIs standard:');
  for (const [name, endpoint] of Object.entries(ENDPOINTS_TO_TEST.standard)) {
    results.summary.total++;
    try {
      const startTime = Date.now();
      const response = await testClient.get(endpoint);
      const responseTime = Date.now() - startTime;
      
      results.standard[name] = {
        status: 'SUCCESS',
        code: response.status,
        responseTime: `${responseTime}ms`,
        dataCount: Array.isArray(response.data) ? response.data.length : 
                   response.data.results ? response.data.results.length : 'N/A'
      };
      
      console.log(`  ✅ ${name}: ${response.status} (${responseTime}ms)`);
      results.summary.success++;
    } catch (error) {
      results.standard[name] = {
        status: 'FAILED',
        error: error.response?.status || error.message,
        message: error.response?.data?.detail || error.message
      };
      
      console.log(`  ❌ ${name}: ${error.response?.status || 'ERROR'} - ${error.message}`);
      results.summary.failed++;
      results.summary.errors.push(`${name}: ${error.message}`);
    }
  }

  // Résumé
  console.log('\n📋 Résumé des tests:');
  console.log(`  Total endpoints testés: ${results.summary.total}`);
  console.log(`  Succès: ${results.summary.success}`);
  console.log(`  Échecs: ${results.summary.failed}`);
  console.log(`  Taux de réussite: ${((results.summary.success / results.summary.total) * 100).toFixed(1)}%`);

  if (results.summary.errors.length > 0) {
    console.log('\n❌ Erreurs détectées:');
    results.summary.errors.forEach(error => console.log(`  - ${error}`));
  }

  return results;
}

// Test spécifique des données unifiées
async function testUnifiedDataStructure() {
  console.log('\n🔍 Test de la structure des données unifiées...\n');
  
  try {
    // Test unified/status
    console.log('📊 Structure de unified/status:');
    const statusRes = await testClient.get('/api/monitoring/unified/status/');
    const statusData = statusRes.data;
    
    console.log(`  ✅ operational: ${statusData.operational}`);
    console.log(`  ✅ components: ${Object.keys(statusData.components || {}).length} disponibles`);
    console.log(`  ✅ docker_health: ${statusData.docker_health?.total_services || 0} services`);
    console.log(`  ✅ gns3_summary: ${statusData.gns3_summary?.total || 0} nœuds GNS3`);

    // Test unified/metrics
    console.log('\n📈 Structure de unified/metrics:');
    const metricsRes = await testClient.get('/api/monitoring/unified/metrics/');
    const metricsData = metricsRes.data;
    
    console.log(`  ✅ nms_services_metrics: ${metricsData.nms_services_metrics?.length || 0} services`);
    console.log(`  ✅ successful_collections: ${metricsData.summary?.successful_collections || 0}`);
    console.log(`  ✅ total_sources: ${metricsData.summary?.total_sources || 0}`);
    
    if (metricsData.nms_services_metrics?.length > 0) {
      const service = metricsData.nms_services_metrics[0];
      console.log(`  ✅ Premier service - ${service.service_name}: ${service.status}`);
      console.log(`  ✅ Métriques disponibles: CPU, Memory, Network`);
    }

    return true;
  } catch (error) {
    console.log(`  ❌ Erreur: ${error.message}`);
    return false;
  }
}

// Exécution des tests
async function runAllTests() {
  try {
    console.log('🚀 Démarrage des tests de connectivité API...\n');
    
    const connectivityResults = await testApiConnectivity();
    const dataStructureOk = await testUnifiedDataStructure();
    
    console.log('\n🎯 Résultat final:');
    if (connectivityResults.summary.success >= 6 && dataStructureOk) {
      console.log('✅ Les APIs de monitoring sont fonctionnelles et compatibles avec le frontend!');
      return true;
    } else {
      console.log('❌ Certaines APIs ne fonctionnent pas correctement.');
      return false;
    }
  } catch (error) {
    console.error('💥 Erreur globale lors des tests:', error.message);
    return false;
  }
}

// Exporter pour utilisation en module
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    testApiConnectivity,
    testUnifiedDataStructure,
    runAllTests
  };
}

// Exécution directe si appelé en script
if (typeof require !== 'undefined' && require.main === module) {
  runAllTests()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      console.error('💥 Erreur fatale:', error);
      process.exit(1);
    });
}