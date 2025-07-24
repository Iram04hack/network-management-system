# 📚 API Reference - Module AI Assistant

## Vue d'ensemble

Ce document fournit la référence complète de l'API du module AI Assistant migré. Le module utilise une architecture basée sur les services de domaine avec une API REST complète.

## 🏗️ Architecture

Le module suit une architecture orientée services avec les couches suivantes :

- **API Layer** (`/api/`) : Points d'entrée REST avec sérialiseurs et vues
- **Application Layer** (`/application/`) : Services d'orchestration et cas d'utilisation
- **Domain Layer** (`/domain/`) : Services métier, entités et interfaces
- **Infrastructure Layer** (`/infrastructure/`) : Implémentations concrètes des interfaces

## 🌐 API Endpoints

### Conversations

#### `GET /api/conversations/`
Récupère la liste des conversations de l'utilisateur.

**Paramètres de requête :**
- `page` (int, optionnel) : Numéro de page
- `page_size` (int, optionnel) : Taille de page (défaut : 20)
- `search` (string, optionnel) : Recherche dans les titres

**Réponse :**
```json
{
  "count": 25,
  "next": "http://api/conversations/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Configuration VLAN",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:15:00Z",
      "message_count": 5,
      "last_message_preview": "Voici la configuration recommandée..."
    }
  ]
}
```

#### `POST /api/conversations/`
Crée une nouvelle conversation.

**Corps de requête :**
```json
{
  "title": "Nouvelle conversation",
  "initial_message": "Comment configurer un VLAN ?"
}
```

**Réponse :**
```json
{
  "id": 2,
  "title": "Nouvelle conversation",
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T12:00:00Z",
  "message_count": 1
}
```

#### `GET /api/conversations/{id}/`
Récupère une conversation spécifique avec ses messages.

**Réponse :**
```json
{
  "id": 1,
  "title": "Configuration VLAN",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:15:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "Comment configurer un VLAN ?",
      "timestamp": "2024-01-15T10:30:00Z",
      "metadata": {}
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "Voici les étapes pour configurer un VLAN...",
      "timestamp": "2024-01-15T10:31:00Z",
      "metadata": {
        "confidence": 0.95,
        "sources": ["doc_vlan_config.md"],
        "actions": [
          {
            "type": "command",
            "data": {"cmd": "vlan database"}
          }
        ]
      }
    }
  ]
}
```

#### `POST /api/conversations/{id}/messages/`
Ajoute un message à une conversation existante.

**Corps de requête :**
```json
{
  "content": "Peux-tu détailler la configuration du trunk ?",
  "context": {
    "previous_topic": "vlan_configuration"
  }
}
```

**Réponse :**
```json
{
  "user_message": {
    "id": 3,
    "role": "user",
    "content": "Peux-tu détailler la configuration du trunk ?",
    "timestamp": "2024-01-15T11:00:00Z"
  },
  "assistant_response": {
    "id": 4,
    "role": "assistant",
    "content": "Pour configurer un port trunk...",
    "timestamp": "2024-01-15T11:01:00Z",
    "metadata": {
      "confidence": 0.92,
      "processing_time": 1.2,
      "actions": []
    }
  }
}
```

### Commandes

#### `POST /api/commands/execute/`
Exécute une commande système avec analyse IA préalable.

**Corps de requête :**
```json
{
  "command": "ping 192.168.1.1",
  "type": "network",
  "parameters": {
    "count": 4,
    "timeout": 10
  },
  "validation_level": "strict"
}
```

**Réponse :**
```json
{
  "success": true,
  "command_id": "cmd_123456",
  "execution_time": 2.5,
  "output": {
    "stdout": "PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data...",
    "stderr": "",
    "return_code": 0
  },
  "analysis": {
    "safety_score": 0.98,
    "detected_risks": [],
    "recommendations": []
  },
  "metadata": {
    "executed_at": "2024-01-15T12:00:00Z",
    "executor": "system",
    "user_id": 1
  }
}
```

