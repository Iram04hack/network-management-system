from django.contrib import admin
from .models import (
    Server, Project, Node, Link,
    Script, ScriptExecution, Snapshot,
    Workflow, WorkflowExecution,
    GNS3Config, Template
)

@admin.register(Server)
class ServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'port', 'protocol', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'protocol', 'created_at')
    search_fields = ('name', 'host')
    ordering = ('name',)

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'server', 'status', 'created_at', 'updated_at', 'created_by')
    list_filter = ('status', 'server', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('-updated_at',)

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('name', 'node_type', 'project', 'status', 'console_port')
    list_filter = ('node_type', 'status', 'project')
    search_fields = ('name',)
    ordering = ('project', 'name')

@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ('source_node', 'destination_node', 'project')
    list_filter = ('project',)
    ordering = ('project', 'source_node')

@admin.register(Script)
class ScriptAdmin(admin.ModelAdmin):
    list_display = ('name', 'script_type', 'is_template', 'node_type_filter')
    list_filter = ('script_type', 'is_template')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(ScriptExecution)
class ScriptExecutionAdmin(admin.ModelAdmin):
    list_display = ('script', 'node', 'project', 'status', 'created_at')
    list_filter = ('status', 'project', 'created_at')
    search_fields = ('script__name', 'node__name')
    ordering = ('-created_at',)

@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'created_at', 'created_by')
    list_filter = ('project', 'created_at')
    search_fields = ('name',)
    ordering = ('-created_at',)

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_template', 'created_at', 'created_by')
    list_filter = ('is_template', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(WorkflowExecution)
class WorkflowExecutionAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'project', 'status', 'created_at')
    list_filter = ('status', 'project', 'created_at')
    search_fields = ('workflow__name', 'project__name')
    ordering = ('-created_at',)


@admin.register(GNS3Config)
class GNS3ConfigAdmin(admin.ModelAdmin):
    """Interface d'administration pour la configuration GNS3."""
    list_display = ('key', 'description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('key',)


@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    """Interface d'administration pour les templates GNS3."""
    list_display = ('name', 'template_type', 'server', 'builtin', 'created_at')
    list_filter = ('template_type', 'server', 'builtin', 'created_at')
    search_fields = ('name', 'template_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('server', 'name') 