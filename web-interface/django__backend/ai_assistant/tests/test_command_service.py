"""
Tests pour le service de commandes.

Ce module contient les tests unitaires pour le service de commandes.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import subprocess
import tempfile
import os

from ai_assistant.domain.services.command_service import CommandService
from ai_assistant.domain.exceptions import CommandExecutionError, SecurityError, ValidationError
from ai_assistant.domain.models import CommandResult


class TestCommandService(unittest.TestCase):
    """Tests pour le service de commandes."""
    
    def setUp(self):
        """Initialise les tests."""
        self.service = CommandService()
        self.user_id = "test_user_123"
    
    @patch('subprocess.Popen')
    def test_execute_command(self, mock_popen):
        """Teste l'exécution d'une commande."""
        # Configurer le mock pour subprocess.Popen
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("Command output", "")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        # Test avec une commande valide
        result = self.service.execute_shell_command("ls -la")
        
        self.assertEqual(result.stdout, "Command output")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.exit_code, 0)
        self.assertTrue(result.success)
        
        # Vérifier que subprocess.Popen a été appelé correctement
        mock_popen.assert_called_once()
        args, kwargs = mock_popen.call_args
        self.assertEqual(args[0], "ls -la")
        self.assertEqual(kwargs["shell"], True)
    
    @patch('subprocess.Popen')
    def test_execute_command_with_error(self, mock_popen):
        """Teste la gestion des erreurs lors de l'exécution d'une commande."""
        # Configurer le mock pour simuler une erreur
        mock_process = MagicMock()
        mock_process.communicate.return_value = ("", "Command error")
        mock_process.returncode = 1
        mock_popen.return_value = mock_process
        
        # Test avec une commande qui échoue mais qui est autorisée
        with patch.object(self.service, 'analyze_command_safety', return_value={"is_safe": True}):
            result = self.service.execute_shell_command("ls /nonexistent")
            
            self.assertEqual(result.stdout, "")
            self.assertEqual(result.stderr, "Command error")
            self.assertEqual(result.exit_code, 1)
            self.assertFalse(result.success)
    
    @patch('subprocess.Popen')
    def test_execute_command_with_exception(self, mock_popen):
        """Teste la gestion des exceptions lors de l'exécution d'une commande."""
        # Configurer le mock pour lever une exception
        mock_popen.side_effect = Exception("Process error")
        
        # Test avec une exception
        with self.assertRaises(CommandExecutionError):
            self.service.execute_shell_command("ls -la")
    
    def test_explain_command(self):
        """Teste l'analyse de la sécurité d'une commande."""
        # Test avec une commande valide
        result = self.service.analyze_command_safety("ls -la", "shell")
        
        self.assertTrue(result.get("is_safe", False))
    
    def test_explain_command_with_error(self):
        """Teste l'analyse de la sécurité d'une commande dangereuse."""
        # Test avec une commande dangereuse
        result = self.service.analyze_command_safety("rm -rf /", "shell")
        
        self.assertFalse(result.get("is_safe", True))
    
    @patch('sqlite3.connect')
    def test_get_command_history(self, mock_connect):
        """Teste l'exécution d'une requête SQL."""
        # Configurer le mock pour simuler une base de données
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [("SELECT * FROM users", 0, "output", "")]
        mock_cursor.description = [("command",), ("exit_code",), ("stdout",), ("stderr",)]
        
        mock_connection = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_connection
        
        # Test avec une requête SQL valide
        result = self.service.execute_sql_query("SELECT * FROM users")
        
        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)
    
    def test_save_command_history(self):
        """Teste l'analyse de la sécurité du code Python."""
        # Test avec du code Python sûr
        result = self.service.analyze_command_safety("print('Hello')", "python")
        
        self.assertTrue(result.get("is_safe", False))
        
        # Test avec du code Python dangereux
        result = self.service.analyze_command_safety("import os; os.system('rm -rf /')", "python")
        
        self.assertFalse(result.get("is_safe", True))


if __name__ == "__main__":
    unittest.main()

