"""
Cas d'utilisation pour les tests de conformité QoS.

Ce module contient les cas d'utilisation pour tester la conformité des politiques QoS
aux exigences de qualité de service.
"""
import logging
import time
import subprocess
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import statistics

from qos_management.domain.entities import QoSPolicyEntity
from qos_management.domain.interfaces import QoSMonitoringService

logger = logging.getLogger(__name__)

@dataclass
class TrafficProfile:
    """
    Profil de trafic pour les tests de conformité QoS.
    """
    name: str
    protocol: str
    port: int
    bandwidth: int  # en kbps
    packet_size: int = 64  # en octets
    duration: int = 10  # en secondes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            'name': self.name,
            'protocol': self.protocol,
            'port': self.port,
            'bandwidth': self.bandwidth,
            'packet_size': self.packet_size,
            'duration': self.duration
        }

@dataclass
class ExpectedMetrics:
    """
    Métriques attendues pour les tests de conformité QoS.
    """
    max_latency: float  # en ms
    max_jitter: float  # en ms
    max_packet_loss: float  # en pourcentage (0-1)
    min_bandwidth: int  # en kbps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            'max_latency': self.max_latency,
            'max_jitter': self.max_jitter,
            'max_packet_loss': self.max_packet_loss,
            'min_bandwidth': self.min_bandwidth
        }

@dataclass
class QoSTestScenario:
    """
    Scénario de test de conformité QoS.
    """
    name: str
    traffic_profile: TrafficProfile
    expected_metrics: ExpectedMetrics
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            'name': self.name,
            'description': self.description,
            'traffic_profile': self.traffic_profile.to_dict(),
            'expected_metrics': self.expected_metrics.to_dict()
        }

@dataclass
class QoSTestResult:
    """
    Résultat d'un test de conformité QoS.
    """
    scenario: QoSTestScenario
    success: bool
    actual_metrics: Dict[str, Any]
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'objet en dictionnaire."""
        return {
            'scenario': self.scenario.to_dict(),
            'success': self.success,
            'actual_metrics': self.actual_metrics,
            'details': self.details
        }

class TrafficGenerator:
    """
    Générateur de trafic pour les tests de conformité QoS.
    
    Cette classe est un stub pour les tests unitaires.
    Dans une implémentation réelle, elle utiliserait des outils comme iperf ou netperf.
    """
    
    def __init__(self, target_ip: str, profile: TrafficProfile):
        """
        Initialise le générateur de trafic.
        
        Args:
            target_ip: Adresse IP cible
            profile: Profil de trafic
        """
        self.target_ip = target_ip
        self.profile = profile
        self.running = False
    
    def start(self) -> bool:
        """
        Démarre la génération de trafic.
        
        Returns:
            True si le démarrage a réussi, False sinon
        """
        # Dans une implémentation réelle, cette méthode lancerait un outil comme iperf
        # Pour les tests unitaires, on simule un démarrage réussi
        self.running = True
        return True
    
    def stop(self) -> None:
        """
        Arrête la génération de trafic.
        """
        # Dans une implémentation réelle, cette méthode arrêterait l'outil de génération de trafic
        self.running = False

