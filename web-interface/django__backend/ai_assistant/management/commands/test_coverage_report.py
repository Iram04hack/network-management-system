from django.core.management.base import BaseCommand
import os
import ast
import json
from pathlib import Path
from collections import defaultdict

class Command(BaseCommand):
    help = 'Génère un rapport détaillé de couverture des tests'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='coverage_report.json',
            help='Fichier de sortie pour le rapport',
        )
        parser.add_argument(
            '--missing-only',
            action='store_true',
            help='Affiche seulement les éléments non testés',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🧪 ANALYSE DE COUVERTURE DES TESTS")
        self.stdout.write("=" * 60)
        
        self.verbose = options.get('verbose', False)
        self.missing_only = options.get('missing_only', False)
        
        # Analyse du code source
        source_analysis = self._analyze_source_code()
        
        # Analyse des tests
        test_analysis = self._analyze_test_code()
        
        # Calcul de la couverture
        coverage_report = self._calculate_coverage(source_analysis, test_analysis)
        
        # Affichage du rapport
        self._display_report(coverage_report)
        
        # Sauvegarde
        self._save_report(coverage_report, options.get('output'))
        
        return 0
    
    def _analyze_source_code(self):
        """Analyse le code source pour identifier les éléments testables."""
        self.stdout.write("📊 Analyse du code source...")
        
        source_dir = Path(__file__).parent.parent.parent
        analysis = {
            'classes': {},
            'functions': {},
            'methods': {},
            'views': {},
            'models': {},
            'api_endpoints': {}
        }
        
        # Parcours des fichiers Python
        for python_file in source_dir.rglob('*.py'):
            # Ignorer certains fichiers
            if any(part in str(python_file) for part in ['__pycache__', 'migrations', 'tests']):
                continue
            
            try:
                with open(python_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                self._analyze_ast(tree, python_file, analysis)
                
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f"⚠️ Erreur analyse {python_file}: {e}")
        
        return analysis
    
    def _analyze_ast(self, tree, file_path, analysis):
        """Analyse l'AST pour extraire les éléments testables."""
        relative_path = str(file_path).split('ai_assistant/')[-1]
        
        for node in ast.walk(tree):
            # Classes
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'file': relative_path,
                    'line': node.lineno,
                    'methods': [],
                    'is_view': 'View' in node.name or 'ViewSet' in node.name,
                    'is_model': any(base.id == 'Model' for base in getattr(node, 'bases', []) if hasattr(base, 'id')),
                    'is_serializer': 'Serializer' in node.name,
                    'is_service': 'Service' in node.name,
                    'is_test': 'Test' in node.name
                }
                
                # Analyser les méthodes de la classe
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            'name': item.name,
                            'class': node.name,
                            'file': relative_path,
                            'line': item.lineno,
                            'is_public': not item.name.startswith('_'),
                            'is_property': any(isinstance(d, ast.Name) and d.id == 'property' for d in getattr(item, 'decorator_list', [])),
                            'args_count': len(item.args.args) - 1,  # -1 pour self
                        }
                        class_info['methods'].append(method_info)
                        
                        # Catégoriser les méthodes
                        method_key = f"{node.name}.{item.name}"
                        analysis['methods'][method_key] = method_info
                
                # Catégoriser les classes
                if class_info['is_view']:
                    analysis['views'][node.name] = class_info
                elif class_info['is_model']:
                    analysis['models'][node.name] = class_info
                else:
                    analysis['classes'][node.name] = class_info
            
            # Fonctions standalone
            elif isinstance(node, ast.FunctionDef) and not hasattr(node, 'parent_class'):
                function_info = {
                    'name': node.name,
                    'file': relative_path,
                    'line': node.lineno,
                    'is_public': not node.name.startswith('_'),
                    'args_count': len(node.args.args),
                    'is_async': isinstance(node, ast.AsyncFunctionDef)
                }
                analysis['functions'][node.name] = function_info
    
    def _analyze_test_code(self):
        """Analyse les tests pour identifier ce qui est testé."""
        self.stdout.write("🔍 Analyse des tests...")
        
        tests_dir = Path(__file__).parent.parent / 'tests'
        analysis = {
            'test_classes': {},
            'test_methods': {},
            'covered_classes': set(),
            'covered_methods': set(),
            'covered_functions': set(),
            'test_types': defaultdict(int)
        }
        
        if not tests_dir.exists():
            self.stdout.write("⚠️ Répertoire de tests non trouvé")
            return analysis
        
        # Parcours des fichiers de test
        for test_file in tests_dir.rglob('test_*.py'):
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                self._analyze_test_ast(tree, test_file, analysis)
                
            except Exception as e:
                if self.verbose:
                    self.stdout.write(f"⚠️ Erreur analyse test {test_file}: {e}")
        
        return analysis
    
    def _analyze_test_ast(self, tree, file_path, analysis):
        """Analyse l'AST des tests."""
        relative_path = str(file_path).split('tests/')[-1]
        
        # Identifier le type de test basé sur le nom du fichier
        filename = Path(file_path).stem
        if 'integration' in filename:
            test_type = 'integration'
        elif 'performance' in filename or 'load' in filename:
            test_type = 'performance'
        elif 'e2e' in filename or 'end_to_end' in filename:
            test_type = 'e2e'
        elif 'security' in filename:
            test_type = 'security'
        elif 'anti_simulation' in filename:
            test_type = 'anti_simulation'
        else:
            test_type = 'unit'
        
        analysis['test_types'][test_type] += 1
        
        for node in ast.walk(tree):
            # Classes de test
            if isinstance(node, ast.ClassDef) and (node.name.startswith('Test') or 'Test' in node.name):
                test_class_info = {
                    'name': node.name,
                    'file': relative_path,
                    'type': test_type,
                    'methods': []
                }
                
                # Analyser les méthodes de test
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                        test_method_info = {
                            'name': item.name,
                            'class': node.name,
                            'file': relative_path,
                            'type': test_type,
                            'line': item.lineno
                        }
                        test_class_info['methods'].append(test_method_info)
                        analysis['test_methods'][f"{node.name}.{item.name}"] = test_method_info
                        
                        # Déduire ce qui est testé basé sur le nom
                        self._deduce_coverage_from_test_name(item.name, analysis)
                
                analysis['test_classes'][node.name] = test_class_info
            
            # Fonctions de test standalone
            elif isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                test_function_info = {
                    'name': node.name,
                    'file': relative_path,
                    'type': test_type,
                    'line': node.lineno
                }
                analysis['test_methods'][node.name] = test_function_info
                self._deduce_coverage_from_test_name(node.name, analysis)
    
    def _deduce_coverage_from_test_name(self, test_name, analysis):
        """Déduit ce qui est testé basé sur le nom du test."""
        # Patterns courants de nommage de tests
        patterns = {
            'test_.*_model': 'models',
            'test_.*_view': 'views', 
            'test_.*_service': 'services',
            'test_.*_serializer': 'serializers',
            'test_.*_command': 'commands',
            'test_.*_api': 'api',
            'test_.*_endpoint': 'api'
        }
        
        # Extraire les noms de classes/méthodes testées
        import re
        for pattern, category in patterns.items():
            if re.match(pattern, test_name):
                # Extraire le nom probable de l'élément testé
                parts = test_name.replace('test_', '').split('_')
                if len(parts) >= 2:
                    potential_class = ''.join(part.capitalize() for part in parts[:-1])
                    analysis['covered_classes'].add(potential_class)
    
    def _calculate_coverage(self, source_analysis, test_analysis):
        """Calcule les statistiques de couverture."""
        self.stdout.write("📈 Calcul de la couverture...")
        
        coverage = {
            'summary': {},
            'by_category': {},
            'missing_tests': {},
            'recommendations': []
        }
        
        # Calcul par catégorie
        categories = ['classes', 'methods', 'functions', 'views', 'models']
        
        for category in categories:
            source_items = source_analysis.get(category, {})
            total_items = len(source_items)
            
            if category == 'methods':
                # Pour les méthodes, on compte celles qui sont publiques
                public_methods = {k: v for k, v in source_items.items() if v.get('is_public', True)}
                tested_items = len([k for k in public_methods.keys() if self._is_method_tested(k, test_analysis)])
                total_items = len(public_methods)
            elif category == 'classes':
                tested_items = len([k for k in source_items.keys() if k in test_analysis['covered_classes']])
            else:
                tested_items = len([k for k in source_items.keys() if self._is_item_tested(k, category, test_analysis)])
            
            coverage_percentage = (tested_items / total_items * 100) if total_items > 0 else 100
            
            coverage['by_category'][category] = {
                'total': total_items,
                'tested': tested_items,
                'coverage': round(coverage_percentage, 1),
                'missing': [k for k in source_items.keys() if not self._is_item_tested(k, category, test_analysis)]
            }
        
        # Calcul global
        total_testable = sum(cat['total'] for cat in coverage['by_category'].values())
        total_tested = sum(cat['tested'] for cat in coverage['by_category'].values())
        global_coverage = (total_tested / total_testable * 100) if total_testable > 0 else 100
        
        coverage['summary'] = {
            'total_testable_items': total_testable,
            'total_tested_items': total_tested,
            'global_coverage': round(global_coverage, 1),
            'test_files_count': len(test_analysis['test_classes']) + len([m for m in test_analysis['test_methods'].values() if '.' not in m['name']]),
            'test_types': dict(test_analysis['test_types'])
        }
        
        # Recommandations
        self._generate_recommendations(coverage, source_analysis, test_analysis)
        
        return coverage
    
    def _is_item_tested(self, item_name, category, test_analysis):
        """Vérifie si un élément est testé."""
        # Logique simplifiée - peut être améliorée
        return item_name in test_analysis['covered_classes'] or any(
            item_name.lower() in test_name.lower() 
            for test_name in test_analysis['test_methods'].keys()
        )
    
    def _is_method_tested(self, method_key, test_analysis):
        """Vérifie si une méthode est testée."""
        class_name, method_name = method_key.split('.', 1)
        return any(
            method_name.lower() in test_name.lower() or class_name.lower() in test_name.lower()
            for test_name in test_analysis['test_methods'].keys()
        )
    
    def _generate_recommendations(self, coverage, source_analysis, test_analysis):
        """Génère des recommandations pour améliorer la couverture."""
        recommendations = []
        
        # Recommandations basées sur la couverture
        global_coverage = coverage['summary']['global_coverage']
        
        if global_coverage < 60:
            recommendations.append("🚨 Couverture critique (<60%) - Priorisez l'ajout de tests unitaires")
        elif global_coverage < 80:
            recommendations.append("⚠️ Couverture insuffisante (<80%) - Ajoutez des tests pour les fonctionnalités principales")
        
        # Recommandations par catégorie
        for category, data in coverage['by_category'].items():
            if data['coverage'] < 50:
                recommendations.append(f"📈 {category.capitalize()}: Couverture très faible ({data['coverage']}%) - Ajoutez des tests de base")
            elif len(data['missing']) > 0 and not self.missing_only:
                top_missing = data['missing'][:3]
                recommendations.append(f"🔍 {category.capitalize()}: Testez {', '.join(top_missing)}")
        
        # Recommandations sur les types de tests
        test_types = coverage['summary']['test_types']
        
        if test_types.get('integration', 0) == 0:
            recommendations.append("🔗 Ajoutez des tests d'intégration pour valider les interactions entre composants")
        
        if test_types.get('performance', 0) == 0:
            recommendations.append("⚡ Ajoutez des tests de performance pour valider la scalabilité")
        
        if test_types.get('security', 0) == 0:
            recommendations.append("🔐 Ajoutez des tests de sécurité pour valider la protection")
        
        if test_types.get('anti_simulation', 0) == 0:
            recommendations.append("🎭 Ajoutez des tests anti-simulation pour détecter les faux positifs")
        
        coverage['recommendations'] = recommendations
    
    def _display_report(self, coverage):
        """Affiche le rapport de couverture."""
        summary = coverage['summary']
        
        self.stdout.write(f"\n📊 RÉSUMÉ GLOBAL")
        self.stdout.write(f"  • Éléments testables: {summary['total_testable_items']}")
        self.stdout.write(f"  • Éléments testés: {summary['total_tested_items']}")
        self.stdout.write(f"  • Couverture globale: {summary['global_coverage']}%")
        self.stdout.write(f"  • Fichiers de test: {summary['test_files_count']}")
        
        # Indicateur visuel de couverture
        coverage_level = summary['global_coverage']
        if coverage_level >= 80:
            indicator = "🟢 EXCELLENTE"
        elif coverage_level >= 60:
            indicator = "🟡 CORRECTE"
        else:
            indicator = "🔴 INSUFFISANTE"
        
        self.stdout.write(f"  • Niveau: {indicator}")
        
        # Types de tests
        if summary['test_types']:
            self.stdout.write(f"\n🧪 TYPES DE TESTS")
            for test_type, count in summary['test_types'].items():
                self.stdout.write(f"  • {test_type.capitalize()}: {count} fichier(s)")
        
        # Détail par catégorie
        self.stdout.write(f"\n📋 DÉTAIL PAR CATÉGORIE")
        for category, data in coverage['by_category'].items():
            status = "✅" if data['coverage'] >= 80 else "⚠️" if data['coverage'] >= 60 else "❌"
            self.stdout.write(f"  {status} {category.capitalize()}: {data['coverage']}% ({data['tested']}/{data['total']})")
            
            if data['missing'] and not self.missing_only:
                if self.verbose:
                    self.stdout.write(f"    Non testés: {', '.join(data['missing'][:5])}")
                    if len(data['missing']) > 5:
                        self.stdout.write(f"    ... et {len(data['missing']) - 5} autre(s)")
        
        # Éléments non testés (si demandé)
        if self.missing_only:
            self.stdout.write(f"\n❌ ÉLÉMENTS NON TESTÉS")
            for category, data in coverage['by_category'].items():
                if data['missing']:
                    self.stdout.write(f"\n{category.capitalize()}:")
                    for item in data['missing']:
                        self.stdout.write(f"  • {item}")
        
        # Recommandations
        if coverage['recommendations']:
            self.stdout.write(f"\n💡 RECOMMANDATIONS")
            for i, rec in enumerate(coverage['recommendations'], 1):
                self.stdout.write(f"  {i}. {rec}")
    
    def _save_report(self, coverage, output_file):
        """Sauvegarde le rapport."""
        try:
            report_data = {
                'timestamp': __import__('datetime').datetime.now().isoformat(),
                'coverage': coverage
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            self.stdout.write(f"\n💾 Rapport sauvegardé: {output_file}")
        except Exception as e:
            self.stdout.write(f"\n⚠️ Erreur sauvegarde: {e}")