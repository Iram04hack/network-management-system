"""
Configuration pour les tests avec pytest.

Ce module contient les fixtures et les configurations nécessaires
pour exécuter les tests avec pytest.
"""

import os
import tempfile
import pytest
from unittest.mock import Mock

from ai_assistant.domain.entities import Message, Conversation, MessageRole
from ai_assistant.domain.interfaces import AIClient, CommandExecutorInterface, KnowledgeBaseInterface, AIAssistantRepository


@pytest.fixture
def temp_dir():
    """Fixture pour créer un répertoire temporaire."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Nettoyage après les tests
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_ai_client():
    """Fixture pour créer un mock de AIClient."""
    mock = Mock(spec=AIClient)
    
    # Configuration des méthodes mock
    mock.generate_response.return_value = {
        "content": "Test response",
        "actions": [],
        "processing_time": 0.5,
        "model_info": {"model": "test-model"}
    }
    
    mock.analyze_command.return_value = {
        "is_valid": True,
        "safety_level": "safe",
        "intent": "query",
        "reason": "Commande sûre"
    }
    
    return mock


@pytest.fixture
def mock_command_executor():
    """Fixture pour créer un mock de CommandExecutorInterface."""
    mock = Mock(spec=CommandExecutorInterface)
    
    # Configuration des méthodes mock
    mock.validate.return_value = {
        "is_valid": True,
        "reason": "Commande autorisée"
    }
    
    mock.execute.return_value = {
        "success": True,
        "output": "Test output",
        "error": "",
        "exit_code": 0,
        "execution_time": 0.1
    }
    
    mock.get_allowed_commands.return_value = ["ls", "ping", "cat"]
    
    return mock


@pytest.fixture
def mock_knowledge_base():
    """Fixture pour créer un mock de KnowledgeBaseInterface."""
    mock = Mock(spec=KnowledgeBaseInterface)
    
    # Configuration des méthodes mock
    mock.search.return_value = []
    mock.add_document.return_value = "doc_123"
    mock.get_document.return_value = None
    mock.delete_document.return_value = True
    
    return mock


@pytest.fixture
def mock_conversation_repository():
    """Fixture pour créer un mock de AIAssistantRepository."""
    mock = Mock(spec=AIAssistantRepository)
    
    # Configuration des méthodes mock
    mock.save_conversation.return_value = "conv_123"
    mock.get_conversation.return_value = None
    mock.delete_conversation.return_value = True
    mock.get_user_conversations.return_value = []
    
    return mock


@pytest.fixture
def sample_conversation():
    """Fixture pour créer une conversation de test."""
    return Conversation(
        id="conv_123",
        title="Test conversation",
        user_id="user_123",
        messages=[
            Message(
                id="msg_1",
                role=MessageRole.SYSTEM,
                content="System message"
            ),
            Message(
                id="msg_2",
                role=MessageRole.USER,
                content="User message"
            )
        ],
        context="test context",
        metadata={"created_at": "2023-01-01T00:00:00"}
    ) 