"""
Tests unitaires pour les classificateurs de trafic.
"""
import unittest

from qos_management.domain.entities import TrafficClassifier


class TrafficClassifierTests(unittest.TestCase):
    """Tests pour la classe TrafficClassifier."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.classifier = TrafficClassifier(
            id=1,
            protocol='tcp',
            source_ip='192.168.1.0/24',
            destination_ip='10.0.0.1',
            source_port_start=1024,
            source_port_end=65535,
            destination_port_start=80,
            destination_port_end=80,
            dscp_marking='AF21',
            vlan=100,
            name='HTTP Traffic',
            description='Classificateur pour le trafic HTTP'
        )
    
    def test_matches_all_criteria(self):
        """Teste la correspondance avec tous les critères."""
        packet_data = {
            'protocol': 'tcp',
            'src_ip': '192.168.1.10',
            'dst_ip': '10.0.0.1',
            'src_port': 1500,
            'dst_port': 80,
            'dscp': 'AF21',
            'vlan': 100
        }
        
        self.assertTrue(self.classifier.matches(packet_data))
    
    def test_protocol_mismatch(self):
        """Teste la non-correspondance du protocole."""
        packet_data = {
            'protocol': 'udp',  # Différent de 'tcp'
            'src_ip': '192.168.1.10',
            'dst_ip': '10.0.0.1',
            'src_port': 1500,
            'dst_port': 80,
            'dscp': 'AF21',
            'vlan': 100
        }
        
        self.assertFalse(self.classifier.matches(packet_data))
    
    def test_source_ip_mismatch(self):
        """Teste la non-correspondance de l'IP source."""
        packet_data = {
            'protocol': 'tcp',
            'src_ip': '172.16.0.1',  # Hors du réseau 192.168.1.0/24
            'dst_ip': '10.0.0.1',
            'src_port': 1500,
            'dst_port': 80,
            'dscp': 'AF21',
            'vlan': 100
        }
        
        self.assertFalse(self.classifier.matches(packet_data))
    
    def test_destination_ip_mismatch(self):
        """Teste la non-correspondance de l'IP destination."""
        packet_data = {
            'protocol': 'tcp',
            'src_ip': '192.168.1.10',
            'dst_ip': '10.0.0.2',  # Différent de '10.0.0.1'
            'src_port': 1500,
            'dst_port': 80,
            'dscp': 'AF21',
            'vlan': 100
        }
        
        self.assertFalse(self.classifier.matches(packet_data))
    
    def test_source_port_mismatch(self):
        """Teste la non-correspondance du port source."""
        packet_data = {
            'protocol': 'tcp',
            'src_ip': '192.168.1.10',
            'dst_ip': '10.0.0.1',
            'src_port': 80,  # Hors de la plage 1024-65535
            'dst_port': 80,
            'dscp': 'AF21',
            'vlan': 100
        }
        
        self.assertFalse(self.classifier.matches(packet_data))
    
    def test_destination_port_mismatch(self):
        """Teste la non-correspondance du port destination."""
        packet_data = {
            'protocol': 'tcp',
            'src_ip': '192.168.1.10',
            'dst_ip': '10.0.0.1',
            'src_port': 1500,
            'dst_port': 443,  # Différent de 80
            'dscp': 'AF21',
            'vlan': 100
        }
        
        self.assertFalse(self.classifier.matches(packet_data))
    
    def test_dscp_mismatch(self):
        """Teste la non-correspondance du DSCP."""
        packet_data = {
            'protocol': 'tcp',
            'src_ip': '192.168.1.10',
            'dst_ip': '10.0.0.1',
            'src_port': 1500,
            'dst_port': 80,
            'dscp': 'EF',  # Différent de 'AF21'
            'vlan': 100
        }
        
        self.assertFalse(self.classifier.matches(packet_data))
    
    def test_vlan_mismatch(self):
        """Teste la non-correspondance du VLAN."""
        packet_data = {
            'protocol': 'tcp',
            'src_ip': '192.168.1.10',
            'dst_ip': '10.0.0.1',
            'src_port': 1500,
            'dst_port': 80,
            'dscp': 'AF21',
            'vlan': 200  # Différent de 100
        }
        
        self.assertFalse(self.classifier.matches(packet_data))
    
    def test_any_protocol(self):
        """Teste la correspondance avec le protocole 'any'."""
        classifier = TrafficClassifier(
            protocol='any',
            destination_port_start=80,
            destination_port_end=80
        )
        
        # Paquet TCP
        tcp_packet = {
            'protocol': 'tcp',
            'dst_port': 80
        }
        self.assertTrue(classifier.matches(tcp_packet))
        
        # Paquet UDP
        udp_packet = {
            'protocol': 'udp',
            'dst_port': 80
        }
        self.assertTrue(classifier.matches(udp_packet))
    
    def test_missing_field(self):
        """Teste le comportement avec un champ manquant dans le paquet."""
        packet_data = {
            'protocol': 'tcp',
            'src_ip': '192.168.1.10',
            'dst_ip': '10.0.0.1',
            # Port source manquant
            'dst_port': 80,
            'dscp': 'AF21',
            'vlan': 100
        }
        
        # Le classificateur devrait échouer car un champ requis est manquant
        self.assertFalse(self.classifier.matches(packet_data))


if __name__ == '__main__':
    unittest.main() 