#### `GET /api/commands/history/`
Récupère l'historique des commandes exécutées.

**Paramètres de requête :**
- `limit` (int) : Nombre maximum de résultats
- `command_type` (string) : Filtrer par type (network, system, sql, python)
- `date_from` (string) : Date de début (ISO format)
- `date_to` (string) : Date de fin (ISO format)

**Réponse :**
```json
{
  "commands": [
    {
      "id": "cmd_123456",
      "command": "ping 192.168.1.1",
      "type": "network",
      "executed_at": "2024-01-15T12:00:00Z",
      "success": true,
      "execution_time": 2.5,
      "user_id": 1
    }
  ],
  "total": 45,
  "page": 1,
  "has_next": true
}
```

#### `POST /api/commands/validate/`
Valide une commande sans l'exécuter.

**Corps de requête :**
```json
{
  "command": "rm -rf /important_data",
  "type": "system"
}
```

**Réponse :**
```json
{
  "is_safe": false,
  "safety_score": 0.15,
  "warnings": [
    {
      "level": "critical",
      "message": "Commande destructive détectée",
      "suggestion": "Utilisez une commande plus spécifique"
    }
  ],
  "blocked": true,
  "reason": "Commande potentiellement dangereuse"
}
```

### Documents

#### `GET /api/documents/`
Liste les documents disponibles.

**Paramètres de requête :**
- `category` (string) : Filtrer par catégorie
- `search` (string) : Recherche textuelle
- `tags` (string) : Filtrer par tags (séparés par virgule)
- `is_public` (boolean) : Filtrer par visibilité

**Réponse :**
```json
{
  "documents": [
    {
      "id": 1,
      "title": "Guide Configuration VLAN",
      "summary": "Guide complet pour la configuration des VLANs",
      "category": "network",
      "tags": ["vlan", "network", "configuration"],
      "author": "Network Team",
      "is_public": true,
      "created_at": "2024-01-10T09:00:00Z",
      "updated_at": "2024-01-12T15:30:00Z"
    }
  ],
  "total": 150,
  "categories": ["network", "security", "troubleshooting"],
  "page": 1
}
```

#### `GET /api/documents/{id}/`
Récupère un document spécifique.

**Réponse :**
```json
{
  "id": 1,
  "title": "Guide Configuration VLAN",
  "content": "# Configuration VLAN\n\nLes VLANs permettent...",
  "summary": "Guide complet pour la configuration des VLANs",
  "category": "network",
  "tags": ["vlan", "network", "configuration"],
  "author": "Network Team",
  "is_public": true,
  "created_at": "2024-01-10T09:00:00Z",
  "updated_at": "2024-01-12T15:30:00Z",
  "metadata": {
    "version": "2.1",
    "reviewed_by": "Security Team",
    "related_documents": [2, 5, 8]
  }
}
```

#### `POST /api/documents/`
Crée un nouveau document.

**Corps de requête :**
```json
{
  "title": "Nouveau Guide Sécurité",
  "content": "# Guide Sécurité\n\nCe guide présente...",
  "category": "security",
  "tags": ["security", "best-practices"],
  "is_public": true,
  "metadata": {
    "version": "1.0",
    "language": "fr"
  }
}
```

### Recherche

#### `POST /api/search/`
Effectue une recherche globale.

**Corps de requête :**
```json
{
  "query": "configuration vlan trunk",
  "filters": {
    "categories": ["network", "documentation"],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-31"
    }
  },
  "options": {
    "max_results": 20,
    "include_snippets": true,
    "semantic_search": true
  }
}
```

