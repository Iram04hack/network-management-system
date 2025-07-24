from django.core.management.base import BaseCommand
import os
import re
from pathlib import Path

class Command(BaseCommand):
    help = 'Détecte et signale les simulations dans le code'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Tente de corriger automatiquement les simulations simples',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé des détections',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🔍 Détection des simulations dans le code...")
        
        # Répertoire du module AI Assistant
        ai_assistant_path = Path(__file__).parent.parent.parent
        
        # Patterns de simulation à détecter
        simulation_patterns = [
            r'def _simulate_.*\(',
            r'\.simulate_.*\(',
            r'# Simulation',
            r'# Placeholder',
            r'# TODO.*implement',
            r'return.*simulation',
            r'placeholder.*response',
            r'fake.*data',
            r'mock.*response',
            r'hardcoded.*response',
            r'non.*implémenté',
            r'non.*implemented',
            r'logger\..*simulation',
            r'logger\..*placeholder'
        ]
        
        # Fichiers à analyser
        python_files = []
        for root, dirs, files in os.walk(ai_assistant_path):
            # Ignorer certains répertoires
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'migrations']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(Path(root) / file)
        
        self.stdout.write(f"📁 Analyse de {len(python_files)} fichiers Python...\n")
        
        total_issues = 0
        files_with_issues = 0
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                file_issues = []
                
                # Chercher les patterns de simulation
                for i, line in enumerate(lines, 1):
                    for pattern in simulation_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            file_issues.append({
                                'line': i,
                                'content': line.strip(),
                                'pattern': pattern,
                                'type': 'simulation'
                            })
                
                # Chercher des mots-clés suspects
                suspicious_keywords = [
                    'fake', 'mock', 'dummy', 'placeholder', 'simulation',
                    'hardcoded', 'simulate', 'not implemented'
                ]
                
                for i, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    for keyword in suspicious_keywords:
                        if keyword in line_lower and 'def ' in line:
                            file_issues.append({
                                'line': i,
                                'content': line.strip(), 
                                'pattern': f'keyword: {keyword}',
                                'type': 'suspicious'
                            })
                
                if file_issues:
                    files_with_issues += 1
                    total_issues += len(file_issues)
                    
                    rel_path = file_path.relative_to(ai_assistant_path)
                    self.stdout.write(f"⚠️  {rel_path} ({len(file_issues)} problème(s))")
                    
                    if options['verbose']:
                        for issue in file_issues[:5]:  # Limiter l'affichage
                            self.stdout.write(f"  L{issue['line']:3d}: {issue['content']}")
                        if len(file_issues) > 5:
                            self.stdout.write(f"  ... et {len(file_issues) - 5} autre(s)")
                    
                    self.stdout.write("")
                    
            except Exception as e:
                self.stderr.write(f"❌ Erreur lors de l'analyse de {file_path}: {e}")
        
        # Résumé
        self.stdout.write("=" * 60)
        self.stdout.write(f"📊 Résultats de l'analyse:")
        self.stdout.write(f"  • Fichiers analysés: {len(python_files)}")
        self.stdout.write(f"  • Fichiers avec problèmes: {files_with_issues}")
        self.stdout.write(f"  • Total des problèmes: {total_issues}")
        
        if total_issues == 0:
            self.stdout.write(self.style.SUCCESS("🎉 Aucune simulation détectée !"))
        else:
            percentage = (files_with_issues / len(python_files)) * 100
            self.stdout.write(self.style.WARNING(f"⚠️  {percentage:.1f}% des fichiers contiennent des simulations"))
        
        # Recommandations spécifiques
        if total_issues > 0:
            self.stdout.write("\n🔧 Actions recommandées par priorité:")
            
            # Analyser les types de problèmes les plus fréquents
            critical_files = [
                'ai_client_impl.py',
                'knowledge_base_impl.py', 
                'command_executor_impl.py'
            ]
            
            for critical_file in critical_files:
                matching_files = [f for f in python_files if f.name == critical_file]
                if matching_files:
                    self.stdout.write(f"  🚨 PRIORITÉ 1: Corriger {critical_file}")
            
            self.stdout.write("  📋 PRIORITÉ 2: Éliminer toutes les méthodes _simulate_*")
            self.stdout.write("  🔄 PRIORITÉ 3: Remplacer les placeholders par de vraies implémentations")
            self.stdout.write("  ✅ PRIORITÉ 4: Ajouter des tests de non-simulation")
        
        # Option de correction automatique
        if options['fix'] and total_issues > 0:
            self.stdout.write("\n🔧 Tentative de correction automatique...")
            
            fixes_applied = 0
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Corrections simples
                    # 1. Commenter les méthodes de simulation
                    content = re.sub(
                        r'(\s*)def _simulate_.*?\n(.*?)return.*?\n',
                        r'\1# def _simulate_... # DISABLED - Replace with real implementation\n\1# \2# return ... # DISABLED\n',
                        content,
                        flags=re.DOTALL
                    )
                    
                    # 2. Ajouter des avertissements
                    if '_simulate_' in content:
                        content = f"# WARNING: This file contains simulations that must be replaced with real implementations\n{content}"
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixes_applied += 1
                        rel_path = file_path.relative_to(ai_assistant_path)
                        self.stdout.write(f"  ✅ Corrections appliquées à {rel_path}")
                        
                except Exception as e:
                    self.stderr.write(f"❌ Erreur lors de la correction de {file_path}: {e}")
            
            if fixes_applied > 0:
                self.stdout.write(f"\n🎉 {fixes_applied} fichier(s) corrigé(s) automatiquement")
                self.stdout.write("⚠️  Vérifiez les modifications et testez le code")
            else:
                self.stdout.write("\n⚠️  Aucune correction automatique possible")
        
        elif total_issues > 0:
            self.stdout.write("\n💡 Utilisez --fix pour tenter des corrections automatiques")
        
        return total_issues