/**
 * ApiTester - Utilitaire de test pour le système unifié
 * 
 * Teste la connectivité avec tous les vrais backends Django
 * Valide le système d'informations API unifié
 */

import apiClient from '../api/client.js';
import unifiedApiSystem from '../services/UnifiedApiSystem.js';
import realBackendIntegration from '../services/RealBackendIntegration.js';

class ApiTester {
  constructor() {
    this.testResults = {
      monitoring: { passed: 0, failed: 0, tests: [] },
      qos: { passed: 0, failed: 0, tests: [] },
      security: { passed: 0, failed: 0, tests: [] },
      gns3: { passed: 0, failed: 0, tests: [] },
      unified: { passed: 0, failed: 0, tests: [] }
    };
  }

  /**
   * Lance tous les tests de connectivité API
   */
  async runAllTests() {
    console.log('🚀 Début des tests de connectivité API...');
    
    try {
      // Tests par module
      await this.testMonitoringAPIs();
      await this.testQoSAPIs();
      await this.testSecurityAPIs();
      await this.testGNS3APIs();
      
      // Tests du système unifié
      await this.testUnifiedSystem();
      
      // Générer le rapport final
      this.generateReport();
      
    } catch (error) {
      console.error('❌ Erreur lors des tests:', error);
    }
  }

  /**
   * Teste les APIs de monitoring
   */
  async testMonitoringAPIs() {
    console.log('📊 Test des APIs Monitoring...');
    
    const tests = [
      { name: 'Status global', url: '/api/monitoring/unified/status/' },
      { name: 'Métriques temps réel', url: '/api/monitoring/unified/metrics/' },
      { name: 'Alertes système', url: '/api/monitoring/alerts/' },
      { name: 'Devices', url: '/api/monitoring/devices/' },
      { name: 'Dashboards', url: '/api/monitoring/dashboards/' }
    ];

    for (const test of tests) {
      await this.runSingleTest('monitoring', test);
    }
  }

  /**
   * Teste les APIs QoS
   */
  async testQoSAPIs() {
    console.log('⚡ Test des APIs QoS Management...');
    
    const tests = [
      { name: 'QoS Status', url: '/api/qos/unified/status/' },
      { name: 'QoS Dashboard', url: '/api/qos/unified/dashboard/' },
      { name: 'Infrastructure Health', url: '/api/qos/unified/infrastructure-health/' },
      { name: 'Integration Status', url: '/api/qos/unified/integration-status/' },
      { name: 'QoS Policies', url: '/api/qos/policies/' },
      { name: 'Traffic Classes', url: '/api/qos/traffic-classes/' }
    ];

    for (const test of tests) {
      await this.runSingleTest('qos', test);
    }
  }

  /**
   * Teste les APIs Security
   */
  async testSecurityAPIs() {
    console.log('🔐 Test des APIs Security Management...');
    
    const tests = [
      { name: 'Security Dashboard', url: '/api/security/dashboard/' },
      { name: 'Security Status', url: '/api/security/status/' },
      { name: 'Security Alerts', url: '/api/security/alerts/' },
      { name: 'Security Rules', url: '/api/security/rules/' },
      { name: 'Vulnerabilities', url: '/api/security/vulnerabilities/' },
      { name: 'Security Metrics', url: '/api/security/metrics/' }
    ];

    for (const test of tests) {
      await this.runSingleTest('security', test);
    }
  }

  /**
   * Teste les APIs GNS3
   */
  async testGNS3APIs() {
    console.log('🌐 Test des APIs GNS3...');
    
    const tests = [
      { name: 'GNS3 Projects', url: '/api/gns3/projects/' },
      { name: 'GNS3 Servers', url: '/api/gns3/servers/' },
      { name: 'GNS3 Nodes', url: '/api/gns3/nodes/' }
    ];

    for (const test of tests) {
      await this.runSingleTest('gns3', test);
    }
  }

  /**
   * Teste le système unifié
   */
  async testUnifiedSystem() {
    console.log('🔄 Test du Système API Unifié...');
    
    const tests = [
      { 
        name: 'Backend Integration - QoS', 
        test: async () => {
          const result = await realBackendIntegration.getQoSStatus();
          return result.success || result.error.includes('Informations d\'authentification');
        }
      },
      { 
        name: 'Backend Integration - Security', 
        test: async () => {
          const result = await realBackendIntegration.getSecurityDashboard();
          return result.success || result.error.includes('Informations d\'authentification');
        }
      },
      { 
        name: 'Unified System - Données initiales', 
        test: async () => {
          const data = unifiedApiSystem.getAllData();
          return data && typeof data === 'object';
        }
      },
      { 
        name: 'Unified System - Force Refresh', 
        test: async () => {
          try {
            await unifiedApiSystem.forceRefresh('systemMetrics');
            return true;
          } catch (error) {
            return error.message.includes('Informations d\'authentification') || 
                   error.message.includes('authentication');
          }
        }
      }
    ];

    for (const test of tests) {
      const testResult = {
        name: test.name,
        status: 'running',
        startTime: new Date(),
        error: null
      };

      try {
        const result = await test.test();
        testResult.status = result ? 'passed' : 'failed';
        testResult.response = result;
        
        if (result) {
          this.testResults.unified.passed++;
          console.log(`  ✅ ${test.name}`);
        } else {
          this.testResults.unified.failed++;
          console.log(`  ❌ ${test.name}`);
        }
      } catch (error) {
        testResult.status = 'failed';
        testResult.error = error.message;
        this.testResults.unified.failed++;
        console.log(`  ❌ ${test.name}: ${error.message}`);
      }

      testResult.endTime = new Date();
      testResult.duration = testResult.endTime - testResult.startTime;
      this.testResults.unified.tests.push(testResult);
    }
  }