**Réponse :**
```json
{
  "results": [
    {
      "type": "document",
      "id": 1,
      "title": "Configuration VLAN Trunk",
      "snippet": "Pour configurer un port en mode trunk...",
      "score": 0.95,
      "source": "documentation",
      "url": "/api/documents/1/",
      "metadata": {
        "category": "network",
        "tags": ["vlan", "trunk", "configuration"]
      }
    },
    {
      "type": "conversation",
      "id": 5,
      "title": "Discussion VLAN",
      "snippet": "Utilisateur: Comment configurer un trunk?\nAssistant: Voici les étapes...",
      "score": 0.87,
      "source": "conversations",
      "url": "/api/conversations/5/"
    }
  ],
  "total": 12,
  "query_analysis": {
    "intent": "configuration",
    "entities": ["vlan", "trunk"],
    "suggestions": ["port configuration", "switch setup"]
  },
  "execution_time": 0.45
}
```

#### `GET /api/search/suggestions/`
Obtient des suggestions de recherche.

**Paramètres de requête :**
- `q` (string) : Début de la requête
- `limit` (int) : Nombre maximum de suggestions

**Réponse :**
```json
{
  "suggestions": [
    {
      "text": "configuration vlan",
      "category": "network",
      "frequency": 45
    },
    {
      "text": "configuration vlan trunk",
      "category": "network",
      "frequency": 23
    }
  ]
}
```

### Analyse Réseau

#### `POST /api/network/ping/`
Effectue un ping vers une adresse.

**Corps de requête :**
```json
{
  "target": "192.168.1.1",
  "count": 4,
  "timeout": 5
}
```

**Réponse :**
```json
{
  "success": true,
  "target": "192.168.1.1",
  "packets_sent": 4,
  "packets_received": 4,
  "packet_loss": 0,
  "min_time": 1.2,
  "max_time": 2.8,
  "avg_time": 1.9,
  "results": [
    {
      "sequence": 1,
      "time": 1.5,
      "ttl": 64
    }
  ]
}
```

#### `POST /api/network/traceroute/`
Effectue un traceroute vers une destination.

**Corps de requête :**
```json
{
  "target": "8.8.8.8",
  "max_hops": 30
}
```

**Réponse :**
```json
{
  "success": true,
  "target": "8.8.8.8",
  "hops": [
    {
      "hop": 1,
      "ip": "192.168.1.1",
      "hostname": "router.local",
      "times": [1.2, 1.1, 1.3]
    },
    {
      "hop": 2,
      "ip": "10.0.0.1",
      "hostname": null,
      "times": [15.2, 14.8, 15.1]
    }
  ],
  "total_hops": 8,
  "destination_reached": true
}
```

#### `POST /api/network/scan/`
Effectue un scan réseau (nmap).

**Corps de requête :**
```json
{
  "target": "192.168.1.0/24",
  "scan_type": "ping_sweep",
  "options": {
    "fast_mode": true,
    "service_detection": false
  }
}
```

**Réponse :**
```json
{
  "success": true,
  "scan_id": "scan_789123",
  "target": "192.168.1.0/24",
  "hosts_discovered": [
    {
      "ip": "192.168.1.1",
      "hostname": "router.local",
      "status": "up",
      "mac_address": "AA:BB:CC:DD:EE:FF",
      "vendor": "Cisco Systems"
    }
  ],
  "scan_time": 15.3,
  "total_hosts": 254,
  "hosts_up": 12
}
```

## 🔧 Services de Domaine

### AIService

Service principal pour l'interaction avec l'IA.

**Méthodes principales :**
- `generate_response(prompt, context, conversation_id)` : Génère une réponse IA
- `analyze_command(command, context)` : Analyse une commande avec l'IA
- `get_model_status()` : Vérifie le statut des modèles IA

### ConversationService

Service de gestion des conversations.

**Méthodes principales :**
- `create_conversation(user_id, title)` : Crée une nouvelle conversation
- `get_conversation(conversation_id)` : Récupère une conversation
- `add_message(conversation_id, role, content, metadata)` : Ajoute un message
- `search_conversations(user_id, query)` : Recherche dans les conversations

### CommandService

Service d'exécution et validation des commandes.

**Méthodes principales :**
- `execute_command(command, command_type, user_id)` : Exécute une commande
- `validate_command(command, command_type)` : Valide une commande
- `get_command_history(user_id, filters)` : Récupère l'historique

### DocumentService

