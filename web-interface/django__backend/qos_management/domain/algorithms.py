"""
Algorithmes avancés pour la gestion de la qualité de service (QoS).

Ce module contient l'implémentation des algorithmes avancés pour la gestion 
des files d'attente et l'allocation de bande passante dans le cadre des 
politiques QoS.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
import math

from .entities import QoSPolicy, TrafficClass


class QueueAlgorithmType(str, Enum):
    """Types d'algorithmes de files d'attente supportés."""
    FIFO = "fifo"                   # First In, First Out
    PQ = "priority_queuing"         # Priority Queuing
    CQ = "custom_queuing"           # Custom Queuing
    FQ = "fair_queuing"             # Fair Queuing
    WFQ = "weighted_fair_queuing"   # Weighted Fair Queuing
    CBWFQ = "class_based_wfq"       # Class-Based Weighted Fair Queuing
    LLQ = "low_latency_queuing"     # Low Latency Queuing
    MDRR = "modified_drr"           # Modified Deficit Round Robin
    FQ_CODEL = "fq_codel"          # Flow Queue Controlled Delay
    DRR = "deficit_round_robin"     # Deficit Round Robin


class CongestionAlgorithmType(str, Enum):
    """Types d'algorithmes d'évitement de congestion supportés."""
    TAIL_DROP = "tail_drop"         # Tail Drop (défaut)
    RED = "random_early_detection"  # Random Early Detection
    WRED = "weighted_red"           # Weighted Random Early Detection
    ECN = "explicit_congestion"     # Explicit Congestion Notification


@dataclass
class QueueParameters:
    """Paramètres pour la configuration d'une file d'attente."""
    buffer_size: int                # Taille du buffer en paquets
    queue_limit: int                # Limite de la file d'attente
    service_rate: int               # Taux de service en kbps
    weight: float = 1.0             # Poids relatif (utilisé par WFQ, CBWFQ)
    priority_level: int = 0         # Niveau de priorité (0 = pas de priorité)
    bandwidth_percent: float = 0.0  # Pourcentage de bande passante garanti


@dataclass
class CongestionParameters:
    """Paramètres pour la configuration de l'évitement de congestion."""
    algorithm: CongestionAlgorithmType = CongestionAlgorithmType.TAIL_DROP
    min_threshold: int = 0          # Seuil minimum pour RED/WRED (en paquets)
    max_threshold: int = 0          # Seuil maximum pour RED/WRED (en paquets)
    drop_probability: float = 0.0   # Probabilité de rejet maximale (0.0-1.0)
    dscp_weights: Dict[str, float] = None  # Poids par DSCP pour WRED


@dataclass
class QueueConfiguration:
    """Configuration complète d'une file d'attente."""
    traffic_class: TrafficClass
    queue_params: QueueParameters
    congestion_params: Optional[CongestionParameters] = None


class QueueAlgorithm(ABC):
    """
    Interface abstraite pour les algorithmes de files d'attente.
    
    Cette classe définit le contrat commun pour tous les algorithmes 
    de gestion de files d'attente.
    """
    
    @abstractmethod
    def calculate_parameters(self, policy: QoSPolicy) -> List[QueueConfiguration]:
        """
        Calcule les paramètres optimaux pour chaque classe de trafic.
        
        Args:
            policy: Politique QoS contenant les classes de trafic
            
        Returns:
            Liste de configurations de file pour chaque classe
        """
        pass


