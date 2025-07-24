"""
Tests unitaires pour la couche infrastructure.

Ce module contient les tests unitaires pour les adaptateurs, les repositories
et les services externes de la couche infrastructure.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime
import os
import tempfile

from ai_assistant.domain.entities import Message, Conversation, MessageRole, Document
from ai_assistant.domain.exceptions import AIClientException, CommandExecutionException, KnowledgeBaseException
from ai_assistant.infrastructure.adapters import OpenAIAdapter, CommandExecutor, VectorDBAdapter
from ai_assistant.infrastructure.repositories import ConversationRepository


class TestOpenAIAdapter(unittest.TestCase):
    """Tests pour l'adaptateur OpenAI."""
    
    def setUp(self):
        """Initialisation des mocks pour les tests."""
        # Création d'un patch pour le client OpenAI
        self.openai_client_patcher = patch('ai_assistant.infrastructure.adapters.openai_adapter.OpenAI')
        self.mock_openai = self.openai_client_patcher.start()
        
        # Configuration du mock pour le client OpenAI
        self.mock_client = Mock()
        self.mock_openai.return_value = self.mock_client
        
        # Configuration du mock pour la méthode chat.completions.create
        self.mock_chat = Mock()
        self.mock_client.chat = self.mock_chat
        self.mock_completions = Mock()
        self.mock_chat.completions = self.mock_completions
        
        # Création de l'adaptateur avec le mock
        self.adapter = OpenAIAdapter(api_key="test_key", model="test-model")
    
    def tearDown(self):
        """Nettoyage après les tests."""
        self.openai_client_patcher.stop()
    
    def test_generate_response_success(self):
        """Teste la génération de réponse avec succès."""
        # Configuration du mock pour simuler une réponse réussie
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = {"content": "Test response", "role": "assistant"}
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "test-model"
        mock_response.usage = {"total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50}
        
        self.mock_completions.create.return_value = mock_response
        
        # Création d'une conversation pour le test
        conversation = Conversation(
            id="conv_123",
            title="Test conversation",
            user_id="user_123",
            messages=[
                Message(
                    role=MessageRole.SYSTEM,
                    content="System message",
                    timestamp=datetime.now()
                ),
                Message(
                    role=MessageRole.USER,
                    content="User message",
                    timestamp=datetime.now()
                )
            ],
            context="test context"
        )
        
        # Appel de la méthode à tester
        response = self.adapter.generate_response(conversation, "New user message")
        
        # Vérifications
        self.mock_completions.create.assert_called_once()
        
        self.assertEqual(response["content"], "Test response")
        self.assertEqual(response["model_info"]["model"], "test-model")
        self.assertEqual(response["model_info"]["usage"]["total_tokens"], 100)
        self.assertEqual(len(response["actions"]), 0)
    
    def test_generate_response_with_actions(self):
        """Teste la génération de réponse avec des actions suggérées."""
        # Configuration du mock pour simuler une réponse avec des actions
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = {
            "content": "Test response with action",
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "execute_command",
                        "arguments": json.dumps({
                            "command": "ls -la",
                            "command_type": "shell"
                        })
                    }
                }
            ]
        }
        mock_response.choices[0].finish_reason = "tool_calls"
        mock_response.model = "test-model"
        mock_response.usage = {"total_tokens": 120, "prompt_tokens": 60, "completion_tokens": 60}
        
        self.mock_completions.create.return_value = mock_response
        
        # Création d'une conversation pour le test
        conversation = Conversation(
            id="conv_123",
            title="Test conversation",
            user_id="user_123",
            messages=[
                Message(
                    role=MessageRole.SYSTEM,
                    content="System message",
                    timestamp=datetime.now()
                ),
                Message(
                    role=MessageRole.USER,
                    content="User message",
                    timestamp=datetime.now()
                )
            ],
            context="test context"
        )
        
        # Appel de la méthode à tester
        response = self.adapter.generate_response(conversation, "Execute ls command")
        
        # Vérifications
        self.mock_completions.create.assert_called_once()
        
        self.assertEqual(response["content"], "Test response with action")
        self.assertEqual(response["model_info"]["model"], "test-model")
        self.assertEqual(len(response["actions"]), 1)
        self.assertEqual(response["actions"][0]["type"], "execute_command")
        self.assertEqual(response["actions"][0]["data"]["command"], "ls -la")
    
    def test_generate_response_error(self):
        """Teste la gestion des erreurs lors de la génération de réponse."""
        # Configuration du mock pour simuler une erreur
        self.mock_completions.create.side_effect = Exception("API Error")
        
        # Création d'une conversation pour le test
        conversation = Conversation(
            id="conv_123",
            title="Test conversation",
            user_id="user_123",
            messages=[],
            context="test context"
        )
        
        # Vérification que l'exception est bien levée
        with self.assertRaises(AIClientException):
            self.adapter.generate_response(conversation, "Error message")
    
    def test_analyze_command(self):
        """Teste l'analyse de commande."""
        # Configuration du mock pour simuler une réponse d'analyse
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = {
            "content": json.dumps({
                "is_valid": True,
                "safety_level": "safe",
                "intent": "query",
                "reason": "Commande sûre pour lister les fichiers"
            })
        }
        
        self.mock_completions.create.return_value = mock_response
        
        # Appel de la méthode à tester
        result = self.adapter.analyze_command("ls -la")
        
        # Vérifications
        self.mock_completions.create.assert_called_once()
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["safety_level"], "safe")
        self.assertEqual(result["intent"], "query")


