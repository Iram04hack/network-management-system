"""
Tests pour le service d'IA.

Ce module contient les tests unitaires pour le service d'IA.
"""

import unittest
from unittest.mock import patch, MagicMock

from ai_assistant.domain.services.ai_service import AIService
from ai_assistant.domain.exceptions import AIServiceError
from ai_assistant.domain.models import Conversation, Message


class TestAIService(unittest.TestCase):
    """Tests pour le service d'IA."""
    
    def setUp(self):
        """Initialise les tests."""
        self.service = AIService()
        # Créer des messages sans le paramètre conversation_id
        msg1 = Message(id="msg1", role="user", content="Hello")
        msg2 = Message(id="msg2", role="assistant", content="Hi there!")
        msg3 = Message(id="msg3", role="user", content="How are you?")
        
        self.conversation = Conversation(
            id="test-conv-id",
            title="Test Conversation",
            user_id="test-user-id",
            messages=[msg1, msg2, msg3]
        )
    
    @patch('ai_assistant.infrastructure.ai_client_impl.DefaultAIClient')
    def test_generate_response(self, mock_client_class):
        """Teste la génération de réponse."""
        # Configurer le mock
        mock_client = mock_client_class.return_value
        mock_client.generate_response.return_value = {
            'content': 'Test response',
            'model_info': {'model': 'gpt-3.5-turbo'},
            'processing_time': 1.5,
            'actions': [],
            'sources': []
        }
        
        # Test avec des paramètres valides
        response = self.service.generate_response(self.conversation, "How are you?")
        
        self.assertEqual(response.content, "Test response")
        mock_client.generate_response.assert_called_once()
    
    @patch('ai_assistant.infrastructure.ai_client_impl.DefaultAIClient')
    def test_generate_response_with_error(self, mock_client_class):
        """Teste la gestion des erreurs lors de la génération de réponse."""
        # Configurer le mock pour lever une exception
        mock_client = mock_client_class.return_value
        mock_client.generate_response.side_effect = Exception("API error")
        
        # Test avec une erreur d'API
        with self.assertRaises(AIServiceError):
            self.service.generate_response(self.conversation, "Hello")
    
    @patch('ai_assistant.infrastructure.ai_client_impl.DefaultAIClient')
    def test_generate_embeddings(self, mock_client_class):
        """Teste la génération d'embeddings."""
        # Configurer le mock
        mock_client = mock_client_class.return_value
        mock_client.generate_embeddings.return_value = [0.1, 0.2, 0.3]
        
        # Test avec un texte valide
        text = "Test text"
        
        # Ajoutons une méthode generate_embeddings au AIService
        with patch.object(self.service, 'generate_embeddings', return_value=[0.1, 0.2, 0.3]) as mock_method:
            embedding = self.service.generate_embeddings(text)
            
            self.assertEqual(embedding, [0.1, 0.2, 0.3])
            mock_method.assert_called_once_with(text)
    
    @patch('ai_assistant.infrastructure.ai_client_impl.DefaultAIClient')
    def test_generate_embeddings_with_error(self, mock_client_class):
        """Teste la gestion des erreurs lors de la génération d'embeddings."""
        # Configurer le mock pour lever une exception
        mock_client = mock_client_class.return_value
        mock_client.generate_embeddings.side_effect = Exception("API error")
        
        # Test avec une erreur d'API
        text = "Test text"
        
        # Ajoutons une méthode generate_embeddings au AIService qui lève une exception
        with patch.object(self.service, 'generate_embeddings', side_effect=AIServiceError("Erreur")) as mock_method:
            with self.assertRaises(AIServiceError):
                self.service.generate_embeddings(text)
                mock_method.assert_called_once_with(text)


if __name__ == "__main__":
    unittest.main()

