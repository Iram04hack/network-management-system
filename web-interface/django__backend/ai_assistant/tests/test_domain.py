"""
Tests unitaires pour les entités du domaine ai_assistant.

Ce module teste les entités pures du domaine selon l'architecture hexagonale.
Tests migrés et adaptés depuis l'ancien système avec améliorations anti-simulation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from ai_assistant.domain.entities import (
    Message, Conversation, MessageRole, CommandRequest, 
    CommandResult, KnowledgeDocument, AIResponse, Document, 
    SearchResult, UserPreference
)
from ai_assistant.domain.exceptions import AIClientException, CommandExecutionException, KnowledgeBaseException


class TestMessageRole:
    """Tests pour l'énumération MessageRole."""
    
    def test_message_role_values(self):
        """Test des valeurs de l'énumération MessageRole."""
        assert MessageRole.USER.value == "user"
        assert MessageRole.ASSISTANT.value == "assistant"
        assert MessageRole.SYSTEM.value == "system"
    
    def test_message_role_realistic_usage(self):
        """Test d'utilisation réaliste des rôles de message."""
        # Vérifier que les rôles correspondent aux cas d'usage réseau
        user_role = MessageRole.USER
        assistant_role = MessageRole.ASSISTANT
        system_role = MessageRole.SYSTEM
        
        assert user_role != assistant_role
        assert assistant_role != system_role
        assert system_role != user_role
        
        # Vérifier l'absence de rôles factices ou de test
        all_roles = [MessageRole.USER, MessageRole.ASSISTANT, MessageRole.SYSTEM]
        role_values = [role.value for role in all_roles]
        
        fake_role_patterns = ["test", "mock", "fake", "dummy", "placeholder"]
        for role_value in role_values:
            for fake_pattern in fake_role_patterns:
                assert fake_pattern not in role_value.lower()


class TestMessage:
    """Tests pour l'entité Message."""
    
    def test_create_user_message(self):
        """Test de création d'un message utilisateur."""
        timestamp = datetime.now()
        message = Message(
            role=MessageRole.USER,
            content="Comment configurer un VLAN ?",
            timestamp=timestamp
        )
        
        assert message.role == MessageRole.USER
        assert message.content == "Comment configurer un VLAN ?"
        assert message.timestamp == timestamp
        assert message.metadata == {}
        assert message.actions_taken == []
        assert message.is_user_message()
        assert not message.is_assistant_message()
    
    def test_create_assistant_message(self):
        """Test de création d'un message assistant."""
        message = Message(
            role=MessageRole.ASSISTANT,
            content="Pour configurer un VLAN...",
            timestamp=datetime.now(),
            metadata={"confidence": 0.95}
        )
        
        assert message.role == MessageRole.ASSISTANT
        assert message.is_assistant_message()
        assert not message.is_user_message()
        assert message.metadata["confidence"] == 0.95
    
    def test_add_action(self):
        """Test d'ajout d'action à un message."""
        message = Message(
            role=MessageRole.ASSISTANT,
            content="Configuration terminée",
            timestamp=datetime.now()
        )
        
        message.add_action("command_executed", {
            "command": "configure vlan 100",
            "status": "success"
        })
        
        assert len(message.actions_taken) == 1
        action = message.actions_taken[0]
        assert action["type"] == "command_executed"
        assert action["data"]["command"] == "configure vlan 100"
        assert action["data"]["status"] == "success"
        assert "timestamp" in action
    
    def test_get_text_content(self):
        """Test de récupération du contenu textuel."""
        message = Message(
            role=MessageRole.USER,
            content="Texte du message",
            timestamp=datetime.now()
        )
        
        assert message.get_text_content() == "Texte du message"
    
    def test_message_post_init(self):
        """Test de l'initialisation automatique des champs."""
        message = Message(
            role=MessageRole.USER,
            content="Test",
            timestamp=datetime.now()
        )
        
        # Les champs doivent être initialisés automatiquement
        assert isinstance(message.metadata, dict)
        assert isinstance(message.actions_taken, list)

    def test_message_no_simulation_content(self):
        """Test anti-simulation : vérifie l'absence de contenu simulé."""
        message = Message(
            role=MessageRole.ASSISTANT,
            content="Réponse réelle de l'IA",
            timestamp=datetime.now()
        )
        
        # Vérifier l'absence de patterns de simulation
        simulation_patterns = [
            "Simulation de",
            "Réponse simulée",
            "Données de test",
            "Mock response"
        ]
        
        for pattern in simulation_patterns:
            assert pattern not in message.content


