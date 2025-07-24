# Documentation du module plugins

Le module `plugins` fournit un système extensible pour ajouter de nouvelles fonctionnalités au NMS sans modifier son code principal.

## Architecture

Le module suit une architecture Domain-Driven Design (DDD) avec les couches suivantes:

- **Domain**: Contient les interfaces et classes de base pour les plugins
- **Infrastructure**: Contient les implémentations concrètes des services utilisés par les plugins
- **Application**: Contient les services de haut niveau qui orchestrent les fonctionnalités
- **API**: Expose les fonctionnalités via une interface REST

## Types de plugins

Le système supporte plusieurs types de plugins:

- **AlertHandlers**: Permettent de traiter et acheminer les alertes vers différents canaux (email, Slack, etc.)
- **DashboardWidgets**: Fournissent des widgets pour le tableau de bord
- **ReportGenerators**: Générateurs de rapports personnalisés

## Utilisation

### Création d'un nouveau plugin

Pour créer un nouveau plugin, vous devez:

1. Créer une classe qui implémente l'interface appropriée
2. Décorer la classe avec `@register_plugin`
3. Implémenter les méthodes requises

Exemple pour un gestionnaire d'alertes:

```python
from plugins.infrastructure.registry import register_plugin
from plugins.domain.interfaces import AlertHandlerPlugin

@register_plugin('alert_handlers')
class MyCustomAlertHandler(AlertHandlerPlugin):
    name = "my_handler"
    
    def initialize(self) -> bool:
        # Code d'initialisation
        return True
    
    def cleanup(self) -> bool:
        # Nettoyage des ressources
        return True
    
    def get_metadata(self):
        return {
            'id': 'my_custom_alert_handler',
            'name': self.name,
            'version': '1.0.0',
            'description': 'Mon gestionnaire d\'alertes personnalisé',
            'author': 'Votre nom',
            'dependencies': [],
            'provides': ['alert_notification']
        }
    
    def can_handle(self, alert):
        # Logique pour déterminer si ce handler peut traiter cette alerte
        return True
    
    def handle_alert(self, alert):
        # Logique pour traiter l'alerte
        return {"success": True}
```

### Utilisation des plugins

Pour utiliser les plugins enregistrés depuis votre code:

```python
from plugins.infrastructure.registry import PluginRegistry

# Récupérer tous les plugins d'un type
alert_handlers = PluginRegistry.get_plugins('alert_handlers')

# Récupérer un plugin spécifique
slack_handler = PluginRegistry.get_plugin('alert_handlers', 'slack')
```

## API REST

Le module expose une API REST pour:

- Lister les plugins disponibles
- Récupérer les détails d'un plugin spécifique
- Utiliser les plugins pour traiter des événements

Consultez la documentation Swagger à l'URL `/api/plugins/swagger/` pour plus de détails.

## Documentation de l'API

Pour accéder à la documentation complète de l'API:

- **Swagger UI**: `/api/plugins/swagger/`
- **ReDoc**: `/api/plugins/redoc/`

## Exemples de plugins inclus

### AlertHandlers

- **EmailAlertHandler**: Envoie des notifications par email
- **SlackAlertHandler**: Envoie des notifications sur Slack

### DashboardWidgets

- **SystemStatsWidget**: Affiche des statistiques système en temps réel

### ReportGenerators

_À venir... 