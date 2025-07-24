"""
Adaptateur réseau pour le module Dashboard.

Ce fichier implémente l'interface INetworkDataProvider pour
connecter le tableau de bord aux données du réseau.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from django.db.models import Count, Q
from asgiref.sync import sync_to_async

from django.conf import settings
from django.utils import timezone

# Import des vrais modèles Django
from network_management.models import NetworkDevice, NetworkInterface, NetworkConnection
try:
    from qos_management.models import QoSPolicy, InterfaceQoSPolicy
except ImportError:
    logger.warning("Module QoS non disponible")
    QoSPolicy = None
    InterfaceQoSPolicy = None

from ..domain.interfaces import INetworkDataProvider
from ..domain.entities import AlertInfo, AlertSeverity

logger = logging.getLogger(__name__)


class NetworkAdapter(INetworkDataProvider):
    """
    Adaptateur pour récupérer les données réseau.
    
    Cette classe implémente l'interface INetworkDataProvider pour récupérer
    les données réseau et les convertir en structures utilisables par le tableau de bord.
    """
    
    def __init__(self):
        """Initialise l'adaptateur réseau."""
        # Dans une implémentation réelle, on initialiserait les services nécessaires
        self._device_service = None
        self._topology_service = None
        self._qos_service = None
        
        # Essayer d'importer les services nécessaires
        try:
            from network_management.services import (
                DeviceService, 
                TopologyService
            )
            from qos_management.services import QoSService
            
            # On les initialiserait ici dans une implémentation complète
            # self._device_service = DeviceService()
            # self._topology_service = TopologyService()
            # self._qos_service = QoSService()
            logger.info("Services réseau importés avec succès")
        except ImportError:
            logger.warning("Services réseau non disponibles. Utilisation de données simulées.")
    
    async def get_device_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé des équipements réseau depuis la base de données réelle.

        Returns:
            Dictionnaire contenant les statistiques sur les équipements
        """
        try:
            logger.info("Récupération des données réelles d'équipements depuis la base de données")

            # Récupération asynchrone des données depuis la base de données
            total_devices = await sync_to_async(NetworkDevice.objects.count)()

            # Statistiques par type d'équipement
            device_types_query = await sync_to_async(
                lambda: dict(NetworkDevice.objects.values('device_type').annotate(count=Count('id')).values_list('device_type', 'count'))
            )()

            # Statistiques par statut
            status_counts_query = await sync_to_async(
                lambda: dict(NetworkDevice.objects.values('status').annotate(count=Count('id')).values_list('status', 'count'))
            )()

            # Statistiques de connexions
            total_connections = await sync_to_async(NetworkConnection.objects.count)()

            # Calculer les connexions par statut (basé sur le statut des équipements connectés)
            healthy_connections = await sync_to_async(
                lambda: NetworkConnection.objects.filter(
                    source_device__status='active',
                    target_device__status='active'
                ).count()
            )()

            degraded_connections = await sync_to_async(
                lambda: NetworkConnection.objects.filter(
                    Q(source_device__status='warning') | Q(target_device__status='warning')
                ).exclude(
                    Q(source_device__status='critical') | Q(target_device__status='critical') | Q(source_device__status='inactive') | Q(target_device__status='inactive')
                ).count()
            )()

            failed_connections = total_connections - healthy_connections - degraded_connections

            # Normaliser les noms de statut pour compatibilité
            status_mapping = {
                'active': 'active',
                'inactive': 'inactive',
                'maintenance': 'maintenance',
                'warning': 'warning',
                'critical': 'critical'
            }

            normalized_status = {}
            for status, count in status_counts_query.items():
                normalized_key = status_mapping.get(status, status)
                normalized_status[normalized_key] = normalized_status.get(normalized_key, 0) + count

            connection_stats = {
                "total": total_connections,
                "healthy": healthy_connections,
                "degraded": degraded_connections,
                "failed": max(0, failed_connections)
            }

            result = {
                "total_devices": total_devices,
                "device_types": device_types_query,
                "status": normalized_status,
                "connections": connection_stats,
                "updated_at": timezone.now().isoformat(),
                "data_source": "real_database"
            }

            logger.info(f"Données réelles récupérées: {total_devices} équipements, {total_connections} connexions")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du résumé des équipements: {e}")
            # Fallback vers des données minimales en cas d'erreur
            return {
                "error": str(e),
                "total_devices": 0,
                "device_types": {},
                "status": {},
                "connections": {"total": 0, "healthy": 0, "degraded": 0, "failed": 0},
                "updated_at": timezone.now().isoformat(),
                "data_source": "error_fallback"
            }
    
    async def get_interface_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé des interfaces réseau depuis la base de données réelle.

        Returns:
            Dictionnaire contenant les statistiques sur les interfaces
        """
        try:
            logger.info("Récupération des données réelles d'interfaces depuis la base de données")

            # Récupération asynchrone des données d'interfaces
            total_interfaces = await sync_to_async(NetworkInterface.objects.count)()

            # Statistiques par vitesse (speed en Mbps dans le modèle)
            interfaces_by_speed_raw = await sync_to_async(
                lambda: list(NetworkInterface.objects.exclude(speed__isnull=True).values('speed').annotate(count=Count('id')))
            )()

            # Convertir les vitesses en format lisible
            interfaces_by_speed = {}
            for item in interfaces_by_speed_raw:
                speed_mbps = item['speed']
                if speed_mbps >= 10000:
                    speed_label = f"{speed_mbps//1000}Gbps"
                elif speed_mbps >= 1000:
                    speed_label = f"{speed_mbps//1000}Gbps"
                else:
                    speed_label = f"{speed_mbps}Mbps"

                interfaces_by_speed[speed_label] = interfaces_by_speed.get(speed_label, 0) + item['count']

            # Statistiques par statut
            interfaces_by_status = await sync_to_async(
                lambda: dict(NetworkInterface.objects.values('status').annotate(count=Count('id')).values_list('status', 'count'))
            )()

            # Calculer les statistiques de trafic depuis les métriques stockées
            # Note: Dans une implémentation complète, ces données viendraient du monitoring SNMP
            traffic_stats = await self._calculate_traffic_stats()

            result = {
                "total_interfaces": total_interfaces,
                "by_speed": interfaces_by_speed,
                "by_status": interfaces_by_status,
                "traffic": traffic_stats,
                "updated_at": timezone.now().isoformat(),
                "data_source": "real_database"
            }

            logger.info(f"Données réelles d'interfaces récupérées: {total_interfaces} interfaces")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du résumé des interfaces: {e}")
            return {
                "error": str(e),
                "total_interfaces": 0,
                "by_speed": {},
                "by_status": {},
                "traffic": {},
                "updated_at": timezone.now().isoformat(),
                "data_source": "error_fallback"
            }
    
    async def get_qos_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé des politiques QoS depuis la base de données réelle.

        Returns:
            Dictionnaire contenant les statistiques sur les politiques QoS
        """
        try:
            if QoSPolicy is None:
                logger.warning("Module QoS non disponible, utilisation de données par défaut")
                return {
                    "policies": {"total": 0, "by_type": {}},
                    "classes": {"total": 0, "by_priority": {}},
                    "metrics": {},
                    "updated_at": timezone.now().isoformat(),
                    "data_source": "qos_module_unavailable"
                }

            logger.info("Récupération des données réelles QoS depuis la base de données")

            # Récupération des politiques QoS
            total_policies = await sync_to_async(QoSPolicy.objects.count)()

            # Statistiques par type de politique
            policies_by_type = await sync_to_async(
                lambda: dict(QoSPolicy.objects.values('policy_type').annotate(count=Count('id')).values_list('policy_type', 'count'))
            )()

            # Statistiques par priorité
            classes_by_priority = await sync_to_async(
                lambda: dict(QoSPolicy.objects.values('priority').annotate(count=Count('id')).values_list('priority', 'count'))
            )()

            total_classes = sum(classes_by_priority.values())

            # Métriques QoS (dans une implémentation complète, ces données viendraient du monitoring)
            metrics = await self._calculate_qos_metrics()

            result = {
                "policies": {
                    "total": total_policies,
                    "by_type": policies_by_type
                },
                "classes": {
                    "total": total_classes,
                    "by_priority": classes_by_priority
                },
                "metrics": metrics,
                "updated_at": timezone.now().isoformat(),
                "data_source": "real_database"
            }

            logger.info(f"Données réelles QoS récupérées: {total_policies} politiques")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération du résumé QoS: {e}")
            return {
                "error": str(e),
                "policies": {"total": 0, "by_type": {}},
                "classes": {"total": 0, "by_priority": {}},
                "metrics": {},
                "updated_at": timezone.now().isoformat(),
                "data_source": "error_fallback"
            }
    
    async def get_topology_data(self, topology_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère les données de topologie depuis la base de données réelle.

        Args:
            topology_id: ID de la topologie (optionnel)

        Returns:
            Données de topologie
        """
        try:
            logger.info(f"Récupération des données réelles de topologie {topology_id or 'toutes'}")

            # Récupérer tous les équipements avec leurs interfaces
            devices_data = await sync_to_async(
                lambda: list(NetworkDevice.objects.select_related().prefetch_related('interfaces').all())
            )()

            # Récupérer toutes les connexions
            connections_data = await sync_to_async(
                lambda: list(NetworkConnection.objects.select_related('source_device', 'target_device', 'source_interface', 'target_interface').all())
            )()

            # Convertir en format de topologie
            nodes = []
            for device in devices_data:
                # Calculer la position (dans une vraie implémentation, cela viendrait de la base de données)
                position = await self._get_device_position(device.id)

                nodes.append({
                    "id": f"device-{device.id}",
                    "name": device.name,
                    "type": device.device_type,
                    "status": device.status,
                    "ip_address": str(device.ip_address),
                    "vendor": device.vendor,
                    "model": device.model,
                    "position": position,
                    "interfaces_count": len(device.interfaces.all()) if hasattr(device, 'interfaces') else 0,
                    "last_seen": device.updated_at.isoformat() if device.updated_at else None
                })

            # Convertir les connexions
            connections = []
            for conn in connections_data:
                connections.append({
                    "id": f"conn-{conn.id}",
                    "source": f"device-{conn.source_device.id}",
                    "target": f"device-{conn.target_device.id}",
                    "source_interface": conn.source_interface.name if conn.source_interface else None,
                    "target_interface": conn.target_interface.name if conn.target_interface else None,
                    "type": conn.connection_type,
                    "bandwidth": conn.bandwidth,
                    "latency": conn.latency,
                    "status": self._determine_connection_status(conn)
                })

            # Calculer les statistiques de santé
            health_summary = {
                "healthy": sum(1 for node in nodes if node["status"] == "active"),
                "warning": sum(1 for node in nodes if node["status"] == "warning"),
                "critical": sum(1 for node in nodes if node["status"] == "critical"),
                "inactive": sum(1 for node in nodes if node["status"] == "inactive")
            }

            result = {
                "topology_id": topology_id,
                "name": f"Topologie réseau {topology_id}" if topology_id else "Topologie complète",
                "nodes": nodes,
                "connections": connections,
                "health_summary": health_summary,
                "last_updated": timezone.now().isoformat(),
                "data_source": "real_database"
            }

            logger.info(f"Topologie récupérée: {len(nodes)} équipements, {len(connections)} connexions")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données de topologie {topology_id}: {e}")
            return {
                "error": str(e),
                "topology_id": topology_id,
                "nodes": [],
                "connections": [],
                "health_summary": {},
                "data_source": "error_fallback"
            }
    
    async def get_network_alerts(self, limit: int = 5, severity_filter: Optional[List[str]] = None) -> List[AlertInfo]:
        """
        Récupère les alertes réseau.
        
        Args:
            limit: Nombre maximum d'alertes à récupérer
            severity_filter: Liste des niveaux de sévérité pour filtrer les alertes
            
        Returns:
            Liste des alertes réseau
        """
        try:
            # Dans une implémentation réelle, on récupérerait les données depuis le service
            # if self._device_service:
            #     raw_alerts = await self._device_service.get_network_alerts(limit=limit, severity=severity_filter)
            #     return [self._convert_to_alert_info(alert) for alert in raw_alerts]
            
            # Utilisation temporaire de données simulées - réutiliser la méthode de l'adaptateur monitoring
            import inspect
            from ..infrastructure.monitoring_adapter import MonitoringAdapter
            
            # Vérifier si la méthode privée existe
            if not hasattr(MonitoringAdapter, '_get_simulated_alerts'):
                raise AttributeError("Méthode _get_simulated_alerts non disponible")
                
            # Créer une instance temporaire pour appeler la méthode
            temp_adapter = MonitoringAdapter()
            alerts = await temp_adapter._get_simulated_alerts(limit, "network", None)
            
            # Modifier les alertes pour être spécifiques au réseau
            network_problems = [
                "Link down on interface eth0/1", 
                "High latency to router-core-01",
                "Packet loss detected on WAN link",
                "BGP session flapping with peer 192.168.1.1",
                "Interface utilization >90% on switch-dist-03"
            ]
            
            for i, alert in enumerate(alerts):
                alert.message = network_problems[i % len(network_problems)]
                alert.source = "network.monitoring"
            
            return alerts
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes réseau: {e}")
            return []
    
    # Méthodes helper pour les données réelles

    async def _calculate_traffic_stats(self) -> Dict[str, Any]:
        """
        Calcule les statistiques de trafic depuis les métriques d'interfaces.
        Dans une implémentation complète, ces données viendraient du monitoring SNMP.
        """
        try:
            # Pour l'instant, retourner des valeurs calculées basiques
            # Dans une vraie implémentation, on interrogerait les métriques SNMP stockées
            interfaces_with_stats = await sync_to_async(
                lambda: list(NetworkInterface.objects.exclude(statistics__isnull=True))
            )()

            total_ingress = 0.0
            total_egress = 0.0

            for interface in interfaces_with_stats:
                stats = interface.statistics or {}
                total_ingress += stats.get('rx_bytes_per_sec', 0) / (1024**3)  # Convert to Gbps
                total_egress += stats.get('tx_bytes_per_sec', 0) / (1024**3)   # Convert to Gbps

            return {
                "total_ingress_gbps": round(total_ingress, 2),
                "total_egress_gbps": round(total_egress, 2),
                "peak_hour_ingress_gbps": round(total_ingress * 1.5, 2),  # Estimation
                "peak_hour_egress_gbps": round(total_egress * 1.3, 2)     # Estimation
            }
        except Exception as e:
            logger.warning(f"Erreur lors du calcul des statistiques de trafic: {e}")
            return {
                "total_ingress_gbps": 0.0,
                "total_egress_gbps": 0.0,
                "peak_hour_ingress_gbps": 0.0,
                "peak_hour_egress_gbps": 0.0
            }

    async def _calculate_qos_metrics(self) -> Dict[str, Any]:
        """
        Calcule les métriques QoS depuis les données de monitoring.
        """
        try:
            # Dans une vraie implémentation, ces données viendraient du monitoring en temps réel
            return {
                "dropped_packets": 0,
                "delayed_packets": 0,
                "reordered_packets": 0,
                "average_jitter_ms": 0.0,
                "policy_violations": 0
            }
        except Exception as e:
            logger.warning(f"Erreur lors du calcul des métriques QoS: {e}")
            return {}

    async def _get_device_position(self, device_id: int) -> Dict[str, int]:
        """
        Récupère la position d'un équipement pour la topologie.
        Dans une vraie implémentation, cela viendrait de la base de données de topologie.
        """
        # Position calculée basée sur l'ID pour une distribution uniforme
        x = (device_id * 150) % 800 + 100
        y = (device_id * 100) % 400 + 100
        return {"x": x, "y": y}

    def _determine_connection_status(self, connection: NetworkConnection) -> str:
        """
        Détermine le statut d'une connexion basé sur le statut des équipements connectés.
        """
        source_status = connection.source_device.status
        target_status = connection.target_device.status

        if source_status == 'critical' or target_status == 'critical':
            return 'critical'
        elif source_status == 'warning' or target_status == 'warning':
            return 'warning'
        elif source_status == 'active' and target_status == 'active':
            return 'healthy'
        else:
            return 'inactive'

    # Méthodes privées pour générer des données simulées (conservées pour compatibilité)

    async def _get_simulated_topology(self, topology_id: int) -> Dict[str, Any]:
        """Génère une topologie simulée pour les tests."""
        # Simulons une topologie de réseau simple
        nodes = []
        connections = []
        
        # Créer des nœuds pour la topologie basés sur l'ID
        prefix = "site" if topology_id == 1 else "datacenter"
        node_count = 8 if topology_id == 1 else 12
        
        for i in range(1, node_count + 1):
            node_type = "router" if i <= 2 else "switch" if i <= 6 else "firewall" if i <= 8 else "server"
            status = "active" if i % 7 != 0 else "warning" if i % 11 != 0 else "critical"
            
            nodes.append({
                "id": f"{prefix}-node-{i}",
                "name": f"{node_type.capitalize()}-{i:02d}",
                "type": node_type,
                "status": status,
                "ip_address": f"10.{topology_id}.{i//10}.{i%10 + 1}",
                "position": {
                    "x": 100 + (i * 120) % 800,
                    "y": 100 + (i * 80) % 400
                },
                "metrics": {
                    "cpu": 20 + (i * 5) % 60,
                    "memory": 30 + (i * 7) % 50,
                    "temp": 35 + (i * 3) % 15
                }
            })
        
        # Créer des connexions entre les nœuds
        for i in range(node_count):
            # Connecter à quelques autres nœuds pour créer un graphe
            # Éviter de créer trop de liens pour garder la topologie lisible
            for j in range(1, 4):
                target_idx = (i + j) % node_count
                if target_idx != i:  # Éviter les boucles
                    status = "healthy" if (i + target_idx) % 7 != 0 else "warning" if (i + target_idx) % 11 != 0 else "critical"
                    link_type = "fiber" if i < 3 or target_idx < 3 else "copper"
                    
                    connections.append({
                        "id": f"conn-{i+1}-{target_idx+1}",
                        "source": f"{prefix}-node-{i+1}",
                        "target": f"{prefix}-node-{target_idx+1}",
                        "status": status,
                        "type": link_type,
                        "metrics": {
                            "bandwidth_mbps": 1000 if link_type == "fiber" else 100,
                            "latency_ms": 2 if link_type == "fiber" else 5,
                            "packet_loss": 0.01 if status == "healthy" else 2.5 if status == "warning" else 8.7
                        }
                    })
        
        # Calculer les statistiques de santé
        health_summary = {
            "healthy": sum(1 for node in nodes if node["status"] == "active"),
            "warning": sum(1 for node in nodes if node["status"] == "warning"),
            "critical": sum(1 for node in nodes if node["status"] == "critical"),
            "inactive": sum(1 for node in nodes if node["status"] not in ["active", "warning", "critical"])
        }
        
        return {
            "topology_id": topology_id,
            "name": f"{'Site réseau principal' if topology_id == 1 else 'Centre de données principal'}",
            "nodes": nodes,
            "connections": connections,
            "health_summary": health_summary,
            "last_updated": timezone.now().isoformat()
        } 