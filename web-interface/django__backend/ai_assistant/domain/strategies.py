"""
Stratégies du domaine pour l'assistant IA.

Ce module définit les stratégies de traitement des messages
selon les principes de l'architecture hexagonale.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .entities import Message, CommandRequest, CommandResult


class MessageProcessingStrategy(ABC):
    """Stratégie abstraite pour le traitement des messages."""
    
    @abstractmethod
    def can_handle(self, message: Message) -> bool:
        """Détermine si cette stratégie peut traiter le message."""
        pass
    
    @abstractmethod
    def process(self, message: Message, context: Dict[str, Any]) -> Dict[str, Any]:
        """Traite le message selon cette stratégie."""
        pass


class ConversationalMessageStrategy(MessageProcessingStrategy):
    """Stratégie pour les messages conversationnels normaux."""
    
    def can_handle(self, message: Message) -> bool:
        """Détermine si c'est un message conversationnel."""
        content = message.content.lower()
        
        # Mots-clés indiquant une commande
        command_keywords = [
            'execute', 'run', 'show', 'configure', 'set',
            'ping', 'traceroute', 'restart', 'reboot'
        ]
        
        # Si contient des mots-clés de commande, ce n'est pas conversationnel
        return not any(keyword in content for keyword in command_keywords)
    
    def process(self, message: Message, context: Dict[str, Any]) -> Dict[str, Any]:
        """Traite comme un message conversationnel."""
        return {
            'strategy': 'conversational',
            'requires_ai': True,
            'requires_knowledge_base': True,
            'requires_command_execution': False,
            'confidence': 0.8
        }


class CommandMessageStrategy(MessageProcessingStrategy):
    """Stratégie pour les messages contenant des commandes."""
    
    def can_handle(self, message: Message) -> bool:
        """Détermine si c'est un message de commande."""
        content = message.content.lower()
        
        command_keywords = [
            'execute', 'run', 'show', 'configure', 'set',
            'ping', 'traceroute', 'restart', 'reboot'
        ]
        
        return any(keyword in content for keyword in command_keywords)
    
    def process(self, message: Message, context: Dict[str, Any]) -> Dict[str, Any]:
        """Traite comme un message de commande."""
        return {
            'strategy': 'command',
            'requires_ai': True,
            'requires_knowledge_base': False,
            'requires_command_execution': True,
            'confidence': 0.9,
            'extracted_command': self._extract_command(message.content)
        }
    
    def _extract_command(self, content: str) -> Optional[str]:
        """Extrait la commande du message."""
        # Simple extraction - peut être améliorée
        content_lower = content.lower()
        
        if 'show' in content_lower:
            return 'show'
        elif 'ping' in content_lower:
            return 'ping'
        elif 'configure' in content_lower:
            return 'configure'
        
        return None


class KnowledgeBaseQueryStrategy(MessageProcessingStrategy):
    """Stratégie pour les requêtes de base de connaissances."""
    
    def can_handle(self, message: Message) -> bool:
        """Détermine si c'est une requête de base de connaissances."""
        content = message.content.lower()
        
        knowledge_keywords = [
            'comment', 'pourquoi', 'qu\'est-ce que', 'expliquer',
            'définition', 'documentation', 'aide', 'tutoriel'
        ]
        
        return any(keyword in content for keyword in knowledge_keywords)
    
    def process(self, message: Message, context: Dict[str, Any]) -> Dict[str, Any]:
        """Traite comme une requête de base de connaissances."""
        return {
            'strategy': 'knowledge_query',
            'requires_ai': True,
            'requires_knowledge_base': True,
            'requires_command_execution': False,
            'confidence': 0.85,
            'query_type': self._identify_query_type(message.content)
        }
    
    def _identify_query_type(self, content: str) -> str:
        """Identifie le type de requête."""
        content_lower = content.lower()
        
        if 'comment' in content_lower:
            return 'how_to'
        elif 'qu\'est-ce que' in content_lower or 'définition' in content_lower:
            return 'definition'
        elif 'pourquoi' in content_lower:
            return 'explanation'
        
        return 'general'