class QoSComplianceTestingUseCase:
    """
    Cas d'utilisation pour les tests de conformité QoS.
    """
    
    def __init__(self, qos_monitoring_service):
        """
        Initialise le cas d'utilisation.
        
        Args:
            qos_monitoring_service: Service de surveillance QoS
        """
        self.qos_monitoring_service = qos_monitoring_service
    
    def run_test(
        self,
        policy: QoSPolicyEntity,
        scenario: QoSTestScenario,
        target_ip: str,
        interface_name: str
    ) -> QoSTestResult:
        """
        Exécute un test de conformité QoS.
        
        Args:
            policy: Politique QoS à tester
            scenario: Scénario de test
            target_ip: Adresse IP cible
            interface_name: Nom de l'interface réseau
            
        Returns:
            Résultat du test
        """
        # Créer un générateur de trafic
        traffic_generator = TrafficGenerator(target_ip, scenario.traffic_profile)
        
        # Démarrer la génération de trafic
        if not traffic_generator.start():
            # Échec du démarrage du générateur
            return QoSTestResult(
                scenario=scenario,
                success=False,
                actual_metrics={},
                details={'error': "Échec du démarrage du générateur de trafic"}
            )
        
        try:
            # Collecter des métriques pendant la durée du test
            metrics_samples = []
            duration = scenario.traffic_profile.duration
            interval = 1  # Intervalle de collecte en secondes
            
            for _ in range(duration):
                # Collecter les métriques
                metrics_response = self.qos_monitoring_service.get_interface_metrics(
                    interface_name=interface_name
                )
                
                if metrics_response.get('success', False):
                    metrics_samples.append(metrics_response)
                
                # Attendre l'intervalle
                time.sleep(interval)
            
            # Analyser les métriques collectées
            if not metrics_samples:
                return QoSTestResult(
                    scenario=scenario,
                    success=False,
                    actual_metrics={},
                    details={'error': "Aucune métrique collectée"}
                )
            
            actual_metrics = self._analyze_metrics(metrics_samples)
            
            # Vérifier la conformité
            success, details = self._check_compliance(actual_metrics, scenario.expected_metrics)
            
            return QoSTestResult(
                scenario=scenario,
                success=success,
                actual_metrics=actual_metrics,
                details=details
            )
        finally:
            # Arrêter la génération de trafic
            traffic_generator.stop()
    
    def _analyze_metrics(self, metrics_samples: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse les métriques collectées.
        
        Args:
            metrics_samples: Liste des échantillons de métriques
            
        Returns:
            Métriques analysées
        """
        latencies = []
        jitters = []
        packet_losses = []
        bandwidths = []
        
        for sample in metrics_samples:
            metrics = sample.get('metrics', {})
            qos_stats = metrics.get('qos_stats', {})
            
            # Collecter les métriques QoS
            if 'latency' in qos_stats:
                latencies.append(qos_stats['latency'])
            
            if 'jitter' in qos_stats:
                jitters.append(qos_stats['jitter'])
            
            if 'packet_loss' in qos_stats:
                packet_losses.append(qos_stats['packet_loss'])
            
            # Collecter les métriques de bande passante
            if 'bandwidth' in metrics and 'tx' in metrics['bandwidth']:
                # Convertir de bps en kbps
                bandwidth_kbps = metrics['bandwidth']['tx'][0]['value'] / 1000
                bandwidths.append(bandwidth_kbps)
        
        result = {}
        
        # Calculer les statistiques
        if latencies:
            result['avg_latency'] = statistics.mean(latencies)
            result['max_latency'] = max(latencies)
        
        if jitters:
            result['avg_jitter'] = statistics.mean(jitters)
            result['max_jitter'] = max(jitters)
        
        if packet_losses:
            result['avg_packet_loss'] = statistics.mean(packet_losses)
            result['max_packet_loss'] = max(packet_losses)
        
        if bandwidths:
            result['avg_bandwidth'] = statistics.mean(bandwidths)
            result['min_bandwidth'] = min(bandwidths)
        
        return result
    
    def _check_compliance(
        self,
        actual_metrics: Dict[str, Any],
        expected_metrics: ExpectedMetrics
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Vérifie la conformité des métriques par rapport aux attentes.
        
        Args:
            actual_metrics: Métriques réelles
            expected_metrics: Métriques attendues
            
        Returns:
            Tuple (succès, détails)
        """
        details = {}
        all_passed = True
        
        # Vérifier la latence
        if 'max_latency' in actual_metrics:
            latency_passed = actual_metrics['max_latency'] <= expected_metrics.max_latency
            details['latency'] = {
                'status': 'passed' if latency_passed else 'failed',
                'actual': actual_metrics['max_latency'],
                'expected': expected_metrics.max_latency
            }
            all_passed = all_passed and latency_passed
        
        # Vérifier le jitter
        if 'max_jitter' in actual_metrics:
            jitter_passed = actual_metrics['max_jitter'] <= expected_metrics.max_jitter
            details['jitter'] = {
                'status': 'passed' if jitter_passed else 'failed',
                'actual': actual_metrics['max_jitter'],
                'expected': expected_metrics.max_jitter
            }
            all_passed = all_passed and jitter_passed
        
        # Vérifier la perte de paquets
        if 'max_packet_loss' in actual_metrics:
            packet_loss_passed = actual_metrics['max_packet_loss'] <= expected_metrics.max_packet_loss
            details['packet_loss'] = {
                'status': 'passed' if packet_loss_passed else 'failed',
                'actual': actual_metrics['max_packet_loss'],
                'expected': expected_metrics.max_packet_loss
            }
            all_passed = all_passed and packet_loss_passed
        
        # Vérifier la bande passante
        if 'min_bandwidth' in actual_metrics:
            bandwidth_passed = actual_metrics['min_bandwidth'] >= expected_metrics.min_bandwidth
            details['bandwidth'] = {
                'status': 'passed' if bandwidth_passed else 'failed',
                'actual': actual_metrics['min_bandwidth'],
                'expected': expected_metrics.min_bandwidth
            }
            all_passed = all_passed and bandwidth_passed
        
        return all_passed, details 