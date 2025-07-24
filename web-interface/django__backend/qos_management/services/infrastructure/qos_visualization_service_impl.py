import logging
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta

from qos_management.domain.interfaces import QoSVisualizationService
from qos_management.domain.entities import QoSVisualizationData
from qos_management.models import QoSPolicy, TrafficClass

logger = logging.getLogger(__name__)

class QoSVisualizationServiceImpl(QoSVisualizationService):
    """
    Implémentation du service de visualisation QoS
    """
    
    def get_policy_visualization(self, policy_id: int) -> QoSVisualizationData:
        """
        Récupère les données de visualisation pour une politique QoS
        
        Args:
            policy_id: ID de la politique QoS
            
        Returns:
            QoSVisualizationData contenant les données de visualisation
            
        Raises:
            ValueError: Si la politique n'existe pas
        """
        try:
            # Récupérer la politique et ses classes de trafic
            policy = QoSPolicy.objects.prefetch_related('traffic_classes').get(id=policy_id)
            traffic_classes = policy.traffic_classes.all().order_by('-priority')
            
            # Préparer les données de visualisation
            traffic_classes_data = self._prepare_traffic_classes(traffic_classes)
            traffic_data = self._simulate_traffic_data(policy, traffic_classes)
            
            return QoSVisualizationData(
                policy_id=policy.id,
                policy_name=policy.name,
                bandwidth_limit=policy.bandwidth_limit,
                traffic_classes=traffic_classes_data,
                traffic_data=traffic_data
            )
            
        except QoSPolicy.DoesNotExist:
            raise ValueError(f"La politique QoS avec l'ID {policy_id} n'existe pas")
        except Exception as e:
            logger.exception(f"Erreur lors de la récupération des données de visualisation: {e}")
            raise
    
    def _prepare_traffic_classes(self, traffic_classes) -> List[Dict[str, Any]]:
        """
        Prépare les données des classes de trafic pour la visualisation
        
        Args:
            traffic_classes: QuerySet de classes de trafic
            
        Returns:
            Liste de dictionnaires représentant les classes de trafic
        """
        result = []
        
        for tc in traffic_classes:
            result.append({
                'id': tc.id,
                'name': tc.name,
                'priority': tc.priority,
                'min_bandwidth': tc.min_bandwidth,
                'max_bandwidth': tc.max_bandwidth,
                'dscp': tc.dscp,
                'color': self._get_class_color(tc.priority)
            })
            
        return result
    
    def _simulate_traffic_data(self, policy, traffic_classes) -> Dict[str, Any]:
        """
        Simule des données de trafic pour la visualisation
        Dans un environnement réel, ces données proviendraient de mesures réelles
        
        Args:
            policy: Politique QoS
            traffic_classes: Classes de trafic
            
        Returns:
            Dictionnaire contenant les données de trafic simulées
        """
        # Générer des points de données sur les dernières 24 heures
        now = datetime.now()
        time_points = []
        class_data = {}
        
        # Initialiser les données pour chaque classe
        for tc in traffic_classes:
            class_data[tc.name] = []
        
        # Générer des données pour les dernières 24 heures par intervalle de 15 minutes
        for i in range(96):  # 24 heures * 4 (15 minutes)
            time_point = now - timedelta(minutes=15 * (95 - i))
            time_points.append(time_point.strftime('%H:%M'))
            
            # Simuler l'utilisation de la bande passante pour chaque classe
            total_used = 0
            for tc in traffic_classes:
                # Simuler une utilisation variable avec des fluctuations
                if tc.max_bandwidth > 0:
                    usage = random.randint(
                        int(tc.min_bandwidth * 0.8),
                        min(tc.max_bandwidth, policy.bandwidth_limit - total_used)
                    )
                else:
                    # Si pas de max, utiliser une valeur aléatoire
                    usage = random.randint(
                        int(tc.min_bandwidth * 0.8),
                        int(policy.bandwidth_limit * 0.3)
                    )
                
                # Ajouter des variations pour rendre les données plus réalistes
                variation = random.uniform(0.8, 1.2)
                usage = int(usage * variation)
                
                # S'assurer que l'utilisation reste dans les limites
                usage = max(tc.min_bandwidth, min(usage, tc.max_bandwidth or policy.bandwidth_limit))
                
                class_data[tc.name].append(usage)
                total_used += usage
        
        return {
            'time_points': time_points,
            'class_data': class_data
        }
    
    def _get_class_color(self, priority: int) -> str:
        """
        Attribue une couleur à une classe de trafic en fonction de sa priorité
        
        Args:
            priority: Priorité de la classe
            
        Returns:
            Code couleur hexadécimal
        """
        # Palette de couleurs pour les différentes priorités
        colors = [
            '#FF0000',  # Rouge - Priorité la plus élevée
            '#FF7F00',  # Orange
            '#FFFF00',  # Jaune
            '#00FF00',  # Vert
            '#0000FF',  # Bleu
            '#4B0082',  # Indigo
            '#9400D3',  # Violet - Priorité la plus basse
        ]
        
        # Attribuer une couleur en fonction de la priorité
        # Plus la priorité est élevée, plus l'indice est petit
        index = min(priority, len(colors) - 1)
        return colors[index] 