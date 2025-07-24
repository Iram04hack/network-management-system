"""Sérialiseurs pour les modèles GNS3."""

from rest_framework import serializers
from .models import (
    Server, Project, Node, Link, Template, Snapshot, 
    Script, ScriptExecution, Workflow, WorkflowExecution,
    GNS3Config
)


class ServerSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les serveurs GNS3 (version liste)."""
    status = serializers.CharField(read_only=True)
    
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'host', 'port', 'protocol', 'username',
            'verify_ssl', 'is_active', 'timeout', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']


class ServerDetailSerializer(ServerSerializer):
    """Sérialiseur détaillé pour les serveurs GNS3."""
    password = serializers.CharField(max_length=255, write_only=True, required=False)
    
    class Meta:
        model = Server
        fields = [
            'id', 'name', 'host', 'port', 'protocol', 'username', 'password',
            'verify_ssl', 'is_active', 'timeout', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }


class TemplateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les templates GNS3."""
    
    class Meta:
        model = Template
        fields = [
            'id', 'name', 'template_id', 'template_type', 'server',
            'builtin', 'symbol', 'properties', 'compute_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class NodeSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les nœuds GNS3."""
    template_name = serializers.CharField(source='template.name', read_only=True)
    
    class Meta:
        model = Node
        fields = [
            'id', 'name', 'node_id', 'node_type', 'project', 'template', 'template_name',
            'status', 'console_type', 'console_port', 'x', 'y', 'symbol',
            'properties', 'compute_id', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'node_id', 'console_port', 'status', 'created_at', 'updated_at']


class LinkSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les liens GNS3."""
    source_node_name = serializers.CharField(source='source_node.name', read_only=True)
    destination_node_name = serializers.CharField(source='destination_node.name', read_only=True)
    
    class Meta:
        model = Link
        fields = [
            'id', 'link_id', 'link_type', 'project', 
            'source_node', 'source_node_name', 'source_port',
            'destination_node', 'destination_node_name', 'destination_port',
            'status', 'properties', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'link_id', 'status', 'created_at', 'updated_at']


class SnapshotSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les snapshots GNS3."""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Snapshot
        fields = [
            'id', 'name', 'snapshot_id', 'project', 'description',
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = ['id', 'snapshot_id', 'created_by', 'created_at']


class ScriptSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les scripts GNS3."""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Script
        fields = [
            'id', 'name', 'script_type', 'content', 'description',
            'node_type_filter', 'is_template', 'template_variables',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class ScriptExecutionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les exécutions de scripts."""
    script_name = serializers.CharField(source='script.name', read_only=True)
    node_name = serializers.CharField(source='node.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = ScriptExecution
        fields = [
            'id', 'script', 'script_name', 'project', 'project_name',
            'node', 'node_name', 'status', 'parameters', 'output',
            'error_message', 'start_time', 'end_time', 'duration',
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'output', 'error_message', 'start_time', 
            'end_time', 'created_by', 'created_at'
        ]
    
    def get_duration(self, obj):
        """Calcule la durée d'exécution."""
        if obj.start_time and obj.end_time:
            return (obj.end_time - obj.start_time).total_seconds()
        return None


class WorkflowSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les workflows GNS3."""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Workflow
        fields = [
            'id', 'name', 'description', 'steps', 'is_template',
            'template_variables', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']


class WorkflowExecutionSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les exécutions de workflows."""
    workflow_name = serializers.CharField(source='workflow.name', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    duration = serializers.SerializerMethodField()
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = WorkflowExecution
        fields = [
            'id', 'workflow', 'workflow_name', 'project', 'project_name',
            'status', 'parameters', 'results', 'current_step', 'progress_percentage',
            'error_message', 'start_time', 'end_time', 'duration',
            'created_by', 'created_by_username', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'results', 'current_step', 'error_message',
            'start_time', 'end_time', 'created_by', 'created_at'
        ]
    
    def get_duration(self, obj):
        """Calcule la durée d'exécution."""
        if obj.start_time and obj.end_time:
            return (obj.end_time - obj.start_time).total_seconds()
        return None
    
    def get_progress_percentage(self, obj):
        """Calcule le pourcentage de progression."""
        if obj.workflow and obj.workflow.steps:
            total_steps = len(obj.workflow.steps)
            if total_steps > 0:
                return (obj.current_step / total_steps) * 100
        return 0


class ProjectSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les projets GNS3 (version liste)."""
    server_name = serializers.CharField(source='server.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    nodes_count = serializers.SerializerMethodField()
    links_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'project_id', 'server', 'server_name', 'status',
            'description', 'auto_start', 'auto_close', 'nodes_count', 'links_count',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'project_id', 'status', 'created_by', 'created_at', 'updated_at']
    
    def get_nodes_count(self, obj):
        """Compte le nombre de nœuds."""
        try:
            if hasattr(obj, 'nodes'):
                return obj.nodes.count()
            return 0
        except Exception:
            return 0
    
    def get_links_count(self, obj):
        """Compte le nombre de liens."""
        try:
            if hasattr(obj, 'links'):
                return obj.links.count()
            return 0
        except Exception:
            return 0

    def __repr__(self):
        """Représentation string pour éviter les problèmes de sérialisation."""
        return f"<ProjectSerializer for {self.Meta.model.__name__}>"


class ProjectDetailSerializer(ProjectSerializer):
    """Sérialiseur détaillé pour les projets GNS3."""
    # Utilisation de strings pour éviter les références circulaires Swagger
    nodes = serializers.StringRelatedField(many=True, read_only=True)
    links = serializers.StringRelatedField(many=True, read_only=True) 
    snapshots = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'project_id', 'server', 'server_name', 'status',
            'description', 'path', 'filename', 'auto_start', 'auto_close',
            'nodes', 'links', 'snapshots', 'nodes_count', 'links_count',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'project_id', 'status', 'created_by', 'created_at', 'updated_at']


class GNS3ConfigSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la configuration GNS3."""
    
    class Meta:
        model = GNS3Config
        fields = ['id', 'key', 'value', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
