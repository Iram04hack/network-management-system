/**
 * Script de test automatique de connexion Frontend ↔ Backend
 * Usage: import { runConnectionTests } from './utils/connectionTest.js'
 */

import { aiAssistantService } from '../services/aiAssistantService.js';

export class ConnectionTester {
    constructor() {
        this.results = [];
        this.onProgress = null;
        this.onComplete = null;
    }

    log(level, message, data = null) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            level,
            message,
            data,
        };
        
        this.results.push(logEntry);
        console.log(`[${level.toUpperCase()}] ${message}`, data || '');
        
        if (this.onProgress) {
            this.onProgress(logEntry);
        }
    }

    async testEndpoint(name, testFunction, description) {
        this.log('info', `🔄 Test: ${description}`);
        const startTime = Date.now();
        
        try {
            const result = await testFunction();
            const duration = Date.now() - startTime;
            
            this.log('success', `✅ ${name} - Succès (${duration}ms)`, result);
            return { success: true, result, duration };
        } catch (error) {
            const duration = Date.now() - startTime;
            
            this.log('error', `❌ ${name} - Erreur (${duration}ms)`, {
                message: error.message,
                stack: error.stack,
                name: error.name
            });
            
            return { success: false, error: error.message, duration };
        }
    }

    async runAllTests() {
        this.log('info', '🚀 Début des tests de connexion Frontend ↔ Backend');
        this.results = [];
        
        const tests = [
            {
                name: 'Conversations',
                description: 'Récupération des conversations',
                test: () => aiAssistantService.getConversations({ page: 1, page_size: 5 })
            },
            {
                name: 'CreateConversation',
                description: 'Création d\'une nouvelle conversation',
                test: () => aiAssistantService.createConversation({
                    title: 'Test Frontend Connection',
                    metadata: { source: 'frontend_test', timestamp: new Date().toISOString() }
                })
            },
            {
                name: 'Messages',
                description: 'Récupération des messages',
                test: () => aiAssistantService.getMessages({ page: 1, page_size: 5 })
            },
            {
                name: 'Documents',
                description: 'Récupération des documents',
                test: () => aiAssistantService.getDocuments({ page: 1, page_size: 5 })
            },
            {
                name: 'Commands',
                description: 'Récupération des commandes',
                test: () => aiAssistantService.getCommands()
            },
            {
                name: 'ExecuteCommand',
                description: 'Exécution d\'une commande test',
                test: () => aiAssistantService.executeCommand({
                    name: 'test_frontend_connection',
                    parameters: { source: 'frontend', timestamp: new Date().toISOString() }
                })
            },
            {
                name: 'Search',
                description: 'Recherche globale',
                test: () => aiAssistantService.search({ q: 'test', limit: 5 })
            },
            {
                name: 'NetworkAnalysis',
                description: 'Analyse réseau',
                test: () => aiAssistantService.analyzeNetwork({
                    target: '127.0.0.1',
                    analysis_type: 'ping'
                })
            }
        ];

        const testResults = [];
        
        for (const [index, test] of tests.entries()) {
            this.log('info', `📋 Test ${index + 1}/${tests.length}: ${test.name}`);
            
            const result = await this.testEndpoint(
                test.name,
                test.test,
                test.description
            );
            
            testResults.push({
                name: test.name,
                description: test.description,
                ...result
            });
            
            // Pause entre les tests
            await new Promise(resolve => setTimeout(resolve, 500));
        }
        
        // Résumé final
        const successCount = testResults.filter(r => r.success).length;
        const totalCount = testResults.length;
        const successRate = ((successCount / totalCount) * 100).toFixed(1);
        
        this.log('info', `📊 Résumé des tests:`);
        this.log('info', `   Réussis: ${successCount}/${totalCount} (${successRate}%)`);
        this.log('info', `   Échoués: ${totalCount - successCount}/${totalCount}`);
        
        if (successCount === totalCount) {
            this.log('success', '🎉 Tous les tests sont passés ! La connexion est fonctionnelle.');
        } else {
            this.log('warning', '⚠️ Certains tests ont échoué. Vérifiez la configuration.');
        }
        
        const summary = {
            totalTests: totalCount,
            successfulTests: successCount,
            failedTests: totalCount - successCount,
            successRate: parseFloat(successRate),
            results: testResults,
            logs: this.results
        };
        
        if (this.onComplete) {
            this.onComplete(summary);
        }
        
        return summary;
    }

    // Méthode pour tester un seul endpoint
    async testSingleEndpoint(endpointName) {
        const endpointTests = {
            conversations: () => aiAssistantService.getConversations(),
            messages: () => aiAssistantService.getMessages(),
            documents: () => aiAssistantService.getDocuments(),
            commands: () => aiAssistantService.getCommands(),
            search: () => aiAssistantService.search({ q: 'test' }),
            networkAnalysis: () => aiAssistantService.analyzeNetwork({ target: '127.0.0.1', analysis_type: 'ping' })
        };
        
        if (!endpointTests[endpointName]) {
            throw new Error(`Endpoint inconnu: ${endpointName}`);
        }
        
        return await this.testEndpoint(
            endpointName,
            endpointTests[endpointName],
            `Test de l'endpoint ${endpointName}`
        );
    }
}

// Instance globale
export const connectionTester = new ConnectionTester();

// Fonction d'aide pour les tests rapides
export async function runConnectionTests(options = {}) {
    const tester = new ConnectionTester();
    
    if (options.onProgress) {
        tester.onProgress = options.onProgress;
    }
    
    if (options.onComplete) {
        tester.onComplete = options.onComplete;
    }
    
    return await tester.runAllTests();
}

// Fonction pour tester depuis la console du navigateur
export function testFromConsole() {
    console.log('🔗 Démarrage des tests de connexion...');
    console.log('Utilisez: await testFromConsole() dans la console');
    
    const tester = new ConnectionTester();
    tester.onProgress = (log) => {
        const emoji = log.level === 'error' ? '❌' : log.level === 'success' ? '✅' : 'ℹ️';
        console.log(`${emoji} ${log.message}`, log.data || '');
    };
    
    return tester.runAllTests();
}

// Export par défaut
export default ConnectionTester;