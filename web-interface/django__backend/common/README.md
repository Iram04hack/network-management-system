# Service Central GNS3 - Infrastructure Complète

## 🚀 Vue d'ensemble

Le Service Central GNS3 est une infrastructure complète et centralisée pour la communication avec GNS3 et la gestion des événements réseau temps réel. Il simplifie l'intégration des différents modules du système de gestion réseau (NMS) avec GNS3.

## 📋 Fonctionnalités Principales

### 🎛️ Service Central GNS3
- **Connexion unique** et persistante au serveur GNS3
- **Cache Redis** pour performances optimales
- **API unifiée** pour toutes les opérations GNS3
- **Gestion automatique** des reconnexions
- **Circuit breaker** pour la résilience

### ⚡ Système d'Événements Temps Réel
- **WebSocket** pour communication bidirectionnelle
- **Redis Pub/Sub** pour distribution d'événements
- **Queue système** avec priorités (CRITICAL → HIGH → NORMAL → LOW)
- **Retry logic** pour événements échoués
- **Métriques** et monitoring complets

### 🔌 Interface Module Simplifiée
- **API transparente** pour les modules externes
- **Cache automatique** et gestion d'erreurs
- **Abonnements événements** plug-and-play
- **Abstraction complète** de la complexité GNS3

### 📡 Communication Inter-Modules
- **Message bus** centralisé
- **Types de messages** standardisés
- **Diffusion ciblée** ou broadcast
- **Corrélation** des événements

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Service Central GNS3                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │   Cache     │  │   WebSocket  │  │   Système d'Événements │ │
│  │   Redis     │  │   Channels   │  │   Temps Réel            │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              API REST + Swagger Documentation               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                Interface Module Simplifiée                 │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Serveur GNS3                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Projets   │  │    Nœuds    │  │      Topologie          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Modules du NMS                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Monitoring  │  │  Security   │  │       Analysis          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Installation et Configuration

### 1. Prérequis
```bash
# Redis (pour cache et événements)
sudo apt-get install redis-server

# PostgreSQL (pour persistance)
sudo apt-get install postgresql postgresql-contrib

# Python packages (déjà dans requirements.txt)
pip install channels channels-redis redis asyncio websockets
```

### 2. Configuration Django
Ajouté automatiquement dans `settings.py` :
```python
# Redis Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, int(REDIS_PORT))],
        },
    },
}

# GNS3 Configuration
GNS3_HOST = os.environ.get('GNS3_HOST', 'localhost')
GNS3_PORT = int(os.environ.get('GNS3_PORT', '3080'))
GNS3_PROTOCOL = os.environ.get('GNS3_PROTOCOL', 'http')
GNS3_TIMEOUT = int(os.environ.get('GNS3_TIMEOUT', '30'))
```

### 3. Migrations
```bash
# Appliquer les migrations
python manage.py migrate
```

## 🚀 Utilisation

### 1. Démarrage du Service
```bash
# Démarrage complet
python manage.py start_gns3_service

# Mode debug
python manage.py start_gns3_service --debug

# Sans événements temps réel
python manage.py start_gns3_service --no-events

# Mode test
python manage.py start_gns3_service --test-mode
```

### 2. API REST Endpoints

#### Service Central
```bash
# État du service
GET /api/common/api/gns3-central/status/

# Topologie complète
GET /api/common/api/gns3-central/topology/

# Démarrer un nœud
POST /api/common/api/gns3-central/start_node/
{
  "project_id": "uuid",
  "node_id": "uuid"
}

# Arrêter un nœud
POST /api/common/api/gns3-central/stop_node/
{
  "project_id": "uuid", 
  "node_id": "uuid"
}

# Redémarrer un nœud
POST /api/common/api/gns3-central/restart_node/
{
  "project_id": "uuid",
  "node_id": "uuid"
}

# Démarrer un projet complet
POST /api/common/api/gns3-central/start_project/
{
  "project_id": "uuid"
}

# Rafraîchir la topologie
POST /api/common/api/gns3-central/refresh_topology/
```

#### Événements
```bash
# Statistiques d'événements
GET /api/common/api/gns3-events/stats/
```

#### Interface Modules
```bash
# Créer une interface pour un module
POST /api/common/api/gns3-central/create_module_interface/
{
  "module_name": "monitoring"
}
```

### 3. WebSocket Connections

#### Connexion de base
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/gns3/events/');

ws.onopen = function(event) {
    console.log('Connexion WebSocket GNS3 établie');
    
    // S'abonner aux événements
    ws.send(JSON.stringify({
        'type': 'subscribe',
        'subscriptions': ['node_status', 'topology_changes']
    }));
};

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Événement reçu:', data);
};
```

#### Actions via WebSocket
```javascript
// Démarrer un nœud
ws.send(JSON.stringify({
    'type': 'node_action',
    'action': 'start',
    'project_id': 'uuid',
    'node_id': 'uuid'
}));

// Demander la topologie
ws.send(JSON.stringify({
    'type': 'request_topology'
}));
```

### 4. Intégration Module

#### Utilisation de l'interface simplifiée
```python
from common.api.gns3_module_interface import create_gns3_interface

# Créer l'interface pour votre module
gns3_interface = create_gns3_interface('monitoring')

# Initialiser (asynchrone)
await gns3_interface.initialize()

# Obtenir le statut d'un nœud
node_status = gns3_interface.get_node_status('node-uuid')

# Démarrer un nœud
result = await gns3_interface.start_node('project-uuid', 'node-uuid')

