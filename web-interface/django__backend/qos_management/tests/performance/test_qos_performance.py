"""
Tests de performance pour le module QoS.

Ce module contient des tests de performance pour évaluer les performances
du module QoS Management dans des conditions de charge diverses.
"""
import time
import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from qos_management.models import QoSPolicy, TrafficClass, TrafficClassifier
from network_management.models import NetworkDevice, NetworkInterface
from qos_management.di_container import qos_container

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.qos, 
    pytest.mark.performance,
    pytest.mark.slow
]


@pytest.fixture
def test_device():
    """Fixture pour créer un équipement réseau de test."""
    user = User.objects.create_user(
        username="perfuser",
        email="perf@example.com",
        password="password"
    )
    
    device = NetworkDevice.objects.create(
        name="Performance Router",
        hostname="perf-router.local",
        ip_address="192.168.1.100",
        device_type="router",
        os="cisco_ios",
        created_by=user
    )
    
    return device


@pytest.fixture
def test_interfaces(test_device):
    """Fixture pour créer plusieurs interfaces pour les tests de performance."""
    interfaces = []
    
    # Créer 10 interfaces
    for i in range(1, 11):
        interface = NetworkInterface.objects.create(
            device=test_device,
            name=f"GigabitEthernet0/{i}",
            mac_address=f"00:11:22:33:44:{i:02d}",
            ip_address=f"192.168.1.{100+i}",
            status="up"
        )
        interfaces.append(interface)
    
    return interfaces


@pytest.fixture
def test_policies():
    """Fixture pour créer plusieurs politiques QoS pour les tests de performance."""
    policies = []
    
    # Créer 5 politiques
    for i in range(1, 6):
        policy = QoSPolicy.objects.create(
            name=f"Performance Policy {i}",
            description=f"Performance test policy {i}",
            is_active=True
        )
        
        # Créer 5 classes de trafic par politique
        for j in range(1, 6):
            traffic_class = TrafficClass.objects.create(
                policy=policy,
                name=f"Class {j} of Policy {i}",
                description=f"Traffic class {j} for policy {i}",
                dscp=f"af{j}1",
                priority=j,
                min_bandwidth=j * 10000,
                max_bandwidth=j * 50000
            )
            
            # Créer 2 classificateurs par classe
            TrafficClassifier.objects.create(
                traffic_class=traffic_class,
                name=f"Classifier {j*2-1} for Class {j}",
                protocol="tcp",
                destination_port_start=j * 1000,
                destination_port_end=j * 1000 + 99,
                dscp_marking=f"af{j}1"
            )
            
            TrafficClassifier.objects.create(
                traffic_class=traffic_class,
                name=f"Classifier {j*2} for Class {j}",
                protocol="udp",
                destination_port_start=j * 2000,
                destination_port_end=j * 2000 + 99,
                dscp_marking=f"af{j}1"
            )
        
        policies.append(policy)
    
    return policies


