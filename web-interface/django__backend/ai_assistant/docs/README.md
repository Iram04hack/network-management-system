# Module AI Assistant

Ce module fournit une interface d'assistant IA pour le système de gestion de réseau.

## Fonctionnalités

- Intégration avec des modèles d'IA pour répondre aux questions des utilisateurs
- Optimisations de performance (cache, streaming, embeddings)
- Outils de benchmark pour mesurer les performances
- Interface utilisateur intuitive

## Documentation

- [Guide d'installation](INSTALLATION.md)
- [Guide d'utilisation](GUIDE_UTILISATION.md)
- [Résumé des optimisations](RESUME_OPTIMISATIONS.md)
- [API Reference](API_REFERENCE.md)

## Commandes Django

Le module fournit plusieurs commandes Django pour faciliter son utilisation:

### Optimisation

```bash
# Exécuter l'optimisation du module AI Assistant
python manage.py run_optimize [options]
```

### Benchmark

```bash
# Tester les performances des optimisations
python manage.py benchmark_optimizations [options]
```

### Autres commandes

```bash
# Initialiser le chatbot
python manage.py init_chatbot

# Tester la connexion à l'API IA
python manage.py test_ai_connection
```

Pour plus de détails sur les commandes et leurs options, consultez le [Guide d'utilisation](GUIDE_UTILISATION.md). 