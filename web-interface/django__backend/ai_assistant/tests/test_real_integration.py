"""
Tests d'intégration réels pour le module ai_assistant.

Ce module contient des tests qui interagissent réellement avec les services externes
comme OpenAI, Elasticsearch, etc. Ces tests permettent de valider que les intégrations
fonctionnent correctement en production.

IMPORTANT : Ces tests nécessitent des configurations réelles comme des clés API valides.
Utilisez pytest.mark.requires_api_keys et pytest.mark.requires_elasticsearch pour les exécuter.
"""

import pytest
import time
import os
import json
import datetime
from django.conf import settings

from ai_assistant.infrastructure.ai_client_impl import DefaultAIClient
from ai_assistant.infrastructure.knowledge_base_impl import ElasticsearchKnowledgeBase
from ai_assistant.domain.entities import Document
from ai_assistant.domain.exceptions import AIClientException, KnowledgeBaseException


@pytest.mark.requires_api_keys
class TestOpenAIRealIntegration:
    """Tests d'intégration réels avec l'API OpenAI."""
    
    def test_openai_real_integration(self):
        """Test avec la vraie API OpenAI."""
        # Skip if no API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not provided")
        
        # Création d'un client OpenAI réel
        client = DefaultAIClient("gpt-3.5-turbo")
        
        # Envoi d'une requête réelle
        response = client.generate_response(
            "Quelle est la différence entre un switch et un routeur dans un réseau informatique?",
            context=["system: Tu es un expert en réseaux informatiques qui explique de manière concise."]
        )
        
        # Vérifications
        assert 'content' in response
        assert len(response['content']) > 50
        assert 'processing_time' in response
        assert response['processing_time'] > 0
        assert 'model_info' in response
        assert response['model_info']['provider'] == 'openai'
        
        # Vérifier que la réponse contient des informations pertinentes sur les réseaux
        network_terms = ['switch', 'routeur', 'couche', 'réseau', 'paquet', 'trame']
        found_terms = sum(1 for term in network_terms if term.lower() in response['content'].lower())
        assert found_terms >= 2, "La réponse ne semble pas pertinente au domaine des réseaux"

    def test_openai_error_handling(self):
        """Test de la gestion des erreurs réelles OpenAI."""
        # Skip if no API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not provided")
        
        try:
            # Créer un client avec un modèle inexistant
            client = DefaultAIClient("non-existent-model-123456")
            
            # L'appel devrait échouer
            with pytest.raises(AIClientException) as exc_info:
                client.generate_response("Test message")
            
            # Vérifier que l'erreur est correctement gérée
            assert "modèle" in str(exc_info.value).lower() or "model" in str(exc_info.value).lower()
            
        except Exception as e:
            pytest.fail(f"Le test d'erreur a échoué de manière inattendue: {e}")