class CBWFQAlgorithm(QueueAlgorithm):
    """
    Algorithme Class-Based Weighted Fair Queuing (CBWFQ).
    
    CBWFQ étend l'algorithme WFQ pour prendre en charge plusieurs classes
    de trafic avec des garanties de bande passante minimales.
    """
    
    def calculate_parameters(self, policy: QoSPolicy) -> List[QueueConfiguration]:
        """
        Calcule les paramètres CBWFQ pour chaque classe de trafic.
        
        Args:
            policy: Politique QoS contenant les classes de trafic
            
        Returns:
            Liste de configurations de file pour chaque classe
        """
        total_bandwidth = policy.bandwidth_limit
        total_min_bandwidth = sum(tc.min_bandwidth for tc in policy.traffic_classes)
        
        # Vérification que la somme des garanties ne dépasse pas la bande passante totale
        if total_min_bandwidth > total_bandwidth:
            raise ValueError(
                f"La somme des bandes passantes garanties ({total_min_bandwidth} kbps) "
                f"excède la limite de bande passante ({total_bandwidth} kbps)"
            )
        
        # Bande passante restante à distribuer selon les poids
        remaining_bandwidth = total_bandwidth - total_min_bandwidth
        
        # Calcul des poids relatifs basés sur la priorité et les besoins en bande passante
        configurations = []
        
        for tc in sorted(policy.traffic_classes, key=lambda x: x.priority, reverse=True):
            # Garantir le minimum de bande passante
            min_bw = tc.min_bandwidth
            
            # Calculer le poids pour la bande passante restante
            # Les classes de priorité plus élevée reçoivent un poids plus important
            weight = self._calculate_weight(tc, policy.traffic_classes)
            
            # Calcul du pourcentage de bande passante garanti
            bw_percent = (min_bw / total_bandwidth) * 100 if total_bandwidth > 0 else 0
            
            # Paramètres de la file d'attente
            queue_params = QueueParameters(
                buffer_size=self._calculate_buffer_size(min_bw, tc.burst),
                queue_limit=self._calculate_queue_limit(min_bw),
                service_rate=min_bw,
                weight=weight,
                priority_level=tc.priority,
                bandwidth_percent=bw_percent
            )
            
            # Paramètres d'évitement de congestion basés sur DSCP
            if tc.dscp != 'default':
                congestion_params = CongestionParameters(
                    algorithm=CongestionAlgorithmType.WRED,
                    min_threshold=self._calculate_min_threshold(min_bw),
                    max_threshold=self._calculate_max_threshold(min_bw),
                    drop_probability=0.1,  # 10% par défaut
                    dscp_weights={tc.dscp: 1.0}
                )
            else:
                congestion_params = CongestionParameters()
            
            configurations.append(QueueConfiguration(
                traffic_class=tc,
                queue_params=queue_params,
                congestion_params=congestion_params
            ))
        
        return configurations
    
    def _calculate_weight(self, traffic_class: TrafficClass, all_classes: List[TrafficClass]) -> float:
        """
        Calcule le poids relatif d'une classe de trafic pour l'algorithme CBWFQ.
        
        Args:
            traffic_class: Classe de trafic à évaluer
            all_classes: Toutes les classes de trafic de la politique
            
        Returns:
            Poids relatif (valeur entre 1 et 100)
        """
        # Bases de calcul: priorité et bande passante relative
        priority_factor = traffic_class.priority / max(tc.priority for tc in all_classes) if any(tc.priority > 0 for tc in all_classes) else 1
        bw_factor = traffic_class.min_bandwidth / max(tc.min_bandwidth for tc in all_classes) if any(tc.min_bandwidth > 0 for tc in all_classes) else 1
        
        # Combinaison des facteurs (70% priorité, 30% bande passante)
        weight = (priority_factor * 0.7 + bw_factor * 0.3) * 100
        
        # Assurer une valeur minimale de 1
        return max(1, min(weight, 100))
    
    def _calculate_buffer_size(self, bandwidth: int, burst: int) -> int:
        """
        Calcule la taille optimale du buffer en fonction de la bande passante et du burst.
        
        Args:
            bandwidth: Bande passante en kbps
            burst: Taille du burst en kb
            
        Returns:
            Taille du buffer en paquets
        """
        # Si le burst est spécifié, l'utiliser comme base
        if burst > 0:
            # Conversion du burst en nombre approximatif de paquets (assumant 1.5KB par paquet en moyenne)
            return math.ceil(burst / 1.5)
        
        # Sinon, calculer en fonction de la bande passante
        # Formule: (Bande passante en kbps * 0.1s) / 12 kbits par paquet
        # Cette formule donne un buffer capable de gérer 100ms de trafic
        return max(16, math.ceil((bandwidth * 0.1) / 12))
    
    def _calculate_queue_limit(self, bandwidth: int) -> int:
        """
        Calcule la limite de la file d'attente en fonction de la bande passante.
        
        Args:
            bandwidth: Bande passante en kbps
            
        Returns:
            Limite de la file en paquets
        """
        # Formule empirique basée sur la bande passante
        # Minimum de 64 paquets, maximum de 4096
        return max(64, min(4096, bandwidth // 8))
    
    def _calculate_min_threshold(self, bandwidth: int) -> int:
        """
        Calcule le seuil minimum pour RED/WRED en fonction de la bande passante.
        
        Args:
            bandwidth: Bande passante en kbps
            
        Returns:
            Seuil minimum en paquets
        """
        # 25% de la limite de la file
        return self._calculate_queue_limit(bandwidth) // 4
    
    def _calculate_max_threshold(self, bandwidth: int) -> int:
        """
        Calcule le seuil maximum pour RED/WRED en fonction de la bande passante.
        
        Args:
            bandwidth: Bande passante en kbps
            
        Returns:
            Seuil maximum en paquets
        """
        # 75% de la limite de la file
        return self._calculate_queue_limit(bandwidth) * 3 // 4


class LowLatencyQueueingAlgorithm(CBWFQAlgorithm):
    """
    Algorithme Low Latency Queuing (LLQ).
    
    LLQ est une extension de CBWFQ qui ajoute une file d'attente à priorité stricte
    pour le trafic sensible à la latence (comme la voix et la vidéo), tout en
    garantissant une bande passante minimale pour les autres classes de trafic.
    """
    
    # Seuil maximum recommandé pour la réservation de bande passante prioritaire
    # (pourcentage de la bande passante totale)
    MAX_PRIORITY_BANDWIDTH_PERCENT = 33
    
    def calculate_parameters(self, policy: QoSPolicy) -> List[QueueConfiguration]:
        """
        Calcule les paramètres LLQ pour chaque classe de trafic.
        
        Args:
            policy: Politique QoS contenant les classes de trafic
            
        Returns:
            Liste de configurations de file pour chaque classe
        """
        total_bandwidth = policy.bandwidth_limit
        
        # Identifier les classes prioritaires (avec priority_level > 0)
        priority_classes = [tc for tc in policy.traffic_classes if tc.priority >= 5]
        standard_classes = [tc for tc in policy.traffic_classes if tc.priority < 5]
        
        # Calculer la bande passante totale réservée pour les classes prioritaires
        priority_bandwidth = sum(tc.min_bandwidth for tc in priority_classes)
        
        # Vérifier que les classes prioritaires ne dépassent pas la limite recommandée
        priority_percent = (priority_bandwidth / total_bandwidth * 100) if total_bandwidth > 0 else 0
        if priority_percent > self.MAX_PRIORITY_BANDWIDTH_PERCENT:
            raise ValueError(
                f"La bande passante totale réservée pour les classes prioritaires ({priority_percent:.1f}%) "
                f"dépasse la limite recommandée ({self.MAX_PRIORITY_BANDWIDTH_PERCENT}%)"
            )
        
        # Calculer la bande passante disponible pour les classes standard
        standard_bandwidth = total_bandwidth - priority_bandwidth
        total_standard_min_bandwidth = sum(tc.min_bandwidth for tc in standard_classes)
        
        if total_standard_min_bandwidth > standard_bandwidth:
            raise ValueError(
                f"La somme des bandes passantes garanties pour les classes non prioritaires "
                f"({total_standard_min_bandwidth} kbps) excède la bande passante disponible "
                f"après réservation des files prioritaires ({standard_bandwidth} kbps)"
            )
        
        # Configurer les classes prioritaires avec stricte priorité
        configurations = []
        
        # 1. Traiter d'abord les classes prioritaires avec LLQ
        for priority_level, classes_group in self._group_by_priority(priority_classes).items():
            for tc in classes_group:
                min_bw = tc.min_bandwidth
                burst_tolerance = max(min_bw // 8, 1)  # En kbits
                
                queue_params = QueueParameters(
                    buffer_size=self._calculate_llq_buffer_size(min_bw, tc.burst),
                    queue_limit=self._calculate_llq_queue_limit(min_bw),
                    service_rate=min_bw,
                    weight=0.0,  # Poids non utilisé en mode prioritaire strict
                    priority_level=priority_level,
                    bandwidth_percent=0.0  # Non applicable pour les files LLQ
                )
                
                # Paramètres d'évitement de congestion adaptés à la faible latence
                congestion_params = CongestionParameters(
                    algorithm=CongestionAlgorithmType.TAIL_DROP,  # Pas de RED pour les files prioritaires
                    min_threshold=0,
                    max_threshold=0
                )
                
                configurations.append(QueueConfiguration(
                    traffic_class=tc,
                    queue_params=queue_params,
                    congestion_params=congestion_params
                ))
        
        # 2. Traiter ensuite les classes standard avec CBWFQ classique
        # On réutilise l'implémentation de CBWFQAlgorithm pour les classes standard,
        # mais en tenant compte de la bande passante déjà réservée
        
        # Créer une politique temporaire avec seulement les classes standard
        temp_policy = QoSPolicy(
            id=policy.id,
            name=policy.name,
            description=policy.description,
            bandwidth_limit=standard_bandwidth,  # Bande passante réduite
            is_active=policy.is_active,
            priority=policy.priority,
            traffic_classes=standard_classes
        )
        
        # Utiliser l'algorithme CBWFQ pour les classes standard
        standard_configs = super().calculate_parameters(temp_policy)
        configurations.extend(standard_configs)
        
        return configurations
    
    def _group_by_priority(self, classes: List[TrafficClass]) -> Dict[int, List[TrafficClass]]:
        """
        Regroupe les classes de trafic par niveau de priorité.
        
        Args:
            classes: Liste des classes de trafic à regrouper
            
        Returns:
            Dictionnaire mappant les niveaux de priorité aux classes
        """
        result = {}
        
        for tc in classes:
            if tc.priority not in result:
                result[tc.priority] = []
            result[tc.priority].append(tc)
            
        # Trier par priorité descendante
        return dict(sorted(result.items(), key=lambda item: item[0], reverse=True))
    
    def _calculate_llq_buffer_size(self, bandwidth: int, burst: int) -> int:
        """
        Calcule la taille optimale du buffer pour une file LLQ.
        
        Pour les files LLQ, les buffers sont typiquement plus petits pour minimiser la latence.
        
        Args:
            bandwidth: Bande passante en kbps
            burst: Taille du burst en kb
            
        Returns:
            Taille du buffer en paquets
        """
        # Si le burst est spécifié, l'utiliser comme base
        if burst > 0:
            return math.ceil(burst / 1.5)
        
        # Pour les files LLQ, utiliser un buffer plus petit pour réduire la latence
        # La latence maximale visée est de 50ms au lieu de 100ms
        return max(8, math.ceil((bandwidth * 0.05) / 12))
    
    def _calculate_llq_queue_limit(self, bandwidth: int) -> int:
        """
        Calcule la limite de file d'attente optimale pour une file LLQ.
        
        Pour les files LLQ, les limites sont plus petites pour éviter l'accumulation
        de paquets et réduire la latence.
        
        Args:
            bandwidth: Bande passante en kbps
            
        Returns:
            Limite de la file en paquets
        """
        # Pour les files LLQ, la limite est généralement plus petite
        # Minimum de 32 paquets, maximum de 1024
        return max(32, min(1024, bandwidth // 16))


class RandomEarlyDetectionAlgorithm:
    """
    Implémentation de l'algorithme Random Early Detection (RED).
    
    RED est un algorithme d'évitement de congestion actif qui rejette des paquets
    de manière probabiliste avant que la file d'attente ne soit complètement pleine,
    afin de réguler le débit moyen.
    """
    
    def calculate_drop_probability(
        self,
        queue_occupancy: int,
        min_threshold: int,
        max_threshold: int,
        max_probability: float
    ) -> float:
        """
        Calcule la probabilité de rejet d'un paquet selon l'algorithme RED.
        
        Args:
            queue_occupancy: Occupation actuelle de la file (nombre de paquets)
            min_threshold: Seuil minimum à partir duquel le rejet commence
            max_threshold: Seuil maximum à partir duquel tous les paquets sont rejetés
            max_probability: Probabilité maximale de rejet quand queue_occupancy = max_threshold
            
        Returns:
            Probabilité de rejet du paquet (entre 0.0 et 1.0)
        """
        # Si l'occupation est inférieure au seuil minimum, aucun rejet
        if queue_occupancy <= min_threshold:
            return 0.0
        
        # Si l'occupation est supérieure au seuil maximum, rejet systématique
        if queue_occupancy >= max_threshold:
            return 1.0
        
        # Sinon, calcul linéaire entre les deux seuils
        # La probabilité augmente linéairement de 0 à max_probability
        queue_fraction = (queue_occupancy - min_threshold) / (max_threshold - min_threshold)
        return queue_fraction * max_probability
    
    def calculate_weighted_drop_probability(
        self,
        queue_occupancy: int,
        min_threshold: int,
        max_threshold: int,
        max_probability: float,
        dscp_weight: float
    ) -> float:
        """
        Calcule la probabilité de rejet d'un paquet selon l'algorithme WRED.
        
        WRED est une extension de RED qui prend en compte la priorité du paquet
        (souvent définie par son marquage DSCP) dans le calcul de la probabilité
        de rejet.
        
        Args:
            queue_occupancy: Occupation actuelle de la file (nombre de paquets)
            min_threshold: Seuil minimum à partir duquel le rejet commence
            max_threshold: Seuil maximum à partir duquel tous les paquets sont rejetés
            max_probability: Probabilité maximale de rejet quand queue_occupancy = max_threshold
            dscp_weight: Poids relatif du marquage DSCP (0.0-1.0, plus élevé = moins de rejets)
            
        Returns:
            Probabilité de rejet du paquet (entre 0.0 et 1.0)
        """
        # Calculer la probabilité de base selon RED
        base_probability = self.calculate_drop_probability(
            queue_occupancy, min_threshold, max_threshold, max_probability
        )
        
        # Ajuster en fonction du poids DSCP
        # Les paquets avec un poids plus élevé ont une probabilité de rejet plus faible
        adjusted_probability = base_probability * (1.0 - dscp_weight)
        
        return max(0.0, min(adjusted_probability, 1.0))


class FQCoDelAlgorithm(QueueAlgorithm):
    """
    Algorithme Flow Queue Controlled Delay (FQ-CoDel).
    
    FQ-CoDel combine la gestion de files d'attente équitable (Fair Queuing)
    avec l'algorithme CoDel (Controlled Delay) pour combattre le bufferbloat
    et garantir une faible latence tout en maintenant l'équité entre les flux.
    """
    
    # Paramètres par défaut pour CoDel
    DEFAULT_TARGET_DELAY = 5000  # 5ms en microsecondes
    DEFAULT_INTERVAL = 100000    # 100ms en microserondes
    DEFAULT_QUANTUM = 1514       # MTU Ethernet + headers
    DEFAULT_FLOWS = 1024         # Nombre de files par défaut
    
    def calculate_parameters(self, policy: QoSPolicy) -> List[QueueConfiguration]:
        """
        Calcule les paramètres FQ-CoDel pour chaque classe de trafic.
        
        Args:
            policy: Politique QoS contenant les classes de trafic
            
        Returns:
            Liste de configurations de file pour chaque classe
        """
        total_bandwidth = policy.bandwidth_limit
        configurations = []
        
        # Calculer le quantum de base selon la bande passante totale
        base_quantum = self._calculate_base_quantum(total_bandwidth)
        
        for tc in sorted(policy.traffic_classes, key=lambda x: x.priority, reverse=True):
            # Calculer les paramètres spécifiques à la classe
            target_delay = self._calculate_target_delay(tc)
            interval = self._calculate_interval(tc)
            quantum = self._calculate_quantum(tc, base_quantum)
            flows = self._calculate_flows_count(tc)
            
            # Paramètres de la file d'attente
            queue_params = QueueParameters(
                buffer_size=flows * 2,  # 2 paquets par flux en moyenne
                queue_limit=flows * 4,  # 4 paquets par flux maximum
                service_rate=tc.min_bandwidth,
                weight=quantum,  # Le quantum sert de poids relatif
                priority_level=tc.priority,
                bandwidth_percent=(tc.min_bandwidth / total_bandwidth * 100) if total_bandwidth > 0 else 0
            )
            
            # Paramètres CoDel pour l'évitement de congestion
            congestion_params = CongestionParameters(
                algorithm=CongestionAlgorithmType.ECN,  # CoDel utilise ECN quand possible
                min_threshold=target_delay,  # Utiliser target_delay comme seuil min
                max_threshold=interval,       # Utiliser interval comme seuil max
                drop_probability=0.0         # CoDel ne dépend pas d'une probabilité fixe
            )
            
            configurations.append(QueueConfiguration(
                traffic_class=tc,
                queue_params=queue_params,
                congestion_params=congestion_params
            ))
        
        return configurations
    
    def _calculate_target_delay(self, traffic_class: TrafficClass) -> int:
        """
        Calcule la latence cible pour une classe de trafic.
        
        Args:
            traffic_class: Classe de trafic
            
        Returns:
            Latence cible en microsecondes
        """
        # Classes haute priorité ont une latence cible plus faible
        if traffic_class.priority >= 7:  # Voix
            return 2000  # 2ms
        elif traffic_class.priority >= 5:  # Vidéo
            return 3000  # 3ms
        elif traffic_class.priority >= 3:  # Interactif
            return self.DEFAULT_TARGET_DELAY  # 5ms
        else:  # Best effort
            return 10000  # 10ms
    
    def _calculate_interval(self, traffic_class: TrafficClass) -> int:
        """
        Calcule l'intervalle CoDel pour une classe de trafic.
        
        Args:
            traffic_class: Classe de trafic
            
        Returns:
            Intervalle en microsecondes
        """
        # L'intervalle est généralement 20x la latence cible
        target_delay = self._calculate_target_delay(traffic_class)
        return max(self.DEFAULT_INTERVAL, target_delay * 20)
    
    def _calculate_quantum(self, traffic_class: TrafficClass, base_quantum: int) -> int:
        """
        Calcule le quantum (nombre d'octets à servir par tour) pour une classe.
        
        Args:
            traffic_class: Classe de trafic
            base_quantum: Quantum de base
            
        Returns:
            Quantum en octets
        """
        # Le quantum est proportionnel à la priorité et à la bande passante
        priority_factor = (traffic_class.priority + 1) / 8  # Normaliser 0-7 vers 0.125-1
        bandwidth_factor = max(1, traffic_class.min_bandwidth / 1000)  # Au moins 1, puis proportionnel
        
        quantum = int(base_quantum * priority_factor * bandwidth_factor)
        return max(self.DEFAULT_QUANTUM, quantum)
    
    def _calculate_base_quantum(self, total_bandwidth: int) -> int:
        """
        Calcule le quantum de base selon la bande passante totale.
        
        Args:
            total_bandwidth: Bande passante totale en kbps
            
        Returns:
            Quantum de base en octets
        """
        # Plus la bande passante est élevée, plus le quantum peut être grand
        if total_bandwidth >= 1000000:  # 1 Gbps+
            return 4608  # 3 * MTU
        elif total_bandwidth >= 100000:  # 100 Mbps+
            return 3072  # 2 * MTU
        else:
            return self.DEFAULT_QUANTUM  # 1 * MTU
    
    def _calculate_flows_count(self, traffic_class: TrafficClass) -> int:
        """
        Calcule le nombre de files de flux pour une classe de trafic.
        
        Args:
            traffic_class: Classe de trafic
            
        Returns:
            Nombre de files de flux
        """
        # Plus la bande passante est élevée, plus on peut avoir de flux
        if traffic_class.min_bandwidth >= 100000:  # 100 Mbps+
            return 2048
        elif traffic_class.min_bandwidth >= 10000:  # 10 Mbps+
            return self.DEFAULT_FLOWS
        else:
            return 512


class DeficitRoundRobinAlgorithm(QueueAlgorithm):
    """
    Algorithme Deficit Round Robin (DRR).
    
    DRR est un algorithme d'ordonnancement qui garantit l'équité entre
    les classes de trafic en allouant un quantum de données à servir
    à chaque classe. Il gère efficacement les paquets de taille variable.
    """
    
    # Quantum par défaut (en octets)
    DEFAULT_QUANTUM = 1500  # Approximativement un MTU Ethernet
    
    def calculate_parameters(self, policy: QoSPolicy) -> List[QueueConfiguration]:
        """
        Calcule les paramètres DRR pour chaque classe de trafic.
        
        Args:
            policy: Politique QoS contenant les classes de trafic
            
        Returns:
            Liste de configurations de file pour chaque classe
        """
        total_bandwidth = policy.bandwidth_limit
        total_weight = sum(self._calculate_weight(tc) for tc in policy.traffic_classes)
        configurations = []
        
        for tc in policy.traffic_classes:
            # Calculer le poids et le quantum pour cette classe
            weight = self._calculate_weight(tc)
            quantum = self._calculate_quantum(tc, weight, total_weight, total_bandwidth)
            
            # Calculer la taille de buffer basée sur le quantum
            buffer_size = self._calculate_buffer_size(quantum)
            queue_limit = buffer_size * 2  # Limite légèrement plus élevée
            
            # Paramètres de la file d'attente
            queue_params = QueueParameters(
                buffer_size=buffer_size,
                queue_limit=queue_limit,
                service_rate=tc.min_bandwidth,
                weight=weight,
                priority_level=tc.priority,
                bandwidth_percent=(tc.min_bandwidth / total_bandwidth * 100) if total_bandwidth > 0 else 0
            )
            
            # DRR utilise généralement Tail Drop ou RED simple
            congestion_params = CongestionParameters(
                algorithm=CongestionAlgorithmType.TAIL_DROP,
                min_threshold=0,
                max_threshold=0,
                drop_probability=0.0
            )
            
            # Si la classe a une priorité élevée, utiliser RED pour un meilleur contrôle
            if tc.priority >= 5:
                congestion_params = CongestionParameters(
                    algorithm=CongestionAlgorithmType.RED,
                    min_threshold=queue_limit // 4,
                    max_threshold=queue_limit * 3 // 4,
                    drop_probability=0.1
                )
            
            configurations.append(QueueConfiguration(
                traffic_class=tc,
                queue_params=queue_params,
                congestion_params=congestion_params
            ))
        
        return configurations
    
    def _calculate_weight(self, traffic_class: TrafficClass) -> float:
        """
        Calcule le poids d'une classe de trafic pour DRR.
        
        Args:
            traffic_class: Classe de trafic
            
        Returns:
            Poids de la classe (valeur positive)
        """
        # Le poids est basé sur la priorité et la bande passante minimale
        priority_weight = traffic_class.priority + 1  # 1-8
        bandwidth_weight = max(1, traffic_class.min_bandwidth / 1000)  # Au moins 1
        
        return priority_weight * bandwidth_weight
    
    def _calculate_quantum(self, traffic_class: TrafficClass, weight: float, 
                          total_weight: float, total_bandwidth: int) -> int:
        """
        Calcule le quantum (en octets) pour une classe de trafic.
        
        Args:
            traffic_class: Classe de trafic
            weight: Poids de la classe
            total_weight: Somme de tous les poids
            total_bandwidth: Bande passante totale
            
        Returns:
            Quantum en octets
        """
        if total_weight == 0:
            return self.DEFAULT_QUANTUM
        
        # Le quantum est proportionnel au poids relatif et à la bande passante
        relative_weight = weight / total_weight
        bandwidth_factor = max(1, total_bandwidth / 100000)  # Facteur basé sur la BP totale
        
        quantum = int(self.DEFAULT_QUANTUM * relative_weight * bandwidth_factor)
        
        # Assurer un quantum minimum et maximum raisonnable
        return max(512, min(quantum, 65536))  # Entre 512 octets et 64KB
    
    def _calculate_buffer_size(self, quantum: int) -> int:
        """
        Calcule la taille du buffer basée sur le quantum.
        
        Args:
            quantum: Quantum en octets
            
        Returns:
            Taille du buffer en paquets
        """
        # Estimer le nombre de paquets que peut contenir le quantum
        # En assumant une taille moyenne de paquet de 1000 octets
        avg_packet_size = 1000
        packets_per_quantum = max(1, quantum // avg_packet_size)
        
        # Buffer pour plusieurs quantum pour absorber les rafales
        buffer_size = packets_per_quantum * 4
        
        return max(16, min(buffer_size, 1024))  # Entre 16 et 1024 paquets


class AlgorithmFactory:
    """
    Fabrique pour créer les instances d'algorithmes de files d'attente.
    """
    
    @classmethod
    def create_algorithm(cls, algorithm_type: QueueAlgorithmType) -> QueueAlgorithm:
        """
        Crée une instance d'algorithme selon le type spécifié.
        
        Args:
            algorithm_type: Type d'algorithme à créer
            
        Returns:
            Instance d'algorithme de file d'attente
            
        Raises:
            ValueError: Si le type d'algorithme n'est pas supporté
        """
        if algorithm_type == QueueAlgorithmType.CBWFQ:
            return CBWFQAlgorithm()
        elif algorithm_type == QueueAlgorithmType.LLQ:
            return LowLatencyQueueingAlgorithm()
        elif algorithm_type == QueueAlgorithmType.FQ_CODEL:
            return FQCoDelAlgorithm()
        elif algorithm_type == QueueAlgorithmType.DRR:
            return DeficitRoundRobinAlgorithm()
        else:
            raise ValueError(f"Algorithme non supporté: {algorithm_type}")


class CongestionAvoidanceFactory:
    """
    Fabrique pour créer les instances d'algorithmes d'évitement de congestion.
    """
    
    @classmethod
    def create_algorithm(cls, algorithm_type: CongestionAlgorithmType):
        """
        Crée une instance d'algorithme d'évitement de congestion selon le type spécifié.
        
        Args:
            algorithm_type: Type d'algorithme à créer
            
        Returns:
            Instance d'algorithme d'évitement de congestion
            
        Raises:
            ValueError: Si le type d'algorithme n'est pas supporté
        """
        if algorithm_type in (CongestionAlgorithmType.RED, CongestionAlgorithmType.WRED):
            return RandomEarlyDetectionAlgorithm()
        elif algorithm_type == CongestionAlgorithmType.TAIL_DROP:
            # Pour Tail Drop, aucun traitement spécial n'est nécessaire
            return None
        else:
            raise ValueError(f"Algorithme d'évitement de congestion non supporté: {algorithm_type}") 