"""
Module contenant les sérialisateurs pour les modèles du module Network Management.
"""

from rest_framework import serializers


class DeviceSerializer(serializers.Serializer):
    """
    Sérialisateur pour les équipements réseau.
    """
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    hostname = serializers.CharField(required=False, allow_blank=True)
    ip_address = serializers.IPAddressField()
    mac_address = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.CharField()
    manufacturer = serializers.CharField(required=False, allow_blank=True)
    vendor = serializers.CharField(required=False, allow_blank=True)
    model = serializers.CharField(required=False, allow_blank=True)
    os = serializers.CharField(required=False, allow_blank=True)
    os_version = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    is_virtual = serializers.BooleanField(default=False)
    management_interface = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class DeviceCreateSerializer(serializers.Serializer):
    """
    Sérialisateur pour la création d'équipements réseau.
    """
    name = serializers.CharField()
    hostname = serializers.CharField(required=False, allow_blank=True)
    ip_address = serializers.IPAddressField()
    mac_address = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.CharField()
    manufacturer = serializers.CharField(required=False, allow_blank=True)
    vendor = serializers.CharField(required=False, allow_blank=True)
    model = serializers.CharField(required=False, allow_blank=True)
    os = serializers.CharField(required=False, allow_blank=True)
    os_version = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(default=True)
    is_virtual = serializers.BooleanField(default=False)
    management_interface = serializers.CharField(required=False, allow_blank=True)


class DeviceUpdateSerializer(serializers.Serializer):
    """
    Sérialisateur pour la mise à jour d'équipements réseau.
    """
    name = serializers.CharField(required=False)
    hostname = serializers.CharField(required=False, allow_blank=True)
    ip_address = serializers.IPAddressField(required=False)
    mac_address = serializers.CharField(required=False, allow_blank=True)
    device_type = serializers.CharField(required=False)
    manufacturer = serializers.CharField(required=False, allow_blank=True)
    vendor = serializers.CharField(required=False, allow_blank=True)
    model = serializers.CharField(required=False, allow_blank=True)
    os = serializers.CharField(required=False, allow_blank=True)
    os_version = serializers.CharField(required=False, allow_blank=True)
    location = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    is_virtual = serializers.BooleanField(required=False)
    management_interface = serializers.CharField(required=False, allow_blank=True)


class InterfaceSerializer(serializers.Serializer):
    """
    Sérialisateur pour les interfaces réseau.
    """
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()
    device = DeviceSerializer(read_only=True)
    device_id = serializers.IntegerField(write_only=True)
    mac_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    subnet_mask = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    interface_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    speed = serializers.IntegerField(required=False, allow_null=True)
    mtu = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(required=False, default='unknown')
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


class InterfaceCreateSerializer(serializers.Serializer):
    """
    Sérialisateur pour la création d'interfaces réseau.
    """
    name = serializers.CharField()
    device_id = serializers.IntegerField()
    mac_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    subnet_mask = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    interface_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    speed = serializers.IntegerField(required=False, allow_null=True)
    mtu = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(required=False, default='unknown')
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class InterfaceUpdateSerializer(serializers.Serializer):
    """
    Sérialisateur pour la mise à jour d'interfaces réseau.
    """
    name = serializers.CharField(required=False)
    mac_address = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ip_address = serializers.IPAddressField(required=False, allow_null=True)
    subnet_mask = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    interface_type = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    speed = serializers.IntegerField(required=False, allow_null=True)
    mtu = serializers.IntegerField(required=False, allow_null=True)
    status = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class ConfigurationSerializer(serializers.Serializer):
    """
    Sérialisateur pour les configurations d'équipements.
    """
    id = serializers.IntegerField(read_only=True)
    device = DeviceSerializer(read_only=True)
    device_id = serializers.IntegerField(write_only=True)
    content = serializers.CharField()
    version = serializers.CharField()
    is_active = serializers.BooleanField(default=False)
    status = serializers.CharField(default='draft')
    comment = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    created_by = serializers.CharField()
    created_at = serializers.DateTimeField(read_only=True)
    applied_at = serializers.DateTimeField(required=False, allow_null=True)
    parent_id = serializers.IntegerField(required=False, allow_null=True)


class ConfigurationCreateSerializer(serializers.Serializer):
    """
    Sérialisateur pour la création de configurations d'équipements.
    """
    device_id = serializers.IntegerField()
    content = serializers.CharField()
    version = serializers.CharField()
    is_active = serializers.BooleanField(default=False)
    status = serializers.CharField(default='draft')
    comment = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    created_by = serializers.CharField()
    parent_id = serializers.IntegerField(required=False, allow_null=True)


class ConfigurationUpdateSerializer(serializers.Serializer):
    """
    Sérialisateur pour la mise à jour de configurations d'équipements.
    """
    content = serializers.CharField(required=False)
    version = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False)
    status = serializers.CharField(required=False)
    comment = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    parent_id = serializers.IntegerField(required=False, allow_null=True) 