#!/usr/bin/env node
/**
 * Script de test pour l'architecture API centralisée
 * Valide la cohérence des données et la connectivité des services
 */

import axios from 'axios';

const BASE_URL = 'http://localhost:8000';
const CREDENTIALS = { username: 'admin', password: 'admin123' };

// Configuration des endpoints à tester
const ENDPOINTS_TO_TEST = {
  dashboard: '/api/dashboard/',
  devices: '/api/network/devices/',
  discovery: '/api/network/discovery/', 
  gns3_projects: '/api/gns3_integration/projects/',
  gns3_servers: '/api/gns3_integration/servers/',
  monitoring_alerts: '/api/monitoring/alerts/',
  monitoring_status: '/api/monitoring/status/',
  qos_policies: '/api/qos/policies/'
};

// Créer un client axios avec authentification
const apiClient = axios.create({
  baseURL: BASE_URL,
  auth: CREDENTIALS,
  timeout: 10000
});

/**
 * Tester la connectivité de tous les endpoints
 */
async function testConnectivity() {
  console.log('🔍 Test de connectivité des endpoints...\n');
  
  const results = {};
  
  for (const [name, endpoint] of Object.entries(ENDPOINTS_TO_TEST)) {
    try {
      const startTime = Date.now();
      const response = await apiClient.get(endpoint);
      const responseTime = Date.now() - startTime;
      
      results[name] = {
        success: true,
        status: response.status,
        responseTime: `${responseTime}ms`,
        dataSize: JSON.stringify(response.data).length,
        hasData: !!response.data && (Array.isArray(response.data) ? response.data.length > 0 : Object.keys(response.data).length > 0)
      };
      
      console.log(`✅ ${name}: ${response.status} (${responseTime}ms) - ${results[name].hasData ? 'Avec données' : 'Vide'}`);
      
    } catch (error) {
      results[name] = {
        success: false,
        error: error.response?.status || error.code,
        message: error.message
      };
      
      console.log(`❌ ${name}: ${error.response?.status || error.code} - ${error.message}`);
    }
  }
  
  return results;
}

/**
 * Tester la cohérence des données équipements
 */
async function testEquipmentDataConsistency() {
  console.log('\n📊 Test de cohérence des données équipements...\n');
  
  try {
    // Récupérer les données de toutes les sources
    const [dashboardRes, devicesRes, discoveryRes, gns3ProjectsRes] = await Promise.allSettled([
      apiClient.get('/api/dashboard/'),
      apiClient.get('/api/network/devices/'),
      apiClient.get('/api/network/discovery/'),
      apiClient.get('/api/gns3_integration/projects/')
    ]);
    
    let totalEquipment = 0;
    let onlineEquipment = 0;
    let sources = [];
    
    // Dashboard data
    if (dashboardRes.status === 'fulfilled') {
      const dashboard = dashboardRes.value.data;
      console.log(`📈 Dashboard: ${dashboard.total_devices || 0} équipements totaux, ${dashboard.active_devices || 0} actifs`);
      sources.push('dashboard');
    }
    
    // Network devices 
    if (devicesRes.status === 'fulfilled') {
      const devices = devicesRes.value.data.results || devicesRes.value.data || [];
      const activeDevices = Array.isArray(devices) ? devices.filter(d => d.is_active || d.status === 'active').length : 0;
      console.log(`🖥️  Network Devices: ${devices.length || 0} équipements, ${activeDevices} actifs`);
      totalEquipment += devices.length || 0;
      onlineEquipment += activeDevices;
      sources.push('devices');
    }
    
    // Discovery results
    if (discoveryRes.status === 'fulfilled') {
      const discovered = discoveryRes.value.data.results || discoveryRes.value.data || [];
      const onlineDiscovered = Array.isArray(discovered) ? discovered.filter(d => d.is_online || d.status === 'online').length : 0;
      console.log(`🔍 Discovery: ${discovered.length || 0} équipements découverts, ${onlineDiscovered} en ligne`);
      totalEquipment += discovered.length || 0;
      onlineEquipment += onlineDiscovered;
      sources.push('discovery');
    }
    
    // GNS3 projects
    if (gns3ProjectsRes.status === 'fulfilled') {
      const projects = gns3ProjectsRes.value.data.results || gns3ProjectsRes.value.data || [];
      let gns3Nodes = 0;
      let activeGns3Nodes = 0;
      
      if (Array.isArray(projects)) {
        for (const project of projects) {
          if (project.status === 'opened' && project.nodes) {
            gns3Nodes += project.nodes.length;
            activeGns3Nodes += project.nodes.filter(n => n.status === 'started').length;
          }
        }
      }
      
      console.log(`🔬 GNS3: ${projects.length || 0} projets, ${gns3Nodes} nœuds totaux, ${activeGns3Nodes} actifs`);
      totalEquipment += gns3Nodes;
      onlineEquipment += activeGns3Nodes;
      sources.push('gns3');
    }
    
    console.log(`\n📋 Résumé consolidé:`);
    console.log(`   Total équipements: ${totalEquipment}`);
    console.log(`   Équipements en ligne: ${onlineEquipment}`);
    console.log(`   Sources actives: ${sources.join(', ')}`);
    
    // Validation
    if (totalEquipment > 0) {
      console.log(`✅ Problème "0 équipements" résolu - ${totalEquipment} équipements détectés`);
    } else {
      console.log(`⚠️  Attention: Toujours 0 équipements détectés`);
    }
    
    return {
      totalEquipment,
      onlineEquipment,
      sources,
      resolved: totalEquipment > 0
    };
    
  } catch (error) {
    console.error(`❌ Erreur test cohérence équipements:`, error.message);
    return { error: error.message };
  }
}

