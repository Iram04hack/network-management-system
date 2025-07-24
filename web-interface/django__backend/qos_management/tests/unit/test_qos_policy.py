"""
Tests unitaires pour les politiques QoS.
"""
import pytest
from django.test import TestCase
from unittest.mock import MagicMock, patch

from qos_management.models import QoSPolicy, TrafficClass, QoSRule
from qos_management.domain.entities import QoSPolicyEntity, TrafficClassEntity
from qos_management.domain.interfaces import TrafficControlService, QoSMonitoringService
from qos_management.domain.repository_interfaces import QoSPolicyRepository
from qos_management.application.qos_policy_use_cases import (
    CreateQoSPolicyUseCase,
    UpdateQoSPolicyUseCase,
    DeleteQoSPolicyUseCase,
    ListQoSPoliciesUseCase,
    GetQoSPolicyUseCase
)

pytestmark = [pytest.mark.django_db, pytest.mark.qos, pytest.mark.unit]


class TestQoSPolicyModel(TestCase):
    """Tests unitaires pour le modèle QoSPolicy."""
    
    def test_qos_policy_creation(self):
        """Test de création d'une politique QoS."""
        policy = QoSPolicy.objects.create(
            name="Test Policy",
            description="Description de test",
            is_active=True
        )
        
        assert policy.id is not None
        assert policy.name == "Test Policy"
        assert policy.description == "Description de test"
        assert policy.is_active is True
    
    def test_qos_policy_with_traffic_classes(self):
        """Test de création d'une politique QoS avec des classes de trafic."""
        policy = QoSPolicy.objects.create(
            name="Policy with Classes",
            description="Politique avec classes",
            is_active=True
        )
        
        # Ajouter des classes de trafic
        voip_class = TrafficClass.objects.create(
            policy=policy,
            name="VoIP",
            description="VoIP traffic",
            dscp="ef",
            priority=10,
            min_bandwidth=1000,
            max_bandwidth=5000
        )
        
        video_class = TrafficClass.objects.create(
            policy=policy,
            name="Video",
            description="Video traffic",
            dscp="af41",
            priority=8,
            min_bandwidth=10000,
            max_bandwidth=20000
        )
        
        # Ajouter des règles QoS
        QoSRule.objects.create(
            policy=policy,
            name="VoIP Rule",
            protocol="udp",
            source_port_start=0,
            source_port_end=65535,
            destination_port_start=5060,
            destination_port_end=5060,
            dscp_marking="ef",
            traffic_class=voip_class
        )
        
        # Récupérer les classes de trafic
        classes = policy.trafficclass_set.all()
        assert classes.count() == 2
        assert classes[0].name == "VoIP"
        assert classes[1].name == "Video"
        
        # Récupérer les règles
        rules = policy.qosrule_set.all()
        assert rules.count() == 1
        assert rules[0].name == "VoIP Rule"
        assert rules[0].traffic_class == voip_class


