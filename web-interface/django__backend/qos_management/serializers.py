# qos_management/serializers.py
from rest_framework import serializers
from .models import (
    QoSPolicy, TrafficClass, TrafficClassifier, InterfaceQoSPolicy
)
from network_management.api.serializers import InterfaceSerializer

class QoSPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = QoSPolicy
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class QoSPolicyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QoSPolicy
        fields = ['name', 'description', 'policy_type', 'bandwidth_limit', 'priority']
        extra_kwargs = {'description': {'required': False}}

class QoSPolicyUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = QoSPolicy
        fields = ['name', 'description', 'bandwidth_limit']
        extra_kwargs = {
            'name': {'required': False},
            'description': {'required': False},
            'bandwidth_limit': {'required': False}
        }

class QoSPolicyApplySerializer(serializers.Serializer):
    interface_id = serializers.IntegerField(required=True)
    parameters = serializers.DictField(required=False)

class TrafficClassSerializer(serializers.ModelSerializer):
    policy = QoSPolicySerializer(read_only=True)
    
    class Meta:
        model = TrafficClass
        fields = '__all__'
        read_only_fields = ['id']

class TrafficClassCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficClass
        fields = ['name', 'description', 'policy', 'priority', 'bandwidth', 'bandwidth_percent', 'dscp', 'queue_limit']
        extra_kwargs = {'description': {'required': False}}

class TrafficClassUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficClass
        fields = ['name', 'description', 'priority', 'bandwidth', 'bandwidth_percent', 'dscp', 'queue_limit']
        extra_kwargs = {
            'name': {'required': False},
            'description': {'required': False},
            'priority': {'required': False},
            'bandwidth': {'required': False},
            'bandwidth_percent': {'required': False},
            'dscp': {'required': False},
            'queue_limit': {'required': False}
        }

class TrafficClassifierSerializer(serializers.ModelSerializer):
    traffic_class = TrafficClassSerializer(read_only=True)
    
    class Meta:
        model = TrafficClassifier
        fields = '__all__'
        read_only_fields = ['id']

class TrafficClassifierCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficClassifier
        fields = ['traffic_class', 'description', 'source_ip', 'destination_ip', 'protocol', 
                 'source_port_start', 'source_port_end', 'destination_port_start', 
                 'destination_port_end', 'dscp', 'vlan_id']
        extra_kwargs = {
            'description': {'required': False},
            'source_ip': {'required': False},
            'destination_ip': {'required': False},
            'protocol': {'required': False, 'default': 'any'},
            'source_port_start': {'required': False},
            'source_port_end': {'required': False},
            'destination_port_start': {'required': False},
            'destination_port_end': {'required': False},
            'dscp': {'required': False},
            'vlan_id': {'required': False}
        }

class TrafficClassifierUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrafficClassifier
        fields = ['description', 'source_ip', 'destination_ip', 'protocol', 
                 'source_port_start', 'source_port_end', 'destination_port_start', 
                 'destination_port_end', 'dscp', 'vlan_id']
        extra_kwargs = {
            'description': {'required': False},
            'source_ip': {'required': False},
            'destination_ip': {'required': False},
            'protocol': {'required': False},
            'source_port_start': {'required': False},
            'source_port_end': {'required': False},
            'destination_port_start': {'required': False},
            'destination_port_end': {'required': False},
            'dscp': {'required': False},
            'vlan_id': {'required': False}
        }

class InterfaceQoSPolicySerializer(serializers.ModelSerializer):
    interface = InterfaceSerializer(read_only=True)
    policy = QoSPolicySerializer(read_only=True)
    
    class Meta:
        model = InterfaceQoSPolicy
        fields = '__all__'
        read_only_fields = ['id', 'applied_at', 'updated_at']
