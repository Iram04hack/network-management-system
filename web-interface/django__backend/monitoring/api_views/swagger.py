"""
Documentation Swagger/OpenAPI pour les API REST du module monitoring.
"""

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

# Schémas pour les métriques
metrics_definition_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de la métrique"),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description de la métrique"),
        'metric_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de métrique (gauge, counter, etc.)"),
        'unit': openapi.Schema(type=openapi.TYPE_STRING, description="Unité de mesure"),
        'collection_method': openapi.Schema(type=openapi.TYPE_STRING, description="Méthode de collecte (snmp, api, etc.)"),
        'collection_config': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration de collecte"),
        'category': openapi.Schema(type=openapi.TYPE_STRING, description="Catégorie de la métrique"),
    },
    required=['name', 'metric_type', 'unit', 'collection_method']
)

device_metric_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'device': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'équipement"),
        'metric': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la définition de métrique"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom personnalisé pour cette instance"),
        'specific_config': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration spécifique"),
        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Si la métrique est active"),
        'last_collection': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de dernière collecte"),
        'last_collection_success': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Si la dernière collecte a réussi"),
        'last_value': openapi.Schema(type=openapi.TYPE_NUMBER, description="Dernière valeur collectée"),
    },
    required=['device', 'metric']
)

metric_value_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'device_metric': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la métrique d'équipement"),
        'value': openapi.Schema(type=openapi.TYPE_NUMBER, description="Valeur de la métrique"),
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Horodatage de la valeur"),
    },
    required=['device_metric', 'value']
)

# Schémas pour les vérifications de service
service_check_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom de la vérification"),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description de la vérification"),
        'check_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de vérification (ping, http, etc.)"),
        'check_config': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration de la vérification"),
        'category': openapi.Schema(type=openapi.TYPE_STRING, description="Catégorie de la vérification"),
        'compatible_device_types': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Types d'équipements compatibles"),
        'enabled': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Si la vérification est activée globalement"),
    },
    required=['name', 'check_type']
)

device_service_check_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'device': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'équipement"),
        'service_check': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la vérification de service"),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom personnalisé pour cette instance"),
        'specific_config': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration spécifique"),
        'check_interval': openapi.Schema(type=openapi.TYPE_INTEGER, description="Intervalle de vérification en secondes"),
        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Si la vérification est active"),
        'last_check': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de dernière vérification"),
        'last_status': openapi.Schema(type=openapi.TYPE_STRING, description="Dernier statut (ok, warning, critical, unknown)"),
        'last_message': openapi.Schema(type=openapi.TYPE_STRING, description="Dernier message"),
    },
    required=['device', 'service_check']
)

check_result_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'device_service_check': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la vérification de service d'équipement"),
        'status': openapi.Schema(type=openapi.TYPE_STRING, description="Statut (ok, warning, critical, unknown)"),
        'execution_time': openapi.Schema(type=openapi.TYPE_NUMBER, description="Temps d'exécution en secondes"),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message du résultat"),
        'details': openapi.Schema(type=openapi.TYPE_OBJECT, description="Détails supplémentaires"),
        'timestamp': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Horodatage du résultat"),
    },
    required=['device_service_check', 'status']
)

# Schémas pour les alertes
alert_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre de l'alerte"),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description de l'alerte"),
        'severity': openapi.Schema(type=openapi.TYPE_STRING, description="Sévérité (critical, high, medium, low, info)"),
        'status': openapi.Schema(type=openapi.TYPE_STRING, description="Statut (active, acknowledged, resolved)"),
        'source_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de source (metric, service_check, etc.)"),
        'source_id': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de la source"),
        'device': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'équipement concerné"),
        'details': openapi.Schema(type=openapi.TYPE_OBJECT, description="Détails supplémentaires"),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de création"),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de mise à jour"),
        'acknowledged_by': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'utilisateur qui a reconnu l'alerte"),
        'acknowledged_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de reconnaissance"),
        'resolved_by': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'utilisateur qui a résolu l'alerte"),
        'resolved_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de résolution"),
        'resolution_comment': openapi.Schema(type=openapi.TYPE_STRING, description="Commentaire de résolution"),
    },
    required=['title', 'severity', 'status']
)

# Schémas pour les tableaux de bord
dashboard_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre du tableau de bord"),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description du tableau de bord"),
        'uid': openapi.Schema(type=openapi.TYPE_STRING, read_only=True, description="UID unique du tableau de bord"),
        'owner': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID du propriétaire"),
        'is_public': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Si le tableau de bord est public"),
        'is_default': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Si le tableau de bord est le tableau de bord par défaut"),
        'layout_config': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration de mise en page"),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de création"),
        'updated_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de mise à jour"),
    },
    required=['title']
)

dashboard_widget_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'dashboard': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID du tableau de bord"),
        'title': openapi.Schema(type=openapi.TYPE_STRING, description="Titre du widget"),
        'widget_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de widget (metric_value, chart, etc.)"),
        'position': openapi.Schema(type=openapi.TYPE_OBJECT, description="Position du widget"),
        'size': openapi.Schema(type=openapi.TYPE_OBJECT, description="Taille du widget"),
        'data_source': openapi.Schema(type=openapi.TYPE_OBJECT, description="Source de données du widget"),
        'config': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration du widget"),
    },
    required=['dashboard', 'title', 'widget_type']
)

