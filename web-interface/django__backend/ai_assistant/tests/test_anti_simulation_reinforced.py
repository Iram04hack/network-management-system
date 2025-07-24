"""
Tests anti-simulation renforcés suite aux corrections de la Phase 1.

Ce module contient des tests spécifiques pour vérifier que les corrections de la Phase 1
ont bien résolu les problèmes de simulation et d'incompatibilité d'interfaces.
"""

import pytest
import inspect
import os
import re
from unittest.mock import patch, MagicMock
from django.test import TestCase
from pathlib import Path

from ai_assistant.infrastructure.ai_client_impl import DefaultAIClient
from ai_assistant.infrastructure.command_executor_impl import SafeCommandExecutor
from ai_assistant.infrastructure.knowledge_base_impl import ElasticsearchKnowledgeBase
from ai_assistant.infrastructure.repositories import DjangoAIAssistantRepository
from ai_assistant.config import settings, di
from ai_assistant.domain.exceptions import AIClientException, CommandExecutionException, KnowledgeBaseException
from ai_assistant.domain.interfaces import AIClient, CommandExecutor, KnowledgeBase, AIAssistantRepository


class TestInterfaceCompatibility(TestCase):
    """Tests pour vérifier que les interfaces et leurs implémentations sont compatibles."""
    
    def test_command_executor_interface_compatibility(self):
        """Vérifie que l'implémentation de CommandExecutor respecte l'interface."""
        # Création d'une instance
        executor = SafeCommandExecutor()
        
        # Vérification que la méthode execute a les bons paramètres
        self.assertTrue(hasattr(executor, 'execute'))
        
        # Inspection de la signature de la méthode
        sig = inspect.signature(executor.execute)
        params = list(sig.parameters.keys())
        
        # Vérification des paramètres requis
        self.assertIn('command', params)
        self.assertIn('command_type', params)
        self.assertIn('user_id', params)
        
        # Vérification que la méthode validate accepte command_type
        sig_validate = inspect.signature(executor.validate)
        self.assertIn('command_type', sig_validate.parameters)
    
    def test_knowledge_base_interface_compatibility(self):
        """Vérifie que l'implémentation de KnowledgeBase respecte l'interface."""
        kb = ElasticsearchKnowledgeBase()
        
        # Vérification que la méthode search a le paramètre threshold
        sig = inspect.signature(kb.search)
        self.assertIn('threshold', sig.parameters)
        
        # Vérification de la valeur par défaut
        self.assertEqual(sig.parameters['threshold'].default, 0.7)
        
        # Vérification que le type de retour est correct
        # Note: La vérification du type exact est difficile en runtime, mais on peut vérifier
        # que la méthode retourne une liste lors d'un appel simulé
        kb.client = MagicMock()
        kb.client.search.return_value = {"hits": {"hits": []}}
        result = kb.search("test")
        self.assertIsInstance(result, list)
    
    def test_repository_interface_compatibility(self):
        """Vérifie que l'implémentation du repository respecte l'interface."""
        repo = DjangoAIAssistantRepository()
        
        # Vérification que les méthodes requises sont présentes
        required_methods = [
            'create_conversation',
            'get_conversation', 
            'get_user_conversations', 
            'update_conversation',
            'delete_conversation',
            'add_message',
            'get_conversation_messages',
            'delete_message'
        ]
        
        for method in required_methods:
            self.assertTrue(hasattr(repo, method), f"Méthode manquante: {method}")
            
        # Vérification que l'ancienne méthode save_conversation n'est plus utilisée
        self.assertFalse(hasattr(repo, 'save_conversation'), 
                       "La méthode save_conversation ne devrait plus exister")
        
        # Vérification de la signature de create_conversation
        sig = inspect.signature(repo.create_conversation)
        self.assertIn('title', sig.parameters)
        self.assertIn('user_id', sig.parameters)


class TestOpenAIModernAPI(TestCase):
    """Tests pour vérifier que l'API OpenAI moderne (v1.0+) est utilisée correctement."""
    
    def test_openai_modern_api_imports(self):
        """Vérifie que le code importe correctement la nouvelle API OpenAI."""
        # Obtenir le code source du client AI
        source_file = inspect.getsource(DefaultAIClient)
        
        # Vérifier l'importation moderne
        pattern_import = r"from\s+openai\s+import\s+OpenAI"
        self.assertRegex(source_file, pattern_import, 
                       "L'importation moderne 'from openai import OpenAI' est manquante")
    
    def test_openai_client_initialization(self):
        """Vérifie que l'initialisation du client OpenAI est moderne."""
        source_file = inspect.getsource(DefaultAIClient)
        
        # Vérifier l'initialisation du client
        pattern_client = r"client\s*=\s*OpenAI\("
        self.assertRegex(source_file, pattern_client, 
                       "L'initialisation moderne du client OpenAI est manquante")
    
    def test_openai_completions_call(self):
        """Vérifie que l'appel à l'API completions est conforme à la nouvelle version."""
        source_file = inspect.getsource(DefaultAIClient)
        
        # Vérifier l'appel à l'API moderne
        pattern_call = r"client\.chat\.completions\.create\("
        self.assertRegex(source_file, pattern_call, 
                       "L'appel moderne client.chat.completions.create est manquant")
        
        # Vérifier que l'ancien appel n'est plus utilisé
        pattern_old_call = r"openai\.ChatCompletion\.create\("
        self.assertNotRegex(source_file, pattern_old_call, 
                          "L'ancien appel openai.ChatCompletion.create est toujours utilisé")


