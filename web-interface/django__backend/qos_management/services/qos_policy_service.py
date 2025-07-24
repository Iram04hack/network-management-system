"""
Service pour la gestion des politiques QoS
"""
import logging
from typing import Dict, Any, List, Optional, Union
from django.utils import timezone
from django.db import transaction

from qos_management.models import QoSPolicy, TrafficClass, InterfaceQoSPolicy
from network_management.infrastructure.models import NetworkInterface as Interface
from common.exceptions import (
    ValidationException, NotFoundException, 
    ServiceUnavailableException
)
from qos_management.events import (
    QoSPolicyCreatedEvent, QoSPolicyUpdatedEvent, QoSPolicyDeletedEvent,
    QoSPolicyAppliedEvent, QoSPolicyRemovedEvent, InterfaceQoSStatusChangedEvent
)

logger = logging.getLogger(__name__)

# Classe EventBus simplifiée pour remplacer l'import externe
class EventBus:
    @staticmethod
    def publish_async(event):
        # Implémentation simplifiée
        logger.info(f"Événement publié de manière asynchrone: {event}")
        pass

class QoSPolicyService:
    """Service pour la gestion des politiques QoS"""
    
    @classmethod
    def create_policy(cls, policy_data: Dict[str, Any]) -> QoSPolicy:
        """
        Crée une nouvelle politique QoS
        
        Args:
            policy_data (dict): Données de la politique
            
        Returns:
            QoSPolicy: La politique créée
            
        Raises:
            ValidationException: Si les données sont invalides
        """
        try:
            with transaction.atomic():
                # Validation des données
                if not policy_data.get('name'):
                    raise ValidationException(
                        message="Le nom de la politique est obligatoire",
                        details={"field": "name"}
                    )
                
                # Vérifier si une politique avec ce nom existe déjà
                if QoSPolicy.objects.filter(name=policy_data['name']).exists():
                    raise ValidationException(
                        message=f"Une politique avec le nom {policy_data['name']} existe déjà",
                        details={"field": "name", "value": policy_data['name']}
                    )
                
                # Créer la politique
                policy = QoSPolicy.objects.create(
                    name=policy_data['name'],
                    description=policy_data.get('description', ''),
                    is_active=policy_data.get('is_active', True),
                    bandwidth_limit=policy_data.get('bandwidth_limit'),
                    default_priority=policy_data.get('default_priority', 'normal')
                )
                
                # Créer les classes de trafic si fournies
                if 'traffic_classes' in policy_data:
                    for tc_data in policy_data['traffic_classes']:
                        TrafficClass.objects.create(
                            policy=policy,
                            name=tc_data['name'],
                            priority=tc_data.get('priority', 'normal'),
                            bandwidth_percentage=tc_data.get('bandwidth_percentage', 0),
                            dscp_marking=tc_data.get('dscp_marking'),
                            description=tc_data.get('description', '')
                        )
                
                # Publier un événement de création
                EventBus.publish_async(QoSPolicyCreatedEvent(
                    policy_id=policy.id,
                    name=policy.name,
                    created_by=policy_data.get('created_by')
                ))
                
                return policy
                
        except ValidationException:
            # Remonter l'exception
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la création de la politique QoS: {str(e)}", exc_info=True)
            raise ValidationException(
                message=f"Erreur lors de la création de la politique QoS: {str(e)}",
                details={"policy_data": policy_data}
            )
    
    @classmethod
    def update_policy(cls, policy_id: int, update_data: Dict[str, Any]) -> QoSPolicy:
        """
        Met à jour une politique QoS
        
        Args:
            policy_id (int): ID de la politique
            update_data (dict): Données à mettre à jour
            
        Returns:
            QoSPolicy: La politique mise à jour
            
        Raises:
            NotFoundException: Si la politique n'existe pas
            ValidationException: Si les données sont invalides
        """
        try:
            # Récupérer la politique
            try:
                policy = QoSPolicy.objects.get(id=policy_id)
            except QoSPolicy.DoesNotExist:
                raise NotFoundException(
                    message=f"Politique QoS {policy_id} non trouvée",
                    details={"policy_id": policy_id}
                )
            
            # Vérifier si le nom est modifié et qu'il n'existe pas déjà
            if 'name' in update_data and update_data['name'] != policy.name:
                if QoSPolicy.objects.filter(name=update_data['name']).exists():
                    raise ValidationException(
                        message=f"Une politique avec le nom {update_data['name']} existe déjà",
                        details={"field": "name", "value": update_data['name']}
                    )
            
            # Enregistrer les changements
            changes = {}
            
            # Mise à jour des champs
            for field, value in update_data.items():
                if field != 'traffic_classes' and hasattr(policy, field):
                    old_value = getattr(policy, field)
                    if old_value != value:
                        changes[field] = {"old": old_value, "new": value}
                        setattr(policy, field, value)
            
            policy.save()
            
            # Mettre à jour les classes de trafic si fournies
            if 'traffic_classes' in update_data:
                # Logique de mise à jour des classes de trafic ici
                # Pour simplifier, nous ne l'implémentons pas dans cet exemple
                pass
            
            # Publier un événement de mise à jour si des changements ont été effectués
            if changes:
                EventBus.publish_async(QoSPolicyUpdatedEvent(
                    policy_id=policy.id,
                    changes=changes,
                    name=policy.name,
                    updated_by=update_data.get('updated_by')
                ))
            
            return policy
            
        except (NotFoundException, ValidationException):
            # Remonter ces exceptions
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la politique QoS {policy_id}: {str(e)}", exc_info=True)
            raise ValidationException(
                message=f"Erreur lors de la mise à jour de la politique QoS: {str(e)}",
                details={"policy_id": policy_id, "update_data": update_data}
            )
    
    @classmethod
    def delete_policy(cls, policy_id: int) -> bool:
        """
        Supprime une politique QoS
        
        Args:
            policy_id (int): ID de la politique
            
        Returns:
            bool: True si la suppression a réussi
            
        Raises:
            NotFoundException: Si la politique n'existe pas
        """
        try:
            # Récupérer la politique
            try:
                policy = QoSPolicy.objects.get(id=policy_id)
            except QoSPolicy.DoesNotExist:
                raise NotFoundException(
                    message=f"Politique QoS {policy_id} non trouvée",
                    details={"policy_id": policy_id}
                )
            
            # Vérifier si la politique est appliquée à des interfaces
            if InterfaceQoSPolicy.objects.filter(policy=policy).exists():
                raise ValidationException(
                    message="Impossible de supprimer la politique car elle est appliquée à une ou plusieurs interfaces",
                    details={"policy_id": policy_id}
                )
            
            # Stocker le nom pour l'événement
            policy_name = policy.name
            
            # Supprimer la politique
            policy.delete()
            
            # Publier un événement de suppression
            EventBus.publish_async(QoSPolicyDeletedEvent(
                policy_id=policy_id,
                name=policy_name
            ))
            
            return True
            
        except NotFoundException:
            # Remonter cette exception
            raise
        except ValidationException:
            # Remonter cette exception
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la politique QoS {policy_id}: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def apply_policy_to_interface(cls, policy_id: int, interface_id: int, 
                                direction: str = 'outbound') -> Dict[str, Any]:
        """
        Applique une politique QoS à une interface
        
        Args:
            policy_id (int): ID de la politique
            interface_id (int): ID de l'interface
            direction (str, optional): Direction (inbound/outbound). Par défaut 'outbound'.
            
        Returns:
            dict: Résultat de l'opération
            
        Raises:
            NotFoundException: Si la politique ou l'interface n'existe pas
            ValidationException: Si la direction est invalide
        """
        try:
            # Valider la direction
            if direction not in ['inbound', 'outbound']:
                raise ValidationException(
                    message=f"Direction invalide: {direction}",
                    details={"direction": direction, "valid_values": ['inbound', 'outbound']}
                )
            
            # Récupérer la politique
            try:
                policy = QoSPolicy.objects.get(id=policy_id)
            except QoSPolicy.DoesNotExist:
                raise NotFoundException(
                    message=f"Politique QoS {policy_id} non trouvée",
                    details={"policy_id": policy_id}
                )
            
            # Récupérer l'interface
            try:
                interface = Interface.objects.get(id=interface_id)
            except Interface.DoesNotExist:
                raise NotFoundException(
                    message=f"Interface {interface_id} non trouvée",
                    details={"interface_id": interface_id}
                )
            
            # Vérifier si la politique est déjà appliquée
            if InterfaceQoSPolicy.objects.filter(
                interface=interface,
                policy=policy,
                direction=direction
            ).exists():
                raise ValidationException(
                    message=f"La politique est déjà appliquée à cette interface dans cette direction",
                    details={"policy_id": policy_id, "interface_id": interface_id, "direction": direction}
                )
            
            # Appliquer la politique
            interface_policy = InterfaceQoSPolicy.objects.create(
                interface=interface,
                policy=policy,
                direction=direction,
                status='active'
            )
            
            # TODO: Implémenter l'application réelle des règles TC sur l'équipement
            # via un service externe ou une commande système
            
            # Publier un événement
            EventBus.publish_async(QoSPolicyAppliedEvent(
                entity_id=interface_policy.id,
                policy_id=policy_id,
                interface_id=interface_id,
                direction=direction
            ))
            
            return {
                "success": True,
                "interface_policy_id": interface_policy.id,
                "policy_id": policy_id,
                "interface_id": interface_id,
                "direction": direction
            }
            
        except (NotFoundException, ValidationException):
            # Remonter ces exceptions
            raise
        except Exception as e:
            logger.error(f"Erreur lors de l'application de la politique QoS: {str(e)}", exc_info=True)
            raise ValidationException(
                message=f"Erreur lors de l'application de la politique QoS: {str(e)}",
                details={"policy_id": policy_id, "interface_id": interface_id}
            )
    
    @classmethod
    def remove_policy_from_interface(cls, interface_policy_id: int) -> Dict[str, Any]:
        """
        Retire une politique QoS d'une interface
        
        Args:
            interface_policy_id (int): ID de l'application de politique
            
        Returns:
            dict: Résultat de l'opération
            
        Raises:
            NotFoundException: Si l'application de politique n'existe pas
        """
        try:
            # Récupérer l'application de politique
            try:
                interface_policy = InterfaceQoSPolicy.objects.get(id=interface_policy_id)
            except InterfaceQoSPolicy.DoesNotExist:
                raise NotFoundException(
                    message=f"Application de politique QoS {interface_policy_id} non trouvée",
                    details={"interface_policy_id": interface_policy_id}
                )
            
            # Récupérer les informations pour l'événement
            policy_id = interface_policy.policy.id
            interface_id = interface_policy.interface.id
            direction = interface_policy.direction
            
            # Supprimer l'application
            interface_policy.delete()
            
            # TODO: Implémenter la suppression réelle des règles TC sur l'équipement
            # via un service externe ou une commande système
            
            # Publier un événement
            EventBus.publish_async(QoSPolicyRemovedEvent(
                entity_id=interface_policy_id,
                policy_id=policy_id,
                interface_id=interface_id,
                direction=direction
            ))
            
            return {
                "success": True,
                "interface_policy_id": interface_policy_id,
                "policy_id": policy_id,
                "interface_id": interface_id
            }
            
        except NotFoundException:
            # Remonter cette exception
            raise
        except Exception as e:
            logger.error(f"Erreur lors du retrait de la politique QoS: {str(e)}", exc_info=True)
            raise ServiceUnavailableException(
                message=f"Erreur lors du retrait de la politique QoS: {str(e)}",
                details={"interface_policy_id": interface_policy_id}
            )
    
    @classmethod
    def get_policy_by_id(cls, policy_id: int) -> QoSPolicy:
        """
        Récupère une politique QoS par son ID
        
        Args:
            policy_id (int): ID de la politique
            
        Returns:
            QoSPolicy: La politique
            
        Raises:
            NotFoundException: Si la politique n'existe pas
        """
        try:
            return QoSPolicy.objects.get(id=policy_id)
        except QoSPolicy.DoesNotExist:
            raise NotFoundException(
                message=f"Politique QoS {policy_id} non trouvée",
                details={"policy_id": policy_id}
            )
    
    @classmethod
    def change_interface_policy_status(cls, interface_policy_id: int, new_status: str) -> InterfaceQoSPolicy:
        """
        Change le statut d'une application de politique QoS
        
        Args:
            interface_policy_id (int): ID de l'application de politique
            new_status (str): Nouveau statut ('active', 'inactive')
            
        Returns:
            InterfaceQoSPolicy: L'application de politique mise à jour
            
        Raises:
            NotFoundException: Si l'application de politique n'existe pas
            ValidationException: Si le statut est invalide
        """
        try:
            # Récupérer l'application de politique
            try:
                interface_policy = InterfaceQoSPolicy.objects.get(id=interface_policy_id)
            except InterfaceQoSPolicy.DoesNotExist:
                raise NotFoundException(
                    message=f"Application de politique QoS {interface_policy_id} non trouvée",
                    details={"interface_policy_id": interface_policy_id}
                )
            
            # Valider le statut
            valid_statuses = ['active', 'inactive']
            if new_status not in valid_statuses:
                raise ValidationException(
                    message=f"Statut invalide: {new_status}",
                    details={"interface_policy_id": interface_policy_id, "valid_statuses": valid_statuses}
                )
            
            # Si le statut est déjà celui demandé, ne rien faire
            if interface_policy.status == new_status:
                return interface_policy
            
            # Enregistrer l'ancien statut
            old_status = interface_policy.status
            
            # Mettre à jour le statut
            interface_policy.status = new_status
            interface_policy.save()
            
            # TODO: Implémenter l'activation/désactivation réelle des règles TC sur l'équipement
            # via un service externe ou une commande système
            
            # Publier un événement
            EventBus.publish_async(InterfaceQoSStatusChangedEvent(
                interface_qos_id=interface_policy_id,
                old_status=old_status,
                new_status=new_status,
                interface_id=interface_policy.interface.id,
                policy_id=interface_policy.policy.id
            ))
            
            return interface_policy
            
        except (NotFoundException, ValidationException):
            # Remonter ces exceptions
            raise
        except Exception as e:
            logger.error(f"Erreur lors du changement de statut de l'application de politique QoS: {str(e)}", exc_info=True)
            raise ServiceUnavailableException(
                message=f"Erreur lors du changement de statut de l'application de politique QoS: {str(e)}",
                details={"interface_policy_id": interface_policy_id, "new_status": new_status}
            ) 