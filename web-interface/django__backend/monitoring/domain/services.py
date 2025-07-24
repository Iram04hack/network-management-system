"""
Services du domaine pour le module monitoring.

Ce module contient les services métier qui implémentent la logique du domaine.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MetricCollectionService:
    """
    Service pour la collecte de métriques.
    """
    
    def __init__(self, device_metric_repository, metric_value_repository):
        self.device_metric_repository = device_metric_repository
        self.metric_value_repository = metric_value_repository
    
    def collect_metric(self, device_metric_id: int) -> Dict[str, Any]:
        """
        Collecte une métrique spécifique.
        
        Args:
            device_metric_id: ID de la métrique d'équipement
            
        Returns:
            La valeur collectée
        """
        try:
            # Récupérer la configuration de la métrique
            device_metric = self.device_metric_repository.get_by_id(device_metric_id)
            if not device_metric:
                return {
                    'success': False,
                    'error': f'Métrique d\'équipement {device_metric_id} non trouvée'
                }
            
            # Collecter la valeur selon le type de métrique
            collection_result = self._collect_metric_value(device_metric)
            
            if collection_result['success']:
                # Sauvegarder la valeur collectée
                metric_value_data = {
                    'device_metric_id': device_metric_id,
                    'value': collection_result['value'],
                    'timestamp': datetime.now(),
                    'status': 'success',
                    'metadata': collection_result.get('metadata', {})
                }
                
                saved_value = self.metric_value_repository.create(metric_value_data)
                
                return {
                    'success': True,
                    'device_metric_id': device_metric_id,
                    'value': collection_result['value'],
                    'metric_value_id': saved_value.get('id'),
                    'timestamp': metric_value_data['timestamp'].isoformat()
                }
            else:
                return {
                    'success': False,
                    'device_metric_id': device_metric_id,
                    'error': collection_result.get('error', 'Échec de collecte')
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la collecte de métrique {device_metric_id}: {e}")
            return {
                'success': False,
                'device_metric_id': device_metric_id,
                'error': str(e)
            }
    
    def _collect_metric_value(self, device_metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collecte la valeur d'une métrique selon son type.
        
        Args:
            device_metric: Configuration de la métrique
            
        Returns:
            Résultat de la collecte
        """
        metric_type = device_metric.get('metric_type', 'snmp')
        
        if metric_type == 'snmp':
            return self._collect_snmp_metric(device_metric)
        elif metric_type == 'ping':
            return self._collect_ping_metric(device_metric)
        elif metric_type == 'port_check':
            return self._collect_port_metric(device_metric)
        else:
            return {
                'success': False,
                'error': f'Type de métrique non supporté: {metric_type}'
            }
    
    def _collect_snmp_metric(self, device_metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collecte une métrique SNMP.
        """
        try:
            from ..infrastructure.adapters.snmp_adapter import SNMPAdapter
            
            snmp_adapter = SNMPAdapter()
            device_ip = device_metric.get('device_ip')
            oid = device_metric.get('oid')
            community = device_metric.get('snmp_community', 'public')
            
            if not device_ip or not oid:
                return {
                    'success': False,
                    'error': 'Adresse IP ou OID manquant pour la métrique SNMP'
                }
            
            result = snmp_adapter.get_single_oid(device_ip, oid, community)
            
            if result['success']:
                return {
                    'success': True,
                    'value': result['value'],
                    'metadata': {
                        'oid': oid,
                        'community': community,
                        'response_time': result.get('response_time')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Erreur SNMP inconnue')
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors de la collecte SNMP: {e}'
            }
    
    def _collect_ping_metric(self, device_metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collecte une métrique de ping (latence).
        """
        try:
            import subprocess
            import re
            
            device_ip = device_metric.get('device_ip')
            if not device_ip:
                return {
                    'success': False,
                    'error': 'Adresse IP manquante pour le ping'
                }
            
            # Exécuter ping
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '5', device_ip],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Extraire la latence
                match = re.search(r'time=([0-9.]+)', result.stdout)
                if match:
                    latency = float(match.group(1))
                    return {
                        'success': True,
                        'value': latency,
                        'metadata': {
                            'unit': 'ms',
                            'packet_loss': 0
                        }
                    }
            
            return {
                'success': False,
                'error': 'Ping échoué ou latence non trouvée'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors du ping: {e}'
            }
    
    def _collect_port_metric(self, device_metric: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collecte une métrique de port (connectivité).
        """
        try:
            import socket
            from datetime import datetime
            
            device_ip = device_metric.get('device_ip')
            port = device_metric.get('port')
            
            if not device_ip or not port:
                return {
                    'success': False,
                    'error': 'Adresse IP ou port manquant'
                }
            
            start_time = datetime.now()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            try:
                result = sock.connect_ex((device_ip, int(port)))
                end_time = datetime.now()
                response_time = (end_time - start_time).total_seconds() * 1000
                
                if result == 0:
                    return {
                        'success': True,
                        'value': 1,  # Port ouvert
                        'metadata': {
                            'port': port,
                            'response_time_ms': response_time
                        }
                    }
                else:
                    return {
                        'success': True,
                        'value': 0,  # Port fermé
                        'metadata': {
                            'port': port,
                            'error_code': result
                        }
                    }
            finally:
                sock.close()
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Erreur lors du test de port: {e}'
            }
    
    def collect_metrics_for_device(self, device_id: int) -> List[Dict[str, Any]]:
        """
        Collecte toutes les métriques pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Liste des valeurs collectées
        """
        try:
            # Récupérer toutes les métriques configurées pour cet équipement
            device_metrics = self.device_metric_repository.get_by_device_id(device_id)
            
            if not device_metrics:
                logger.warning(f"Aucune métrique configurée pour l'équipement {device_id}")
                return []
            
            results = []
            successful_collections = 0
            failed_collections = 0
            
            for device_metric in device_metrics:
                if not device_metric.get('is_enabled', True):
                    continue
                    
                metric_result = self.collect_metric(device_metric['id'])
                results.append(metric_result)
                
                if metric_result['success']:
                    successful_collections += 1
                else:
                    failed_collections += 1
            
            logger.info(
                f"Collecte terminée pour l'équipement {device_id}: "
                f"{successful_collections} succès, {failed_collections} échecs"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte pour l'équipement {device_id}: {e}")
            return [{
                'success': False,
                'device_id': device_id,
                'error': str(e)
            }]


class AlertingService:
    """
    Service pour la gestion des alertes.
    """
    
    def __init__(self, alert_repository, notification_service):
        self.alert_repository = alert_repository
        self.notification_service = notification_service
    
    def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle alerte.
        
        Args:
            alert_data: Données de l'alerte
            
        Returns:
            L'alerte créée
        """
        try:
            # Validation des données obligatoires
            required_fields = ['device_id', 'metric_name', 'severity', 'message']
            for field in required_fields:
                if field not in alert_data:
                    return {
                        'success': False,
                        'error': f'Champ obligatoire manquant: {field}'
                    }
            
            # Vérifier si une alerte similaire existe déjà
            existing_alert = self._check_existing_alert(alert_data)
            if existing_alert:
                # Mettre à jour l'alerte existante
                return self._update_existing_alert(existing_alert, alert_data)
            
            # Enrichir les données de l'alerte
            enriched_alert_data = {
                **alert_data,
                'status': 'active',
                'created_at': datetime.now(),
                'last_occurrence': datetime.now(),
                'occurrence_count': 1,
                'acknowledged': False
            }
            
            # Sauvegarder l'alerte
            created_alert = self.alert_repository.create(enriched_alert_data)
            
            # Envoyer la notification
            notification_result = self.notification_service.send_notification({
                'alert_id': created_alert['id'],
                'type': 'alert_created',
                'severity': alert_data['severity'],
                'message': alert_data['message'],
                'device_id': alert_data['device_id']
            })
            
            logger.info(f"Alerte créée: {created_alert['id']} pour l'équipement {alert_data['device_id']}")
            
            return {
                'success': True,
                'alert': created_alert,
                'notification_sent': notification_result.get('success', False)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la création d'alerte: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _check_existing_alert(self, alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Vérifie si une alerte similaire existe déjà.
        """
        try:
            # Rechercher des alertes actives pour le même équipement et métrique
            existing_alerts = self.alert_repository.find_by_criteria({
                'device_id': alert_data['device_id'],
                'metric_name': alert_data['metric_name'],
                'status': 'active'
            })
            
            return existing_alerts[0] if existing_alerts else None
            
        except Exception as e:
            logger.warning(f"Erreur lors de la vérification d'alerte existante: {e}")
            return None
    
    def _update_existing_alert(self, existing_alert: Dict[str, Any], new_alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Met à jour une alerte existante.
        """
        try:
            update_data = {
                'last_occurrence': datetime.now(),
                'occurrence_count': existing_alert.get('occurrence_count', 1) + 1,
                'message': new_alert_data['message'],
                'severity': new_alert_data['severity']
            }
            
            updated_alert = self.alert_repository.update(existing_alert['id'], update_data)
            
            logger.info(f"Alerte mise à jour: {existing_alert['id']} (occurrence #{update_data['occurrence_count']})")
            
            return {
                'success': True,
                'alert': updated_alert,
                'updated': True
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour d'alerte: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_alert(self, alert_id: int) -> Dict[str, Any]:
        """
        Traite une alerte.
        
        Args:
            alert_id: ID de l'alerte
            
        Returns:
            L'alerte traitée
        """
        try:
            # Récupérer l'alerte
            alert = self.alert_repository.get_by_id(alert_id)
            if not alert:
                return {
                    'success': False,
                    'error': f'Alerte {alert_id} non trouvée'
                }
            
            processing_result = {
                'alert_id': alert_id,
                'actions_taken': [],
                'success': True
            }
            
            # Évaluer la sévérité et prendre les actions appropriées
            severity = alert.get('severity', 'medium')
            
            if severity == 'critical':
                # Actions pour alertes critiques
                processing_result['actions_taken'].extend([
                    'notification_immediate',
                    'escalation_triggered'
                ])
                
                # Notifier immédiatement
                self.notification_service.send_notification({
                    'alert_id': alert_id,
                    'type': 'critical_alert',
                    'priority': 'immediate',
                    'message': alert['message']
                })
                
            elif severity == 'high':
                # Actions pour alertes élevées
                processing_result['actions_taken'].extend([
                    'notification_high_priority'
                ])
                
            # Vérifier si l'alerte doit être auto-résolue
            if self._should_auto_resolve(alert):
                resolve_result = self.resolve_alert(alert_id, 'auto_resolved')
                if resolve_result['success']:
                    processing_result['actions_taken'].append('auto_resolved')
            
            # Mettre à jour le statut de traitement
            self.alert_repository.update(alert_id, {
                'processed_at': datetime.now(),
                'processing_status': 'processed'
            })
            
            return processing_result
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement d'alerte {alert_id}: {e}")
            return {
                'success': False,
                'alert_id': alert_id,
                'error': str(e)
            }
    
    def _should_auto_resolve(self, alert: Dict[str, Any]) -> bool:
        """
        Détermine si une alerte doit être auto-résolue.
        """
        # Logique pour déterminer l'auto-résolution
        # Par exemple, si la métrique est revenue à la normale
        return False  # À implémenter selon les besoins spécifiques
    
    def resolve_alert(self, alert_id: int, resolution_reason: str = 'manual') -> Dict[str, Any]:
        """
        Résout une alerte.
        
        Args:
            alert_id: ID de l'alerte
            resolution_reason: Raison de la résolution
            
        Returns:
            Résultat de la résolution
        """
        try:
            update_data = {
                'status': 'resolved',
                'resolved_at': datetime.now(),
                'resolution_reason': resolution_reason
            }
            
            updated_alert = self.alert_repository.update(alert_id, update_data)
            
            # Notifier la résolution
            self.notification_service.send_notification({
                'alert_id': alert_id,
                'type': 'alert_resolved',
                'reason': resolution_reason
            })
            
            logger.info(f"Alerte {alert_id} résolue: {resolution_reason}")
            
            return {
                'success': True,
                'alert': updated_alert
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la résolution d'alerte {alert_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class ServiceCheckService:
    """
    Service pour les vérifications de service.
    """
    
    def __init__(self, service_check_repository, device_service_check_repository, check_result_repository, alerting_service):
        self.service_check_repository = service_check_repository
        self.device_service_check_repository = device_service_check_repository
        self.check_result_repository = check_result_repository
        self.alerting_service = alerting_service
    
    def perform_check(self, device_service_check_id: int) -> Dict[str, Any]:
        """
        Effectue une vérification de service.
        
        Args:
            device_service_check_id: ID de la vérification appliquée
            
        Returns:
            Le résultat de la vérification
        """
        # Implémentation de la vérification de service
        pass
    
    def process_check_result(self, check_result_id: int) -> Dict[str, Any]:
        """
        Traite un résultat de vérification.
        
        Args:
            check_result_id: ID du résultat
            
        Returns:
            Le résultat traité
        """
        # Implémentation du traitement de résultat
        pass


class DashboardService:
    """
    Service pour les tableaux de bord.
    """
    
    def __init__(self, dashboard_repository):
        self.dashboard_repository = dashboard_repository
    
    def create_dashboard(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau tableau de bord.
        
        Args:
            dashboard_data: Données du tableau de bord
            
        Returns:
            Le tableau de bord créé
        """
        # Implémentation de la création de tableau de bord
        pass
    
    def add_widget(self, dashboard_id: int, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ajoute un widget à un tableau de bord.
        
        Args:
            dashboard_id: ID du tableau de bord
            widget_data: Données du widget
            
        Returns:
            Le widget ajouté
        """
        # Implémentation de l'ajout de widget
        pass


class NotificationService:
    """
    Service pour les notifications.
    """
    
    def __init__(self, notification_repository):
        self.notification_repository = notification_repository
    
    def send_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Envoie une notification.
        
        Args:
            notification_data: Données de la notification
            
        Returns:
            La notification envoyée
        """
        try:
            # Enrichir les données de notification
            enriched_notification = {
                **notification_data,
                'sent_at': datetime.now(),
                'status': 'pending',
                'attempts': 0
            }
            
            # Sauvegarder la notification
            saved_notification = self.notification_repository.create(enriched_notification)
            
            # Déterminer le canal de notification
            notification_type = notification_data.get('type', 'info')
            priority = notification_data.get('priority', 'normal')
            
            send_results = []
            
            # Envoyer via email (simulation)
            if self._should_send_email(notification_type, priority):
                email_result = self._send_email_notification(saved_notification)
                send_results.append(email_result)
            
            # Envoyer via webhook (simulation)
            if self._should_send_webhook(notification_type, priority):
                webhook_result = self._send_webhook_notification(saved_notification)
                send_results.append(webhook_result)
            
            # Mettre à jour le statut
            success = any(result.get('success', False) for result in send_results)
            status = 'sent' if success else 'failed'
            
            updated_notification = self.notification_repository.update(saved_notification['id'], {
                'status': status,
                'sent_at': datetime.now() if success else None,
                'send_results': send_results
            })
            
            return {
                'success': success,
                'notification': updated_notification,
                'channels_used': len(send_results)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de notification: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _should_send_email(self, notification_type: str, priority: str) -> bool:
        """
        Détermine si une notification doit être envoyée par email.
        """
        return notification_type in ['alert_created', 'critical_alert'] or priority == 'immediate'
    
    def _should_send_webhook(self, notification_type: str, priority: str) -> bool:
        """
        Détermine si une notification doit être envoyée via webhook.
        """
        return notification_type in ['alert_created', 'alert_resolved', 'critical_alert']
    
    def _send_email_notification(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simule l'envoi d'une notification par email.
        """
        try:
            # Simulation d'envoi d'email
            logger.info(f"Email envoyé pour notification {notification['id']}")
            return {
                'success': True,
                'channel': 'email',
                'sent_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'channel': 'email',
                'error': str(e)
            }
    
    def _send_webhook_notification(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simule l'envoi d'une notification via webhook.
        """
        try:
            # Simulation d'envoi de webhook
            logger.info(f"Webhook envoyé pour notification {notification['id']}")
            return {
                'success': True,
                'channel': 'webhook',
                'sent_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'channel': 'webhook',
                'error': str(e)
            }
    
    def mark_as_read(self, notification_id: int) -> Dict[str, Any]:
        """
        Marque une notification comme lue.
        
        Args:
            notification_id: ID de la notification
            
        Returns:
            La notification mise à jour
        """
        # Implémentation de la marque comme lue
        pass


class AnomalyDetectionService:
    """
    Service pour la détection d'anomalies.
    """
    
    def __init__(self, metric_value_repository):
        self.metric_value_repository = metric_value_repository
    
    def detect_anomalies(self, device_metric_id: int, time_range: Dict[str, datetime]) -> List[Dict[str, Any]]:
        """
        Détecte les anomalies pour une métrique.
        
        Args:
            device_metric_id: ID de la métrique d'équipement
            time_range: Plage de temps
            
        Returns:
            Liste des anomalies détectées
        """
        # Implémentation de la détection d'anomalies
        pass
    
    def predict_trend(self, device_metric_id: int, time_range: Dict[str, datetime]) -> Dict[str, Any]:
        """
        Prédit la tendance pour une métrique.
        
        Args:
            device_metric_id: ID de la métrique d'équipement
            time_range: Plage de temps
            
        Returns:
            La prédiction de tendance
        """
        # Implémentation de la prédiction de tendance
        pass 