Service de gestion documentaire.

**Méthodes principales :**
- `create_document(title, content, category, tags)` : Crée un document
- `search_documents(query, filters)` : Recherche dans les documents
- `get_document_by_category(category)` : Récupère par catégorie

### NetworkAnalysisService

Service d'analyse réseau.

**Méthodes principales :**
- `ping(target, options)` : Effectue un ping
- `traceroute(target, options)` : Effectue un traceroute
- `port_scan(target, ports)` : Scanne des ports
- `network_discovery(subnet)` : Découverte réseau

### SearchService

Service de recherche avancée.

**Méthodes principales :**
- `search_global(query, filters)` : Recherche globale
- `search_documentation(query, limit)` : Recherche documentaire
- `get_search_suggestions(partial_query)` : Suggestions de recherche

## 🔒 Authentification et Permissions

### Headers requis

Toutes les requêtes API doivent inclure :
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Niveaux de permissions

- **viewer** : Lecture seule
- **editor** : Lecture + modification
- **admin** : Tous droits + gestion utilisateurs

### Gestion d'erreurs

#### Codes d'erreur HTTP

- `400` : Requête malformée
- `401` : Non authentifié
- `403` : Non autorisé
- `404` : Ressource non trouvée
- `429` : Trop de requêtes
- `500` : Erreur serveur

#### Format des erreurs

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Les données fournies sont invalides",
    "details": {
      "field": "command",
      "issue": "Commande trop longue (max 1000 caractères)"
    },
    "timestamp": "2024-01-15T12:00:00Z",
    "request_id": "req_123456"
  }
}
```

## 📊 Limites et Quotas

### Limites par défaut

- **Requêtes/minute** : 100 (viewer), 200 (editor), 500 (admin)
- **Taille max requête** : 10MB
- **Timeout requête** : 30 secondes
- **Conversations simultanées** : 10 par utilisateur
- **Historique commandes** : 1000 par utilisateur

### Headers de limite

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## 🔍 Exemples d'utilisation

### Conversation complète avec IA

```python
import requests

# 1. Créer une conversation
response = requests.post('/api/conversations/', {
    'title': 'Configuration réseau',
    'initial_message': 'Comment configurer un VLAN ?'
})
conversation_id = response.json()['id']

# 2. Ajouter des messages
response = requests.post(f'/api/conversations/{conversation_id}/messages/', {
    'content': 'Peux-tu me donner la commande exacte ?'
})

# 3. Récupérer l'historique
history = requests.get(f'/api/conversations/{conversation_id}/')
```

### Exécution de commande avec validation

```python
# 1. Valider la commande d'abord
validation = requests.post('/api/commands/validate/', {
    'command': 'ping 192.168.1.1',
    'type': 'network'
})

if validation.json()['is_safe']:
    # 2. Exécuter la commande
    result = requests.post('/api/commands/execute/', {
        'command': 'ping 192.168.1.1',
        'type': 'network',
        'parameters': {'count': 4}
    })
    print(result.json()['output']['stdout'])
```

### Recherche et découverte

```python
# Recherche globale
search_results = requests.post('/api/search/', {
    'query': 'configuration vlan',
    'filters': {'categories': ['network']},
    'options': {'semantic_search': True}
})

for result in search_results.json()['results']:
    print(f"{result['title']}: {result['snippet']}")
```

## 📝 Notes de migration

### Différences avec l'ancien module

1. **Architecture** : Passage de l'architecture hexagonale pure vers services de domaine
2. **API** : RESTification complète avec sérialiseurs DRF
3. **Sécurité** : Validation renforcée des commandes
4. **Recherche** : Nouveau service de recherche avancée
5. **Documentation** : Gestion documentaire intégrée

### Compatibilité

- **Endpoints dépréciés** : Voir section Migration Guide
- **Changements de format** : Métadonnées structurées différemment
- **Nouvelles fonctionnalités** : Services réseau et documents

---

*Documentation générée pour le module AI Assistant migré - Version 2.0*