# S'abonner aux événements
def handle_gns3_event(event):
    print(f"Événement reçu: {event.event_type}")

gns3_interface.subscribe_to_events(
    ['node_status', 'topology_changes'],
    handle_gns3_event
)

# Obtenir un résumé du réseau
summary = gns3_interface.get_network_summary()
```

## 📊 Monitoring et Métriques

### Types d'Événements GNS3
- `node.started` - Nœud démarré
- `node.stopped` - Nœud arrêté
- `node.suspended` - Nœud suspendu
- `node.created` - Nouveau nœud créé
- `node.deleted` - Nœud supprimé
- `project.opened` - Projet ouvert
- `project.closed` - Projet fermé
- `topology.changed` - Changement de topologie
- `link.created` - Nouveau lien créé
- `link.deleted` - Lien supprimé

### Priorités d'Événements
- `CRITICAL` - Événements critiques (traités immédiatement)
- `HIGH` - Haute priorité (actions réseau importantes)
- `NORMAL` - Priorité normale (mises à jour standard)
- `LOW` - Faible priorité (informations de routine)

### Métriques Disponibles
- Nombre d'événements traités
- Temps de réponse API moyen
- Ratio cache hit/miss
- Connexions WebSocket actives
- Statut des modules connectés

## 🔧 Configuration Avancée

### Variables d'Environnement
```bash
# GNS3 Server
export GNS3_HOST=localhost
export GNS3_PORT=3080
export GNS3_PROTOCOL=http
export GNS3_USERNAME=admin
export GNS3_PASSWORD=password
export GNS3_TIMEOUT=30

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0

# Service Central
export GNS3_AUTO_MONITOR=true
export GNS3_MONITOR_INTERVAL=30
export GNS3_CACHE_TTL=300
```

### Configuration Personnalisée
```python
# Dans votre module
from common.infrastructure.gns3_central_service import gns3_central_service

# Personnaliser la configuration
gns3_central_service.gns3_config.update({
    'host': 'custom-gns3-server',
    'port': 3080,
    'timeout': 60
})
```

## 🧪 Tests et Debugging

### Mode Debug
```bash
python manage.py start_gns3_service --debug
```

### Tests de Connectivité
```python
from common.infrastructure.gns3_central_service import gns3_central_service

# Tester la connexion
status = gns3_central_service.get_service_status()
print(f"Statut: {status['status']}")
print(f"GNS3 connecté: {status['gns3_server']['connected']}")
```

### Logs et Monitoring
```python
import logging

# Activer les logs détaillés
logging.getLogger('common.infrastructure').setLevel(logging.DEBUG)
```

## 📚 Documentation API

### Swagger Documentation
- **Interface interactive** : `http://localhost:8000/api/docs/`
- **Documentation ReDoc** : `http://localhost:8000/api/redoc/`
- **Schéma JSON** : `http://localhost:8000/api/schema/`

### Endpoints Compatibilité
- `/api/gns3/status/` - Ancien endpoint de statut
- `/api/gns3/nodes/start/` - Ancien endpoint de démarrage nœud
- `/api/gns3/topology/` - Ancien endpoint de topologie

## 🔒 Sécurité

### Authentification
Toutes les APIs nécessitent une authentification Django standard.

### WebSocket Security
- **AllowedHostsOriginValidator** pour valider les origines
- **AuthMiddlewareStack** pour l'authentification des connexions
- **Filtrage par abonnements** pour limiter l'accès aux événements

### Gestion des Erreurs
- **Circuit breaker** pour éviter les cascades d'erreurs
- **Retry logic** avec backoff exponentiel
- **Isolation des erreurs** par module

## 🚧 Développement Futur

### Améliorations Prévues
- [ ] Support WebSocket natif GNS3 (v3.0+)
- [ ] Clustering multi-serveurs GNS3
- [ ] Interface graphique temps réel
- [ ] Métriques Prometheus/Grafana
- [ ] Support notifications Slack/Teams
- [ ] API REST versionnée (v2)

### Contributions
Pour contribuer au développement :
1. Respecter l'architecture événementielle
2. Utiliser l'interface module simplifiée
3. Implémenter la gestion d'erreurs robuste
4. Ajouter tests unitaires et d'intégration
5. Documenter les nouvelles fonctionnalités

## 📞 Support

### Logs d'Erreurs
```bash
# Logs du service central
tail -f logs/gns3_central_service.log

# Logs des événements
tail -f logs/realtime_events.log

# Logs Django
tail -f logs/django.log
```

### Commandes de Diagnostic
```bash
# Vérifier l'état du service
python manage.py shell -c "
from common.infrastructure.gns3_central_service import gns3_central_service
print(gns3_central_service.get_service_status())
"

# Statistiques d'événements
python manage.py shell -c "
from common.infrastructure.realtime_event_system import realtime_event_manager
print(realtime_event_manager.get_statistics())
"
```

---

## 🎉 Infrastructure Complète Déployée !

L'infrastructure Service Central GNS3 est maintenant **complètement déployée** et **opérationnelle** avec :

✅ **Service Central GNS3** avec cache Redis et gestion d'événements  
✅ **API REST complète** avec documentation Swagger automatique  
✅ **Système d'événements temps réel** avec WebSocket et Redis Pub/Sub  
✅ **Interface simplifiée** pour intégration facile des modules  
✅ **Migrations appliquées** et base de données configurée  
✅ **Commandes de gestion** pour démarrage et monitoring  
✅ **Documentation complète** et exemples d'utilisation  

**L'infrastructure est prête** pour que tous les modules puissent **facilement intégrer GNS3** ! 🚀