# Schémas pour les notifications
notification_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'channel': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID du canal de notification"),
        'subject': openapi.Schema(type=openapi.TYPE_STRING, description="Sujet de la notification"),
        'message': openapi.Schema(type=openapi.TYPE_STRING, description="Message de la notification"),
        'recipients': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_STRING), description="Liste des destinataires"),
        'user_recipients': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER), description="Liste des IDs des utilisateurs destinataires"),
        'alert': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'alerte associée"),
        'status': openapi.Schema(type=openapi.TYPE_STRING, description="Statut (pending, sent, error)"),
        'details': openapi.Schema(type=openapi.TYPE_OBJECT, description="Détails supplémentaires"),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de création"),
        'sent_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date d'envoi"),
        'read_by': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER), description="Liste des IDs des utilisateurs qui ont lu la notification"),
    },
    required=['channel', 'message']
)

notification_channel_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        'id': openapi.Schema(type=openapi.TYPE_INTEGER, read_only=True),
        'name': openapi.Schema(type=openapi.TYPE_STRING, description="Nom du canal"),
        'channel_type': openapi.Schema(type=openapi.TYPE_STRING, description="Type de canal (email, sms, webhook, etc.)"),
        'config': openapi.Schema(type=openapi.TYPE_OBJECT, description="Configuration du canal"),
        'description': openapi.Schema(type=openapi.TYPE_STRING, description="Description du canal"),
        'created_by': openapi.Schema(type=openapi.TYPE_INTEGER, description="ID de l'utilisateur qui a créé le canal"),
        'is_active': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Si le canal est actif"),
        'is_shared': openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Si le canal est partagé avec d'autres utilisateurs"),
        'created_at': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description="Date de création"),
    },
    required=['name', 'channel_type', 'config']
)

# Décorateurs pour les vues API
alert_list_schema = swagger_auto_schema(
    operation_description="Récupère la liste des alertes",
    responses={
        200: openapi.Response(
            description="Liste des alertes",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=alert_schema
            )
        )
    }
)

alert_detail_schema = swagger_auto_schema(
    operation_description="Récupère les détails d'une alerte",
    responses={
        200: openapi.Response(
            description="Détails de l'alerte",
            schema=alert_schema
        ),
        404: "Alerte non trouvée"
    }
)

alert_create_schema = swagger_auto_schema(
    operation_description="Crée une nouvelle alerte",
    request_body=alert_schema,
    responses={
        201: openapi.Response(
            description="Alerte créée",
            schema=alert_schema
        ),
        400: "Données invalides"
    }
)

alert_update_schema = swagger_auto_schema(
    operation_description="Met à jour une alerte existante",
    request_body=alert_schema,
    responses={
        200: openapi.Response(
            description="Alerte mise à jour",
            schema=alert_schema
        ),
        400: "Données invalides",
        404: "Alerte non trouvée"
    }
)

alert_delete_schema = swagger_auto_schema(
    operation_description="Supprime une alerte",
    responses={
        204: "Alerte supprimée",
        404: "Alerte non trouvée"
    }
)

# Décorateurs pour les vues API de métriques
metrics_definition_list_schema = swagger_auto_schema(
    operation_description="Récupère la liste des définitions de métriques",
    responses={
        200: openapi.Response(
            description="Liste des définitions de métriques",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=metrics_definition_schema
            )
        )
    }
)

metrics_definition_detail_schema = swagger_auto_schema(
    operation_description="Récupère les détails d'une définition de métrique",
    responses={
        200: openapi.Response(
            description="Détails de la définition de métrique",
            schema=metrics_definition_schema
        ),
        404: "Définition de métrique non trouvée"
    }
)

# Décorateurs pour les vues API de tableaux de bord
dashboard_list_schema = swagger_auto_schema(
    operation_description="Récupère la liste des tableaux de bord",
    responses={
        200: openapi.Response(
            description="Liste des tableaux de bord",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=dashboard_schema
            )
        )
    }
)

dashboard_detail_schema = swagger_auto_schema(
    operation_description="Récupère les détails d'un tableau de bord",
    responses={
        200: openapi.Response(
            description="Détails du tableau de bord",
            schema=dashboard_schema
        ),
        404: "Tableau de bord non trouvé"
    }
)

# Décorateurs pour les vues API de notifications
notification_list_schema = swagger_auto_schema(
    operation_description="Récupère la liste des notifications",
    responses={
        200: openapi.Response(
            description="Liste des notifications",
            schema=openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=notification_schema
            )
        )
    }
)

notification_detail_schema = swagger_auto_schema(
    operation_description="Récupère les détails d'une notification",
    responses={
        200: openapi.Response(
            description="Détails de la notification",
            schema=notification_schema
        ),
        404: "Notification non trouvée"
    }
)

"""
Configuration de la documentation Swagger pour l'API monitoring.
"""

from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

# Création du schéma Swagger pour le module monitoring uniquement
# Sera intégré dans la documentation globale du projet
schema_view = get_schema_view(
    openapi.Info(
        title="Monitoring API",
        default_version='v1',
        description="API pour le système de monitoring réseau - Module intégré",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],  # Aligné avec la configuration globale
    patterns=[],  # Sera configuré par le routeur principal
) 