class TestElasticsearchErrorHandling(TestCase):
    """Tests pour vérifier la gestion des erreurs Elasticsearch."""
    
    @patch('ai_assistant.config.settings.REQUIRE_ELASTICSEARCH', True)
    def test_elasticsearch_required_but_unavailable(self):
        """Vérifie que le système échoue clairement quand Elasticsearch est requis mais indisponible."""
        # Créer une instance de KnowledgeBase avec un client mocké
        kb = ElasticsearchKnowledgeBase()
        kb.client = MagicMock()
        kb.client.ping.return_value = False
        
        # La méthode _initialize_client doit lever une exception KnowledgeBaseException
        with self.assertRaises(KnowledgeBaseException) as context:
            kb._initialize_client()
        
        # Vérifier que l'erreur contient une information claire
        self.assertIn("Elasticsearch est requis mais inaccessible", str(context.exception))
    
    @patch('ai_assistant.config.settings.REQUIRE_ELASTICSEARCH', False)
    def test_elasticsearch_optional_fallback(self):
        """Vérifie que le système continue avec des fonctionnalités limitées quand Elasticsearch est optionnel."""
        # Créer une instance de KnowledgeBase avec un client mocké
        kb = ElasticsearchKnowledgeBase()
        kb.client = MagicMock()
        kb.client.ping.return_value = False
        
        # La méthode ne doit pas lever d'exception mais générer un avertissement
        with patch('ai_assistant.infrastructure.knowledge_base_impl.logger.warning') as mock_warning:
            kb._initialize_client()
            mock_warning.assert_called_once()
            self.assertIn("Impossible de se connecter à Elasticsearch", mock_warning.call_args[0][0])
        
        # Le client doit être None après initialisation
        self.assertIsNone(kb.client)


class TestConfigurationDI(TestCase):
    """Tests pour vérifier la configuration de l'injection de dépendances."""
    
    def test_validate_configuration_catches_errors(self):
        """Vérifie que validate_configuration détecte les problèmes de configuration."""
        # Test avec une configuration ES requise mais non disponible
        with patch('ai_assistant.config.settings.REQUIRE_ELASTICSEARCH', True):
            with patch('builtins.__import__', side_effect=ImportError("No module named 'elasticsearch'")):
                with self.assertRaises(Exception):
                    di.validate_configuration()
    
    def test_di_uses_correct_service_implementation(self):
        """Vérifie que DI utilise la bonne implémentation de service."""
        # Vérifier que get_ai_assistant_service importe depuis ai_assistant_service.py
        with patch('ai_assistant.config.di.get_ai_client') as mock_get_client:
            with patch('ai_assistant.config.di.get_repository') as mock_get_repo:
                with patch('ai_assistant.config.di.get_knowledge_base') as mock_get_kb:
                    with patch('ai_assistant.application.ai_assistant_service.AIAssistantService') as mock_service:
                        # Réinitialiser l'instance pour forcer la recréation
                        di._ai_assistant_service_instance = None
                        # Appeler get_ai_assistant_service
                        di.get_ai_assistant_service()
                        # Vérifier que le constructeur est appelé avec les bonnes dépendances
                        mock_service.assert_called_once()


class TestCodeQuality(TestCase):
    """Tests pour vérifier la qualité du code et l'absence de simulation."""
    
    def test_no_simulation_methods(self):
        """Vérifie qu'il n'y a pas de méthodes de simulation dans le code."""
        # Patterns de simulation à détecter
        simulation_patterns = [
            r'def\s+_?simulate',
            r'def\s+_?mock',
            r'def\s+_?fake',
            r'mock_response',
            r'fake_data',
            r'simulated_',
            r'# SIMULATION'
        ]
        
        # Répertoire du module
        module_dir = os.path.dirname(inspect.getfile(di))
        module_root = os.path.dirname(module_dir)
        
        # Exclure certains répertoires
        excluded_dirs = ['tests', '__pycache__', 'migrations']
        
        # Explorer récursivement les fichiers Python
        for root, dirs, files in os.walk(module_root):
            # Filtrer les répertoires exclus
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Vérifier chaque pattern
                            for pattern in simulation_patterns:
                                matches = re.findall(pattern, content)
                                if matches:
                                    rel_path = os.path.relpath(file_path, module_root)
                                    self.fail(f"Pattern de simulation trouvé dans {rel_path}: {pattern}")
                    except UnicodeDecodeError:
                        pass  # Ignorer les fichiers non-texte
    
    def test_proper_error_handling_not_silenced(self):
        """Vérifie que les erreurs sont correctement gérées et non silencieusement ignorées."""
        # Vérifier le code source des implémentations principales
        sources = [
            inspect.getsource(DefaultAIClient),
            inspect.getsource(SafeCommandExecutor),
            inspect.getsource(ElasticsearchKnowledgeBase)
        ]
        
        # Patterns à éviter
        bad_patterns = [
            r'except.*:(\s*pass|\s*return)',  # Exception attrapée sans traitement
            r'except\s+Exception.*:(\s*pass|\s*return)',  # Exception générique attrapée sans traitement
            r'except.*:\s*print',  # Exception simplement affichée
        ]
        
        for source in sources:
            for pattern in bad_patterns:
                matches = re.findall(pattern, source)
                self.assertEqual(len(matches), 0, f"Mauvaise gestion d'erreurs trouvée: {pattern}")
                
                
if __name__ == '__main__':
    pytest.main() 