# Guide d'utilisation des commandes d'optimisation et de benchmark

Ce document explique comment utiliser les commandes d'optimisation et de benchmark du module AI Assistant.

## Commande d'optimisation

La commande `run_optimize` permet d'exécuter les optimisations du module AI Assistant directement depuis Django.

### Utilisation

```bash
python manage.py run_optimize [options]
```

### Options

- `--redis-host`: Adresse IP du serveur Redis (par défaut: 172.18.0.3)
- `--redis-port`: Port du serveur Redis (par défaut: 6379)
- `--force`: Force la réoptimisation même si déjà optimisé

### Exemple

```bash
# Exécuter l'optimisation avec les paramètres par défaut
python manage.py run_optimize

# Exécuter l'optimisation avec un serveur Redis personnalisé
python manage.py run_optimize --redis-host=localhost --redis-port=6379

# Forcer la réoptimisation
python manage.py run_optimize --force
```

## Commande de benchmark

La commande `benchmark_optimizations` permet de tester les performances des différentes optimisations du module AI Assistant.

### Utilisation

```bash
python manage.py benchmark_optimizations [options]
```

### Options

- `--iterations`: Nombre d'itérations pour chaque configuration (par défaut: 5)
- `--redis-host`: Adresse IP du serveur Redis (par défaut: 172.18.0.3)
- `--redis-port`: Port du serveur Redis (par défaut: 6379)
- `--config`: Configuration à tester (choix: base, cache, streaming, embeddings, all, compare; par défaut: compare)

### Exemple

```bash
# Exécuter le benchmark complet avec les paramètres par défaut
python manage.py benchmark_optimizations

# Exécuter le benchmark avec 10 itérations
python manage.py benchmark_optimizations --iterations=10

# Tester uniquement la configuration avec cache
python manage.py benchmark_optimizations --config=cache

# Tester toutes les optimisations ensemble
python manage.py benchmark_optimizations --config=all
```

## Résultats du benchmark

Les résultats du benchmark sont affichés dans la console et incluent:

1. Le temps moyen de réponse pour chaque configuration
2. L'écart-type des temps de réponse
3. Le pourcentage d'amélioration par rapport à la configuration de base

Exemple de résultat:

```
=== RÉSUMÉ DES BENCHMARKS ===
Configuration              Temps moyen      Écart-type 
--------------------------------------------------
Base                       2.00s            0.00s
Base+Cache                 1.82s            0.40s
Base+Streaming             2.00s            0.00s
Base+Embeddings            1.90s            0.00s
Base+Cache+Streaming+Embeddings 1.62s       0.40s

=== AMÉLIORATIONS DE PERFORMANCE ===
Base+Cache: 9.0% d'amélioration
Base+Streaming: 0.0% d'amélioration
Base+Embeddings: 5.0% d'amélioration
Base+Cache+Streaming+Embeddings: 19.0% d'amélioration
``` 