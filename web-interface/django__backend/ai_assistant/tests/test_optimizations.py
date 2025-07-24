"""
Tests pour les optimisations de la Phase 3 du module AI Assistant.

Ce module contient les tests pour vérifier les optimisations de performance
introduites dans la Phase 3, notamment la mise en cache, le streaming et les embeddings vectoriels.
"""

import unittest
import time
import json
from unittest.mock import patch, MagicMock, AsyncMock
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path

from ai_assistant.infrastructure.ai_client_impl import DefaultAIClient
from ai_assistant.infrastructure.knowledge_base_impl import ElasticsearchKnowledgeBase
from ai_assistant.application.ai_assistant_service import AIAssistantService
from ai_assistant.consumers import AIAssistantConsumer
from ai_assistant.models import AIModel, Conversation, Message
from ai_assistant.domain.models import MessageRole


class CacheOptimizationTest(TestCase):
    """Tests pour les optimisations de mise en cache."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Vider le cache
        cache.clear()
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Créer un modèle AI
        self.ai_model = AIModel.objects.create(
            name='test-model',
            provider='openai',
            model_name='gpt-3.5-turbo',
            api_key='test-key',
            is_active=True,
            parameters={
                'temperature': 0.7,
                'max_tokens': 1000,
                'system_message': "Tu es un assistant de test."
            }
        )
        
        # Créer une conversation de test
        self.conversation = Conversation.objects.create(
            title="Test Conversation",
            user=self.user
        )
    
    @patch('ai_assistant.infrastructure.ai_client_impl.OpenAI')
    def test_response_caching(self, mock_openai):
        """Teste que les réponses sont correctement mises en cache."""
        # Configurer le mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Réponse de test"
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Créer le client AI
        ai_client = DefaultAIClient('test-key')
        
        # Premier appel - devrait appeler l'API
        response1 = ai_client.generate_response("Test message", ["context"])
        
        # Deuxième appel avec les mêmes paramètres - devrait utiliser le cache
        response2 = ai_client.generate_response("Test message", ["context"])
        
        # Vérifier que l'API n'a été appelée qu'une seule fois
        mock_client.chat.completions.create.assert_called_once()
        
        # Vérifier que les réponses sont identiques
        self.assertEqual(response1['content'], response2['content'])
        
        # Appel avec paramètres différents - devrait appeler l'API à nouveau
        ai_client.generate_response("Message différent", ["context"])
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
    
    @override_settings(AI_ASSISTANT_CACHE_ENABLED=False)
    @patch('ai_assistant.infrastructure.ai_client_impl.OpenAI')
    def test_cache_disabled(self, mock_openai):
        """Teste que le cache est correctement désactivé."""
        # Configurer le mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Réponse de test"
        mock_client.chat.completions.create.return_value = mock_completion
        
        # Créer le client AI
        ai_client = DefaultAIClient('test-key')
        
        # Premier appel
        ai_client.generate_response("Test message", ["context"])
        
        # Deuxième appel avec les mêmes paramètres - devrait appeler l'API à nouveau
        ai_client.generate_response("Test message", ["context"])
        
        # Vérifier que l'API a été appelée deux fois
        self.assertEqual(mock_client.chat.completions.create.call_count, 2)
    
    def test_cache_key_generation(self):
        """Teste la génération des clés de cache."""
        ai_client = DefaultAIClient('test-key')
        
        # Générer des clés pour différents messages et contextes
        key1 = ai_client._generate_cache_key("Message 1", ["context"])
        key2 = ai_client._generate_cache_key("Message 1", ["context"])
        key3 = ai_client._generate_cache_key("Message 2", ["context"])
        key4 = ai_client._generate_cache_key("Message 1", ["different context"])
        
        # Vérifier que les clés sont cohérentes et uniques
        self.assertEqual(key1, key2)  # Mêmes paramètres -> même clé
        self.assertNotEqual(key1, key3)  # Message différent -> clé différente
        self.assertNotEqual(key1, key4)  # Contexte différent -> clé différente


class StreamingTest(TestCase):
    """Tests pour les fonctionnalités de streaming."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Créer un modèle AI
        self.ai_model = AIModel.objects.create(
            name='test-model',
            provider='openai',
            model_name='gpt-3.5-turbo',
            api_key='test-key',
            is_active=True,
            parameters={
                'temperature': 0.7,
                'max_tokens': 1000,
                'system_message': "Tu es un assistant de test."
            }
        )
        
        # Créer une conversation de test
        self.conversation = Conversation.objects.create(
            title="Test Conversation",
            user=self.user
        )
    
    @patch('ai_assistant.infrastructure.ai_client_impl.OpenAI')
    def test_streaming_response(self, mock_openai):
        """Teste la génération de réponses en streaming."""
        # Configurer le mock pour simuler le streaming
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Simuler des chunks de réponse
        chunks = [
            MagicMock(choices=[MagicMock(delta=MagicMock(content="Bonjour"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=", "))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content="comment"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" ça"))]),
            MagicMock(choices=[MagicMock(delta=MagicMock(content=" va"))])
        ]
        mock_client.chat.completions.create.return_value = chunks
        
        # Créer le client AI
        ai_client = DefaultAIClient('test-key')
        
        # Collecter les fragments de réponse
        collected_chunks = []
        callback = lambda chunk: collected_chunks.append(chunk)
        
        # Générer la réponse en streaming
        full_response = ""
        for chunk in ai_client.generate_response_stream("Test message", ["context"], callback):
            full_response += chunk
        
        # Vérifier que tous les fragments ont été collectés
        self.assertEqual(full_response, "Bonjour, comment ça va")
        self.assertEqual(len(collected_chunks), 5)
        self.assertEqual("".join(collected_chunks), "Bonjour, comment ça va")


