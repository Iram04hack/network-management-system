"""
Service principal d'orchestration de l'assistant IA.

Ce module fournit l'implémentation du service d'assistant IA selon l'architecture hexagonale,
utilisant les interfaces du domaine.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, NamedTuple, Callable, Union, Generator
from datetime import datetime
import time

from ..domain.interfaces import AIClient, KnowledgeBase, AIAssistantRepository, CommandExecutor
from ..domain.entities import Message, MessageRole, Conversation
from ..domain.exceptions import AIClientException, CommandExecutionException, KnowledgeBaseException
from ..config import settings
from ..infrastructure.gns3_ai_adapter import gns3_ai_adapter

logger = logging.getLogger(__name__)

class AIResponse(NamedTuple):
    """
    Réponse structurée de l'assistant IA.
    
    Attributes:
        message: Contenu de la réponse
        context: Contexte utilisé pour générer la réponse
        confidence: Score de confiance (0.0-1.0)
        metadata: Métadonnées additionnelles
    """
    message: str
    context: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    metadata: Optional[Dict[str, Any]] = None


class AIAssistantService:
    """
    Service principal d'orchestration de l'assistant IA.
    
    Cette classe orchestre l'interaction avec l'IA, la base de connaissances
    et la persistance des conversations.
    """
    
    def __init__(
        self,
        ai_client: AIClient,
        repository: AIAssistantRepository,
        knowledge_base: Optional[KnowledgeBase] = None,
        command_executor: Optional[CommandExecutor] = None
    ):
        """
        Initialise le service avec ses dépendances.
        
        Args:
            ai_client: Client pour interagir avec l'IA
            repository: Repository pour la persistance des conversations
            knowledge_base: Base de connaissances pour enrichir les réponses
            command_executor: Exécuteur de commandes (optionnel)
        """
        self.ai_client = ai_client
        self.repository = repository
        self.knowledge_base = knowledge_base
        self.command_executor = command_executor
        self.gns3_adapter = gns3_ai_adapter
    
    def process_message(self, conversation_id: str, user_id: int, message_content: str) -> Dict[str, Any]:
        """
        Traite un message utilisateur et génère une réponse.
        
        Args:
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur
            message_content: Contenu du message
            
        Returns:
            Dictionnaire contenant la réponse générée
        """
        start_time = time.time()
        
        try:
            # Vérifier si la conversation existe
            conversation = self.repository.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} non trouvée")
                
            if conversation['user_id'] != user_id:
                raise ValueError("Vous n'êtes pas autorisé à accéder à cette conversation")
            
            # Enregistrer le message de l'utilisateur
            user_message = self.repository.add_message(
                conversation_id=conversation_id,
                content=message_content,
                role=MessageRole.USER,
                user_id=user_id
            )
            
            # Récupérer l'historique de la conversation
            messages = self.repository.get_conversation_messages(conversation_id)
            
            # Préparer le contexte pour le client IA
            context = self._prepare_context(messages)
            
            # Rechercher dans la base de connaissances si disponible
            knowledge_results = []
            if self.knowledge_base and settings.ENABLE_KNOWLEDGE_BASE:
                try:
                    knowledge_results = self.knowledge_base.search(
                        query=message_content,
                        limit=settings.MAX_QUERY_RESULTS
                    )
                    
                    if knowledge_results:
                        # Ajouter les résultats de la recherche au contexte
                        knowledge_context = self._format_knowledge_for_context(knowledge_results)
                        context.append(f"Informations pertinentes de la base de connaissances:\n{knowledge_context}")
                except KnowledgeBaseException as e:
                    logger.warning(f"Erreur lors de la recherche dans la base de connaissances: {e}")
            
            # Enrichir avec le contexte GNS3 si disponible
            gns3_context = None
            if self.gns3_adapter.is_available():
                try:
                    # Utiliser asyncio pour récupérer le contexte GNS3
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        gns3_context = loop.run_until_complete(self.gns3_adapter.get_network_context_for_ai())
                    finally:
                        loop.close()
                    
                    if gns3_context and gns3_context.get('context_available'):
                        # Ajouter le contexte GNS3 au contexte de l'IA
                        context.append(f"Contexte infrastructure réseau GNS3:\n{gns3_context['topology_summary']}")
                        context.append(f"Analyse réseau:\n{gns3_context['analysis_summary']}")
                        logger.info("Contexte GNS3 ajouté à la requête IA")
                except Exception as e:
                    logger.warning(f"Erreur lors de la récupération du contexte GNS3: {e}")
            
            # Générer la réponse
            response = self.ai_client.generate_response(message_content, context)
            
            # Enregistrer la réponse de l'assistant
            assistant_message = self.repository.add_message(
                conversation_id=conversation_id,
                content=response['content'],
                role=MessageRole.ASSISTANT,
                user_id=user_id
            )
            
            # Mettre à jour le titre de la conversation si c'est le premier échange
            if len(messages) <= 2:  # Premier échange (message utilisateur + réponse assistant)
                # Générer un titre basé sur le contenu du message
                try:
                    title_prompt = f"Génère un titre court (5 mots maximum) pour cette conversation: {message_content}"
                    title_response = self.ai_client.generate_response(title_prompt)
                    new_title = title_response['content'].strip().strip('"\'')
                    
                    # Limiter la longueur du titre
                    if len(new_title) > 50:
                        new_title = new_title[:47] + "..."
                        
                    # Mettre à jour le titre
                    self.repository.update_conversation(conversation_id, {'title': new_title})
                except Exception as e:
                    logger.warning(f"Erreur lors de la génération du titre: {e}")
            
            # Ajouter les sources de connaissances à la réponse
            sources = []
            if knowledge_results:
                for result in knowledge_results[:3]:  # Limiter à 3 sources
                    sources.append({
                        'title': result.get('title', ''),
                        'content_snippet': result.get('content', '')[:150] + '...',
                        'score': result.get('score', 0)
                    })
            
            # Calculer le temps de traitement
            processing_time = time.time() - start_time
            
            # Construire la réponse complète
            result = {
                'content': response['content'],
                'actions': response.get('actions', []),
                'sources': sources,
                'conversation_id': conversation_id,
                'message_id': assistant_message['id'],
                'processing_time': round(processing_time, 2),
                'gns3_context': gns3_context if gns3_context and gns3_context.get('context_available') else None
            }
            
            return result
        except Exception as e:
            logger.exception(f"Erreur lors du traitement du message: {e}")
            processing_time = time.time() - start_time
            
            # Enregistrer le message d'erreur
            try:
                error_message = f"Erreur lors du traitement du message: {str(e)}"
                self.repository.add_message(
                    conversation_id=conversation_id,
                    content=error_message,
                    role=MessageRole.SYSTEM,
                    user_id=user_id
                )
            except Exception:
                pass
            
            return {
                'content': f"Désolé, une erreur est survenue lors du traitement de votre message: {str(e)}",
                'actions': [],
                'sources': [],
                'conversation_id': conversation_id,
                'processing_time': round(processing_time, 2),
                'error': str(e)
            }
    
    def process_message_stream(
        self, 
        conversation_id: str, 
        user_id: int, 
        message_content: str,
        callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Traite un message utilisateur et génère une réponse en streaming.
        
        Args:
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur
            message_content: Contenu du message
            callback: Fonction de rappel pour traiter chaque fragment de réponse
            
        Returns:
            Dictionnaire contenant la réponse complète générée
        """
        start_time = time.time()
        
        try:
            # Vérifier si la conversation existe
            conversation = self.repository.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} non trouvée")
                
            if conversation['user_id'] != user_id:
                raise ValueError("Vous n'êtes pas autorisé à accéder à cette conversation")
            
            # Enregistrer le message de l'utilisateur
            user_message = self.repository.add_message(
                conversation_id=conversation_id,
                content=message_content,
                role=MessageRole.USER,
                user_id=user_id
            )
            
            # Récupérer l'historique de la conversation
            messages = self.repository.get_conversation_messages(conversation_id)
            
            # Préparer le contexte pour le client IA
            context = self._prepare_context(messages)
            
            # Rechercher dans la base de connaissances si disponible
            knowledge_results = []
            if self.knowledge_base and settings.ENABLE_KNOWLEDGE_BASE:
                try:
                    knowledge_results = self.knowledge_base.search(
                        query=message_content,
                        limit=settings.MAX_QUERY_RESULTS
                    )
                    
                    if knowledge_results:
                        # Ajouter les résultats de la recherche au contexte
                        knowledge_context = self._format_knowledge_for_context(knowledge_results)
                        context.append(f"Informations pertinentes de la base de connaissances:\n{knowledge_context}")
                except KnowledgeBaseException as e:
                    logger.warning(f"Erreur lors de la recherche dans la base de connaissances: {e}")
            
            # Enrichir avec le contexte GNS3 si disponible
            gns3_context = None
            if self.gns3_adapter.is_available():
                try:
                    # Utiliser asyncio pour récupérer le contexte GNS3
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        gns3_context = loop.run_until_complete(self.gns3_adapter.get_network_context_for_ai())
                    finally:
                        loop.close()
                    
                    if gns3_context and gns3_context.get('context_available'):
                        # Ajouter le contexte GNS3 au contexte de l'IA
                        context.append(f"Contexte infrastructure réseau GNS3:\n{gns3_context['topology_summary']}")
                        context.append(f"Analyse réseau:\n{gns3_context['analysis_summary']}")
                        logger.info("Contexte GNS3 ajouté à la requête IA (streaming)")
                except Exception as e:
                    logger.warning(f"Erreur lors de la récupération du contexte GNS3 (streaming): {e}")
            
            # Générer la réponse en streaming
            full_content = ""
            
            # Utiliser le générateur de streaming
            generator = self.ai_client.generate_response_stream(message_content, context, callback)
            
            # Consommer le générateur pour obtenir les fragments et la réponse complète
            for chunk in generator:
                full_content += chunk
            
            # Récupérer le résultat final du générateur
            final_response = generator.send(None)  # Obtenir la valeur de retour du générateur
            
            # Enregistrer la réponse complète de l'assistant
            assistant_message = self.repository.add_message(
                conversation_id=conversation_id,
                content=full_content,
                role=MessageRole.ASSISTANT,
                user_id=user_id
            )
            
            # Mettre à jour le titre de la conversation si c'est le premier échange
            if len(messages) <= 2:  # Premier échange (message utilisateur + réponse assistant)
                try:
                    title_prompt = f"Génère un titre court (5 mots maximum) pour cette conversation: {message_content}"
                    title_response = self.ai_client.generate_response(title_prompt)
                    new_title = title_response['content'].strip().strip('"\'')
                    
                    # Limiter la longueur du titre
                    if len(new_title) > 50:
                        new_title = new_title[:47] + "..."
                        
                    # Mettre à jour le titre
                    self.repository.update_conversation(conversation_id, {'title': new_title})
                except Exception as e:
                    logger.warning(f"Erreur lors de la génération du titre: {e}")
            
            # Ajouter les sources de connaissances à la réponse
            sources = []
            if knowledge_results:
                for result in knowledge_results[:3]:  # Limiter à 3 sources
                    sources.append({
                        'title': result.get('title', ''),
                        'content_snippet': result.get('content', '')[:150] + '...',
                        'score': result.get('score', 0)
                    })
            
            # Calculer le temps de traitement
            processing_time = time.time() - start_time
            
            # Construire la réponse complète
            result = {
                'content': full_content,
                'actions': final_response.get('actions', []),
                'sources': sources,
                'conversation_id': conversation_id,
                'message_id': assistant_message['id'],
                'processing_time': round(processing_time, 2),
                'gns3_context': gns3_context if gns3_context and gns3_context.get('context_available') else None
            }
            
            return result
        except Exception as e:
            logger.exception(f"Erreur lors du traitement du message en streaming: {e}")
            processing_time = time.time() - start_time
            
            # Enregistrer le message d'erreur
            try:
                error_message = f"Erreur lors du traitement du message: {str(e)}"
                self.repository.add_message(
                    conversation_id=conversation_id,
                    content=error_message,
                    role=MessageRole.SYSTEM,
                    user_id=user_id
                )
            except Exception:
                pass
            
            return {
                'content': f"Désolé, une erreur est survenue lors du traitement de votre message: {str(e)}",
                'actions': [],
                'sources': [],
                'conversation_id': conversation_id,
                'processing_time': round(processing_time, 2),
                'error': str(e)
            }
    
    def execute_command(self, conversation_id: str, user_id: int, command: str, command_type: str) -> Dict[str, Any]:
        """
        Exécute une commande.
        
        Args:
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur
            command: Commande à exécuter
            command_type: Type de commande
            
        Returns:
            Résultat de l'exécution de la commande
        """
        start_time = time.time()
        
        try:
            # Vérifier si l'exécuteur de commandes est disponible
            if not self.command_executor:
                raise CommandExecutionException("L'exécution de commandes n'est pas disponible", "unavailable")
                
            # Vérifier si l'exécution de commandes est activée
            if not settings.ENABLE_COMMAND_EXECUTION:
                raise CommandExecutionException("L'exécution de commandes est désactivée", "disabled")
            
            # Vérifier si la conversation existe
            conversation = self.repository.get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} non trouvée")
                
            if conversation['user_id'] != user_id:
                raise ValueError("Vous n'êtes pas autorisé à accéder à cette conversation")
            
            # Valider la commande
            is_valid = self.command_executor.validate(command, command_type)
            if not is_valid:
                raise CommandExecutionException(
                    f"Commande non autorisée: {command} (type: {command_type})",
                    "unauthorized"
                )
            
            # Enregistrer la commande dans l'historique
            command_message = self.repository.add_message(
                conversation_id=conversation_id,
                content=f"[COMMAND:{command_type}] {command}",
                role=MessageRole.USER,
                user_id=user_id
            )
            
            # Exécuter la commande
            result = self.command_executor.execute(command, command_type, user_id)
            
            # Enregistrer le résultat de la commande
            result_content = f"Résultat de la commande: {command}\n\n"
            if "stdout" in result:
                result_content += f"Sortie standard:\n{result['stdout']}\n\n"
            if "stderr" in result and result["stderr"]:
                result_content += f"Erreur standard:\n{result['stderr']}\n\n"
            if "returncode" in result:
                result_content += f"Code de retour: {result['returncode']}"
                
            result_message = self.repository.add_message(
                conversation_id=conversation_id,
                content=result_content,
                role=MessageRole.SYSTEM,
                user_id=user_id
            )
            
            # Calculer le temps d'exécution
            execution_time = time.time() - start_time
            
            # Analyser le résultat avec l'IA si configuré
            analysis = {}
            if settings.ENABLE_AI_CLIENT and result.get("returncode", 0) != 0:
                try:
                    analysis_prompt = f"Analyse le résultat de cette commande et explique l'erreur de manière concise:\nCommande: {command}\nSortie standard: {result.get('stdout', '')}\nErreur standard: {result.get('stderr', '')}\nCode de retour: {result.get('returncode', 0)}"
                    analysis = self.ai_client.generate_response(analysis_prompt)
                    
                    # Enregistrer l'analyse
                    self.repository.add_message(
                        conversation_id=conversation_id,
                        content=analysis['content'],
                        role=MessageRole.ASSISTANT,
                        user_id=user_id
                    )
                except Exception as e:
                    logger.warning(f"Erreur lors de l'analyse du résultat de la commande: {e}")
            
            return {
                'stdout': result.get('stdout', ''),
                'stderr': result.get('stderr', ''),
                'returncode': result.get('returncode', 0),
                'execution_time': round(execution_time, 2),
                'analysis': analysis.get('content', '') if analysis else '',
                'command': command,
                'command_type': command_type
            }
        except Exception as e:
            logger.exception(f"Erreur lors de l'exécution de la commande: {e}")
            execution_time = time.time() - start_time
            
            # Enregistrer l'erreur
            try:
                error_message = f"Erreur lors de l'exécution de la commande: {str(e)}"
                self.repository.add_message(
                    conversation_id=conversation_id,
                    content=error_message,
                    role=MessageRole.SYSTEM,
                    user_id=user_id
                )
            except Exception:
                pass
            
            return {
                'stdout': '',
                'stderr': str(e),
                'returncode': 1,
                'execution_time': round(execution_time, 2),
                'error': str(e),
                'command': command,
                'command_type': command_type
            }
    
    def _prepare_context(self, messages: List[Dict[str, Any]]) -> List[str]:
        """
        Prépare le contexte pour le client IA à partir de l'historique des messages.
        
        Args:
            messages: Liste des messages de la conversation
            
        Returns:
            Liste des messages formatés pour le contexte
        """
        context = []
        
        # Limiter le nombre de messages pour éviter de dépasser les limites de tokens
        max_messages = settings.MAX_CONVERSATION_HISTORY
        messages = messages[-max_messages:] if len(messages) > max_messages else messages
        
        # Convertir les messages en format texte pour le contexte
        for message in messages:
            if message['role'] == MessageRole.USER:
                context.append(message['content'])
            elif message['role'] == MessageRole.ASSISTANT:
                context.append(message['content'])
        
        return context
    
    def _format_knowledge_for_context(self, knowledge_results: List[Dict[str, Any]]) -> str:
        """
        Formate les résultats de la base de connaissances pour le contexte.
        
        Args:
            knowledge_results: Liste des résultats de la recherche
            
        Returns:
            Texte formaté pour le contexte
        """
        formatted = ""
        
        for i, result in enumerate(knowledge_results[:5]):  # Limiter à 5 résultats
            title = result.get('title', f"Document {i+1}")
            content = result.get('content', '')
            
            # Limiter la taille du contenu
            if len(content) > 500:
                content = content[:497] + "..."
                
            formatted += f"--- {title} ---\n{content}\n\n"
            
        return formatted
    
    async def analyze_network_device(self, conversation_id: str, user_id: int, device_name: str) -> Dict[str, Any]:
        """
        Analyse un dispositif réseau spécifique avec le contexte GNS3.
        
        Args:
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur
            device_name: Nom du dispositif à analyser
            
        Returns:
            Résultat de l'analyse du dispositif
        """
        start_time = time.time()
        
        try:
            # Vérifier l'autorisation
            conversation = self.repository.get_conversation(conversation_id)
            if not conversation or conversation['user_id'] != user_id:
                raise ValueError("Accès non autorisé à cette conversation")
            
            # Analyser le dispositif avec GNS3
            device_context = await self.gns3_adapter.analyze_device_context(device_name)
            
            if not device_context:
                return {
                    'error': f"Dispositif '{device_name}' non trouvé dans l'infrastructure GNS3",
                    'device_name': device_name,
                    'analysis_time': round(time.time() - start_time, 2)
                }
            
            # Générer une analyse IA du dispositif
            analysis_prompt = f"""
            Analyse ce dispositif réseau et fournis des recommandations :
            
            {device_context['context_summary']}
            
            Recommandations actuelles :
            {', '.join(device_context['recommendations']) if device_context['recommendations'] else 'Aucune'}
            
            Fournis une analyse détaillée et des recommandations d'optimisation.
            """
            
            ai_analysis = self.ai_client.generate_response(analysis_prompt)
            
            # Enregistrer l'analyse dans la conversation
            analysis_message = f"Analyse du dispositif {device_name}:\n\n{ai_analysis['content']}"
            self.repository.add_message(
                conversation_id=conversation_id,
                content=analysis_message,
                role=MessageRole.ASSISTANT,
                user_id=user_id
            )
            
            return {
                'device_info': device_context['device_info'],
                'ai_analysis': ai_analysis['content'],
                'technical_details': device_context['performance_analysis'],
                'recommendations': device_context['recommendations'],
                'device_name': device_name,
                'analysis_time': round(time.time() - start_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du dispositif {device_name}: {e}")
            return {
                'error': f"Erreur lors de l'analyse du dispositif: {str(e)}",
                'device_name': device_name,
                'analysis_time': round(time.time() - start_time, 2)
            }
    
    async def analyze_network_project(self, conversation_id: str, user_id: int, project_name: str) -> Dict[str, Any]:
        """
        Analyse un projet réseau spécifique avec le contexte GNS3.
        
        Args:
            conversation_id: ID de la conversation
            user_id: ID de l'utilisateur
            project_name: Nom du projet à analyser
            
        Returns:
            Résultat de l'analyse du projet
        """
        start_time = time.time()
        
        try:
            # Vérifier l'autorisation
            conversation = self.repository.get_conversation(conversation_id)
            if not conversation or conversation['user_id'] != user_id:
                raise ValueError("Accès non autorisé à cette conversation")
            
            # Analyser le projet avec GNS3
            project_context = await self.gns3_adapter.analyze_project_context(project_name)
            
            if not project_context:
                return {
                    'error': f"Projet '{project_name}' non trouvé dans GNS3",
                    'project_name': project_name,
                    'analysis_time': round(time.time() - start_time, 2)
                }
            
            # Générer une analyse IA du projet
            topology_analysis = project_context['topology_analysis']
            analysis_prompt = f"""
            Analyse ce projet de topologie réseau et fournis des recommandations d'optimisation :
            
            Projet : {project_name}
            Statistiques :
            - Dispositifs : {project_context['topology_stats']['total_nodes']}
            - Connexions : {project_context['topology_stats']['total_links']}
            - Dispositifs actifs : {project_context['topology_stats']['running_nodes']}
            
            Analyse de topologie :
            - Densité réseau : {topology_analysis.get('network_density', 0):.1f}%
            - Niveau de redondance : {topology_analysis.get('redundancy_level', 'inconnu')}
            - Santé topologie : {topology_analysis.get('topology_health', 'inconnue')}
            
            Dispositifs centraux : {', '.join(topology_analysis.get('central_devices', []))}
            Dispositifs isolés : {', '.join(topology_analysis.get('isolated_devices', []))}
            
            Recommandations actuelles :
            {chr(10).join(f'- {rec}' for rec in project_context['recommendations'])}
            
            Fournis une analyse détaillée de cette topologie et des recommandations d'amélioration.
            """
            
            ai_analysis = self.ai_client.generate_response(analysis_prompt)
            
            # Enregistrer l'analyse dans la conversation
            analysis_message = f"Analyse du projet {project_name}:\n\n{ai_analysis['content']}"
            self.repository.add_message(
                conversation_id=conversation_id,
                content=analysis_message,
                role=MessageRole.ASSISTANT,
                user_id=user_id
            )
            
            return {
                'project_info': project_context['project_info'],
                'ai_analysis': ai_analysis['content'],
                'topology_stats': project_context['topology_stats'],
                'topology_analysis': topology_analysis,
                'devices': project_context['devices'],
                'recommendations': project_context['recommendations'],
                'project_name': project_name,
                'analysis_time': round(time.time() - start_time, 2)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du projet {project_name}: {e}")
            return {
                'error': f"Erreur lors de l'analyse du projet: {str(e)}",
                'project_name': project_name,
                'analysis_time': round(time.time() - start_time, 2)
            }
    
    def get_gns3_integration_status(self) -> Dict[str, Any]:
        """
        Retourne le statut de l'intégration GNS3.
        
        Returns:
            Statut de l'intégration GNS3
        """
        return {
            'gns3_available': self.gns3_adapter.is_available(),
            'last_update_info': self.gns3_adapter.get_last_update_info(),
            'integration_enabled': True,
            'supported_features': [
                'network_context_enrichment',
                'device_analysis',
                'project_analysis',
                'topology_recommendations'
            ]
        }