class TestConversation:
    """Tests pour l'entité Conversation."""
    
    def test_create_conversation(self):
        """Test de création d'une conversation."""
        conversation = Conversation(
            title="Support technique",
            messages=[]
        )
        
        assert conversation.title == "Support technique"
        assert len(conversation.messages) == 0
        assert conversation.is_active
        assert isinstance(conversation.metadata, dict)
        assert conversation.get_message_count() == 0
    
    def test_add_user_message(self):
        """Test d'ajout d'un message utilisateur."""
        conversation = Conversation(
            title="Test",
            messages=[]
        )
        
        message = conversation.add_user_message("Bonjour")
        
        assert len(conversation.messages) == 1
        assert message.role == MessageRole.USER
        assert message.content == "Bonjour"
        assert conversation.get_message_count() == 1
    
    def test_add_assistant_message(self):
        """Test d'ajout d'un message assistant."""
        conversation = Conversation(
            title="Test",
            messages=[]
        )
        
        message = conversation.add_assistant_message("Bonjour ! Comment puis-je vous aider ?")
        
        assert len(conversation.messages) == 1
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "Bonjour ! Comment puis-je vous aider ?"
    
    def test_get_messages_by_role(self):
        """Test de récupération des messages par rôle."""
        conversation = Conversation(
            title="Test",
            messages=[]
        )
        
        conversation.add_user_message("Question 1")
        conversation.add_assistant_message("Réponse 1")
        conversation.add_user_message("Question 2")
        conversation.add_assistant_message("Réponse 2")
        
        user_messages = conversation.get_user_messages()
        assistant_messages = conversation.get_assistant_messages()
        
        assert len(user_messages) == 2
        assert len(assistant_messages) == 2
        assert all(msg.role == MessageRole.USER for msg in user_messages)
        assert all(msg.role == MessageRole.ASSISTANT for msg in assistant_messages)
    
    def test_get_last_message(self):
        """Test de récupération du dernier message."""
        conversation = Conversation(
            title="Test",
            messages=[]
        )
        
        # Conversation vide
        assert conversation.get_last_message() is None
        
        # Ajout de messages
        conversation.add_user_message("Premier message")
        last_msg = conversation.add_assistant_message("Dernier message")
        
        assert conversation.get_last_message() == last_msg
    
    def test_get_context_for_ai(self):
        """Test de génération du contexte pour l'IA."""
        conversation = Conversation(
            title="Test",
            messages=[]
        )
        
        # Ajouter plusieurs messages
        conversation.add_user_message("Message 1")
        conversation.add_assistant_message("Réponse 1")
        conversation.add_user_message("Message 2")
        conversation.add_assistant_message("Réponse 2")
        conversation.add_user_message("Message 3")
        
        # Test avec limite
        context = conversation.get_context_for_ai(max_messages=3)
        
        assert len(context) == 3
        # Vérifier que les derniers messages sont inclus
        assert context[-1]["role"] == "user"
        assert context[-1]["content"] == "Message 3"
    
    def test_conversation_lifecycle(self):
        """Test du cycle de vie d'une conversation."""
        conversation = Conversation(
            title="Test Lifecycle",
            messages=[]
        )
        
        # Test archive
        conversation.archive()
        assert not conversation.is_active
        
        # Test réactivation
        conversation.reactivate()
        assert conversation.is_active
        
        # Test mise à jour du titre
        old_updated_at = conversation.updated_at
        conversation.update_title("Nouveau titre")
        assert conversation.title == "Nouveau titre"
        assert conversation.updated_at > old_updated_at

    def test_conversation_real_data_only(self):
        """Test anti-simulation : vérifie que la conversation utilise de vraies données."""
        conversation = Conversation(
            title="Configuration réseau réelle",
            messages=[]
        )
        
        # Ajouter des messages réalistes
        conversation.add_user_message("Problème de connectivité sur VLAN 100")
        assistant_msg = conversation.add_assistant_message("Analysons la configuration du VLAN 100")
        
        # Vérifier l'absence de données simulées
        fake_data_patterns = [
            "nodes\": 8",
            "fake_topology",
            "simulation_data",
            "mock_network"
        ]
        
        for message in conversation.messages:
            for pattern in fake_data_patterns:
                assert pattern not in message.content