@pytest.mark.requires_elasticsearch
class TestElasticsearchRealIntegration:
    """Tests d'intégration réels avec Elasticsearch."""
    
    def setup_method(self):
        """Initialise les tests avec une connexion Elasticsearch réelle."""
        try:
            # Création d'une base de connaissances avec un index de test
            self.index_name = f"test_integration_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.kb = ElasticsearchKnowledgeBase(index_name=self.index_name)
            
            if not self.kb.client:
                pytest.skip("Elasticsearch non disponible ou non configuré")
                
        except Exception as e:
            pytest.skip(f"Erreur lors de l'initialisation d'Elasticsearch: {e}")
    
    def teardown_method(self):
        """Nettoie l'index de test après les tests."""
        try:
            if hasattr(self, 'kb') and self.kb.client and self.kb.client.indices.exists(index=self.index_name):
                self.kb.client.indices.delete(index=self.index_name)
        except Exception as e:
            print(f"Erreur lors du nettoyage de l'index: {e}")
    
    def test_elasticsearch_real_search(self):
        """Test de recherche réelle dans Elasticsearch."""
        # Ajout de documents de test
        test_docs = [
            Document(
                title="Configuration des VLANs",
                content="Guide complet pour configurer des VLANs sur des équipements Cisco",
                metadata={"type": "guide", "equipment": "cisco"}
            ),
            Document(
                title="Dépannage DNS",
                content="Procédures de dépannage pour résoudre les problèmes DNS courants",
                metadata={"type": "troubleshooting", "domain": "dns"}
            ),
            Document(
                title="Sécurisation des routeurs",
                content="Bonnes pratiques pour sécuriser les routeurs de l'entreprise",
                metadata={"type": "security", "equipment": "router"}
            )
        ]
        
        # Ajouter les documents
        for doc in test_docs:
            doc_id = self.kb.add_document(doc)
            assert doc_id, "L'ajout du document a échoué"
        
        # Attendre l'indexation
        time.sleep(2)
        
        # Test de recherche
        results = self.kb.search("cisco vlan", limit=5, threshold=0.1)
        
        # Vérifications
        assert isinstance(results, list)
        assert len(results) > 0
        assert "cisco" in results[0]["content"].lower() or "vlan" in results[0]["content"].lower()
        assert results[0]["score"] > 0
    
    def test_elasticsearch_document_operations(self):
        """Test des opérations CRUD sur les documents."""
        # Création d'un document
        doc = Document(
            title="Test CRUD Elasticsearch",
            content="Contenu de test pour les opérations CRUD",
            metadata={"test_type": "crud", "version": 1}
        )
        
        # Ajout
        doc_id = self.kb.add_document(doc)
        assert doc_id, "L'ajout du document a échoué"
        
        # Attendre l'indexation
        time.sleep(1)
        
        # Récupération
        retrieved_doc = self.kb.get_document(doc_id)
        assert retrieved_doc is not None
        assert retrieved_doc.title == doc.title
        assert retrieved_doc.content == doc.content
        
        # Mise à jour
        updated_doc = Document(
            title="Test CRUD Elasticsearch - Mis à jour",
            content="Contenu mis à jour pour les opérations CRUD",
            metadata={"test_type": "crud", "version": 2}
        )
        
        update_result = self.kb.update_document(doc_id, updated_doc)
        assert update_result is True
        
        # Attendre l'indexation
        time.sleep(1)
        
        # Vérification de la mise à jour
        retrieved_updated_doc = self.kb.get_document(doc_id)
        assert retrieved_updated_doc is not None
        assert retrieved_updated_doc.title == updated_doc.title
        assert retrieved_updated_doc.metadata.get("version") == 2
        
        # Suppression
        delete_result = self.kb.delete_document(doc_id)
        assert delete_result is True
        
        # Attendre l'indexation
        time.sleep(1)
        
        # Vérification de la suppression
        try:
            deleted_doc = self.kb.get_document(doc_id)
            # Si on arrive ici sans exception, le document existe encore
            assert deleted_doc is None, "Le document n'a pas été supprimé correctement"
        except KnowledgeBaseException:
            # C'est normal si le document n'existe plus
            pass


class TestRealWorkflow:
    """Tests des workflows complets avec intégrations réelles."""
    
    @pytest.mark.requires_api_keys
    @pytest.mark.requires_elasticsearch
    def test_combined_real_integrations(self):
        """Test combinant OpenAI et Elasticsearch dans un workflow réel."""
        # Skip if no API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not provided")
        
        try:
            # Créer l'index Elasticsearch temporaire
            index_name = f"test_workflow_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            kb = ElasticsearchKnowledgeBase(index_name=index_name)
            
            if not kb.client:
                pytest.skip("Elasticsearch non disponible ou non configuré")
                
            # Ajouter des documents
            kb.add_document(Document(
                title="Dépannage Réseau WiFi",
                content="1. Vérifier la force du signal\n2. Vérifier les interférences\n3. Tester avec un autre dispositif",
                metadata={"type": "troubleshooting"}
            ))
            
            # Attendre l'indexation
            time.sleep(2)
            
            # Créer client OpenAI
            client = DefaultAIClient("gpt-3.5-turbo")
            
            # Effectuer une recherche
            search_results = kb.search("problème wifi signal faible", limit=2, threshold=0.1)
            assert len(search_results) > 0
            
            # Enrichir le contexte avec les résultats
            context = [
                "system: Tu es un expert en dépannage réseau.",
                f"assistant: Voici des informations utiles: {search_results[0]['content']}"
            ]
            
            # Générer une réponse avec le contexte enrichi
            response = client.generate_response(
                "J'ai un problème de connexion WiFi faible, que dois-je faire?",
                context=context
            )
            
            # Vérifications
            assert 'content' in response
            assert len(response['content']) > 50
            
            # La réponse devrait mentionner le signal et des étapes de dépannage
            assert any(term in response['content'].lower() 
                    for term in ["signal", "interférence", "dispositif"])
            
        finally:
            # Nettoyage
            try:
                if 'kb' in locals() and kb.client and kb.client.indices.exists(index=index_name):
                    kb.client.indices.delete(index=index_name)
            except Exception as e:
                print(f"Erreur lors du nettoyage: {e}") 