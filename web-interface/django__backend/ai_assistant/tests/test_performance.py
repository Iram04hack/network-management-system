"""
Tests de performance pour le module AI Assistant.

Ce module contient des tests qui évaluent les performances du module AI Assistant
après les corrections apportées dans la Phase 1. 

Note: Ces tests sont marqués avec le décorateur pytest.mark.performance et peuvent
être exécutés séparément avec la commande:
    pytest -m performance
"""

import pytest
import time
import statistics
from unittest.mock import patch, MagicMock
from django.test import TestCase

from ai_assistant.infrastructure.ai_client_impl import DefaultAIClient
from ai_assistant.infrastructure.knowledge_base_impl import ElasticsearchKnowledgeBase
from ai_assistant.infrastructure.command_executor_impl import SafeCommandExecutor
from ai_assistant.infrastructure.repositories import DjangoAIAssistantRepository
from ai_assistant.application.ai_assistant_service import AIAssistantService
from ai_assistant.domain.models import Message, MessageRole
from ai_assistant.domain.exceptions import AIClientException, KnowledgeBaseException


@pytest.mark.performance
class TestAIClientPerformance(TestCase):
    """Tests de performance pour le client AI."""

    def setUp(self):
        """Configuration initiale des tests de performance."""
        self.client = DefaultAIClient()
        # Configuration du mock pour éviter les appels réels à l'API
        self.client.openai_client = MagicMock()
        self.client.openai_client.chat.completions.create.return_value = MagicMock(
            id="test-id",
            choices=[
                MagicMock(
                    message=MagicMock(
                        content="Réponse simulée pour tests de performance"
                    ),
                    finish_reason="stop"
                )
            ]
        )
        self.client.model_config = MagicMock(
            provider="openai",
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=500
        )

    def test_response_generation_performance(self):
        """Teste la performance de génération de réponses."""
        # Préparer un message de test
        message = "Ceci est un message de test pour évaluer les performances."
        
        # Exécuter plusieurs fois pour mesurer les performances
        execution_times = []
        num_executions = 10
        
        for _ in range(num_executions):
            start_time = time.time()
            _ = self.client.generate_response(message)
            end_time = time.time()
            execution_times.append(end_time - start_time)
        
        # Calculer les statistiques
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Vérifier que le temps moyen est acceptable (moins de 50ms pour un mock)
        # Cette valeur devra être ajustée en fonction des performances réelles de l'environnement
        self.assertLess(avg_time, 0.05, 
                      f"Performance insuffisante: temps moyen {avg_time:.4f}s > 0.05s")
        
        print(f"Stats de performance du client AI:")
        print(f"  Temps moyen: {avg_time:.4f}s")
        print(f"  Temps min: {min_time:.4f}s")
        print(f"  Temps max: {max_time:.4f}s")

    def test_concurrent_requests_simulation(self):
        """Simule des requêtes concurrentes pour tester la robustesse."""
        import threading
        
        # Nombre de requêtes concurrentes à simuler
        num_concurrent = 5
        success_count = 0
        lock = threading.Lock()
        
        def execute_request():
            nonlocal success_count
            try:
                _ = self.client.generate_response("Test de concurrence")
                with lock:
                    success_count += 1
            except Exception:
                pass
        
        # Créer et démarrer les threads
        threads = []
        for _ in range(num_concurrent):
            thread = threading.Thread(target=execute_request)
            threads.append(thread)
            thread.start()
        
        # Attendre que tous les threads terminent
        for thread in threads:
            thread.join()
        
        # Vérifier que toutes les requêtes ont réussi
        self.assertEqual(success_count, num_concurrent, 
                        f"Seulement {success_count}/{num_concurrent} requêtes ont réussi")


@pytest.mark.performance
class TestKnowledgeBasePerformance(TestCase):
    """Tests de performance pour la base de connaissances."""

    def setUp(self):
        """Configuration initiale des tests de performance."""
        self.kb = ElasticsearchKnowledgeBase()
        # Configuration du mock
        self.kb.client = MagicMock()
        self.kb.client.search.return_value = {
            "took": 5,
            "hits": {
                "total": {"value": 2},
                "max_score": 0.9,
                "hits": [
                    {
                        "_score": 0.9,
                        "_source": {"content": "Document 1", "metadata": {"source": "test"}}
                    },
                    {
                        "_score": 0.8,
                        "_source": {"content": "Document 2", "metadata": {"source": "test"}}
                    }
                ]
            }
        }

    def test_search_performance(self):
        """Teste la performance des recherches dans la base de connaissances."""
        # Requête de test
        query = "Requête de test pour performance"
        
        # Exécuter plusieurs fois pour mesurer les performances
        execution_times = []
        num_executions = 10
        
        for _ in range(num_executions):
            start_time = time.time()
            _ = self.kb.search(query)
            end_time = time.time()
            execution_times.append(end_time - start_time)
        
        # Calculer les statistiques
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Vérifier que le temps moyen est acceptable (moins de 20ms pour un mock)
        self.assertLess(avg_time, 0.02, 
                      f"Performance insuffisante: temps moyen {avg_time:.4f}s > 0.02s")
        
        print(f"Stats de performance de la base de connaissances:")
        print(f"  Temps moyen: {avg_time:.4f}s")
        print(f"  Temps min: {min_time:.4f}s")
        print(f"  Temps max: {max_time:.4f}s")

    def test_search_with_different_thresholds(self):
        """Teste l'impact des différents seuils sur les performances."""
        query = "Test des seuils"
        thresholds = [0.1, 0.5, 0.7, 0.9]
        
        for threshold in thresholds:
            start_time = time.time()
            results = self.kb.search(query, threshold=threshold)
            end_time = time.time()
            
            # Le nombre de résultats doit varier en fonction du seuil
            # Pour notre mock, nous devons adapter manuellement le comportement
            expected_count = 0
            for hit in self.kb.client.search.return_value["hits"]["hits"]:
                if hit["_score"] >= threshold:
                    expected_count += 1
            
            self.assertEqual(len(results), expected_count, 
                          f"Nombre incorrect de résultats pour seuil={threshold}")
            
            print(f"Seuil {threshold}: temps={end_time-start_time:.4f}s, résultats={len(results)}")


