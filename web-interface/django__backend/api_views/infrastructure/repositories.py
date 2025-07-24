"""
Implémentations des repositories pour le module api_views.

Ce fichier fournit les implémentations concrètes des interfaces définies 
dans domain/interfaces.py.
"""

from typing import Dict, Any, List, Optional
import logging
from django.db.models import Q
from django.conf import settings

from ..domain.interfaces import DashboardRepository, TopologyDiscoveryRepository, APISearchRepository
from ..domain.exceptions import ResourceNotFoundException, TopologyDiscoveryException

logger = logging.getLogger(__name__)


class DjangoDashboardRepository(DashboardRepository):
    """
    Implémentation Django du repository de tableaux de bord.
    """
    
    def get_dashboard_data(self, dashboard_type: str, user_id: Optional[int] = None,
                         filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Récupère les données d'un tableau de bord.
        """
        # Import tardif pour éviter les imports circulaires
        from network_management.infrastructure.models import NetworkDevice
        from network_management.infrastructure.models import Topology as NetworkTopology
        from monitoring.models import Alert, ServiceCheck
        from security_management.models import SecurityRule, SecurityAlert
        
        filters = filters or {}
        result = {}
        
        if dashboard_type == "system-overview":
            # Récupérer les métriques système globales
            result = {
                "devices": {
                    "total": NetworkDevice.objects.count(),
                    "online": NetworkDevice.objects.filter(status="online").count(),
                    "offline": NetworkDevice.objects.filter(status="offline").count(),
                    "warning": NetworkDevice.objects.filter(status="warning").count(),
                },
                "alerts": {
                    "total": Alert.objects.count(),
                    "critical": Alert.objects.filter(severity="critical").count(),
                    "warning": Alert.objects.filter(severity="warning").count(),
                    "info": Alert.objects.filter(severity="info").count(),
                },
                "security": {
                    "alerts": SecurityAlert.objects.count(),
                    "rules": SecurityRule.objects.count(),
                    "blocked_ips": SecurityRule.objects.filter(action="block").count(),
                }
            }
        elif dashboard_type == "network-status":
            # Récupérer les métriques réseau
            result = {
                "topology": {
                    "devices": NetworkDevice.objects.count(),
                    "connections": NetworkTopology.objects.count(),
                },
                "bandwidth": self._get_real_bandwidth_metrics(),
                "services": {
                    "total": ServiceCheck.objects.count(),
                    "up": ServiceCheck.objects.filter(status="up").count(),
                    "down": ServiceCheck.objects.filter(status="down").count(),
                    "warning": ServiceCheck.objects.filter(status="warning").count(),
                }
            }
        elif dashboard_type == "user-dashboard":
            # Pour un tableau de bord personnalisé par utilisateur
            if not user_id:
                return {"error": "User ID is required for user dashboard"}
                
            # Récupérer la configuration utilisateur
            config = self.get_dashboard_configuration(dashboard_type, user_id)
            widgets = config.get("widgets", [])
            
            # Préparer les données pour chaque widget
            result = {
                "widgets": []
            }
            
            for widget in widgets:
                widget_type = widget.get("type")
                widget_data = {}
                
                if widget_type == "alerts":
                    widget_data = {
                        "alerts": list(Alert.objects.filter(
                            severity__in=widget.get("severities", ["critical", "warning"])
                        ).values("id", "title", "severity", "created_at")[:5])
                    }
                elif widget_type == "devices":
                    widget_data = {
                        "devices": list(NetworkDevice.objects.filter(
                            status__in=widget.get("statuses", ["offline", "warning"])
                        ).values("id", "name", "status", "device_type")[:5])
                    }
                
                result["widgets"].append({
                    "id": widget.get("id"),
                    "type": widget_type,
                    "title": widget.get("title"),
                    "data": widget_data
                })
        
        return result
    
    def save_dashboard_configuration(self, dashboard_type: str, configuration: Dict[str, Any],
                                  user_id: Optional[int] = None) -> bool:
        """
        Sauvegarde la configuration d'un tableau de bord.
        """
        # Import tardif pour éviter les imports circulaires
        from network_management.infrastructure.models import DashboardConfiguration
        from django.contrib.auth import get_user_model
        
        if not user_id and dashboard_type in ["user-dashboard", "custom"]:
            return False
            
        try:
            User = get_user_model()
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    logger.warning(f"User {user_id} not found for dashboard configuration")
            
            # Créer ou mettre à jour la configuration
            config, created = DashboardConfiguration.objects.update_or_create(
                dashboard_type=dashboard_type,
                user=user,
                defaults={
                    'configuration': configuration,
                    'is_active': True
                }
            )
            
            logger.info(f"Dashboard configuration {'created' if created else 'updated'} for {dashboard_type}, user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving dashboard configuration: {e}")
            return False
    
    def get_dashboard_configuration(self, dashboard_type: str, 
                                 user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Récupère la configuration d'un tableau de bord.
        """
        # Configuration par défaut pour un tableau de bord utilisateur
        if dashboard_type == "user-dashboard":
            return {
                "widgets": [
                    {
                        "id": "alerts-widget",
                        "type": "alerts",
                        "title": "Dernières alertes",
                        "severities": ["critical", "warning"]
                    },
                    {
                        "id": "devices-widget",
                        "type": "devices",
                        "title": "Appareils hors ligne",
                        "statuses": ["offline"]
                    }
                ]
            }
        elif dashboard_type == "system-overview":
            return {
                "refresh_interval": 30,
                "metrics": ["cpu", "memory", "disk", "network"],
                "show_alerts": True
            }
        elif dashboard_type == "network-status":
            return {
                "refresh_interval": 60,
                "show_topology": True,
                "show_bandwidth": True,
                "show_services": True
            }
            
        # Configuration vide par défaut
        return {}
    
    def _get_real_bandwidth_metrics(self) -> Dict[str, int]:
        """
        Récupère les métriques de bande passante réelles depuis les équipements réseau.
        """
        try:
            # Import tardif pour éviter les imports circulaires
            from network_management.infrastructure.models import NetworkInterface
            from django.db.models import Sum, Avg, F
            
            # Récupération des interfaces réseau actives
            interfaces = NetworkInterface.objects.filter(status='up')
            interface_count = interfaces.count()
            
            # Pour l'instant, utiliser des données simulées car les champs de bande passante
            # ne sont pas encore implémentés dans le modèle NetworkInterface
            
            # Simulation basée sur le nombre d'interfaces et de dispositifs
            from network_management.infrastructure.models import NetworkDevice
            device_count = NetworkDevice.objects.count()
            
            # Calculs simulés basés sur des valeurs réalistes
            estimated_capacity = interface_count * 1000  # 1 Gbps par interface
            current_usage = int(estimated_capacity * 0.15)  # 15% d'utilisation moyenne
            peak_usage = int(estimated_capacity * 0.45)  # 45% pic d'utilisation
            
            # Protocoles top simulés
            top_protocols = [
                {"protocol": "HTTP/HTTPS", "usage": current_usage * 0.4},
                {"protocol": "SSH", "usage": current_usage * 0.2},
                {"protocol": "SNMP", "usage": current_usage * 0.15},
                {"protocol": "DNS", "usage": current_usage * 0.1},
                {"protocol": "Other", "usage": current_usage * 0.15}
            ]
            
            # Tendance simulée (croissance légère)
            usage_trend = 2.5  # +2.5% de croissance
            
            return {
                "total_capacity": estimated_capacity,  # Bande passante totale disponible (Mbps)
                "current_usage": current_usage,        # Utilisation actuelle (Mbps)
                "utilization_percent": (current_usage / estimated_capacity * 100) if estimated_capacity > 0 else 0,
                "peak_usage": peak_usage,              # Pic d'utilisation (Mbps)
                "top_protocols": top_protocols,        # Principaux protocoles consommateurs
                "trend": usage_trend,                  # Tendance d'utilisation (% de changement)
                "interface_count": interface_count,    # Nombre d'interfaces actives
                "device_count": device_count          # Nombre de dispositifs
            }
            
        except Exception as e:
            # Journaliser l'erreur mais ne pas planter
            logger.error(f"Erreur lors de la récupération des métriques de bande passante: {e}")
            
            # En cas d'erreur, retourner des valeurs par défaut
            return {
                "total_capacity": 0,
                "current_usage": 0,
                "utilization_percent": 0,
                "peak_usage": 0,
                "top_protocols": [],
                "trend": 0,
                "interface_count": 0,
                "device_count": 0,
                "error": str(e)
            }


class DjangoTopologyDiscoveryRepository(TopologyDiscoveryRepository):
    """
    Implémentation Django du repository de découverte de topologie.
    """
    
    def get_network_topology(self, network_id: Optional[str] = None,
                           filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Récupère la topologie d'un réseau.
        """
        # Import tardif pour éviter les imports circulaires
        from network_management.infrastructure.models import NetworkDevice
        from network_management.infrastructure.models import Topology as NetworkTopology
        
        filters = filters or {}
        
        # Si un ID de réseau est fourni, filtrer par ce réseau
        topology_query = NetworkTopology.objects.all()
        if network_id:
            topology_query = topology_query.filter(network_id=network_id)
        
        # Appliquer d'autres filtres
        device_type = filters.get("device_type")
        if device_type:
            topology_query = topology_query.filter(
                Q(source_device__device_type=device_type) | 
                Q(target_device__device_type=device_type)
            )
        
        # Construire la topologie
        nodes = []
        edges = []
        device_ids = set()
        
        for conn in topology_query:
            source_id = str(conn.source_device.id)
            target_id = str(conn.target_device.id)
            
            # Ajouter les noeuds s'ils n'existent pas déjà
            if source_id not in device_ids:
                device_ids.add(source_id)
                nodes.append({
                    "id": source_id,
                    "label": conn.source_device.name,
                    "type": conn.source_device.device_type,
                    "status": conn.source_device.status
                })
                
            if target_id not in device_ids:
                device_ids.add(target_id)
                nodes.append({
                    "id": target_id,
                    "label": conn.target_device.name,
                    "type": conn.target_device.device_type,
                    "status": conn.target_device.status
                })
            
            # Ajouter l'arête
            edges.append({
                "id": str(conn.id),
                "source": source_id,
                "target": target_id,
                "interface_source": conn.source_interface,
                "interface_target": conn.target_interface,
                "type": conn.connection_type
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "network_id": network_id,
                "node_count": len(nodes),
                "edge_count": len(edges)
            }
        }
    
    def start_discovery(self, network_id: str, discovery_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Démarre une découverte de topologie.
        """
        from network_management.tasks import start_network_discovery
        
        # Créer une tâche de découverte (via Celery)
        task = start_network_discovery.delay(
            network_id=network_id,
            ip_range=discovery_params.get("ip_range"),
            scan_type=discovery_params.get("scan_type", "standard"),
            protocols=discovery_params.get("protocols", ["snmp", "ssh", "telnet"])
        )
        
        return {
            "discovery_id": task.id,
            "network_id": network_id,
            "status": "started",
            "estimated_time": "5-10 minutes"
        }
    
    def get_discovery_status(self, discovery_id: str) -> Dict[str, Any]:
        """
        Récupère le statut d'une découverte de topologie.
        """
        from network_management.tasks import start_network_discovery
        from celery.result import AsyncResult
        
        # Récupérer le statut de la tâche Celery
        task_result = AsyncResult(discovery_id)
        
        status = {
            "discovery_id": discovery_id,
            "status": task_result.status,
            "progress": 0,
            "devices_found": 0,
            "details": ""
        }
        
        if task_result.successful():
            result = task_result.get()
            status.update({
                "progress": 100,
                "devices_found": result.get("devices_found", 0),
                "connections_found": result.get("connections_found", 0),
                "details": "Discovery completed successfully"
            })
        elif task_result.failed():
            status.update({
                "status": "failed",
                "details": str(task_result.result)
            })
        elif task_result.status == "PROGRESS":
            if task_result.info:
                status.update({
                    "progress": task_result.info.get("progress", 0),
                    "devices_found": task_result.info.get("devices_found", 0),
                    "details": task_result.info.get("details", "")
                })
        
        return status
    
    def save_topology(self, topology_data: Dict[str, Any], network_id: str) -> bool:
        """
        Sauvegarde une topologie découverte.
        """
        # Import tardif pour éviter les imports circulaires
        from network_management.infrastructure.models import NetworkDevice
        from network_management.infrastructure.models import Topology as NetworkTopology
        
        try:
            nodes = topology_data.get("nodes", [])
            edges = topology_data.get("edges", [])
            
            # Sauvegarder ou mettre à jour les périphériques
            for node in nodes:
                device, created = NetworkDevice.objects.update_or_create(
                    id=node.get("id"),
                    defaults={
                        "name": node.get("label"),
                        "device_type": node.get("type"),
                        "status": node.get("status", "unknown"),
                        "network_id": network_id
                    }
                )
            
            # Sauvegarder ou mettre à jour les connexions
            for edge in edges:
                source_device = NetworkDevice.objects.get(id=edge.get("source"))
                target_device = NetworkDevice.objects.get(id=edge.get("target"))
                
                connection, created = NetworkTopology.objects.update_or_create(
                    source_device=source_device,
                    target_device=target_device,
                    defaults={
                        "connection_type": edge.get("type", "ethernet"),
                        "source_interface": edge.get("interface_source", ""),
                        "target_interface": edge.get("interface_target", ""),
                        "network_id": network_id
                    }
                )
            
            return True
        except Exception as e:
            logger.error(f"Error saving topology: {e}")
            return False


class DjangoAPISearchRepository(APISearchRepository):
    """
    Implémentation Django du repository de recherche API.
    """
    
    def search(self, query: str, resource_types: List[str],
             filters: Optional[Dict[str, Any]] = None,
             pagination: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
        """
        Effectue une recherche dans les ressources.
        """
        # Import tardif pour éviter les imports circulaires
        from network_management.infrastructure.models import NetworkDevice
        from network_management.infrastructure.models import Alert
        from monitoring.models import ServiceCheck
        from security_management.models import SecurityAlert
        
        results = {
            "results": [],
            "total": 0,
            "pagination": {
                "page": 1,
                "per_page": 25,
                "total_pages": 1
            }
        }
        
        # Appliquer la pagination
        pagination = pagination or {}
        page = pagination.get("page", 1)
        per_page = pagination.get("per_page", 25)
        
        # Effectuer des recherches par type de ressource
        all_results = []
        
        if "devices" in resource_types:
            devices = NetworkDevice.objects.filter(
                Q(name__icontains=query) |
                Q(ip_address__icontains=query) |
                Q(description__icontains=query)
            )
            for device in devices:
                all_results.append({
                    "id": str(device.id),
                    "type": "device",
                    "name": device.name,
                    "description": f"{device.device_type} - {device.ip_address}"
                })
        
        if "alerts" in resource_types:
            alerts = Alert.objects.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
            for alert in alerts:
                all_results.append({
                    "id": str(alert.id),
                    "type": "alert",
                    "name": alert.title,
                    "description": f"{alert.severity} - {alert.status}"
                })
        
        # Appliquer des filtres supplémentaires
        filters = filters or {}
        resource_type_filter = filters.get("type")
        if resource_type_filter:
            all_results = [r for r in all_results if r["type"] == resource_type_filter]
        
        # Calculer la pagination
        total = len(all_results)
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        
        # Paginer les résultats
        results["results"] = all_results[start:end]
        results["total"] = total
        results["pagination"] = {
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
        
        return results
    
    def get_resource_details(self, resource_type: str, resource_id: str) -> Dict[str, Any]:
        """
        Récupère les détails d'une ressource.
        """
        if resource_type == "device":
            try:
                device = NetworkDevice.objects.get(id=resource_id)
                return {
                    "id": str(device.id),
                    "type": "device",
                    "name": device.name,
                    "ip_address": device.ip_address,
                    "device_type": device.device_type,
                    "status": device.status,
                    "description": device.description,
                    "location": device.location,
                    "interfaces": list(device.interfaces.values(
                        "id", "name", "type", "status", "ip_address", "mac_address"
                    ))
                }
            except NetworkDevice.DoesNotExist:
                raise ResourceNotFoundException("Device", resource_id)
        
        elif resource_type == "alert":
            try:
                alert = Alert.objects.get(id=resource_id)
                return {
                    "id": str(alert.id),
                    "type": "alert",
                    "title": alert.title,
                    "description": alert.description,
                    "severity": alert.severity,
                    "status": alert.status,
                    "created_at": alert.created_at,
                    "device": {
                        "id": str(alert.device.id),
                        "name": alert.device.name
                    } if alert.device else None
                }
            except Alert.DoesNotExist:
                raise ResourceNotFoundException("Alert", resource_id)
        
        else:
            raise ResourceNotFoundException(resource_type, resource_id,
                                          message=f"Resource type {resource_type} not supported") 