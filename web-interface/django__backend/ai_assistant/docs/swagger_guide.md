# 📖 Guide d'Utilisation Swagger - API AI Assistant

## 🎯 Accès à la Documentation Interactive

### URLs disponibles

Une fois le serveur Django démarré, la documentation Swagger est accessible via :

- **Swagger UI** (recommandé) : `http://localhost:8000/api/ai-assistant/swagger/`
- **ReDoc** (alternative moderne) : `http://localhost:8000/api/ai-assistant/redoc/`
- **Schéma JSON** : `http://localhost:8000/api/ai-assistant/swagger.json`
- **Schéma YAML** : `http://localhost:8000/api/ai-assistant/swagger.yaml`

## 🚀 Configuration et Activation

### 1. Installation des dépendances

Assurez-vous que `drf-yasg` est installé :

```bash
pip install drf-yasg
```

### 2. Configuration dans settings.py

Ajoutez dans votre `settings.py` :

```python
# settings.py
INSTALLED_APPS = [
    # ... autres apps
    'drf_yasg',
    'ai_assistant',
]

# Configuration Swagger
from ai_assistant.api.docs import get_swagger_settings
SWAGGER_CONFIG = get_swagger_settings()

# Mise à jour de la configuration
SWAGGER_SETTINGS = SWAGGER_CONFIG['SWAGGER_SETTINGS']
REDOC_SETTINGS = SWAGGER_CONFIG['REDOC_SETTINGS']
```

### 3. Intégration des URLs

Dans votre `urls.py` principal :

```python
# urls.py principal
from django.urls import path, include

urlpatterns = [
    # ... autres URLs
    path('api/ai-assistant/', include('ai_assistant.api.urls')),
    path('api/ai-assistant/', include('ai_assistant.api.swagger_urls')),
]
```

## 🔐 Authentification dans Swagger

### Configuration du token d'authentification

1. **Dans l'interface Swagger** :
   - Cliquez sur le bouton "Authorize" 🔒
   - Entrez votre token au format : `Bearer <votre_token>`
   - Cliquez sur "Authorize"

2. **Obtenir un token** :
   ```bash
   # Via l'API Django
   curl -X POST http://localhost:8000/api/auth/token/ \
        -H "Content-Type: application/json" \
        -d '{"username": "votre_username", "password": "votre_password"}'
   ```

3. **Test d'authentification** :
   ```bash
   # Test avec curl
   curl -X GET http://localhost:8000/api/ai-assistant/conversations/ \
        -H "Authorization: Bearer <votre_token>"
   ```

## 📚 Utilisation de l'Interface Swagger

### Navigation par sections

L'API est organisée en 5 sections principales :

#### 💬 Conversations
- `GET /conversations/` : Liste des conversations
- `POST /conversations/` : Créer une nouvelle conversation
- `GET /conversations/{id}/` : Détails d'une conversation
- `POST /conversations/{id}/messages/` : Envoyer un message

#### ⚡ Commandes
- `POST /commands/execute/` : Exécuter une commande
- `POST /commands/validate/` : Valider une commande
- `GET /commands/history/` : Historique des commandes

#### 📚 Documents
- `GET /documents/` : Liste des documents
- `POST /documents/` : Créer un document
- `GET /documents/{id}/` : Détails d'un document
- `DELETE /documents/{id}/` : Supprimer un document

#### 🔍 Recherche
- `POST /search/` : Recherche globale
- `GET /search/suggestions/` : Suggestions de recherche

#### 🌐 Analyse Réseau
- `POST /network/ping/` : Test de ping
- `POST /network/traceroute/` : Traceroute
- `POST /network/scan/` : Scan réseau (nmap)

### Test des Endpoints

#### Exemple 1 : Créer une conversation

1. **Sélectionnez** `POST /conversations/`
2. **Cliquez** sur "Try it out"
3. **Modifiez** le JSON d'exemple :
   ```json
   {
     "title": "Ma première conversation",
     "initial_message": "Bonjour, comment configurer un VLAN ?"
   }
   ```
4. **Cliquez** sur "Execute"
5. **Vérifiez** la réponse dans la section "Response"

#### Exemple 2 : Envoyer un message

1. **Copiez** l'ID de conversation obtenu précédemment
2. **Sélectionnez** `POST /conversations/{id}/messages/`
3. **Entrez** l'ID dans le champ "conversation_id"
4. **Modifiez** le corps de la requête :
   ```json
   {
     "content": "Peux-tu me donner la commande exacte ?",
     "context": {
       "previous_topic": "vlan_configuration"
     }
   }
   ```

#### Exemple 3 : Exécuter une commande

1. **Sélectionnez** `POST /commands/execute/`
2. **Testez** avec une commande sécurisée :
   ```json
   {
     "command": "ping 8.8.8.8",
     "type": "network",
     "parameters": {
       "count": 3,
       "timeout": 5
     },
     "validation_level": "strict"
   }
   ```

## 🔧 Fonctionnalités Avancées

### Filtrage et Pagination

La plupart des endpoints de liste supportent :

```bash
# Pagination
GET /conversations/?page=2&page_size=10

# Recherche
GET /documents/?search=vlan&category=network

# Tri
GET /conversations/?ordering=-created_at
```

### Gestion des Erreurs

Swagger affiche tous les codes d'erreur possibles :

