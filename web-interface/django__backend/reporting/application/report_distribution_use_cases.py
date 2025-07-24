"""
Cas d'utilisation pour la distribution des rapports.

Ce module implémente les cas d'utilisation liés à la distribution
des rapports via différents canaux (email, Slack, webhooks, etc.).
"""

from typing import Dict, List, Any, Optional, Union
from ..domain.interfaces import ReportRepository, ScheduledReportRepository
from ..domain.strategies import ReportDistributionStrategy

class DistributeReportUseCase:
    """
    Cas d'utilisation pour distribuer un rapport.
    
    Cette classe utilise le pattern Strategy pour déléguer la distribution 
    à différentes stratégies selon le canal de distribution choisi.
    """
    
    def __init__(self, 
                 report_repository: ReportRepository,
                 distribution_strategies: Dict[str, ReportDistributionStrategy]):
        """
        Initialise le cas d'utilisation avec les dépendances nécessaires.
        
        Args:
            report_repository: Repository pour accéder aux rapports
            distribution_strategies: Dictionnaire des stratégies de distribution disponibles
        """
        self.report_repository = report_repository
        self.distribution_strategies = distribution_strategies
    
    def execute(self, report_id: int, 
               distribution_channels: List[str], 
               recipients: Dict[str, List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Distribue un rapport via les canaux spécifiés.
        
        Args:
            report_id: ID du rapport à distribuer
            distribution_channels: Liste des canaux de distribution ('email', 'slack', 'webhook', etc.)
            recipients: Dictionnaire des destinataires par canal
                       {'email': [{'address': 'user@example.com'}, ...],
                        'slack': [{'channel': '#notifications'}, ...]}
                        
        Returns:
            Résultat de la distribution
            
        Raises:
            ValueError: Si le rapport n'existe pas ou si un canal n'est pas supporté
        """
        # Récupérer le rapport
        report = self.report_repository.get_by_id(report_id)
        if not report:
            raise ValueError(f"Rapport avec ID {report_id} introuvable")
        
        results = {
            'report_id': report_id,
            'success': [],
            'failed': []
        }
        
        # Distribuer via chaque canal
        for channel in distribution_channels:
            if channel not in self.distribution_strategies:
                results['failed'].append({
                    'channel': channel,
                    'error': 'Canal non supporté'
                })
                continue
            
            # Récupérer les destinataires pour ce canal
            channel_recipients = recipients.get(channel, []) if recipients else []
            
            try:
                # Utiliser la stratégie appropriée
                strategy = self.distribution_strategies[channel]
                
                # Valider les destinataires
                validation_errors = strategy.validate_recipients(channel_recipients)
                if validation_errors:
                    results['failed'].append({
                        'channel': channel,
                        'error': 'Validation des destinataires échouée',
                        'details': validation_errors
                    })
                    continue
                
                # Distribuer le rapport
                success = strategy.distribute(report, channel_recipients)
                
                if success:
                    results['success'].append({'channel': channel})
                else:
                    results['failed'].append({
                        'channel': channel,
                        'error': 'Échec de la distribution'
                    })
            except Exception as e:
                results['failed'].append({
                    'channel': channel,
                    'error': str(e)
                })
        
        # Mettre à jour le rapport avec les informations de distribution
        self.report_repository.update(report_id, {
            'distribution': {
                'channels': distribution_channels,
                'results': results
            }
        })
        
        return results

class ScheduleReportDistributionUseCase:
    """
    Cas d'utilisation pour planifier la distribution d'un rapport.
    """
    
    def __init__(self, 
                 report_repository: ReportRepository,
                 scheduled_report_repository: ScheduledReportRepository):
        """
        Initialise le cas d'utilisation avec les dépendances nécessaires.
        
        Args:
            report_repository: Repository pour accéder aux rapports
            scheduled_report_repository: Repository pour accéder aux rapports planifiés
        """
        self.report_repository = report_repository
        self.scheduled_report_repository = scheduled_report_repository
    
    def execute(self, 
               report_id: int, 
               schedule: str, 
               distribution_channels: List[str],
               recipients: Dict[str, List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Planifie la distribution d'un rapport.
        
        Args:
            report_id: ID du rapport à distribuer
            schedule: Fréquence de planification ('daily', 'weekly', 'monthly', 'quarterly')
            distribution_channels: Liste des canaux de distribution
            recipients: Dictionnaire des destinataires par canal
            
        Returns:
            Rapport planifié créé
            
        Raises:
            ValueError: Si le rapport n'existe pas ou si le format de planification est invalide
        """
        # Vérifier que le rapport existe
        report = self.report_repository.get_by_id(report_id)
        if not report:
            raise ValueError(f"Rapport avec ID {report_id} introuvable")
        
        # Valider la fréquence
        if schedule not in ['daily', 'weekly', 'monthly', 'quarterly']:
            raise ValueError(f"Fréquence de planification invalide: {schedule}")
        
        # Créer la planification
        scheduled_data = {
            'report_id': report_id,
            'frequency': schedule,
            'distribution_channels': distribution_channels,
            'recipients': recipients or {}
        }
        
        scheduled_report = self.scheduled_report_repository.create(scheduled_data)
        
        return scheduled_report

class CancelReportDistributionUseCase:
    """
    Cas d'utilisation pour annuler la distribution planifiée d'un rapport.
    """
    
    def __init__(self, scheduled_report_repository: ScheduledReportRepository):
        """
        Initialise le cas d'utilisation avec les dépendances nécessaires.
        
        Args:
            scheduled_report_repository: Repository pour accéder aux rapports planifiés
        """
        self.scheduled_report_repository = scheduled_report_repository
    
    def execute(self, scheduled_report_id: int) -> bool:
        """
        Annule une distribution planifiée.
        
        Args:
            scheduled_report_id: ID de la distribution planifiée à annuler
            
        Returns:
            True si l'annulation a réussi
            
        Raises:
            ValueError: Si la distribution planifiée n'existe pas
        """
        # Vérifier que la planification existe
        scheduled_report = self.scheduled_report_repository.get_by_id(scheduled_report_id)
        if not scheduled_report:
            raise ValueError(f"Distribution planifiée avec ID {scheduled_report_id} introuvable")
        
        # Désactiver la planification
        result = self.scheduled_report_repository.update(
            scheduled_report_id,
            {'is_active': False}
        )
        
        return result is not None

class ManageDistributionRecipientsUseCase:
    """
    Cas d'utilisation pour gérer les destinataires d'une distribution.
    """
    
    def __init__(self, scheduled_report_repository: ScheduledReportRepository):
        """
        Initialise le cas d'utilisation avec les dépendances nécessaires.
        
        Args:
            scheduled_report_repository: Repository pour accéder aux rapports planifiés
        """
        self.scheduled_report_repository = scheduled_report_repository
    
    def add_recipients(self, scheduled_report_id: int, 
                      channel: str, 
                      recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Ajoute des destinataires à une distribution planifiée.
        
        Args:
            scheduled_report_id: ID de la distribution planifiée
            channel: Canal de distribution ('email', 'slack', etc.)
            recipients: Liste des destinataires à ajouter
            
        Returns:
            Distribution planifiée mise à jour
            
        Raises:
            ValueError: Si la distribution planifiée n'existe pas
        """
        # Vérifier que la planification existe
        scheduled_report = self.scheduled_report_repository.get_by_id(scheduled_report_id)
        if not scheduled_report:
            raise ValueError(f"Distribution planifiée avec ID {scheduled_report_id} introuvable")
        
        # Récupérer les destinataires actuels
        current_recipients = scheduled_report.get('recipients', {})
        
        # Ajouter les nouveaux destinataires
        channel_recipients = current_recipients.get(channel, [])
        channel_recipients.extend(recipients)
        
        # Supprimer les doublons en utilisant un identifiant unique par destinataire
        unique_recipients = []
        seen = set()
        
        for recipient in channel_recipients:
            # Créer une clé unique basée sur les propriétés du destinataire
            if channel == 'email':
                key = recipient.get('address')
            elif channel == 'slack':
                key = recipient.get('channel')
            else:
                key = str(recipient)
            
            if key not in seen:
                seen.add(key)
                unique_recipients.append(recipient)
        
        # Mettre à jour les destinataires
        current_recipients[channel] = unique_recipients
        
        # Mettre à jour la planification
        updated_report = self.scheduled_report_repository.update(
            scheduled_report_id,
            {'recipients': current_recipients}
        )
        
        return updated_report
    
    def remove_recipients(self, scheduled_report_id: int, 
                         channel: str, 
                         recipients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Retire des destinataires d'une distribution planifiée.
        
        Args:
            scheduled_report_id: ID de la distribution planifiée
            channel: Canal de distribution ('email', 'slack', etc.)
            recipients: Liste des destinataires à retirer
            
        Returns:
            Distribution planifiée mise à jour
            
        Raises:
            ValueError: Si la distribution planifiée n'existe pas
        """
        # Vérifier que la planification existe
        scheduled_report = self.scheduled_report_repository.get_by_id(scheduled_report_id)
        if not scheduled_report:
            raise ValueError(f"Distribution planifiée avec ID {scheduled_report_id} introuvable")
        
        # Récupérer les destinataires actuels
        current_recipients = scheduled_report.get('recipients', {})
        
        if channel not in current_recipients:
            return scheduled_report  # Rien à faire
        
        # Créer un ensemble des identifiants à supprimer
        to_remove = set()
        
        for recipient in recipients:
            if channel == 'email':
                key = recipient.get('address')
            elif channel == 'slack':
                key = recipient.get('channel')
            else:
                key = str(recipient)
            
            to_remove.add(key)
        
        # Filtrer les destinataires
        filtered_recipients = []
        
        for recipient in current_recipients.get(channel, []):
            if channel == 'email':
                key = recipient.get('address')
            elif channel == 'slack':
                key = recipient.get('channel')
            else:
                key = str(recipient)
            
            if key not in to_remove:
                filtered_recipients.append(recipient)
        
        # Mettre à jour les destinataires
        current_recipients[channel] = filtered_recipients
        
        # Mettre à jour la planification
        updated_report = self.scheduled_report_repository.update(
            scheduled_report_id,
            {'recipients': current_recipients}
        )
        
        return updated_report 