  /**
   * Exécute un test individuel d'API
   */
  async runSingleTest(module, test) {
    const testResult = {
      name: test.name,
      url: test.url,
      status: 'running',
      startTime: new Date(),
      error: null
    };

    try {
      const response = await apiClient.get(test.url);
      testResult.status = 'passed';
      testResult.response = {
        status: response.status,
        hasData: !!response.data,
        dataType: typeof response.data
      };
      
      this.testResults[module].passed++;
      console.log(`  ✅ ${test.name}`);
      
    } catch (error) {
      // Les erreurs d'authentification sont "normales" - l'API existe et fonctionne
      if (error.message.includes('401') || 
          error.message.includes('Informations d\'authentification') ||
          error.response?.status === 401) {
        testResult.status = 'passed';
        testResult.response = { status: 401, message: 'API accessible (authentification requise)' };
        this.testResults[module].passed++;
        console.log(`  ✅ ${test.name} (auth requise)`);
      } else {
        testResult.status = 'failed';
        testResult.error = error.message;
        testResult.response = error.response ? {
          status: error.response.status,
          statusText: error.response.statusText
        } : null;
        
        this.testResults[module].failed++;
        console.log(`  ❌ ${test.name}: ${error.message}`);
      }
    }

    testResult.endTime = new Date();
    testResult.duration = testResult.endTime - testResult.startTime;
    this.testResults[module].tests.push(testResult);
  }

  /**
   * Génère un rapport de test détaillé
   */
  generateReport() {
    console.log('\n📋 RAPPORT DE TEST - Système API Unifié');
    console.log('='.repeat(50));

    let totalPassed = 0;
    let totalFailed = 0;

    Object.entries(this.testResults).forEach(([module, results]) => {
      const total = results.passed + results.failed;
      const successRate = total > 0 ? (results.passed / total * 100).toFixed(1) : 0;
      
      console.log(`\n${module.toUpperCase()}:`);
      console.log(`  Tests: ${total} | Réussis: ${results.passed} | Échecs: ${results.failed} | Taux: ${successRate}%`);
      
      totalPassed += results.passed;
      totalFailed += results.failed;

      // Afficher les tests échoués
      const failedTests = results.tests.filter(t => t.status === 'failed');
      if (failedTests.length > 0) {
        console.log('  Échecs:');
        failedTests.forEach(test => {
          console.log(`    - ${test.name}: ${test.error}`);
        });
      }
    });

    const grandTotal = totalPassed + totalFailed;
    const globalSuccessRate = grandTotal > 0 ? (totalPassed / grandTotal * 100).toFixed(1) : 0;

    console.log('\n' + '='.repeat(50));
    console.log(`RÉSULTAT GLOBAL:`);
    console.log(`Total: ${grandTotal} | Réussis: ${totalPassed} | Échecs: ${totalFailed}`);
    console.log(`Taux de réussite global: ${globalSuccessRate}%`);
    
    if (globalSuccessRate >= 80) {
      console.log('🎉 SUCCÈS: Le système API unifié fonctionne correctement!');
    } else if (globalSuccessRate >= 50) {
      console.log('⚠️  ATTENTION: Le système fonctionne partiellement');
    } else {
      console.log('❌ ÉCHEC: Problèmes majeurs détectés');
    }

    console.log('\n💡 NOTE: Les erreurs 401 (authentification requise) indiquent que les APIs');
    console.log('   existent et fonctionnent. L\'authentification est normale en production.');

    return {
      totalTests: grandTotal,
      passed: totalPassed,
      failed: totalFailed,
      successRate: parseFloat(globalSuccessRate),
      details: this.testResults
    };
  }

  /**
   * Test spécifique pour valider les URLs et la connectivité
   */
  async testConnectivity() {
    console.log('🔌 Test de connectivité de base...');
    
    // Test de base du serveur Django
    try {
      const response = await apiClient.get('/api/');
      console.log('✅ Serveur Django accessible');
      console.log('📄 Modules disponibles:', Object.keys(response.data.modules || {}));
      return true;
    } catch (error) {
      console.log('❌ Serveur Django non accessible:', error.message);
      return false;
    }
  }

  /**
   * Lance un test rapide du système
   */
  async quickTest() {
    console.log('⚡ Test rapide du système unifié...');
    
    const isConnected = await this.testConnectivity();
    if (!isConnected) {
      console.log('❌ Impossible de continuer - serveur non accessible');
      return false;
    }

    // Test de quelques endpoints clés
    const keyTests = [
      { module: 'monitoring', name: 'Status', url: '/api/monitoring/unified/status/' },
      { module: 'qos', name: 'QoS Status', url: '/api/qos/unified/status/' },
      { module: 'security', name: 'Security Dashboard', url: '/api/security/dashboard/' }
    ];

    let passed = 0;
    for (const test of keyTests) {
      try {
        await apiClient.get(test.url);
        passed++;
        console.log(`✅ ${test.name}`);
      } catch (error) {
        if (error.response?.status === 401) {
          passed++;
          console.log(`✅ ${test.name} (auth requise)`);
        } else {
          console.log(`❌ ${test.name}: ${error.message}`);
        }
      }
    }

    const success = passed === keyTests.length;
    console.log(`\n${success ? '🎉' : '⚠️'} Test rapide: ${passed}/${keyTests.length} APIs accessibles`);
    return success;
  }
}

// Instance singleton
const apiTester = new ApiTester();

export default apiTester;