- **400** : Requête malformée - Vérifiez la syntaxe JSON
- **401** : Non authentifié - Vérifiez votre token
- **403** : Non autorisé - Permissions insuffisantes
- **404** : Ressource non trouvée
- **429** : Trop de requêtes - Respectez les limites
- **500** : Erreur serveur - Vérifiez les logs

### Export et Import

#### Exporter le schéma

```bash
# JSON
curl http://localhost:8000/api/ai-assistant/swagger.json > api_schema.json

# YAML  
curl http://localhost:8000/api/ai-assistant/swagger.yaml > api_schema.yaml
```

#### Importer dans Postman

1. Ouvrez Postman
2. Cliquez sur "Import"
3. Collez l'URL : `http://localhost:8000/api/ai-assistant/swagger.json`
4. Toutes les requêtes seront importées automatiquement

## 🎨 Personnalisation de la Documentation

### Modifier l'apparence

Dans `api/docs.py`, vous pouvez personnaliser :

```python
# Changer le titre et la description
schema_view = get_schema_view(
    openapi.Info(
        title="🤖 Mon API AI Assistant",
        default_version='v2.0',
        description="Ma description personnalisée...",
        # ...
    )
)

# Modifier les couleurs et thèmes
SWAGGER_SETTINGS = {
    'DEFAULT_MODEL_RENDERING': 'example',
    'DOC_EXPANSION': 'list',  # Expandre toutes les sections
    'DEEP_LINKING': True,
    # ...
}
```

### Ajouter des exemples personnalisés

```python
# Dans REQUEST_EXAMPLES
REQUEST_EXAMPLES['mon_endpoint'] = {
    'summary': 'Mon exemple',
    'value': {
        'field1': 'valeur1',
        'field2': 'valeur2'
    }
}
```

## 📊 Monitoring et Analytics

### Métriques Swagger

Ajoutez des métriques pour surveiller l'utilisation :

```python
# Dans vos vues
from django.core.cache import cache
import json

@swagger_auto_schema(...)
def ma_vue(request):
    # Compter les appels d'API
    cache_key = f"api_calls_{request.path}"
    calls = cache.get(cache_key, 0)
    cache.set(cache_key, calls + 1, timeout=3600)
    
    # Votre logique
    return Response(...)
```

### Logs des requêtes

```python
# settings.py
LOGGING = {
    'loggers': {
        'ai_assistant.api': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}
```

## 🚀 Cas d'Utilisation Avancés

### Workflow Complet d'Utilisation

#### Scénario : Configuration réseau avec IA

```bash
# 1. Créer une conversation
POST /conversations/
{
  "title": "Configuration Switch",
  "initial_message": "J'ai besoin d'aide pour configurer un switch"
}

# 2. Dialogue avec l'IA
POST /conversations/1/messages/
{
  "content": "Comment configurer des VLANs pour segmenter le réseau ?"
}

# 3. Exécuter les commandes suggérées
POST /commands/execute/
{
  "command": "show vlan brief",
  "type": "network"
}

# 4. Rechercher dans la documentation
POST /search/
{
  "query": "VLAN configuration best practices",
  "filters": {"categories": ["network"]}
}

# 5. Sauvegarder la configuration dans un document
POST /documents/
{
  "title": "Configuration VLAN Final",
  "content": "# Configuration obtenue...",
  "category": "network"
}
```

## 🔍 Dépannage

### Problèmes Courants

#### Swagger ne s'affiche pas

1. **Vérifiez l'installation** :
   ```bash
   pip show drf-yasg
   ```

2. **Vérifiez les URLs** :
   ```python
   # Dans urls.py
   from ai_assistant.api.swagger_urls import urlpatterns as swagger_urls
   urlpatterns += swagger_urls
   ```

3. **Vérifiez les settings** :
   ```python
   # Dans settings.py
   INSTALLED_APPS = [..., 'drf_yasg', ...]
   ```

#### Erreurs d'authentification

1. **Token expiré** : Générez un nouveau token
2. **Format incorrect** : Utilisez `Bearer <token>` et non juste `<token>`
3. **Permissions** : Vérifiez que l'utilisateur a les bonnes permissions

#### Schémas manquants

```python
# Vérifiez que tous les serializers sont importés
from .serializers import *

# Vérifiez les décorateurs swagger
@swagger_auto_schema(
    request_body=MonSerializer,
    responses={200: MonSerializer}
)
```

### Debug Mode

Pour plus de détails en développement :

```python
# settings.py
DEBUG = True
SWAGGER_SETTINGS['VALIDATOR_URL'] = 'http://localhost:8189'
```

## 📖 Ressources Supplémentaires

### Documentation officielle
- [drf-yasg](https://drf-yasg.readthedocs.io/)
- [OpenAPI 3.0](https://swagger.io/specification/)
- [Django REST Framework](https://www.django-rest-framework.org/)

### Outils complémentaires
- [Postman](https://www.postman.com/) : Test des APIs
- [Insomnia](https://insomnia.rest/) : Alternative à Postman
- [OpenAPI Generator](https://openapi-generator.tech/) : Génération de clients

---

**🎉 Félicitations !** Vous avez maintenant une documentation API interactive complète pour le module AI Assistant. La documentation est automatiquement mise à jour à chaque modification de l'API.

*Guide créé pour le module AI Assistant v2.0 - Documentation Swagger Interactive*