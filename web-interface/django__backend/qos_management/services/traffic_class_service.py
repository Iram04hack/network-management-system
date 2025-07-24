"""
Service pour la gestion des classes de trafic
"""
import logging
from typing import Dict, Any, List, Optional, Union
from django.db import transaction

from qos_management.models import TrafficClass, QoSPolicy
from common.exceptions import (
    ValidationException, NotFoundException, 
    ServiceUnavailableException
)
from qos_management.events import (
    TrafficClassCreatedEvent, TrafficClassUpdatedEvent, 
    TrafficClassDeletedEvent, EventBus
)

logger = logging.getLogger(__name__)

class TrafficClassService:
    """Service pour la gestion des classes de trafic"""
    
    @classmethod
    def create_traffic_class(cls, traffic_class_data: Dict[str, Any]) -> TrafficClass:
        """
        Crée une nouvelle classe de trafic
        
        Args:
            traffic_class_data (dict): Données de la classe de trafic
            
        Returns:
            TrafficClass: La classe de trafic créée
            
        Raises:
            ValidationException: Si les données sont invalides
            NotFoundException: Si la politique QoS n'existe pas
        """
        try:
            with transaction.atomic():
                # Vérifier si une politique QoS est spécifiée
                if not traffic_class_data.get('policy_id'):
                    raise ValidationException(
                        message="L'ID de politique QoS est obligatoire",
                        details={"field": "policy_id"}
                    )
                
                # Récupérer la politique QoS
                try:
                    policy = QoSPolicy.objects.get(id=traffic_class_data['policy_id'])
                except QoSPolicy.DoesNotExist:
                    raise NotFoundException(
                        message=f"Politique QoS {traffic_class_data['policy_id']} non trouvée",
                        details={"policy_id": traffic_class_data['policy_id']}
                    )
                
                # Valider la classe de trafic
                if 'name' not in traffic_class_data or not traffic_class_data['name']:
                    raise ValidationException(
                        message="Le nom de la classe de trafic est obligatoire",
                        details={"field": "name"}
                    )
                
                # Valider la priorité
                valid_priorities = ['highest', 'high', 'normal', 'low', 'lowest']
                priority = traffic_class_data.get('priority', 'normal')
                if priority not in valid_priorities:
                    raise ValidationException(
                        message=f"Priorité invalide: {priority}",
                        details={"field": "priority", "value": priority, "valid_values": valid_priorities}
                    )
                
                # Valider le pourcentage de bande passante
                bandwidth_percentage = traffic_class_data.get('bandwidth_percentage', 0)
                if not isinstance(bandwidth_percentage, (int, float)) or not (0 <= bandwidth_percentage <= 100):
                    raise ValidationException(
                        message=f"Pourcentage de bande passante invalide: {bandwidth_percentage}",
                        details={"field": "bandwidth_percentage", "value": bandwidth_percentage, "valid_range": "0-100"}
                    )
                
                # Vérifier si le nom de classe est déjà utilisé dans cette politique
                if TrafficClass.objects.filter(policy=policy, name=traffic_class_data['name']).exists():
                    raise ValidationException(
                        message=f"Une classe de trafic avec le nom {traffic_class_data['name']} existe déjà pour cette politique",
                        details={"field": "name", "value": traffic_class_data['name'], "policy_id": policy.id}
                    )
                
                # Créer la classe de trafic
                traffic_class = TrafficClass.objects.create(
                    policy=policy,
                    name=traffic_class_data['name'],
                    description=traffic_class_data.get('description', ''),
                    priority=priority,
                    bandwidth_percentage=bandwidth_percentage,
                    dscp_marking=traffic_class_data.get('dscp_marking', ''),
                    max_burst=traffic_class_data.get('max_burst'),
                    max_latency=traffic_class_data.get('max_latency')
                )
                
                # Publier un événement de création
                EventBus.publish_async(TrafficClassCreatedEvent(
                    traffic_class_id=traffic_class.id,
                    policy_id=policy.id,
                    name=traffic_class.name
                ))
                
                return traffic_class
                
        except (ValidationException, NotFoundException):
            # Remonter ces exceptions
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la création de la classe de trafic: {str(e)}", exc_info=True)
            raise ValidationException(
                message=f"Erreur lors de la création de la classe de trafic: {str(e)}",
                details={"traffic_class_data": traffic_class_data}
            )
    
    @classmethod
    def update_traffic_class(cls, traffic_class_id: int, update_data: Dict[str, Any]) -> TrafficClass:
        """
        Met à jour une classe de trafic
        
        Args:
            traffic_class_id (int): ID de la classe de trafic
            update_data (dict): Données à mettre à jour
            
        Returns:
            TrafficClass: La classe de trafic mise à jour
            
        Raises:
            NotFoundException: Si la classe de trafic n'existe pas
            ValidationException: Si les données sont invalides
        """
        try:
            # Récupérer la classe de trafic
            try:
                traffic_class = TrafficClass.objects.get(id=traffic_class_id)
            except TrafficClass.DoesNotExist:
                raise NotFoundException(
                    message=f"Classe de trafic {traffic_class_id} non trouvée",
                    details={"traffic_class_id": traffic_class_id}
                )
            
            # Valider et mettre à jour les champs modifiables
            if 'name' in update_data:
                if not update_data['name']:
                    raise ValidationException(
                        message="Le nom de la classe de trafic est obligatoire",
                        details={"field": "name"}
                    )
                
                # Vérifier si le nouveau nom est déjà utilisé dans cette politique
                if update_data['name'] != traffic_class.name and TrafficClass.objects.filter(
                    policy=traffic_class.policy, 
                    name=update_data['name']
                ).exists():
                    raise ValidationException(
                        message=f"Une classe de trafic avec le nom {update_data['name']} existe déjà pour cette politique",
                        details={"field": "name", "value": update_data['name'], "policy_id": traffic_class.policy.id}
                    )
                
                traffic_class.name = update_data['name']
            
            if 'description' in update_data:
                traffic_class.description = update_data['description']
            
            if 'priority' in update_data:
                valid_priorities = ['highest', 'high', 'normal', 'low', 'lowest']
                if update_data['priority'] not in valid_priorities:
                    raise ValidationException(
                        message=f"Priorité invalide: {update_data['priority']}",
                        details={"field": "priority", "value": update_data['priority'], "valid_values": valid_priorities}
                    )
                traffic_class.priority = update_data['priority']
            
            if 'bandwidth_percentage' in update_data:
                bandwidth_percentage = update_data['bandwidth_percentage']
                if not isinstance(bandwidth_percentage, (int, float)) or not (0 <= bandwidth_percentage <= 100):
                    raise ValidationException(
                        message=f"Pourcentage de bande passante invalide: {bandwidth_percentage}",
                        details={"field": "bandwidth_percentage", "value": bandwidth_percentage, "valid_range": "0-100"}
                    )
                traffic_class.bandwidth_percentage = bandwidth_percentage
            
            if 'dscp_marking' in update_data:
                traffic_class.dscp_marking = update_data['dscp_marking']
            
            if 'max_burst' in update_data:
                traffic_class.max_burst = update_data['max_burst']
            
            if 'max_latency' in update_data:
                traffic_class.max_latency = update_data['max_latency']
            
            # Enregistrer les modifications
            traffic_class.save()
            
            # Publier un événement de mise à jour
            EventBus.publish_async(TrafficClassUpdatedEvent(
                traffic_class_id=traffic_class.id,
                changes=update_data,
                policy_id=traffic_class.policy.id,
                name=traffic_class.name
            ))
            
            return traffic_class
            
        except (NotFoundException, ValidationException):
            # Remonter ces exceptions
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la classe de trafic {traffic_class_id}: {str(e)}", exc_info=True)
            raise ValidationException(
                message=f"Erreur lors de la mise à jour de la classe de trafic: {str(e)}",
                details={"traffic_class_id": traffic_class_id, "update_data": update_data}
            )
    
    @classmethod
    def delete_traffic_class(cls, traffic_class_id: int) -> bool:
        """
        Supprime une classe de trafic
        
        Args:
            traffic_class_id (int): ID de la classe de trafic
            
        Returns:
            bool: True si la suppression a réussi
            
        Raises:
            NotFoundException: Si la classe de trafic n'existe pas
            ValidationException: Si la classe de trafic a des classificateurs
        """
        try:
            # Récupérer la classe de trafic
            try:
                traffic_class = TrafficClass.objects.get(id=traffic_class_id)
            except TrafficClass.DoesNotExist:
                raise NotFoundException(
                    message=f"Classe de trafic {traffic_class_id} non trouvée",
                    details={"traffic_class_id": traffic_class_id}
                )
            
            # Vérifier si la classe a des classificateurs
            if traffic_class.trafficclassifier_set.exists():
                raise ValidationException(
                    message="Impossible de supprimer la classe de trafic car elle a des classificateurs associés",
                    details={"traffic_class_id": traffic_class_id, "classifiers_count": traffic_class.trafficclassifier_set.count()}
                )
            
            # Récupérer les informations pour l'événement
            policy_id = traffic_class.policy.id
            name = traffic_class.name
            
            # Supprimer la classe de trafic
            traffic_class.delete()
            
            # Publier un événement de suppression
            EventBus.publish_async(TrafficClassDeletedEvent(
                traffic_class_id=traffic_class_id,
                policy_id=policy_id,
                name=name
            ))
            
            return True
            
        except (NotFoundException, ValidationException):
            # Remonter ces exceptions
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la classe de trafic {traffic_class_id}: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def get_traffic_class_by_id(cls, traffic_class_id: int) -> TrafficClass:
        """
        Récupère une classe de trafic par son ID
        
        Args:
            traffic_class_id (int): ID de la classe de trafic
            
        Returns:
            TrafficClass: La classe de trafic
            
        Raises:
            NotFoundException: Si la classe de trafic n'existe pas
        """
        try:
            return TrafficClass.objects.get(id=traffic_class_id)
        except TrafficClass.DoesNotExist:
            raise NotFoundException(
                message=f"Classe de trafic {traffic_class_id} non trouvée",
                details={"traffic_class_id": traffic_class_id}
            )
    
    @classmethod
    def get_traffic_classes_by_policy(cls, policy_id: int) -> List[TrafficClass]:
        """
        Récupère les classes de trafic d'une politique
        
        Args:
            policy_id (int): ID de la politique
            
        Returns:
            list: Les classes de trafic
            
        Raises:
            NotFoundException: Si la politique n'existe pas
        """
        try:
            # Vérifier si la politique existe
            if not QoSPolicy.objects.filter(id=policy_id).exists():
                raise NotFoundException(
                    message=f"Politique QoS {policy_id} non trouvée",
                    details={"policy_id": policy_id}
                )
            
            return list(TrafficClass.objects.filter(policy_id=policy_id).order_by('priority'))
            
        except NotFoundException:
            # Remonter cette exception
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des classes de trafic pour la politique {policy_id}: {str(e)}", exc_info=True)
            return [] 