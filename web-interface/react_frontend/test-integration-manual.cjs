/**
 * Script de test d'intégration manuel avec Node.js
 * Teste la connectivité entre frontend et backend
 */

const https = require('https');
const http = require('http');

// Configuration
const BACKEND_URL = 'https://localhost:8000';  // HTTPS détecté
const FRONTEND_URL = 'http://localhost:5173';

// Résultats de test
const testResults = {
  backend_running: false,
  frontend_running: false,
  endpoints: {},
  errors: []
};

// Helper pour faire des requêtes HTTP
function makeRequest(url, options = {}) {
  const urlObj = new URL(url);
  const client = urlObj.protocol === 'https:' ? https : http;
  
  return new Promise((resolve, reject) => {
    const req = client.request(url, {
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: 5000,
      rejectUnauthorized: false  // Accepter les certificats auto-signés
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          data: data
        });
      });
    });

    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });

    if (options.body) {
      req.write(options.body);
    }
    req.end();
  });
}

// Test de connectivité de base
async function testConnectivity() {
  console.log('🚀 Démarrage des tests d\'intégration manuel\n');

  // Test Backend Django
  console.log('📡 Test Backend Django...');
  try {
    const response = await makeRequest(`${BACKEND_URL}/admin/login/`);
    testResults.backend_running = [200, 301, 302].includes(response.status);
    console.log(`✅ Backend Django: Status ${response.status} - ${testResults.backend_running ? 'OK' : 'ERREUR'}`);
  } catch (error) {
    console.log(`❌ Backend Django: ${error.message}`);
    testResults.errors.push(`Backend: ${error.message}`);
  }

  // Test Frontend React
  console.log('📡 Test Frontend React...');
  try {
    const response = await makeRequest(`${FRONTEND_URL}/`);
    testResults.frontend_running = [200, 301, 302].includes(response.status);
    console.log(`✅ Frontend React: Status ${response.status} - ${testResults.frontend_running ? 'OK' : 'ERREUR'}`);
  } catch (error) {
    console.log(`❌ Frontend React: ${error.message}`);
    testResults.errors.push(`Frontend: ${error.message}`);
  }
}

// Test des endpoints API
async function testAPIEndpoints() {
  if (!testResults.backend_running) {
    console.log('\n⏭️ Tests API ignorés - Backend non accessible');
    return;
  }

  console.log('\n📡 Test des endpoints API...');

  const endpoints = [
    '/api/clients/',
    '/api/views/dashboard/',
    '/api/dashboard/config/',
    '/api/gns3_integration/api/servers/',
    '/swagger/',
    '/api/schema/'
  ];

  for (const endpoint of endpoints) {
    try {
      const response = await makeRequest(`${BACKEND_URL}${endpoint}`);
      testResults.endpoints[endpoint] = response.status;
      
      const status = [200, 401, 403].includes(response.status) ? '✅' : 
                    [404].includes(response.status) ? '⚠️' : '❌';
      
      console.log(`${status} ${endpoint}: Status ${response.status}`);
    } catch (error) {
      testResults.endpoints[endpoint] = 'error';
      console.log(`❌ ${endpoint}: ${error.message}`);
      testResults.errors.push(`${endpoint}: ${error.message}`);
    }
  }
}

// Test de la documentation Swagger
async function testSwagger() {
  if (!testResults.backend_running) {
    console.log('\n⏭️ Test Swagger ignoré - Backend non accessible');
    return;
  }

  console.log('\n📖 Test Swagger Documentation...');

  try {
    const response = await makeRequest(`${BACKEND_URL}/swagger/`);
    const swaggerOk = [200, 301, 302].includes(response.status);
    console.log(`${swaggerOk ? '✅' : '❌'} Swagger UI: Status ${response.status}`);

    // Test des schemas OpenAPI
    try {
      const schemaResponse = await makeRequest(`${BACKEND_URL}/api/schema/`);
      const schemaOk = [200].includes(schemaResponse.status);
      console.log(`${schemaOk ? '✅' : '❌'} Schema OpenAPI: Status ${schemaResponse.status}`);
      
      if (schemaOk && schemaResponse.data) {
        try {
          const schema = JSON.parse(schemaResponse.data);
          console.log(`📋 Schema OpenAPI: ${Object.keys(schema.paths || {}).length} endpoints documentés`);
        } catch (e) {
          console.log('⚠️ Schema OpenAPI non parsable');
        }
      }
    } catch (error) {
      console.log(`❌ Schema OpenAPI: ${error.message}`);
    }

  } catch (error) {
    console.log(`❌ Swagger UI: ${error.message}`);
  }
}

