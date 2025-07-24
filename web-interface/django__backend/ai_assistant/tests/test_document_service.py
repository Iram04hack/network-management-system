"""
Tests pour le service de gestion des documents.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock

class Document:
    """Classe simple pour simuler un document"""
    def __init__(self, id=None, title=None, content=None, author=None, category=None):
        self.id = id
        self.title = title
        self.content = content
        self.author = author
        self.category = category

class DocumentService:
    """Service de gestion des documents pour les tests"""
    
    def __init__(self):
        self.document_repository = None
    
    def create_document(self, **kwargs):
        """Créer un document"""
        if self.document_repository:
            return self.document_repository.create(**kwargs)
        return Document(**kwargs)
    
    def get_document_by_id(self, doc_id):
        """Récupérer un document par ID"""
        if self.document_repository:
            return self.document_repository.get_by_id(doc_id)
        return None
    
    def update_document(self, doc_id, **kwargs):
        """Mettre à jour un document"""
        if self.document_repository:
            return self.document_repository.update(doc_id, **kwargs)
        return None
    
    def delete_document(self, doc_id):
        """Supprimer un document"""
        if self.document_repository:
            return self.document_repository.delete(doc_id)
        return True
    
    def search_documents(self, **kwargs):
        """Rechercher des documents"""
        if self.document_repository:
            return self.document_repository.search(**kwargs)
        return []


class TestDocumentService(unittest.TestCase):
    """Tests pour le service de documents"""

    def setUp(self):
        """Configuration des tests"""
        self.document_service = DocumentService()

    def test_create_document_success(self):
        """Test de creation de document avec succes"""
        document_data = {
            'title': 'Test Document',
            'content': 'Contenu du document de test',
            'author': 'Test User',
            'category': 'documentation'
        }
        
        result = self.document_service.create_document(**document_data)
        
        # Vérifications
        self.assertIsNotNone(result)
        self.assertEqual(result.title, document_data['title'])
        self.assertEqual(result.content, document_data['content'])
        self.assertEqual(result.author, document_data['author'])
        self.assertEqual(result.category, document_data['category'])

    def test_get_document_by_id(self):
        """Test de recuperation d'un document par ID"""
        # Création d'un document de test
        document_data = {
            'id': '123',
            'title': 'Test Document',
            'content': 'Contenu du document de test',
            'author': 'Test User',
            'category': 'documentation'
        }
        
        # Mock du repository
        self.document_service.document_repository = Mock()
        self.document_service.document_repository.get_by_id.return_value = Document(**document_data)
        
        # Appel de la méthode à tester
        result = self.document_service.get_document_by_id('123')
        
        # Vérifications
        self.assertIsNotNone(result)
        self.assertEqual(result.id, document_data['id'])
        self.assertEqual(result.title, document_data['title'])
        self.document_service.document_repository.get_by_id.assert_called_once_with('123')

    def test_update_document(self):
        """Test de mise a jour d'un document"""
        # Création d'un document de test
        document_data = {
            'id': '123',
            'title': 'Test Document',
            'content': 'Contenu du document de test',
            'author': 'Test User',
            'category': 'documentation'
        }
        
        # Données de mise à jour
        update_data = {
            'title': 'Test Document Updated',
            'content': 'Contenu mis à jour'
        }
        
        # Mock du repository
        self.document_service.document_repository = Mock()
        self.document_service.document_repository.get_by_id.return_value = Document(**document_data)
        self.document_service.document_repository.update.return_value = Document(
            id='123',
            title=update_data['title'],
            content=update_data['content'],
            author=document_data['author'],
            category=document_data['category']
        )
        
        # Appel de la méthode à tester
        result = self.document_service.update_document('123', **update_data)
        
        # Vérifications
        self.assertIsNotNone(result)
        self.assertEqual(result.id, '123')
        self.assertEqual(result.title, update_data['title'])
        self.assertEqual(result.content, update_data['content'])
        self.document_service.document_repository.update.assert_called_once()

    def test_delete_document(self):
        """Test de suppression d'un document"""
        # Mock du repository
        self.document_service.document_repository = Mock()
        self.document_service.document_repository.delete.return_value = True
        
        # Appel de la méthode à tester
        result = self.document_service.delete_document('123')
        
        # Vérifications
        self.assertTrue(result)
        self.document_service.document_repository.delete.assert_called_once_with('123')

    def test_search_documents(self):
        """Test de recherche de documents"""
        # Création de documents de test
        documents = [
            Document(
                id='1',
                title='Network Configuration',
                content='Configuration du réseau',
                author='Admin',
                category='network'
            ),
            Document(
                id='2',
                title='Security Policy',
                content='Politique de sécurité',
                author='Admin',
                category='security'
            )
        ]
        
        # Mock du repository
        self.document_service.document_repository = Mock()
        self.document_service.document_repository.search.return_value = documents
        
        # Appel de la méthode à tester
        results = self.document_service.search_documents(query='network', category='network')
        
        # Vérifications
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, '1')
        self.assertEqual(results[0].title, 'Network Configuration')
        self.document_service.document_repository.search.assert_called_once_with(
            query='network', category='network'
        )


if __name__ == '__main__':
    unittest.main()