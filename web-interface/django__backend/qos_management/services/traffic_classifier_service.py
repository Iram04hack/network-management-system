"""
Service pour la gestion des classificateurs de trafic
"""
import logging
import re
import ipaddress
from typing import Dict, Any, List, Optional, Union, Tuple
from django.utils import timezone
from django.db import transaction

from qos_management.models import TrafficClassifier, TrafficClass
from common.exceptions import (
    ValidationException, NotFoundException, 
    ServiceUnavailableException
)
from qos_management.events import (
    TrafficClassifierCreatedEvent, TrafficClassifierUpdatedEvent, 
    TrafficClassifierDeletedEvent, TrafficClassifiedEvent, EventBus
)

logger = logging.getLogger(__name__)

class TrafficClassifierService:
    """Service pour la gestion des classificateurs de trafic"""
    
    @classmethod
    def create_classifier(cls, classifier_data: Dict[str, Any]) -> TrafficClassifier:
        """
        Crée un nouveau classificateur de trafic
        
        Args:
            classifier_data (dict): Données du classificateur
            
        Returns:
            TrafficClassifier: Le classificateur créé
            
        Raises:
            ValidationException: Si les données sont invalides
            NotFoundException: Si la classe de trafic n'existe pas
        """
        try:
            with transaction.atomic():
                # Vérifier si une classe de trafic est spécifiée
                if not classifier_data.get('traffic_class_id'):
                    raise ValidationException(
                        message="L'ID de classe de trafic est obligatoire",
                        details={"field": "traffic_class_id"}
                    )
                
                # Récupérer la classe de trafic
                try:
                    traffic_class = TrafficClass.objects.get(id=classifier_data['traffic_class_id'])
                except TrafficClass.DoesNotExist:
                    raise NotFoundException(
                        message=f"Classe de trafic {classifier_data['traffic_class_id']} non trouvée",
                        details={"traffic_class_id": classifier_data['traffic_class_id']}
                    )
                
                # Valider le classificateur
                if 'name' not in classifier_data or not classifier_data['name']:
                    raise ValidationException(
                        message="Le nom du classificateur est obligatoire",
                        details={"field": "name"}
                    )
                
                # Valider l'adresse IP source si fournie
                if classifier_data.get('source_ip'):
                    try:
                        # Vérifier si c'est un CIDR valide
                        ipaddress.ip_network(classifier_data['source_ip'])
                    except ValueError:
                        raise ValidationException(
                            message=f"Adresse IP source invalide: {classifier_data['source_ip']}",
                            details={"field": "source_ip", "value": classifier_data['source_ip']}
                        )
                
                # Valider l'adresse IP destination si fournie
                if classifier_data.get('destination_ip'):
                    try:
                        # Vérifier si c'est un CIDR valide
                        ipaddress.ip_network(classifier_data['destination_ip'])
                    except ValueError:
                        raise ValidationException(
                            message=f"Adresse IP destination invalide: {classifier_data['destination_ip']}",
                            details={"field": "destination_ip", "value": classifier_data['destination_ip']}
                        )
                
                # Valider les ports source si fournis
                if classifier_data.get('source_port_start') is not None:
                    if not (0 <= classifier_data['source_port_start'] <= 65535):
                        raise ValidationException(
                            message=f"Port source de début invalide: {classifier_data['source_port_start']}",
                            details={"field": "source_port_start", "value": classifier_data['source_port_start'], "valid_range": "0-65535"}
                        )
                
                if classifier_data.get('source_port_end') is not None:
                    if not (0 <= classifier_data['source_port_end'] <= 65535):
                        raise ValidationException(
                            message=f"Port source de fin invalide: {classifier_data['source_port_end']}",
                            details={"field": "source_port_end", "value": classifier_data['source_port_end'], "valid_range": "0-65535"}
                        )
                    
                    if classifier_data.get('source_port_start') is not None and classifier_data['source_port_end'] < classifier_data['source_port_start']:
                        raise ValidationException(
                            message="Le port source de fin doit être supérieur ou égal au port source de début",
                            details={"source_port_start": classifier_data['source_port_start'], "source_port_end": classifier_data['source_port_end']}
                        )
                
                # Valider les ports destination si fournis
                if classifier_data.get('destination_port_start') is not None:
                    if not (0 <= classifier_data['destination_port_start'] <= 65535):
                        raise ValidationException(
                            message=f"Port destination de début invalide: {classifier_data['destination_port_start']}",
                            details={"field": "destination_port_start", "value": classifier_data['destination_port_start'], "valid_range": "0-65535"}
                        )
                
                if classifier_data.get('destination_port_end') is not None:
                    if not (0 <= classifier_data['destination_port_end'] <= 65535):
                        raise ValidationException(
                            message=f"Port destination de fin invalide: {classifier_data['destination_port_end']}",
                            details={"field": "destination_port_end", "value": classifier_data['destination_port_end'], "valid_range": "0-65535"}
                        )
                    
                    if classifier_data.get('destination_port_start') is not None and classifier_data['destination_port_end'] < classifier_data['destination_port_start']:
                        raise ValidationException(
                            message="Le port destination de fin doit être supérieur ou égal au port destination de début",
                            details={"destination_port_start": classifier_data['destination_port_start'], "destination_port_end": classifier_data['destination_port_end']}
                        )
                
                # Créer le classificateur
                classifier = TrafficClassifier.objects.create(
                    traffic_class=traffic_class,
                    name=classifier_data['name'],
                    description=classifier_data.get('description', ''),
                    protocol=classifier_data.get('protocol', 'any'),
                    source_ip=classifier_data.get('source_ip', ''),
                    destination_ip=classifier_data.get('destination_ip', ''),
                    source_port_start=classifier_data.get('source_port_start'),
                    source_port_end=classifier_data.get('source_port_end'),
                    destination_port_start=classifier_data.get('destination_port_start'),
                    destination_port_end=classifier_data.get('destination_port_end'),
                    dscp_marking=classifier_data.get('dscp_marking', ''),
                    vlan=classifier_data.get('vlan')
                )
                
                # Publier un événement de création
                EventBus.publish_async(TrafficClassifierCreatedEvent(
                    classifier_id=classifier.id,
                    traffic_class_id=traffic_class.id,
                    name=classifier.name
                ))
                
                return classifier
                
        except (ValidationException, NotFoundException):
            # Remonter ces exceptions
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la création du classificateur de trafic: {str(e)}", exc_info=True)
            raise ValidationException(
                message=f"Erreur lors de la création du classificateur de trafic: {str(e)}",
                details={"classifier_data": classifier_data}
            )
    
    @classmethod
    def update_classifier(cls, classifier_id: int, update_data: Dict[str, Any]) -> TrafficClassifier:
        """
        Met à jour un classificateur de trafic
        
        Args:
            classifier_id (int): ID du classificateur
            update_data (dict): Données à mettre à jour
            
        Returns:
            TrafficClassifier: Le classificateur mis à jour
            
        Raises:
            NotFoundException: Si le classificateur n'existe pas
            ValidationException: Si les données sont invalides
        """
        try:
            # Récupérer le classificateur
            try:
                classifier = TrafficClassifier.objects.get(id=classifier_id)
            except TrafficClassifier.DoesNotExist:
                raise NotFoundException(
                    message=f"Classificateur de trafic {classifier_id} non trouvé",
                    details={"classifier_id": classifier_id}
                )
            
            # Changer la classe de trafic si demandé
            if 'traffic_class_id' in update_data:
                try:
                    traffic_class = TrafficClass.objects.get(id=update_data['traffic_class_id'])
                    classifier.traffic_class = traffic_class
                except TrafficClass.DoesNotExist:
                    raise NotFoundException(
                        message=f"Classe de trafic {update_data['traffic_class_id']} non trouvée",
                        details={"traffic_class_id": update_data['traffic_class_id']}
                    )
            
            # Valider et mettre à jour les champs modifiables
            if 'name' in update_data:
                if not update_data['name']:
                    raise ValidationException(
                        message="Le nom du classificateur est obligatoire",
                        details={"field": "name"}
                    )
                classifier.name = update_data['name']
            
            if 'description' in update_data:
                classifier.description = update_data['description']
            
            if 'protocol' in update_data:
                classifier.protocol = update_data['protocol']
            
            # Valider et mettre à jour l'adresse IP source
            if 'source_ip' in update_data:
                if update_data['source_ip']:
                    try:
                        ipaddress.ip_network(update_data['source_ip'])
                        classifier.source_ip = update_data['source_ip']
                    except ValueError:
                        raise ValidationException(
                            message=f"Adresse IP source invalide: {update_data['source_ip']}",
                            details={"field": "source_ip", "value": update_data['source_ip']}
                        )
                else:
                    classifier.source_ip = ''
            
            # Valider et mettre à jour l'adresse IP destination
            if 'destination_ip' in update_data:
                if update_data['destination_ip']:
                    try:
                        ipaddress.ip_network(update_data['destination_ip'])
                        classifier.destination_ip = update_data['destination_ip']
                    except ValueError:
                        raise ValidationException(
                            message=f"Adresse IP destination invalide: {update_data['destination_ip']}",
                            details={"field": "destination_ip", "value": update_data['destination_ip']}
                        )
                else:
                    classifier.destination_ip = ''
            
            # Mettre à jour les ports
            if 'source_port_start' in update_data:
                if update_data['source_port_start'] is not None and not (0 <= update_data['source_port_start'] <= 65535):
                    raise ValidationException(
                        message=f"Port source de début invalide: {update_data['source_port_start']}",
                        details={"field": "source_port_start", "value": update_data['source_port_start'], "valid_range": "0-65535"}
                    )
                classifier.source_port_start = update_data['source_port_start']
            
            if 'source_port_end' in update_data:
                if update_data['source_port_end'] is not None and not (0 <= update_data['source_port_end'] <= 65535):
                    raise ValidationException(
                        message=f"Port source de fin invalide: {update_data['source_port_end']}",
                        details={"field": "source_port_end", "value": update_data['source_port_end'], "valid_range": "0-65535"}
                    )
                classifier.source_port_end = update_data['source_port_end']
            
            # Vérifier la cohérence des ports source
            if classifier.source_port_start is not None and classifier.source_port_end is not None:
                if classifier.source_port_end < classifier.source_port_start:
                    raise ValidationException(
                        message="Le port source de fin doit être supérieur ou égal au port source de début",
                        details={"source_port_start": classifier.source_port_start, "source_port_end": classifier.source_port_end}
                    )
            
            if 'destination_port_start' in update_data:
                if update_data['destination_port_start'] is not None and not (0 <= update_data['destination_port_start'] <= 65535):
                    raise ValidationException(
                        message=f"Port destination de début invalide: {update_data['destination_port_start']}",
                        details={"field": "destination_port_start", "value": update_data['destination_port_start'], "valid_range": "0-65535"}
                    )
                classifier.destination_port_start = update_data['destination_port_start']
            
            if 'destination_port_end' in update_data:
                if update_data['destination_port_end'] is not None and not (0 <= update_data['destination_port_end'] <= 65535):
                    raise ValidationException(
                        message=f"Port destination de fin invalide: {update_data['destination_port_end']}",
                        details={"field": "destination_port_end", "value": update_data['destination_port_end'], "valid_range": "0-65535"}
                    )
                classifier.destination_port_end = update_data['destination_port_end']
            
            # Vérifier la cohérence des ports destination
            if classifier.destination_port_start is not None and classifier.destination_port_end is not None:
                if classifier.destination_port_end < classifier.destination_port_start:
                    raise ValidationException(
                        message="Le port destination de fin doit être supérieur ou égal au port destination de début",
                        details={"destination_port_start": classifier.destination_port_start, "destination_port_end": classifier.destination_port_end}
                    )
            
            # Mettre à jour les autres champs
            if 'dscp_marking' in update_data:
                classifier.dscp_marking = update_data['dscp_marking']
            
            if 'vlan' in update_data:
                classifier.vlan = update_data['vlan']
            
            # Enregistrer les modifications
            classifier.save()
            
            # Publier un événement de mise à jour
            EventBus.publish_async(TrafficClassifierUpdatedEvent(
                classifier_id=classifier.id,
                changes=update_data,
                traffic_class_id=classifier.traffic_class.id,
                name=classifier.name
            ))
            
            return classifier
            
        except (NotFoundException, ValidationException):
            # Remonter ces exceptions
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du classificateur de trafic {classifier_id}: {str(e)}", exc_info=True)
            raise ValidationException(
                message=f"Erreur lors de la mise à jour du classificateur de trafic: {str(e)}",
                details={"classifier_id": classifier_id, "update_data": update_data}
            )
    
    @classmethod
    def delete_classifier(cls, classifier_id: int) -> bool:
        """
        Supprime un classificateur de trafic
        
        Args:
            classifier_id (int): ID du classificateur
            
        Returns:
            bool: True si la suppression a réussi
            
        Raises:
            NotFoundException: Si le classificateur n'existe pas
        """
        try:
            # Récupérer le classificateur
            try:
                classifier = TrafficClassifier.objects.get(id=classifier_id)
            except TrafficClassifier.DoesNotExist:
                raise NotFoundException(
                    message=f"Classificateur de trafic {classifier_id} non trouvé",
                    details={"classifier_id": classifier_id}
                )
            
            # Récupérer les informations pour l'événement
            traffic_class_id = classifier.traffic_class.id
            name = classifier.name
            
            # Supprimer le classificateur
            classifier.delete()
            
            # Publier un événement de suppression
            EventBus.publish_async(TrafficClassifierDeletedEvent(
                classifier_id=classifier_id,
                traffic_class_id=traffic_class_id,
                name=name
            ))
            
            return True
            
        except NotFoundException:
            # Remonter cette exception
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du classificateur de trafic {classifier_id}: {str(e)}", exc_info=True)
            return False
    
    @classmethod
    def match_packet(cls, classifier_id: int, packet_data: Dict[str, Any]) -> bool:
        """
        Vérifie si un paquet correspond à un classificateur
        
        Args:
            classifier_id (int): ID du classificateur
            packet_data (dict): Données du paquet
            
        Returns:
            bool: True si le paquet correspond au classificateur
            
        Raises:
            NotFoundException: Si le classificateur n'existe pas
            ValidationException: Si les données du paquet sont invalides
        """
        try:
            # Valider les données du paquet
            required_fields = ['protocol', 'src_ip', 'dst_ip']
            for field in required_fields:
                if field not in packet_data:
                    raise ValidationException(
                        message=f"Le champ {field} est obligatoire dans les données du paquet",
                        details={"field": field}
                    )
            
            # Récupérer le classificateur
            try:
                classifier = TrafficClassifier.objects.get(id=classifier_id)
            except TrafficClassifier.DoesNotExist:
                raise NotFoundException(
                    message=f"Classificateur de trafic {classifier_id} non trouvé",
                    details={"classifier_id": classifier_id}
                )
            
            # Vérifier le protocole
            if classifier.protocol != 'any' and packet_data['protocol'] != classifier.protocol:
                return False
            
            # Vérifier l'adresse IP source
            if classifier.source_ip:
                if not cls._ip_matches_cidr(packet_data['src_ip'], classifier.source_ip):
                    return False
            
            # Vérifier l'adresse IP destination
            if classifier.destination_ip:
                if not cls._ip_matches_cidr(packet_data['dst_ip'], classifier.destination_ip):
                    return False
            
            # Vérifier le port source
            if classifier.source_port_start is not None:
                if 'sport' not in packet_data:
                    return False
                
                if classifier.source_port_end is not None:
                    # Plage de ports
                    if not (classifier.source_port_start <= packet_data['sport'] <= classifier.source_port_end):
                        return False
                else:
                    # Port unique
                    if packet_data['sport'] != classifier.source_port_start:
                        return False
            
            # Vérifier le port destination
            if classifier.destination_port_start is not None:
                if 'dport' not in packet_data:
                    return False
                
                if classifier.destination_port_end is not None:
                    # Plage de ports
                    if not (classifier.destination_port_start <= packet_data['dport'] <= classifier.destination_port_end):
                        return False
                else:
                    # Port unique
                    if packet_data['dport'] != classifier.destination_port_start:
                        return False
            
            # Vérifier le VLAN si spécifié
            if classifier.vlan is not None:
                if 'vlan' not in packet_data or packet_data['vlan'] != classifier.vlan:
                    return False
            
            # Vérifier le DSCP si spécifié
            if classifier.dscp_marking:
                if 'dscp' not in packet_data or packet_data['dscp'] != classifier.dscp_marking:
                    return False
            
            # Le paquet correspond au classificateur
            # Publier un événement de classification
            EventBus.publish_async(TrafficClassifiedEvent(
                packet_id=packet_data.get('id', 0),
                classifier_id=classifier_id,
                traffic_class_id=classifier.traffic_class.id,
                matched=True
            ))
            
            return True
            
        except (NotFoundException, ValidationException):
            # Remonter ces exceptions
            raise
        except Exception as e:
            logger.error(f"Erreur lors de la vérification du paquet avec le classificateur {classifier_id}: {str(e)}", exc_info=True)
            # Publier un événement d'échec de classification
            if 'classifier' in locals():
                EventBus.publish_async(TrafficClassifiedEvent(
                    packet_id=packet_data.get('id', 0),
                    classifier_id=classifier_id,
                    traffic_class_id=classifier.traffic_class.id,
                    matched=False,
                    details={"error": str(e)}
                ))
            return False
    
    @classmethod
    def find_matching_traffic_class(cls, packet_data: Dict[str, Any], policy_id: int) -> Tuple[Optional[int], Optional[int]]:
        """
        Trouve la classe de trafic correspondant à un paquet pour une politique donnée
        
        Args:
            packet_data (dict): Données du paquet
            policy_id (int): ID de la politique QoS
            
        Returns:
            tuple: (traffic_class_id, classifier_id) ou (None, None) si aucune correspondance
        """
        try:
            # Récupérer tous les classificateurs de la politique, dans l'ordre de priorité
            classifiers = TrafficClassifier.objects.filter(
                traffic_class__policy_id=policy_id
            ).select_related('traffic_class').order_by('traffic_class__priority')
            
            # Essayer chaque classificateur
            for classifier in classifiers:
                if cls.match_packet(classifier.id, packet_data):
                    return classifier.traffic_class.id, classifier.id
            
            # Aucune correspondance trouvée
            return None, None
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de classe de trafic pour le paquet: {str(e)}", exc_info=True)
            return None, None
    
    @classmethod
    def _ip_matches_cidr(cls, ip: str, cidr: str) -> bool:
        """
        Vérifie si une adresse IP correspond à un CIDR
        
        Args:
            ip (str): Adresse IP à vérifier
            cidr (str): CIDR à comparer
            
        Returns:
            bool: True si l'IP correspond au CIDR
        """
        try:
            return ipaddress.ip_address(ip) in ipaddress.ip_network(cidr)
        except Exception:
            return False 