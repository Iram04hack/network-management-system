/**
 * Script de test pour vérifier l'intégration API Dashboard
 */

import unifiedDashboardService from './src/services/unifiedDashboardService.js';

async function testApiIntegration() {
  console.log('🚀 Test d\'intégration API Dashboard - Démarrage...\n');

  try {
    // Test 1: Connectivité de base
    console.log('1️⃣ Test de connectivité de base...');
    const connectivityTest = await unifiedDashboardService.testConnection();
    
    if (connectivityTest.success) {
      console.log(`✅ Connectivité OK - Temps de réponse: ${connectivityTest.responseTime}ms`);
    } else {
      console.log(`❌ Échec connectivité: ${connectivityTest.error.userMessage}`);
      return;
    }

    // Test 2: Récupération des données dashboard
    console.log('\n2️⃣ Test récupération données dashboard...');
    const dashboardData = await unifiedDashboardService.getDashboardData();
    
    if (dashboardData.success) {
      console.log(`✅ Données dashboard OK - ${Object.keys(dashboardData.data).length} sections`);
      console.log(`   - GNS3 Projects: ${dashboardData.data.gns3_projects?.length || 0}`);
      console.log(`   - GNS3 Nodes: ${dashboardData.data.gns3_nodes?.length || 0}`);
      console.log(`   - Docker Services: ${Object.keys(dashboardData.data.docker_services?.services_status || {}).length}`);
    } else {
      console.log(`❌ Échec données dashboard: ${dashboardData.error.userMessage}`);
    }

    // Test 3: Santé système
    console.log('\n3️⃣ Test santé système...');
    const systemHealth = await unifiedDashboardService.getSystemHealth();
    
    if (systemHealth.success) {
      console.log(`✅ Santé système OK - ${Object.keys(systemHealth.data).length} sources`);
    } else {
      console.log(`❌ Échec santé système: ${systemHealth.error.userMessage}`);
    }

    // Test 4: Réseau
    console.log('\n4️⃣ Test données réseau...');
    const networkSummary = await unifiedDashboardService.getNetworkSummary();
    
    if (networkSummary.success) {
      console.log(`✅ Données réseau OK`);
      console.log(`   - Projets GNS3: ${networkSummary.data.gns3_projects?.length || 0}`);
      console.log(`   - Nœuds actifs: ${networkSummary.data.gns3_nodes?.filter(n => n.status === 'started')?.length || 0}`);
    } else {
      console.log(`❌ Échec données réseau: ${networkSummary.error.userMessage}`);
    }

    // Test 5: Alertes
    console.log('\n5️⃣ Test alertes...');
    const alerts = await unifiedDashboardService.getAlerts();
    
    if (alerts.success) {
      console.log(`✅ Alertes OK - ${alerts.data.length} alertes formatées`);
    } else {
      console.log(`❌ Échec alertes: ${alerts.error.userMessage}`);
    }

    // Test 6: Cache
    console.log('\n6️⃣ Test du cache...');
    const cachedData = await unifiedDashboardService.getDashboardData(false); // Utiliser cache
    
    if (cachedData.success) {
      console.log(`✅ Cache OK`);
    }

    // Statistiques finales
    console.log('\n📊 Statistiques du service:');
    const stats = unifiedDashboardService.getStats();
    console.log(`   - Total requêtes: ${stats.totalRequests}`);
    console.log(`   - Cache hits: ${stats.cacheHits}`);
    console.log(`   - Taux de cache: ${stats.cacheHitRate}%`);
    console.log(`   - Erreurs: ${stats.errors}`);

    console.log('\n🎉 Tous les tests sont passés ! L\'intégration API est fonctionnelle.');

  } catch (error) {
    console.error('\n💥 Erreur lors des tests:', error.message);
    console.error(error.stack);
  }
}

// Exécuter les tests si le script est lancé directement
if (import.meta.url === `file://${process.argv[1]}`) {
  testApiIntegration().then(() => process.exit(0)).catch(err => {
    console.error('Erreur fatale:', err);
    process.exit(1);
  });
}

export default testApiIntegration;