class EmbeddingsTest(TestCase):
    """Tests pour les fonctionnalités d'embeddings vectoriels."""
    
    @patch('ai_assistant.infrastructure.knowledge_base_impl.Elasticsearch')
    @patch('ai_assistant.infrastructure.knowledge_base_impl.OpenAI')
    def test_embedding_generation(self, mock_openai, mock_elasticsearch):
        """Teste la génération d'embeddings."""
        # Configurer les mocks
        mock_es_client = MagicMock()
        mock_elasticsearch.return_value = mock_es_client
        mock_es_client.ping.return_value = True
        
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client
        
        # Simuler une réponse d'embedding
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_client.embeddings.create.return_value = mock_embedding_response
        
        # Créer la base de connaissances
        with patch('ai_assistant.infrastructure.knowledge_base_impl.ENABLE_EMBEDDINGS', True):
            kb = ElasticsearchKnowledgeBase()
            
            # Générer un embedding
            embedding = kb._generate_embedding("Test text")
            
            # Vérifier que l'embedding a été généré correctement
            self.assertIsNotNone(embedding)
            self.assertEqual(embedding, [0.1, 0.2, 0.3])
            
            # Vérifier que l'API a été appelée avec les bons paramètres
            mock_openai_client.embeddings.create.assert_called_once()
            args, kwargs = mock_openai_client.embeddings.create.call_args
            self.assertEqual(kwargs['input'], "Test text")
    
    @patch('ai_assistant.infrastructure.knowledge_base_impl.Elasticsearch')
    @patch('ai_assistant.infrastructure.knowledge_base_impl.OpenAI')
    def test_vector_search(self, mock_openai, mock_elasticsearch):
        """Teste la recherche vectorielle."""
        # Configurer les mocks
        mock_es_client = MagicMock()
        mock_elasticsearch.return_value = mock_es_client
        mock_es_client.ping.return_value = True
        
        # Simuler un résultat de recherche
        mock_search_response = {
            "hits": {
                "hits": [
                    {
                        "_score": 0.95,
                        "_source": {
                            "title": "Document 1",
                            "content": "Contenu du document 1",
                            "metadata": {"source": "test"}
                        }
                    },
                    {
                        "_score": 0.85,
                        "_source": {
                            "title": "Document 2",
                            "content": "Contenu du document 2",
                            "metadata": {"source": "test"}
                        }
                    }
                ]
            }
        }
        mock_es_client.search.return_value = mock_search_response
        
        # Simuler la génération d'embedding
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client
        
        mock_embedding_response = MagicMock()
        mock_embedding_response.data = [MagicMock(embedding=[0.1, 0.2, 0.3])]
        mock_openai_client.embeddings.create.return_value = mock_embedding_response
        
        # Créer la base de connaissances
        with patch('ai_assistant.infrastructure.knowledge_base_impl.ENABLE_EMBEDDINGS', True):
            kb = ElasticsearchKnowledgeBase()
            
            # Effectuer une recherche
            results = kb.search("Test query", max_results=2)
            
            # Vérifier les résultats
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["title"], "Document 1")
            self.assertEqual(results[1]["title"], "Document 2")
            
            # Vérifier que la recherche a été effectuée avec les bons paramètres
            mock_es_client.search.assert_called_once()


