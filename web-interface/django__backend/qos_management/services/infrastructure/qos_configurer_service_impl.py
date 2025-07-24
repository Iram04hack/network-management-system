import logging
from typing import List

from ..domain.interfaces import QoSConfigurerService
from ..domain.entities import QoSRecommendation, RecommendedTrafficClass

logger = logging.getLogger(__name__)

class QoSConfigurerServiceImpl(QoSConfigurerService):
    """
    Implémentation du service de configuration QoS
    """
    
    def generate_recommendations(self, traffic_type: str, network_size: str) -> QoSRecommendation:
        """
        Génère des recommandations de politique QoS basées sur le type de trafic et la taille du réseau
        
        Args:
            traffic_type: Type de trafic (general, voice, streaming, etc.)
            network_size: Taille du réseau (small, medium, large)
            
        Returns:
            QoSRecommendation contenant les recommandations
        """
        policy_name = f"{traffic_type.capitalize()} QoS Policy"
        description = f"Recommended QoS policy for {traffic_type} traffic in a {network_size} network"
        traffic_classes = []
        
        # Recommandations pour les réseaux généraux
        if traffic_type == 'general':
            traffic_classes = [
                RecommendedTrafficClass(
                    name='Voice',
                    description='Real-time voice traffic',
                    dscp='ef',
                    priority=5,
                    min_bandwidth=10,  # 10% de la bande passante
                    max_bandwidth=30   # 30% de la bande passante
                ),
                RecommendedTrafficClass(
                    name='Video',
                    description='Video conferencing and streaming',
                    dscp='af41',
                    priority=4,
                    min_bandwidth=20,
                    max_bandwidth=40
                ),
                RecommendedTrafficClass(
                    name='Mission Critical',
                    description='Business critical applications',
                    dscp='af31',
                    priority=3,
                    min_bandwidth=15,
                    max_bandwidth=35
                ),
                RecommendedTrafficClass(
                    name='Best Effort',
                    description='Regular traffic',
                    dscp='default',
                    priority=2,
                    min_bandwidth=5,
                    max_bandwidth=50
                ),
                RecommendedTrafficClass(
                    name='Background',
                    description='Bulk transfers, backups, etc.',
                    dscp='cs1',
                    priority=1,
                    min_bandwidth=1,
                    max_bandwidth=20
                )
            ]
        
        # Recommandations pour les environnements VoIP/Téléphonie
        elif traffic_type == 'voice':
            traffic_classes = [
                RecommendedTrafficClass(
                    name='Voice Signaling',
                    description='Voice control protocols (SIP, H.323)',
                    dscp='cs3',
                    priority=4,
                    min_bandwidth=5,
                    max_bandwidth=10
                ),
                RecommendedTrafficClass(
                    name='Voice RTP',
                    description='Voice media streams',
                    dscp='ef',
                    priority=5,
                    min_bandwidth=30,
                    max_bandwidth=50
                ),
                RecommendedTrafficClass(
                    name='Video Calls',
                    description='Video conferencing',
                    dscp='af41',
                    priority=3,
                    min_bandwidth=20,
                    max_bandwidth=30
                ),
                RecommendedTrafficClass(
                    name='Other Traffic',
                    description='All other traffic',
                    dscp='default',
                    priority=1,
                    min_bandwidth=5,
                    max_bandwidth=40
                )
            ]
        
        # Recommandations pour les environnements de streaming vidéo
        elif traffic_type == 'streaming':
            traffic_classes = [
                RecommendedTrafficClass(
                    name='Live Streaming',
                    description='Live video streams',
                    dscp='af41',
                    priority=5,
                    min_bandwidth=40,
                    max_bandwidth=60
                ),
                RecommendedTrafficClass(
                    name='VOD Streaming',
                    description='Video on demand',
                    dscp='af31',
                    priority=4,
                    min_bandwidth=30,
                    max_bandwidth=50
                ),
                RecommendedTrafficClass(
                    name='Interactive Services',
                    description='Interactive applications',
                    dscp='af21',
                    priority=3,
                    min_bandwidth=10,
                    max_bandwidth=20
                ),
                RecommendedTrafficClass(
                    name='Other Traffic',
                    description='All other traffic',
                    dscp='default',
                    priority=1,
                    min_bandwidth=5,
                    max_bandwidth=20
                )
            ]
            
        # Adapter les recommandations en fonction de la taille du réseau
        if network_size == 'small':
            # Simplifier les recommandations pour les petits réseaux
            pass
        elif network_size == 'large':
            # Ajouter des classes plus détaillées pour les grands réseaux
            pass
            
        return QoSRecommendation(
            policy_name=policy_name,
            description=description,
            traffic_classes=traffic_classes
        ) 