"""
Système d'alertes basé sur des seuils réels pour le module Dashboard.

Ce module implémente l'évaluation de seuils en temps réel et la génération
d'alertes automatiques basées sur les métriques collectées.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from django.utils import timezone
from asgiref.sync import sync_to_async

# Import des modèles Django
from monitoring.models import (
    Alert, DeviceMetric, MetricValue, ThresholdRule, 
    MetricThreshold, MetricsDefinition
)
from network_management.models import NetworkDevice

logger = logging.getLogger(__name__)


class ThresholdAlertingService:
    """
    Service d'évaluation de seuils et de génération d'alertes automatiques.
    """
    
    def __init__(self):
        """Initialise le service d'alertes."""
        self._default_thresholds = {
            'cpu_utilization': {'warning': 70.0, 'critical': 90.0},
            'memory_utilization': {'warning': 80.0, 'critical': 95.0},
            'disk_utilization': {'warning': 85.0, 'critical': 95.0},
            'interface_utilization': {'warning': 80.0, 'critical': 95.0},
            'temperature': {'warning': 60.0, 'critical': 75.0},
            'packet_loss': {'warning': 1.0, 'critical': 5.0}
        }
    
    async def evaluate_device_thresholds(self, device_id: int) -> Dict[str, Any]:
        """
        Évalue les seuils pour un équipement spécifique et génère des alertes si nécessaire.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Résultats de l'évaluation des seuils
        """
        try:
            device = await sync_to_async(
                lambda: NetworkDevice.objects.get(id=device_id)
            )()
            
            logger.info(f"Évaluation des seuils pour l'équipement {device.name}")
            
            # Récupérer les métriques récentes de l'équipement
            device_metrics = await sync_to_async(
                lambda: list(DeviceMetric.objects.filter(
                    device=device, 
                    is_active=True
                ).select_related('metric_definition'))
            )()
            
            alerts_generated = []
            thresholds_evaluated = 0
            
            for device_metric in device_metrics:
                # Récupérer la valeur la plus récente
                latest_value = await sync_to_async(
                    lambda dm=device_metric: MetricValue.objects.filter(
                        device_metric=dm
                    ).order_by('-timestamp').first()
                )()
                
                if latest_value:
                    # Évaluer les seuils pour cette métrique
                    alert_result = await self._evaluate_metric_threshold(
                        device, device_metric, latest_value
                    )
                    
                    if alert_result:
                        alerts_generated.append(alert_result)
                    
                    thresholds_evaluated += 1
            
            result = {
                'device_id': device_id,
                'device_name': device.name,
                'thresholds_evaluated': thresholds_evaluated,
                'alerts_generated': len(alerts_generated),
                'alerts': alerts_generated,
                'evaluation_time': timezone.now().isoformat()
            }
            
            logger.info(f"Évaluation terminée pour {device.name}: {len(alerts_generated)} alertes générées")
            return result
            
        except NetworkDevice.DoesNotExist:
            logger.error(f"Équipement {device_id} non trouvé")
            return {"error": f"Device {device_id} not found"}
        except Exception as e:
            logger.error(f"Erreur évaluation seuils pour l'équipement {device_id}: {e}")
            return {"error": str(e)}
    
    async def _evaluate_metric_threshold(
        self, 
        device: NetworkDevice, 
        device_metric: DeviceMetric, 
        metric_value: MetricValue
    ) -> Optional[Dict[str, Any]]:
        """
        Évalue les seuils pour une métrique spécifique.
        
        Args:
            device: Équipement
            device_metric: Métrique de l'équipement
            metric_value: Valeur de la métrique
            
        Returns:
            Informations sur l'alerte générée ou None
        """
        try:
            metric_name = device_metric.metric_definition.name
            current_value = metric_value.value
            
            # Récupérer les seuils configurés pour cette métrique
            thresholds = await self._get_metric_thresholds(device_metric)
            
            if not thresholds:
                return None
            
            # Déterminer le niveau d'alerte
            alert_level = None
            threshold_value = None
            
            if current_value >= thresholds.get('critical', float('inf')):
                alert_level = 'critical'
                threshold_value = thresholds['critical']
            elif current_value >= thresholds.get('warning', float('inf')):
                alert_level = 'warning'
                threshold_value = thresholds['warning']
            
            if alert_level:
                # Vérifier si une alerte similaire existe déjà
                existing_alert = await sync_to_async(
                    lambda: Alert.objects.filter(
                        device=device,
                        metric_name=metric_name,
                        status='active'
                    ).first()
                )()
                
                if existing_alert:
                    # Mettre à jour l'alerte existante si nécessaire
                    if existing_alert.severity != alert_level:
                        existing_alert.severity = alert_level
                        existing_alert.updated_at = timezone.now()
                        await sync_to_async(existing_alert.save)()
                        
                        logger.info(f"Alerte mise à jour: {device.name} - {metric_name} - {alert_level}")
                        return {
                            'alert_id': existing_alert.id,
                            'action': 'updated',
                            'metric_name': metric_name,
                            'severity': alert_level,
                            'current_value': current_value,
                            'threshold_value': threshold_value
                        }
                else:
                    # Créer une nouvelle alerte
                    new_alert = await self._create_threshold_alert(
                        device, metric_name, alert_level, current_value, threshold_value
                    )
                    
                    logger.info(f"Nouvelle alerte créée: {device.name} - {metric_name} - {alert_level}")
                    return {
                        'alert_id': new_alert.id,
                        'action': 'created',
                        'metric_name': metric_name,
                        'severity': alert_level,
                        'current_value': current_value,
                        'threshold_value': threshold_value
                    }
            else:
                # Résoudre les alertes existantes si la valeur est revenue normale
                await self._resolve_threshold_alerts(device, metric_name)
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur évaluation seuil pour {metric_name}: {e}")
            return None
    
    async def _get_metric_thresholds(self, device_metric: DeviceMetric) -> Dict[str, float]:
        """
        Récupère les seuils configurés pour une métrique.
        
        Args:
            device_metric: Métrique de l'équipement
            
        Returns:
            Dictionnaire des seuils (warning, critical)
        """
        try:
            # Récupérer les seuils personnalisés s'ils existent
            custom_thresholds = await sync_to_async(
                lambda: list(MetricThreshold.objects.filter(device_metric=device_metric))
            )()
            
            if custom_thresholds:
                thresholds = {}
                for threshold in custom_thresholds:
                    thresholds[threshold.threshold_type] = threshold.threshold_value
                return thresholds
            
            # Utiliser les seuils par défaut
            metric_name = device_metric.metric_definition.name
            return self._default_thresholds.get(metric_name, {})
            
        except Exception as e:
            logger.error(f"Erreur récupération seuils: {e}")
            return {}
    
    async def _create_threshold_alert(
        self, 
        device: NetworkDevice, 
        metric_name: str, 
        severity: str, 
        current_value: float, 
        threshold_value: float
    ) -> Alert:
        """
        Crée une nouvelle alerte de seuil.
        
        Args:
            device: Équipement
            metric_name: Nom de la métrique
            severity: Niveau de sévérité
            current_value: Valeur actuelle
            threshold_value: Valeur du seuil
            
        Returns:
            Alerte créée
        """
        message = (
            f"{metric_name} threshold exceeded on {device.name}: "
            f"current={current_value:.2f}, threshold={threshold_value:.2f}"
        )
        
        alert = await sync_to_async(
            lambda: Alert.objects.create(
                device=device,
                alert_type='threshold',
                severity=severity,
                status='active',
                message=message,
                metric_name=metric_name,
                metric_value=current_value,
                threshold_value=threshold_value,
                created_at=timezone.now()
            )
        )()
        
        return alert
    
    async def _resolve_threshold_alerts(self, device: NetworkDevice, metric_name: str):
        """
        Résout les alertes de seuil pour une métrique quand elle revient normale.
        
        Args:
            device: Équipement
            metric_name: Nom de la métrique
        """
        try:
            active_alerts = await sync_to_async(
                lambda: list(Alert.objects.filter(
                    device=device,
                    metric_name=metric_name,
                    alert_type='threshold',
                    status='active'
                ))
            )()
            
            for alert in active_alerts:
                alert.status = 'resolved'
                alert.resolved_at = timezone.now()
                alert.resolution_comment = 'Metric returned to normal levels'
                await sync_to_async(alert.save)()
                
                logger.info(f"Alerte résolue: {device.name} - {metric_name}")
                
        except Exception as e:
            logger.error(f"Erreur résolution alertes: {e}")
    
    async def evaluate_all_devices_thresholds(self) -> Dict[str, Any]:
        """
        Évalue les seuils pour tous les équipements actifs.
        
        Returns:
            Résumé de l'évaluation globale
        """
        try:
            logger.info("Début de l'évaluation globale des seuils")
            
            # Récupérer tous les équipements actifs
            active_devices = await sync_to_async(
                lambda: list(NetworkDevice.objects.filter(status='active'))
            )()
            
            total_devices = len(active_devices)
            total_alerts = 0
            devices_with_alerts = 0
            
            results = []
            
            for device in active_devices:
                try:
                    device_result = await self.evaluate_device_thresholds(device.id)
                    results.append(device_result)
                    
                    alerts_count = device_result.get('alerts_generated', 0)
                    total_alerts += alerts_count
                    
                    if alerts_count > 0:
                        devices_with_alerts += 1
                        
                except Exception as e:
                    logger.error(f"Erreur évaluation pour {device.name}: {e}")
                    results.append({
                        'device_id': device.id,
                        'device_name': device.name,
                        'error': str(e)
                    })
                
                # Pause entre les évaluations
                await asyncio.sleep(0.1)
            
            summary = {
                'total_devices': total_devices,
                'devices_with_alerts': devices_with_alerts,
                'total_alerts_generated': total_alerts,
                'evaluation_time': timezone.now().isoformat(),
                'device_results': results
            }
            
            logger.info(f"Évaluation globale terminée: {total_alerts} alertes sur {devices_with_alerts} équipements")
            return summary
            
        except Exception as e:
            logger.error(f"Erreur évaluation globale des seuils: {e}")
            return {"error": str(e)}
    
    async def configure_device_thresholds(
        self, 
        device_id: int, 
        metric_name: str, 
        warning_threshold: float, 
        critical_threshold: float
    ) -> Dict[str, Any]:
        """
        Configure les seuils personnalisés pour une métrique d'un équipement.
        
        Args:
            device_id: ID de l'équipement
            metric_name: Nom de la métrique
            warning_threshold: Seuil d'avertissement
            critical_threshold: Seuil critique
            
        Returns:
            Résultat de la configuration
        """
        try:
            device = await sync_to_async(
                lambda: NetworkDevice.objects.get(id=device_id)
            )()
            
            # Récupérer ou créer la définition de métrique
            metric_def, created = await sync_to_async(
                lambda: MetricsDefinition.objects.get_or_create(
                    name=metric_name,
                    defaults={'description': f'Métrique {metric_name}', 'unit': 'percent'}
                )
            )()
            
            # Récupérer ou créer la métrique d'équipement
            device_metric, created = await sync_to_async(
                lambda: DeviceMetric.objects.get_or_create(
                    device=device,
                    metric_definition=metric_def,
                    defaults={'is_active': True}
                )
            )()
            
            # Configurer les seuils
            warning_threshold_obj, created = await sync_to_async(
                lambda: MetricThreshold.objects.update_or_create(
                    device_metric=device_metric,
                    threshold_type='warning',
                    defaults={'threshold_value': warning_threshold}
                )
            )()
            
            critical_threshold_obj, created = await sync_to_async(
                lambda: MetricThreshold.objects.update_or_create(
                    device_metric=device_metric,
                    threshold_type='critical',
                    defaults={'threshold_value': critical_threshold}
                )
            )()
            
            result = {
                'device_id': device_id,
                'device_name': device.name,
                'metric_name': metric_name,
                'warning_threshold': warning_threshold,
                'critical_threshold': critical_threshold,
                'configured_at': timezone.now().isoformat()
            }
            
            logger.info(f"Seuils configurés pour {device.name} - {metric_name}")
            return result
            
        except NetworkDevice.DoesNotExist:
            logger.error(f"Équipement {device_id} non trouvé")
            return {"error": f"Device {device_id} not found"}
        except Exception as e:
            logger.error(f"Erreur configuration seuils: {e}")
            return {"error": str(e)}


# Instance globale du service d'alertes
threshold_alerting = ThresholdAlertingService()