class WebSocketTest(unittest.IsolatedAsyncioTestCase):
    """Tests pour l'interface WebSocket."""
    
    async def test_websocket_connection(self):
        """Teste la connexion WebSocket."""
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Créer un communicateur WebSocket
        application = URLRouter([
            path('ws/ai_assistant/', AIAssistantConsumer.as_asgi()),
        ])
        
        # Simuler une connexion authentifiée
        communicator = WebsocketCommunicator(application, "/ws/ai_assistant/")
        communicator.scope["user"] = user
        
        # Se connecter
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Fermer la connexion
        await communicator.disconnect()
    
    @patch('ai_assistant.consumers.di')
    async def test_message_streaming(self, mock_di):
        """Teste le streaming de messages via WebSocket."""
        # Créer un utilisateur de test
        user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        
        # Créer un service mock
        mock_service = MagicMock()
        mock_di.get_ai_assistant_service.return_value = mock_service
        
        # Simuler le streaming de réponse
        async def process_message_stream(conversation_id, user_id, content, callback):
            # Appeler le callback avec des fragments
            await callback("Fragment 1")
            await callback("Fragment 2")
            await callback("Fragment 3")
            
            # Retourner la réponse complète
            return {
                "content": "Fragment 1Fragment 2Fragment 3",
                "actions": [],
                "sources": [],
                "processing_time": 0.5
            }
        
        mock_service.process_message_stream = process_message_stream
        
        # Créer un communicateur WebSocket
        application = URLRouter([
            path('ws/ai_assistant/', AIAssistantConsumer.as_asgi()),
        ])
        
        # Simuler une connexion authentifiée
        communicator = WebsocketCommunicator(application, "/ws/ai_assistant/")
        communicator.scope["user"] = user
        
        # Se connecter
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        # Envoyer un message
        await communicator.send_json_to({
            'type': 'message',
            'conversation_id': '123',
            'content': 'Test message'
        })
        
        # Recevoir l'accusé de réception
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'message_received')
        
        # Recevoir les fragments
        fragment1 = await communicator.receive_json_from()
        self.assertEqual(fragment1['type'], 'message_chunk')
        self.assertEqual(fragment1['content'], 'Fragment 1')
        
        fragment2 = await communicator.receive_json_from()
        self.assertEqual(fragment2['type'], 'message_chunk')
        self.assertEqual(fragment2['content'], 'Fragment 2')
        
        fragment3 = await communicator.receive_json_from()
        self.assertEqual(fragment3['type'], 'message_chunk')
        self.assertEqual(fragment3['content'], 'Fragment 3')
        
        # Recevoir la fin du streaming
        complete = await communicator.receive_json_from()
        self.assertEqual(complete['type'], 'message_complete')
        
        # Fermer la connexion
        await communicator.disconnect()


class PerformanceTest(TestCase):
    """Tests de performance pour les optimisations."""
    
    @patch('ai_assistant.infrastructure.ai_client_impl.OpenAI')
    def test_cache_performance(self, mock_openai):
        """Teste les gains de performance avec la mise en cache."""
        # Configurer le mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_completion = MagicMock()
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Réponse de test"
        
        # Simuler un délai de 0.5 seconde pour l'API
        def delayed_response(*args, **kwargs):
            time.sleep(0.5)
            return mock_completion
            
        mock_client.chat.completions.create.side_effect = delayed_response
        
        # Créer le client AI
        ai_client = DefaultAIClient('test-key')
        
        # Premier appel - devrait prendre environ 0.5 seconde
        start_time = time.time()
        response1 = ai_client.generate_response("Test message", ["context"])
        first_call_time = time.time() - start_time
        
        # Deuxième appel avec les mêmes paramètres - devrait être beaucoup plus rapide
        start_time = time.time()
        response2 = ai_client.generate_response("Test message", ["context"])
        second_call_time = time.time() - start_time
        
        # Vérifier que le deuxième appel est significativement plus rapide
        self.assertGreater(first_call_time, second_call_time * 5)  # Au moins 5 fois plus rapide
        self.assertLess(second_call_time, 0.1)  # Moins de 100ms