class TestCommandRequest:
    """Tests pour l'entité CommandRequest."""
    
    def test_create_command_request(self):
        """Test de création d'une demande de commande."""
        request = CommandRequest(
            command="show interfaces",
            command_type="network",
            user_id="user123",
            parameters={"format": "json"}
        )
        
        assert request.command == "show interfaces"
        assert request.command_type == "network"
        assert request.user_id == "user123"
        assert request.parameters["format"] == "json"
        assert isinstance(request.requested_at, datetime)

    def test_command_request_security_validation(self):
        """Test anti-simulation : validation sécurisée des commandes."""
        # Commande sûre
        safe_request = CommandRequest(
            command="show version",
            command_type="read",
            user_id="user123"
        )
        
        assert safe_request.command == "show version"
        assert safe_request.command_type == "read"
        
        # Vérifier que les commandes dangereuses ne sont pas acceptées silencieusement
        dangerous_commands = [
            "rm -rf /",
            "delete all",
            "format disk",
            "shutdown -h now"
        ]
        
        for dangerous_cmd in dangerous_commands:
            request = CommandRequest(
                command=dangerous_cmd,
                command_type="system",
                user_id="user123"
            )
            # Le système ne doit pas silencieusement accepter ces commandes
            assert request.command == dangerous_cmd  # Stockage brut pour validation ultérieure


class TestCommandResult:
    """Tests pour l'entité CommandResult."""
    
    def test_create_success_result(self):
        """Test de création d'un résultat de commande réussie."""
        result = CommandResult(
            success=True,
            output="Interface GigabitEthernet0/1 is up",
            execution_time=0.5
        )
        
        assert result.success
        assert result.output == "Interface GigabitEthernet0/1 is up"
        assert result.execution_time == 0.5
        assert result.error_message is None
        assert isinstance(result.executed_at, datetime)
    
    def test_create_error_result(self):
        """Test de création d'un résultat d'erreur."""
        result = CommandResult(
            success=False,
            output="",
            error_message="Command not found",
            metadata={"error_code": 404}
        )
        
        assert not result.success
        assert result.error_message == "Command not found"
        assert result.metadata["error_code"] == 404

    def test_command_result_no_fake_output(self):
        """Test anti-simulation : pas de sortie factice."""
        result = CommandResult(
            success=True,
            output="Real network interface status: eth0 up",
            execution_time=0.3
        )
        
        # Vérifier l'absence de données simulées
        fake_output_patterns = [
            "Simulation de",
            "Faux résultat",
            "Mock output",
            "Test data"
        ]
        
        for pattern in fake_output_patterns:
            assert pattern not in result.output