@pytest.mark.performance
class TestCommandExecutorPerformance(TestCase):
    """Tests de performance pour l'exécuteur de commandes."""

    def setUp(self):
        """Configuration initiale des tests de performance."""
        self.executor = SafeCommandExecutor()
    
    @patch('subprocess.run')
    def test_command_execution_performance(self, mock_run):
        """Teste la performance d'exécution de commandes."""
        # Configurer le mock
        mock_run.return_value = MagicMock(
            stdout=b"Sortie de test",
            stderr=b"",
            returncode=0
        )
        
        # Commande de test
        command = "echo 'test'"
        command_type = "system_info"
        user_id = 1
        
        # Exécuter plusieurs fois pour mesurer les performances
        execution_times = []
        num_executions = 10
        
        for _ in range(num_executions):
            start_time = time.time()
            _ = self.executor.execute(command, command_type, user_id)
            end_time = time.time()
            execution_times.append(end_time - start_time)
        
        # Calculer les statistiques
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Vérifier que le temps moyen est acceptable (moins de 10ms pour un mock)
        self.assertLess(avg_time, 0.01, 
                      f"Performance insuffisante: temps moyen {avg_time:.4f}s > 0.01s")
        
        print(f"Stats de performance de l'exécuteur de commandes:")
        print(f"  Temps moyen: {avg_time:.4f}s")
        print(f"  Temps min: {min_time:.4f}s")
        print(f"  Temps max: {max_time:.4f}s")


@pytest.mark.performance
class TestServiceIntegrationPerformance(TestCase):
    """Tests de performance pour le service AI Assistant complet."""

    def setUp(self):
        """Configuration initiale des tests de performance."""
        # Créer des mocks pour toutes les dépendances
        self.ai_client = MagicMock()
        self.ai_client.generate_response.return_value = "Réponse de test"
        
        self.kb = MagicMock()
        self.kb.search.return_value = [
            {"content": "Document 1", "metadata": {"source": "test"}},
            {"content": "Document 2", "metadata": {"source": "test"}}
        ]
        
        self.command_executor = MagicMock()
        self.command_executor.execute.return_value = {"stdout": "Sortie de test", "stderr": "", "returncode": 0}
        self.command_executor.validate.return_value = True
        
        self.repository = MagicMock()
        self.repository.create_conversation.return_value = {"id": "test-conv-id", "title": "Test", "user_id": 1}
        self.repository.add_message.return_value = {"id": "test-msg-id", "content": "Test", "role": "user"}
        self.repository.get_conversation_messages.return_value = [
            {"id": "msg1", "content": "Bonjour", "role": "user"},
            {"id": "msg2", "content": "Bonjour! Comment puis-je vous aider?", "role": "assistant"}
        ]
        
        # Créer le service avec les mocks
        self.service = AIAssistantService(self.ai_client, self.kb, self.command_executor, self.repository)

    def test_message_processing_performance(self):
        """Teste la performance du traitement des messages."""
        # Paramètres de test
        conversation_id = "test-conv-id"
        user_id = 1
        message_content = "Comment fonctionne cette application?"
        
        # Exécuter plusieurs fois pour mesurer les performances
        execution_times = []
        num_executions = 5
        
        for _ in range(num_executions):
            start_time = time.time()
            _ = self.service.process_message(conversation_id, user_id, message_content)
            end_time = time.time()
            execution_times.append(end_time - start_time)
        
        # Calculer les statistiques
        avg_time = statistics.mean(execution_times)
        max_time = max(execution_times)
        min_time = min(execution_times)
        
        # Vérifier que le temps moyen est acceptable (moins de 100ms pour un mock complet)
        self.assertLess(avg_time, 0.1, 
                      f"Performance insuffisante: temps moyen {avg_time:.4f}s > 0.1s")
        
        print(f"Stats de performance du service AI Assistant complet:")
        print(f"  Temps moyen: {avg_time:.4f}s")
        print(f"  Temps min: {min_time:.4f}s")
        print(f"  Temps max: {max_time:.4f}s")

    def test_command_processing_performance(self):
        """Teste la performance du traitement des commandes."""
        # Paramètres de test
        conversation_id = "test-conv-id"
        user_id = 1
        command = "echo 'test'"
        command_type = "system_info"
        
        # Exécuter plusieurs fois pour mesurer les performances
        execution_times = []
        num_executions = 5
        
        for _ in range(num_executions):
            start_time = time.time()
            _ = self.service.execute_command(conversation_id, user_id, command, command_type)
            end_time = time.time()
            execution_times.append(end_time - start_time)
        
        # Calculer les statistiques
        avg_time = statistics.mean(execution_times)
        
        # Vérifier que le temps moyen est acceptable (moins de 50ms pour un mock)
        self.assertLess(avg_time, 0.05, 
                      f"Performance insuffisante: temps moyen {avg_time:.4f}s > 0.05s")
        
        print(f"Stats de performance de l'exécution de commandes via service:")
        print(f"  Temps moyen: {avg_time:.4f}s")


if __name__ == '__main__':
    pytest.main(['-v', '-m', 'performance'])