class TestQoSPolicyUseCases:
    """Tests unitaires pour les cas d'utilisation des politiques QoS."""
    
    @patch('qos_management.domain.repository_interfaces.QoSPolicyRepository')
    @patch('qos_management.domain.interfaces.TrafficControlService')
    def test_create_qos_policy_use_case(self, mock_traffic_control, mock_repository):
        """Test du cas d'utilisation de création de politique QoS."""
        # Configurer les mocks
        mock_repository.create = MagicMock(return_value=QoSPolicyEntity(
            id=1,
            name="New Policy",
            description="New policy description",
            is_active=True
        ))
        
        # Créer le cas d'utilisation
        use_case = CreateQoSPolicyUseCase(
            qos_policy_repository=mock_repository,
            traffic_control_service=mock_traffic_control
        )
        
        # Exécuter le cas d'utilisation
        policy_data = {
            "name": "New Policy",
            "description": "New policy description",
            "is_active": True
        }
        
        result = use_case.execute(policy_data)
        
        # Vérifier le résultat
        assert result.id == 1
        assert result.name == "New Policy"
        assert result.description == "New policy description"
        assert result.is_active is True
        
        # Vérifier que le repository a été appelé
        mock_repository.create.assert_called_once()
    
    @patch('qos_management.domain.repository_interfaces.QoSPolicyRepository')
    @patch('qos_management.domain.interfaces.TrafficControlService')
    def test_update_qos_policy_use_case(self, mock_traffic_control, mock_repository):
        """Test du cas d'utilisation de mise à jour de politique QoS."""
        # Configurer les mocks
        mock_repository.get = MagicMock(return_value=QoSPolicyEntity(
            id=1,
            name="Original Policy",
            description="Original description",
            is_active=True
        ))
        
        mock_repository.update = MagicMock(return_value=QoSPolicyEntity(
            id=1,
            name="Updated Policy",
            description="Updated description",
            is_active=False
        ))
        
        # Créer le cas d'utilisation
        use_case = UpdateQoSPolicyUseCase(
            qos_policy_repository=mock_repository,
            traffic_control_service=mock_traffic_control,
            interface_qos_repository=MagicMock()
        )
        
        # Exécuter le cas d'utilisation
        policy_data = {
            "name": "Updated Policy",
            "description": "Updated description",
            "is_active": False
        }
        
        result = use_case.execute(1, policy_data)
        
        # Vérifier le résultat
        assert result.id == 1
        assert result.name == "Updated Policy"
        assert result.description == "Updated description"
        assert result.is_active is False
        
        # Vérifier que le repository a été appelé
        mock_repository.get.assert_called_once_with(1)
        mock_repository.update.assert_called_once()
    
    @patch('qos_management.domain.repository_interfaces.QoSPolicyRepository')
    @patch('qos_management.domain.interfaces.TrafficControlService')
    def test_list_qos_policies_use_case(self, mock_traffic_control, mock_repository):
        """Test du cas d'utilisation de liste des politiques QoS."""
        # Configurer les mocks
        mock_repository.list = MagicMock(return_value=[
            QoSPolicyEntity(id=1, name="Policy 1", description="Description 1", is_active=True),
            QoSPolicyEntity(id=2, name="Policy 2", description="Description 2", is_active=False)
        ])
        
        # Créer le cas d'utilisation
        use_case = ListQoSPoliciesUseCase(qos_policy_repository=mock_repository)
        
        # Exécuter le cas d'utilisation
        result = use_case.execute()
        
        # Vérifier le résultat
        assert len(result) == 2
        assert result[0].id == 1
        assert result[0].name == "Policy 1"
        assert result[1].id == 2
        assert result[1].name == "Policy 2"
        
        # Vérifier que le repository a été appelé
        mock_repository.list.assert_called_once()
    
    @patch('qos_management.domain.repository_interfaces.QoSPolicyRepository')
    def test_get_qos_policy_use_case(self, mock_repository):
        """Test du cas d'utilisation de récupération d'une politique QoS."""
        # Configurer les mocks
        mock_repository.get = MagicMock(return_value=QoSPolicyEntity(
            id=1,
            name="Test Policy",
            description="Test description",
            is_active=True
        ))
        
        # Créer le cas d'utilisation
        use_case = GetQoSPolicyUseCase(qos_policy_repository=mock_repository)
        
        # Exécuter le cas d'utilisation
        result = use_case.execute(1)
        
        # Vérifier le résultat
        assert result.id == 1
        assert result.name == "Test Policy"
        assert result.description == "Test description"
        assert result.is_active is True
        
        # Vérifier que le repository a été appelé
        mock_repository.get.assert_called_once_with(1)
    
    @patch('qos_management.domain.repository_interfaces.QoSPolicyRepository')
    @patch('qos_management.domain.interfaces.TrafficControlService')
    def test_delete_qos_policy_use_case(self, mock_traffic_control, mock_repository):
        """Test du cas d'utilisation de suppression d'une politique QoS."""
        # Configurer les mocks
        mock_repository.delete = MagicMock(return_value=True)
        mock_repository.get = MagicMock(return_value=QoSPolicyEntity(
            id=1,
            name="Policy to Delete",
            description="Will be deleted",
            is_active=True
        ))
        
        # Créer le cas d'utilisation
        use_case = DeleteQoSPolicyUseCase(
            qos_policy_repository=mock_repository,
            interface_qos_repository=MagicMock(return_value=[])
        )
        
        # Exécuter le cas d'utilisation
        result = use_case.execute(1)
        
        # Vérifier le résultat
        assert result is True
        
        # Vérifier que le repository a été appelé
        mock_repository.get.assert_called_once_with(1)
        mock_repository.delete.assert_called_once_with(1) 