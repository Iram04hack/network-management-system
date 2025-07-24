"""
Entités du domaine pour l'assistant IA.

Ce module définit les entités métier du domaine ai_assistant
selon les principes de l'architecture hexagonale.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    """Énumération des rôles de message."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """
    Entité Message représentant un message dans une conversation.
    
    Cette entité est pure et ne dépend d'aucune infrastructure.
    """
    role: MessageRole
    content: str
    timestamp: datetime
    id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    actions_taken: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        """Initialisation post-création."""
        if self.metadata is None:
            self.metadata = {}
        if self.actions_taken is None:
            self.actions_taken = []
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def add_action(self, action_type: str, data: Dict[str, Any]) -> None:
        """
        Ajoute une action prise pour ce message.
        
        Args:
            action_type: Type d'action
            data: Données de l'action
        """
        action = {
            "type": action_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.actions_taken.append(action)
    
    def get_text_content(self) -> str:
        """Retourne le contenu textuel du message."""
        return self.content
    
    def is_user_message(self) -> bool:
        """Vérifie si le message provient de l'utilisateur."""
        return self.role == MessageRole.USER
    
    def is_assistant_message(self) -> bool:
        """Vérifie si le message provient de l'assistant."""
        return self.role == MessageRole.ASSISTANT


@dataclass
class Conversation:
    """
    Entité Conversation représentant une conversation avec l'assistant.
    
    Cette entité encapsule la logique métier liée aux conversations.
    """
    title: str
    messages: List[Message]
    id: Optional[str] = None
    user_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True
    
    def __post_init__(self):
        """Initialisation post-création."""
        if self.messages is None:
            self.messages = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def add_message(self, message: Message) -> None:
        """
        Ajoute un message à la conversation.
        
        Args:
            message: Message à ajouter
        """
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def add_user_message(self, content: str) -> Message:
        """
        Ajoute un message utilisateur à la conversation.
        
        Args:
            content: Contenu du message
            
        Returns:
            Message créé et ajouté
        """
        message = Message(
            role=MessageRole.USER,
            content=content,
            timestamp=datetime.now()
        )
        self.add_message(message)
        return message
    
    def add_assistant_message(self, content: str) -> Message:
        """
        Ajoute un message assistant à la conversation.
        
        Args:
            content: Contenu du message
            
        Returns:
            Message créé et ajouté
        """
        message = Message(
            role=MessageRole.ASSISTANT,
            content=content,
            timestamp=datetime.now()
        )
        self.add_message(message)
        return message
    
    def get_last_message(self) -> Optional[Message]:
        """Retourne le dernier message de la conversation."""
        return self.messages[-1] if self.messages else None
    
    def get_user_messages(self) -> List[Message]:
        """Retourne tous les messages de l'utilisateur."""
        return [msg for msg in self.messages if msg.is_user_message()]
    
    def get_assistant_messages(self) -> List[Message]:
        """Retourne tous les messages de l'assistant."""
        return [msg for msg in self.messages if msg.is_assistant_message()]
    
    def get_message_count(self) -> int:
        """Retourne le nombre total de messages."""
        return len(self.messages)
    
    def get_context_for_ai(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """
        Génère le contexte pour l'IA à partir des messages récents.
        
        Args:
            max_messages: Nombre maximum de messages à inclure
            
        Returns:
            Liste de messages formatés pour l'IA
        """
        recent_messages = self.messages[-max_messages:]
        return [
            {
                "role": msg.role.value,
                "content": msg.content
            }
            for msg in recent_messages
        ]
    
    def update_title(self, new_title: str) -> None:
        """
        Met à jour le titre de la conversation.
        
        Args:
            new_title: Nouveau titre
        """
        self.title = new_title
        self.updated_at = datetime.now()
    
    def archive(self) -> None:
        """Archive la conversation."""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def reactivate(self) -> None:
        """Réactive la conversation."""
        self.is_active = True
        self.updated_at = datetime.now()


@dataclass
class CommandRequest:
    """
    Entité représentant une demande d'exécution de commande.
    """
    command: str
    command_type: str
    user_id: str
    parameters: Optional[Dict[str, Any]] = None
    requested_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialisation post-création."""
        if self.parameters is None:
            self.parameters = {}
        if self.requested_at is None:
            self.requested_at = datetime.now()


@dataclass
class CommandResult:
    """
    Entité représentant le résultat d'une exécution de commande.
    """
    success: bool
    output: str
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    executed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialisation post-création."""
        if self.metadata is None:
            self.metadata = {}
        if self.executed_at is None:
            self.executed_at = datetime.now()


@dataclass
class KnowledgeDocument:
    """
    Entité représentant un document dans la base de connaissances.
    """
    title: str
    content: str
    category: str
    id: Optional[str] = None
    keywords: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    relevance_score: Optional[float] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialisation post-création."""
        if self.keywords is None:
            self.keywords = []
        if self.metadata is None:
            self.metadata = {}
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class AIResponse:
    """
    Entité représentant une réponse de l'IA.
    """
    content: str
    confidence: float
    sources: Optional[List[KnowledgeDocument]] = None
    suggested_actions: Optional[List[Dict[str, Any]]] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    
    def __post_init__(self):
        """Initialisation post-création."""
        if self.sources is None:
            self.sources = []
        if self.suggested_actions is None:
            self.suggested_actions = []


@dataclass
class Document:
    """
    Entité Document représentant un document dans la base de connaissances.
    
    Cette entité est utilisée par l'interface KnowledgeBase.
    """
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    
    def __post_init__(self):
        """Initialisation post-création."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class SearchResult:
    """
    Entité SearchResult représentant un résultat de recherche.
    
    Cette entité est utilisée par l'interface KnowledgeBase.
    """
    id: str
    title: str
    content: str
    score: float
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialisation post-création."""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class UserPreference:
    """
    Entité UserPreference représentant les préférences d'un utilisateur.
    
    Cette entité contient les préférences de l'utilisateur pour l'assistant IA.
    """
    user_id: str
    ai_model: Optional[str] = None
    language: str = "fr"
    theme: str = "light"
    notifications_enabled: bool = True
    max_history_items: int = 50
    custom_settings: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialisation post-création."""
        if self.custom_settings is None:
            self.custom_settings = {} 