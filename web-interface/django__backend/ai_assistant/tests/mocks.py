"""
Mocks pour les tests.

Ce module contient les implémentations de mocks pour simuler
les dépendances externes lors des tests.
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime
import os
import uuid

from ai_assistant.domain.entities import Message, Conversation, MessageRole, Document, SearchResult
from ai_assistant.domain.interfaces import AIClient, CommandExecutorInterface, KnowledgeBaseInterface
from ai_assistant.domain.repositories import ConversationRepositoryInterface


class MockAIClient(AIClient):
    """Mock pour le client AI."""
    
    def __init__(self, responses: Dict[str, Any] = None, errors: Dict[str, Any] = None):
        """
        Initialise le mock avec des réponses prédéfinies.
        
        Args:
            responses: Dictionnaire de réponses prédéfinies par type de requête
            errors: Dictionnaire d'erreurs à lever pour certains types de requêtes
        """
        self.responses = responses or {}
        self.errors = errors or {}
        self.calls = []
    
    def generate_response(self, conversation: Conversation, message_content: str) -> Dict[str, Any]:
        """
        Génère une réponse simulée à partir d'une conversation et d'un message.
        
        Args:
            conversation: Conversation pour laquelle générer une réponse
            message_content: Contenu du message utilisateur
            
        Returns:
            Dictionnaire contenant la réponse générée
        """
        self.calls.append({
            "method": "generate_response",
            "conversation_id": conversation.id if conversation else None,
            "message_content": message_content
        })
        
        # Si une erreur est configurée pour cette méthode, la lever
        if "generate_response" in self.errors:
            raise self.errors["generate_response"]
        
        # Retourner une réponse prédéfinie ou une réponse par défaut
        if "generate_response" in self.responses:
            return self.responses["generate_response"]
        
        return {
            "content": f"Réponse simulée à: {message_content}",
            "actions": [],
            "processing_time": 0.1,
            "model_info": {
                "model": "mock-model",
                "usage": {
                    "total_tokens": 50,
                    "prompt_tokens": 25,
                    "completion_tokens": 25
                }
            }
        }
    
    def analyze_command(self, command: str) -> Dict[str, Any]:
        """
        Analyse une commande simulée.
        
        Args:
            command: Commande à analyser
            
        Returns:
            Dictionnaire contenant l'analyse de la commande
        """
        self.calls.append({
            "method": "analyze_command",
            "command": command
        })
        
        # Si une erreur est configurée pour cette méthode, la lever
        if "analyze_command" in self.errors:
            raise self.errors["analyze_command"]
        
        # Retourner une réponse prédéfinie ou une réponse par défaut
        if "analyze_command" in self.responses:
            return self.responses["analyze_command"]
        
        # Analyse par défaut basée sur des mots-clés simples
        is_dangerous = any(kw in command.lower() for kw in ["rm -rf", "drop", "delete", "truncate"])
        
        return {
            "is_valid": not is_dangerous,
            "safety_level": "dangerous" if is_dangerous else "safe",
            "intent": "delete" if is_dangerous else "query",
            "reason": "Commande potentiellement dangereuse" if is_dangerous else "Commande sûre"
        }


class MockCommandExecutor(CommandExecutorInterface):
    """Mock pour l'exécuteur de commandes."""
    
    def __init__(self, responses: Dict[str, Any] = None, errors: Dict[str, Any] = None):
        """
        Initialise le mock avec des réponses prédéfinies.
        
        Args:
            responses: Dictionnaire de réponses prédéfinies par type de requête
            errors: Dictionnaire d'erreurs à lever pour certains types de requêtes
        """
        self.responses = responses or {}
        self.errors = errors or {}
        self.calls = []
        self.allowed_commands = ["ls", "ping", "cat", "echo", "grep", "find"]
    
    def validate(self, command: str, command_type: str) -> Dict[str, Any]:
        """
        Valide une commande simulée.
        
        Args:
            command: Commande à valider
            command_type: Type de commande
            
        Returns:
            Dictionnaire contenant le résultat de la validation
        """
        self.calls.append({
            "method": "validate",
            "command": command,
            "command_type": command_type
        })
        
        # Si une erreur est configurée pour cette méthode, la lever
        if "validate" in self.errors:
            raise self.errors["validate"]
        
        # Retourner une réponse prédéfinie ou une réponse par défaut
        if "validate" in self.responses:
            return self.responses["validate"]
        
        # Validation par défaut basée sur la liste des commandes autorisées
        cmd_base = command.split()[0] if command else ""
        is_valid = cmd_base in self.allowed_commands
        
        return {
            "is_valid": is_valid,
            "reason": "Commande autorisée" if is_valid else "Commande non autorisée"
        }
    
    def execute(self, command: str, command_type: str, user_id: str) -> Dict[str, Any]:
        """
        Exécute une commande simulée.
        
        Args:
            command: Commande à exécuter
            command_type: Type de commande
            user_id: Identifiant de l'utilisateur
            
        Returns:
            Dictionnaire contenant le résultat de l'exécution
        """
        self.calls.append({
            "method": "execute",
            "command": command,
            "command_type": command_type,
            "user_id": user_id
        })
        
        # Si une erreur est configurée pour cette méthode, la lever
        if "execute" in self.errors:
            raise self.errors["execute"]
        
        # Retourner une réponse prédéfinie ou une réponse par défaut
        if "execute" in self.responses:
            return self.responses["execute"]
        
        # Exécution simulée avec des réponses spécifiques pour certaines commandes
        if command.startswith("ls"):
            output = "file1.txt\nfile2.txt\ndir1\ndir2"
        elif command.startswith("ping"):
            output = "PING example.com (93.184.216.34): 56 data bytes\n64 bytes from 93.184.216.34: icmp_seq=0 ttl=56 time=11.632 ms"
        elif command.startswith("cat"):
            output = "Contenu simulé du fichier"
        else:
            output = f"Exécution simulée de: {command}"
        
        return {
            "success": True,
            "output": output,
            "error": "",
            "exit_code": 0,
            "execution_time": 0.1
        }
    
    def get_allowed_commands(self) -> List[str]:
        """
        Retourne la liste des commandes autorisées.
        
        Returns:
            Liste des commandes autorisées
        """
        self.calls.append({
            "method": "get_allowed_commands"
        })
        
        return self.allowed_commands