class TestCommandExecutor(unittest.TestCase):
    """Tests pour l'exécuteur de commandes."""
    
    def setUp(self):
        """Initialisation pour les tests."""
        # Création de l'exécuteur avec une configuration de test
        self.allowed_commands = ["ls", "ping", "cat", "echo"]
        self.executor = CommandExecutor(allowed_commands=self.allowed_commands)
    
    @patch('ai_assistant.infrastructure.adapters.command_executor.subprocess.run')
    def test_execute_valid_command(self, mock_run):
        """Teste l'exécution d'une commande valide."""
        # Configuration du mock pour simuler l'exécution d'une commande
        mock_process = Mock()
        mock_process.returncode = 0
        mock_process.stdout = "Test output"
        mock_process.stderr = ""
        mock_run.return_value = mock_process
        
        # Appel de la méthode à tester
        result = self.executor.execute("ls -la", "shell", "user_123")
        
        # Vérifications
        mock_run.assert_called_once()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["stdout"], "Test output")
        self.assertEqual(result["stderr"], "")
    
    def test_validate_allowed_command(self):
        """Teste la validation d'une commande autorisée."""
        # Appel de la méthode à tester
        result = self.executor.validate("ls -la", "shell")
        
        # Vérifications
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["reason"], "Commande autorisée")
    
    def test_validate_disallowed_command(self):
        """Teste la validation d'une commande non autorisée."""
        # Appel de la méthode à tester
        result = self.executor.validate("rm -rf /", "shell")
        
        # Vérifications
        self.assertFalse(result["is_valid"])
        self.assertIn("non autorisée", result["reason"])
    
    @patch('ai_assistant.infrastructure.adapters.command_executor.subprocess.run')
    def test_execute_command_error(self, mock_run):
        """Teste la gestion des erreurs lors de l'exécution d'une commande."""
        # Configuration du mock pour simuler une erreur
        mock_run.side_effect = Exception("Command execution error")
        
        # Appel de la méthode à tester
        result = self.executor.execute("ls -la", "shell", "user_123")
        
        # Vérifications
        mock_run.assert_called_once()
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    def test_get_allowed_commands(self):
        """Teste la récupération des commandes autorisées."""
        # Appel de la méthode à tester
        commands = self.executor.get_allowed_commands()
        
        # Vérifications
        self.assertEqual(commands, self.allowed_commands)


