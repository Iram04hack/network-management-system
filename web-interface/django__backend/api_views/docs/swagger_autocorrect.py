"""
Auto-correcteur de documentation Swagger pour api_views.

Ce script corrige automatiquement tous les problèmes de documentation Swagger
identifiés par le validateur en ajoutant les décorateurs et informations manquantes.
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Tuple


class SwaggerAutoCorrector:
    """Auto-correcteur de documentation Swagger."""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent / "views"
        self.corrections_count = 0
        self.files_modified = []
        
        # Templates de documentation pour chaque type de méthode
        self.method_templates = {
            'list': {
                'summary': "Liste tous les {resource_name}",
                'description': "Récupère la liste complète des {resource_name} avec filtrage, tri et pagination.",
                'parameters': [
                    "openapi.Parameter('page', openapi.IN_QUERY, description='Numéro de page', type=openapi.TYPE_INTEGER, default=1)",
                    "openapi.Parameter('page_size', openapi.IN_QUERY, description='Éléments par page', type=openapi.TYPE_INTEGER, default=20)",
                    "openapi.Parameter('search', openapi.IN_QUERY, description='Recherche textuelle', type=openapi.TYPE_STRING)",
                    "openapi.Parameter('ordering', openapi.IN_QUERY, description='Champ de tri', type=openapi.TYPE_STRING)",
                ],
                'responses': {
                    "200": "Liste récupérée avec succès",
                    "401": "Non authentifié",
                    "500": "Erreur serveur"
                }
            },
            'create': {
                'summary': "Crée un nouveau {resource_name}",
                'description': "Crée un nouveau {resource_name} avec validation des données et configuration automatique.",
                'responses': {
                    "201": "Créé avec succès",
                    "400": "Données invalides",
                    "401": "Non authentifié",
                    "500": "Erreur serveur"
                }
            },
            'retrieve': {
                'summary': "Détails d'un {resource_name}",
                'description': "Récupère les détails complets d'un {resource_name} spécifique.",
                'responses': {
                    "200": "Détails récupérés avec succès",
                    "404": "Non trouvé",
                    "401": "Non authentifié",
                    "500": "Erreur serveur"
                }
            },
            'update': {
                'summary': "Met à jour un {resource_name}",
                'description': "Met à jour complètement un {resource_name} existant.",
                'responses': {
                    "200": "Mis à jour avec succès",
                    "400": "Données invalides",
                    "404": "Non trouvé",
                    "401": "Non authentifié",
                    "500": "Erreur serveur"
                }
            },
            'partial_update': {
                'summary': "Met à jour partiellement un {resource_name}",
                'description': "Met à jour partiellement un {resource_name} existant.",
                'responses': {
                    "200": "Mis à jour avec succès",
                    "400": "Données invalides",
                    "404": "Non trouvé",
                    "401": "Non authentifié",
                    "500": "Erreur serveur"
                }
            },
            'destroy': {
                'summary': "Supprime un {resource_name}",
                'description': "Supprime définitivement un {resource_name} du système.",
                'responses': {
                    "204": "Supprimé avec succès",
                    "404": "Non trouvé",
                    "401": "Non authentifié",
                    "403": "Permission refusée",
                    "500": "Erreur serveur"
                }
            }
        }
        
        # Correspondance ViewSet -> nom de ressource
        self.resource_names = {
            'DashboardViewSet': 'tableau de bord',
            'DashboardWidgetViewSet': 'widget de tableau de bord',
            'DeviceManagementViewSet': 'équipement réseau',
            'GlobalSearchViewSet': 'recherche globale',
            'ResourceSearchViewSet': 'recherche de ressource',
            'SearchHistoryViewSet': 'historique de recherche',
            'TopologyDiscoveryViewSet': 'découverte de topologie',
            'PrometheusViewSet': 'métrique Prometheus',
            'GrafanaViewSet': 'dashboard Grafana',
            'Fail2banViewSet': 'configuration Fail2ban',
            'SuricataViewSet': 'règle Suricata',
        }
    
    def correct_all_files(self):
        """Corrige tous les fichiers ViewSets."""
        print("🔧 === AUTO-CORRECTION SWAGGER API_VIEWS ===\n")
        
        view_files = [
            'dashboard_views.py',
            'device_management_views.py',
            'search_views.py',
            'topology_discovery_views.py',
            'prometheus_views.py',
            'grafana_views.py',
            'security_views.py'
        ]
        
        for file_name in view_files:
            file_path = self.base_path / file_name
            if file_path.exists():
                print(f"📝 Correction de {file_name}...")
                self._correct_file(file_path)
            else:
                print(f"⚠️ Fichier non trouvé: {file_name}")
        
        self._print_summary()
    
    def _correct_file(self, file_path: Path):
        """Corrige un fichier spécifique."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Ajouter les imports nécessaires si manquants
            content = self._ensure_swagger_imports(content)
            
            # Trouver et corriger les ViewSets
            content = self._correct_viewsets_in_content(content, file_path.name)
            
            if content != original_content:
                # Sauvegarder le fichier modifié
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.files_modified.append(str(file_path))
                print(f"  ✅ {file_path.name} corrigé")
            else:
                print(f"  ℹ️ {file_path.name} déjà correct")
                
        except Exception as e:
            print(f"  ❌ Erreur lors de la correction de {file_path.name}: {e}")
    
    def _ensure_swagger_imports(self, content: str) -> str:
        """S'assure que les imports Swagger sont présents."""
        required_imports = [
            "from drf_yasg.utils import swagger_auto_schema",
            "from drf_yasg import openapi"
        ]
        
        for import_line in required_imports:
            if import_line not in content:
                # Ajouter l'import après les autres imports drf_yasg s'ils existent
                if "from drf_yasg" in content:
                    content = re.sub(
                        r'(from drf_yasg[^\n]+\n)',
                        r'\1' + import_line + '\n',
                        content,
                        count=1
                    )
                else:
                    # Ajouter après les imports rest_framework
                    content = re.sub(
                        r'(from rest_framework[^\n]+\n)',
                        r'\1' + import_line + '\n',
                        content,
                        count=1
                    )
        
        return content
    
    def _correct_viewsets_in_content(self, content: str, filename: str) -> str:
        """Corrige les ViewSets dans le contenu du fichier."""
        # Pattern pour trouver les définitions de méthodes dans les ViewSets
        method_pattern = r'(\s+)(def\s+(list|create|retrieve|update|partial_update|destroy|\w+)\s*\([^)]+\):)'
        
        lines = content.split('\n')
        new_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Vérifier si c'est une définition de méthode
            method_match = re.match(method_pattern, line)
            if method_match:
                indent = method_match.group(1)
                method_def = method_match.group(2)
                method_name = method_match.group(3)
                
                # Vérifier si la méthode a déjà un décorateur swagger_auto_schema
                has_swagger = False
                j = i - 1
                while j >= 0 and lines[j].strip():
                    if '@swagger_auto_schema' in lines[j]:
                        has_swagger = True
                        break
                    if lines[j].strip() and not lines[j].strip().startswith('@'):
                        break
                    j -= 1
                
                if not has_swagger:
                    # Ajouter le décorateur swagger_auto_schema
                    swagger_decorator = self._generate_swagger_decorator(
                        method_name, indent, filename
                    )
                    new_lines.extend(swagger_decorator)
                    self.corrections_count += 1
            
            new_lines.append(line)
            i += 1
        
        return '\n'.join(new_lines)
    
    def _generate_swagger_decorator(self, method_name: str, indent: str, filename: str) -> List[str]:
        """Génère un décorateur swagger_auto_schema pour une méthode."""
        decorator_lines = []
        
        # Déterminer le nom de la ressource
        viewset_name = self._extract_viewset_name_from_filename(filename)
        resource_name = self.resource_names.get(viewset_name, "ressource")
        
        # Utiliser le template approprié ou un template générique
        template = self.method_templates.get(method_name, {
            'summary': f"Action {method_name}",
            'description': f"Exécute l'action {method_name} sur {resource_name}.",
            'responses': {
                "200": "Opération réussie",
                "401": "Non authentifié",
                "500": "Erreur serveur"
            }
        })
        
        # Formater avec le nom de la ressource
        summary = template['summary'].format(resource_name=resource_name)
        description = template['description'].format(resource_name=resource_name)
        
        # Construire le décorateur
        decorator_lines.append(f"{indent}@swagger_auto_schema(")
        decorator_lines.append(f"{indent}    operation_summary=\"{summary}\",")
        decorator_lines.append(f"{indent}    operation_description=\"{description}\",")
        
        # Ajouter les paramètres si définis
        if 'parameters' in template:
            decorator_lines.append(f"{indent}    manual_parameters=[")
            for param in template['parameters']:
                decorator_lines.append(f"{indent}        {param},")
            decorator_lines.append(f"{indent}    ],")
        
        # Ajouter les réponses
        decorator_lines.append(f"{indent}    responses={{")
        for code, desc in template['responses'].items():
            decorator_lines.append(f"{indent}        {code}: \"{desc}\",")
        decorator_lines.append(f"{indent}    }},")
        
        # Ajouter le tag
        decorator_lines.append(f"{indent}    tags=['views']")
        decorator_lines.append(f"{indent})")
        
        return decorator_lines
    
    def _extract_viewset_name_from_filename(self, filename: str) -> str:
        """Extrait le nom principal du ViewSet depuis le nom de fichier."""
        viewset_mapping = {
            'dashboard_views.py': 'DashboardViewSet',
            'device_management_views.py': 'DeviceManagementViewSet',
            'search_views.py': 'GlobalSearchViewSet',
            'topology_discovery_views.py': 'TopologyDiscoveryViewSet',
            'prometheus_views.py': 'PrometheusViewSet',
            'grafana_views.py': 'GrafanaViewSet',
            'security_views.py': 'Fail2banViewSet',
        }
        return viewset_mapping.get(filename, 'ViewSet')
    
    def _print_summary(self):
        """Affiche le résumé des corrections."""
        print("\n" + "="*60)
        print("📊 === RÉSUMÉ DES CORRECTIONS ===")
        print("="*60)
        
        print(f"\n✨ **CORRECTIONS APPLIQUÉES**")
        print(f"  • Décorateurs ajoutés: {self.corrections_count}")
        print(f"  • Fichiers modifiés: {len(self.files_modified)}")
        
        if self.files_modified:
            print(f"\n📝 **FICHIERS MODIFIÉS**")
            for file_path in self.files_modified:
                print(f"  • {Path(file_path).name}")
        
        print(f"\n🎯 **PROCHAINES ÉTAPES**")
        print(f"  1. Vérifier que le serveur Django démarre sans erreur")
        print(f"  2. Tester l'interface Swagger (/api/views/docs/)")
        print(f"  3. Exécuter le validateur pour vérifier les améliorations")
        
        print(f"\n✅ Auto-correction terminée!")


def main():
    """Point d'entrée principal."""
    corrector = SwaggerAutoCorrector()
    corrector.correct_all_files()


if __name__ == "__main__":
    main() 