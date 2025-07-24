"""
Interfaces du domaine pour l'assistant IA.

Ce module définit les interfaces du domaine pour l'assistant IA
selon les principes de l'architecture hexagonale.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class AIClient(ABC):
    """
    Interface pour le client IA.
    
    Cette interface définit le contrat que doit respecter
    tout client IA utilisé par l'assistant.
    """
    
    @abstractmethod
    def generate_response(
        self, 
        message: str,
        context: List[str] = None
    ) -> Dict[str, Any]:
        """
        Génère une réponse à partir d'un message et d'un contexte.
        
        Args:
            message: Contenu du message
            context: Liste de messages précédents pour contexte
            
        Returns:
            Dictionnaire contenant la réponse générée avec:
            - content: Contenu de la réponse
            - actions: Actions suggérées
            - sources: Sources utilisées
            - processing_time: Temps de traitement
        """
        pass
    
    @abstractmethod
    def analyze_command(self, command: str) -> Dict[str, Any]:
        """
        Analyse une commande pour déterminer sa validité et son intention.
        
        Args:
            command: La commande à analyser
            
        Returns:
            Dictionnaire avec l'analyse de la commande:
            - is_valid: Si la commande est valide
            - safety_level: Niveau de sécurité
            - intent: Intention détectée
            - reason: Raison de l'analyse
        """
        pass


class CommandExecutor(ABC):
    """
    Interface pour l'exécuteur de commandes.
    
    Cette interface définit le contrat que doit respecter
    tout exécuteur de commandes utilisé par l'assistant.
    """
    
    @abstractmethod
    def execute(
        self,
        command: str,
        command_type: str,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Exécute une commande.
        
        Args:
            command: Commande à exécuter
            command_type: Type de commande
            user_id: ID de l'utilisateur
            
        Returns:
            Résultat de l'exécution
        """
        pass
    
    @abstractmethod
    def validate(self, command: str, command_type: str) -> Dict[str, Any]:
        """
        Valide une commande.
        
        Args:
            command: Commande à valider
            command_type: Type de commande
            
        Returns:
            Résultat de la validation
        """
        pass


class KnowledgeBase(ABC):
    """
    Interface pour la base de connaissances.
    
    Cette interface définit le contrat que doit respecter
    toute base de connaissances utilisée par l'assistant.
    """
    
    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Recherche des documents pertinents pour une requête.
        
        Args:
            query: Requête de recherche
            limit: Nombre maximum de documents à retourner
            threshold: Seuil de pertinence
            
        Returns:
            Liste de documents pertinents
        """
        pass
    
    @abstractmethod
    def add_document(
        self,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ajoute un document à la base de connaissances.
        
        Args:
            document: Document à ajouter
            
        Returns:
            Résultat de l'opération
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        Supprime un document de la base de connaissances.
        
        Args:
            document_id: ID du document
            
        Returns:
            True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def update_document(
        self,
        document_id: str,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Met à jour un document dans la base de connaissances.
        
        Args:
            document_id: ID du document
            document: Nouvelles données du document
            
        Returns:
            Document mis à jour
        """
        pass


class AIAssistantRepository(ABC):
    """
    Interface pour le repository de l'assistant IA.
    
    Cette interface définit le contrat que doit respecter
    tout repository utilisé par l'assistant.
    """
    
    @abstractmethod
    def create_conversation(
        self,
        title: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Crée une nouvelle conversation.
        
        Args:
            title: Titre de la conversation
            user_id: ID de l'utilisateur
            
        Returns:
            Conversation créée
        """
        pass
    
    @abstractmethod
    def get_conversation(self, conversation_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère une conversation par son ID.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            Conversation ou None si non trouvée
        """
        pass
    
    @abstractmethod
    def get_user_conversations(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Récupère toutes les conversations d'un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des conversations
        """
        pass
    
    @abstractmethod
    def update_conversation(
        self,
        conversation_id: int,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Met à jour une conversation.
        
        Args:
            conversation_id: ID de la conversation
            title: Nouveau titre (optionnel)
            metadata: Nouvelles métadonnées (optionnel)
            
        Returns:
            Conversation mise à jour
        """
        pass
    
    @abstractmethod
    def delete_conversation(self, conversation_id: int) -> bool:
        """
        Supprime une conversation.
        
        Args:
            conversation_id: ID de la conversation
            
        Returns:
            True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def add_message(
        self,
        conversation_id: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ajoute un message à une conversation.
        
        Args:
            conversation_id: ID de la conversation
            role: Rôle du message (user, assistant, system)
            content: Contenu du message
            metadata: Métadonnées du message
            
        Returns:
            Message ajouté
        """
        pass
    
    @abstractmethod
    def get_conversation_messages(
        self,
        conversation_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Récupère les messages d'une conversation.
        
        Args:
            conversation_id: ID de la conversation
            limit: Nombre maximum de messages à retourner
            offset: Décalage pour la pagination
            
        Returns:
            Liste des messages
        """
        pass
    
    @abstractmethod
    def delete_message(self, message_id: int) -> bool:
        """
        Supprime un message.
        
        Args:
            message_id: ID du message
            
        Returns:
            True si la suppression a réussi
        """
        pass


# Alias pour compatibilité avec les tests existants
CommandExecutorInterface = CommandExecutor
KnowledgeBaseInterface = KnowledgeBase 