"""
Collecteur de métriques avancé pour le module dashboard.

Ce module implémente un système de collecte de métriques en temps réel
avec seuils configurables et alertes automatiques.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction

from ..domain.entities import AlertSeverity, DeviceStatus

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types de métriques supportées."""
    SYSTEM_HEALTH = 'system_health'
    NETWORK_HEALTH = 'network_health'
    SECURITY_HEALTH = 'security_health'
    DEVICE_CPU = 'device_cpu'
    DEVICE_MEMORY = 'device_memory'
    DEVICE_TEMPERATURE = 'device_temperature'
    NETWORK_LATENCY = 'network_latency'
    BANDWIDTH_UTILIZATION = 'bandwidth_utilization'
    PACKET_LOSS = 'packet_loss'
    CONNECTION_COUNT = 'connection_count'
    ALERT_COUNT = 'alert_count'


class ThresholdOperator(str, Enum):
    """Opérateurs pour les seuils."""
    GREATER_THAN = 'gt'
    GREATER_EQUAL = 'gte'
    LESS_THAN = 'lt'
    LESS_EQUAL = 'lte'
    EQUAL = 'eq'
    NOT_EQUAL = 'ne'


@dataclass
class MetricThreshold:
    """Configuration d'un seuil de métrique."""
    metric_type: MetricType
    operator: ThresholdOperator
    value: float
    severity: AlertSeverity
    message_template: str
    is_active: bool = True
    device_id: Optional[int] = None
    
    def evaluate(self, metric_value: float) -> bool:
        """
        Évalue si le seuil est dépassé.
        
        Args:
            metric_value: Valeur de la métrique
            
        Returns:
            True si le seuil est dépassé
        """
        operations = {
            ThresholdOperator.GREATER_THAN: metric_value > self.value,
            ThresholdOperator.GREATER_EQUAL: metric_value >= self.value,
            ThresholdOperator.LESS_THAN: metric_value < self.value,
            ThresholdOperator.LESS_EQUAL: metric_value <= self.value,
            ThresholdOperator.EQUAL: metric_value == self.value,
            ThresholdOperator.NOT_EQUAL: metric_value != self.value,
        }
        return operations.get(self.operator, False)
    
    def format_message(self, metric_value: float, device_name: str = None) -> str:
        """
        Formate le message d'alerte.
        
        Args:
            metric_value: Valeur de la métrique
            device_name: Nom de l'équipement (optionnel)
            
        Returns:
            Message formaté
        """
        context = {
            'metric_value': metric_value,
            'threshold_value': self.value,
            'device_name': device_name or 'Unknown',
            'metric_type': self.metric_type.value
        }
        
        try:
            return self.message_template.format(**context)
        except KeyError:
            return f"Seuil dépassé pour {self.metric_type.value}: {metric_value}"