class TestVectorDBAdapter(unittest.TestCase):
    """Tests pour l'adaptateur de base de données vectorielle."""
    
    def setUp(self):
        """Initialisation des mocks pour les tests."""
        # Création d'un répertoire temporaire pour les tests
        self.test_dir = tempfile.mkdtemp()
        
        # Création de l'adaptateur avec le répertoire de test
        self.adapter = VectorDBAdapter(db_path=self.test_dir)
    
    def tearDown(self):
        """Nettoyage après les tests."""
        # Suppression du répertoire temporaire
        import shutil
        shutil.rmtree(self.test_dir)
    
    @patch('ai_assistant.infrastructure.adapters.vector_db_adapter.FAISS')
    @patch('ai_assistant.infrastructure.adapters.vector_db_adapter.OpenAIEmbeddings')
    def test_add_document(self, mock_embeddings, mock_faiss):
        """Teste l'ajout d'un document."""
        # Configuration des mocks
        mock_index = Mock()
        mock_faiss.from_documents.return_value = mock_index
        
        # Appel de la méthode à tester
        document_id = self.adapter.add_document(
            title="Test document",
            content="Test content",
            metadata={"source": "test"}
        )
        
        # Vérifications
        self.assertIsNotNone(document_id)
        mock_faiss.from_documents.assert_called_once()
    
    @patch('ai_assistant.infrastructure.adapters.vector_db_adapter.FAISS')
    @patch('ai_assistant.infrastructure.adapters.vector_db_adapter.OpenAIEmbeddings')
    def test_search(self, mock_embeddings, mock_faiss):
        """Teste la recherche dans la base de données vectorielle."""
        # Configuration des mocks
        mock_index = Mock()
        mock_faiss.load_local.return_value = mock_index
        
        # Simulation de résultats de recherche
        mock_doc1 = Mock()
        mock_doc1.page_content = "Test content 1"
        mock_doc1.metadata = {"title": "Test document 1", "id": "doc_1", "source": "test"}
        
        mock_doc2 = Mock()
        mock_doc2.page_content = "Test content 2"
        mock_doc2.metadata = {"title": "Test document 2", "id": "doc_2", "source": "test"}
        
        # Configuration du mock pour la méthode similarity_search_with_score
        mock_index.similarity_search_with_score.return_value = [
            (mock_doc1, 0.95),
            (mock_doc2, 0.85)
        ]
        
        # Appel de la méthode à tester
        results = self.adapter.search("test query", 2)
        
        # Vérifications
        mock_index.similarity_search_with_score.assert_called_once()
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, "doc_1")
        self.assertEqual(results[0].title, "Test document 1")
        self.assertEqual(results[0].content, "Test content 1")
        self.assertEqual(results[0].score, 0.95)
        
        self.assertEqual(results[1].id, "doc_2")
        self.assertEqual(results[1].title, "Test document 2")
        self.assertEqual(results[1].content, "Test content 2")
        self.assertEqual(results[1].score, 0.85)
    
    @patch('ai_assistant.infrastructure.adapters.vector_db_adapter.FAISS')
    @patch('ai_assistant.infrastructure.adapters.vector_db_adapter.OpenAIEmbeddings')
    def test_get_document(self, mock_embeddings, mock_faiss):
        """Teste la récupération d'un document."""
        # Configuration des mocks
        mock_index = Mock()
        mock_faiss.load_local.return_value = mock_index
        
        # Création d'un fichier de métadonnées pour le test
        os.makedirs(os.path.join(self.test_dir, "documents"), exist_ok=True)
        with open(os.path.join(self.test_dir, "documents", "doc_123.json"), "w") as f:
            json.dump({
                "id": "doc_123",
                "title": "Test document",
                "content": "Test content",
                "metadata": {"source": "test"}
            }, f)
        
        # Appel de la méthode à tester
        document = self.adapter.get_document("doc_123")
        
        # Vérifications
        self.assertEqual(document.title, "Test document")
        self.assertEqual(document.content, "Test content")
        self.assertEqual(document.metadata, {"source": "test"})
    
    @patch('ai_assistant.infrastructure.adapters.vector_db_adapter.FAISS')
    @patch('ai_assistant.infrastructure.adapters.vector_db_adapter.OpenAIEmbeddings')
    def test_delete_document(self, mock_embeddings, mock_faiss):
        """Teste la suppression d'un document."""
        # Configuration des mocks
        mock_index = Mock()
        mock_faiss.load_local.return_value = mock_index
        
        # Création d'un fichier de métadonnées pour le test
        os.makedirs(os.path.join(self.test_dir, "documents"), exist_ok=True)
        with open(os.path.join(self.test_dir, "documents", "doc_123.json"), "w") as f:
            json.dump({
                "id": "doc_123",
                "title": "Test document",
                "content": "Test content",
                "metadata": {"source": "test"}
            }, f)
        
        # Appel de la méthode à tester
        result = self.adapter.delete_document("doc_123")
        
        # Vérifications
        self.assertTrue(result)
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "documents", "doc_123.json")))


