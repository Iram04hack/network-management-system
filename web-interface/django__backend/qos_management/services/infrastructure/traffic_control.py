import logging
from typing import List
from api_clients.infrastructure.traffic_control_client import TrafficControlClient
from ..domain.interfaces import TrafficControlService
from ..domain.entities import TrafficClassEntity

logger = logging.getLogger(__name__)

class TrafficControlServiceImpl(TrafficControlService):
    def __init__(self, sudo_required: bool = True):
        self.client = TrafficControlClient(sudo_required=sudo_required)
        
    def configure_interface(self, interface_name: str, direction: str,
                          bandwidth_limit: int, traffic_classes: List[TrafficClassEntity]) -> bool:
        try:
            return self.client.configure_interface(
                interface_name=interface_name,
                direction=direction,
                bandwidth_limit=bandwidth_limit,
                traffic_classes=[
                    {
                        'id': tc.id,
                        'priority': tc.priority,
                        'min_bandwidth': tc.min_bandwidth,
                        'max_bandwidth': tc.max_bandwidth,
                        'dscp': tc.dscp,
                        'burst': tc.burst,
                        'classifiers': [
                            {
                                'protocol': c.protocol,
                                'source_ip': c.source_ip,
                                'destination_ip': c.destination_ip,
                                'source_port_start': c.source_port_start,
                                'source_port_end': c.source_port_end,
                                'destination_port_start': c.destination_port_start,
                                'destination_port_end': c.destination_port_end,
                                'dscp_marking': c.dscp_marking,
                                'vlan': c.vlan
                            }
                            for c in tc.classifiers
                        ]
                    }
                    for tc in traffic_classes
                ]
            )
        except Exception as e:
            logger.error(f"Erreur lors de la configuration de l'interface {interface_name}: {str(e)}")
            return False
            
    def clear_interface(self, interface_name: str) -> bool:
        try:
            return self.client.clear_interface(interface_name)
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage de l'interface {interface_name}: {str(e)}")
            return False
            
    def test_connection(self) -> bool:
        try:
            return self.client.test_connection()
        except Exception as e:
            logger.error(f"Erreur lors du test de connexion à Traffic Control: {str(e)}")
            return False 