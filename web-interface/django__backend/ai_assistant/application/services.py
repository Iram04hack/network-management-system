"""
Services de l'application pour l'assistant IA.

Ce module contient les services métier de l'assistant IA
qui orchestrent les différentes fonctionnalités.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..domain.interfaces import AIClient, CommandExecutor, KnowledgeBase, AIAssistantRepository
from ..domain.entities import Message, Conversation, MessageRole, Document, SearchResult, CommandResult
from ..domain.exceptions import AIClientException, CommandExecutionException, KnowledgeBaseException

logger = logging.getLogger(__name__)


class LegacyAIAssistantService:
    """
    Service principal de l'assistant IA.
    
    DÉPRÉCIÉ: Cette classe a été remplacée par AIAssistantService dans ai_assistant_service.py.
    Ne pas utiliser dans les nouveaux développements.
    
    Ce service orchestre les interactions entre l'utilisateur et l'assistant IA,
    en utilisant les différentes interfaces du domaine.
    """
    
    def __init__(
        self,
        ai_client: AIClient,
        command_executor: CommandExecutor,
        knowledge_base: KnowledgeBase,
        repository: AIAssistantRepository
    ):
        """
        Initialise le service de l'assistant IA.
        
        Args:
            ai_client: Client IA pour générer des réponses
            command_executor: Exécuteur de commandes
            knowledge_base: Base de connaissances
            repository: Repository pour la persistance
        """
        logger.warning("DÉPRÉCIÉ: LegacyAIAssistantService est déprécié. Utiliser AIAssistantService dans ai_assistant_service.py")
        self.ai_client = ai_client
        self.command_executor = command_executor
        self.knowledge_base = knowledge_base
        self.repository = repository
    
    def process_message(
        self,
        conversation_id: str,
        message_content: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Traite un message utilisateur et génère une réponse.
        
        Args:
            conversation_id: ID de la conversation
            message_content: Contenu du message
            user_id: ID de l'utilisateur
            
        Returns:
            Dictionnaire contenant la réponse et les métadonnées
        """
        try:
            # Récupération ou création de la conversation
            conversation = self.repository.get_conversation(conversation_id)
            if not conversation:
                # Création d'une nouvelle conversation
                conversation = Conversation(
                    id=None,
                    title=f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                    user_id=user_id,
                    messages=[],
                    context="assistant IA pour la gestion de réseau",
                    metadata={}
                )
                conversation_id = self.repository.save_conversation(conversation)
                conversation.id = conversation_id
            
            # Ajout du message utilisateur
            user_message = Message(
                id=None,
                role=MessageRole.USER,
                content=message_content,
                timestamp=datetime.now()
            )
            conversation.messages.append(user_message)
            
            # Préparation du contexte pour l'IA
            context = self._prepare_context(conversation)
            
            # Génération de la réponse
            ai_response = self.ai_client.generate_response(message_content, context)
            
            # Traitement des actions suggérées
            actions_taken = []
            if 'actions' in ai_response:
                actions_taken = self._process_actions(ai_response['actions'], user_id)
            
            # Création du message de réponse
            assistant_message = Message(
                id=None,
                role=MessageRole.ASSISTANT,
                content=ai_response['content'],
                timestamp=datetime.now(),
                metadata={
                    'processing_time': ai_response.get('processing_time', 0),
                    'model_info': ai_response.get('model_info', {})
                },
                actions_taken=actions_taken
            )
            conversation.messages.append(assistant_message)
            
            # Mise à jour du titre si c'est la première interaction
            if len(conversation.messages) <= 2:
                # Génération d'un titre basé sur le contenu
                title_summary = self._generate_title(message_content)
                conversation.title = title_summary
            
            # Sauvegarde de la conversation mise à jour
            self.repository.save_conversation(conversation)
            
            # Préparation de la réponse
            response = {
                'message': {
                    'content': assistant_message.content,
                    'role': assistant_message.role.value,
                    'timestamp': assistant_message.timestamp.isoformat(),
                    'actions_taken': assistant_message.actions_taken
                },
                'conversation': {
                    'id': conversation.id,
                    'title': conversation.title
                }
            }
            
            return response
        except Exception as e:
            logger.exception(f"Erreur lors du traitement du message: {e}")
            return {
                'error': str(e),
                'message': {
                    'content': f"Désolé, une erreur s'est produite lors du traitement de votre message: {str(e)}",
                    'role': MessageRole.ASSISTANT.value,
                    'timestamp': datetime.now().isoformat()
                }
            }
    
    def _prepare_context(self, conversation: Conversation) -> List[str]:
        """
        Prépare le contexte pour l'IA à partir de la conversation.
        
        Args:
            conversation: La conversation
            
        Returns:
            Liste des messages formatés pour le contexte
        """
        context = []
        
        # Ajout du contexte système
        if conversation.context:
            context.append(f"system: {conversation.context}")
        
        # Ajout des messages précédents (limités aux 10 derniers)
        recent_messages = conversation.messages[-10:] if len(conversation.messages) > 10 else conversation.messages
        
        for msg in recent_messages:
            prefix = "user: " if msg.role == MessageRole.USER else "assistant: "
            context.append(f"{prefix}{msg.content}")
        
        return context
    
    def _process_actions(self, actions: List[Dict[str, Any]], user_id: str) -> List[Dict[str, Any]]:
        """
        Traite les actions suggérées par l'IA.
        
        Args:
            actions: Liste des actions à traiter
            user_id: ID de l'utilisateur
            
        Returns:
            Liste des actions effectuées avec leur résultat
        """
        actions_taken = []
        
        for action in actions:
            action_type = action.get('type', '')
            action_data = action.get('data', {})
            
            try:
                if action_type == 'execute_command':
                    # Exécution d'une commande
                    command = action_data.get('command', '')
                    command_type = action_data.get('command_type', 'shell')
                    
                    # Validation de la commande
                    validation = self.command_executor.validate(command, command_type)
                    if not validation.get('is_valid', False):
                        actions_taken.append({
                            'type': action_type,
                            'status': 'failed',
                            'reason': validation.get('reason', 'Commande invalide'),
                            'data': action_data
                        })
                        continue
                    
                    # Exécution de la commande
                    result = self.command_executor.execute(command, command_type, user_id)
                    actions_taken.append({
                        'type': action_type,
                        'status': 'success' if result.get('success', False) else 'failed',
                        'data': {
                            'command': command,
                            'output': result.get('output', ''),
                            'error': result.get('error', '')
                        }
                    })
                
                elif action_type == 'search_knowledge':
                    # Recherche dans la base de connaissances
                    query = action_data.get('query', '')
                    limit = action_data.get('limit', 5)
                    
                    results = self.knowledge_base.search(query, limit)
                    actions_taken.append({
                        'type': action_type,
                        'status': 'success',
                        'data': {
                            'query': query,
                            'results': results
                        }
                    })
                
                else:
                    # Action non reconnue
                    actions_taken.append({
                        'type': action_type,
                        'status': 'skipped',
                        'reason': 'Type d\'action non supporté',
                        'data': action_data
                    })
            
            except Exception as e:
                logger.exception(f"Erreur lors du traitement de l'action {action_type}: {e}")
                actions_taken.append({
                    'type': action_type,
                    'status': 'error',
                    'reason': str(e),
                    'data': action_data
                })
        
        return actions_taken
    
    def _generate_title(self, message_content: str) -> str:
        """
        Génère un titre pour une conversation à partir du contenu du message.
        
        Args:
            message_content: Contenu du message
            
        Returns:
            Titre généré
        """
        # Simplification: utilisation des premiers mots du message
        words = message_content.split()
        if len(words) <= 5:
            return message_content
        
        return ' '.join(words[:5]) + '...'
    
    def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des conversations d'un utilisateur.
        
        Args:
            user_id: ID de l'utilisateur
            limit: Nombre maximum de conversations à retourner
            offset: Décalage pour la pagination
            
        Returns:
            Liste des conversations
        """
        try:
            conversations = self.repository.get_user_conversations(user_id)
            
            # Application de la pagination
            paginated = conversations[offset:offset + limit] if conversations else []
            
            # Conversion en dictionnaires
            result = []
            for conv in paginated:
                # Récupération du dernier message pour l'aperçu
                last_message = conv.messages[-1] if conv.messages else None
                
                result.append({
                    'id': conv.id,
                    'title': conv.title,
                    'created_at': conv.metadata.get('created_at', datetime.now().isoformat()),
                    'updated_at': conv.metadata.get('updated_at', datetime.now().isoformat()),
                    'preview': last_message.content[:100] + '...' if last_message and len(last_message.content) > 100 else (last_message.content if last_message else '')
                })
            
            return result
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération de l'historique des conversations: {e}")
            return []


class NetworkAnalysisService:
    """
    Service d'analyse réseau.
    
    Ce service fournit des fonctionnalités spécifiques à l'analyse
    et à la gestion des réseaux informatiques.
    """
    
    def __init__(
        self,
        command_executor: CommandExecutor,
        knowledge_base: KnowledgeBase
    ):
        """
        Initialise le service d'analyse réseau.
        
        Args:
            command_executor: Exécuteur de commandes
            knowledge_base: Base de connaissances
        """
        self.command_executor = command_executor
        self.knowledge_base = knowledge_base
    
    def analyze_network_topology(self, user_id: str) -> Dict[str, Any]:
        """
        Analyse la topologie du réseau.
        
        Args:
            user_id: ID de l'utilisateur
            
        Returns:
            Résultats de l'analyse
        """
        try:
            # Exécution des commandes pour récupérer la topologie
            commands = [
                ('ip addr', 'shell'),
                ('ip route', 'shell'),
                ('netstat -tuln', 'shell')
            ]
            
            results = {}
            for cmd, cmd_type in commands:
                result = self.command_executor.execute(cmd, cmd_type, user_id)
                if result.get('success', False):
                    results[cmd] = result.get('output', '')
                else:
                    error_msg = result.get('error', 'Échec de l\'exécution')
                    results[cmd] = f"Erreur: {error_msg}"
            
            # Analyse des résultats
            analysis = self._analyze_network_data(results)
            
            return {
                'topology': analysis,
                'raw_data': results
            }
        except Exception as e:
            logger.exception(f"Erreur lors de l'analyse de la topologie réseau: {e}")
            return {
                'error': str(e),
                'message': f"Erreur lors de l'analyse de la topologie réseau: {str(e)}"
            }
    
    def _analyze_network_data(self, data: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyse les données réseau brutes.
        
        Args:
            data: Données réseau brutes
            
        Returns:
            Analyse structurée
        """
        # Exemple simplifié d'analyse
        analysis = {
            'interfaces': [],
            'routes': [],
            'open_ports': []
        }
        
        # Analyse des interfaces
        if 'ip addr' in data:
            # Extraction des interfaces et adresses IP
            # Implémentation simplifiée
            interfaces_data = data['ip addr']
            # Analyse basique des interfaces
            for line in interfaces_data.split('\n'):
                if 'inet ' in line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        ip_addr = parts[1].split('/')[0]
                        analysis['interfaces'].append({
                            'ip': ip_addr
                        })
        
        # Analyse des routes
        if 'ip route' in data:
            # Extraction des routes
            # Implémentation simplifiée
            routes_data = data['ip route']
            for line in routes_data.split('\n'):
                if line.strip():
                    analysis['routes'].append({
                        'route': line.strip()
                    })
        
        # Analyse des ports ouverts
        if 'netstat -tuln' in data:
            # Extraction des ports ouverts
            # Implémentation simplifiée
            netstat_data = data['netstat -tuln']
            for line in netstat_data.split('\n'):
                if 'LISTEN' in line:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        local_addr = parts[3]
                        analysis['open_ports'].append({
                            'address': local_addr
                        })
        
        return analysis
    
    def get_network_recommendations(self) -> List[Dict[str, Any]]:
        """
        Fournit des recommandations pour l'optimisation du réseau.
        
        Returns:
            Liste de recommandations
        """
        try:
            # Recherche dans la base de connaissances
            results = self.knowledge_base.search("network optimization recommendations", 5)
            
            recommendations = []
            for result in results:
                recommendations.append({
                    'title': result.get('title', 'Recommandation'),
                    'description': result.get('content', ''),
                    'confidence': result.get('score', 0.0)
                })
            
            # Si pas assez de recommandations, ajouter des recommandations par défaut
            if len(recommendations) < 3:
                default_recommendations = [
                    {
                        'title': 'Sécurisation des ports ouverts',
                        'description': 'Vérifiez régulièrement les ports ouverts et fermez ceux qui ne sont pas nécessaires.',
                        'confidence': 0.9
                    },
                    {
                        'title': 'Mise à jour des équipements',
                        'description': 'Assurez-vous que tous les équipements réseau sont à jour avec les derniers firmwares.',
                        'confidence': 0.85
                    },
                    {
                        'title': 'Segmentation du réseau',
                        'description': 'Segmentez votre réseau en VLANs pour améliorer la sécurité et les performances.',
                        'confidence': 0.8
                    }
                ]
                
                for rec in default_recommendations:
                    if len(recommendations) < 5:
                        recommendations.append(rec)
            
            return recommendations
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des recommandations réseau: {e}")
            return [
                {
                    'title': 'Erreur',
                    'description': f"Impossible de récupérer les recommandations: {str(e)}",
                    'confidence': 0.0
                }
            ]
