"""
Cas d'utilisation pour la gestion des rapports planifiés.

Ce module contient les cas d'utilisation spécifiquement dédiés aux rapports planifiés,
intégrant avec le système de notification et la génération automatique.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..domain.interfaces import ReportRepository, ScheduledReportRepository
from ..domain.strategies import ReportGenerationStrategy
from ..infrastructure.notification_service import ReportingNotificationService

logger = logging.getLogger(__name__)


class GetScheduledReportUseCase:
    """Cas d'utilisation pour récupérer les rapports planifiés."""
    
    def __init__(self, scheduled_report_repository: ScheduledReportRepository):
        self.scheduled_report_repository = scheduled_report_repository
    
    def get_scheduled_report_by_id(self, scheduled_report_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un rapport planifié par son ID.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            
        Returns:
            Données du rapport planifié ou None si introuvable
        """
        try:
            scheduled_report = self.scheduled_report_repository.get_by_id(scheduled_report_id)
            
            if scheduled_report:
                # Enrichir avec les métadonnées
                scheduled_report['next_execution'] = self._calculate_next_execution(scheduled_report)
                
            return scheduled_report
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du rapport planifié {scheduled_report_id}: {e}")
            return None
    
    def list_scheduled_reports(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Liste les rapports planifiés selon les filtres.
        
        Args:
            filters: Filtres à appliquer
            
        Returns:
            Liste des rapports planifiés
        """
        try:
            scheduled_reports = self.scheduled_report_repository.list(filters)
            
            # Enrichir chaque rapport avec les métadonnées
            for report in scheduled_reports:
                report['next_execution'] = self._calculate_next_execution(report)
                
            return scheduled_reports
            
        except Exception as e:
            logger.error(f"Erreur lors de la liste des rapports planifiés: {e}")
            return []
    
    def _calculate_next_execution(self, scheduled_report: Dict[str, Any]) -> Optional[str]:
        """Calcule la prochaine exécution d'un rapport planifié."""
        frequency = scheduled_report.get('frequency')
        last_executed = scheduled_report.get('last_executed_at')
        
        if not frequency:
            return None
        
        # Simulation simple - dans une implémentation réelle, utiliser une bibliothèque comme croniter
        from datetime import timedelta
        
        base_time = datetime.now()
        if last_executed:
            try:
                base_time = datetime.fromisoformat(last_executed.replace('Z', '+00:00'))
            except:
                pass
        
        if frequency == 'daily':
            next_time = base_time + timedelta(days=1)
        elif frequency == 'weekly':
            next_time = base_time + timedelta(weeks=1)
        elif frequency == 'monthly':
            next_time = base_time + timedelta(days=30)
        elif frequency == 'quarterly':
            next_time = base_time + timedelta(days=90)
        else:
            return None
            
        return next_time.isoformat()


class CreateScheduledReportUseCase:
    """Cas d'utilisation pour créer des rapports planifiés."""
    
    def __init__(self, 
                 scheduled_report_repository: ScheduledReportRepository,
                 report_repository: ReportRepository):
        self.scheduled_report_repository = scheduled_report_repository
        self.report_repository = report_repository
    
    def create_scheduled_report(self, scheduled_report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau rapport planifié.
        
        Args:
            scheduled_report_data: Données du rapport planifié
            
        Returns:
            Rapport planifié créé
            
        Raises:
            ValueError: Si les données sont invalides
        """
        try:
            # Validation des données essentielles
            required_fields = ['report_type', 'frequency', 'created_by_id']
            for field in required_fields:
                if field not in scheduled_report_data:
                    raise ValueError(f"Champ requis manquant: {field}")
            
            # Validation de la fréquence
            valid_frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
            if scheduled_report_data['frequency'] not in valid_frequencies:
                raise ValueError(f"Fréquence invalide. Valeurs acceptées: {valid_frequencies}")
            
            # Enrichir les données
            creation_data = {
                **scheduled_report_data,
                'created_at': datetime.now().isoformat(),
                'is_active': scheduled_report_data.get('is_active', True),
                'last_executed_at': None,
                'execution_count': 0
            }
            
            # Créer le rapport planifié
            created_report = self.scheduled_report_repository.create(creation_data)
            
            logger.info(f"Rapport planifié créé avec succès: {created_report.get('id')}")
            return created_report
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du rapport planifié: {e}")
            raise


class ManageScheduledReportUseCase:
    """Cas d'utilisation pour gérer les rapports planifiés."""
    
    def __init__(self, scheduled_report_repository: ScheduledReportRepository):
        self.scheduled_report_repository = scheduled_report_repository
    
    def update_scheduled_report(self, scheduled_report_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            update_data: Données à mettre à jour
            
        Returns:
            Rapport planifié mis à jour
            
        Raises:
            ValueError: Si le rapport n'existe pas
        """
        try:
            # Vérifier que le rapport existe
            existing_report = self.scheduled_report_repository.get_by_id(scheduled_report_id)
            if not existing_report:
                raise ValueError(f"Rapport planifié {scheduled_report_id} introuvable")
            
            # Enrichir avec la date de modification
            update_data['updated_at'] = datetime.now().isoformat()
            
            # Mettre à jour
            updated_report = self.scheduled_report_repository.update(scheduled_report_id, update_data)
            
            logger.info(f"Rapport planifié {scheduled_report_id} mis à jour")
            return updated_report
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du rapport planifié {scheduled_report_id}: {e}")
            raise
    
    def delete_scheduled_report(self, scheduled_report_id: int) -> bool:
        """
        Supprime un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            
        Returns:
            True si supprimé avec succès
            
        Raises:
            ValueError: Si le rapport n'existe pas
        """
        try:
            # Vérifier que le rapport existe
            existing_report = self.scheduled_report_repository.get_by_id(scheduled_report_id)
            if not existing_report:
                raise ValueError(f"Rapport planifié {scheduled_report_id} introuvable")
            
            # Supprimer
            result = self.scheduled_report_repository.delete(scheduled_report_id)
            
            logger.info(f"Rapport planifié {scheduled_report_id} supprimé")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du rapport planifié {scheduled_report_id}: {e}")
            raise
    
    def add_recipient(self, scheduled_report_id: int, user_id: int) -> bool:
        """
        Ajoute un destinataire à un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            user_id: ID de l'utilisateur à ajouter
            
        Returns:
            True si ajouté avec succès
        """
        try:
            # Récupérer le rapport
            scheduled_report = self.scheduled_report_repository.get_by_id(scheduled_report_id)
            if not scheduled_report:
                raise ValueError(f"Rapport planifié {scheduled_report_id} introuvable")
            
            # Ajouter le destinataire
            recipients = scheduled_report.get('recipients', [])
            if user_id not in recipients:
                recipients.append(user_id)
                
                # Mettre à jour
                update_data = {
                    'recipients': recipients,
                    'updated_at': datetime.now().isoformat()
                }
                self.scheduled_report_repository.update(scheduled_report_id, update_data)
                
                logger.info(f"Destinataire {user_id} ajouté au rapport planifié {scheduled_report_id}")
                return True
            else:
                logger.warning(f"Destinataire {user_id} déjà présent dans le rapport planifié {scheduled_report_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du destinataire: {e}")
            return False
    
    def remove_recipient(self, scheduled_report_id: int, user_id: int) -> bool:
        """
        Retire un destinataire d'un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            user_id: ID de l'utilisateur à retirer
            
        Returns:
            True si retiré avec succès
        """
        try:
            # Récupérer le rapport
            scheduled_report = self.scheduled_report_repository.get_by_id(scheduled_report_id)
            if not scheduled_report:
                raise ValueError(f"Rapport planifié {scheduled_report_id} introuvable")
            
            # Retirer le destinataire
            recipients = scheduled_report.get('recipients', [])
            if user_id in recipients:
                recipients.remove(user_id)
                
                # Mettre à jour
                update_data = {
                    'recipients': recipients,
                    'updated_at': datetime.now().isoformat()
                }
                self.scheduled_report_repository.update(scheduled_report_id, update_data)
                
                logger.info(f"Destinataire {user_id} retiré du rapport planifié {scheduled_report_id}")
                return True
            else:
                logger.warning(f"Destinataire {user_id} non trouvé dans le rapport planifié {scheduled_report_id}")
                return True
                
        except Exception as e:
            logger.error(f"Erreur lors du retrait du destinataire: {e}")
            return False


class ExecuteScheduledReportUseCase:
    """Cas d'utilisation pour exécuter les rapports planifiés."""
    
    def __init__(self, 
                 scheduled_report_repository: ScheduledReportRepository,
                 report_repository: ReportRepository,
                 notification_service: ReportingNotificationService):
        self.scheduled_report_repository = scheduled_report_repository
        self.report_repository = report_repository
        self.notification_service = notification_service
    
    def execute_scheduled_report(self, scheduled_report_id: int) -> bool:
        """
        Exécute un rapport planifié.
        
        Args:
            scheduled_report_id: ID du rapport planifié
            
        Returns:
            True si exécuté avec succès
        """
        try:
            # Récupérer le rapport planifié
            scheduled_report = self.scheduled_report_repository.get_by_id(scheduled_report_id)
            if not scheduled_report:
                raise ValueError(f"Rapport planifié {scheduled_report_id} introuvable")
            
            if not scheduled_report.get('is_active', True):
                logger.warning(f"Rapport planifié {scheduled_report_id} inactif - exécution ignorée")
                return False
            
            # Préparer les paramètres du rapport
            report_params = {
                'title': scheduled_report.get('title', f"Rapport planifié {scheduled_report['report_type']}"),
                'description': scheduled_report.get('description', ''),
                'format': scheduled_report.get('format', 'pdf'),
                'parameters': scheduled_report.get('parameters', {}),
                'scheduled_execution': True,
                'scheduled_report_id': scheduled_report_id
            }
            
            # Générer le rapport
            # Note: Ici nous simulons la génération car elle dépend des services d'infrastructure
            report_data = {
                'title': report_params['title'],
                'description': report_params['description'],
                'report_type': scheduled_report['report_type'],
                'parameters': report_params['parameters'],
                'content': self._generate_mock_content(scheduled_report['report_type']),
                'file_path': f"/tmp/scheduled_report_{scheduled_report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                'created_by': scheduled_report.get('created_by_id'),
                'scheduled_report_id': scheduled_report_id,
                'generated_at': datetime.now().isoformat()
            }
            
            # Sauvegarder le rapport généré
            created_report = self.report_repository.create(report_data)
            
            # Mettre à jour les statistiques du rapport planifié
            execution_update = {
                'last_executed_at': datetime.now().isoformat(),
                'execution_count': scheduled_report.get('execution_count', 0) + 1,
                'last_report_id': created_report.get('id')
            }
            self.scheduled_report_repository.update(scheduled_report_id, execution_update)
            
            # Envoyer les notifications si des destinataires sont configurés
            recipients = scheduled_report.get('recipients', [])
            if recipients:
                notification_data = {
                    'report_id': created_report.get('id'),
                    'report_title': report_data['title'],
                    'report_type': report_data['report_type'],
                    'recipients': recipients,
                    'channels': scheduled_report.get('notification_channels', ['email']),
                    'report_file_path': report_data['file_path']
                }
                
                notification_result = self.notification_service.send_report_notification(notification_data)
                logger.info(f"Notifications envoyées pour le rapport planifié {scheduled_report_id}: {notification_result}")
            
            logger.info(f"Rapport planifié {scheduled_report_id} exécuté avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du rapport planifié {scheduled_report_id}: {e}")
            
            # Mettre à jour les statistiques d'erreur
            try:
                error_update = {
                    'last_error_at': datetime.now().isoformat(),
                    'last_error_message': str(e),
                    'error_count': scheduled_report.get('error_count', 0) + 1
                }
                self.scheduled_report_repository.update(scheduled_report_id, error_update)
            except:
                pass
            
            return False
    
    def execute_due_reports(self) -> Dict[str, Any]:
        """
        Exécute tous les rapports planifiés qui sont dus.
        
        Returns:
            Résumé des exécutions
        """
        try:
            # Récupérer tous les rapports actifs
            active_reports = self.scheduled_report_repository.list({'is_active': True})
            
            execution_summary = {
                'total_checked': len(active_reports),
                'executed': 0,
                'skipped': 0,
                'failed': 0,
                'details': []
            }
            
            for scheduled_report in active_reports:
                scheduled_report_id = scheduled_report['id']
                
                # Vérifier si le rapport est dû
                if self._is_report_due(scheduled_report):
                    try:
                        success = self.execute_scheduled_report(scheduled_report_id)
                        if success:
                            execution_summary['executed'] += 1
                            execution_summary['details'].append({
                                'id': scheduled_report_id,
                                'title': scheduled_report.get('title'),
                                'status': 'executed'
                            })
                        else:
                            execution_summary['failed'] += 1
                            execution_summary['details'].append({
                                'id': scheduled_report_id,
                                'title': scheduled_report.get('title'),
                                'status': 'failed'
                            })
                    except Exception as e:
                        execution_summary['failed'] += 1
                        execution_summary['details'].append({
                            'id': scheduled_report_id,
                            'title': scheduled_report.get('title'),
                            'status': 'error',
                            'error': str(e)
                        })
                else:
                    execution_summary['skipped'] += 1
            
            logger.info(f"Exécution des rapports dus terminée: {execution_summary}")
            return execution_summary
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution des rapports dus: {e}")
            return {
                'total_checked': 0,
                'executed': 0,
                'skipped': 0,
                'failed': 0,
                'error': str(e)
            }
    
    def _is_report_due(self, scheduled_report: Dict[str, Any]) -> bool:
        """Vérifie si un rapport planifié est dû pour exécution."""
        frequency = scheduled_report.get('frequency')
        last_executed = scheduled_report.get('last_executed_at')
        
        if not frequency:
            return False
        
        if not last_executed:
            return True  # Jamais exécuté, donc dû
        
        try:
            last_exec_time = datetime.fromisoformat(last_executed.replace('Z', '+00:00'))
            current_time = datetime.now()
            
            if frequency == 'daily':
                return (current_time - last_exec_time).days >= 1
            elif frequency == 'weekly':
                return (current_time - last_exec_time).days >= 7
            elif frequency == 'monthly':
                return (current_time - last_exec_time).days >= 30
            elif frequency == 'quarterly':
                return (current_time - last_exec_time).days >= 90
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'échéance: {e}")
            return False
        
        return False
    
    def _generate_mock_content(self, report_type: str) -> Dict[str, Any]:
        """Génère un contenu de rapport simulé."""
        return {
            'report_type': report_type,
            'generated_at': datetime.now().isoformat(),
            'summary': f'Résumé du rapport {report_type}',
            'data': {
                'metrics': [
                    {'name': 'Total Devices', 'value': 45},
                    {'name': 'Online Devices', 'value': 42},
                    {'name': 'Alerts', 'value': 3}
                ],
                'details': f'Détails spécifiques au rapport {report_type}'
            }
        }