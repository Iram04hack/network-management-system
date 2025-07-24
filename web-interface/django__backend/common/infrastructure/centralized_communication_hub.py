"""
Hub de communication centralisé pour l'orchestration inter-modules.
"""
import logging
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from django.utils import timezone
from django.conf import settings

from .inter_module_service import inter_module_service, MessageType
from .gns3_integration_service import gns3_integration_service
from .ubuntu_notification_service import ubuntu_notification_service

logger = logging.getLogger(__name__)

class Priority(Enum):
    """Priorités des messages."""
    LOW = "low"
    NORMAL = "normal" 
    HIGH = "high"
    CRITICAL = "critical"

class MessageStatus(Enum):
    """Statuts des messages."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

@dataclass
class CommunicationMessage:
    """Message de communication inter-modules."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender: str = ""
    target: Optional[str] = None
    message_type: MessageType = MessageType.NOTIFICATION
    data: Dict[str, Any] = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    timestamp: datetime = field(default_factory=timezone.now)
    status: MessageStatus = MessageStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 30
    callback: Optional[Callable] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class ModuleRegistry:
    """Registre des modules avec leurs capacités."""
    
    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.capabilities: Dict[str, Set[str]] = {}
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.last_heartbeat: Dict[str, datetime] = {}
        
    def register_module(self, module_name: str, capabilities: List[str], 
                       health_check_callback: Optional[Callable] = None):
        """Enregistre un module avec ses capacités."""
        self.modules[module_name] = {
            'name': module_name,
            'registered_at': timezone.now(),
            'health_check_callback': health_check_callback,
            'message_count': 0,
            'error_count': 0,
            'last_activity': timezone.now()
        }
        
        self.capabilities[module_name] = set(capabilities)
        self.last_heartbeat[module_name] = timezone.now()
        
        logger.info(f"Module '{module_name}' enregistré avec capacités: {capabilities}")
        
    def unregister_module(self, module_name: str):
        """Désenregistre un module."""
        self.modules.pop(module_name, None)
        self.capabilities.pop(module_name, None)
        self.health_status.pop(module_name, None)
        self.last_heartbeat.pop(module_name, None)
        
        logger.info(f"Module '{module_name}' désenregistré")
        
    def update_heartbeat(self, module_name: str):
        """Met à jour le heartbeat d'un module."""
        if module_name in self.modules:
            self.last_heartbeat[module_name] = timezone.now()
            self.modules[module_name]['last_activity'] = timezone.now()
            
    def get_modules_with_capability(self, capability: str) -> List[str]:
        """Retourne les modules ayant une capacité spécifique."""
        return [
            module for module, caps in self.capabilities.items()
            if capability in caps
        ]
        
    def is_module_healthy(self, module_name: str, timeout_minutes: int = 5) -> bool:
        """Vérifie si un module est en bonne santé."""
        if module_name not in self.last_heartbeat:
            return False
            
        last_beat = self.last_heartbeat[module_name]
        timeout_threshold = timezone.now() - timedelta(minutes=timeout_minutes)
        
        return last_beat > timeout_threshold