// Test des services spécifiques
async function testSpecificServices() {
  if (!testResults.backend_running) {
    console.log('\n⏭️ Tests services ignorés - Backend non accessible');
    return;
  }

  console.log('\n🔧 Test des services spécifiques...');

  // Test service health check si disponible
  try {
    const response = await makeRequest(`${BACKEND_URL}/health/`);
    console.log(`✅ Health Check: Status ${response.status}`);
  } catch (error) {
    console.log(`⚠️ Health Check non disponible: ${error.message}`);
  }

  // Test authentification
  try {
    const response = await makeRequest(`${BACKEND_URL}/api/auth/user/`);
    console.log(`📱 Auth endpoint: Status ${response.status}`);
  } catch (error) {
    console.log(`⚠️ Auth endpoint: ${error.message}`);
  }
}

// Génération du rapport final
function generateReport() {
  console.log('\n' + '='.repeat(60));
  console.log('📊 RAPPORT D\'INTÉGRATION FINAL');
  console.log('='.repeat(60));

  // Statut des services
  console.log('\n🏗️ SERVICES:');
  console.log(`Backend Django:  ${testResults.backend_running ? '✅ RUNNING' : '❌ DOWN'}`);
  console.log(`Frontend React:  ${testResults.frontend_running ? '✅ RUNNING' : '❌ DOWN'}`);

  // Statut des endpoints
  console.log('\n📡 ENDPOINTS API:');
  const workingEndpoints = Object.entries(testResults.endpoints)
    .filter(([_, status]) => [200, 401, 403].includes(status));
  const totalEndpoints = Object.keys(testResults.endpoints).length;
  
  Object.entries(testResults.endpoints).forEach(([endpoint, status]) => {
    const icon = [200, 401, 403].includes(status) ? '✅' : 
                 status === 404 ? '⚠️' : '❌';
    console.log(`${icon} ${endpoint}: ${status}`);
  });

  // Calcul du score
  let score = 0;
  let maxScore = 0;

  if (testResults.backend_running) score += 40;
  if (testResults.frontend_running) score += 20;
  maxScore += 60;

  score += workingEndpoints.length * 5;
  maxScore += totalEndpoints * 5;

  const percentage = maxScore > 0 ? (score / maxScore) * 100 : 0;

  console.log('\n📈 SCORE D\'INTÉGRATION:');
  console.log(`Score: ${score}/${maxScore} (${percentage.toFixed(1)}%)`);
  console.log(`Endpoints fonctionnels: ${workingEndpoints.length}/${totalEndpoints}`);

  // Erreurs
  if (testResults.errors.length > 0) {
    console.log('\n❌ ERREURS DÉTECTÉES:');
    testResults.errors.forEach((error, index) => {
      console.log(`${index + 1}. ${error}`);
    });
  }

  // Recommandations
  console.log('\n💡 RECOMMANDATIONS:');
  if (!testResults.backend_running) {
    console.log('- Vérifier que Django est démarré sur le port 8000');
    console.log('- Vérifier la configuration Docker du backend');
  }
  if (!testResults.frontend_running) {
    console.log('- Vérifier que React est démarré sur le port 5173');
    console.log('- Vérifier la configuration Vite du frontend');
  }
  if (workingEndpoints.length < totalEndpoints / 2) {
    console.log('- Vérifier la configuration des URLs Django');
    console.log('- Vérifier les permissions et l\'authentification');
  }

  // Statut global
  console.log('\n🎯 STATUT GLOBAL:');
  if (percentage >= 80) {
    console.log('✅ INTÉGRATION EXCELLENTE - Système prêt pour la production');
  } else if (percentage >= 60) {
    console.log('⚠️ INTÉGRATION CORRECTE - Quelques ajustements nécessaires');
  } else if (percentage >= 40) {
    console.log('🔧 INTÉGRATION PARTIELLE - Corrections importantes requises');
  } else {
    console.log('❌ INTÉGRATION DÉFAILLANTE - Résolution des problèmes critiques requise');
  }

  console.log('\n' + '='.repeat(60));

  return percentage >= 50; // Retourne true si l'intégration est acceptable
}

// Fonction principale
async function main() {
  try {
    await testConnectivity();
    await testAPIEndpoints();
    await testSwagger();
    await testSpecificServices();
    
    const success = generateReport();
    process.exit(success ? 0 : 1);

  } catch (error) {
    console.error('❌ Erreur fatale lors des tests:', error);
    process.exit(1);
  }
}

// Exécution
if (require.main === module) {
  main();
}

module.exports = {
  testConnectivity,
  testAPIEndpoints,
  testSwagger,
  generateReport
};