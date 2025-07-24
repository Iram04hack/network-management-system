# Guide d'utilisation des optimisations du module AI Assistant

Ce guide explique comment utiliser les optimisations de performance introduites dans la Phase 3 du module AI Assistant.

## Sommaire

1. [Introduction](#introduction)
2. [Mise en cache](#mise-en-cache)
3. [Streaming des réponses](#streaming-des-réponses)
4. [Embeddings vectoriels](#embeddings-vectoriels)
5. [Configuration](#configuration)
6. [Outils de diagnostic](#outils-de-diagnostic)

## Introduction

La Phase 3 du module AI Assistant introduit plusieurs optimisations majeures pour améliorer les performances, la réactivité et la pertinence des résultats :

- **Mise en cache** : Stockage temporaire des réponses pour éviter des appels API répétitifs
- **Streaming des réponses** : Affichage progressif des réponses à mesure qu'elles sont générées
- **Embeddings vectoriels** : Recherche sémantique avancée dans la base de connaissances

Ces optimisations peuvent être activées individuellement selon vos besoins et peuvent être configurées via différents paramètres.

## Mise en cache

La mise en cache permet de stocker temporairement les réponses générées par l'IA pour éviter de solliciter l'API pour des requêtes identiques ou très similaires.

### Avantages

- Réduction significative du temps de réponse pour les requêtes répétitives
- Économie de coûts d'API
- Réduction de la charge sur les services externes

### Utilisation

La mise en cache est activée par défaut. Pour la configurer manuellement :

```bash
# Activer la mise en cache
python manage.py optimize_ai_assistant --enable-cache

# Désactiver la mise en cache
python manage.py optimize_ai_assistant --disable-cache

# Vider le cache
python manage.py optimize_ai_assistant --clear-cache
```

### Configuration avancée

Vous pouvez ajuster les paramètres de cache dans `settings.py` :

```python
# Durée de validité du cache en secondes (1 heure par défaut)
AI_ASSISTANT_CACHE_TIMEOUT = 3600
```

## Streaming des réponses

Le streaming permet d'afficher les réponses de l'IA progressivement, à mesure qu'elles sont générées, plutôt que d'attendre la fin de la génération.

### Avantages

- Meilleure expérience utilisateur avec un affichage progressif
- Perception de rapidité accrue
- Possibilité d'interrompre la génération si la réponse n'est pas satisfaisante

### Utilisation

Le streaming fonctionne via WebSocket pour permettre une communication en temps réel avec le navigateur.

Pour activer ou désactiver le streaming :

```bash
# Activer le streaming
python manage.py optimize_ai_assistant --enable-streaming

# Désactiver le streaming
python manage.py optimize_ai_assistant --disable-streaming
```

### Intégration frontend

Pour intégrer le streaming dans votre interface :

```javascript
// Établir une connexion WebSocket
const socket = new WebSocket('ws://votre-serveur.com/ws/ai_assistant/');

// Écouter les messages
socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch (data.type) {
        case 'message_chunk':
            // Ajouter le fragment à la réponse en cours d'affichage
            appendResponseChunk(data.content);
            break;
        
        case 'message_complete':
            // Traitement final (actions, sources, etc.)
            finalizeResponse(data);
            break;
    }
};

// Envoyer un message
socket.send(JSON.stringify({
    type: 'message',
    conversation_id: 'your-conversation-id',
    content: 'Votre question ici'
}));
```

## Embeddings vectoriels

Les embeddings vectoriels permettent d'améliorer considérablement la qualité des recherches dans la base de connaissances en utilisant la similarité sémantique plutôt que la simple correspondance de mots-clés.

### Avantages

- Recherche basée sur le sens plutôt que sur les mots exacts
- Meilleure compréhension du contexte et des concepts liés
- Résultats plus pertinents pour des requêtes complexes ou ambiguës

### Utilisation

Pour activer ou configurer les embeddings :

```bash
# Activer les embeddings vectoriels
python manage.py optimize_ai_assistant --enable-embeddings

# Désactiver les embeddings vectoriels
python manage.py optimize_ai_assistant --disable-embeddings

# Configurer Elasticsearch pour les embeddings
python manage.py optimize_ai_assistant --setup-elasticsearch
```

### Utilisation des embeddings dans votre code

Les embeddings peuvent être utilisés directement via les fonctions utilitaires :

```python
from ai_assistant.utils.embedding_utils import generate_embedding, cosine_similarity, get_similar_chunks

# Générer un embedding pour un texte
embedding = generate_embedding("Comment optimiser les performances réseau?")

# Trouver des chunks de texte similaires
texts = ["Optimisation des réseaux", "Configuration des serveurs", "Sécurité des données"]
similar_chunks = get_similar_chunks("performances réseau", texts)
```

## Configuration

### Fichier de configuration

Les paramètres d'optimisation peuvent être configurés dans le fichier `settings.py` :

```python
# Configuration du cache
AI_ASSISTANT_CACHE_ENABLED = True
AI_ASSISTANT_CACHE_TIMEOUT = 3600  # 1 heure

# Configuration des embeddings
AI_ASSISTANT_ENABLE_EMBEDDINGS = True
AI_ASSISTANT_EMBEDDING_MODEL = 'text-embedding-ada-002'
AI_ASSISTANT_EMBEDDING_DIMENSION = 768

# Configuration du streaming
AI_ASSISTANT_ENABLE_STREAMING = True
```

### Variables d'environnement

Vous pouvez également configurer ces paramètres via des variables d'environnement :

```bash
# Cache
export AI_CACHE_ENABLED=True
export AI_CACHE_TIMEOUT=3600

# Embeddings
export AI_ENABLE_EMBEDDINGS=True
export AI_EMBEDDING_MODEL=text-embedding-ada-002
export AI_EMBEDDING_DIMENSION=768

# Streaming
export AI_ENABLE_STREAMING=True
```

## Outils de diagnostic

### Benchmark des optimisations

Pour évaluer les gains de performance des optimisations, utilisez la commande de benchmark :

```bash
# Exécuter tous les benchmarks
python manage.py benchmark_optimizations

# Benchmarks spécifiques
python manage.py benchmark_optimizations --cache-benchmark
python manage.py benchmark_optimizations --embedding-benchmark
python manage.py benchmark_optimizations --streaming-benchmark

# Nombre d'itérations personnalisé
python manage.py benchmark_optimizations --iterations 10
```

### Journalisation

Les optimisations génèrent des logs détaillés que vous pouvez consulter pour diagnostiquer les problèmes ou évaluer les performances :

```
# Format des logs pour le cache
[INFO] ai_assistant.infrastructure.ai_client_impl - Réponse récupérée du cache pour la clé: ai_response:03d1b...

# Format des logs pour les embeddings
[DEBUG] ai_assistant.utils.embedding_utils - Embedding généré en 0.325s

# Format des logs pour le streaming
[DEBUG] ai_assistant.consumers - Streaming démarré pour la conversation 123, fragment #1 envoyé
```

## Conclusion

Les optimisations de la Phase 3 du module AI Assistant permettent d'améliorer significativement les performances et l'expérience utilisateur. En fonction de vos besoins spécifiques, vous pouvez activer et configurer ces optimisations pour obtenir les meilleurs résultats.

Pour toute question ou problème, consultez la documentation complète ou contactez l'équipe de support technique. 