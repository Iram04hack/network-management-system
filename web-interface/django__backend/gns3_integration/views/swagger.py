"""
Configuration Swagger pour l'API GNS3.

Ce module contient la configuration nécessaire pour la documentation
automatique de l'API REST GNS3 avec Swagger/OpenAPI.
"""
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Configuration du schéma Swagger
schema_view = get_schema_view(
    openapi.Info(
        title="API GNS3 Integration",
        default_version='v1',
        description="""
        API complète pour l'intégration GNS3 dans le système de gestion de réseau
        
        ## Fonctionnalités principales
        
        ### 🖥️ **Gestion des serveurs GNS3**
        - Configuration et monitoring des serveurs GNS3
        - Test de connexion automatique
        - Gestion sécurisée des credentials
        
        ### 📁 **Gestion des projets**
        - CRUD complet des projets GNS3
        - Ouverture/fermeture des projets
        - Duplication et export de projets
        - Statistiques détaillées
        - Démarrage/arrêt global des nœuds
        
        ### 🔧 **Gestion des équipements (nœuds)**
        - CRUD des nœuds réseau virtuels
        - Démarrage/arrêt individuel des nœuds
        - Positionnement sur la topologie
        - Gestion des consoles
        
        ### 🔗 **Gestion des liens**
        - Création/suppression de liens entre nœuds
        - Configuration des ports
        - Types de liens multiples
        
        ### 📋 **Gestion des templates**
        - Templates d'équipements prédéfinis
        - Support QEMU, Docker, Dynamips, IOU, etc.
        - Configuration personnalisée
        
        ### 📸 **Système de snapshots**
        - Sauvegarde d'état de projets
        - Restauration rapide
        - Gestion des versions
        
        ### 🤖 **Scripts d'automatisation**
        - Scripts Bash, Python, Expect
        - Exécution sur nœuds spécifiques
        - Historique des exécutions
        - Validation de syntaxe
        
        ### ⚙️ **Workflows complexes**
        - Automatisation multi-étapes
        - Paramètres personnalisables
        - Suivi de progression
        - Exécution asynchrone
        
        ## Authentification
        - Session Django pour l'interface web
        - Permissions configurables
        
        ## Utilisation de l'API
        
        Tous les endpoints supportent les formats JSON et sont documentés avec des exemples.
        La plupart des opérations nécessitent des paramètres de query (project_id, server_id).
        
        ### Endpoints principaux:
        - `/api/servers/` - Gestion des serveurs GNS3
        - `/api/projects/` - Gestion des projets
        - `/api/nodes/` - Gestion des nœuds
        - `/api/links/` - Gestion des liens
        - `/api/templates/` - Gestion des templates
        - `/api/snapshots/` - Gestion des snapshots
        - `/api/scripts/` - Gestion des scripts
        - `/api/workflows/` - Gestion des workflows
        """,
        terms_of_service="https://www.nms.local/terms/",
        contact=openapi.Contact(
            name="NMS Support Team",
            email="admin@nms.local",
            url="https://www.nms.local/support/"
        ),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# Exemples de requêtes et réponses pour les différentes ressources
server_examples = {
    "server_list": {
            "application/json": [
                {
                    "id": 1,
                "name": "GNS3 Server Principal",
                    "host": "192.168.1.100",
                    "port": 3080,
                    "protocol": "http",
                "username": "admin",
                "verify_ssl": True,
                "is_active": True,
                "timeout": 30,
                "status": "online",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            },
            {
                "id": 2,
                "name": "GNS3 Server Test",
                "host": "192.168.1.101",
                "port": 3080,
                "protocol": "https",
                "username": "testuser",
                "verify_ssl": False,
                "is_active": False,
                "timeout": 15,
                "status": "offline",
                "created_at": "2024-01-02T10:00:00Z",
                "updated_at": "2024-01-02T10:00:00Z"
            }
        ]
    }
}

project_examples = {
    "project_list": {
        "application/json": [
            {
                "id": "uuid-project-1",
                "name": "Topologie Réseau Entreprise",
                "project_id": "00000000-0000-0000-0000-000000000001",
                "server": 1,
                "server_name": "GNS3 Server Principal",
                "status": "opened",
                "description": "Simulation complète d'un réseau d'entreprise avec routeurs, switches et serveurs",
                "auto_start": False,
                "auto_close": True,
                "nodes_count": 15,
                "links_count": 23,
                "created_by": 1,
                "created_by_username": "admin",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T12:30:00Z"
            }
        ]
    },
    "project_detail": {
        "application/json": {
            "id": "uuid-project-1",
            "name": "Topologie Réseau Entreprise",
            "project_id": "00000000-0000-0000-0000-000000000001",
            "server": 1,
            "server_name": "GNS3 Server Principal",
            "status": "opened",
            "description": "Simulation complète d'un réseau d'entreprise",
            "path": "/opt/gns3/projects/enterprise-network",
            "filename": "enterprise-network.gns3",
            "auto_start": False,
            "auto_close": True,
            "nodes": [
                {
                    "id": "node-1",
                    "name": "Router-Core",
                    "node_id": "00000000-0000-0000-0000-000000000001",
                    "node_type": "dynamips",
                    "template_name": "Cisco 7200",
                    "status": "started",
                    "console_type": "telnet",
                    "console_port": 5000,
                    "x": 100,
                    "y": 100
                }
            ],
            "links": [
                {
                    "id": "link-1",
                    "link_id": "00000000-0000-0000-0000-000000000001",
                    "link_type": "ethernet",
                    "source_node": "node-1",
                    "source_node_name": "Router-Core",
                    "source_port": 0,
                    "destination_node": "node-2",
                    "destination_node_name": "Switch-Distrib",
                    "destination_port": 0,
                    "status": "started"
                }
            ],
            "snapshots": [
                {
                    "id": 1,
                    "name": "Configuration initiale",
                    "snapshot_id": "snapshot-001",
                    "description": "État après configuration de base",
                    "created_by_username": "admin",
                    "created_at": "2024-01-01T14:00:00Z"
                }
            ],
            "nodes_count": 15,
            "links_count": 23,
            "created_by_username": "admin",
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T12:30:00Z"
        }
    }
}

node_examples = {
    "node_list": {
        "application/json": [
            {
                "id": "node-1",
                "name": "Router-Core-01",
                "node_id": "00000000-0000-0000-0000-000000000001",
                "node_type": "dynamips",
                "project": "uuid-project-1",
                "template": 1,
                "template_name": "Cisco 7200",
                "status": "started",
                "console_type": "telnet",
                "console_port": 5000,
                "x": 100,
                "y": 100,
                "symbol": ":/symbols/router.svg",
                "properties": {
                    "platform": "c7200",
                    "ram": 512,
                    "image": "c7200-adventerprisek9-mz.124-24.T5.image"
                },
                "compute_id": "local",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T11:30:00Z"
            },
            {
                "id": "node-2",
                "name": "Switch-Access-01",
                "node_id": "00000000-0000-0000-0000-000000000002",
                "node_type": "ethernet_switch",
                "project": "uuid-project-1",
                "template": 2,
                "template_name": "Ethernet Switch",
                "status": "started",
                "console_type": "none",
                "console_port": None,
                "x": 200,
                "y": 200,
                "symbol": ":/symbols/ethernet_switch.svg",
                "properties": {
                    "ports_mapping": [
                        {"name": "Ethernet0", "port_number": 0, "type": "access", "vlan": 1},
                        {"name": "Ethernet1", "port_number": 1, "type": "access", "vlan": 1}
                    ]
                },
                "compute_id": "local",
                "created_at": "2024-01-01T10:15:00Z",
                "updated_at": "2024-01-01T10:15:00Z"
            }
        ]
    }
}

script_examples = {
    "script_list": {
        "application/json": [
            {
                "id": 1,
                "name": "Configuration Interface Cisco",
                "script_type": "cisco_ios",
                "content": "interface GigabitEthernet0/0\nip address 192.168.1.1 255.255.255.0\nno shutdown\nexit",
                "description": "Configure une interface Gigabit avec adresse IP",
                "node_type_filter": "dynamips",
                "is_template": True,
                "template_variables": {
                    "interface": "GigabitEthernet0/0",
                    "ip_address": "192.168.1.1",
                    "subnet_mask": "255.255.255.0"
                },
                "created_by": 1,
                "created_by_username": "admin",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            }
        ]
    }
}

workflow_examples = {
    "workflow_list": {
        "application/json": [
            {
                "id": 1,
                "name": "Déploiement Réseau Complet",
                "description": "Workflow automatisé pour déployer une topologie réseau complète",
                "steps": [
                    {
                        "step": 1,
                        "name": "Créer les nœuds",
                        "type": "create_nodes",
                        "parameters": {
                            "nodes": [
                                {"name": "Router-Core", "template": "cisco-7200", "x": 100, "y": 100},
                                {"name": "Switch-01", "template": "ethernet-switch", "x": 200, "y": 200}
                            ]
                        }
                    },
                    {
                        "step": 2,
                        "name": "Créer les liens",
                        "type": "create_links",
                        "parameters": {
                            "links": [
                                {"source": "Router-Core", "source_port": 0, "target": "Switch-01", "target_port": 0}
                            ]
                        }
                    },
                    {
                        "step": 3,
                        "name": "Démarrer les nœuds",
                        "type": "start_nodes",
                        "parameters": {"node_filter": "all"}
                    }
                ],
                "is_template": False,
                "template_variables": {},
                "created_by": 1,
                "created_by_username": "admin",
                "created_at": "2024-01-01T10:00:00Z",
                "updated_at": "2024-01-01T10:00:00Z"
            }
        ]
    }
}

# Réponses d'exemples pour la documentation
server_list_response = {
    "200": openapi.Response(
        description="Liste des serveurs GNS3",
        examples=server_examples["server_list"]
    )
}

project_list_response = {
    "200": openapi.Response(
        description="Liste des projets GNS3",
        examples=project_examples["project_list"]
    )
}

project_detail_response = {
    "200": openapi.Response(
        description="Détails complets du projet GNS3",
        examples=project_examples["project_detail"]
    )
}

node_list_response = {
    "200": openapi.Response(
        description="Liste des nœuds GNS3",
        examples=node_examples["node_list"]
    )
}

script_list_response = {
    "200": openapi.Response(
        description="Liste des scripts GNS3",
        examples=script_examples["script_list"]
    )
}

workflow_list_response = {
    "200": openapi.Response(
        description="Liste des workflows GNS3",
        examples=workflow_examples["workflow_list"]
    )
} 