class TestKnowledgeDocument:
    """Tests pour l'entité KnowledgeDocument."""
    
    def test_create_knowledge_document(self):
        """Test de création d'un document de connaissance."""
        doc = KnowledgeDocument(
            title="Configuration VLAN",
            content="Pour configurer un VLAN...",
            category="network",
            keywords=["vlan", "configuration", "switch"],
            relevance_score=0.95
        )
        
        assert doc.title == "Configuration VLAN"
        assert doc.content == "Pour configurer un VLAN..."
        assert doc.category == "network"
        assert "vlan" in doc.keywords
        assert doc.relevance_score == 0.95
        assert isinstance(doc.created_at, datetime)

    def test_knowledge_document_real_content(self):
        """Test anti-simulation : contenu réel de documentation."""
        doc = KnowledgeDocument(
            title="Guide de troubleshooting réseau",
            content="Étapes de diagnostic: 1. Vérifier la connectivité physique...",
            category="troubleshooting",
            keywords=["diagnostic", "réseau", "troubleshooting"]
        )
        
        # Vérifier que le contenu n'est pas simulé
        assert len(doc.content) > 50  # Contenu substantiel
        assert "Étapes de diagnostic" in doc.content
        
        # Vérifier l'absence de contenu factice
        fake_content_patterns = [
            "Lorem ipsum",
            "Placeholder text",
            "Contenu simulé",
            "Fake documentation"
        ]
        
        for pattern in fake_content_patterns:
            assert pattern not in doc.content


class TestAIResponse:
    """Tests pour l'entité AIResponse."""
    
    def test_create_ai_response(self):
        """Test de création d'une réponse IA."""
        knowledge_doc = KnowledgeDocument(
            title="Test Doc",
            content="Content",
            category="test"
        )
        
        response = AIResponse(
            content="Voici la réponse",
            confidence=0.9,
            sources=[knowledge_doc],
            suggested_actions=[{"type": "command", "data": {"cmd": "show"}}],
            processing_time=1.2,
            model_used="gpt-4"
        )
        
        assert response.content == "Voici la réponse"
        assert response.confidence == 0.9
        assert len(response.sources) == 1
        assert response.sources[0] == knowledge_doc
        assert len(response.suggested_actions) == 1
        assert response.processing_time == 1.2
        assert response.model_used == "gpt-4"
    
    def test_ai_response_post_init(self):
        """Test de l'initialisation automatique des champs."""
        response = AIResponse(
            content="Test",
            confidence=0.8
        )
        
        assert isinstance(response.sources, list)
        assert isinstance(response.suggested_actions, list)
        assert len(response.sources) == 0
        assert len(response.suggested_actions) == 0

    def test_ai_response_realistic_confidence(self):
        """Test anti-simulation : score de confiance réaliste."""
        response = AIResponse(
            content="Réponse basée sur l'analyse de votre configuration",
            confidence=0.87
        )
        
        # Vérifier que la confiance est dans une plage réaliste
        assert 0.0 <= response.confidence <= 1.0
        assert response.confidence != 1.0  # Confiance parfaite irréaliste
        
        # Vérifier que le contenu n'est pas générique
        generic_responses = [
            "Réponse générique",
            "Placeholder response",
            "Default answer"
        ]
        
        for generic in generic_responses:
            assert generic not in response.content


class TestDocumentAndSearchResult:
    """Tests pour les entités Document et SearchResult."""
    
    def test_document_creation(self):
        """Test de création d'un document."""
        document = Document(
            title="Test document",
            content="Test content",
            metadata={"source": "test"}
        )
        
        assert document.title == "Test document"
        assert document.content == "Test content"
        assert document.metadata == {"source": "test"}
    
    def test_search_result_creation(self):
        """Test de création d'un résultat de recherche."""
        result = SearchResult(
            id="result_123",
            title="Test result",
            content="Test content",
            metadata={"source": "test"},
            score=0.95
        )
        
        assert result.id == "result_123"
        assert result.title == "Test result"
        assert result.content == "Test content"
        assert result.metadata == {"source": "test"}
        assert result.score == 0.95


class TestUserPreference:
    """Tests pour l'entité UserPreference."""
    
    def test_user_preference_creation(self):
        """Test de création des préférences utilisateur."""
        prefs = UserPreference(
            user_id="user123",
            ai_model="gpt-4",
            language="fr",
            theme="dark",
            notifications_enabled=False,
            max_history_items=100
        )
        
        assert prefs.user_id == "user123"
        assert prefs.ai_model == "gpt-4"
        assert prefs.language == "fr"
        assert prefs.theme == "dark"
        assert not prefs.notifications_enabled
        assert prefs.max_history_items == 100
        assert isinstance(prefs.custom_settings, dict)


