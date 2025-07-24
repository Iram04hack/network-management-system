"""
Commande Django pour importer des règles de sécurité depuis un fichier.

Cette commande permet d'importer des règles de sécurité à partir de fichiers
au format JSON ou YAML.
"""

import os
import json
import yaml
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from security_management.di_container import container
from security_management.domain.exceptions import SecurityRuleValidationException, RuleConflictException


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Commande pour importer des règles de sécurité depuis un fichier.
    """
    
    help = 'Importe des règles de sécurité depuis un fichier JSON ou YAML'
    
    def add_arguments(self, parser):
        """
        Ajoute les arguments de la commande.
        """
        parser.add_argument(
            'file_path',
            type=str,
            help='Chemin vers le fichier de règles à importer'
        )
        
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'yaml'],
            default='json',
            help='Format du fichier (json ou yaml)'
        )
        
        parser.add_argument(
            '--skip-conflicts',
            action='store_true',
            help='Ignorer les règles qui entrent en conflit avec des règles existantes'
        )
        
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Remplacer les règles existantes avec le même nom'
        )
    
    def handle(self, *args, **options):
        """
        Exécute la commande.
        """
        file_path = options['file_path']
        file_format = options['format']
        skip_conflicts = options['skip_conflicts']
        replace = options['replace']
        
        # Vérifier que le fichier existe
        if not os.path.exists(file_path):
            raise CommandError(f"Le fichier {file_path} n'existe pas")
        
        # Charger les règles depuis le fichier
        try:
            rules = self.load_rules_from_file(file_path, file_format)
        except Exception as e:
            raise CommandError(f"Erreur lors du chargement du fichier: {e}")
        
        # Vérifier que les règles sont dans un format valide
        if not isinstance(rules, list):
            raise CommandError("Le fichier doit contenir une liste de règles")
        
        # Importer les règles
        imported_count = 0
        skipped_count = 0
        error_count = 0
        
        for rule_data in rules:
            try:
                # Si l'option replace est activée et que la règle existe déjà, la supprimer
                if replace and 'name' in rule_data:
                    existing_rules = container.rule_management_use_case.list_rules({'name': rule_data['name']})
                    for existing_rule in existing_rules:
                        self.stdout.write(f"Suppression de la règle existante: {existing_rule.name}")
                        container.rule_management_use_case.delete_rule(existing_rule.id)
                
                # Créer la règle
                rule = container.rule_management_use_case.create_rule(rule_data)
                self.stdout.write(self.style.SUCCESS(f"Règle importée avec succès: {rule.name}"))
                imported_count += 1
                
            except SecurityRuleValidationException as e:
                self.stdout.write(self.style.ERROR(f"Erreur de validation: {e.message}"))
                for detail in e.details:
                    self.stdout.write(f"  - {detail}")
                error_count += 1
                
            except RuleConflictException as e:
                if skip_conflicts:
                    self.stdout.write(self.style.WARNING(f"Règle ignorée (conflit): {rule_data.get('name', 'Sans nom')}"))
                    skipped_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f"Conflit de règles: {e.message}"))
                    for conflict in e.conflicts:
                        self.stdout.write(f"  - Conflit avec {conflict['rule_name']} (ID: {conflict['rule_id']})")
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors de l'importation: {e}"))
                error_count += 1
        
        # Afficher le résumé
        self.stdout.write("\nRésumé de l'importation:")
        self.stdout.write(f"  - Règles importées: {imported_count}")
        self.stdout.write(f"  - Règles ignorées: {skipped_count}")
        self.stdout.write(f"  - Erreurs: {error_count}")
        
        if imported_count > 0:
            self.stdout.write(self.style.SUCCESS("Importation terminée avec succès"))
        else:
            self.stdout.write(self.style.WARNING("Aucune règle n'a été importée"))
    
    def load_rules_from_file(self, file_path, file_format):
        """
        Charge les règles depuis un fichier.
        
        Args:
            file_path: Chemin vers le fichier
            file_format: Format du fichier (json ou yaml)
            
        Returns:
            Liste de règles
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_format == 'json':
                return json.load(f)
            elif file_format == 'yaml':
                return yaml.safe_load(f)
            else:
                raise ValueError(f"Format non supporté: {file_format}") 