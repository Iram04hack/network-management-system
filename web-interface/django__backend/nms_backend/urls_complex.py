"""
Configuration des URLs pour le projet NMS.

Ce module définit les points d'entrée URL pour l'application NMS.
"""

import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def discover_api_modules():
    """
    Découvre automatiquement tous les modules avec des URLs API.

    Returns:
        tuple: (api_patterns, api_urlpatterns, module_descriptions)
    """
    api_patterns = []
    api_urlpatterns = []
    module_descriptions = []

    # Configuration des modules API disponibles
    # Format: (url_prefix, module_path, title, description, features, enabled)
    api_modules = [
        ('api/views/', 'api_views.urls', 'API Views', 'Vues agrégées du système et monitoring', [
            '**Tableaux de bord** : Vues agrégées du système et monitoring',
            '**Découverte de topologie** : Exploration et cartographie du réseau',
            '**Gestion d\'équipements** : CRUD et configuration des dispositifs',
            '**Recherche avancée** : Recherche multi-critères avec filtrage dynamique',
            '**Monitoring Enterprise** : Intégration Prometheus et Grafana',
            '**Sécurité avancée** : Intégrations Fail2ban et Suricata IDS/IPS',
            'Documentation complète : `/api/views/docs/`'
        ], True),

        ('api/clients/', 'api_clients.urls', 'API Clients', 'Gestion des clients API pour les services réseau', [
            'Gestion des clients API pour les services réseau',
            'Clients pour GNS3, SNMP, Netflow, HAProxy, etc.',
            'Monitoring et santé des services',
            'Configuration et authentification des clients'
        ], True),

        ('api/ai/', 'ai_assistant.api.urls', 'AI Assistant', 'Module d\'assistance IA pour la gestion réseau', [
            'Module d\'assistance IA pour la gestion réseau',
            'Analyse et recommandations automatisées',
            'Détection d\'anomalies intelligente',
            'Optimisation automatique des configurations'
        ], True),

        ('api/dashboard/', 'dashboard.api.urls', 'Dashboard', 'Tableau de bord et métriques système', [
            '**Données du tableau de bord** : Métriques et statistiques système',
            '**Configuration utilisateur** : Personnalisation du tableau de bord',
            '**Vue d\'ensemble réseau** : Aperçu global des équipements et liens',
            '**Santé du système** : Métriques CPU, mémoire, disque et services',
            '**Métriques d\'équipements** : Données détaillées par équipement',
            '**Gestion de topologie** : Liste et données des topologies réseau'
        ], True),

        ('api/monitoring/', 'monitoring.urls', 'Monitoring', 'Surveillance et métriques avancées', [
            'Surveillance en temps réel des équipements',
            'Collecte et analyse des métriques SNMP',
            'Alertes et notifications automatisées',
            'Intégration Prometheus et Grafana'
        ], True),  

        ('api/network/', 'network_management.urls', 'Network Management', 'Gestion complète des équipements réseau', [
            'Gestion des équipements réseau (routeurs, switches, etc.)',
            'Configuration automatisée des équipements',
            'Découverte automatique de topologie',
            'Gestion des VLANs et interfaces'
        ], True),  # ✅ Module réactivé

        ('api/qos/', 'qos_management.urls', 'QoS Management', 'Gestion de la qualité de service', [
            'Configuration des politiques QoS',
            'Monitoring de la bande passante',
            'Gestion des priorités de trafic',
            'Analyse des performances réseau'
        ], False),  # Temporairement désactivé

        ('api/security/', 'security_management.urls', 'Security Management', 'Gestion avancée de la sécurité réseau', [
            'Gestion des politiques de sécurité',
            'Intégration Fail2ban et Suricata IDS/IPS',
            'Analyse des logs de sécurité',
            'Détection d\'intrusions et réponse automatique'
        ], False),  # Temporairement désactivé

        ('api/gns3/', 'gns3_integration.urls', 'GNS3 Integration', 'Intégration complète avec GNS3', [
            'Gestion des projets et topologies GNS3',
            'Contrôle des équipements virtuels',
            'Synchronisation avec l\'environnement de production',
            'Simulation et tests de configurations'
        ], True),  # ✅ Module activé

        ('api/reporting/', 'reporting.urls', 'Reporting', 'Génération de rapports avancés', [
            'Génération de rapports personnalisés',
            'Analyse des tendances et statistiques',
            'Export en multiple formats (PDF, Excel, CSV)',
            'Rapports automatisés et planifiés'
        ], False),  # Temporairement désactivé
    ]

    for url_prefix, module_path, title, description, features, enabled in api_modules:
        if enabled:
            try:
                # Vérifier si le module existe
                module_name = module_path.split('.')[0]
                if module_name in settings.INSTALLED_APPS:
                    api_patterns.append(path(url_prefix, include(module_path)))
                    api_urlpatterns.append(path(url_prefix, include(module_path)))

                    # Ajouter la documentation du module
                    module_descriptions.append(f"        ### {title} (`/{url_prefix}`)")
                    module_descriptions.append(f"        {description}")
                    module_descriptions.append("")
                    for feature in features:
                        module_descriptions.append(f"        - {feature}")
                    module_descriptions.append("")
            except Exception as e:
                print(f"Warning: Could not load module {module_path}: {e}")
                continue

    return api_patterns, api_urlpatterns, module_descriptions


# Découverte automatique des modules API
api_patterns, api_urlpatterns, module_descriptions = discover_api_modules()

# Configuration Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Network Management System (NMS) API",
        default_version='v1',
        description=f"""
        API complète pour le Network Management System (NMS)

        ## Modules disponibles:

{chr(10).join(module_descriptions)}
        ## Authentification
        - Session Django pour l'interface web
        - Token API pour les intégrations externes

        ## Support
        - Documentation générée automatiquement
        - Modules activés/désactivés selon la configuration
        - Exemples d'utilisation inclus
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
    patterns=api_patterns,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Modules API (auto-découverts)
] + api_urlpatterns + [

    # Vues web Django (non-API, pas dans Swagger)
    path('dashboard/', include('dashboard.urls')),  # Vues web du dashboard

    # Documentation Swagger/OpenAPI
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='api-docs'),
]

# Servir les fichiers statiques (pour développement et HTTPS)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
