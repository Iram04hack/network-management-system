# Guide d'utilisation des décorateurs Swagger automatiques

Ce guide explique comment utiliser le système de génération automatique de documentation Swagger pour le module `api_clients`.

## Introduction

Les décorateurs Swagger automatiques permettent de documenter rapidement et facilement les API REST pour les exposer dans l'interface Swagger sans avoir à écrire manuellement des décorateurs `@swagger_auto_schema` pour chaque méthode.

## Méthodes disponibles

### 1. Utilisation du décorateur `@auto_schema_viewset`

Le décorateur `@auto_schema_viewset` peut être appliqué directement sur une classe ViewSet pour documenter automatiquement toutes ses méthodes :

```python
from api_clients.utils.swagger_utils import auto_schema_viewset

@auto_schema_viewset
class MyViewSet(viewsets.ModelViewSet):
    """
    Documentation pour mon ViewSet.
    
    Cette documentation sera automatiquement incluse dans Swagger.
    """
    serializer_class = MySerializer
    
    def list(self, request):
        """Cette description apparaîtra dans Swagger."""
        return Response({"data": []})
```

### 2. Utilisation de la fonction `apply_swagger_auto_schema`

Pour une application manuelle sur une classe existante :

```python
from api_clients.utils.swagger_utils import apply_swagger_auto_schema

class ExistingViewSet(viewsets.ViewSet):
    # ... méthodes existantes ...

# Application manuelle du décorateur
ExistingViewSet = apply_swagger_auto_schema(ExistingViewSet)
```

### 3. Documentation automatique de toutes les vues d'un module

Pour appliquer automatiquement la documentation à toutes les vues d'un module :

```python
from api_clients.utils.swagger_utils import generate_schema_for_all_views
import my_views_module

generate_schema_for_all_views(my_views_module)
```

## Comment ça fonctionne

Le système analyse automatiquement :

1. Les docstrings des classes et méthodes
2. Les serializers associés aux ViewSets
3. Les types de paramètres et de retour

Et génère la documentation Swagger correspondante.

## Application automatique

Le module est configuré pour appliquer automatiquement les décorateurs Swagger au démarrage de l'application Django, via :

1. La configuration dans `apps.py` qui charge le module `views_decorator.py`
2. Le module `views_decorator.py` qui décore toutes les vues existantes

## Personnalisation

Pour personnaliser la documentation d'un endpoint spécifique, vous pouvez toujours utiliser le décorateur `@swagger_auto_schema` manuellement sur cette méthode.
Le système détectera que la méthode a déjà une documentation Swagger et ne la remplacera pas.

## Documentation JSON

Les fichiers JSON de documentation Swagger sont générés automatiquement au démarrage de l'application et stockés dans le répertoire `api_clients/docs/swagger_output/`.

Pour désactiver cette génération, définissez la variable d'environnement `DISABLE_SWAGGER_GEN=True`.

## Accès à l'interface Swagger

La documentation générée est visible à l'adresse : http://localhost:8000/swagger/ 