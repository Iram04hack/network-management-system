"""
Script de migration des données depuis l'ancien module reporting.

Ce script permet de migrer les données de l'ancien module reporting 
(/django_backend/reporting/) vers le nouveau module (/django__backend/reporting/).
"""

import os
import sys
import logging
from django.core.management.base import BaseCommand
from django.db import connections, transaction
from django.conf import settings
from django.apps import apps
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Migre les données depuis l\'ancien module reporting vers le nouveau'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source-db',
            dest='source_db',
            type=str,
            default='source',
            help='Alias de la base de données source dans DATABASES'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Exécuter sans réellement migrer les données'
        )
        parser.add_argument(
            '--include-models',
            type=str,
            help='Liste des modèles à migrer (séparés par une virgule). Par défaut, tous les modèles sont migrés.'
        )
    
    def handle(self, *args, **options):
        source_db = options['source_db']
        dry_run = options['dry_run']
        include_models = options.get('include_models')
        
        if include_models:
            include_models = include_models.split(',')
        
        # Vérifier que la base de données source existe
        if source_db not in settings.DATABASES:
            # Si la source n'est pas configurée, nous allons essayer de la configurer dynamiquement
            self.setup_dynamic_source_db(source_db)
        
        # Vérifier à nouveau après la configuration dynamique
        if source_db not in settings.DATABASES:
            self.stderr.write(self.style.ERROR(f'Base de données source "{source_db}" non configurée dans settings.DATABASES'))
            self.stderr.write(self.style.ERROR('Veuillez configurer une source dans settings.py ou utiliser --source-db'))
            return
        
        # Récupérer les modèles du module reporting
        reporting_app = apps.get_app_config('reporting')
        models = reporting_app.get_models()
        
        if include_models:
            models = [model for model in models if model.__name__ in include_models]
        
        self.stdout.write(f'{"(DRY RUN) " if dry_run else ""}Migration des données depuis {source_db} vers default')
        
        # Migrer les données pour chaque modèle
        for model in models:
            self.migrate_model(model, source_db, dry_run)
    
    def setup_dynamic_source_db(self, source_db):
        """Configure dynamiquement une base de données source basée sur la configuration actuelle."""
        try:
            # Récupérer la configuration actuelle de la base de données par défaut
            default_config = settings.DATABASES['default'].copy()
            
            # Déterminer le chemin vers l'ancienne base de données
            if default_config['ENGINE'] == 'django.db.backends.sqlite3':
                # Pour SQLite, utiliser un autre fichier de base de données
                default_path = default_config.get('NAME', '')
                old_path = default_path.replace('django__backend', 'django_backend')
                
                if os.path.exists(old_path):
                    # Configurer une nouvelle connexion à la base de données source
                    settings.DATABASES[source_db] = default_config.copy()
                    settings.DATABASES[source_db]['NAME'] = old_path
                    self.stdout.write(self.style.SUCCESS(f'Base de données source "{source_db}" configurée dynamiquement: {old_path}'))
                else:
                    self.stderr.write(self.style.ERROR(f'Base de données source introuvable: {old_path}'))
            else:
                # Pour d'autres types de bases de données (PostgreSQL, MySQL, etc.)
                self.stderr.write(self.style.ERROR(f'Configuration dynamique non prise en charge pour {default_config["ENGINE"]}'))
                self.stderr.write(self.style.ERROR('Veuillez configurer manuellement la source dans settings.py'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erreur lors de la configuration dynamique de la source: {e}'))
    
    def migrate_model(self, model, source_db, dry_run):
        """Migre les données d'un modèle depuis la source vers la destination."""
        model_name = model.__name__
        self.stdout.write(f'Migration du modèle {model_name}...')
        
        try:
            # Récupérer la connection à la base de données source
            with connections[source_db].cursor() as cursor:
                table_name = model._meta.db_table
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                self.stdout.write(f'  - {count} enregistrements à migrer')
                
                if count == 0:
                    self.stdout.write(f'  - Aucun enregistrement à migrer pour {model_name}')
                    return
                
                # Récupérer les données de la source
                cursor.execute(f"SELECT * FROM {table_name}")
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                if dry_run:
                    self.stdout.write(self.style.SUCCESS(f'  - (DRY RUN) {len(rows)} enregistrements seraient migrés pour {model_name}'))
                    return
                
                # Migration des données
                with transaction.atomic():
                    # Supprimer toutes les données existantes dans la destination
                    model.objects.all().delete()
                    
                    # Insérer les nouvelles données
                    for row in rows:
                        data = dict(zip(columns, row))
                        # Gesttion spéciale pour les clés étrangères vers User
                        if 'created_by_id' in data and data['created_by_id']:
                            # Vérifier si l'utilisateur existe dans la destination
                            try:
                                User.objects.get(pk=data['created_by_id'])
                            except User.DoesNotExist:
                                # Si l'utilisateur n'existe pas, utiliser l'utilisateur admin par défaut ou None
                                try:
                                    admin_user = User.objects.get(username='admin')
                                    data['created_by_id'] = admin_user.id
                                except User.DoesNotExist:
                                    data['created_by_id'] = None
                        
                        # Créer l'objet dans la destination
                        instance = model(**data)
                        instance.save()
                
                self.stdout.write(self.style.SUCCESS(f'  - {len(rows)} enregistrements migrés pour {model_name}'))
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erreur lors de la migration du modèle {model_name}: {e}'))
            logging.exception(f'Exception lors de la migration du modèle {model_name}: {e}') 