/**
 * Tester les données temps réel
 */
async function testRealtimeCapabilities() {
  console.log('\n⚡ Test des capacités temps réel...\n');
  
  try {
    // Tester différentes requêtes pour voir les variations
    console.log('📡 Test de variabilité des données (3 requêtes espacées)...');
    
    const samples = [];
    for (let i = 0; i < 3; i++) {
      const timestamp = new Date().toISOString();
      const response = await apiClient.get('/api/dashboard/');
      
      samples.push({
        timestamp,
        totalDevices: response.data.total_devices,
        activeDevices: response.data.active_devices,
        cpuUsage: response.data.system_health?.cpu_usage || 0,
        memoryUsage: response.data.system_health?.memory_usage || 0
      });
      
      console.log(`   Échantillon ${i + 1}: ${samples[i].totalDevices} équipements, CPU: ${samples[i].cpuUsage}%`);
      
      if (i < 2) await new Promise(resolve => setTimeout(resolve, 2000)); // 2s entre les requêtes
    }
    
    // Analyser les variations
    const variations = {
      devices: new Set(samples.map(s => s.totalDevices)).size > 1,
      cpu: new Set(samples.map(s => s.cpuUsage)).size > 1,
      memory: new Set(samples.map(s => s.memoryUsage)).size > 1
    };
    
    console.log(`\n📈 Analyse des variations:`);
    console.log(`   Équipements: ${variations.devices ? '✅ Variable' : '⚪ Stable'}`);
    console.log(`   CPU: ${variations.cpu ? '✅ Variable' : '⚪ Stable'}`); 
    console.log(`   Mémoire: ${variations.memory ? '✅ Variable' : '⚪ Stable'}`);
    
    return { samples, variations };
    
  } catch (error) {
    console.error(`❌ Erreur test temps réel:`, error.message);
    return { error: error.message };
  }
}

/**
 * Fonction principale de test
 */
async function runTests() {
  console.log(`🚀 Test de l'Architecture API Centralisée`);
  console.log(`   Backend: ${BASE_URL}`);
  console.log(`   Utilisateur: ${CREDENTIALS.username}`);
  console.log(`   Timestamp: ${new Date().toISOString()}\n`);
  
  const results = {};
  
  // Test 1: Connectivité
  results.connectivity = await testConnectivity();
  
  // Test 2: Cohérence des données
  results.dataConsistency = await testEquipmentDataConsistency();
  
  // Test 3: Capacités temps réel
  results.realtime = await testRealtimeCapabilities();
  
  // Résumé final
  console.log(`\n🏁 Résumé des Tests`);
  console.log(`================`);
  
  const connectivityScore = Object.values(results.connectivity).filter(r => r.success).length;
  const totalEndpoints = Object.keys(results.connectivity).length;
  console.log(`📡 Connectivité: ${connectivityScore}/${totalEndpoints} endpoints OK`);
  
  if (results.dataConsistency.resolved) {
    console.log(`📊 Cohérence: ✅ Problème équipements résolu (${results.dataConsistency.totalEquipment} équipements)`);
  } else if (results.dataConsistency.error) {
    console.log(`📊 Cohérence: ❌ Erreur - ${results.dataConsistency.error}`);
  } else {
    console.log(`📊 Cohérence: ⚠️  Problème équipements non résolu`);
  }
  
  if (results.realtime.error) {
    console.log(`⚡ Temps réel: ❌ Erreur - ${results.realtime.error}`);
  } else {
    const variableCount = Object.values(results.realtime.variations).filter(Boolean).length;
    console.log(`⚡ Temps réel: ${variableCount > 0 ? '✅' : '⚪'} ${variableCount}/3 métriques variables`);
  }
  
  // Score global
  let globalScore = 0;
  globalScore += connectivityScore / totalEndpoints * 40; // 40% pour connectivité
  globalScore += (results.dataConsistency.resolved ? 40 : 0); // 40% pour cohérence
  globalScore += (!results.realtime.error ? 20 : 0); // 20% pour temps réel
  
  console.log(`\n🎯 Score Global: ${Math.round(globalScore)}%`);
  
  if (globalScore >= 80) {
    console.log(`✅ Architecture VALIDÉE - Prête pour production`);
  } else if (globalScore >= 60) {
    console.log(`⚠️  Architecture FONCTIONNELLE - Améliorations recommandées`);
  } else {
    console.log(`❌ Architecture NON VALIDÉE - Corrections nécessaires`);
  }
  
  return results;
}

// Exécuter les tests
runTests().catch(error => {
  console.error('❌ Erreur fatale:', error);
  process.exit(1);
});