class CommandProcessingStrategy(ABC):
    """Stratégie abstraite pour le traitement des commandes."""
    
    @abstractmethod
    def can_execute(self, command_request: CommandRequest) -> bool:
        """Détermine si cette stratégie peut exécuter la commande."""
        pass
    
    @abstractmethod
    def execute(self, command_request: CommandRequest) -> CommandResult:
        """Exécute la commande selon cette stratégie."""
        pass


class NetworkDiagnosticCommandStrategy(CommandProcessingStrategy):
    """Stratégie pour les commandes de diagnostic réseau."""
    
    def can_execute(self, command_request: CommandRequest) -> bool:
        """Vérifie si c'est une commande de diagnostic réseau."""
        command = command_request.command.lower()
        
        diagnostic_commands = ['ping', 'traceroute', 'nslookup', 'dig', 'netstat']
        return any(cmd in command for cmd in diagnostic_commands)
    
    def execute(self, command_request: CommandRequest) -> CommandResult:
        """Exécute une commande de diagnostic réseau."""
        # Simulation - dans la vraie implémentation, on exécuterait la commande
        return CommandResult(
            success=True,
            output=f"Résultat simulé pour: {command_request.command}",
            execution_time=1.0
        )


class DeviceCommandStrategy(CommandProcessingStrategy):
    """Stratégie pour les commandes d'équipements réseau."""
    
    def can_execute(self, command_request: CommandRequest) -> bool:
        """Vérifie si c'est une commande d'équipement."""
        command = command_request.command.lower()
        
        device_commands = ['show', 'configure', 'interface', 'vlan', 'route']
        return any(cmd in command for cmd in device_commands)
    
    def execute(self, command_request: CommandRequest) -> CommandResult:
        """Exécute une commande d'équipement."""
        # Vérification de sécurité
        if self._is_dangerous_command(command_request.command):
            return CommandResult(
                success=False,
                output="",
                error_message="Commande dangereuse bloquée pour des raisons de sécurité"
            )
        
        # Simulation d'exécution
        return CommandResult(
            success=True,
            output=f"Configuration appliquée: {command_request.command}",
            execution_time=2.0
        )
    
    def _is_dangerous_command(self, command: str) -> bool:
        """Vérifie si la commande est dangereuse."""
        dangerous_keywords = ['delete', 'erase', 'format', 'reload', 'shutdown']
        command_lower = command.lower()
        
        return any(keyword in command_lower for keyword in dangerous_keywords)


class SystemCommandStrategy(CommandProcessingStrategy):
    """Stratégie pour les commandes système."""
    
    def can_execute(self, command_request: CommandRequest) -> bool:
        """Vérifie si c'est une commande système."""
        return command_request.command_type == "system"
    
    def execute(self, command_request: CommandRequest) -> CommandResult:
        """Exécute une commande système."""
        # Vérification des permissions
        if not self._has_permission(command_request):
            return CommandResult(
                success=False,
                output="",
                error_message="Permission refusée pour cette commande système"
            )
        
        # Exécution réelle (à implémenter)
        return CommandResult(
            success=True,
            output=f"Commande système exécutée: {command_request.command}",
            execution_time=0.5
        )
    
    def _has_permission(self, command_request: CommandRequest) -> bool:
        """Vérifie si l'utilisateur a la permission."""
        # Logique de vérification de permissions à implémenter
        return True


class MessageStrategySelector:
    """Sélecteur de stratégie pour les messages."""
    
    def __init__(self):
        self.strategies = [
            CommandMessageStrategy(),
            KnowledgeBaseQueryStrategy(),
            ConversationalMessageStrategy()  # Fallback strategy
        ]
    
    def select_strategy(self, message: Message) -> MessageProcessingStrategy:
        """Sélectionne la stratégie appropriée pour le message."""
        for strategy in self.strategies:
            if strategy.can_handle(message):
                return strategy
        
        # Fallback to conversational if no strategy matches
        return self.strategies[-1]


class CommandStrategySelector:
    """Sélecteur de stratégie pour les commandes."""
    
    def __init__(self):
        self.strategies = [
            NetworkDiagnosticCommandStrategy(),
            DeviceCommandStrategy(),
            SystemCommandStrategy()
        ]
    
    def select_strategy(self, command_request: CommandRequest) -> Optional[CommandProcessingStrategy]:
        """Sélectionne la stratégie appropriée pour la commande."""
        for strategy in self.strategies:
            if strategy.can_execute(command_request):
                return strategy
        
        return None 