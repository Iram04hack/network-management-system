"""
Tests unitaires pour les politiques QoS.
"""
import unittest

from qos_management.domain.entities import QoSPolicy, TrafficClass, TrafficClassifier, QoSPolicyEntity


class QoSPolicyEntityTests(unittest.TestCase):
    """Tests pour l'entité QoSPolicyEntity."""
    
    def test_from_policy_conversion(self):
        """Teste la conversion de QoSPolicy vers QoSPolicyEntity."""
        # Créer une politique avec des classes de trafic
        tc1 = TrafficClass(
            id=1,
            name="Voix",
            priority=1,
            min_bandwidth=1000,
            max_bandwidth=2000,
            dscp="EF"
        )
        
        tc2 = TrafficClass(
            id=2,
            name="Vidéo",
            priority=2,
            min_bandwidth=2000,
            max_bandwidth=5000,
            dscp="AF41"
        )
        
        policy = QoSPolicy(
            id=1,
            name="Politique Multimedia",
            description="Politique pour le trafic multimédia",
            bandwidth_limit=10000,
            is_active=True,
            priority=1
        )
        
        policy.add_traffic_class(tc1)
        policy.add_traffic_class(tc2)
        
        # Convertir en entité
        entity = QoSPolicyEntity.from_policy(policy)
        
        # Vérifier les attributs de base
        self.assertEqual(entity.id, policy.id)
        self.assertEqual(entity.name, policy.name)
        self.assertEqual(entity.description, policy.description)
        self.assertEqual(entity.bandwidth_limit, policy.bandwidth_limit)
        self.assertEqual(entity.is_active, policy.is_active)
        self.assertEqual(entity.priority, policy.priority)
        
        # Vérifier les classes de trafic
        self.assertEqual(len(entity.traffic_classes), 2)
        
        # Vérifier la première classe
        tc_entity_1 = entity.traffic_classes[0]
        self.assertEqual(tc_entity_1['id'], tc1.id)
        self.assertEqual(tc_entity_1['name'], tc1.name)
        self.assertEqual(tc_entity_1['priority'], tc1.priority)
        self.assertEqual(tc_entity_1['min_bandwidth'], tc1.min_bandwidth)
        self.assertEqual(tc_entity_1['max_bandwidth'], tc1.max_bandwidth)
        self.assertEqual(tc_entity_1['dscp'], tc1.dscp)
        
        # Vérifier la deuxième classe
        tc_entity_2 = entity.traffic_classes[1]
        self.assertEqual(tc_entity_2['id'], tc2.id)
        self.assertEqual(tc_entity_2['name'], tc2.name)
        self.assertEqual(tc_entity_2['priority'], tc2.priority)
        self.assertEqual(tc_entity_2['min_bandwidth'], tc2.min_bandwidth)
        self.assertEqual(tc_entity_2['max_bandwidth'], tc2.max_bandwidth)
        self.assertEqual(tc_entity_2['dscp'], tc2.dscp)


class QoSPolicyTests(unittest.TestCase):
    """Tests pour la classe QoSPolicy."""
    
    def setUp(self):
        """Configuration initiale pour les tests."""
        self.policy = QoSPolicy(
            id=1,
            name="Test Policy",
            description="Test Description",
            bandwidth_limit=10000,
            is_active=True,
            priority=1
        )
        
        self.tc1 = TrafficClass(
            id=1,
            name="Voix",
            priority=1,
            min_bandwidth=1000,
            max_bandwidth=2000
        )
        
        self.tc2 = TrafficClass(
            id=2,
            name="Vidéo",
            priority=2,
            min_bandwidth=2000,
            max_bandwidth=5000
        )
    
    def test_add_traffic_class(self):
        """Teste l'ajout d'une classe de trafic à une politique."""
        # Vérifier que la politique n'a pas de classe de trafic initialement
        self.assertEqual(len(self.policy.traffic_classes), 0)
        
        # Ajouter une classe de trafic
        self.policy.add_traffic_class(self.tc1)
        
        # Vérifier que la classe a été ajoutée
        self.assertEqual(len(self.policy.traffic_classes), 1)
        self.assertEqual(self.policy.traffic_classes[0], self.tc1)
        
        # Ajouter une autre classe de trafic
        self.policy.add_traffic_class(self.tc2)
        
        # Vérifier que la deuxième classe a été ajoutée
        self.assertEqual(len(self.policy.traffic_classes), 2)
        self.assertEqual(self.policy.traffic_classes[1], self.tc2)
    
    def test_remove_traffic_class(self):
        """Teste la suppression d'une classe de trafic d'une politique."""
        # Ajouter deux classes de trafic
        self.policy.add_traffic_class(self.tc1)
        self.policy.add_traffic_class(self.tc2)
        
        # Vérifier que les classes ont été ajoutées
        self.assertEqual(len(self.policy.traffic_classes), 2)
        
        # Supprimer la première classe
        result = self.policy.remove_traffic_class(self.tc1.id)
        
        # Vérifier que la suppression a réussi
        self.assertTrue(result)
        
        # Vérifier qu'il ne reste qu'une classe
        self.assertEqual(len(self.policy.traffic_classes), 1)
        self.assertEqual(self.policy.traffic_classes[0], self.tc2)
        
        # Tenter de supprimer une classe inexistante
        result = self.policy.remove_traffic_class(999)
        
        # Vérifier que la suppression a échoué
        self.assertFalse(result)
        
        # Vérifier que le nombre de classes n'a pas changé
        self.assertEqual(len(self.policy.traffic_classes), 1)


if __name__ == '__main__':
    unittest.main() 