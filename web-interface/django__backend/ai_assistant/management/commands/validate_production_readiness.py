from django.core.management.base import BaseCommand
from django.conf import settings
import os
import re
import json
from pathlib import Path
from ai_assistant.models import AIModel, KnowledgeBase, Command

class Command(BaseCommand):
    help = 'Valide que le module est prêt pour la production (sans simulations)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-warnings',
            action='store_true',
            help='Tente de corriger automatiquement les avertissements',
        )
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Mode strict - échoue sur tout problème',
        )
        parser.add_argument(
            '--report-file',
            type=str,
            help='Fichier de sortie pour le rapport détaillé',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🔍 VALIDATION DE LA PRÉPARATION PRODUCTION")
        self.stdout.write("=" * 60)
        
        # Variables de suivi
        self.errors = []
        self.warnings = []
        self.info = []
        self.fixed = []
        
        # Tests de validation
        self._check_database_configuration()
        self._check_ai_models_configuration()
        self._check_code_simulations()
        self._check_security_settings()
        self._check_performance_settings()
        self._check_monitoring_setup()
        self._check_dependencies()
        self._check_tests_coverage()
        
        # Génération du rapport
        self._generate_report(options.get('report_file'))
        
        # Affichage des résultats
        self._display_results(options.get('strict', False))
        
        return len(self.errors)
    
    def _check_database_configuration(self):
        """Vérifie la configuration de la base de données."""
        self.stdout.write("\n📊 Vérification Base de Données...")
        
        try:
            # Vérifier la présence des modèles essentiels
            models_count = {
                'Conversations': AIModel.objects.filter(is_active=True).count(),
                'Modèles IA': AIModel.objects.count(),
                'Base de Connaissances': KnowledgeBase.objects.count(),
                'Commandes': Command.objects.count(),
            }
            
            for model_name, count in models_count.items():
                if count == 0:
                    self.warnings.append(f"Aucune donnée trouvée pour {model_name}")
                else:
                    self.info.append(f"{model_name}: {count} entrée(s)")
            
            # Vérifier les migrations
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM django_migrations WHERE app = 'ai_assistant'"
                )
                migration_count = cursor.fetchone()[0]
                
            if migration_count == 0:
                self.errors.append("Aucune migration appliquée pour ai_assistant")
            else:
                self.info.append(f"Migrations appliquées: {migration_count}")
                
        except Exception as e:
            self.errors.append(f"Erreur de vérification DB: {e}")
    
    def _check_ai_models_configuration(self):
        """Vérifie la configuration des modèles IA."""
        self.stdout.write("\n🤖 Vérification Modèles IA...")
        
        try:
            active_models = AIModel.objects.filter(is_active=True)
            
            if not active_models.exists():
                self.errors.append("Aucun modèle IA actif configuré")
                return
            
            for model in active_models:
                # Vérifier la présence des clés API
                if model.provider in ['openai', 'anthropic'] and not model.api_key:
                    self.warnings.append(f"Clé API manquante pour {model.name}")
                elif model.api_key:
                    self.info.append(f"Modèle {model.name} configuré avec clé API")
                
                # Vérifier les capacités
                if not model.capabilities:
                    self.warnings.append(f"Capacités non définies pour {model.name}")
                
                # Vérifier les paramètres
                if not model.max_tokens or model.max_tokens <= 0:
                    self.warnings.append(f"max_tokens invalide pour {model.name}")
                
                if not (0.0 <= model.temperature <= 2.0):
                    self.warnings.append(f"temperature invalide pour {model.name}")
                    
        except Exception as e:
            self.errors.append(f"Erreur de vérification modèles IA: {e}")
    
    def _check_code_simulations(self):
        """Détecte les simulations dans le code."""
        self.stdout.write("\n🔍 Détection des Simulations...")
        
        # Patterns de simulation à détecter
        simulation_patterns = [
            (r'def _simulate_', 'Méthode de simulation'),
            (r'\.simulate_', 'Appel de simulation'),
            (r'# Simulation', 'Commentaire de simulation'),
            (r'# Placeholder', 'Commentaire placeholder'),
            (r'placeholder.*response', 'Réponse placeholder'),
            (r'fake.*data', 'Données factices'),
            (r'mock.*response', 'Réponse mockée'),
            (r'hardcoded.*response', 'Réponse hardcodée'),
            (r'return.*\{[^}]*"content":\s*"[^"]*test[^"]*"', 'Contenu de test hardcodé'),
            (r'return.*\{[^}]*"content":\s*"[^"]*placeholder[^"]*"', 'Contenu placeholder hardcodé'),
        ]
        
        ai_assistant_path = Path(__file__).parent.parent.parent
        simulation_count = 0
        
        for root, dirs, files in os.walk(ai_assistant_path):
            # Ignorer certains répertoires
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'migrations']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        for pattern, description in simulation_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                rel_path = file_path.relative_to(ai_assistant_path)
                                self.warnings.append(
                                    f"Simulation détectée dans {rel_path}: {description} ({len(matches)} occurrence(s))"
                                )
                                simulation_count += len(matches)
                                
                    except Exception as e:
                        self.warnings.append(f"Erreur lecture {file_path}: {e}")
        
        if simulation_count == 0:
            self.info.append("✅ Aucune simulation détectée dans le code")
        else:
            self.warnings.append(f"⚠️ {simulation_count} simulation(s) détectée(s) au total")
    
    def _check_security_settings(self):
        """Vérifie les paramètres de sécurité."""
        self.stdout.write("\n🔐 Vérification Sécurité...")
        
        # Vérifier DEBUG mode
        if getattr(settings, 'DEBUG', True):
            self.errors.append("DEBUG=True en production n'est pas sécurisé")
        else:
            self.info.append("DEBUG=False ✅")
        
        # Vérifier ALLOWED_HOSTS
        allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', [])
        if not allowed_hosts or allowed_hosts == ['*']:
            self.warnings.append("ALLOWED_HOSTS doit être configuré de manière restrictive")
        else:
            self.info.append(f"ALLOWED_HOSTS configuré: {len(allowed_hosts)} host(s)")
        
        # Vérifier SECRET_KEY
        secret_key = getattr(settings, 'SECRET_KEY', '')
        if not secret_key:
            self.errors.append("SECRET_KEY manquante")
        elif len(secret_key) < 50:
            self.warnings.append("SECRET_KEY trop courte")
        else:
            self.info.append("SECRET_KEY configurée ✅")
        
        # Vérifier les paramètres de session
        session_cookie_secure = getattr(settings, 'SESSION_COOKIE_SECURE', False)
        if not session_cookie_secure:
            self.warnings.append("SESSION_COOKIE_SECURE devrait être True en production")
        
        csrf_cookie_secure = getattr(settings, 'CSRF_COOKIE_SECURE', False)
        if not csrf_cookie_secure:
            self.warnings.append("CSRF_COOKIE_SECURE devrait être True en production")
    
    def _check_performance_settings(self):
        """Vérifie les paramètres de performance."""
        self.stdout.write("\n⚡ Vérification Performance...")
        
        # Vérifier la configuration de cache
        caches = getattr(settings, 'CACHES', {})
        default_cache = caches.get('default', {})
        
        if default_cache.get('BACKEND') == 'django.core.cache.backends.locmem.LocMemCache':
            self.warnings.append("Cache local non recommandé en production")
        elif 'redis' in default_cache.get('BACKEND', '').lower():
            self.info.append("Cache Redis configuré ✅")
        
        # Vérifier la configuration de la base de données
        databases = getattr(settings, 'DATABASES', {})
        default_db = databases.get('default', {})
        
        if 'sqlite' in default_db.get('ENGINE', '').lower():
            self.warnings.append("SQLite non recommandé pour la production")
        elif 'postgresql' in default_db.get('ENGINE', '').lower():
            self.info.append("PostgreSQL configuré ✅")
        
        # Vérifier la configuration Celery
        if hasattr(settings, 'CELERY_BROKER_URL'):
            self.info.append("Celery broker configuré ✅")
        else:
            self.warnings.append("Celery broker non configuré")
    
    def _check_monitoring_setup(self):
        """Vérifie la configuration du monitoring."""
        self.stdout.write("\n📊 Vérification Monitoring...")
        
        # Vérifier la configuration de logging
        logging_config = getattr(settings, 'LOGGING', {})
        if not logging_config:
            self.warnings.append("Configuration de logging manquante")
        else:
            loggers = logging_config.get('loggers', {})
            if 'ai_assistant' in loggers:
                self.info.append("Logger ai_assistant configuré ✅")
            else:
                self.warnings.append("Logger ai_assistant non configuré")
        
        # Vérifier la configuration de Sentry (exemple)
        if hasattr(settings, 'SENTRY_DSN'):
            self.info.append("Sentry configuré ✅")
        else:
            self.warnings.append("Sentry non configuré pour le monitoring d'erreurs")
    
    def _check_dependencies(self):
        """Vérifie les dépendances requises."""
        self.stdout.write("\n📦 Vérification Dépendances...")
        
        required_packages = {
            'django': 'Framework web',
            'djangorestframework': 'API REST',
            'drf-yasg': 'Documentation Swagger',
            'celery': 'Tâches asynchrones',
            'channels': 'WebSocket support',
        }
        
        optional_packages = {
            'openai': 'Support OpenAI',
            'anthropic': 'Support Anthropic',
            'elasticsearch': 'Recherche avancée',
            'redis': 'Cache et broker',
            'psycopg2': 'PostgreSQL',
        }
        
        for package, description in required_packages.items():
            try:
                __import__(package)
                self.info.append(f"{package} ✅ ({description})")
            except ImportError:
                self.errors.append(f"{package} manquant - {description}")
        
        for package, description in optional_packages.items():
            try:
                __import__(package)
                self.info.append(f"{package} ✅ ({description})")
            except ImportError:
                self.warnings.append(f"{package} optionnel manquant - {description}")
    
    def _check_tests_coverage(self):
        """Vérifie la couverture des tests."""
        self.stdout.write("\n🧪 Vérification Tests...")
        
        tests_dir = Path(__file__).parent.parent / 'tests'
        
        if not tests_dir.exists():
            self.errors.append("Répertoire de tests manquant")
            return
        
        test_files = list(tests_dir.glob('test_*.py'))
        if len(test_files) < 5:
            self.warnings.append(f"Couverture de tests faible: {len(test_files)} fichiers")
        else:
            self.info.append(f"Tests présents: {len(test_files)} fichiers")
        
        # Vérifier les tests anti-simulation
        anti_sim_tests = list(tests_dir.glob('*anti_simulation*'))
        if not anti_sim_tests:
            self.warnings.append("Tests anti-simulation manquants")
        else:
            self.info.append("Tests anti-simulation présents ✅")
    
    def _generate_report(self, report_file):
        """Génère un rapport détaillé."""
        if not report_file:
            return
        
        report = {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'summary': {
                'errors': len(self.errors),
                'warnings': len(self.warnings),
                'info': len(self.info),
                'fixed': len(self.fixed),
                'production_ready': len(self.errors) == 0
            },
            'details': {
                'errors': self.errors,
                'warnings': self.warnings,
                'info': self.info,
                'fixed': self.fixed
            }
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.info.append(f"Rapport sauvegardé: {report_file}")
        except Exception as e:
            self.warnings.append(f"Erreur sauvegarde rapport: {e}")
    
    def _display_results(self, strict_mode):
        """Affiche les résultats finaux."""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📋 RÉSULTATS DE VALIDATION")
        
        # Statistiques
        self.stdout.write(f"\n📊 Statistiques:")
        self.stdout.write(f"  • Erreurs: {len(self.errors)}")
        self.stdout.write(f"  • Avertissements: {len(self.warnings)}")
        self.stdout.write(f"  • Informations: {len(self.info)}")
        self.stdout.write(f"  • Corrections: {len(self.fixed)}")
        
        # Erreurs
        if self.errors:
            self.stdout.write(f"\n❌ ERREURS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                self.stdout.write(f"  {i}. {error}")
        
        # Avertissements
        if self.warnings:
            self.stdout.write(f"\n⚠️  AVERTISSEMENTS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                self.stdout.write(f"  {i}. {warning}")
        
        # Verdict final
        self.stdout.write("\n" + "=" * 60)
        if len(self.errors) == 0:
            if len(self.warnings) == 0:
                self.stdout.write(self.style.SUCCESS("🎉 MODULE PRÊT POUR LA PRODUCTION"))
            else:
                self.stdout.write(self.style.WARNING("⚠️  MODULE PRÊT AVEC RÉSERVES"))
                self.stdout.write("   Corrigez les avertissements pour une production optimale")
        else:
            self.stdout.write(self.style.ERROR("❌ MODULE NON PRÊT POUR LA PRODUCTION"))
            self.stdout.write("   Corrigez toutes les erreurs avant le déploiement")
        
        # Recommandations
        self.stdout.write("\n💡 RECOMMANDATIONS:")
        if self.errors:
            self.stdout.write("  1. Corrigez toutes les erreurs listées ci-dessus")
            self.stdout.write("  2. Relancez la validation avec: python manage.py validate_production_readiness")
        
        if self.warnings:
            self.stdout.write("  3. Examinez et corrigez les avertissements")
            self.stdout.write("  4. Utilisez --fix-warnings pour les corrections automatiques")
        
        self.stdout.write("  5. Testez en environnement de staging avant production")
        self.stdout.write("  6. Configurez le monitoring en production")
        
        # Mode strict
        if strict_mode and (self.errors or self.warnings):
            self.stdout.write(f"\n⚠️  Mode strict activé - Échec avec {len(self.errors + self.warnings)} problème(s)")
            exit(1)