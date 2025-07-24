"""
Service d'intelligence artificielle.

Ce module contient le service pour interagir avec les modèles d'IA.
"""

import logging
import time
from typing import List, Dict, Any, Optional

from ai_assistant.domain.models import Conversation, AIResponse
from ai_assistant.domain.exceptions import AIServiceError

logger = logging.getLogger(__name__)


class AIService:
    """Service pour interagir avec les modèles d'IA."""
    
    def __init__(self):
        """Initialise le service d'IA."""
        # Configuration du modèle d'IA
        self.model_config = {
            "model": "gpt-3.5-turbo",  # Modèle par défaut
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
        }
    
    def generate_response(self, conversation: Conversation, user_message: str) -> AIResponse:
        """
        Génère une réponse de l'IA à partir d'une conversation et d'un message utilisateur.
        
        Args:
            conversation: Conversation en cours
            user_message: Message de l'utilisateur
            
        Returns:
            AIResponse: Réponse générée par l'IA
            
        Raises:
            AIServiceError: Si une erreur se produit lors de la génération de la réponse
        """
        try:
            # Importer le client IA depuis l'infrastructure
            from ai_assistant.infrastructure.ai_client_impl import DefaultAIClient
            
            # Utiliser le vrai client IA
            ai_client = DefaultAIClient()
            
            # Construire le contexte de la conversation
            context = [f"{msg.role}: {msg.content}" for msg in conversation.messages[-10:]]
            
            # Appel réel à l'IA
            start_time = time.time()
            ai_response = ai_client.generate_response(user_message, context)
            processing_time = time.time() - start_time
            
            # Créer la réponse
            response = AIResponse(
                content=ai_response.get('content', ''),
                metadata={
                    "model_info": ai_response.get('model_info', {}),
                    "processing_info": {
                        "processing_time": ai_response.get('processing_time', processing_time),
                    },
                    "actions": ai_response.get('actions', []),
                    "sources": ai_response.get('sources', [])
                }
            )
            
            return response
        
        except Exception as e:
            logger.exception("Erreur lors de la génération de la réponse")
            raise AIServiceError(f"Erreur lors de la génération de la réponse: {str(e)}")
    
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Génère des embeddings pour un texte donné.
        
        Args:
            text: Texte pour lequel générer des embeddings
            
        Returns:
            List[float]: Liste des embeddings
            
        Raises:
            AIServiceError: Si une erreur se produit lors de la génération des embeddings
            ValueError: Si le texte est vide
        """
        if not text:
            raise ValueError("Le texte ne peut pas être vide")
        
        try:
            # Importer le client IA depuis l'infrastructure
            from ai_assistant.infrastructure.ai_client_impl import DefaultAIClient
            
            # Utiliser le vrai client IA
            ai_client = DefaultAIClient()
            
            # Appel réel à l'IA
            embeddings = ai_client.generate_embeddings(text)
            
            return embeddings
        
        except Exception as e:
            logger.exception("Erreur lors de la génération des embeddings")
            raise AIServiceError(f"Erreur lors de la génération des embeddings: {str(e)}")
    
    def generate_title(self, conversation: Conversation) -> str:
        """
        Génère un titre pour une conversation.
        
        Args:
            conversation: Conversation pour laquelle générer un titre
            
        Returns:
            str: Titre généré
            
        Raises:
            AIServiceError: Si une erreur se produit lors de la génération du titre
        """
        try:
            # Extraire le premier message de l'utilisateur
            user_messages = [msg for msg in conversation.messages if msg.role == "user"]
            if not user_messages:
                return "Nouvelle conversation"
            
            first_user_message = user_messages[0].content
            
            # Limiter la longueur du message pour le prompt
            if len(first_user_message) > 100:
                first_user_message = first_user_message[:100] + "..."
            
            # Construire le prompt pour générer le titre
            prompt = f"Génère un titre court (5 mots maximum) pour une conversation qui commence par ce message: '{first_user_message}'"
            
            # Utiliser le vrai client IA
            from ai_assistant.infrastructure.ai_client_impl import DefaultAIClient
            ai_client = DefaultAIClient()
            
            try:
                ai_response = ai_client.generate_response(prompt, [])
                title = ai_response.get('content', '').strip().strip('"\'').strip()
                
                # Si le titre est vide ou trop long, utiliser un titre par défaut
                if not title or len(title) > 50:
                    return "Nouvelle conversation"
                
                return title
            except Exception:
                # En cas d'erreur IA, utiliser un titre basé sur le contenu
                return self._generate_fallback_title(first_user_message)
        
        except Exception as e:
            logger.exception("Erreur lors de la génération du titre")
            return "Nouvelle conversation"
    
    def _generate_fallback_title(self, message: str) -> str:
        """
        Génère un titre de fallback basé sur le contenu du message.
        
        Args:
            message: Le message à analyser
            
        Returns:
            str: Titre généré
        """
        # Extraire les mots-clés principaux
        import re
        
        # Nettoyer le message
        clean_message = re.sub(r'[^\w\s]', ' ', message.lower())
        words = clean_message.split()
        
        # Mots-clés réseau courants
        network_keywords = {
            'vlan': 'Configuration VLAN',
            'routeur': 'Configuration Routeur',
            'switch': 'Configuration Switch',
            'firewall': 'Configuration Firewall',
            'ping': 'Test Connectivité',
            'ip': 'Configuration IP',
            'réseau': 'Gestion Réseau',
            'configuration': 'Configuration Réseau',
            'sécurité': 'Sécurité Réseau',
            'performance': 'Performance Réseau',
            'problème': 'Dépannage Réseau',
            'erreur': 'Résolution Erreur'
        }
        
        # Chercher des mots-clés pertinents
        for word in words:
            if word in network_keywords:
                return network_keywords[word]
        
        # Si aucun mot-clé trouvé, utiliser les premiers mots
        title_words = words[:3]
        title = ' '.join(title_words).title()
        
        return title if len(title) <= 50 else "Nouvelle conversation"
    
    def _build_prompt(self, conversation: Conversation, user_message: str) -> str:
        """
        Construit un prompt pour l'IA à partir d'une conversation et d'un message utilisateur.
        
        Args:
            conversation: Conversation en cours
            user_message: Message de l'utilisateur
            
        Returns:
            str: Prompt pour l'IA
        """
        # Construire le contexte système
        system_prompt = (
            "Tu es un assistant IA spécialisé dans la gestion de réseau. "
            "Tu aides les utilisateurs à analyser leur réseau, à résoudre des problèmes "
            "et à optimiser leurs configurations. "
            "Réponds de manière concise et précise, en utilisant un ton professionnel."
        )
        
        # Ajouter le contexte de la conversation s'il existe
        if conversation.context:
            system_prompt += f"\n\nContexte supplémentaire: {conversation.context}"
        
        # Construire l'historique de la conversation
        history = []
        for message in conversation.messages[-10:]:  # Limiter à 10 messages pour éviter les prompts trop longs
            history.append(f"{message.role}: {message.content}")
        
        # Assembler le prompt final
        prompt = f"{system_prompt}\n\n"
        if history:
            prompt += "Historique de la conversation:\n" + "\n".join(history) + "\n\n"
        prompt += f"user: {user_message}\nassistant:"
        
        return prompt
    
 