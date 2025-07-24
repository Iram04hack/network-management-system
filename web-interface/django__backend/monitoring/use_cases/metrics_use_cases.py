"""
Use cases pour la gestion des métriques.

Ce module contient les cas d'utilisation pour la collecte,
l'analyse et la gestion des métriques de surveillance.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal

from ..domain.interfaces.repositories import (
    MetricsDefinitionRepository,
    DeviceMetricRepository,
    MetricValueRepository,
    AlertRepository
)
from ..domain.services import (
    MetricCollectionService,
    AlertingService
)

logger = logging.getLogger(__name__)


class CollectMetricsUseCase:
    """
    Use case pour la collecte de métriques des équipements.
    
    Coordonne la collecte de métriques selon les configurations
    définies pour chaque équipement.
    """
    
    def __init__(
        self,
        device_metric_repository: DeviceMetricRepository,
        metric_value_repository: MetricValueRepository,
        collection_service: MetricCollectionService,
        alert_service: AlertingService
    ):
        self.device_metric_repository = device_metric_repository
        self.metric_value_repository = metric_value_repository
        self.collection_service = collection_service
        self.alert_service = alert_service
    
    def execute(self, device_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Exécute la collecte de métriques.
        
        Args:
            device_id: ID de l'équipement spécifique (optionnel)
            
        Returns:
            Résultat de la collecte avec statistiques
        """
        try:
            if device_id:
                return self._collect_device_metrics(device_id)
            else:
                return self._collect_all_metrics()
                
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _collect_device_metrics(self, device_id: int) -> Dict[str, Any]:
        """Collecte les métriques pour un équipement spécifique."""
        try:
            metrics = self.device_metric_repository.list_by_device(device_id)
            
            if not metrics:
                return {
                    "success": False,
                    "message": f"Aucune métrique configurée pour l'équipement {device_id}",
                    "device_id": device_id,
                    "collected": 0
                }
            
            collected = 0
            errors = []
            
            for metric in metrics:
                try:
                    value = self.collection_service.collect_metric(metric)
                    if value is not None:
                        self.metric_value_repository.save({
                            'device_metric_id': metric.get('id'),
                            'value': value,
                            'timestamp': datetime.now()
                        })
                        collected += 1
                        
                        # Vérifier les seuils d'alerte
                        self._check_thresholds(metric, value)
                        
                except Exception as e:
                    error_msg = f"Erreur métrique {metric.get('id')}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            return {
                "success": True,
                "message": f"Collecte terminée pour l'équipement {device_id}",
                "device_id": device_id,
                "collected": collected,
                "total": len(metrics),
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte pour l'équipement {device_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "device_id": device_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _collect_all_metrics(self) -> Dict[str, Any]:
        """Collecte les métriques pour tous les équipements actifs."""
        try:
            # Récupérer toutes les métriques actives de tous les équipements
            metrics = self.device_metric_repository.list_all()
            
            collected = 0
            errors = []
            devices_count = 0
            
            devices = {}
            for metric in metrics:
                device_id = metric.get('device_id')
                if device_id not in devices:
                    devices[device_id] = []
                devices[device_id].append(metric)
            
            devices_count = len(devices)
            
            for device_id, device_metrics in devices.items():
                for metric in device_metrics:
                    try:
                        value = self.collection_service.collect_metric(metric)
                        if value is not None:
                            self.metric_value_repository.save({
                                'device_metric_id': metric.get('id'),
                                'value': value,
                                'timestamp': datetime.now()
                            })
                            collected += 1
                            
                            # Vérifier les seuils d'alerte
                            self._check_thresholds(metric, value)
                            
                    except Exception as e:
                        error_msg = f"Erreur métrique {metric.get('id')}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            
            return {
                "success": True,
                "message": "Collecte globale terminée",
                "devices_processed": devices_count,
                "collected": collected,
                "total": len(metrics),
                "errors": errors,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte globale: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _check_thresholds(self, metric, value: Union[float, int]):
        """Vérifie les seuils d'alerte pour une métrique."""
        try:
            # Récupérer les seuils configurés pour cette métrique
            thresholds = self._get_metric_thresholds(metric)
            
            if not thresholds:
                # Utiliser des seuils par défaut selon le type de métrique
                thresholds = self._get_default_thresholds(metric)
            
            for threshold in thresholds:
                if self._threshold_exceeded(value, threshold):
                    self.alert_service.create_alert({
                        'title': f"Seuil dépassé: {metric.get('name', 'Métrique inconnue')}",
                        'description': f"Valeur {value} dépasse le seuil {threshold.get('value')}",
                        'severity': threshold.get('severity'),
                        'source_type': 'metric',
                        'source_id': metric.get('id'),
                        'device_id': metric.get('device_id')
                    })
                    
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des seuils: {e}")
    
    def _get_metric_thresholds(self, metric) -> List[Dict[str, Any]]:
        """Récupère les seuils configurés pour une métrique."""
        try:
            # Récupérer depuis la base de données ou configuration
            # Pour l'instant, retourner une liste vide
            return []
        except Exception as e:
            logger.warning(f"Erreur lors de la récupération des seuils: {e}")
            return []
    
    def _get_default_thresholds(self, metric) -> List[Dict[str, Any]]:
        """Génère des seuils par défaut selon le type de métrique."""
        metric_name = metric.get('name', '').lower()
        metric_type = metric.get('metric_type', '')
        
        # Seuils par défaut selon le type de métrique
        if 'cpu' in metric_name or 'processor' in metric_name:
            return [
                {'condition': 'greater_than', 'value': 80, 'severity': 'warning'},
                {'condition': 'greater_than', 'value': 95, 'severity': 'critical'}
            ]
        elif 'memory' in metric_name or 'mem' in metric_name:
            return [
                {'condition': 'greater_than', 'value': 85, 'severity': 'warning'},
                {'condition': 'greater_than', 'value': 95, 'severity': 'critical'}
            ]
        elif 'disk' in metric_name or 'storage' in metric_name:
            return [
                {'condition': 'greater_than', 'value': 90, 'severity': 'warning'},
                {'condition': 'greater_than', 'value': 98, 'severity': 'critical'}
            ]
        elif 'bandwidth' in metric_name or 'traffic' in metric_name:
            return [
                {'condition': 'greater_than', 'value': 80, 'severity': 'warning'},
                {'condition': 'greater_than', 'value': 95, 'severity': 'critical'}
            ]
        elif 'ping' in metric_name or 'latency' in metric_name:
            return [
                {'condition': 'greater_than', 'value': 100, 'severity': 'warning'},  # 100ms
                {'condition': 'greater_than', 'value': 500, 'severity': 'critical'}   # 500ms
            ]
        elif 'packet_loss' in metric_name:
            return [
                {'condition': 'greater_than', 'value': 1, 'severity': 'warning'},    # 1%
                {'condition': 'greater_than', 'value': 5, 'severity': 'critical'}     # 5%
            ]
        else:
            # Seuils génériques
            return [
                {'condition': 'greater_than', 'value': 80, 'severity': 'warning'},
                {'condition': 'greater_than', 'value': 95, 'severity': 'critical'}
            ]
    
    def _threshold_exceeded(self, value: Union[float, int], threshold) -> bool:
        """Vérifie si un seuil est dépassé."""
        condition = threshold.get('condition')
        threshold_value = threshold.get('value')

        if condition == 'greater_than':
            return value > threshold_value
        elif condition == 'less_than':
            return value < threshold_value
        elif condition == 'equal':
            return value == threshold_value
        elif condition == 'greater_equal':
            return value >= threshold_value
        elif condition == 'less_equal':
            return value <= threshold_value
        return False


class AnalyzeMetricsUseCase:
    """
    Use case pour l'analyse des métriques.
    
    Fournit des analyses statistiques et des tendances
    sur les données de métriques collectées.
    """
    
    def __init__(
        self,
        metric_value_repository: MetricValueRepository,
        metrics_definition_repository: MetricsDefinitionRepository
    ):
        self.metric_value_repository = metric_value_repository
        self.metrics_definition_repository = metrics_definition_repository
    
    def execute(
        self,
        metric_id: int,
        start_time: datetime,
        end_time: datetime,
        analysis_type: str = "basic"
    ) -> Dict[str, Any]:
        """
        Exécute l'analyse des métriques.
        
        Args:
            metric_id: ID de la métrique à analyser
            start_time: Début de la période d'analyse
            end_time: Fin de la période d'analyse
            analysis_type: Type d'analyse ("basic", "advanced", "trend")
            
        Returns:
            Résultats de l'analyse
        """
        try:
            # Récupérer les données de la métrique
            values = self.metric_value_repository.get_values_by_period(
                metric_id, start_time, end_time
            )
            
            if not values:
                return {
                    "success": False,
                    "message": "Aucune donnée trouvée pour la période spécifiée",
                    "metric_id": metric_id
                }
            
            # Effectuer l'analyse selon le type demandé
            if analysis_type == "basic":
                results = self._basic_analysis(values)
            elif analysis_type == "advanced":
                results = self._advanced_analysis(values)
            elif analysis_type == "trend":
                results = self._trend_analysis(values)
            else:
                raise ValueError(f"Type d'analyse non supporté: {analysis_type}")
            
            results.update({
                "success": True,
                "metric_id": metric_id,
                "period": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "data_points": len(values),
                "analysis_type": analysis_type,
                "timestamp": datetime.now().isoformat()
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des métriques: {e}")
            return {
                "success": False,
                "error": str(e),
                "metric_id": metric_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def _basic_analysis(self, values: List[Dict]) -> Dict[str, Any]:
        """Analyse statistique de base."""
        numeric_values = [float(v['value']) for v in values]
        
        return {
            "statistics": {
                "min": min(numeric_values),
                "max": max(numeric_values),
                "avg": sum(numeric_values) / len(numeric_values),
                "count": len(numeric_values)
            },
            "first_value": numeric_values[0],
            "last_value": numeric_values[-1],
            "change": numeric_values[-1] - numeric_values[0]
        }
    
    def _advanced_analysis(self, values: List[Dict]) -> Dict[str, Any]:
        """Analyse statistique avancée."""
        import statistics
        
        numeric_values = [float(v['value']) for v in values]
        
        # Calcul de la médiane et écart-type
        median = statistics.median(numeric_values)
        std_dev = statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0
        
        # Détection des valeurs aberrantes (plus de 2 écarts-types)
        mean = statistics.mean(numeric_values)
        outliers = [v for v in numeric_values if abs(v - mean) > 2 * std_dev]
        
        return {
            "statistics": {
                "min": min(numeric_values),
                "max": max(numeric_values),
                "avg": mean,
                "median": median,
                "std_dev": std_dev,
                "count": len(numeric_values)
            },
            "outliers": {
                "count": len(outliers),
                "values": outliers[:10]  # Limiter à 10 valeurs
            },
            "percentiles": {
                "p25": statistics.quantiles(numeric_values, n=4)[0] if len(numeric_values) > 1 else numeric_values[0],
                "p50": median,
                "p75": statistics.quantiles(numeric_values, n=4)[2] if len(numeric_values) > 1 else numeric_values[0],
                "p95": statistics.quantiles(numeric_values, n=20)[18] if len(numeric_values) > 1 else numeric_values[0]
            }
        }
    
    def _trend_analysis(self, values: List[Dict]) -> Dict[str, Any]:
        """Analyse de tendance."""
        if len(values) < 2:
            return {"trend": "insufficient_data"}
        
        numeric_values = [float(v['value']) for v in values]
        
        # Calculer la tendance linéaire simple
        n = len(numeric_values)
        x_values = list(range(n))
        
        # Régression linéaire simple
        sum_x = sum(x_values)
        sum_y = sum(numeric_values)
        sum_xy = sum(x * y for x, y in zip(x_values, numeric_values))
        sum_x_squared = sum(x * x for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x_squared - sum_x * sum_x)
        intercept = (sum_y - slope * sum_x) / n
        
        # Déterminer la direction de la tendance
        if abs(slope) < 0.001:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "increasing"
        else:
            trend_direction = "decreasing"
        
        return {
            "trend": {
                "direction": trend_direction,
                "slope": slope,
                "intercept": intercept,
                "strength": abs(slope)
            },
            "prediction": {
                "next_value": slope * n + intercept,
                "confidence": "low" if abs(slope) < 0.1 else "medium" if abs(slope) < 1.0 else "high"
            }
        }


class CleanupMetricsUseCase:
    """
    Use case pour le nettoyage des anciennes données de métriques.
    
    Supprime les données obsolètes selon les politiques de rétention
    configurées.
    """
    
    def __init__(
        self,
        metric_value_repository: MetricValueRepository,
        metrics_definition_repository: MetricsDefinitionRepository
    ):
        self.metric_value_repository = metric_value_repository
        self.metrics_definition_repository = metrics_definition_repository
    
    def execute(self, retention_days: int = 30) -> Dict[str, Any]:
        """
        Exécute le nettoyage des anciennes données.
        
        Args:
            retention_days: Nombre de jours de rétention
            
        Returns:
            Résultat du nettoyage
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            # Compter les enregistrements à supprimer
            count_to_delete = self.metric_value_repository.count_before_date(cutoff_date)
            
            if count_to_delete == 0:
                return {
                    "success": True,
                    "message": "Aucune donnée ancienne trouvée",
                    "deleted_count": 0,
                    "cutoff_date": cutoff_date.isoformat(),
                    "timestamp": datetime.now().isoformat()
                }
            
            # Supprimer les anciennes données
            deleted_count = self.metric_value_repository.delete_before_date(cutoff_date)
            
            return {
                "success": True,
                "message": f"Nettoyage terminé: {deleted_count} enregistrements supprimés",
                "deleted_count": deleted_count,
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": retention_days,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des données: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class MetricsDefinitionUseCase:
    """Cas d'utilisation pour la gestion des définitions de métriques."""

    def __init__(self, metrics_definition_repository):
        self.metrics_definition_repository = metrics_definition_repository

    def list_metrics_definitions(self, filters=None):
        """Liste toutes les définitions de métriques avec filtres optionnels."""
        if filters is None:
            filters = {}

        if 'category' in filters:
            return self.metrics_definition_repository().get_by_category(filters['category'])
        elif 'collection_method' in filters:
            return self.metrics_definition_repository().get_by_collection_method(filters['collection_method'])
        else:
            return self.metrics_definition_repository().list_all()

    def get_metrics_definition(self, metrics_definition_id: int):
        """Récupère une définition de métrique par son ID."""
        definition = self.metrics_definition_repository().get_by_id(metrics_definition_id)
        if not definition:
            raise ValueError(f"Définition de métrique {metrics_definition_id} non trouvée")
        return definition

    def create_metrics_definition(self, name: str, description: str, metric_type: str,
                                unit: str, collection_method: str, collection_config: dict,
                                category: str = None):
        """Crée une nouvelle définition de métrique."""
        data = {
            'name': name,
            'description': description,
            'metric_type': metric_type,
            'unit': unit,
            'collection_method': collection_method,
            'collection_config': collection_config,
            'category': category
        }
        return self.metrics_definition_repository().create(data)

    def update_metrics_definition(self, metrics_definition_id: int, **kwargs):
        """Met à jour une définition de métrique."""
        definition = self.metrics_definition_repository().update(metrics_definition_id, kwargs)
        if not definition:
            raise ValueError(f"Définition de métrique {metrics_definition_id} non trouvée")
        return definition

    def delete_metrics_definition(self, metrics_definition_id: int):
        """Supprime une définition de métrique."""
        return self.metrics_definition_repository().delete(metrics_definition_id)


class DeviceMetricUseCase:
    """Cas d'utilisation pour la gestion des métriques d'équipement."""

    def __init__(self, device_metric_repository, metrics_definition_repository):
        self.device_metric_repository = device_metric_repository
        self.metrics_definition_repository = metrics_definition_repository

    def list_device_metrics(self, device_id: int = None):
        """Liste les métriques d'équipement."""
        if device_id:
            return self.device_metric_repository().list_by_device(device_id)
        else:
            return self.device_metric_repository().list_all()

    def get_device_metric(self, device_metric_id: int):
        """Récupère une métrique d'équipement par son ID."""
        metric = self.device_metric_repository().get_by_id(device_metric_id)
        if not metric:
            raise ValueError(f"Métrique d'équipement {device_metric_id} non trouvée")
        return metric

    def create_device_metric(self, device_id: int, metric_id: int, name: str = None,
                           specific_config: dict = None, is_active: bool = True):
        """Crée une nouvelle métrique d'équipement."""
        data = {
            'device_id': device_id,
            'metric_id': metric_id,
            'name': name,
            'specific_config': specific_config or {},
            'is_active': is_active
        }
        return self.device_metric_repository().create(data)

    def update_device_metric(self, device_metric_id: int, **kwargs):
        """Met à jour une métrique d'équipement."""
        metric = self.device_metric_repository().update(device_metric_id, kwargs)
        if not metric:
            raise ValueError(f"Métrique d'équipement {device_metric_id} non trouvée")
        return metric

    def delete_device_metric(self, device_metric_id: int):
        """Supprime une métrique d'équipement."""
        metric = self.device_metric_repository().get_by_id(device_metric_id)
        if not metric:
            raise ValueError(f"Métrique d'équipement {device_metric_id} non trouvée")
        # TODO: Implémenter la suppression dans le repository
        return True


class MetricValueUseCase:
    """Cas d'utilisation pour la gestion des valeurs de métriques."""

    def __init__(self, metric_value_repository, device_metric_repository,
                 anomaly_detection_service, alerting_service):
        self.metric_value_repository = metric_value_repository
        self.device_metric_repository = device_metric_repository
        self.anomaly_detection_service = anomaly_detection_service
        self.alerting_service = alerting_service

    def get_metric_values(self, device_metric_id: int, start_time=None, end_time=None,
                         limit=None, aggregation=None, interval=None):
        """Récupère les valeurs de métriques."""
        # Vérifier que la métrique existe
        metric = self.device_metric_repository.get_by_id(device_metric_id)
        if not metric:
            raise ValueError(f"Métrique d'équipement {device_metric_id} non trouvée")

        # Construire la plage de temps
        time_range = {}
        if start_time:
            time_range['start'] = start_time
        if end_time:
            time_range['end'] = end_time

        # Récupérer les valeurs
        if time_range:
            return self.metric_value_repository.get_values(device_metric_id, time_range, aggregation)
        else:
            # TODO: Implémenter une méthode pour récupérer les dernières valeurs
            return []

    def get_latest_value(self, device_metric_id: int):
        """Récupère la dernière valeur d'une métrique."""
        # TODO: Implémenter dans le repository
        return None

    def create_metric_value(self, device_metric_id: int, value: float, timestamp=None):
        """Crée une nouvelle valeur de métrique."""
        if timestamp is None:
            timestamp = datetime.now()

        data = {
            'device_metric_id': device_metric_id,
            'value': value,
            'timestamp': timestamp
        }
        return self.metric_value_repository.create(data)

    def batch_create_metric_values(self, metric_values_data):
        """Crée plusieurs valeurs de métrique en lot."""
        return self.metric_value_repository.create_batch(metric_values_data)