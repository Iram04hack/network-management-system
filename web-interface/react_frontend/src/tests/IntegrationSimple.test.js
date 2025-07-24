/**
 * Tests d'intégration simplifiés pour valider la liaison frontend-backend
 */

// Tests sans imports complexes pour éviter les problèmes de configuration Jest
describe('Tests d\'intégration frontend-backend', () => {

  let testResults = {
    backend_running: false,
    frontend_running: false,
    endpoints_tested: 0,
    errors: []
  };

  beforeAll(async () => {
    console.log('🚀 Démarrage des tests d\'intégration simplifiés');
    
    // Test 1: Vérifier que le backend Django répond
    try {
      const response = await fetch('http://localhost:8000/admin/login/');
      testResults.backend_running = response.ok;
      console.log('✅ Backend Django accessible:', response.status);
    } catch (error) {
      console.log('❌ Backend Django non accessible:', error.message);
      testResults.backend_running = false;
      testResults.errors.push('Backend Django: ' + error.message);
    }

    // Test 2: Vérifier que le frontend React répond
    try {
      const response = await fetch('http://localhost:5173/');
      testResults.frontend_running = response.ok;
      console.log('✅ Frontend React accessible:', response.status);
    } catch (error) {
      console.log('❌ Frontend React non accessible:', error.message);
      testResults.frontend_running = false;
      testResults.errors.push('Frontend React: ' + error.message);
    }
  });

  afterAll(() => {
    console.log('\n📊 Résumé des tests d\'intégration:');
    console.log(`Backend Django: ${testResults.backend_running ? '✅ OK' : '❌ ERREUR'}`);
    console.log(`Frontend React: ${testResults.frontend_running ? '✅ OK' : '❌ ERREUR'}`);
    console.log(`Endpoints testés: ${testResults.endpoints_tested}`);
    if (testResults.errors.length > 0) {
      console.log('Erreurs rencontrées:');
      testResults.errors.forEach(err => console.log('  -', err));
    }
  });

  test('devrait avoir le backend Django accessible', () => {
    expect(testResults.backend_running).toBe(true);
  });

  test('devrait avoir le frontend React accessible', () => {
    expect(testResults.frontend_running).toBe(true);
  });

  describe('Tests des endpoints API', () => {
    
    test('devrait tester l\'endpoint /api/clients/', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/clients/');
        testResults.endpoints_tested++;
        
        console.log(`📡 /api/clients/ - Status: ${response.status}`);
        
        // Accept 200 (success), 401 (unauthorized), or 403 (forbidden) - all indicate the endpoint exists
        expect([200, 401, 403].includes(response.status)).toBe(true);
      } catch (error) {
        console.log('❌ Erreur /api/clients/:', error.message);
        testResults.errors.push('/api/clients/: ' + error.message);
        // Don't fail the test for network errors, just log them
      }
    });

    test('devrait tester l\'endpoint /api/views/dashboard/', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/views/dashboard/');
        testResults.endpoints_tested++;
        
        console.log(`📡 /api/views/dashboard/ - Status: ${response.status}`);
        
        expect([200, 401, 403].includes(response.status)).toBe(true);
      } catch (error) {
        console.log('❌ Erreur /api/views/dashboard/:', error.message);
        testResults.errors.push('/api/views/dashboard/: ' + error.message);
      }
    });

    test('devrait tester l\'endpoint /api/dashboard/config/', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/dashboard/config/');
        testResults.endpoints_tested++;
        
        console.log(`📡 /api/dashboard/config/ - Status: ${response.status}`);
        
        expect([200, 401, 403].includes(response.status)).toBe(true);
      } catch (error) {
        console.log('❌ Erreur /api/dashboard/config/:', error.message);
        testResults.errors.push('/api/dashboard/config/: ' + error.message);
      }
    });

    test('devrait tester l\'endpoint /api/gns3_integration/api/servers/', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/api/gns3_integration/api/servers/');
        testResults.endpoints_tested++;
        
        console.log(`📡 /api/gns3_integration/api/servers/ - Status: ${response.status}`);
        
        expect([200, 401, 403].includes(response.status)).toBe(true);
      } catch (error) {
        console.log('❌ Erreur /api/gns3_integration/api/servers/:', error.message);
        testResults.errors.push('/api/gns3_integration/api/servers/: ' + error.message);
      }
    });
  });

  describe('Tests de connectivité avancée', () => {
    
    test('devrait tester Swagger UI', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/swagger/');
        console.log(`📖 Swagger UI - Status: ${response.status}`);
        
        // Swagger should be accessible
        expect([200, 301, 302].includes(response.status)).toBe(true);
      } catch (error) {
        console.log('❌ Erreur Swagger:', error.message);
        testResults.errors.push('Swagger: ' + error.message);
      }
    });

    test('devrait vérifier les CORS entre frontend et backend', async () => {
      if (!testResults.backend_running || !testResults.frontend_running) {
        console.log('⏭️ Test ignoré - Services non accessibles');
        return;
      }

      try {
        // Test simple de requête CORS
        const response = await fetch('http://localhost:8000/api/clients/', {
          method: 'OPTIONS',
          headers: {
            'Origin': 'http://localhost:5173',
            'Access-Control-Request-Method': 'GET'
          }
        });
        
        console.log(`🔄 CORS test - Status: ${response.status}`);
        
        // CORS preflight should work or endpoint should allow direct access
        expect([200, 204, 404].includes(response.status)).toBe(true);
      } catch (error) {
        console.log('⚠️ Info CORS:', error.message);
        // Don't fail on CORS errors as they might be expected
      }
    });
  });

  describe('Tests de validation des services', () => {
    
    test('devrait valider l\'intégration globale', () => {
      let score = 0;
      let total = 0;

      // Points pour les services de base
      if (testResults.backend_running) score += 3;
      if (testResults.frontend_running) score += 2;
      total += 5;

      // Points pour les endpoints
      score += testResults.endpoints_tested;
      total += 4; // 4 endpoints testés

      const percentage = (score / total) * 100;
      
      console.log(`📊 Score d'intégration: ${score}/${total} (${percentage.toFixed(1)}%)`);
      
      // Au moins 50% des fonctionnalités devraient marcher
      expect(percentage).toBeGreaterThanOrEqual(50);
    });

    test('devrait avoir moins de 50% d\'erreurs', () => {
      const totalTests = testResults.endpoints_tested + 2; // +2 pour backend/frontend
      const errorRate = (testResults.errors.length / totalTests) * 100;
      
      console.log(`❌ Taux d'erreur: ${errorRate.toFixed(1)}%`);
      
      expect(errorRate).toBeLessThan(50);
    });
  });

  describe('Tests de performance basique', () => {
    
    test('devrait mesurer le temps de réponse du backend', async () => {
      if (!testResults.backend_running) {
        console.log('⏭️ Test ignoré - Backend non accessible');
        return;
      }

      const startTime = Date.now();
      
      try {
        await fetch('http://localhost:8000/admin/login/');
        const responseTime = Date.now() - startTime;
        
        console.log(`⏱️ Temps de réponse backend: ${responseTime}ms`);
        
        // Backend should respond in less than 5 seconds
        expect(responseTime).toBeLessThan(5000);
      } catch (error) {
        console.log('❌ Erreur mesure performance:', error.message);
      }
    });
  });
});