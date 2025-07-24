# Guide d'utilisation des optimisations du module AI Assistant

Ce guide explique comment utiliser et configurer les optimisations de performance du module AI Assistant (Phase 3), notamment la mise en cache des réponses, le streaming et les embeddings vectoriels.

## Table des matières

1. [Introduction](#introduction)
2. [Prérequis](#prérequis)
3. [Configuration des optimisations](#configuration-des-optimisations)
4. [Mise en cache des réponses](#mise-en-cache-des-réponses)
5. [Streaming des réponses](#streaming-des-réponses)
6. [Embeddings vectoriels](#embeddings-vectoriels)
7. [Benchmark des optimisations](#benchmark-des-optimisations)
8. [Dépannage](#dépannage)

## Introduction

Le module AI Assistant a été optimisé pour améliorer les performances et l'expérience utilisateur grâce à trois fonctionnalités principales :

- **Mise en cache des réponses** : Stocke les réponses précédentes pour réduire le temps de réponse et les coûts d'API.
- **Streaming des réponses** : Affiche les réponses progressivement à mesure qu'elles sont générées.
- **Embeddings vectoriels** : Améliore la pertinence des réponses en utilisant des représentations vectorielles pour la recherche sémantique.

## Prérequis

Pour utiliser les optimisations, vous devez disposer des éléments suivants :

- Redis (pour la mise en cache et le streaming)
- Elasticsearch (pour les embeddings vectoriels)
- Les bibliothèques Python requises :
  - `redis`
  - `sentence-transformers`
  - `numpy`
  - `scikit-learn`

## Configuration des optimisations

### Configuration automatique

Utilisez la commande Django suivante pour configurer toutes les optimisations :

```bash
python manage.py optimize_ai_assistant
```

Ou utilisez le script direct si vous rencontrez des problèmes avec Django :

```bash
python direct_optimize.py
```

### Configuration manuelle

Si vous préférez configurer manuellement les optimisations, modifiez les fichiers suivants :

- `ai_assistant/config/settings.py` : Paramètres généraux du module
- `ai_assistant/config/optimizations.py` : Configuration spécifique des optimisations

## Mise en cache des réponses

### Comment ça fonctionne

La mise en cache stocke les réponses générées par l'IA dans Redis pour une réutilisation ultérieure. Lorsqu'une requête similaire est reçue, le système vérifie d'abord si une réponse existe déjà dans le cache avant de faire appel à l'API externe.

### Configuration

Dans `ai_assistant/config/optimizations.py` :

```python
# Mise en cache des réponses
CACHE_ENABLED = True
CACHE_TIMEOUT = 3600  # Durée de conservation en cache (en secondes)
```

### Utilisation dans le code

```python
from ai_assistant.config.optimizations import CACHE_ENABLED, CACHE_TIMEOUT

# Vérifier si le cache est activé
if CACHE_ENABLED:
    # Logique de mise en cache
```

## Streaming des réponses

### Comment ça fonctionne

Le streaming permet d'afficher les réponses de l'IA progressivement, à mesure qu'elles sont générées, plutôt que d'attendre la réponse complète. Cela améliore considérablement l'expérience utilisateur, surtout pour les réponses longues.

### Configuration

Dans `ai_assistant/config/optimizations.py` :

```python
# Streaming des réponses
ENABLE_STREAMING = True
STREAMING_CHUNK_SIZE = 50  # Taille des chunks en caractères
```

### Utilisation dans le code

Pour les vues WebSocket :

```python
from ai_assistant.config.optimizations import ENABLE_STREAMING

# Dans un consumer WebSocket
async def receive(self, text_data):
    # ...
    if ENABLE_STREAMING:
        # Utiliser le streaming
        for chunk in ai_client.generate_streaming(prompt):
            await self.send(text_data=json.dumps({
                'type': 'stream',
                'content': chunk
            }))
    else:
        # Génération classique
        response = ai_client.generate(prompt)
        await self.send(text_data=json.dumps({
            'type': 'response',
            'content': response
        }))
```

## Embeddings vectoriels

### Comment ça fonctionne

Les embeddings vectoriels transforment le texte en vecteurs numériques qui capturent le sens sémantique. Cela permet de rechercher des informations similaires conceptuellement, plutôt que par simple correspondance de mots-clés.

### Configuration

Dans `ai_assistant/config/optimizations.py` :

```python
# Embeddings vectoriels
ENABLE_EMBEDDINGS = True
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384
```

### Utilisation dans le code

```python
from ai_assistant.utils.embedding_utils import generate_embedding, compute_similarity

# Générer un embedding pour une requête
query_embedding = generate_embedding("Comment configurer un firewall?")

# Calculer la similarité avec d'autres textes
similarity = compute_similarity(query_embedding, document_embedding)
```

## Benchmark des optimisations

Pour évaluer l'impact des optimisations sur les performances, utilisez le script de benchmark :

```bash
python run_benchmark.py
```

Ce script teste les différentes combinaisons d'optimisations et affiche un rapport comparatif des performances.

## Dépannage

### Redis non disponible

Si Redis n'est pas disponible, la mise en cache et le streaming seront désactivés. Vérifiez que Redis est en cours d'exécution et accessible :

```bash
redis-cli ping
```

### Problèmes avec les embeddings

Si vous rencontrez des problèmes avec les embeddings vectoriels :

1. Vérifiez que Elasticsearch est correctement configuré et accessible
2. Assurez-vous que le modèle d'embedding est correctement installé :

```bash
pip install sentence-transformers
```

3. Vérifiez les logs pour les erreurs spécifiques

### Problèmes de performance

Si les optimisations n'améliorent pas les performances comme prévu :

1. Exécutez le benchmark pour identifier les goulots d'étranglement
2. Vérifiez la configuration de Redis (mémoire, persistance)
3. Ajustez les paramètres dans les fichiers de configuration 