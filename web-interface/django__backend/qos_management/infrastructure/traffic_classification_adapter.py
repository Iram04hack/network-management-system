"""
Adaptateur pour la classification de trafic.

Ce module fournit une implémentation de l'interface TrafficClassificationService
pour classifier le trafic réseau et suggérer des politiques QoS appropriées.
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
from datetime import datetime

from ..domain.interfaces import TrafficClassificationService
from ..domain.exceptions import QoSValidationException

logger = logging.getLogger(__name__)


class TrafficClassificationAdapter(TrafficClassificationService):
    """
    Adaptateur pour la classification de trafic réseau.
    
    Cette classe implémente l'interface TrafficClassificationService
    pour classifier le trafic réseau et suggérer des politiques QoS.
    """
    
    # Mapping des ports vers les classes de trafic
    PORT_TO_CLASS = {
        # VoIP/Temps réel
        5060: "voice",     # SIP
        5061: "voice",     # SIP over TLS
        1720: "voice",     # H.323
        1719: "voice",     # H.323 RAS
        4569: "voice",     # Asterisk IAX
        
        # Vidéo
        1935: "video",     # RTMP
        554: "video",      # RTSP
        5004: "video",     # RTP Video
        5005: "video",     # RTCP Video
        
        # Données critiques
        22: "critical_data",    # SSH
        23: "critical_data",    # Telnet
        161: "critical_data",   # SNMP
        162: "critical_data",   # SNMP Trap
        3389: "critical_data",  # RDP
        5900: "critical_data",  # VNC
        
        # Web et applications
        80: "business_data",    # HTTP
        443: "business_data",   # HTTPS
        8080: "business_data",  # HTTP alternate
        8443: "business_data",  # HTTPS alternate
        
        # Email
        25: "business_data",    # SMTP
        110: "business_data",   # POP3
        143: "business_data",   # IMAP
        993: "business_data",   # IMAPS
        995: "business_data",   # POP3S
        
        # Transfert de fichiers
        20: "bulk_data",        # FTP Data
        21: "bulk_data",        # FTP Control
        69: "bulk_data",        # TFTP
        
        # P2P et divertissement
        6881: "best_effort",    # BitTorrent
        6882: "best_effort",    # BitTorrent
        6883: "best_effort",    # BitTorrent
        6884: "best_effort",    # BitTorrent
        6885: "best_effort",    # BitTorrent
    }
    
    # Configuration par défaut des classes de trafic
    TRAFFIC_CLASS_CONFIG = {
        "voice": {
            "priority": 7,
            "max_latency": 150,        # ms
            "max_jitter": 30,          # ms
            "max_packet_loss": 1.0,    # %
            "guaranteed_bandwidth": 64,  # Kbps
            "dscp": "EF",              # Expedited Forwarding
            "description": "Trafic VoIP temps réel"
        },
        "video": {
            "priority": 6,
            "max_latency": 300,        # ms
            "max_jitter": 50,          # ms
            "max_packet_loss": 2.0,    # %
            "guaranteed_bandwidth": 512,  # Kbps
            "dscp": "AF41",            # Assured Forwarding
            "description": "Trafic vidéo en streaming"
        },
        "critical_data": {
            "priority": 5,
            "max_latency": 500,        # ms
            "max_jitter": 100,         # ms
            "max_packet_loss": 0.5,    # %
            "guaranteed_bandwidth": 128,  # Kbps
            "dscp": "AF31",            # Assured Forwarding
            "description": "Données critiques (management, monitoring)"
        },
        "business_data": {
            "priority": 4,
            "max_latency": 1000,       # ms
            "max_jitter": 200,         # ms
            "max_packet_loss": 1.0,    # %
            "guaranteed_bandwidth": 256,  # Kbps
            "dscp": "AF21",            # Assured Forwarding
            "description": "Données métier (web, email, applications)"
        },
        "bulk_data": {
            "priority": 2,
            "max_latency": 5000,       # ms
            "max_jitter": 1000,        # ms
            "max_packet_loss": 5.0,    # %
            "guaranteed_bandwidth": 0,  # Kbps
            "dscp": "AF11",            # Assured Forwarding
            "description": "Transferts de fichiers volumineux"
        },
        "best_effort": {
            "priority": 1,
            "max_latency": 10000,      # ms
            "max_jitter": 2000,        # ms
            "max_packet_loss": 10.0,   # %
            "guaranteed_bandwidth": 0,  # Kbps
            "dscp": "BE",              # Best Effort
            "description": "Trafic non critique (P2P, divertissement)"
        }
    }
    
    def __init__(self):
        """Initialise l'adaptateur de classification de trafic."""
        pass
    
    def classify_traffic(self, traffic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classifie le trafic réseau selon ses caractéristiques.
        
        Args:
            traffic_data: Données de trafic à classifier
                - protocol: Protocole (TCP, UDP, ICMP)
                - source_ip: IP source
                - destination_ip: IP destination
                - source_port: Port source
                - destination_port: Port destination
                - payload: Charge utile (optionnel)
                - packet_size: Taille du paquet
                - flags: Flags TCP (optionnel)
            
        Returns:
            Classification du trafic avec classe et confiance
        """
        try:
            # Extraire les informations de base
            protocol = traffic_data.get("protocol", "").upper()
            src_port = traffic_data.get("source_port", 0)
            dst_port = traffic_data.get("destination_port", 0)
            payload = traffic_data.get("payload", "")
            packet_size = traffic_data.get("packet_size", 0)
            
            # Classification par port
            port_classification = self._classify_by_port(src_port, dst_port)
            
            # Classification par pattern de trafic
            pattern_classification = self._classify_by_pattern(traffic_data)
            
            # Combiner les résultats
            final_class, confidence = self._combine_classifications([
                port_classification,
                pattern_classification
            ])
            
            # Calculer les métriques de qualité
            quality_metrics = self._calculate_quality_metrics(final_class, traffic_data)
            
            return {
                "traffic_class": final_class,
                "confidence": confidence,
                "classification_methods": {
                    "port_based": port_classification,
                    "pattern_based": pattern_classification
                },
                "quality_requirements": quality_metrics,
                "suggested_dscp": self.TRAFFIC_CLASS_CONFIG.get(final_class, {}).get("dscp", "BE"),
                "priority": self.TRAFFIC_CLASS_CONFIG.get(final_class, {}).get("priority", 1),
                "description": self.TRAFFIC_CLASS_CONFIG.get(final_class, {}).get("description", "Trafic non classifié")
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la classification du trafic: {e}")
            return {
                "traffic_class": "best_effort",
                "confidence": 0.0,
                "error": str(e),
                "quality_requirements": self.TRAFFIC_CLASS_CONFIG["best_effort"]
            }
    
    def suggest_qos_policy(self, traffic_class: str) -> Dict[str, Any]:
        """
        Suggère une politique QoS adaptée à une classe de trafic.
        
        Args:
            traffic_class: Classe de trafic
            
        Returns:
            Politique QoS suggérée
        """
        if traffic_class not in self.TRAFFIC_CLASS_CONFIG:
            raise QoSValidationException(
                f"Classe de trafic inconnue: {traffic_class}",
                "unknown_traffic_class",
                {"available_classes": list(self.TRAFFIC_CLASS_CONFIG.keys())}
            )
        
        config = self.TRAFFIC_CLASS_CONFIG[traffic_class]
        
        # Générer une politique QoS basique
        policy = {
            "name": f"Policy_{traffic_class}",
            "description": f"Politique QoS automatique pour {config['description']}",
            "traffic_class": traffic_class,
            "priority": config["priority"],
            "dscp_marking": config["dscp"],
            "bandwidth_allocation": {
                "guaranteed_min": config.get("guaranteed_bandwidth", 0),
                "max_burst": self._calculate_burst_size(traffic_class),
                "shaping_rate": self._calculate_shaping_rate(traffic_class)
            },
            "quality_requirements": {
                "max_latency_ms": config["max_latency"],
                "max_jitter_ms": config["max_jitter"],
                "max_packet_loss_percent": config["max_packet_loss"]
            },
            "queue_management": {
                "algorithm": self._suggest_queue_algorithm(traffic_class),
                "queue_depth": self._suggest_queue_depth(traffic_class),
                "drop_policy": self._suggest_drop_policy(traffic_class)
            }
        }
        
        return policy
    
    def get_traffic_classes(self) -> List[str]:
        """
        Récupère la liste des classes de trafic disponibles.
        
        Returns:
            Liste des classes de trafic
        """
        return list(self.TRAFFIC_CLASS_CONFIG.keys())
    
    def _classify_by_port(self, src_port: int, dst_port: int) -> Tuple[str, float]:
        """
        Classifie le trafic basé sur les ports source et destination.
        
        Args:
            src_port: Port source
            dst_port: Port destination
            
        Returns:
            Tuple (classe, confiance)
        """
        # Vérifier le port de destination d'abord (plus fiable)
        if dst_port in self.PORT_TO_CLASS:
            return self.PORT_TO_CLASS[dst_port], 0.8
        
        # Vérifier le port source
        if src_port in self.PORT_TO_CLASS:
            return self.PORT_TO_CLASS[src_port], 0.6
        
        # Ports dynamiques/éphémères
        if dst_port >= 1024:
            return "best_effort", 0.3
        
        return "best_effort", 0.1
    
    def _classify_by_pattern(self, traffic_data: Dict[str, Any]) -> Tuple[str, float]:
        """
        Classifie le trafic basé sur les patterns de comportement.
        
        Args:
            traffic_data: Données complètes du trafic
            
        Returns:
            Tuple (classe, confiance)
        """
        packet_size = traffic_data.get("packet_size", 0)
        protocol = traffic_data.get("protocol", "").upper()
        
        # Petits paquets UDP réguliers = probablement VoIP
        if protocol == "UDP" and packet_size < 200:
            return "voice", 0.7
        
        # Gros paquets TCP = probablement transfert de données
        if protocol == "TCP" and packet_size > 1400:
            return "bulk_data", 0.6
        
        # Paquets moyens TCP = probablement web/business
        if protocol == "TCP" and 500 <= packet_size <= 1400:
            return "business_data", 0.5
        
        return "best_effort", 0.3
    
    def _combine_classifications(self, classifications: List[Tuple[str, float]]) -> Tuple[str, float]:
        """
        Combine plusieurs résultats de classification.
        
        Args:
            classifications: Liste de tuples (classe, confiance)
            
        Returns:
            Tuple (classe finale, confiance combinée)
        """
        if not classifications:
            return "best_effort", 0.0
        
        # Calculer un score pondéré pour chaque classe
        class_scores = defaultdict(float)
        total_weight = 0
        
        for traffic_class, confidence in classifications:
            weight = confidence
            class_scores[traffic_class] += weight
            total_weight += weight
        
        if total_weight == 0:
            return "best_effort", 0.0
        
        # Normaliser les scores
        for traffic_class in class_scores:
            class_scores[traffic_class] /= total_weight
        
        # Retourner la classe avec le score le plus élevé
        best_class = max(class_scores.items(), key=lambda x: x[1])
        return best_class[0], best_class[1]
    
    def _calculate_quality_metrics(self, traffic_class: str, traffic_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcule les métriques de qualité requises pour une classe de trafic.
        
        Args:
            traffic_class: Classe de trafic
            traffic_data: Données du trafic
            
        Returns:
            Métriques de qualité
        """
        base_config = self.TRAFFIC_CLASS_CONFIG.get(traffic_class, self.TRAFFIC_CLASS_CONFIG["best_effort"])
        
        # Ajuster selon les caractéristiques du trafic
        packet_size = traffic_data.get("packet_size", 1500)
        
        # Calculer la bande passante recommandée
        bandwidth = base_config.get("guaranteed_bandwidth", 0)
        if traffic_class == "voice":
            # Estimer selon la taille des paquets (codec)
            if packet_size < 100:
                bandwidth = 64  # G.729
            elif packet_size < 200:
                bandwidth = 128  # G.711
            else:
                bandwidth = 256  # HD Voice
        elif traffic_class == "video":
            # Estimer selon la taille des paquets
            if packet_size < 500:
                bandwidth = 512   # SD
            elif packet_size < 1000:
                bandwidth = 2048  # HD
            else:
                bandwidth = 8192  # 4K
        
        return {
            **base_config,
            "recommended_bandwidth_kbps": bandwidth,
            "estimated_packet_rate": self._estimate_packet_rate(traffic_class, packet_size)
        }
    
    def _estimate_packet_rate(self, traffic_class: str, packet_size: int) -> int:
        """
        Estime le taux de paquets par seconde pour une classe de trafic.
        """
        if traffic_class == "voice":
            return 50  # Typique pour VoIP (20ms interval)
        elif traffic_class == "video":
            return 30  # Typique pour vidéo
        elif packet_size > 1400:
            return 10  # Gros paquets, probablement moins fréquents
        else:
            return 20  # Taux moyen
    
    def _suggest_queue_algorithm(self, traffic_class: str) -> str:
        """Suggère un algorithme de file d'attente."""
        if traffic_class in ["voice", "video"]:
            return "PQ"  # Priority Queue
        elif traffic_class == "critical_data":
            return "WFQ"  # Weighted Fair Queue
        else:
            return "FIFO"  # First In First Out
    
    def _suggest_queue_depth(self, traffic_class: str) -> int:
        """Suggère une profondeur de file d'attente."""
        depths = {
            "voice": 10,
            "video": 20,
            "critical_data": 30,
            "business_data": 50,
            "bulk_data": 100,
            "best_effort": 200
        }
        return depths.get(traffic_class, 50)
    
    def _suggest_drop_policy(self, traffic_class: str) -> str:
        """Suggère une politique de suppression de paquets."""
        if traffic_class in ["voice", "video"]:
            return "tail_drop"
        else:
            return "random_early_detection"
    
    def _calculate_burst_size(self, traffic_class: str) -> int:
        """Calcule la taille de burst appropriée."""
        bursts = {
            "voice": 1500,
            "video": 15000,
            "critical_data": 10000,
            "business_data": 50000,
            "bulk_data": 100000,
            "best_effort": 200000
        }
        return bursts.get(traffic_class, 50000)
    
    def _calculate_shaping_rate(self, traffic_class: str) -> Optional[int]:
        """Calcule le taux de mise en forme."""
        if traffic_class in ["bulk_data", "best_effort"]:
            return 10000  # 10 Mbps
        return None