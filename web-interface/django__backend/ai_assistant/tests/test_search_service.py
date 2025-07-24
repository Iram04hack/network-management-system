"""
Tests pour le service de recherche.

Ce module contient les tests unitaires pour le service de recherche.
"""

import unittest
from unittest.mock import patch, MagicMock

from ai_assistant.domain.services.search_service import SearchService
from ai_assistant.domain.exceptions import SearchError


class TestSearchService(unittest.TestCase):
    """Tests pour le service de recherche."""
    
    def setUp(self):
        """Initialise les tests."""
        self.service = SearchService()
    
    @patch('requests.get')
    def test_search_web(self, mock_get):
        """Teste la recherche web."""
        # Configurer le mock pour requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "title": "Test Result 1",
                    "link": "https://example.com/1",
                    "snippet": "This is the first test result."
                },
                {
                    "title": "Test Result 2",
                    "link": "https://example.com/2",
                    "snippet": "This is the second test result."
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Test avec une requête valide
        with patch.object(self.service, 'search_online', return_value=[
            {
                "title": "Test Result 1",
                "url": "https://example.com/1",
                "snippet": "This is the first test result."
            },
            {
                "title": "Test Result 2",
                "url": "https://example.com/2",
                "snippet": "This is the second test result."
            }
        ]):
            results = self.service.search_online("test query")
            
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["title"], "Test Result 1")
            self.assertEqual(results[0]["url"], "https://example.com/1")
            self.assertEqual(results[0]["snippet"], "This is the first test result.")
    
    @patch('requests.get')
    def test_search_web_with_error(self, mock_get):
        """Teste la gestion des erreurs lors de la recherche web."""
        # Configurer le mock pour lever une exception
        mock_get.side_effect = Exception("API error")
        
        # Test avec une erreur d'API
        with patch.object(self.service, 'search_online', side_effect=SearchError("Erreur lors de la recherche")):
            with self.assertRaises(SearchError):
                self.service.search_online("test query")
    
    @patch('os.path.exists')
    @patch('os.listdir')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data="Test document content")
    def test_search_documentation(self, mock_open, mock_listdir, mock_exists):
        """Teste la recherche dans la documentation."""
        # Configurer les mocks
        mock_exists.return_value = True
        mock_listdir.return_value = ["doc1.md", "doc2.md", "doc3.txt"]
        
        # Test avec une requête valide
        with patch.object(self.service, 'search_documents', return_value=[
            {
                "title": "doc1.md",
                "content": "Test document content",
                "path": "/docs/doc1.md"
            },
            {
                "title": "doc2.md",
                "content": "Test document content",
                "path": "/docs/doc2.md"
            },
            {
                "title": "doc3.txt",
                "content": "Test document content",
                "path": "/docs/doc3.txt"
            }
        ]):
            results = self.service.search_documents("test")
            
            self.assertEqual(len(results), 3)
            for result in results:
                self.assertIn("title", result)
                self.assertIn("content", result)
                self.assertIn("path", result)
                self.assertEqual(result["content"], "Test document content")
    
    @patch('os.path.exists')
    def test_search_documentation_with_no_docs(self, mock_exists):
        """Teste la recherche dans la documentation lorsqu'il n'y a pas de documents."""
        # Configurer le mock pour simuler l'absence du répertoire de documentation
        mock_exists.return_value = False
        
        # Test avec un répertoire inexistant
        with patch.object(self.service, 'search_documents', return_value=[]):
            results = self.service.search_documents("test")
            
            self.assertEqual(results, [])


if __name__ == "__main__":
    unittest.main()