class MockKnowledgeBase(KnowledgeBaseInterface):
    """Mock pour la base de connaissances."""
    
    def __init__(self, documents: Dict[str, Document] = None, search_results: List[SearchResult] = None):
        """
        Initialise le mock avec des documents prédéfinis.
        
        Args:
            documents: Dictionnaire de documents prédéfinis par ID
            search_results: Liste de résultats de recherche prédéfinis
        """
        self.documents = documents or {}
        self.search_results = search_results or []
        self.calls = []
    
    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        """
        Recherche dans la base de connaissances simulée.
        
        Args:
            query: Requête de recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            Liste des résultats de recherche
        """
        self.calls.append({
            "method": "search",
            "query": query,
            "max_results": max_results
        })
        
        # Retourner les résultats prédéfinis ou une liste vide
        results = self.search_results[:max_results] if self.search_results else []
        
        return results
    
    def add_document(self, title: str, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        Ajoute un document à la base de connaissances simulée.
        
        Args:
            title: Titre du document
            content: Contenu du document
            metadata: Métadonnées du document
            
        Returns:
            Identifiant du document ajouté
        """
        self.calls.append({
            "method": "add_document",
            "title": title,
            "content": content,
            "metadata": metadata
        })
        
        # Créer un nouveau document
        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        self.documents[doc_id] = Document(
            title=title,
            content=content,
            metadata=metadata or {}
        )
        
        return doc_id
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Récupère un document de la base de connaissances simulée.
        
        Args:
            document_id: Identifiant du document
            
        Returns:
            Document ou None si non trouvé
        """
        self.calls.append({
            "method": "get_document",
            "document_id": document_id
        })
        
        # Retourner le document s'il existe
        return self.documents.get(document_id)
    
    def delete_document(self, document_id: str) -> bool:
        """
        Supprime un document de la base de connaissances simulée.
        
        Args:
            document_id: Identifiant du document
            
        Returns:
            True si le document a été supprimé, False sinon
        """
        self.calls.append({
            "method": "delete_document",
            "document_id": document_id
        })
        
        # Supprimer le document s'il existe
        if document_id in self.documents:
            del self.documents[document_id]
            return True
        
        return False


class MockConversationRepository(ConversationRepositoryInterface):
    """Mock pour le repository de conversations."""
    
    def __init__(self, conversations: Dict[str, Conversation] = None):
        """
        Initialise le mock avec des conversations prédéfinies.
        
        Args:
            conversations: Dictionnaire de conversations prédéfinies par ID
        """
        self.conversations = conversations or {}
        self.calls = []
    
    def save_conversation(self, conversation: Conversation) -> str:
        """
        Enregistre une conversation simulée.
        
        Args:
            conversation: Conversation à enregistrer
            
        Returns:
            Identifiant de la conversation
        """
        self.calls.append({
            "method": "save_conversation",
            "conversation": conversation
        })
        
        # Si la conversation n'a pas d'ID, en générer un
        if not conversation.id:
            conversation_id = f"conv_{uuid.uuid4().hex[:8]}"
            conversation.id = conversation_id
        else:
            conversation_id = conversation.id
        
        # Enregistrer la conversation
        self.conversations[conversation_id] = conversation
        
        return conversation_id
    
    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Récupère une conversation simulée.
        
        Args:
            conversation_id: Identifiant de la conversation
            
        Returns:
            Conversation ou None si non trouvée
        """
        self.calls.append({
            "method": "get_conversation",
            "conversation_id": conversation_id
        })
        
        # Retourner la conversation si elle existe
        return self.conversations.get(conversation_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Supprime une conversation simulée.
        
        Args:
            conversation_id: Identifiant de la conversation
            
        Returns:
            True si la conversation a été supprimée, False sinon
        """
        self.calls.append({
            "method": "delete_conversation",
            "conversation_id": conversation_id
        })
        
        # Supprimer la conversation si elle existe
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        
        return False
    
    def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """
        Récupère les conversations d'un utilisateur simulé.
        
        Args:
            user_id: Identifiant de l'utilisateur
            
        Returns:
            Liste des conversations de l'utilisateur
        """
        self.calls.append({
            "method": "get_user_conversations",
            "user_id": user_id
        })
        
        # Filtrer les conversations par user_id
        return [conv for conv in self.conversations.values() if conv.user_id == user_id] 