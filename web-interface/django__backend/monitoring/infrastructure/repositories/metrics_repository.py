"""
Implémentation concrète des repositories pour les métriques.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone, timedelta

from django.db.models import Q, Avg, Max, Min, Count

from ...domain.interfaces.repositories import (
    DeviceMetricRepository as IDeviceMetricRepository,
    MetricValueRepository as IMetricValueRepository,
    MetricsDefinitionRepository as IMetricsDefinitionRepository
)
from ...models import MetricsDefinition, DeviceMetric, MetricValue, MetricThreshold
from .base_repository import BaseRepository

# Configuration du logger
logger = logging.getLogger(__name__)


class MetricsDefinitionRepository(BaseRepository[MetricsDefinition], IMetricsDefinitionRepository):
    """
    Repository pour les définitions de métriques.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle MetricsDefinition.
        """
        super().__init__(MetricsDefinition)
    
    def create_metrics_definition(self, name: str, description: str, 
                                 metric_type: str, unit: str,
                                 collection_method: str,
                                 collection_config: Dict[str, Any] = None,
                                 category: str = None) -> MetricsDefinition:
        """
        Crée une nouvelle définition de métrique.
        
        Args:
            name: Nom de la métrique
            description: Description de la métrique
            metric_type: Type de métrique ('gauge', 'counter', 'derive', etc.)
            unit: Unité de mesure ('bytes', 'seconds', 'percent', etc.)
            collection_method: Méthode de collecte ('snmp', 'api', 'agent', etc.)
            collection_config: Configuration spécifique pour la collecte (optionnel)
            category: Catégorie de la métrique (optionnel)
            
        Returns:
            La définition de métrique créée
        """
        try:
            metric = MetricsDefinition(
                name=name,
                description=description,
                metric_type=metric_type,
                unit=unit,
                collection_method=collection_method,
                collection_config=collection_config or {},
                category=category
            )
            
            metric.save()
            logger.info(f"Définition de métrique créée: {metric.id} - {name}")
            return metric
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une définition de métrique: {e}")
            raise
    
    def get_by_collection_method(self, collection_method: str) -> List[Dict[str, Any]]:
        """
        Récupère les définitions de métriques par méthode de collecte.

        Args:
            collection_method: Méthode de collecte à filtrer

        Returns:
            Liste des définitions de métriques
        """
        metrics = self.filter(collection_method=collection_method)
        return [
            {
                'id': metric.id,
                'name': metric.name,
                'description': metric.description,
                'metric_type': metric.metric_type,
                'unit': metric.unit,
                'collection_method': metric.collection_method,
                'collection_config': metric.collection_config,
                'category': metric.category,
                'created_at': metric.created_at.isoformat() if metric.created_at else None,
                'updated_at': metric.updated_at.isoformat() if metric.updated_at else None,
            }
            for metric in metrics
        ]

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Récupère les définitions de métriques par catégorie.

        Args:
            category: Catégorie à filtrer

        Returns:
            Liste des définitions de métriques
        """
        metrics = self.filter(category=category)
        return [
            {
                'id': metric.id,
                'name': metric.name,
                'description': metric.description,
                'metric_type': metric.metric_type,
                'unit': metric.unit,
                'collection_method': metric.collection_method,
                'collection_config': metric.collection_config,
                'category': metric.category,
                'created_at': metric.created_at.isoformat() if metric.created_at else None,
                'updated_at': metric.updated_at.isoformat() if metric.updated_at else None,
            }
            for metric in metrics
        ]
    
    def add_threshold(self, metric_id: int, threshold_type: str, 
                     warning_value: float = None, critical_value: float = None,
                     comparison: str = "gt") -> Optional[MetricThreshold]:
        """
        Ajoute un seuil à une définition de métrique.
        
        Args:
            metric_id: ID de la définition de métrique
            threshold_type: Type de seuil ('static', 'dynamic', 'baseline')
            warning_value: Valeur d'avertissement (optionnel)
            critical_value: Valeur critique (optionnel)
            comparison: Type de comparaison ('gt', 'lt', 'eq', 'ne', 'ge', 'le')
            
        Returns:
            Le seuil créé ou None si la métrique n'existe pas
        """
        metric = self.get_by_id(metric_id)
        if not metric:
            return None
        
        try:
            threshold = MetricThreshold(
                metrics_definition=metric,
                threshold_type=threshold_type,
                warning_value=warning_value,
                critical_value=critical_value,
                comparison=comparison
            )
            
            threshold.save()
            logger.info(f"Seuil ajouté à la métrique {metric_id}")
            return threshold
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout d'un seuil à la métrique {metric_id}: {e}")
            raise
    
    def get_thresholds(self, metric_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les seuils pour une définition de métrique.

        Args:
            metric_id: ID de la définition de métrique

        Returns:
            Liste des seuils
        """
        thresholds = MetricThreshold.objects.filter(metrics_definition_id=metric_id)
        return [
            {
                'id': threshold.id,
                'threshold_type': threshold.threshold_type,
                'warning_value': threshold.warning_value,
                'critical_value': threshold.critical_value,
                'comparison': threshold.comparison,
                'created_at': threshold.created_at.isoformat() if threshold.created_at else None,
                'updated_at': threshold.updated_at.isoformat() if threshold.updated_at else None,
            }
            for threshold in thresholds
        ]
    
    def update_collection_config(self, metric_id: int, 
                                collection_config: Dict[str, Any]) -> Optional[MetricsDefinition]:
        """
        Met à jour la configuration de collecte d'une définition de métrique.
        
        Args:
            metric_id: ID de la définition de métrique
            collection_config: Nouvelle configuration de collecte
            
        Returns:
            La définition de métrique mise à jour ou None si elle n'existe pas
        """
        metric = self.get_by_id(metric_id)
        if not metric:
            return None
        
        try:
            # Fusionner avec la configuration existante
            if metric.collection_config:
                metric.collection_config.update(collection_config)
            else:
                metric.collection_config = collection_config
                
            metric.save()
            logger.info(f"Configuration de collecte mise à jour pour la métrique {metric_id}")
            return metric
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la configuration de collecte pour la métrique {metric_id}: {e}")
            raise

    # Implémentation des méthodes abstraites de l'interface
    def get_by_id(self, metrics_definition_id: int) -> Optional[Dict[str, Any]]:
        """Récupère une définition de métrique par son ID."""
        try:
            metric = MetricsDefinition.objects.get(id=metrics_definition_id)
            return {
                'id': metric.id,
                'name': metric.name,
                'description': metric.description,
                'metric_type': metric.metric_type,
                'unit': metric.unit,
                'collection_method': metric.collection_method,
                'collection_config': metric.collection_config,
                'category': metric.category,
                'created_at': metric.created_at.isoformat() if metric.created_at else None,
                'updated_at': metric.updated_at.isoformat() if metric.updated_at else None,
            }
        except MetricsDefinition.DoesNotExist:
            return None

    def list_all(self) -> List[Dict[str, Any]]:
        """Liste toutes les définitions de métriques."""
        metrics = MetricsDefinition.objects.all()
        return [
            {
                'id': metric.id,
                'name': metric.name,
                'description': metric.description,
                'metric_type': metric.metric_type,
                'unit': metric.unit,
                'collection_method': metric.collection_method,
                'collection_config': metric.collection_config,
                'category': metric.category,
                'created_at': metric.created_at.isoformat() if metric.created_at else None,
                'updated_at': metric.updated_at.isoformat() if metric.updated_at else None,
            }
            for metric in metrics
        ]

    def create(self, metrics_definition_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle définition de métrique."""
        metric = self.create_metrics_definition(
            name=metrics_definition_data['name'],
            description=metrics_definition_data['description'],
            metric_type=metrics_definition_data['metric_type'],
            unit=metrics_definition_data['unit'],
            collection_method=metrics_definition_data['collection_method'],
            collection_config=metrics_definition_data.get('collection_config'),
            category=metrics_definition_data.get('category')
        )
        return {
            'id': metric.id,
            'name': metric.name,
            'description': metric.description,
            'metric_type': metric.metric_type,
            'unit': metric.unit,
            'collection_method': metric.collection_method,
            'collection_config': metric.collection_config,
            'category': metric.category,
            'created_at': metric.created_at.isoformat() if metric.created_at else None,
            'updated_at': metric.updated_at.isoformat() if metric.updated_at else None,
        }

    def update(self, metrics_definition_id: int, metrics_definition_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Met à jour une définition de métrique."""
        try:
            metric = MetricsDefinition.objects.get(id=metrics_definition_id)
            for key, value in metrics_definition_data.items():
                if hasattr(metric, key):
                    setattr(metric, key, value)
            metric.save()
            return {
                'id': metric.id,
                'name': metric.name,
                'description': metric.description,
                'metric_type': metric.metric_type,
                'unit': metric.unit,
                'collection_method': metric.collection_method,
                'collection_config': metric.collection_config,
                'category': metric.category,
                'created_at': metric.created_at.isoformat() if metric.created_at else None,
                'updated_at': metric.updated_at.isoformat() if metric.updated_at else None,
            }
        except MetricsDefinition.DoesNotExist:
            return None

    def delete(self, metrics_definition_id: int) -> bool:
        """Supprime une définition de métrique."""
        try:
            metric = MetricsDefinition.objects.get(id=metrics_definition_id)
            metric.delete()
            return True
        except MetricsDefinition.DoesNotExist:
            return False


class DeviceMetricRepository(BaseRepository[DeviceMetric], IDeviceMetricRepository):
    """
    Repository pour les métriques d'équipement.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle DeviceMetric.
        """
        super().__init__(DeviceMetric)
    
    def create_device_metric(self, device_id: int, metric_id: int, 
                            name: Optional[str] = None,
                            specific_config: Dict[str, Any] = None,
                            is_active: bool = True) -> DeviceMetric:
        """
        Crée une nouvelle métrique d'équipement.
        
        Args:
            device_id: ID de l'équipement
            metric_id: ID de la définition de métrique
            name: Nom personnalisé pour cette instance (optionnel)
            specific_config: Configuration spécifique pour cette instance (optionnel)
            is_active: Si la métrique est active
            
        Returns:
            La métrique d'équipement créée
        """
        try:
            # Si aucun nom n'est fourni, utiliser le nom de la définition de métrique
            if not name:
                metric_def = MetricsDefinition.objects.get(id=metric_id)
                name = metric_def.name
                
            device_metric = DeviceMetric(
                device_id=device_id,
                metric_id=metric_id,
                name=name,
                specific_config=specific_config or {},
                is_active=is_active
            )
            
            device_metric.save()
            logger.info(f"Métrique d'équipement créée: {device_metric.id} - {name} pour l'équipement {device_id}")
            return device_metric
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une métrique d'équipement: {e}")
            raise
    
    def get_by_device(self, device_id: int, active_only: bool = True) -> List[DeviceMetric]:
        """
        Récupère les métriques pour un équipement donné.
        
        Args:
            device_id: ID de l'équipement
            active_only: Si on ne récupère que les métriques actives
            
        Returns:
            Liste des métriques d'équipement
        """
        query = Q(device_id=device_id)
        
        if active_only:
            query &= Q(is_active=True)
            
        return list(DeviceMetric.objects.filter(query))
    
    def get_by_metric_type(self, metric_type: str, active_only: bool = True) -> List[DeviceMetric]:
        """
        Récupère les métriques d'équipement par type de métrique.
        
        Args:
            metric_type: Type de métrique à filtrer
            active_only: Si on ne récupère que les métriques actives
            
        Returns:
            Liste des métriques d'équipement
        """
        query = Q(metric__metric_type=metric_type)
        
        if active_only:
            query &= Q(is_active=True)
            
        return list(DeviceMetric.objects.filter(query))
    
    def update_collection_status(self, device_metric_id: int, 
                                success: bool, 
                                last_value: Optional[float] = None,
                                message: Optional[str] = None) -> Optional[DeviceMetric]:
        """
        Met à jour le statut de collecte d'une métrique d'équipement.
        
        Args:
            device_metric_id: ID de la métrique d'équipement
            success: Si la collecte a réussi
            last_value: Dernière valeur collectée (optionnel)
            message: Message associé à la collecte (optionnel)
            
        Returns:
            La métrique d'équipement mise à jour ou None si elle n'existe pas
        """
        device_metric = self.get_by_id(device_metric_id)
        if not device_metric:
            return None
        
        try:
            device_metric.last_collection = datetime.now(timezone.utc)
            device_metric.last_collection_success = success
            
            if last_value is not None:
                device_metric.last_value = last_value
                
            if message:
                device_metric.last_collection_message = message
                
            device_metric.save()
            logger.info(f"Statut de collecte mis à jour pour la métrique d'équipement {device_metric_id}")
            return device_metric
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut de collecte pour la métrique d'équipement {device_metric_id}: {e}")
            raise
    
    def get_metrics_to_collect(self, limit: int = 100) -> List[DeviceMetric]:
        """
        Récupère les métriques d'équipement à collecter.
        
        Args:
            limit: Nombre maximum de métriques à récupérer
            
        Returns:
            Liste des métriques d'équipement à collecter
        """
        # Récupérer les métriques actives qui n'ont jamais été collectées
        # ou qui n'ont pas été collectées depuis longtemps
        from django.db.models import Q
        from datetime import timedelta
        
        never_collected = Q(last_collection__isnull=True)
        
        # Collecter les métriques qui n'ont pas été collectées depuis plus de 5 minutes
        collection_due = Q(last_collection__lt=datetime.now(timezone.utc) - timedelta(minutes=5))
        
        query = Q(is_active=True) & (never_collected | collection_due)
        
        return list(DeviceMetric.objects.filter(query).order_by('last_collection')[:limit])

    # Implémentation des méthodes abstraites de l'interface IDeviceMetricRepository
    def get_by_id(self, device_metric_id: int) -> Optional[Dict[str, Any]]:
        """Récupère une métrique d'équipement par son ID."""
        try:
            device_metric = DeviceMetric.objects.get(id=device_metric_id)
            return {
                'id': device_metric.id,
                'device_id': device_metric.device_id,
                'metric_id': device_metric.metric_id,
                'name': device_metric.name,
                'specific_config': device_metric.specific_config,
                'is_active': device_metric.is_active,
                'last_collection': device_metric.last_collection.isoformat() if device_metric.last_collection else None,
                'last_collection_success': device_metric.last_collection_success,
                'last_value': device_metric.last_value,
                'last_collection_message': device_metric.last_collection_message,
                'created_at': device_metric.created_at.isoformat() if device_metric.created_at else None,
                'updated_at': device_metric.updated_at.isoformat() if device_metric.updated_at else None,
            }
        except DeviceMetric.DoesNotExist:
            return None

    def list_by_device(self, device_id: int) -> List[Dict[str, Any]]:
        """Liste les métriques pour un équipement."""
        device_metrics = self.get_by_device(device_id, active_only=False)
        return [
            {
                'id': device_metric.id,
                'device_id': device_metric.device_id,
                'metric_id': device_metric.metric_id,
                'name': device_metric.name,
                'specific_config': device_metric.specific_config,
                'is_active': device_metric.is_active,
                'last_collection': device_metric.last_collection.isoformat() if device_metric.last_collection else None,
                'last_collection_success': device_metric.last_collection_success,
                'last_value': device_metric.last_value,
                'last_collection_message': device_metric.last_collection_message,
                'created_at': device_metric.created_at.isoformat() if device_metric.created_at else None,
                'updated_at': device_metric.updated_at.isoformat() if device_metric.updated_at else None,
            }
            for device_metric in device_metrics
        ]

    def create(self, device_metric_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crée une nouvelle métrique d'équipement."""
        device_metric = self.create_device_metric(
            device_id=device_metric_data['device_id'],
            metric_id=device_metric_data['metric_id'],
            name=device_metric_data.get('name'),
            specific_config=device_metric_data.get('specific_config'),
            is_active=device_metric_data.get('is_active', True)
        )
        return {
            'id': device_metric.id,
            'device_id': device_metric.device_id,
            'metric_id': device_metric.metric_id,
            'name': device_metric.name,
            'specific_config': device_metric.specific_config,
            'is_active': device_metric.is_active,
            'last_collection': device_metric.last_collection.isoformat() if device_metric.last_collection else None,
            'last_collection_success': device_metric.last_collection_success,
            'last_value': device_metric.last_value,
            'last_collection_message': device_metric.last_collection_message,
            'created_at': device_metric.created_at.isoformat() if device_metric.created_at else None,
            'updated_at': device_metric.updated_at.isoformat() if device_metric.updated_at else None,
        }

    def update(self, device_metric_id: int, device_metric_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Met à jour une métrique d'équipement."""
        try:
            device_metric = DeviceMetric.objects.get(id=device_metric_id)
            for key, value in device_metric_data.items():
                if hasattr(device_metric, key):
                    setattr(device_metric, key, value)
            device_metric.save()
            return {
                'id': device_metric.id,
                'device_id': device_metric.device_id,
                'metric_id': device_metric.metric_id,
                'name': device_metric.name,
                'specific_config': device_metric.specific_config,
                'is_active': device_metric.is_active,
                'last_collection': device_metric.last_collection.isoformat() if device_metric.last_collection else None,
                'last_collection_success': device_metric.last_collection_success,
                'last_value': device_metric.last_value,
                'last_collection_message': device_metric.last_collection_message,
                'created_at': device_metric.created_at.isoformat() if device_metric.created_at else None,
                'updated_at': device_metric.updated_at.isoformat() if device_metric.updated_at else None,
            }
        except DeviceMetric.DoesNotExist:
            return None

    def list_all(self) -> List[Dict[str, Any]]:
        """Liste toutes les métriques d'équipements."""
        device_metrics = DeviceMetric.objects.all()
        return [
            {
                'id': device_metric.id,
                'device_id': device_metric.device_id,
                'metric_id': device_metric.metric_id,
                'name': device_metric.name,
                'specific_config': device_metric.specific_config,
                'is_active': device_metric.is_active,
                'last_collection': device_metric.last_collection.isoformat() if device_metric.last_collection else None,
                'last_collection_success': device_metric.last_collection_success,
                'last_value': device_metric.last_value,
                'last_collection_message': device_metric.last_collection_message,
                'created_at': device_metric.created_at.isoformat() if device_metric.created_at else None,
                'updated_at': device_metric.updated_at.isoformat() if device_metric.updated_at else None,
            }
            for device_metric in device_metrics
        ]


class MetricValueRepository(BaseRepository[MetricValue], IMetricValueRepository):
    """
    Repository pour les valeurs de métriques.
    """
    
    def __init__(self):
        """
        Initialise le repository avec le modèle MetricValue.
        """
        super().__init__(MetricValue)
    
    def create_metric_value(self, device_metric_id: int, value: float, 
                           timestamp: Optional[datetime] = None) -> MetricValue:
        """
        Crée une nouvelle valeur de métrique.
        
        Args:
            device_metric_id: ID de la métrique d'équipement
            value: Valeur de la métrique
            timestamp: Horodatage de la valeur (optionnel, utilise l'heure actuelle par défaut)
            
        Returns:
            La valeur de métrique créée
        """
        try:
            if timestamp is None:
                timestamp = datetime.now(timezone.utc)
                
            metric_value = MetricValue(
                device_metric_id=device_metric_id,
                value=value,
                timestamp=timestamp
            )
            
            metric_value.save()
            return metric_value
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une valeur de métrique: {e}")
            raise
    
    def batch_create(self, values: List[Dict[str, Any]]) -> List[MetricValue]:
        """
        Crée plusieurs valeurs de métriques en une seule opération.
        
        Args:
            values: Liste de dictionnaires contenant les valeurs à créer
            
        Returns:
            Liste des valeurs de métriques créées
        """
        try:
            metric_values = []
            
            for value_data in values:
                device_metric_id = value_data.get('device_metric_id')
                value = value_data.get('value')
                timestamp = value_data.get('timestamp')
                
                if device_metric_id is None or value is None:
                    continue
                    
                if timestamp is None:
                    timestamp = datetime.now(timezone.utc)
                elif isinstance(timestamp, str):
                    try:
                        timestamp = datetime.fromisoformat(timestamp)
                    except ValueError:
                        timestamp = datetime.now(timezone.utc)
                
                metric_value = MetricValue(
                    device_metric_id=device_metric_id,
                    value=value,
                    timestamp=timestamp
                )
                
                metric_values.append(metric_value)
            
            # Créer les objets en masse
            if metric_values:
                MetricValue.objects.bulk_create(metric_values)
                
            return metric_values
        except Exception as e:
            logger.error(f"Erreur lors de la création en masse de valeurs de métriques: {e}")
            raise
    
    def get_values_for_device_metric(self, device_metric_id: int, 
                                   start_time: Optional[datetime] = None,
                                   end_time: Optional[datetime] = None,
                                   limit: int = 1000) -> List[MetricValue]:
        """
        Récupère les valeurs pour une métrique d'équipement.
        
        Args:
            device_metric_id: ID de la métrique d'équipement
            start_time: Heure de début (optionnel)
            end_time: Heure de fin (optionnel)
            limit: Nombre maximum de valeurs à récupérer
            
        Returns:
            Liste des valeurs de métriques
        """
        query = Q(device_metric_id=device_metric_id)
        
        if start_time:
            query &= Q(timestamp__gte=start_time)
            
        if end_time:
            query &= Q(timestamp__lte=end_time)
            
        return list(MetricValue.objects.filter(query).order_by('-timestamp')[:limit])
    
    def get_latest_value(self, device_metric_id: int) -> Optional[MetricValue]:
        """
        Récupère la dernière valeur pour une métrique d'équipement.
        
        Args:
            device_metric_id: ID de la métrique d'équipement
            
        Returns:
            La dernière valeur ou None si aucune valeur n'existe
        """
        try:
            return MetricValue.objects.filter(device_metric_id=device_metric_id).latest('timestamp')
        except MetricValue.DoesNotExist:
            return None
    
    def get_aggregated_values(self, device_metric_id: int, 
                             start_time: datetime, end_time: datetime,
                             aggregation: str = 'avg') -> Dict[str, Any]:
        """
        Récupère des valeurs agrégées pour une métrique d'équipement.
        
        Args:
            device_metric_id: ID de la métrique d'équipement
            start_time: Heure de début
            end_time: Heure de fin
            aggregation: Type d'agrégation ('avg', 'min', 'max', 'count')
            
        Returns:
            Dictionnaire contenant les valeurs agrégées
        """
        query = Q(device_metric_id=device_metric_id) & Q(timestamp__gte=start_time) & Q(timestamp__lte=end_time)
        
        values = MetricValue.objects.filter(query)
        
        result = {}
        
        if aggregation == 'avg' or aggregation == 'all':
            result['avg'] = values.aggregate(avg_value=Avg('value'))['avg_value']
            
        if aggregation == 'min' or aggregation == 'all':
            result['min'] = values.aggregate(min_value=Min('value'))['min_value']
            
        if aggregation == 'max' or aggregation == 'all':
            result['max'] = values.aggregate(max_value=Max('value'))['max_value']
            
        if aggregation == 'count' or aggregation == 'all':
            result['count'] = values.count()
            
        return result
    
    def clean_old_values(self, device_metric_id: int, 
                        retention_days: int = 30) -> int:
        """
        Supprime les anciennes valeurs pour une métrique d'équipement.
        
        Args:
            device_metric_id: ID de la métrique d'équipement
            retention_days: Nombre de jours de rétention
            
        Returns:
            Nombre de valeurs supprimées
        """
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
            
            # Compter les valeurs à supprimer
            count = MetricValue.objects.filter(
                device_metric_id=device_metric_id,
                timestamp__lt=cutoff_date
            ).count()
            
            # Supprimer les valeurs
            MetricValue.objects.filter(
                device_metric_id=device_metric_id,
                timestamp__lt=cutoff_date
            ).delete()
            
            logger.info(f"Suppression de {count} anciennes valeurs pour la métrique d'équipement {device_metric_id}")
            return count
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des anciennes valeurs pour la métrique d'équipement {device_metric_id}: {e}")
            raise

    # Implémentation des méthodes abstraites de l'interface IMetricValueRepository
    def create(self, metric_value_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle valeur de métrique.
        
        Args:
            metric_value_data: Données de la valeur
            
        Returns:
            La valeur créée
        """
        try:
            device_metric_id = metric_value_data.get('device_metric_id')
            value = metric_value_data.get('value')
            timestamp = metric_value_data.get('timestamp')
            
            if device_metric_id is None or value is None:
                raise ValueError("device_metric_id et value sont requis")
            
            if timestamp and isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except ValueError:
                    timestamp = None
            
            metric_value = self.create_metric_value(
                device_metric_id=device_metric_id,
                value=value,
                timestamp=timestamp
            )
            
            return {
                'id': metric_value.id,
                'device_metric_id': metric_value.device_metric_id,
                'value': metric_value.value,
                'timestamp': metric_value.timestamp.isoformat() if metric_value.timestamp else None,
                'created_at': metric_value.created_at.isoformat() if hasattr(metric_value, 'created_at') and metric_value.created_at else None,
            }
        except Exception as e:
            logger.error(f"Erreur lors de la création d'une valeur de métrique: {e}")
            raise

    def create_batch(self, metric_values: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Crée un lot de valeurs de métriques.
        
        Args:
            metric_values: Liste des données de valeurs
            
        Returns:
            Liste des valeurs créées
        """
        try:
            created_values = self.batch_create(metric_values)
            
            return [
                {
                    'id': value.id,
                    'device_metric_id': value.device_metric_id,
                    'value': value.value,
                    'timestamp': value.timestamp.isoformat() if value.timestamp else None,
                    'created_at': value.created_at.isoformat() if hasattr(value, 'created_at') and value.created_at else None,
                }
                for value in created_values
            ]
        except Exception as e:
            logger.error(f"Erreur lors de la création en lot de valeurs de métriques: {e}")
            raise

    def get_values(self, device_metric_id: int, time_range: Dict[str, datetime],
                  aggregation: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les valeurs pour une métrique d'équipement sur une période donnée.

        Args:
            device_metric_id: ID de la métrique d'équipement
            time_range: Plage de temps (start et end)
            aggregation: Méthode d'agrégation optionnelle

        Returns:
            Liste des valeurs
        """
        try:
            start_time = time_range.get('start')
            end_time = time_range.get('end')
            
            if aggregation:
                # Si une agrégation est demandée, utiliser la méthode d'agrégation
                return [self.get_aggregated_values(device_metric_id, start_time, end_time, aggregation)]
            else:
                # Sinon, retourner les valeurs brutes
                values = self.get_values_for_device_metric(
                    device_metric_id=device_metric_id,
                    start_time=start_time,
                    end_time=end_time
                )
                
                return [
                    {
                        'id': value.id,
                        'device_metric_id': value.device_metric_id,
                        'value': value.value,
                        'timestamp': value.timestamp.isoformat() if value.timestamp else None,
                    }
                    for value in values
                ]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des valeurs pour la métrique d'équipement {device_metric_id}: {e}")
            raise

    def save(self, metric_value_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sauvegarde une valeur de métrique (alias pour create).

        Args:
            metric_value_data: Données de la valeur

        Returns:
            La valeur sauvegardée
        """
        return self.create(metric_value_data)

    def get_values_by_period(self, metric_id: int, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Récupère les valeurs pour une métrique sur une période.

        Args:
            metric_id: ID de la métrique
            start_time: Début de la période
            end_time: Fin de la période

        Returns:
            Liste des valeurs
        """
        try:
            values = self.get_values_for_device_metric(
                device_metric_id=metric_id,
                start_time=start_time,
                end_time=end_time
            )
            
            return [
                {
                    'id': value.id,
                    'device_metric_id': value.device_metric_id,
                    'value': value.value,
                    'timestamp': value.timestamp.isoformat() if value.timestamp else None,
                }
                for value in values
            ]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des valeurs pour la métrique {metric_id}: {e}")
            raise

    def count_before_date(self, cutoff_date: datetime) -> int:
        """
        Compte les valeurs avant une date donnée.

        Args:
            cutoff_date: Date limite

        Returns:
            Nombre de valeurs
        """
        try:
            return MetricValue.objects.filter(timestamp__lt=cutoff_date).count()
        except Exception as e:
            logger.error(f"Erreur lors du comptage des valeurs avant {cutoff_date}: {e}")
            raise

    def delete_before_date(self, cutoff_date: datetime) -> int:
        """
        Supprime les valeurs avant une date donnée.

        Args:
            cutoff_date: Date limite

        Returns:
            Nombre de valeurs supprimées
        """
        try:
            # Compter les valeurs à supprimer
            count = MetricValue.objects.filter(timestamp__lt=cutoff_date).count()
            
            # Supprimer les valeurs
            MetricValue.objects.filter(timestamp__lt=cutoff_date).delete()
            
            logger.info(f"Suppression de {count} valeurs avant {cutoff_date}")
            return count
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des valeurs avant {cutoff_date}: {e}")
            raise