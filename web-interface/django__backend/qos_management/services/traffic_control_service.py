import logging

logger = logging.getLogger(__name__)

class TrafficControlClient:
    """Client simple pour Traffic Control"""
    
    def __init__(self, sudo_required=True):
        self.sudo_required = sudo_required
    
    def test_connection(self):
        """Test de connexion simple"""
        return True
    
    def clear_interface(self, interface_name):
        """Nettoie une interface"""
        logger.info(f"Clearing interface {interface_name}")
        return True
    
    def configure_interface(self, interface_name, direction, bandwidth_limit, traffic_classes):
        """Configure une interface"""
        logger.info(f"Configuring interface {interface_name}")
        return True
    
    def get_interface_stats(self, interface_name):
        """Récupère les stats d'une interface"""
        return {"interface": interface_name, "stats": {}}

class TrafficControlService:
    """Service pour l'intégration avec Traffic Control"""
    
    def __init__(self, sudo_required=True):
        """
        Initialise le service Traffic Control
        
        Args:
            sudo_required (bool): Si True, utilise sudo pour les commandes TC
        """
        self.tc_client = TrafficControlClient(sudo_required=sudo_required)
        
    def test_connection(self):
        """
        Teste la connexion avec le service Traffic Control
        
        Returns:
            bool: True si la connexion est disponible
        """
        try:
            return self.tc_client.test_connection()
        except Exception as e:
            logger.error(f"Erreur lors du test de connexion avec Traffic Control: {str(e)}")
            return False
    
    def clear_interface(self, interface_name):
        """
        Nettoie la configuration QoS d'une interface
        
        Args:
            interface_name (str): Nom de l'interface réseau
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            if not self.test_connection():
                return False
                
            self.tc_client.clear_interface(interface_name)
            return True
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de l'interface {interface_name}: {str(e)}")
            return False
    
    def configure_interface(self, interface_name, direction, bandwidth_limit=0, traffic_classes=None):
        """
        Configure une interface avec une politique QoS
        
        Args:
            interface_name (str): Nom de l'interface
            direction (str): Direction du trafic (ingress/egress)
            bandwidth_limit (int): Limite de bande passante en kbps
            traffic_classes (list): Liste des classes de trafic à configurer
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            if not self.test_connection():
                logger.error("Impossible de se connecter au service Traffic Control")
                return False
                
            # Nettoyer l'interface avant de configurer
            self.clear_interface(interface_name)
            
            # Configurer l'interface avec les classes de trafic
            traffic_classes = traffic_classes or []
            
            self.tc_client.configure_interface(
                interface_name=interface_name,
                direction=direction,
                bandwidth_limit=bandwidth_limit,
                traffic_classes=traffic_classes
            )
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de l'interface {interface_name}: {str(e)}")
            return False
    
    def get_interface_stats(self, interface_name):
        """
        Récupère les statistiques d'une interface
        
        Args:
            interface_name (str): Nom de l'interface
            
        Returns:
            dict: Statistiques de l'interface ou None en cas d'erreur
        """
        try:
            if not self.test_connection():
                return None
                
            return self.tc_client.get_interface_stats(interface_name)
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques de l'interface {interface_name}: {str(e)}")
            return None 