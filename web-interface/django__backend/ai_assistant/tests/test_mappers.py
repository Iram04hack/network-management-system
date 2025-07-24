"""
Tests pour les mappers de conversion entre les couches de l'architecture hexagonale.
Ces tests sont critiques pour assurer l'intégrité de la conversion entre entités domaine et modèles Django.
"""

import pytest
from datetime import datetime
from django.test import TestCase
from django.contrib.auth.models import User

from ai_assistant.domain.entities import (
    Conversation, Message, MessageRole, CommandRequest, CommandResult,
    Document, SearchResult, AIResponse
)
from ai_assistant.infrastructure.repositories import (
    ConversationMapper, MessageMapper, DocumentMapper
)


class TestConversationMapper(TestCase):
    """Tests pour le mapper de conversations"""

    def setUp(self):
        """Configuration des tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.mapper = ConversationMapper()

    def test_domain_to_model_conversion(self):
        """Test de conversion entité domaine vers modèle Django"""
        # Créer une entité domaine
        domain_conversation = Conversation(
            id=None,
            user_id=self.user.id,
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            metadata={"source": "test"}
        )
        
        # Convertir vers modèle Django
        django_model = self.mapper.domain_to_model(domain_conversation)
        
        # Vérifications
        self.assertEqual(django_model.user_id, domain_conversation.user_id)
        self.assertEqual(django_model.title, domain_conversation.title)
        self.assertEqual(django_model.is_active, domain_conversation.is_active)
        self.assertEqual(django_model.metadata, domain_conversation.metadata)

    def test_model_to_domain_conversion(self):
        """Test de conversion modèle Django vers entité domaine"""
        from ai_assistant.models import Conversation as ConversationModel
        
        # Créer un modèle Django
        django_conversation = ConversationModel.objects.create(
            user=self.user,
            title="Test Django Conversation",
            is_active=True,
            metadata={"source": "django"}
        )
        
        # Convertir vers entité domaine
        domain_entity = self.mapper.model_to_domain(django_conversation)
        
        # Vérifications
        self.assertIsInstance(domain_entity, Conversation)
        self.assertEqual(domain_entity.id, django_conversation.id)
        self.assertEqual(domain_entity.user_id, django_conversation.user.id)
        self.assertEqual(domain_entity.title, django_conversation.title)
        self.assertEqual(domain_entity.is_active, django_conversation.is_active)
        self.assertEqual(domain_entity.metadata, django_conversation.metadata)

    def test_bidirectional_conversion_integrity(self):
        """Test d'intégrité de la conversion bidirectionnelle"""
        from ai_assistant.models import Conversation as ConversationModel
        
        # Créer un modèle Django original
        original_model = ConversationModel.objects.create(
            user=self.user,
            title="Original Conversation",
            is_active=True,
            metadata={"test": "bidirectional"}
        )
        
        # Conversion modèle -> domaine -> modèle
        domain_entity = self.mapper.model_to_domain(original_model)
        converted_model = self.mapper.domain_to_model(domain_entity)
        
        # Vérifier que les données sont préservées
        self.assertEqual(original_model.title, converted_model.title)
        self.assertEqual(original_model.user_id, converted_model.user_id)
        self.assertEqual(original_model.is_active, converted_model.is_active)
        self.assertEqual(original_model.metadata, converted_model.metadata)

    def test_null_handling(self):
        """Test de gestion des valeurs nulles"""
        # Test avec None
        self.assertIsNone(self.mapper.model_to_domain(None))
        
        # Test avec entité domaine avec champs optionnels None
        domain_conversation = Conversation(
            id=None,
            user_id=self.user.id,
            title="Test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_active=True,
            metadata=None
        )
        
        django_model = self.mapper.domain_to_model(domain_conversation)
        self.assertIsNotNone(django_model)
        self.assertEqual(django_model.metadata, {})  # Conversion None -> dict vide

    def test_error_handling_invalid_data(self):
        """Test de gestion d'erreurs avec données invalides"""
        # Test avec objet invalide
        with self.assertRaises((AttributeError, TypeError)):
            self.mapper.model_to_domain("not_a_model")
        
        with self.assertRaises((AttributeError, TypeError)):
            self.mapper.domain_to_model("not_a_domain_entity")