class CentralizedCommunicationHub:
    """Hub de communication centralisé pour orchestrer tous les modules."""
    
    def __init__(self):
        self.registry = ModuleRegistry()
        self.message_queue: List[CommunicationMessage] = []
        self.processing_queue: List[CommunicationMessage] = []
        self.completed_messages: List[CommunicationMessage] = []
        self.failed_messages: List[CommunicationMessage] = []
        
        self.is_running = False
        self.processor_thread = None
        self._lock = threading.Lock()
        
        # Statistiques
        self.stats = {
            'total_messages': 0,
            'successful_messages': 0,
            'failed_messages': 0,
            'average_processing_time': 0.0,
            'peak_queue_size': 0
        }
        
        # Workflows prédéfinis
        self.workflows: Dict[str, List[Dict[str, Any]]] = {}
        self._initialize_default_workflows()
        
    def _initialize_default_workflows(self):
        """Initialise les workflows par défaut."""
        # Workflow de découverte d'équipement
        self.workflows['equipment_discovery'] = [
            {
                'step': 'gns3_detection',
                'module': 'gns3_integration',
                'action': 'get_project_nodes',
                'timeout': 30
            },
            {
                'step': 'snmp_discovery',
                'module': 'monitoring', 
                'action': 'discover_snmp_devices',
                'timeout': 60
            },
            {
                'step': 'security_analysis',
                'module': 'security_management',
                'action': 'analyze_network_security',
                'timeout': 45
            },
            {
                'step': 'performance_baseline',
                'module': 'monitoring',
                'action': 'establish_performance_baseline',
                'timeout': 30
            }
        ]
        
        # Workflow de réponse aux incidents
        self.workflows['incident_response'] = [
            {
                'step': 'incident_detection',
                'module': 'monitoring',
                'action': 'analyze_incident',
                'timeout': 15
            },
            {
                'step': 'security_assessment',
                'module': 'security_management',
                'action': 'assess_security_impact',
                'timeout': 30
            },
            {
                'step': 'containment',
                'module': 'security_management',
                'action': 'apply_containment_measures',
                'timeout': 60
            },
            {
                'step': 'notification',
                'module': 'common',
                'action': 'send_incident_notifications',
                'timeout': 10
            }
        ]
        
        # Workflow de mise à jour de topologie
        self.workflows['topology_update'] = [
            {
                'step': 'gns3_sync',
                'module': 'gns3_integration',
                'action': 'sync_topology_changes',
                'timeout': 30
            },
            {
                'step': 'monitoring_update',
                'module': 'monitoring',
                'action': 'update_monitoring_targets',
                'timeout': 45
            },
            {
                'step': 'security_update',
                'module': 'security_management',
                'action': 'update_security_policies',
                'timeout': 30
            },
            {
                'step': 'qos_update',
                'module': 'qos_management',
                'action': 'update_qos_policies',
                'timeout': 30
            }
        ]
        
        # Workflow complet de tests de sécurité
        self.workflows['security_testing_full_workflow'] = [
            {
                'step': 'project_startup',
                'module': 'gns3_integration',
                'action': 'start_project_complete',
                'timeout': 60
            },
            {
                'step': 'orchestrate_system',
                'module': 'common',
                'action': 'orchestrate_system_monitoring',
                'timeout': 120
            },
            {
                'step': 'activate_multi_projects_monitoring',
                'module': 'gns3_integration',
                'action': 'monitor_multi_projects_traffic',
                'timeout': 30
            },
            {
                'step': 'start_network_monitoring',
                'module': 'monitoring',
                'action': 'collect_metrics',
                'timeout': 60
            },
            {
                'step': 'start_security_monitoring',
                'module': 'security_management',
                'action': 'monitor_security_alerts',
                'timeout': 45
            },
            {
                'step': 'start_qos_monitoring',
                'module': 'qos_management',
                'action': 'collect_traffic_statistics',
                'timeout': 45
            },
            {
                'step': 'network_device_discovery',
                'module': 'network_management',
                'action': 'discover_network_devices',
                'timeout': 90
            },
            {
                'step': 'ai_assistant_activation',
                'module': 'ai_assistant',
                'action': 'check_ai_services_health',
                'timeout': 30
            }
        ]
        
    def start(self):
        """Démarre le hub de communication."""
        if self.is_running:
            logger.warning("Le hub de communication est déjà en cours d'exécution")
            return
            
        self.is_running = True
        self.processor_thread = threading.Thread(target=self._process_messages, daemon=True)
        self.processor_thread.start()
        
        logger.info("Hub de communication centralisé démarré")
        
        # Notification de démarrage
        ubuntu_notification_service.send_notification(
            title="🔗 Hub de Communication Démarré",
            message="Le hub centralisé de communication inter-modules est opérationnel",
            urgency='low',
            category='system.communication'
        )
        
    def stop(self):
        """Arrête le hub de communication."""
        self.is_running = False
        
        if self.processor_thread and self.processor_thread.is_alive():
            self.processor_thread.join(timeout=5)
            
        logger.info("Hub de communication centralisé arrêté")
        
    def register_module(self, module_name: str, capabilities: List[str], 
                       health_check_callback: Optional[Callable] = None):
        """Enregistre un module dans le hub."""
        self.registry.register_module(module_name, capabilities, health_check_callback)
        
        # Envoyer un message de bienvenue
        welcome_message = CommunicationMessage(
            sender='communication_hub',
            target=module_name,
            message_type=MessageType.SERVICE_DISCOVERY,
            data={
                'action': 'welcome',
                'registered_modules': list(self.registry.modules.keys()),
                'available_workflows': list(self.workflows.keys())
            },
            priority=Priority.NORMAL
        )
        
        self.send_message(welcome_message)
        
    def send_message(self, message: CommunicationMessage) -> str:
        """Envoie un message via le hub."""
        with self._lock:
            self.message_queue.append(message)
            self.stats['total_messages'] += 1
            self.stats['peak_queue_size'] = max(
                self.stats['peak_queue_size'],
                len(self.message_queue)
            )
            
        logger.debug(f"Message {message.id} ajouté à la queue (priorité: {message.priority.value})")
        return message.id
        
    def send_high_priority_message(self, sender: str, target: str, 
                                 message_type: MessageType, data: Dict[str, Any],
                                 callback: Optional[Callable] = None) -> str:
        """Envoie un message haute priorité."""
        message = CommunicationMessage(
            sender=sender,
            target=target,
            message_type=message_type,
            data=data,
            priority=Priority.HIGH,
            callback=callback
        )
        
        return self.send_message(message)
        
    def broadcast_message(self, sender: str, message_type: MessageType, 
                         data: Dict[str, Any], capability_filter: Optional[str] = None) -> List[str]:
        """Diffuse un message à plusieurs modules."""
        message_ids = []
        
        # Déterminer les destinataires
        if capability_filter:
            targets = self.registry.get_modules_with_capability(capability_filter)
        else:
            targets = list(self.registry.modules.keys())
            
        # Exclure l'expéditeur
        targets = [t for t in targets if t != sender]
        
        for target in targets:
            message = CommunicationMessage(
                sender=sender,
                target=target,
                message_type=message_type,
                data=data,
                priority=Priority.NORMAL
            )
            
            message_id = self.send_message(message)
            message_ids.append(message_id)
            
        logger.info(f"Message diffusé de {sender} vers {len(targets)} modules")
        return message_ids
        
    def execute_workflow(self, workflow_name: str, initial_data: Dict[str, Any],
                        callback: Optional[Callable] = None) -> str:
        """Exécute un workflow prédéfini."""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' non trouvé")
            
        workflow_id = str(uuid.uuid4())
        workflow_steps = self.workflows[workflow_name]
        
        logger.info(f"Démarrage du workflow '{workflow_name}' (ID: {workflow_id})")
        
        # Créer une séquence de messages pour le workflow
        workflow_data = {
            'workflow_id': workflow_id,
            'workflow_name': workflow_name,
            'total_steps': len(workflow_steps),
            'current_step': 0,
            'initial_data': initial_data,
            'step_results': {},
            'callback': callback
        }
        
        # Démarrer la première étape
        self._execute_workflow_step(workflow_data, 0)
        
        return workflow_id
        
    def _execute_workflow_step(self, workflow_data: Dict[str, Any], step_index: int):
        """Exécute une étape de workflow."""
        workflow_name = workflow_data['workflow_name']
        workflow_steps = self.workflows[workflow_name]
        
        if step_index >= len(workflow_steps):
            # Workflow terminé
            self._complete_workflow(workflow_data)
            return
            
        step = workflow_steps[step_index]
        workflow_data['current_step'] = step_index
        
        # Créer le message pour cette étape
        step_message = CommunicationMessage(
            sender='communication_hub',
            target=step['module'],
            message_type=MessageType.CONFIGURATION_CHANGE,
            data={
                'workflow_data': workflow_data,
                'step_data': step,
                'action': step['action']
            },
            priority=Priority.HIGH,
            timeout_seconds=step.get('timeout', 30),
            callback=lambda response: self._handle_workflow_step_response(
                workflow_data, step_index, response
            )
        )
        
        self.send_message(step_message)
        
    def _handle_workflow_step_response(self, workflow_data: Dict[str, Any], 
                                     step_index: int, response: Dict[str, Any]):
        """Traite la réponse d'une étape de workflow."""
        workflow_steps = self.workflows[workflow_data['workflow_name']]
        step = workflow_steps[step_index]
        
        # Stocker le résultat de l'étape
        workflow_data['step_results'][step['step']] = response
        
        # Continuer vers l'étape suivante
        self._execute_workflow_step(workflow_data, step_index + 1)
        
    def _complete_workflow(self, workflow_data: Dict[str, Any]):
        """Finalise un workflow."""
        workflow_id = workflow_data['workflow_id']
        workflow_name = workflow_data['workflow_name']
        
        logger.info(f"Workflow '{workflow_name}' terminé (ID: {workflow_id})")
        
        # Appeler le callback si fourni
        callback = workflow_data.get('callback')
        if callback:
            callback(workflow_data)
            
        # Envoyer notification
        ubuntu_notification_service.send_notification(
            title=f"✅ Workflow {workflow_name} Terminé",
            message=f"Toutes les étapes du workflow ont été exécutées avec succès",
            urgency='low',
            category='system.workflow'
        )
        
    def _process_messages(self):
        """Boucle de traitement des messages."""
        while self.is_running:
            try:
                # Traiter les messages en attente
                self._process_pending_messages()
                
                # Vérifier les timeouts
                self._check_message_timeouts()
                
                # Nettoyer les anciens messages
                self._cleanup_old_messages()
                
                # Health check des modules
                self._check_module_health()
                
                time.sleep(1)  # Pause courte
                
            except Exception as e:
                logger.error(f"Erreur dans la boucle de traitement: {e}")
                time.sleep(5)
                
    def _process_pending_messages(self):
        """Traite les messages en attente."""
        with self._lock:
            # Trier par priorité (CRITICAL > HIGH > NORMAL > LOW)
            priority_order = {Priority.CRITICAL: 0, Priority.HIGH: 1, Priority.NORMAL: 2, Priority.LOW: 3}
            self.message_queue.sort(key=lambda m: priority_order[m.priority])
            
            # Traiter jusqu'à 10 messages par itération
            messages_to_process = self.message_queue[:10]
            self.message_queue = self.message_queue[10:]
            
        for message in messages_to_process:
            self._process_single_message(message)
            
    def _process_single_message(self, message: CommunicationMessage):
        """Traite un message individuel."""
        try:
            start_time = time.time()
            message.status = MessageStatus.PROCESSING
            
            with self._lock:
                self.processing_queue.append(message)
                
            # Mettre à jour l'activité du module expéditeur
            self.registry.update_heartbeat(message.sender)
            
            # Vérifier si c'est une action de workflow avec une tâche Celery
            workflow_data = message.data.get('workflow_data')
            step_data = message.data.get('step_data')
            action = message.data.get('action')
            
            if workflow_data and step_data and action:
                # C'est une étape de workflow, déclencher la tâche Celery correspondante
                self._execute_celery_task_for_workflow_step(action, step_data, workflow_data, message)
            else:
                # Envoyer le message via inter_module_service comme avant
                inter_module_service.send_message(
                    message.message_type,
                    message.data,
                    sender=message.sender,
                    target=message.target
                )
            
            # Marquer comme terminé
            processing_time = time.time() - start_time
            message.status = MessageStatus.COMPLETED
            message.response_data = {'processing_time': processing_time}
            
            # Mettre à jour les statistiques
            self.stats['successful_messages'] += 1
            self._update_average_processing_time(processing_time)
            
            # Appeler le callback si fourni
            if message.callback:
                try:
                    message.callback(message.response_data)
                except Exception as e:
                    logger.error(f"Erreur dans callback du message {message.id}: {e}")
                    
            with self._lock:
                self.processing_queue.remove(message)
                self.completed_messages.append(message)
                
            logger.debug(f"Message {message.id} traité avec succès en {processing_time:.3f}s")
            
        except Exception as e:
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
            
            # Tentative de retry
            if message.retry_count < message.max_retries:
                message.retry_count += 1
                message.status = MessageStatus.PENDING
                
                with self._lock:
                    self.message_queue.append(message)
                    if message in self.processing_queue:
                        self.processing_queue.remove(message)
                        
                logger.warning(f"Message {message.id} en retry ({message.retry_count}/{message.max_retries})")
            else:
                self.stats['failed_messages'] += 1
                
                with self._lock:
                    if message in self.processing_queue:
                        self.processing_queue.remove(message)
                    self.failed_messages.append(message)
                    
                logger.error(f"Message {message.id} échoué définitivement: {e}")
                
    def _check_message_timeouts(self):
        """Vérifie les timeouts des messages."""
        current_time = timezone.now()
        
        with self._lock:
            timed_out_messages = []
            
            for message in self.processing_queue:
                elapsed = (current_time - message.timestamp).total_seconds()
                if elapsed > message.timeout_seconds:
                    timed_out_messages.append(message)
                    
            for message in timed_out_messages:
                message.status = MessageStatus.TIMEOUT
                self.processing_queue.remove(message)
                self.failed_messages.append(message)
                
                logger.warning(f"Message {message.id} timeout après {message.timeout_seconds}s")
                
    def _cleanup_old_messages(self):
        """Nettoie les anciens messages."""
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        with self._lock:
            # Garder seulement les messages des dernières 24h
            self.completed_messages = [
                m for m in self.completed_messages 
                if m.timestamp > cutoff_time
            ]
            
            self.failed_messages = [
                m for m in self.failed_messages
                if m.timestamp > cutoff_time
            ]
            
    def _check_module_health(self):
        """Vérifie la santé des modules enregistrés."""
        unhealthy_modules = []
        
        for module_name in self.registry.modules:
            if not self.registry.is_module_healthy(module_name):
                unhealthy_modules.append(module_name)
                
        if unhealthy_modules:
            logger.warning(f"Modules non responsifs: {unhealthy_modules}")
            
            # Envoyer notification pour les modules critiques
            critical_modules = ['gns3_integration', 'monitoring', 'security_management']
            critical_unhealthy = [m for m in unhealthy_modules if m in critical_modules]
            
            if critical_unhealthy:
                ubuntu_notification_service.send_notification(
                    title="⚠️ Modules Critiques Non Responsifs",
                    message=f"Les modules critiques suivants ne répondent pas: {', '.join(critical_unhealthy)}",
                    urgency='critical',
                    category='system.health'
                )
    
    def _execute_celery_task_for_workflow_step(self, action: str, step_data: Dict[str, Any], 
                                             workflow_data: Dict[str, Any], message: CommunicationMessage):
        """Exécute une tâche Celery correspondant à une étape de workflow."""
        try:
            from celery import current_app
            
            # Mapper les actions vers les vraies tâches Celery
            task_mapping = {
                'start_project_complete': 'common.tasks.start_gns3_project_complete',
                'orchestrate_system_monitoring': 'common.tasks.orchestrate_system_monitoring',
                'monitor_multi_projects_traffic': 'gns3_integration.tasks.monitor_multi_projects_traffic',
                'collect_metrics': 'monitoring.tasks.collect_metrics',
                'monitor_security_alerts': 'security_management.tasks.monitor_security_alerts',
                'collect_traffic_statistics': 'qos_management.tasks.collect_traffic_statistics',
                'discover_network_devices': 'network_management.tasks.discover_network_devices',
                'check_ai_services_health': 'ai_assistant.tasks.check_ai_services_health',
            }
            
            task_name = task_mapping.get(action)
            if not task_name:
                logger.warning(f"Aucune tâche Celery trouvée pour l'action: {action}")
                return
            
            # Préparer les arguments pour la tâche
            task_kwargs = {
                'workflow_id': workflow_data.get('workflow_id'),
                'step_name': step_data.get('step'),
                'trigger_source': 'workflow_hub',
                'initial_data': workflow_data.get('initial_data', {}),
                'timestamp': timezone.now().isoformat()
            }
            
            # Ajouter le project_id si disponible
            project_id = workflow_data.get('initial_data', {}).get('project_id')
            if project_id:
                task_kwargs['project_id'] = project_id
            
            # Déclencher la tâche Celery
            logger.info(f"🚀 Déclenchement tâche Celery: {task_name} pour workflow {workflow_data.get('workflow_id')}")
            
            task = current_app.send_task(
                task_name,
                kwargs=task_kwargs,
                countdown=0
            )
            
            # Sauvegarder l'ID de la tâche
            response_data = {
                'task_id': task.id,
                'task_name': task_name,
                'action': action,
                'status': 'triggered',
                'timestamp': timezone.now().isoformat()
            }
            
            message.response_data = response_data
            
            logger.info(f"✅ Tâche Celery {task_name} déclenchée avec ID: {task.id}")
            
            # Appeler le callback si fourni
            if message.callback:
                try:
                    message.callback(response_data)
                except Exception as e:
                    logger.error(f"Erreur dans callback du workflow: {e}")
            
        except Exception as e:
            logger.error(f"❌ Erreur déclenchement tâche Celery pour action {action}: {e}")
            message.status = MessageStatus.FAILED
            message.error_message = str(e)
                
    def _update_average_processing_time(self, processing_time: float):
        """Met à jour le temps de traitement moyen."""
        current_avg = self.stats['average_processing_time']
        total_successful = self.stats['successful_messages']
        
        if total_successful == 1:
            self.stats['average_processing_time'] = processing_time
        else:
            # Moyenne mobile
            self.stats['average_processing_time'] = (
                (current_avg * (total_successful - 1) + processing_time) / total_successful
            )
            
    def get_status(self) -> Dict[str, Any]:
        """Récupère le statut du hub de communication."""
        with self._lock:
            queue_sizes = {
                'pending': len(self.message_queue),
                'processing': len(self.processing_queue),
                'completed': len(self.completed_messages),
                'failed': len(self.failed_messages)
            }
            
        return {
            'hub_status': 'running' if self.is_running else 'stopped',
            'registered_modules': list(self.registry.modules.keys()),
            'queue_sizes': queue_sizes,
            'statistics': self.stats,
            'available_workflows': list(self.workflows.keys()),
            'module_health': {
                name: self.registry.is_module_healthy(name)
                for name in self.registry.modules
            },
            'timestamp': timezone.now().isoformat()
        }

# Instance globale du hub
communication_hub = CentralizedCommunicationHub()