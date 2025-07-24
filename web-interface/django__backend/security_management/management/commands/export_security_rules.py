"""
Commande Django pour exporter des règles de sécurité vers un fichier.

Cette commande permet d'exporter des règles de sécurité vers un fichier
au format JSON ou YAML.
"""

import os
import json
import yaml
import logging
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from security_management.di_container import container
from security_management.domain.entities import SecurityRule


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Commande pour exporter des règles de sécurité vers un fichier.
    """
    
    help = 'Exporte des règles de sécurité vers un fichier JSON ou YAML'
    
    def add_arguments(self, parser):
        """
        Ajoute les arguments de la commande.
        """
        parser.add_argument(
            'file_path',
            type=str,
            help='Chemin vers le fichier de sortie'
        )
        
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'yaml'],
            default='json',
            help='Format du fichier (json ou yaml)'
        )
        
        parser.add_argument(
            '--rule-type',
            type=str,
            help='Filtrer par type de règle (suricata, firewall, fail2ban, access_control)'
        )
        
        parser.add_argument(
            '--enabled-only',
            action='store_true',
            help='Exporter uniquement les règles activées'
        )
        
        parser.add_argument(
            '--pretty',
            action='store_true',
            help='Formater le fichier de sortie pour une meilleure lisibilité'
        )
    
    def handle(self, *args, **options):
        """
        Exécute la commande.
        """
        file_path = options['file_path']
        file_format = options['format']
        rule_type = options['rule_type']
        enabled_only = options['enabled_only']
        pretty = options['pretty']
        
        # Construire les filtres
        filters = {}
        if rule_type:
            filters['rule_type'] = rule_type
        if enabled_only:
            filters['enabled'] = True
        
        # Récupérer les règles
        rules = container.rule_management_use_case.list_rules(filters)
        
        # Convertir les règles en dictionnaires
        rules_data = [self.rule_to_dict(rule) for rule in rules]
        
        # Exporter les règles
        try:
            self.export_rules_to_file(rules_data, file_path, file_format, pretty)
            self.stdout.write(self.style.SUCCESS(
                f"{len(rules_data)} règles exportées avec succès vers {file_path}"
            ))
        except Exception as e:
            raise CommandError(f"Erreur lors de l'exportation: {e}")
    
    def rule_to_dict(self, rule):
        """
        Convertit une règle en dictionnaire.
        
        Args:
            rule: Instance de SecurityRule
            
        Returns:
            Dictionnaire représentant la règle
        """
        # Exclure les champs qui ne peuvent pas être sérialisés ou qui sont générés automatiquement
        excluded_fields = ['id', 'creation_date', 'last_modified', 'trigger_count']
        
        rule_dict = {}
        for key, value in rule.__dict__.items():
            if key not in excluded_fields and not key.startswith('_'):
                # Convertir les énumérations en chaînes
                if hasattr(value, 'value'):
                    rule_dict[key] = value.value
                else:
                    rule_dict[key] = value
        
        return rule_dict
    
    def export_rules_to_file(self, rules_data, file_path, file_format, pretty=False):
        """
        Exporte les règles vers un fichier.
        
        Args:
            rules_data: Liste de dictionnaires représentant les règles
            file_path: Chemin vers le fichier de sortie
            file_format: Format du fichier (json ou yaml)
            pretty: Si True, formate le fichier pour une meilleure lisibilité
        """
        # Créer le répertoire de destination s'il n'existe pas
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            if file_format == 'json':
                if pretty:
                    json.dump(rules_data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(rules_data, f, ensure_ascii=False)
            elif file_format == 'yaml':
                yaml.dump(rules_data, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"Format non supporté: {file_format}") 