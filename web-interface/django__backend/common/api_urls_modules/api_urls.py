"""
URLs pour les APIs du module Common.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'integration'

from ..api_views.integration_api import (
    integration_status,
    detect_gns3,
    consolidated_topology,
    gns3_projects,
    start_monitoring,
    stop_monitoring,
    integrated_modules,
    send_inter_module_message,
    message_history,
    send_notification,
    health_check
)

from ..api_views.equipment_discovery_api import (
    list_project_equipment,
    discover_equipment_details,
    discover_project_complete
)

# Import des endpoints de test pour la découverte d'IPs améliorée
from ..api_views.equipment_discovery_test import (
    test_enhanced_equipment_discovery,
    test_enhanced_project_discovery
)

from ..api_views.snmp_monitoring_api import (
    start_snmp_monitoring,
    stop_snmp_monitoring,
    get_snmp_monitoring_data,
    list_snmp_monitoring_sessions,
    test_snmp_connectivity
)

from ..api_views.communication_hub_api import (
    get_hub_status,
    start_hub,
    stop_hub,
    register_module,
    send_message,
    broadcast_message,
    execute_workflow,
    list_workflows
)

from ..api_views.celery_tasks_api import (
    trigger_celery_task,
    trigger_security_monitoring,
    trigger_network_monitoring,
    list_available_tasks
)

from ..api_views.gns3_central_api import (
    gns3_central_status,
    start_node,
    stop_node,
    restart_node,
    start_project,
    get_topology,
    refresh_topology,
    create_module_interface,
    get_events_stats
)

# URLs pour les APIs d'intégration
integration_patterns = [
    # Statut général
    path('status/', integration_status, name='integration-status'),
    path('health/', health_check, name='health-check'),
    
    # GNS3
    path('gns3/detect/', detect_gns3, name='detect-gns3'),
    path('gns3/projects/', gns3_projects, name='gns3-projects'),
    
    # Topologie
    path('topology/', consolidated_topology, name='consolidated-topology'),
    
    # Surveillance
    path('monitoring/start/', start_monitoring, name='start-monitoring'),
    path('monitoring/stop/', stop_monitoring, name='stop-monitoring'),
    
    # Modules
    path('modules/', integrated_modules, name='integrated-modules'),
    
    # Communication inter-modules
    path('messages/send/', send_inter_module_message, name='send-message'),
    path('messages/history/', message_history, name='message-history'),
    
    # Notifications
    path('notifications/send/', send_notification, name='send-notification'),
]

# URLs pour la découverte d'équipements
equipment_patterns = [
    # Liste des équipements d'un projet
    path('projects/<str:project_id>/equipment/', list_project_equipment, name='list-project-equipment'),
    
    # Découverte détaillée d'un équipement
    path('projects/<str:project_id>/equipment/<str:equipment_id>/', discover_equipment_details, name='discover-equipment-details'),
    
    # Découverte complète d'un projet
    path('projects/<str:project_id>/discover/', discover_project_complete, name='discover-project-complete'),
    
    # 🔧 ENDPOINTS DE TEST pour la découverte d'IPs améliorée
    path('projects/<str:project_id>/equipment/<str:equipment_id>/test-discovery/', test_enhanced_equipment_discovery, name='test-enhanced-equipment-discovery'),
    path('projects/<str:project_id>/test-discovery/', test_enhanced_project_discovery, name='test-enhanced-project-discovery'),
]

# URLs pour le monitoring SNMP
snmp_patterns = [
    # Gestion des sessions de monitoring
    path('monitoring/start/', start_snmp_monitoring, name='start-snmp-monitoring'),
    path('monitoring/sessions/', list_snmp_monitoring_sessions, name='list-snmp-sessions'),
    path('monitoring/sessions/<str:session_id>/', get_snmp_monitoring_data, name='get-snmp-data'),
    path('monitoring/sessions/<str:session_id>/stop/', stop_snmp_monitoring, name='stop-snmp-monitoring'),
    
    # Tests SNMP
    path('test/', test_snmp_connectivity, name='test-snmp-connectivity'),
]

# URLs pour le hub de communication
hub_patterns = [
    # Statut et contrôle du hub
    path('status/', get_hub_status, name='hub-status'),
    path('start/', start_hub, name='start-hub'),
    path('stop/', stop_hub, name='stop-hub'),
    
    # Gestion des modules
    path('modules/register/', register_module, name='register-module'),
    
    # Envoi de messages
    path('messages/send/', send_message, name='hub-send-message'),
    path('messages/broadcast/', broadcast_message, name='hub-broadcast-message'),
    
    # Workflows
    path('workflows/', list_workflows, name='list-workflows'),
    path('workflows/execute/', execute_workflow, name='execute-workflow'),
]

# URLs pour les tâches Celery centralisées
celery_patterns = [
    # Déclenchement de tâches Celery
    path('trigger/', trigger_celery_task, name='trigger-celery-task'),
    path('tasks/', list_available_tasks, name='list-available-tasks'),
]

# URLs pour les endpoints spécialisés (compatibilité avec le framework)
security_patterns = [
    path('monitor/', trigger_security_monitoring, name='trigger-security-monitoring'),
]

network_patterns = [
    path('monitor/', trigger_network_monitoring, name='trigger-network-monitoring'),
]

# URLs pour le service central GNS3
gns3_central_patterns = [
    # Statut du service
    path('status/', gns3_central_status, name='gns3-central-status'),
    
    # Gestion des nœuds
    path('nodes/start/', start_node, name='gns3-start-node'),
    path('nodes/stop/', stop_node, name='gns3-stop-node'),
    path('nodes/restart/', restart_node, name='gns3-restart-node'),
    
    # Gestion des projets
    path('projects/start/', start_project, name='gns3-start-project'),
    
    # Topologie
    path('topology/', get_topology, name='gns3-get-topology'),
    path('topology/refresh/', refresh_topology, name='gns3-refresh-topology'),
    
    # Interface modules
    path('modules/create-interface/', create_module_interface, name='gns3-create-module-interface'),
    
    # Événements et statistiques
    path('events/stats/', get_events_stats, name='gns3-events-stats'),
]

urlpatterns = [
    path('integration/', include(integration_patterns)),
    path('equipment/', include(equipment_patterns)),
    path('snmp/', include(snmp_patterns)),
    path('hub/', include(hub_patterns)),
    path('gns3-central/', include(gns3_central_patterns)),
    path('celery/', include(celery_patterns)),
    path('security/', include(security_patterns)),
    path('network/', include(network_patterns)),
]