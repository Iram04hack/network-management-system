"""
Adaptateurs pour le monitoring de la qualité de service (QoS).

Ce module contient les différents adaptateurs permettant de récupérer des données
de monitoring de la qualité de service depuis différentes sources.
"""

import logging
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict

from ..domain.interfaces import QoSMonitoringService
from ..domain.exceptions import QoSConfigurationException


logger = logging.getLogger(__name__)


class PrometheusQoSMonitoringAdapter(QoSMonitoringService):
    """
    Adaptateur permettant d'accéder aux données de monitoring QoS
    via Prometheus.
    """
    
    # Métriques disponibles dans Prometheus pour le monitoring QoS
    AVAILABLE_METRICS = {
        "throughput": "iface_throughput",
        "packet_loss": "iface_packet_loss_rate",
        "latency": "iface_latency_ms",
        "jitter": "iface_jitter_ms",
        "queue_size": "iface_queue_length",
        "drop_rate": "iface_packet_drop_rate",
        "buffer_usage": "iface_buffer_usage_percent",
        "tcp_retransmit": "iface_tcp_retransmission_rate"
    }
    
    # Mapping des métriques aux seuils SLA typiques (pour chaque classe de service)
    SLA_THRESHOLDS = {
        "voice": {
            "latency": 150,         # ms
            "jitter": 30,           # ms 
            "packet_loss": 1.0,     # %
            "throughput": 0         # Kbps min
        },
        "video": {
            "latency": 300,         # ms
            "jitter": 50,           # ms
            "packet_loss": 2.0,     # %
            "throughput": 0         # Kbps min
        },
        "critical_data": {
            "latency": 500,         # ms
            "packet_loss": 0.5,     # %
            "throughput": 0         # Kbps min
        },
        "bulk_data": {
            "packet_loss": 5.0,     # %
            "throughput": 0         # Kbps min
        },
        "best_effort": {
            "packet_loss": 15.0,    # % 
            "throughput": 0         # Kbps min
        }
    }
    
    def __init__(self, prometheus_url: str):
        """
        Initialise l'adaptateur avec l'URL de Prometheus.
        
        Args:
            prometheus_url: URL du serveur Prometheus
        """
        self.prometheus_url = prometheus_url
    
    def _query_prometheus(self, query: str) -> Dict[str, Any]:
        """
        Effectue une requête à l'API Prometheus.
        
        Args:
            query: Requête PromQL à exécuter
            
        Returns:
            Résultat de la requête
            
        Raises:
            QoSConfigurationException: En cas d'erreur de communication avec Prometheus
        """
        try:
            url = f"{self.prometheus_url}/query"
            response = requests.get(url, params={"query": query})
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Erreur de communication avec Prometheus: {str(e)}")
            raise QoSConfigurationException(
                "Impossible de communiquer avec le service de monitoring",
                "prometheus_communication_error",
                {"details": str(e)}
            )
    
    def get_metrics(self, device_id: int, interface_id: Optional[int] = None, 
                   period: str = "1h") -> Dict[str, Any]:
        """
        Récupère les métriques QoS d'un équipement ou d'une interface.
        
        Args:
            device_id: ID de l'équipement
            interface_id: ID de l'interface (optionnel)
            period: Période sur laquelle récupérer les métriques
            
        Returns:
            Métriques QoS
        """
        try:
            # Simuler des données de monitoring pour la démonstration
            return {
                "device_id": device_id,
                "interface_id": interface_id,
                "period": period,
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "throughput": {"current": 850000, "avg": 820000, "max": 950000},
                    "latency": {"current": 25, "avg": 28, "max": 45},
                    "jitter": {"current": 5, "avg": 7, "max": 15},
                    "packet_loss": {"current": 0.1, "avg": 0.2, "max": 0.8},
                    "queue_depth": {"current": 15, "avg": 18, "max": 32}
                }
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des métriques QoS: {str(e)}")
            return {
                "device_id": device_id,
                "interface_id": interface_id,
                "period": period,
                "error": str(e),
                "metrics": {}
            }
    
    def get_sla_compliance(self, device_id: int, period: str = "24h") -> Dict[str, Any]:
        """
        Récupère le taux de conformité aux SLA pour un équipement.
        
        Args:
            device_id: ID de l'équipement
            period: Période sur laquelle calculer la conformité
            
        Returns:
            Rapport de conformité SLA
        """
        try:
            # Simuler un rapport de conformité SLA
            return {
                "device_id": device_id,
                "period": period,
                "timestamp": datetime.now().isoformat(),
                "overall_compliance": 0.94,
                "service_classes": {
                    "voice": {"compliance": 0.96, "violations": 12},
                    "video": {"compliance": 0.92, "violations": 28},
                    "critical_data": {"compliance": 0.98, "violations": 5},
                    "best_effort": {"compliance": 0.88, "violations": 45}
                },
                "recommendations": [
                    "Augmenter la priorité des flux vidéo",
                    "Réviser les seuils de latence pour le trafic critique"
                ]
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul de conformité SLA: {str(e)}")
            return {
                "device_id": device_id,
                "period": period,
                "error": str(e),
                "overall_compliance": 0.0
            }
    
    def get_qos_report(self, device_ids: Optional[List[int]] = None, 
                      period: str = "7d") -> Dict[str, Any]:
        """
        Génère un rapport global sur les performances QoS.
        
        Args:
            device_ids: Liste des IDs d'équipements à inclure (optionnel)
            period: Période du rapport
            
        Returns:
            Rapport QoS
        """
        try:
            if not device_ids:
                device_ids = [1, 2, 3]  # Équipements par défaut
            
            # Simuler un rapport global
            return {
                "timestamp": datetime.now().isoformat(),
                "period": period,
                "summary": {
                    "total_devices": len(device_ids),
                    "avg_compliance": 0.92,
                    "total_violations": 156,
                    "critical_issues": 8
                },
                "devices": {
                    device_id: {
                        "compliance": 0.90 + (device_id * 0.02),
                        "violations": 50 - (device_id * 5),
                        "status": "healthy" if device_id % 2 == 0 else "warning"
                    }
                    for device_id in device_ids
                },
                "trends": {
                    "compliance_trend": [0.88, 0.90, 0.92, 0.91, 0.93, 0.92, 0.94],
                    "latency_trend": [28, 26, 30, 25, 27, 24, 26]
                }
            }
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport QoS: {str(e)}")
            return {
                "timestamp": datetime.now().isoformat(),
                "period": period,
                "error": str(e)
            }


class NetflowQoSMonitoringAdapter(QoSMonitoringService):
    """
    Adaptateur permettant d'accéder aux données de monitoring QoS
    via un collecteur Netflow.
    """
    
    def __init__(self, netflow_collector_url: str):
        """
        Initialise l'adaptateur avec l'URL du collecteur Netflow.
        
        Args:
            netflow_collector_url: URL du collecteur Netflow
        """
        self.netflow_collector_url = netflow_collector_url
    
    def get_metrics(self, device_id: int, interface_id: Optional[int] = None, 
                   period: str = "1h") -> Dict[str, Any]:
        """
        Récupère les métriques QoS depuis le collecteur Netflow.
        """
        try:
            # Simuler des données Netflow
            return {
                "device_id": device_id,
                "interface_id": interface_id,
                "period": period,
                "source": "netflow",
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "flows_count": 1250,
                    "bytes_total": 85000000,
                    "packets_total": 120000,
                    "top_applications": [
                        {"name": "HTTP", "bytes": 35000000, "percentage": 41.2},
                        {"name": "HTTPS", "bytes": 28000000, "percentage": 32.9},
                        {"name": "SSH", "bytes": 12000000, "percentage": 14.1},
                        {"name": "VoIP", "bytes": 8000000, "percentage": 9.4}
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Erreur Netflow: {str(e)}")
            return {"error": str(e), "metrics": {}}
    
    def get_sla_compliance(self, device_id: int, period: str = "24h") -> Dict[str, Any]:
        """
        Calcule la conformité SLA basée sur les données Netflow.
        """
        return {
            "device_id": device_id,
            "period": period,
            "source": "netflow",
            "overall_compliance": 0.91,
            "note": "Conformité basée sur l'analyse des flux Netflow"
        }
    
    def get_qos_report(self, device_ids: Optional[List[int]] = None, 
                      period: str = "7d") -> Dict[str, Any]:
        """
        Génère un rapport QoS basé sur les données Netflow.
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "period": period,
            "source": "netflow",
            "summary": "Rapport basé sur l'analyse des flux réseau Netflow"
        }


class SNMPQoSMonitoringAdapter(QoSMonitoringService):
    """
    Adaptateur pour le monitoring QoS via SNMP.
    """
    
    def __init__(self, snmp_config: Dict[str, Any]):
        """
        Initialise l'adaptateur SNMP.
        
        Args:
            snmp_config: Configuration SNMP (host, port, community, etc.)
        """
        self.snmp_config = snmp_config
    
    def get_metrics(self, device_id: int, interface_id: Optional[int] = None, 
                   period: str = "1h") -> Dict[str, Any]:
        """
        Récupère les métriques QoS via SNMP.
        """
        try:
            # Simuler des données SNMP
            return {
                "device_id": device_id,
                "interface_id": interface_id,
                "period": period,
                "source": "snmp",
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "interface_utilization": 75.2,
                    "input_rate": 15000000,
                    "output_rate": 12000000,
                    "input_packets": 2500000,
                    "output_packets": 2300000,
                    "input_errors": 125,
                    "output_errors": 89,
                    "queue_drops": 1250
                }
            }
        except Exception as e:
            logger.error(f"Erreur SNMP: {str(e)}")
            return {"error": str(e), "metrics": {}}
    
    def get_sla_compliance(self, device_id: int, period: str = "24h") -> Dict[str, Any]:
        """
        Calcule la conformité SLA basée sur les données SNMP.
        """
        return {
            "device_id": device_id,
            "period": period,
            "source": "snmp",
            "overall_compliance": 0.93,
            "interface_compliance": {
                "GigabitEthernet0/0": 0.95,
                "GigabitEthernet0/1": 0.91,
                "Serial0/0": 0.89
            }
        }
    
    def get_qos_report(self, device_ids: Optional[List[int]] = None, 
                      period: str = "7d") -> Dict[str, Any]:
        """
        Génère un rapport QoS basé sur les données SNMP.
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "period": period,
            "source": "snmp",
            "summary": "Rapport basé sur les métriques SNMP des équipements"
        }


class CompositeQoSMonitoringAdapter(QoSMonitoringService):
    """
    Adaptateur composite qui combine plusieurs sources de monitoring QoS.
    
    Cette classe permet d'agréger les données de monitoring provenant de
    différentes sources (Prometheus, NetFlow, SNMP) pour fournir une vue
    complète et fiable des métriques QoS.
    """
    
    def __init__(self, prometheus_adapter: PrometheusQoSMonitoringAdapter = None,
                 netflow_adapter: NetflowQoSMonitoringAdapter = None,
                 snmp_adapter: SNMPQoSMonitoringAdapter = None):
        """
        Initialise l'adaptateur composite avec les adaptateurs spécialisés.
        
        Args:
            prometheus_adapter: Adaptateur Prometheus
            netflow_adapter: Adaptateur NetFlow
            snmp_adapter: Adaptateur SNMP
        """
        self.prometheus_adapter = prometheus_adapter or PrometheusQoSMonitoringAdapter()
        self.netflow_adapter = netflow_adapter or NetflowQoSMonitoringAdapter()
        self.snmp_adapter = snmp_adapter or SNMPQoSMonitoringAdapter()
        
        # Priorité des sources (de la plus fiable à la moins fiable)
        self.adapter_priority = [
            ("prometheus", self.prometheus_adapter),
            ("netflow", self.netflow_adapter),
            ("snmp", self.snmp_adapter)
        ]
    
    def get_qos_metrics(self, interface_id: int, time_range: str = "1h") -> Dict[str, Any]:
        """
        Récupère les métriques QoS en combinant plusieurs sources.
        
        Args:
            interface_id: ID de l'interface
            time_range: Période de temps (ex: "1h", "24h", "7d")
            
        Returns:
            Métriques QoS combinées
        """
        combined_metrics = {
            "interface_id": interface_id,
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "sources": [],
            "metrics": {}
        }
        
        # Collecter les données de toutes les sources disponibles
        for source_name, adapter in self.adapter_priority:
            try:
                metrics = adapter.get_qos_metrics(interface_id, time_range)
                if metrics and metrics.get("success", True):
                    combined_metrics["sources"].append({
                        "name": source_name,
                        "status": "success",
                        "data": metrics
                    })
                    
                    # Fusionner les métriques avec priorité aux sources plus fiables
                    if not combined_metrics["metrics"]:
                        combined_metrics["metrics"] = metrics.get("metrics", {})
                    else:
                        # Compléter avec les données manquantes
                        source_metrics = metrics.get("metrics", {})
                        for key, value in source_metrics.items():
                            if key not in combined_metrics["metrics"]:
                                combined_metrics["metrics"][key] = value
                                
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des métriques QoS depuis {source_name}: {e}")
                combined_metrics["sources"].append({
                    "name": source_name,
                    "status": "error",
                    "error": str(e)
                })
        
        combined_metrics["success"] = len([s for s in combined_metrics["sources"] if s["status"] == "success"]) > 0
        return combined_metrics
    
    def get_traffic_statistics(self, device_ids: Optional[List[int]] = None, 
                             period: str = "1h") -> Dict[str, Any]:
        """
        Récupère les statistiques de trafic depuis plusieurs sources.
        
        Args:
            device_ids: Liste des IDs d'équipements
            period: Période de temps
            
        Returns:
            Statistiques de trafic combinées
        """
        combined_stats = {
            "device_ids": device_ids,
            "period": period,
            "timestamp": datetime.now().isoformat(),
            "sources": [],
            "statistics": {}
        }
        
        # Collecter les statistiques de toutes les sources
        for source_name, adapter in self.adapter_priority:
            try:
                stats = adapter.get_traffic_statistics(device_ids, period)
                if stats and stats.get("success", True):
                    combined_stats["sources"].append({
                        "name": source_name,
                        "status": "success",
                        "data": stats
                    })
                    
                    # Fusionner les statistiques
                    if not combined_stats["statistics"]:
                        combined_stats["statistics"] = stats.get("statistics", {})
                    else:
                        source_stats = stats.get("statistics", {})
                        for key, value in source_stats.items():
                            if key not in combined_stats["statistics"]:
                                combined_stats["statistics"][key] = value
                                
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des statistiques depuis {source_name}: {e}")
                combined_stats["sources"].append({
                    "name": source_name,
                    "status": "error",
                    "error": str(e)
                })
        
        combined_stats["success"] = len([s for s in combined_stats["sources"] if s["status"] == "success"]) > 0
        return combined_stats
    
    def get_bandwidth_utilization(self, interface_ids: List[int], 
                                time_range: str = "1h") -> Dict[str, Any]:
        """
        Récupère l'utilisation de la bande passante depuis la source la plus fiable.
        
        Args:
            interface_ids: Liste des IDs d'interfaces
            time_range: Période de temps
            
        Returns:
            Utilisation de la bande passante
        """
        # Essayer chaque source par ordre de priorité
        for source_name, adapter in self.adapter_priority:
            try:
                utilization = adapter.get_bandwidth_utilization(interface_ids, time_range)
                if utilization and utilization.get("success", True):
                    utilization["source"] = source_name
                    return utilization
            except Exception as e:
                logger.warning(f"Échec de récupération depuis {source_name}: {e}")
                continue
        
        # Si aucune source n'est disponible, retourner des données par défaut
        return {
            "interface_ids": interface_ids,
            "time_range": time_range,
            "timestamp": datetime.now().isoformat(),
            "source": "none",
            "success": False,
            "error": "Aucune source de monitoring disponible",
            "utilization": {}
        }
    
    def get_qos_report(self, device_ids: Optional[List[int]] = None, 
                      period: str = "7d") -> Dict[str, Any]:
        """
        Génère un rapport QoS complet en combinant toutes les sources.
        
        Args:
            device_ids: Liste des IDs d'équipements
            period: Période du rapport
            
        Returns:
            Rapport QoS complet
        """
        report = {
            "device_ids": device_ids,
            "period": period,
            "timestamp": datetime.now().isoformat(),
            "source": "composite",
            "sources_status": {},
            "summary": {},
            "details": {}
        }
        
        # Collecter les rapports de toutes les sources
        for source_name, adapter in self.adapter_priority:
            try:
                source_report = adapter.get_qos_report(device_ids, period)
                if source_report:
                    report["sources_status"][source_name] = "success"
                    
                    # Fusionner les données du rapport
                    if "summary" in source_report:
                        report["summary"][source_name] = source_report["summary"]
                    
                    if "details" in source_report:
                        report["details"][source_name] = source_report["details"]
                        
            except Exception as e:
                logger.error(f"Erreur lors de la génération du rapport depuis {source_name}: {e}")
                report["sources_status"][source_name] = f"error: {str(e)}"
        
        # Générer un résumé global
        successful_sources = [s for s, status in report["sources_status"].items() if status == "success"]
        report["global_summary"] = {
            "successful_sources": len(successful_sources),
            "total_sources": len(self.adapter_priority),
            "reliability": len(successful_sources) / len(self.adapter_priority),
            "primary_source": successful_sources[0] if successful_sources else None
        }
        
        return report