class TestQoSPerformance(TestCase):
    """Tests de performance pour le module QoS."""
    
    def test_list_policies_performance(self, test_policies):
        """Test de performance pour la liste des politiques QoS."""
        list_policies_use_case = qos_container.list_qos_policies_use_case()
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        policies = list_policies_use_case.execute()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Vérifier les résultats
        assert len(policies) >= 5
        
        # Vérifier la performance
        assert execution_time < 0.1, f"Liste des politiques QoS trop lente: {execution_time:.4f} secondes"
        
        print(f"Liste des politiques QoS exécutée en {execution_time:.4f} secondes")
    
    def test_get_traffic_classes_performance(self, test_policies):
        """Test de performance pour la récupération des classes de trafic."""
        list_classes_use_case = qos_container.list_traffic_classes_use_case()
        
        policy = test_policies[0]
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        traffic_classes = list_classes_use_case.execute(policy_id=policy.id)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Vérifier les résultats
        assert len(traffic_classes) == 5
        
        # Vérifier la performance
        assert execution_time < 0.1, f"Récupération des classes de trafic trop lente: {execution_time:.4f} secondes"
        
        print(f"Récupération des classes de trafic exécutée en {execution_time:.4f} secondes")
    
    def test_bulk_apply_policies_performance(self, test_policies, test_interfaces):
        """Test de performance pour l'application de plusieurs politiques à plusieurs interfaces."""
        apply_policy_use_case = qos_container.apply_policy_to_interface_use_case()
        
        # Initialiser les compteurs
        total_execution_time = 0
        operations_count = 0
        
        # Appliquer chaque politique à deux interfaces
        for i, policy in enumerate(test_policies):
            for j in range(2):
                # Calculer l'index de l'interface
                interface_idx = (i * 2 + j) % len(test_interfaces)
                interface = test_interfaces[interface_idx]
                
                # Mesurer le temps d'exécution
                start_time = time.time()
                result = apply_policy_use_case.execute(
                    policy_id=policy.id,
                    interface_id=interface.id,
                    direction="egress"
                )
                end_time = time.time()
                
                execution_time = end_time - start_time
                total_execution_time += execution_time
                operations_count += 1
                
                # Vérifier le résultat
                assert result is not None
                assert result.policy_id == policy.id
                assert result.interface_id == interface.id
        
        # Calculer la moyenne
        avg_execution_time = total_execution_time / operations_count if operations_count > 0 else 0
        
        # Vérifier la performance
        assert avg_execution_time < 0.2, f"Application des politiques trop lente: {avg_execution_time:.4f} secondes en moyenne"
        
        print(f"Application de {operations_count} politiques exécutée en {total_execution_time:.4f} secondes")
        print(f"Temps moyen par application: {avg_execution_time:.4f} secondes")
    
    def test_qos_visualization_performance(self, test_policies):
        """Test de performance pour la visualisation des politiques QoS."""
        from qos_management.views.qos_visualization_views import QoSVisualizationData
        
        # Prendre la politique la plus complexe (dernière créée)
        policy = test_policies[-1]
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        visualization = QoSVisualizationData(policy)
        data = visualization.get_visualization_data()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Vérifier les résultats
        assert data is not None
        assert "traffic_classes" in data
        assert len(data["traffic_classes"]) == 5
        
        # Vérifier la performance
        assert execution_time < 0.5, f"Visualisation QoS trop lente: {execution_time:.4f} secondes"
        
        print(f"Visualisation QoS exécutée en {execution_time:.4f} secondes")
    
    @pytest.mark.parametrize("num_classes", [5, 10, 20])
    def test_policy_creation_scalability(self, num_classes):
        """
        Test de performance pour évaluer la création de politiques QoS
        avec un nombre variable de classes de trafic.
        """
        di_container = get_container()
        create_policy_use_case = di_container.create_qos_policy_use_case()
        
        # Préparer les données de la politique
        policy_data = {
            "name": f"Scalability Policy {num_classes}",
            "description": f"Policy with {num_classes} traffic classes",
            "is_active": True,
            "traffic_classes": []
        }
        
        # Ajouter des classes de trafic
        for i in range(1, num_classes + 1):
            traffic_class = {
                "name": f"Class {i}",
                "description": f"Traffic class {i}",
                "dscp": f"af{(i % 4) + 1}1",
                "priority": i % 10,
                "min_bandwidth": i * 5000,
                "max_bandwidth": i * 20000,
                "traffic_classifiers": [
                    {
                        "name": f"TCP Classifier {i}",
                        "protocol": "tcp",
                        "destination_port_start": i * 100,
                        "destination_port_end": i * 100 + 99,
                        "dscp_marking": f"af{(i % 4) + 1}1"
                    },
                    {
                        "name": f"UDP Classifier {i}",
                        "protocol": "udp",
                        "destination_port_start": i * 200,
                        "destination_port_end": i * 200 + 99,
                        "dscp_marking": f"af{(i % 4) + 1}1"
                    }
                ]
            }
            policy_data["traffic_classes"].append(traffic_class)
        
        # Mesurer le temps d'exécution
        start_time = time.time()
        policy = create_policy_use_case.execute(policy_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Vérifier les résultats
        assert policy is not None
        assert policy.id is not None
        
        # Vérifier la performance
        max_allowed_time = 0.01 * num_classes + 0.2  # Temps maximum autorisé basé sur le nombre de classes
        assert execution_time < max_allowed_time, f"Création de politique avec {num_classes} classes trop lente: {execution_time:.4f} secondes"
        
        print(f"Création de politique avec {num_classes} classes exécutée en {execution_time:.4f} secondes") 