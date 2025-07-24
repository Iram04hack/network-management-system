# Documentation Swagger - API Views Module

## 🎯 Objectif

Ce module configure une documentation Swagger complète pour exposer toutes les fonctionnalités API du système de gestion réseau via l'interface web accessible sur `http://localhost:8000/swagger/`.

## 📁 Structure de la documentation

```
api_views/docs/
├── __init__.py              # Exports principaux
├── swagger.py               # Configuration Swagger principale avec exemples
├── swagger_schemas.py       # Schémas OpenAPI détaillés
└── README.md               # Ce fichier
```

## 🔧 Configuration

### URLs Swagger disponibles

| URL | Description |
|-----|-------------|
| `/swagger/` | Interface Swagger UI interactive |
| `/docs/` | Interface Swagger UI (alias) |
| `/docs/redoc/` | Interface ReDoc alternative |
| `/docs/schema/` | Schéma OpenAPI brut (JSON) |

### APIs documentées

#### 📊 Dashboard APIs
- **DashboardViewSet** : CRUD tableaux de bord
- **SystemDashboardView** : Vue système
- **NetworkDashboardView** : Vue réseau  
- **SecurityDashboardView** : Vue sécurité
- **MonitoringDashboardView** : Vue monitoring
- **CustomDashboardView** : Tableaux personnalisés
- **DashboardWidgetViewSet** : Gestion des widgets

#### 🖥️ Device Management APIs  
- **DeviceManagementViewSet** : CRUD équipements
- Gestion des configurations
- Métriques temps réel
- Opérations en lot

#### 🔍 Topology Discovery APIs
- **TopologyDiscoveryViewSet** : Découverte de topologie
- **NetworkMapView** : Cartographie réseau
- **ConnectionsView** : Analyse des connexions
- **DeviceDependenciesView** : Dépendances d'équipements
- **PathDiscoveryView** : Découverte de chemins

#### 🔎 Search APIs
- **GlobalSearchViewSet** : Recherche globale
- **ResourceSearchViewSet** : Recherche de ressources
- **SearchHistoryViewSet** : Historique de recherche

#### 📈 Monitoring APIs
- **PrometheusViewSet** : Intégration Prometheus
- **GrafanaViewSet** : Intégration Grafana

#### 🛡️ Security APIs
- **Fail2BanViewSet** : Gestion Fail2ban
- **SuricataViewSet** : Gestion Suricata IDS/IPS

## 🏷️ Tags d'organisation

Les endpoints sont organisés par tags dans l'interface Swagger :

- `Dashboard` - Tableaux de bord
- `Device Management` - Gestion d'équipements
- `Topology Discovery` - Découverte de topologie
- `Search` - Recherche
- `Monitoring - Prometheus` - Métriques Prometheus
- `Monitoring - Grafana` - Dashboards Grafana
- `Security - Fail2ban` - Sécurité Fail2ban
- `Security - Suricata` - Sécurité Suricata

## 📋 Fonctionnalités avancées

### Exemples complets
- Exemples de requêtes et réponses pour chaque endpoint
- Cas d'usage documentés avec curl
- Gestion d'erreurs standardisée

### Schémas détaillés
- Validation automatique des données
- Types et formats spécifiés
- Documentation des champs obligatoires

### Authentification
- Documentation JWT complète
- Exemples d'utilisation des tokens
- Gestion des permissions

## 🚀 Utilisation

### Accès à la documentation

1. Démarrer le serveur Django :
```bash
cd /home/adjada/network-management-system/web-interface/django__backend
source nms_env/bin/activate
python manage.py runserver
```

2. Accéder à Swagger UI :
```
http://localhost:8000/swagger/
```

### Test des APIs

Depuis l'interface Swagger, vous pouvez :
- 📖 Consulter la documentation de chaque endpoint
- 🧪 Tester les APIs directement
- 📝 Voir les exemples de réponses
- 🔍 Explorer les schémas de données
- 📊 Comprendre les relations entre APIs

### Authentification dans Swagger

1. Obtenir un token JWT via l'API d'authentification
2. Cliquer sur "Authorize" dans Swagger UI
3. Entrer : `Bearer <votre_token>`
4. Tester les endpoints protégés

## 📚 Documentation des exemples

### Exemples de workflow complets

Le fichier `swagger.py` contient des exemples détaillés pour :

- **Authentification** : Obtention et utilisation des tokens JWT
- **Dashboard workflow** : Création et gestion des tableaux de bord
- **Topology discovery** : Découverte et cartographie réseau
- **Monitoring integration** : Intégration Prometheus/Grafana
- **Security management** : Gestion Fail2ban/Suricata
- **Error handling** : Gestion des erreurs et codes de retour

### Structure des réponses

Toutes les réponses suivent des formats standardisés :

```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2023-10-25T14:30:15Z",
  "request_id": "req-123456-abcd"
}
```

Pour les erreurs :
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Description de l'erreur",
    "details": { ... }
  },
  "timestamp": "2023-10-25T14:30:15Z",
  "request_id": "req-123456-abcd"
}
```

## 🔧 Maintenance

### Mise à jour de la documentation

Pour ajouter de nouvelles APIs :

1. Ajouter les vues dans le module approprié
2. Configurer les décorateurs `@swagger_auto_schema`
3. Mettre à jour `urls.py` pour inclure les nouvelles routes
4. Ajouter des exemples dans `swagger.py` si nécessaire
5. Mettre à jour les schémas dans `swagger_schemas.py`

### Bonnes pratiques

- ✅ Utiliser des tags cohérents pour organiser les endpoints
- ✅ Fournir des descriptions détaillées pour chaque API
- ✅ Inclure des exemples de requêtes et réponses
- ✅ Documenter tous les paramètres et codes d'erreur
- ✅ Maintenir la cohérence dans les formats de réponse
- ✅ Tester régulièrement les exemples fournis

## 🎉 Résultat

Après cette configuration, toutes les fonctionnalités du module `api_views` sont maintenant entièrement exposées et documentées sur l'interface Swagger accessible via `http://localhost:8000/swagger/`, permettant aux développeurs et utilisateurs de :

- Découvrir toutes les APIs disponibles
- Comprendre leur utilisation
- Les tester interactivement
- Intégrer facilement le système dans leurs applications