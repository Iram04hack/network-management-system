"""
Package de modèles pour le domaine de l'assistant IA.

Ce package contient les modèles de données du domaine de l'assistant IA.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class Message:
    """Représente un message dans une conversation."""
    
    role: str
    content: str
    id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Conversation:
    """Représente une conversation entre un utilisateur et l'assistant IA."""
    
    title: str
    user_id: str
    id: Optional[str] = None
    messages: List[Message] = field(default_factory=list)
    context: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    """Représente un document stocké dans le système."""
    
    title: str
    content: str
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult:
    """Représente un résultat de recherche."""
    
    title: str
    content: str
    score: float
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandResult:
    """Représente le résultat d'une commande exécutée."""
    
    command: str
    exit_code: int
    stdout: str
    stderr: str
    success: bool


@dataclass
class AIResponse:
    """Représente une réponse générée par l'IA."""
    
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict) 