#!/usr/bin/env python
"""
Commande Django pour exécuter l'optimisation de l'AI Assistant.

Cette commande permet d'exécuter les optimisations du module AI Assistant
directement depuis le framework Django, en contournant les problèmes
d'importation circulaire potentiels.
"""

import os
import sys
import django
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = "Exécute l'optimisation du module AI Assistant"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--redis-host',
            type=str,
            default='172.18.0.2',
            help='Adresse IP du serveur Redis'
        )
        parser.add_argument(
            '--redis-port',
            type=int,
            default=6379,
            help='Port du serveur Redis'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la réoptimisation même si déjà optimisé'
        )
    
    def handle(self, *args, **options):
        redis_host = options.get('redis_host')
        redis_port = options.get('redis_port')
        force = options.get('force')
        
        # Configurer les variables d'environnement pour Redis
        os.environ['REDIS_HOST'] = redis_host
        os.environ['REDIS_PORT'] = str(redis_port)
        
        self.stdout.write(self.style.NOTICE("Exécution de la commande d'optimisation AI Assistant..."))
        
        # Import direct de la commande d'optimisation pour éviter les importations circulaires
        from ai_assistant.management.commands.optimize_ai_assistant import Command as OptimizeCommand
        
        # Exécuter la commande d'optimisation
        optimize_command = OptimizeCommand()
        optimize_command.handle(force=force)
        
        self.stdout.write(self.style.SUCCESS("Optimisation terminée avec succès.")) 