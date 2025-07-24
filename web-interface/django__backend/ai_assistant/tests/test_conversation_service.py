"""
Tests pour le service de conversation.

Ce module contient les tests unitaires pour le service de conversation.
"""

import unittest
from unittest.mock import patch, MagicMock

from ai_assistant.domain.services import ConversationService
from ai_assistant.domain.exceptions import ConversationNotFoundError, MessageNotFoundError, ValidationError


class TestConversationService(unittest.TestCase):
    """Tests pour le service de conversation."""
    
    def setUp(self):
        """Initialise les tests."""
        self.service = ConversationService()
        self.user_id = "test_user_123"
    
    def test_create_conversation(self):
        """Teste la création d'une conversation."""
        # Test avec des paramètres valides
        conversation = self.service.create_conversation(
            user_id=self.user_id,
            title="Test Conversation",
            context="Test Context"
        )
        
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.title, "Test Conversation")
        self.assertEqual(conversation.user_id, self.user_id)
        self.assertEqual(conversation.context, "Test Context")
        self.assertIsNotNone(conversation.id)
        self.assertEqual(len(conversation.messages), 0)
        
        # Test avec un titre par défaut
        conversation = self.service.create_conversation(
            user_id=self.user_id
        )
        
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.title, "Nouvelle conversation")
        
        # Test avec un user_id invalide
        with self.assertRaises(ValidationError):
            self.service.create_conversation(user_id="")
    
    def test_get_conversation_by_id(self):
        """Teste la récupération d'une conversation par son ID."""
        # Créer une conversation
        conversation = self.service.create_conversation(
            user_id=self.user_id,
            title="Test Conversation"
        )
        
        # Test avec un ID valide
        retrieved_conversation = self.service.get_conversation_by_id(
            conversation_id=conversation.id,
            user_id=self.user_id
        )
        
        self.assertEqual(retrieved_conversation.id, conversation.id)
        self.assertEqual(retrieved_conversation.title, conversation.title)
        
        # Test avec un ID invalide
        with self.assertRaises(ConversationNotFoundError):
            self.service.get_conversation_by_id(
                conversation_id="invalid_id",
                user_id=self.user_id
            )
        
        # Test avec un user_id différent
        with self.assertRaises(ConversationNotFoundError):
            self.service.get_conversation_by_id(
                conversation_id=conversation.id,
                user_id="different_user"
            )
    
    def test_get_conversations_by_user_id(self):
        """Teste la récupération des conversations d'un utilisateur."""
        # Créer des conversations
        self.service.create_conversation(
            user_id=self.user_id,
            title="Conversation 1"
        )
        self.service.create_conversation(
            user_id=self.user_id,
            title="Conversation 2"
        )
        self.service.create_conversation(
            user_id="other_user",
            title="Other User Conversation"
        )
        
        # Test avec un user_id valide
        conversations = self.service.get_conversations_by_user_id(self.user_id)
        
        self.assertEqual(len(conversations), 2)
        self.assertTrue(all(conv.user_id == self.user_id for conv in conversations))
        
        # Test avec un user_id sans conversations
        conversations = self.service.get_conversations_by_user_id("new_user")
        
        self.assertEqual(len(conversations), 0)
    
    def test_update_conversation(self):
        """Teste la mise à jour d'une conversation."""
        # Créer une conversation
        conversation = self.service.create_conversation(
            user_id=self.user_id,
            title="Original Title",
            context="Original Context"
        )
        
        # Test avec des paramètres valides
        updated_conversation = self.service.update_conversation(
            conversation_id=conversation.id,
            user_id=self.user_id,
            title="Updated Title",
            context="Updated Context"
        )
        
        self.assertEqual(updated_conversation.title, "Updated Title")
        self.assertEqual(updated_conversation.context, "Updated Context")
        
        # Test avec un ID invalide
        with self.assertRaises(ConversationNotFoundError):
            self.service.update_conversation(
                conversation_id="invalid_id",
                user_id=self.user_id,
                title="New Title"
            )
        
        # Test avec un user_id différent
        with self.assertRaises(ConversationNotFoundError):
            self.service.update_conversation(
                conversation_id=conversation.id,
                user_id="different_user",
                title="New Title"
            )
    
    def test_delete_conversation(self):
        """Teste la suppression d'une conversation."""
        # Créer une conversation
        conversation = self.service.create_conversation(
            user_id=self.user_id,
            title="Test Conversation"
        )
        
        # Test avec un ID valide
        self.service.delete_conversation(
            conversation_id=conversation.id,
            user_id=self.user_id
        )
        
        # Vérifier que la conversation a été supprimée
        with self.assertRaises(ConversationNotFoundError):
            self.service.get_conversation_by_id(
                conversation_id=conversation.id,
                user_id=self.user_id
            )
        
        # Test avec un ID invalide
        with self.assertRaises(ConversationNotFoundError):
            self.service.delete_conversation(
                conversation_id="invalid_id",
                user_id=self.user_id
            )
    
    def test_add_message(self):
        """Teste l'ajout d'un message à une conversation."""
        # Créer une conversation
        conversation = self.service.create_conversation(
            user_id=self.user_id,
            title="Test Conversation"
        )
        
        # Test avec des paramètres valides
        message = self.service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Test Message"
        )
        
        self.assertIsNotNone(message)
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Test Message")
        self.assertIsNotNone(message.id)
        
        # Vérifier que le message a été ajouté à la conversation
        updated_conversation = self.service.get_conversation_by_id(
            conversation_id=conversation.id,
            user_id=self.user_id
        )
        
        self.assertEqual(len(updated_conversation.messages), 1)
        self.assertEqual(updated_conversation.messages[0].id, message.id)
        
        # Test avec un rôle invalide
        with self.assertRaises(ValidationError):
            self.service.add_message(
                conversation_id=conversation.id,
                role="invalid_role",
                content="Test Message"
            )
        
        # Test avec un contenu vide
        with self.assertRaises(ValidationError):
            self.service.add_message(
                conversation_id=conversation.id,
                role="user",
                content=""
            )
        
        # Test avec un ID de conversation invalide
        with self.assertRaises(ConversationNotFoundError):
            self.service.add_message(
                conversation_id="invalid_id",
                role="user",
                content="Test Message"
            )
    
    def test_get_message_by_id(self):
        """Teste la récupération d'un message par son ID."""
        # Créer une conversation et ajouter un message
        conversation = self.service.create_conversation(
            user_id=self.user_id,
            title="Test Conversation"
        )
        
        message = self.service.add_message(
            conversation_id=conversation.id,
            role="user",
            content="Test Message"
        )
        
        # Test avec des IDs valides
        retrieved_message = self.service.get_message_by_id(
            conversation_id=conversation.id,
            message_id=message.id,
            user_id=self.user_id
        )
        
        self.assertEqual(retrieved_message.id, message.id)
        self.assertEqual(retrieved_message.content, message.content)
        
        # Test avec un ID de message invalide
        with self.assertRaises(MessageNotFoundError):
            self.service.get_message_by_id(
                conversation_id=conversation.id,
                message_id="invalid_id",
                user_id=self.user_id
            )
        
        # Test avec un ID de conversation invalide
        with self.assertRaises(ConversationNotFoundError):
            self.service.get_message_by_id(
                conversation_id="invalid_id",
                message_id=message.id,
                user_id=self.user_id
            )
    
    def test_get_conversation_history(self):
        """Teste la récupération de l'historique des messages d'une conversation."""
        # Créer une conversation et ajouter des messages
        conversation = self.service.create_conversation(
            user_id=self.user_id,
            title="Test Conversation"
        )
        
        for i in range(15):
            self.service.add_message(
                conversation_id=conversation.id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}"
            )
        
        # Test avec un max_messages par défaut (10)
        messages = self.service.get_conversation_history(
            conversation_id=conversation.id,
            user_id=self.user_id
        )
        
        self.assertEqual(len(messages), 10)
        self.assertEqual(messages[0].content, "Message 5")
        self.assertEqual(messages[9].content, "Message 14")
        
        # Test avec un max_messages personnalisé
        messages = self.service.get_conversation_history(
            conversation_id=conversation.id,
            user_id=self.user_id,
            max_messages=5
        )
        
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[0].content, "Message 10")
        self.assertEqual(messages[4].content, "Message 14")
        
        # Test avec un ID de conversation invalide
        with self.assertRaises(ConversationNotFoundError):
            self.service.get_conversation_history(
                conversation_id="invalid_id",
                user_id=self.user_id
            )


if __name__ == "__main__":
    unittest.main() 