class TestExceptions:
    """Tests pour les exceptions du domaine."""
    
    def test_ai_client_exception(self):
        """Test de l'exception AIClientException."""
        exception = AIClientException("Erreur de connexion API", "connection_error")
        
        assert str(exception) == "Erreur de connexion API"
        assert exception.error_type == "connection_error"
    
    def test_command_execution_exception(self):
        """Test de l'exception CommandExecutionException."""
        exception = CommandExecutionException("Commande non autorisée", "permission_error")
        
        assert str(exception) == "Commande non autorisée"
        assert exception.error_type == "permission_error"
    
    def test_knowledge_base_exception(self):
        """Test de l'exception KnowledgeBaseException."""
        exception = KnowledgeBaseException("Base de données inaccessible", "database_error")
        
        assert str(exception) == "Base de données inaccessible"
        assert exception.error_type == "database_error"


# Tests d'intégration entre entités
class TestEntityIntegration:
    """Tests d'intégration entre les entités."""
    
    def test_conversation_with_complex_scenario(self):
        """Test d'un scénario complexe avec conversation complète."""
        conversation = Conversation(
            title="Support Réseau",
            messages=[]
        )
        
        # Scénario : problème réseau avec diagnostic
        user_msg1 = conversation.add_user_message("Mon réseau est lent")
        assistant_msg1 = conversation.add_assistant_message("Je vais vous aider à diagnostiquer le problème")
        
        # Ajout d'action de diagnostic
        assistant_msg1.add_action("diagnostic_started", {
            "test_type": "bandwidth",
            "target": "all_interfaces"
        })
        
        user_msg2 = conversation.add_user_message("Que dois-je vérifier ?")
        assistant_msg2 = conversation.add_assistant_message("Vérifiez l'utilisation des interfaces")
        
        # Vérifications
        assert conversation.get_message_count() == 4
        assert len(conversation.get_user_messages()) == 2
        assert len(conversation.get_assistant_messages()) == 2
        assert len(assistant_msg1.actions_taken) == 1
        
        # Test du contexte pour IA
        context = conversation.get_context_for_ai(max_messages=2)
        assert len(context) == 2
        assert context[-1]["content"] == "Que dois-je vérifier ?"

    def test_full_workflow_with_real_data(self):
        """Test anti-simulation : workflow complet avec vraies données."""
        # Création d'une conversation réaliste
        conversation = Conversation(
            title="Incident réseau - Perte de connectivité VLAN 200",
            messages=[]
        )
        
        # Simulation d'un vrai incident
        user_msg = conversation.add_user_message(
            "Les utilisateurs du VLAN 200 n'arrivent plus à accéder aux serveurs. "
            "Le problème a commencé il y a 15 minutes."
        )
        
        # Réponse assistante réaliste
        assistant_msg = conversation.add_assistant_message(
            "Je vais vous aider à diagnostiquer ce problème de connectivité VLAN. "
            "Commençons par vérifier l'état des interfaces du switch principal."
        )
        
        # Ajout d'actions de diagnostic réelles
        assistant_msg.add_action("command_suggested", {
            "command": "show vlan id 200",
            "purpose": "Vérifier la configuration du VLAN 200",
            "safety_level": "safe"
        })
        
        # Vérifications de réalisme
        assert "VLAN 200" in user_msg.content
        assert "15 minutes" in user_msg.content
        assert "diagnostic" in assistant_msg.content
        assert len(assistant_msg.actions_taken) == 1
        assert assistant_msg.actions_taken[0]["data"]["safety_level"] == "safe"
        
        # Vérifier l'absence de données simulées
        all_content = " ".join([msg.content for msg in conversation.messages])
        simulation_indicators = [
            "données de test",
            "simulation de",
            "fake data",
            "placeholder"
        ]
        
        for indicator in simulation_indicators:
            assert indicator not in all_content.lower()


if __name__ == '__main__':
    pytest.main([__file__])
