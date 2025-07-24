/**
 * SystemTest - Page de test du système simplifié
 * 
 * Interface pour tester les APIs basiques sans système unifié
 */

import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CheckCircle, 
  XCircle, 
  AlertCircle, 
  RefreshCw,
  Play,
  Monitor,
  Shield,
  Network,
  Server,
  Database,
  Zap
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const SystemTest = () => {
  const { getThemeClasses } = useTheme();
  
  // État des tests mockés
  const [testResults, setTestResults] = useState(null);
  const [isRunningTests, setIsRunningTests] = useState(false);
  const [quickTestResult, setQuickTestResult] = useState(null);
  const [isRunningQuickTest, setIsRunningQuickTest] = useState(false);

  // Données mockées pour les tests
  const mockSystemData = {
    systemMetrics: {
      cpu: { current: 45 },
      memory: { current: 67 },
      network: { current: 123 }
    },
    totalGns3Projects: 5,
    totalDockerServices: 8,
    healthyDockerServices: 7,
    qosAvailable: true,
    securityAvailable: true,
    systemOperational: true,
    isSystemHealthy: true,
    isLoading: false,
    hasErrors: false,
    errors: {}
  };

  // Simulation d'un test rapide
  const runQuickTest = async () => {
    setIsRunningQuickTest(true);
    
    // Simulation d'un délai
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setQuickTestResult({
      success: true,
      timestamp: new Date().toISOString(),
      duration: 2000,
      endpoints: {
        dashboard: { success: true, responseTime: 145 },
        monitoring: { success: true, responseTime: 89 },
        gns3: { success: true, responseTime: 234 },
        network: { success: true, responseTime: 123 }
      }
    });
    
    setIsRunningQuickTest(false);
  };

  // Simulation d'un test complet
  const runFullTest = async () => {
    setIsRunningTests(true);
    
    // Simulation d'un délai plus long
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    setTestResults({
      success: true,
      timestamp: new Date().toISOString(),
      duration: 5000,
      categories: {
        backend: { success: true, tests: 12, passed: 12, failed: 0 },
        api: { success: true, tests: 8, passed: 8, failed: 0 },
        integration: { success: true, tests: 6, passed: 5, failed: 1 },
        performance: { success: true, tests: 4, passed: 4, failed: 0 }
      }
    });
    
    setIsRunningTests(false);
  };

  return (
    <div className="p-6 space-y-6">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`${getThemeClasses('text', 'dashboard')} text-3xl font-bold`}>
            Tests Système
          </h1>
          <p className={`${getThemeClasses('textSecondary', 'dashboard')} mt-1`}>
            Validation et test des composants système (version simplifiée)
          </p>
        </div>
      </div>

      {/* Statut système simulé */}
      <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
        <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold mb-4`}>
          Statut Système (Données Simulées)
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="flex items-center space-x-3 p-4 bg-gray-700/30 rounded">
            <Monitor className="w-8 h-8 text-blue-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>CPU</p>
              <p className="text-lg font-bold">{mockSystemData.systemMetrics.cpu.current}%</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-4 bg-gray-700/30 rounded">
            <Database className="w-8 h-8 text-green-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Mémoire</p>
              <p className="text-lg font-bold">{mockSystemData.systemMetrics.memory.current}%</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-4 bg-gray-700/30 rounded">
            <Network className="w-8 h-8 text-purple-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Projets GNS3</p>
              <p className="text-lg font-bold">{mockSystemData.totalGns3Projects}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 p-4 bg-gray-700/30 rounded">
            <Server className="w-8 h-8 text-orange-400" />
            <div>
              <p className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>Services</p>
              <p className="text-lg font-bold">
                {mockSystemData.healthyDockerServices}/{mockSystemData.totalDockerServices}
              </p>
            </div>
          </div>
        </div>
        
        <div className="mt-4 flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span>Système Opérationnel</span>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span>QoS Disponible</span>
          </div>
          <div className="flex items-center space-x-2">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <span>Sécurité Active</span>
          </div>
        </div>
      </div>

      {/* Tests rapides */}
      <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
            Test Rapide
          </h2>
          <button
            onClick={runQuickTest}
            disabled={isRunningQuickTest}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:opacity-50"
          >
            {isRunningQuickTest ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            <span>{isRunningQuickTest ? 'Test en cours...' : 'Lancer Test Rapide'}</span>
          </button>
        </div>

        {quickTestResult && (
          <div className="bg-gray-700/30 rounded p-4">
            <div className="flex items-center space-x-2 mb-3">
              <CheckCircle className="w-5 h-5 text-green-400" />
              <span className="font-medium">Test Rapide Réussi</span>
              <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                ({quickTestResult.duration}ms)
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              {Object.entries(quickTestResult.endpoints).map(([name, result]) => (
                <div key={name} className="flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span className="capitalize">{name}: {result.responseTime}ms</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Tests complets */}
      <div className={`${getThemeClasses('card', 'dashboard')} p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className={`${getThemeClasses('text', 'dashboard')} text-xl font-semibold`}>
            Test Complet
          </h2>
          <button
            onClick={runFullTest}
            disabled={isRunningTests}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors disabled:opacity-50"
          >
            {isRunningTests ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Zap className="w-4 h-4" />
            )}
            <span>{isRunningTests ? 'Test en cours...' : 'Lancer Test Complet'}</span>
          </button>
        </div>

        {testResults && (
          <div className="bg-gray-700/30 rounded p-4">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span className="font-medium">Tests Complets Réussis</span>
              </div>
              <span className={`${getThemeClasses('textSecondary', 'dashboard')} text-sm`}>
                Durée: {testResults.duration}ms
              </span>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(testResults.categories).map(([name, category]) => (
                <div key={name} className="p-3 bg-gray-800/50 rounded">
                  <div className="flex items-center space-x-2 mb-2">
                    <CheckCircle className="w-4 h-4 text-green-400" />
                    <span className="font-medium capitalize">{name}</span>
                  </div>
                  <p className="text-sm">
                    <span className="text-green-400">{category.passed}</span>
                    /{category.tests} tests
                  </p>
                  {category.failed > 0 && (
                    <p className="text-sm text-red-400">
                      {category.failed} échecs
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SystemTest;