@dataclass
class MetricReading:
    """Lecture d'une métrique."""
    metric_type: MetricType
    value: float
    timestamp: datetime
    device_id: Optional[int] = None
    device_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MetricsCollector:
    """
    Collecteur de métriques en temps réel.
    
    Collecte, traite et analyse les métriques système avec
    détection automatique des anomalies et alertes.
    """
    
    def __init__(self):
        """Initialise le collecteur de métriques."""
        self.thresholds: List[MetricThreshold] = []
        self.metric_handlers: Dict[MetricType, Callable] = {}
        self.alert_callbacks: List[Callable] = []
        self.is_collecting = False
        self._setup_default_thresholds()
        self._setup_metric_handlers()
    
    def _setup_default_thresholds(self):
        """Configure les seuils par défaut."""
        default_thresholds = [
            # Santé système
            MetricThreshold(
                MetricType.SYSTEM_HEALTH,
                ThresholdOperator.LESS_THAN,
                0.5,
                AlertSeverity.CRITICAL,
                "Santé système critique: {metric_value:.1%} < {threshold_value:.1%}"
            ),
            MetricThreshold(
                MetricType.SYSTEM_HEALTH,
                ThresholdOperator.LESS_THAN,
                0.7,
                AlertSeverity.HIGH,
                "Santé système dégradée: {metric_value:.1%} < {threshold_value:.1%}"
            ),
            
            # CPU des équipements
            MetricThreshold(
                MetricType.DEVICE_CPU,
                ThresholdOperator.GREATER_THAN,
                90.0,
                AlertSeverity.CRITICAL,
                "CPU critique sur {device_name}: {metric_value:.1f}% > {threshold_value:.1f}%"
            ),
            MetricThreshold(
                MetricType.DEVICE_CPU,
                ThresholdOperator.GREATER_THAN,
                80.0,
                AlertSeverity.HIGH,
                "CPU élevé sur {device_name}: {metric_value:.1f}% > {threshold_value:.1f}%"
            ),
            
            # Mémoire des équipements
            MetricThreshold(
                MetricType.DEVICE_MEMORY,
                ThresholdOperator.GREATER_THAN,
                95.0,
                AlertSeverity.CRITICAL,
                "Mémoire critique sur {device_name}: {metric_value:.1f}% > {threshold_value:.1f}%"
            ),
            MetricThreshold(
                MetricType.DEVICE_MEMORY,
                ThresholdOperator.GREATER_THAN,
                85.0,
                AlertSeverity.HIGH,
                "Mémoire élevée sur {device_name}: {metric_value:.1f}% > {threshold_value:.1f}%"
            ),
            
            # Latence réseau
            MetricThreshold(
                MetricType.NETWORK_LATENCY,
                ThresholdOperator.GREATER_THAN,
                1000.0,
                AlertSeverity.HIGH,
                "Latence réseau élevée: {metric_value:.1f}ms > {threshold_value:.1f}ms"
            ),
            
            # Perte de paquets
            MetricThreshold(
                MetricType.PACKET_LOSS,
                ThresholdOperator.GREATER_THAN,
                5.0,
                AlertSeverity.CRITICAL,
                "Perte de paquets critique: {metric_value:.1f}% > {threshold_value:.1f}%"
            ),
            
            # Utilisation de la bande passante
            MetricThreshold(
                MetricType.BANDWIDTH_UTILIZATION,
                ThresholdOperator.GREATER_THAN,
                90.0,
                AlertSeverity.HIGH,
                "Bande passante saturée: {metric_value:.1f}% > {threshold_value:.1f}%"
            ),
        ]
        
        self.thresholds.extend(default_thresholds)
    
    def _setup_metric_handlers(self):
        """Configure les gestionnaires de métriques."""
        self.metric_handlers = {
            MetricType.SYSTEM_HEALTH: self._collect_system_health,
            MetricType.NETWORK_HEALTH: self._collect_network_health,
            MetricType.SECURITY_HEALTH: self._collect_security_health,
            MetricType.DEVICE_CPU: self._collect_device_cpu,
            MetricType.DEVICE_MEMORY: self._collect_device_memory,
            MetricType.NETWORK_LATENCY: self._collect_network_latency,
            MetricType.BANDWIDTH_UTILIZATION: self._collect_bandwidth_utilization,
            MetricType.PACKET_LOSS: self._collect_packet_loss,
        }
    
    def add_threshold(self, threshold: MetricThreshold):
        """
        Ajoute un nouveau seuil de métrique.
        
        Args:
            threshold: Configuration du seuil
        """
        self.thresholds.append(threshold)
        logger.info(f"Seuil ajouté: {threshold.metric_type.value} {threshold.operator.value} {threshold.value}")
    
    def remove_threshold(self, metric_type: MetricType, value: float, operator: ThresholdOperator):
        """
        Supprime un seuil existant.
        
        Args:
            metric_type: Type de métrique
            value: Valeur du seuil
            operator: Opérateur du seuil
        """
        self.thresholds = [
            t for t in self.thresholds 
            if not (t.metric_type == metric_type and t.value == value and t.operator == operator)
        ]
    
    def add_alert_callback(self, callback: Callable[[str, AlertSeverity, Dict[str, Any]], None]):
        """
        Ajoute un callback pour les alertes.
        
        Args:
            callback: Fonction à appeler lors d'une alerte
        """
        self.alert_callbacks.append(callback)
    
    async def start_collection(self, interval: int = 30):
        """
        Démarre la collecte de métriques en arrière-plan.
        
        Args:
            interval: Intervalle de collecte en secondes
        """
        if self.is_collecting:
            logger.warning("Collecte déjà en cours")
            return
        
        self.is_collecting = True
        logger.info(f"Démarrage de la collecte de métriques (intervalle: {interval}s)")
        
        try:
            while self.is_collecting:
                await self._collect_all_metrics()
                await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"Erreur dans la collecte de métriques: {e}")
        finally:
            self.is_collecting = False
    
    def stop_collection(self):
        """Arrête la collecte de métriques."""
        self.is_collecting = False
        logger.info("Arrêt de la collecte de métriques")
    
    async def _collect_all_metrics(self):
        """Collecte toutes les métriques configurées."""
        collected_metrics = []
        
        for metric_type, handler in self.metric_handlers.items():
            try:
                metrics = await handler()
                if isinstance(metrics, list):
                    collected_metrics.extend(metrics)
                elif metrics:
                    collected_metrics.append(metrics)
            except Exception as e:
                logger.error(f"Erreur lors de la collecte de {metric_type.value}: {e}")
        
        # Traiter les métriques collectées
        for metric in collected_metrics:
            self._process_metric(metric)
    
    def _process_metric(self, metric: MetricReading):
        """
        Traite une métrique et vérifie les seuils.
        
        Args:
            metric: Lecture de métrique à traiter
        """
        # Sauvegarder la métrique en cache
        cache_key = f"metric:{metric.metric_type.value}:{metric.device_id or 'global'}:{metric.timestamp.strftime('%Y%m%d%H%M')}"
        cache.set(cache_key, {
            'value': metric.value,
            'timestamp': metric.timestamp.isoformat(),
            'device_name': metric.device_name
        }, timeout=3600)  # 1 heure
        
        # Vérifier les seuils
        for threshold in self.thresholds:
            if not threshold.is_active or threshold.metric_type != metric.metric_type:
                continue
            
            # Filtrer par équipement si spécifié
            if threshold.device_id and threshold.device_id != metric.device_id:
                continue
            
            if threshold.evaluate(metric.value):
                self._trigger_alert(threshold, metric)
    
    def _trigger_alert(self, threshold: MetricThreshold, metric: MetricReading):
        """
        Déclenche une alerte.
        
        Args:
            threshold: Seuil dépassé
            metric: Métrique ayant déclenché l'alerte
        """
        message = threshold.format_message(metric.value, metric.device_name)
        
        alert_data = {
            'metric_type': metric.metric_type.value,
            'metric_value': metric.value,
            'threshold_value': threshold.value,
            'device_id': metric.device_id,
            'device_name': metric.device_name,
            'timestamp': metric.timestamp.isoformat(),
            'metadata': metric.metadata or {}
        }
        
        # Appeler les callbacks d'alerte
        for callback in self.alert_callbacks:
            try:
                callback(message, threshold.severity, alert_data)
            except Exception as e:
                logger.error(f"Erreur dans le callback d'alerte: {e}")
        
        logger.warning(f"Alerte {threshold.severity.value}: {message}")
    
    async def _collect_system_health(self) -> MetricReading:
        """Collecte la métrique de santé système."""
        try:
            from ..application.use_cases import GetSystemHealthMetricsUseCase
            from ..di_container import get_container
            
            container = get_container()
            health_use_case = container.resolve(GetSystemHealthMetricsUseCase)
            health_data = health_use_case.execute()
            
            system_health = health_data.get('system_health', 0)
            
            return MetricReading(
                metric_type=MetricType.SYSTEM_HEALTH,
                value=system_health,
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte de santé système: {e}")
            return None
    
    async def _collect_network_health(self) -> MetricReading:
        """Collecte la métrique de santé réseau."""
        try:
            from ..application.use_cases import GetSystemHealthMetricsUseCase
            from ..di_container import get_container
            
            container = get_container()
            health_use_case = container.resolve(GetSystemHealthMetricsUseCase)
            health_data = health_use_case.execute()
            
            network_health = health_data.get('network_health', 0)
            
            return MetricReading(
                metric_type=MetricType.NETWORK_HEALTH,
                value=network_health,
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte de santé réseau: {e}")
            return None
    
    async def _collect_security_health(self) -> MetricReading:
        """Collecte la métrique de santé sécurité."""
        try:
            from ..application.use_cases import GetSystemHealthMetricsUseCase
            from ..di_container import get_container
            
            container = get_container()
            health_use_case = container.resolve(GetSystemHealthMetricsUseCase)
            health_data = health_use_case.execute()
            
            security_health = health_data.get('security_health', 0)
            
            return MetricReading(
                metric_type=MetricType.SECURITY_HEALTH,
                value=security_health,
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte de santé sécurité: {e}")
            return None
    
    async def _collect_device_cpu(self) -> List[MetricReading]:
        """
        Collecte les métriques CPU des équipements via SNMP.
        
        Implémentation réelle avec SNMP pour récupérer les vraies métriques CPU.
        """
        metrics = []
        
        try:
            # Importer les dépendances nécessaires
            from network_management.models import NetworkDevice
            from api_clients.network.snmp_client import SNMPClient
            import asyncio
            
            # Récupérer les équipements réseau avec SNMP activé
            devices = NetworkDevice.objects.filter(
                is_monitored=True,
                snmp_community__isnull=False
            ).exclude(snmp_community='')
            
            logger.info(f"Collecte CPU pour {devices.count()} équipements")
            
            # Collecter en parallèle avec limite de concurrence
            semaphore = asyncio.Semaphore(5)  # Max 5 connexions simultanées
            
            async def collect_device_cpu(device):
                async with semaphore:
                    try:
                        # Initialiser le client SNMP
                        snmp_client = SNMPClient(
                            host=str(device.ip_address),
                            community=device.snmp_community or 'public',
                            port=device.snmp_port or 161,
                            timeout=5,
                            retries=2
                        )
                        
                        # OIDs pour CPU usage (standard Cisco et générique)
                        cpu_oids = [
                            '1.3.6.1.4.1.9.9.109.1.1.1.1.7.1',  # Cisco CPU 5min avg
                            '1.3.6.1.4.1.9.9.109.1.1.1.1.8.1',  # Cisco CPU 1min avg
                            '1.3.6.1.2.1.25.3.3.1.2.1',         # Generic CPU usage
                            '1.3.6.1.4.1.2021.11.9.0',         # Net-SNMP CPU user
                        ]
                        
                        cpu_value = None
                        for oid in cpu_oids:
                            try:
                                result = await asyncio.get_event_loop().run_in_executor(
                                    None, snmp_client.get, oid
                                )
                                if result and 'value' in result:
                                    cpu_value = float(result['value'])
                                    break
                            except Exception as oid_error:
                                logger.debug(f"OID {oid} failed for {device.name}: {oid_error}")
                                continue
                        
                        if cpu_value is not None:
                            # Assurer que la valeur est dans la plage 0-100
                            if cpu_value > 100:
                                cpu_value = cpu_value / 100  # Conversion si nécessaire
                            
                            return MetricReading(
                                metric_type=MetricType.DEVICE_CPU,
                                value=min(max(cpu_value, 0), 100),  # Clamp entre 0-100
                                timestamp=timezone.now(),
                                device_id=device.id,
                                device_name=device.name,
                                metadata={
                                    'snmp_host': str(device.ip_address),
                                    'device_type': device.device_type,
                                    'vendor': device.vendor
                                }
                            )
                        else:
                            logger.warning(f"Aucune métrique CPU trouvée pour {device.name}")
                            return None
                            
                    except Exception as e:
                        logger.error(f"Erreur collecte CPU pour {device.name}: {e}")
                        return None
            
            # Exécuter la collecte en parallèle
            tasks = [collect_device_cpu(device) for device in devices]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filtrer les résultats valides
            for result in results:
                if isinstance(result, MetricReading):
                    metrics.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Erreur dans la collecte: {result}")
            
            # Si aucune métrique réelle n'est disponible, créer des équipements de test
            if not metrics and not devices.exists():
                logger.info("Aucun équipement SNMP configuré, création d'équipements de test")
                
                # Créer quelques équipements de test
                test_devices = [
                    {
                        'name': 'Test-Router-01',
                        'device_type': 'router',
                        'ip_address': '127.0.0.1',  # Localhost pour test
                        'snmp_community': 'public',
                        'is_monitored': True,
                        'location': 'Test Lab'
                    }
                ]
                
                for device_data in test_devices:
                    device, created = NetworkDevice.objects.get_or_create(
                        name=device_data['name'],
                        defaults=device_data
                    )
                    if created:
                        logger.info(f"Équipement de test créé: {device.name}")
            
            logger.info(f"Collecte CPU terminée: {len(metrics)} métriques collectées")
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte CPU: {e}")
            return []
    
    async def _collect_device_memory(self) -> List[MetricReading]:
        """Collecte les métriques mémoire des équipements via SNMP."""
        metrics = []
        
        try:
            from network_management.models import NetworkDevice
            from api_clients.network.snmp_client import SNMPClient
            import asyncio
            
            # Récupérer les équipements réseau avec SNMP activé
            devices = NetworkDevice.objects.filter(
                is_monitored=True,
                snmp_community__isnull=False
            ).exclude(snmp_community='')
            
            logger.info(f"Collecte mémoire pour {devices.count()} équipements")
            
            async def collect_device_memory(device):
                try:
                    snmp_client = SNMPClient(
                        host=str(device.ip_address),
                        community=device.snmp_community or 'public',
                        port=device.snmp_port or 161,
                        timeout=5,
                        retries=2
                    )
                    
                    # OIDs pour mémoire usage
                    memory_oids = [
                        # Cisco memory pool
                        ('1.3.6.1.4.1.9.9.48.1.1.1.5.1', '1.3.6.1.4.1.9.9.48.1.1.1.6.1'),  # Used, Free
                        # Generic memory from HOST-RESOURCES-MIB
                        ('1.3.6.1.2.1.25.2.3.1.6.1', '1.3.6.1.2.1.25.2.3.1.5.1'),  # Used, Total
                        # Net-SNMP memory
                        ('1.3.6.1.4.1.2021.4.6.0', '1.3.6.1.4.1.2021.4.5.0'),  # Available, Total
                    ]
                    
                    memory_usage = None
                    for used_oid, total_oid in memory_oids:
                        try:
                            used_result = await asyncio.get_event_loop().run_in_executor(
                                None, snmp_client.get, used_oid
                            )
                            total_result = await asyncio.get_event_loop().run_in_executor(
                                None, snmp_client.get, total_oid
                            )
                            
                            if (used_result and 'value' in used_result and 
                                total_result and 'value' in total_result):
                                used = float(used_result['value'])
                                total = float(total_result['value'])
                                
                                if total > 0:
                                    memory_usage = (used / total) * 100
                                    break
                        except Exception as oid_error:
                            logger.debug(f"Memory OIDs failed for {device.name}: {oid_error}")
                            continue
                    
                    if memory_usage is not None:
                        return MetricReading(
                            metric_type=MetricType.DEVICE_MEMORY,
                            value=min(max(memory_usage, 0), 100),
                            timestamp=timezone.now(),
                            device_id=device.id,
                            device_name=device.name,
                            metadata={
                                'snmp_host': str(device.ip_address),
                                'device_type': device.device_type,
                                'vendor': device.vendor
                            }
                        )
                    else:
                        logger.warning(f"Aucune métrique mémoire trouvée pour {device.name}")
                        return None
                        
                except Exception as e:
                    logger.error(f"Erreur collecte mémoire pour {device.name}: {e}")
                    return None
            
            # Exécuter la collecte en parallèle
            tasks = [collect_device_memory(device) for device in devices]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filtrer les résultats valides
            for result in results:
                if isinstance(result, MetricReading):
                    metrics.append(result)
            
            logger.info(f"Collecte mémoire terminée: {len(metrics)} métriques collectées")
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte mémoire: {e}")
            return []
        
        try:
            # TODO: Remplacer par une intégration réelle avec le module network
            # from network_management.models import NetworkDevice
            # from monitoring.models import Metric
            
            # Simulation temporaire pour éviter les erreurs
            # DOIT ÊTRE REMPLACÉ par une vraie collecte SNMP/API
            import random
            
            for device_id in range(1, 6):
                memory_usage = random.uniform(30, 90)  # Simulation Memory usage
                
                metrics.append(MetricReading(
                    metric_type=MetricType.DEVICE_MEMORY,
                    value=memory_usage,
                    timestamp=timezone.now(),
                    device_id=device_id,
                    device_name=f"Device-{device_id:02d}"
                ))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte mémoire: {e}")
            return []
    
    async def _collect_network_latency(self) -> MetricReading:
        """Collecte la métrique de latence réseau."""
        try:
            from ..infrastructure.monitoring_adapter import MonitoringAdapter
            
            adapter = MonitoringAdapter()
            performance_data = adapter.get_performance_metrics()
            
            latency = performance_data.get('latency_avg', 0)
            
            return MetricReading(
                metric_type=MetricType.NETWORK_LATENCY,
                value=latency,
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte de latence: {e}")
            return None
    
    async def _collect_bandwidth_utilization(self) -> MetricReading:
        """Collecte la métrique d'utilisation de bande passante."""
        try:
            from ..infrastructure.monitoring_adapter import MonitoringAdapter
            
            adapter = MonitoringAdapter()
            performance_data = adapter.get_performance_metrics()
            
            bandwidth = performance_data.get('bandwidth_utilization', 0)
            
            return MetricReading(
                metric_type=MetricType.BANDWIDTH_UTILIZATION,
                value=bandwidth,
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte de bande passante: {e}")
            return None
    
    async def _collect_packet_loss(self) -> MetricReading:
        """Collecte la métrique de perte de paquets."""
        try:
            from ..infrastructure.monitoring_adapter import MonitoringAdapter
            
            adapter = MonitoringAdapter()
            performance_data = adapter.get_performance_metrics()
            
            packet_loss = performance_data.get('packet_loss', 0)
            
            return MetricReading(
                metric_type=MetricType.PACKET_LOSS,
                value=packet_loss,
                timestamp=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la collecte de perte de paquets: {e}")
            return None
    
    def get_metric_history(self, metric_type: MetricType, device_id: int = None, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Récupère l'historique d'une métrique.
        
        Args:
            metric_type: Type de métrique
            device_id: ID de l'équipement (optionnel)
            hours: Nombre d'heures d'historique
            
        Returns:
            Liste des valeurs historiques
        """
        try:
            history = []
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Rechercher dans le cache par intervalles de minutes
            current_time = start_time
            while current_time <= end_time:
                cache_key = f"metric:{metric_type.value}:{device_id or 'global'}:{current_time.strftime('%Y%m%d%H%M')}"
                cached_data = cache.get(cache_key)
                
                if cached_data:
                    history.append(cached_data)
                
                current_time += timedelta(minutes=1)
            
            return sorted(history, key=lambda x: x['timestamp'])
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []
    
    def get_active_thresholds(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des seuils actifs.
        
        Returns:
            Liste des seuils configurés
        """
        return [
            {
                'metric_type': t.metric_type.value,
                'operator': t.operator.value,
                'value': t.value,
                'severity': t.severity.value,
                'message_template': t.message_template,
                'device_id': t.device_id,
                'is_active': t.is_active
            }
            for t in self.thresholds
        ]


# Instance globale du collecteur
metrics_collector = MetricsCollector()


def create_alert_callback(alert_model_class):
    """
    Crée un callback pour enregistrer les alertes en base de données.
    
    Args:
        alert_model_class: Classe du modèle d'alerte
        
    Returns:
        Fonction callback
    """
    def callback(message: str, severity: AlertSeverity, data: Dict[str, Any]):
        """Callback pour enregistrer l'alerte."""
        try:
            with transaction.atomic():
                alert_model_class.objects.create(
                    message=message,
                    severity=severity.value,
                    metric_name=data.get('metric_type'),
                    source='metrics_collector',
                    status='new',
                    timestamp=timezone.now(),
                    metadata=data
                )
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de l'alerte: {e}")
    
    return callback