class TestConversationRepository(unittest.TestCase):
    """Tests pour le repository de conversations."""
    
    def setUp(self):
        """Initialisation pour les tests."""
        # Création d'un répertoire temporaire pour les tests
        self.test_dir = tempfile.mkdtemp()
        
        # Création du repository avec le répertoire de test
        self.repository = ConversationRepository(db_path=self.test_dir)
    
    def tearDown(self):
        """Nettoyage après les tests."""
        # Suppression du répertoire temporaire
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_save_conversation_new(self):
        """Teste l'enregistrement d'une nouvelle conversation."""
        # Création d'une conversation pour le test
        conversation = Conversation(
            title="Test conversation",
            user_id="user_123",
            messages=[
                Message(
                    role=MessageRole.SYSTEM,
                    content="System message",
                    timestamp=datetime.now()
                )
            ],
            context="test context"
        )
        
        # Appel de la méthode à tester
        conversation_id = self.repository.save_conversation(conversation)
        
        # Vérifications
        self.assertIsNotNone(conversation_id)
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, "conversations", f"{conversation_id}.json")))
    
    def test_save_conversation_existing(self):
        """Teste la mise à jour d'une conversation existante."""
        # Création d'une conversation pour le test
        conversation = Conversation(
            id="conv_123",
            title="Test conversation",
            user_id="user_123",
            messages=[
                Message(
                    role=MessageRole.SYSTEM,
                    content="System message",
                    timestamp=datetime.now()
                )
            ],
            context="test context"
        )
        
        # Enregistrement initial
        self.repository.save_conversation(conversation)
        
        # Ajout d'un message
        conversation.add_message(Message(
            role=MessageRole.USER,
            content="User message",
            timestamp=datetime.now()
        ))
        
        # Mise à jour
        conversation_id = self.repository.save_conversation(conversation)
        
        # Vérifications
        self.assertEqual(conversation_id, "conv_123")
        
        # Lecture du fichier pour vérifier la mise à jour
        with open(os.path.join(self.test_dir, "conversations", "conv_123.json"), "r") as f:
            data = json.load(f)
            self.assertEqual(len(data["messages"]), 2)
            self.assertEqual(data["messages"][1]["content"], "User message")
    
    def test_get_conversation(self):
        """Teste la récupération d'une conversation."""
        # Création d'un fichier de conversation pour le test
        os.makedirs(os.path.join(self.test_dir, "conversations"), exist_ok=True)
        conversation_data = {
            "id": "conv_123",
            "title": "Test conversation",
            "user_id": "user_123",
            "messages": [
                {
                    "id": "msg_1",
                    "role": "system",
                    "content": "System message",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {},
                    "actions_taken": []
                },
                {
                    "id": "msg_2",
                    "role": "user",
                    "content": "User message",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {},
                    "actions_taken": []
                }
            ],
            "context": "test context",
            "metadata": {"created_at": datetime.now().isoformat()}
        }
        
        with open(os.path.join(self.test_dir, "conversations", "conv_123.json"), "w") as f:
            json.dump(conversation_data, f)
        
        # Appel de la méthode à tester
        conversation = self.repository.get_conversation("conv_123")
        
        # Vérifications
        self.assertIsNotNone(conversation)
        self.assertEqual(conversation.id, "conv_123")
        self.assertEqual(conversation.title, "Test conversation")
        self.assertEqual(conversation.user_id, "user_123")
        self.assertEqual(len(conversation.messages), 2)
        self.assertEqual(conversation.messages[0].role, MessageRole.SYSTEM)
        self.assertEqual(conversation.messages[1].role, MessageRole.USER)
    
    def test_delete_conversation(self):
        """Teste la suppression d'une conversation."""
        # Création d'un fichier de conversation pour le test
        os.makedirs(os.path.join(self.test_dir, "conversations"), exist_ok=True)
        with open(os.path.join(self.test_dir, "conversations", "conv_123.json"), "w") as f:
            json.dump({"id": "conv_123"}, f)
        
        # Appel de la méthode à tester
        result = self.repository.delete_conversation("conv_123")
        
        # Vérifications
        self.assertTrue(result)
        self.assertFalse(os.path.exists(os.path.join(self.test_dir, "conversations", "conv_123.json")))
    
    def test_get_user_conversations(self):
        """Teste la récupération des conversations d'un utilisateur."""
        # Création de fichiers de conversation pour le test
        os.makedirs(os.path.join(self.test_dir, "conversations"), exist_ok=True)
        
        # Conversation 1
        conversation1_data = {
            "id": "conv_1",
            "title": "Test conversation 1",
            "user_id": "user_123",
            "messages": [],
            "context": "test context",
            "metadata": {"created_at": datetime.now().isoformat()}
        }
        with open(os.path.join(self.test_dir, "conversations", "conv_1.json"), "w") as f:
            json.dump(conversation1_data, f)
        
        # Conversation 2
        conversation2_data = {
            "id": "conv_2",
            "title": "Test conversation 2",
            "user_id": "user_123",
            "messages": [],
            "context": "test context",
            "metadata": {"created_at": datetime.now().isoformat()}
        }
        with open(os.path.join(self.test_dir, "conversations", "conv_2.json"), "w") as f:
            json.dump(conversation2_data, f)
        
        # Conversation d'un autre utilisateur
        conversation3_data = {
            "id": "conv_3",
            "title": "Test conversation 3",
            "user_id": "user_456",
            "messages": [],
            "context": "test context",
            "metadata": {"created_at": datetime.now().isoformat()}
        }
        with open(os.path.join(self.test_dir, "conversations", "conv_3.json"), "w") as f:
            json.dump(conversation3_data, f)
        
        # Appel de la méthode à tester
        conversations = self.repository.get_user_conversations("user_123")
        
        # Vérifications
        self.assertEqual(len(conversations), 2)
        self.assertIn("conv_1", [conv.id for conv in conversations])
        self.assertIn("conv_2", [conv.id for conv in conversations])
        self.assertNotIn("conv_3", [conv.id for conv in conversations])


if __name__ == '__main__':
    unittest.main()
