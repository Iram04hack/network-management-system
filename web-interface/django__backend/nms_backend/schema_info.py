from drf_yasg import openapi

# Définition de l'objet openapi.Info pour la documentation API
schema_info = openapi.Info(
    title="NMS API",
    default_version='v1',
    description="""
    # API de gestion réseau (NMS)
    
    Cette API permet de gérer et surveiller un réseau complet à travers plusieurs modules.
    
    ## Modules principaux
    
    ### Sécurité
    - `/api/security/rules/` - Gestion des règles de sécurité
    - `/api/security/alerts/` - Alertes de sécurité
    - `/api/security/audit-logs/` - Journaux d'audit
    
    ### Réseau
    - `/api/network/devices/` - Gestion des équipements réseau
    - `/api/network/interfaces/` - Gestion des interfaces réseau
    - `/api/network/topologies/` - Visualisation et gestion des topologies
    - `/api/network/configurations/` - Gestion des configurations d'équipements
    
    ### Monitoring
    - `/api/monitoring/templates/` - Modèles de surveillance
    - `/api/monitoring/service-checks/` - Vérifications de services
    - `/api/monitoring/device-checks/` - Vérifications d'équipements
    - `/api/monitoring/metrics-definitions/` - Définitions de métriques
    - `/api/monitoring/device-metrics/` - Métriques des équipements
    - `/api/monitoring/alerts/` - Alertes de monitoring
    - `/api/monitoring/notifications/` - Notifications
    
    ### QoS
    - `/api/qos/policies/` - Politiques de qualité de service
    - `/api/qos/traffic-classes/` - Classes de trafic
    - `/api/qos/traffic-classifiers/` - Classificateurs de trafic
    - `/api/qos/interface-policies/` - Politiques QoS par interface
    
    ### GNS3
    - `/api/gns3/servers/` - Gestion des serveurs GNS3
    - `/api/gns3/projects/` - Projets GNS3
    - `/api/gns3/nodes/` - Nœuds dans les projets GNS3
    - `/api/gns3/links/` - Liens entre les nœuds
    
    ### Reporting
    - `/api/reporting/reports/` - Rapports générés
    - `/api/reporting/scheduled-reports/` - Planification de rapports
    
    ### Dashboard
    - `/api/dashboard/` - Vue d'ensemble du système
    - `/api/dashboard/overview/` - Vue d'ensemble détaillée
    - `/api/dashboard/network/` - Vue d'ensemble du réseau
    
    ### Assistant IA
    - `/api/ai/chatbot/chat/` - Interaction avec l'assistant IA
    - `/api/ai/chatbot/execute_command/` - Exécution de commandes
    - `/api/ai/chatbot/suggestions/` - Suggestions d'actions
    - `/api/ai/knowledge-base/` - Gestion de la base de connaissances
    - `/api/ai/conversations/` - Gestion des conversations
    - `/api/ai/messages/` - Gestion des messages
    
    ## Authentification
    
    Toutes les API nécessitent une authentification via JWT. Utilisez le endpoint `/api/token/` 
    pour obtenir un token, puis incluez-le dans l'en-tête `Authorization` de chaque requête:
    
    ```
    Authorization: Bearer <votre_token>
    ```
    
    ### Obtenir un token
    
    ```bash
    curl -X POST "http://localhost:8000/api/token/" \\
      -H "Content-Type: application/json" \\
      -d '{"username": "admin", "password": "password"}'
    ```
    
    ### Exemple de réponse
    
    ```json
    {
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    ```
    
    ## Pagination
    
    Les endpoints retournant des listes utilisent la pagination. Par défaut, 20 éléments sont retournés par page.
    
    Paramètres de pagination:
    - `page`: Numéro de la page (commence à 1)
    - `page_size`: Nombre d'éléments par page (max 100)
    
    ```
    GET /api/network/devices/?page=2&page_size=10
    ```
    
    ## Filtrage et recherche
    
    La plupart des endpoints supportent le filtrage et la recherche:
    
    - Recherche générale: `?search=terme`
    - Filtres spécifiques: `?status=active&type=router`
    
    ## Tri
    
    Utilisez le paramètre `ordering` pour trier les résultats:
    
    ```
    GET /api/network/devices/?ordering=name
    GET /api/network/devices/?ordering=-created_at  # Tri descendant
    ```
    
    ## Formats de réponse
    
    L'API supporte les formats JSON et XML. Par défaut, les réponses sont en JSON.
    Pour obtenir une réponse en XML, utilisez l'en-tête `Accept: application/xml`.
    
    ## Codes d'erreur
    
    | Code | Description                                      |
    |------|--------------------------------------------------|
    | 200  | Succès                                           |
    | 201  | Créé avec succès                                 |
    | 400  | Requête invalide ou données incorrectes          |
    | 401  | Non authentifié                                  |
    | 403  | Permissions insuffisantes                        |
    | 404  | Ressource non trouvée                            |
    | 500  | Erreur serveur                                   |
    
    ## WebSockets
    
    Pour les données en temps réel (métriques, alertes), utilisez les WebSockets:
    
    - `/ws/monitoring/metrics/`
    - `/ws/monitoring/alerts/`
    - `/ws/dashboard/`
    - `/ws/ai/chat/`
    
    ## Limites de taux
    
    Les API sont soumises à des limites de taux pour éviter les abus:
    
    - Utilisateurs anonymes: 10 requêtes/minute
    - Utilisateurs authentifiés: 60 requêtes/minute
    - Administrateurs: 300 requêtes/minute
    
    ## Support et contact
    
    Pour toute question ou problème, contactez l'équipe de support à l'adresse support@example.com.
    """,
    terms_of_service="https://www.example.com/terms/",
    contact=openapi.Contact(email="contact@example.com"),
    license=openapi.License(name="BSD License"),
) 