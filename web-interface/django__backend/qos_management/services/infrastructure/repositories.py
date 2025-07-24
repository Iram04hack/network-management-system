from typing import List, Optional
from django.db import transaction
from qos_management.models import QoSPolicy as QoSPolicyModel
from qos_management.models import InterfaceQoSPolicy as InterfaceQoSPolicyModel
from network_management.infrastructure.models import NetworkInterface
from ..domain.interfaces import QoSPolicyRepository, InterfaceQoSPolicyRepository
from ..domain.entities import QoSPolicyEntity as QoSPolicy, InterfaceQoSPolicyEntity as InterfaceQoSPolicy, TrafficClassEntity as TrafficClass, TrafficClassifierEntity as TrafficClassifier

class DjangoQoSPolicyRepository(QoSPolicyRepository):
    def get_by_id(self, policy_id: int) -> Optional[QoSPolicy]:
        try:
            model = QoSPolicyModel.objects.prefetch_related(
                'traffic_classes__classifiers'
            ).get(id=policy_id)
            return self._to_entity(model)
        except QoSPolicyModel.DoesNotExist:
            return None
            
    def save(self, policy: QoSPolicy) -> QoSPolicy:
        with transaction.atomic():
            if policy.id:
                model = QoSPolicyModel.objects.get(id=policy.id)
                model.name = policy.name
                model.description = policy.description
                model.bandwidth_limit = policy.bandwidth_limit
                model.is_active = policy.is_active
            else:
                model = QoSPolicyModel(
                    name=policy.name,
                    description=policy.description,
                    bandwidth_limit=policy.bandwidth_limit,
                    is_active=policy.is_active
                )
            model.save()
            return self._to_entity(model)
            
    def delete(self, policy_id: int) -> bool:
        try:
            QoSPolicyModel.objects.get(id=policy_id).delete()
            return True
        except QoSPolicyModel.DoesNotExist:
            return False
            
    def list_all(self) -> List[QoSPolicy]:
        models = QoSPolicyModel.objects.prefetch_related(
            'traffic_classes__classifiers'
        ).all()
        return [self._to_entity(model) for model in models]
        
    def _to_entity(self, model: QoSPolicyModel) -> QoSPolicy:
        return QoSPolicy(
            id=model.id,
            name=model.name,
            description=model.description,
            bandwidth_limit=model.bandwidth_limit,
            is_active=model.is_active,
            traffic_classes=[
                TrafficClass(
                    id=tc.id,
                    priority=tc.priority,
                    min_bandwidth=tc.min_bandwidth,
                    max_bandwidth=tc.max_bandwidth,
                    dscp=tc.dscp,
                    burst=tc.burst,
                    classifiers=[
                        TrafficClassifier(
                            protocol=c.protocol,
                            source_ip=c.source_ip,
                            destination_ip=c.destination_ip,
                            source_port_start=c.source_port_start,
                            source_port_end=c.source_port_end,
                            destination_port_start=c.destination_port_start,
                            destination_port_end=c.destination_port_end,
                            dscp_marking=c.dscp_marking,
                            vlan=c.vlan
                        )
                        for c in tc.classifiers.all()
                    ]
                )
                for tc in model.traffic_classes.all()
            ]
        )

class DjangoInterfaceQoSPolicyRepository(InterfaceQoSPolicyRepository):
    def get_by_interface_and_direction(self, interface_id: int, direction: str) -> Optional[InterfaceQoSPolicy]:
        try:
            model = InterfaceQoSPolicyModel.objects.select_related(
                'interface', 'policy'
            ).get(
                interface_id=interface_id,
                direction=direction
            )
            return self._to_entity(model)
        except InterfaceQoSPolicyModel.DoesNotExist:
            return None
            
    def save(self, interface_policy: InterfaceQoSPolicy) -> InterfaceQoSPolicy:
        with transaction.atomic():
            if interface_policy.id:
                model = InterfaceQoSPolicyModel.objects.get(id=interface_policy.id)
                model.is_active = interface_policy.is_active
            else:
                model = InterfaceQoSPolicyModel(
                    interface_id=interface_policy.interface_id,
                    policy_id=interface_policy.policy.id,
                    direction=interface_policy.direction,
                    is_active=interface_policy.is_active
                )
            model.save()
            return self._to_entity(model)
            
    def delete(self, interface_policy_id: int) -> bool:
        try:
            InterfaceQoSPolicyModel.objects.get(id=interface_policy_id).delete()
            return True
        except InterfaceQoSPolicyModel.DoesNotExist:
            return False
            
    def _to_entity(self, model: InterfaceQoSPolicyModel) -> InterfaceQoSPolicy:
        return InterfaceQoSPolicy(
            id=model.id,
            interface_id=model.interface.id,
            interface_name=model.interface.name,
            policy=QoSPolicy(
                id=model.policy.id,
                name=model.policy.name,
                description=model.policy.description,
                bandwidth_limit=model.policy.bandwidth_limit,
                is_active=model.policy.is_active,
                traffic_classes=[]  # À remplir si nécessaire
            ),
            direction=model.direction,
            is_active=model.is_active
        ) 