class TestMessageMapper(TestCase):
    """Tests pour le mapper de messages"""

    def setUp(self):
        """Configuration des tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        
        from ai_assistant.models import Conversation as ConversationModel
        self.conversation = ConversationModel.objects.create(
            user=self.user,
            title="Test Conversation"
        )
        
        self.mapper = MessageMapper()

    def test_domain_to_model_conversion(self):
        """Test de conversion message domaine vers modèle Django"""
        # Créer une entité domaine Message
        domain_message = Message(
            id=None,
            conversation_id=self.conversation.id,
            role=MessageRole.USER,
            content="Test message content",
            timestamp=datetime.now(),
            metadata={"source": "test", "confidence": 0.95}
        )
        
        # Convertir vers modèle Django
        django_model = self.mapper.domain_to_model(domain_message)
        
        # Vérifications
        self.assertEqual(django_model.conversation_id, domain_message.conversation_id)
        self.assertEqual(django_model.role, domain_message.role.value)
        self.assertEqual(django_model.content, domain_message.content)
        self.assertEqual(django_model.metadata, domain_message.metadata)

    def test_model_to_domain_conversion(self):
        """Test de conversion modèle Django vers entité domaine"""
        from ai_assistant.models import Message as MessageModel
        
        # Créer un modèle Django
        django_message = MessageModel.objects.create(
            conversation=self.conversation,
            role="assistant",
            content="Assistant response",
            metadata={"confidence": 0.9, "actions": []}
        )
        
        # Convertir vers entité domaine
        domain_entity = self.mapper.model_to_domain(django_message)
        
        # Vérifications
        self.assertIsInstance(domain_entity, Message)
        self.assertEqual(domain_entity.id, django_message.id)
        self.assertEqual(domain_entity.conversation_id, django_message.conversation.id)
        self.assertEqual(domain_entity.role, MessageRole.ASSISTANT)
        self.assertEqual(domain_entity.content, django_message.content)
        self.assertEqual(domain_entity.metadata, django_message.metadata)

    def test_message_role_conversion(self):
        """Test de conversion des rôles de message"""
        # Test tous les rôles possibles
        role_mappings = [
            (MessageRole.USER, "user"),
            (MessageRole.ASSISTANT, "assistant"),
            (MessageRole.SYSTEM, "system")
        ]
        
        for domain_role, model_role in role_mappings:
            # Créer message avec rôle domaine
            domain_message = Message(
                id=None,
                conversation_id=self.conversation.id,
                role=domain_role,
                content="Test content",
                timestamp=datetime.now(),
                metadata={}
            )
            
            # Convertir et vérifier
            django_model = self.mapper.domain_to_model(domain_message)
            self.assertEqual(django_model.role, model_role)
            
            # Reconvertir et vérifier
            reconverted = self.mapper.model_to_domain(django_model)
            self.assertEqual(reconverted.role, domain_role)

    def test_metadata_serialization(self):
        """Test de sérialisation des métadonnées"""
        complex_metadata = {
            "confidence": 0.95,
            "actions": [
                {"type": "command", "data": {"cmd": "ping"}},
                {"type": "search", "data": {"query": "network"}}
            ],
            "sources": ["doc1", "doc2"],
            "processing_time": 1.5
        }
        
        domain_message = Message(
            id=None,
            conversation_id=self.conversation.id,
            role=MessageRole.ASSISTANT,
            content="Complex response",
            timestamp=datetime.now(),
            metadata=complex_metadata
        )
        
        # Conversion domaine -> modèle -> domaine
        django_model = self.mapper.domain_to_model(domain_message)
        reconverted = self.mapper.model_to_domain(django_model)
        
        # Vérifier que les métadonnées complexes sont préservées
        self.assertEqual(reconverted.metadata, complex_metadata)


class TestDocumentMapper(TestCase):
    """Tests pour le mapper de documents"""

    def setUp(self):
        """Configuration des tests"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass'
        )
        self.mapper = DocumentMapper()

    def test_domain_to_model_conversion(self):
        """Test de conversion document domaine vers modèle Django"""
        domain_document = Document(
            id=None,
            title="Test Document",
            content="Document content for testing",
            author="Test Author",
            category="test",
            tags=["test", "mapper"],
            is_public=True,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={"version": "1.0"}
        )
        
        django_model = self.mapper.domain_to_model(domain_document)
        
        self.assertEqual(django_model.title, domain_document.title)
        self.assertEqual(django_model.content, domain_document.content)
        self.assertEqual(django_model.author, domain_document.author)
        self.assertEqual(django_model.category, domain_document.category)
        self.assertEqual(django_model.tags, domain_document.tags)
        self.assertEqual(django_model.is_public, domain_document.is_public)

    def test_model_to_domain_conversion(self):
        """Test de conversion modèle Django vers entité domaine"""
        from ai_assistant.models import Document as DocumentModel
        
        django_document = DocumentModel.objects.create(
            title="Django Document",
            content="Content from Django model",
            author="Django Author",
            category="django",
            tags=["django", "test"],
            is_public=False,
            metadata={"framework": "django"}
        )
        
        domain_entity = self.mapper.model_to_domain(django_document)
        
        self.assertIsInstance(domain_entity, Document)
        self.assertEqual(domain_entity.title, django_document.title)
        self.assertEqual(domain_entity.content, django_document.content)
        self.assertEqual(domain_entity.author, django_document.author)
        self.assertEqual(domain_entity.category, django_document.category)
        self.assertEqual(domain_entity.tags, django_document.tags)
        self.assertEqual(domain_entity.is_public, django_document.is_public)

    def test_tags_array_handling(self):
        """Test de gestion des tableaux de tags"""
        tags = ["networking", "configuration", "vlan", "security"]
        
        domain_document = Document(
            id=None,
            title="Tagged Document",
            content="Document with multiple tags",
            author="Tagger",
            category="network",
            tags=tags,
            is_public=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Conversion domaine -> modèle -> domaine
        django_model = self.mapper.domain_to_model(domain_document)
        reconverted = self.mapper.model_to_domain(django_model)
        
        # Vérifier que les tags sont préservés
        self.assertEqual(reconverted.tags, tags)


class TestMapperErrorHandling(TestCase):
    """Tests de gestion d'erreurs pour tous les mappers"""

    def test_mapper_error_logging(self):
        """Test que les erreurs de mapping sont loggées"""
        from ai_assistant.infrastructure.repositories import logger
        
        with self.assertLogs(logger, level='ERROR'):
            mapper = ConversationMapper()
            # Tenter une conversion avec des données invalides
            try:
                mapper.model_to_domain("invalid_data")
            except:
                pass  # L'erreur doit être loggée

    def test_partial_data_handling(self):
        """Test de gestion de données partielles"""
        mapper = MessageMapper()
        
        # Créer une entité domaine avec des champs optionnels manquants
        partial_message = Message(
            id=None,
            conversation_id=1,
            role=MessageRole.USER,
            content="Partial message",
            timestamp=datetime.now(),
            metadata=None  # Métadonnées manquantes
        )
        
        # La conversion doit réussir malgré les données partielles
        django_model = mapper.domain_to_model(partial_message)
        self.assertIsNotNone(django_model)
        
        # Les métadonnées None doivent être converties en dict vide
        reconverted = mapper.model_to_domain(django_model)
        self.assertEqual(reconverted.metadata, {})


class TestMapperPerformance(TestCase):
    """Tests de performance pour les mappers"""

    def test_bulk_conversion_performance(self):
        """Test de performance pour conversion en lot"""
        import time
        from ai_assistant.models import Conversation as ConversationModel
        
        # Créer un utilisateur
        user = User.objects.create_user(
            username='perftest',
            email='perf@test.com',
            password='testpass'
        )
        
        # Créer beaucoup de conversations
        conversations = []
        for i in range(100):
            conv = ConversationModel.objects.create(
                user=user,
                title=f"Conversation {i}",
                metadata={"index": i}
            )
            conversations.append(conv)
        
        mapper = ConversationMapper()
        
        # Mesurer le temps de conversion
        start_time = time.time()
        domain_entities = [mapper.model_to_domain(conv) for conv in conversations]
        conversion_time = time.time() - start_time
        
        # Vérifier que toutes les conversions ont réussi
        self.assertEqual(len(domain_entities), 100)
        
        # Vérifier que la conversion est raisonnablement rapide (< 1 seconde pour 100 éléments)
        self.assertLess(conversion_time, 1.0, 
                       f"Conversion trop lente: {conversion_time:.3f}s pour 100 éléments")

    def test_mapper_memory_usage(self):
        """Test que les mappers ne créent pas de fuites mémoire"""
        import gc
        
        mapper = MessageMapper()
        
        # Forcer un garbage collection avant le test
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Effectuer beaucoup de conversions
        for i in range(1000):
            domain_message = Message(
                id=i,
                conversation_id=1,
                role=MessageRole.USER,
                content=f"Message {i}",
                timestamp=datetime.now(),
                metadata={"index": i}
            )
            
            # Conversion aller-retour
            django_model = mapper.domain_to_model(domain_message)
            reconverted = mapper.model_to_domain(django_model)
            
            # Supprimer les références
            del domain_message, django_model, reconverted
        
        # Forcer un garbage collection
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Vérifier qu'il n'y a pas trop d'objets créés en permanence
        objects_created = final_objects - initial_objects
        self.assertLess(objects_created, 100, 
                       f"Possible fuite mémoire: {objects_created} objets créés")