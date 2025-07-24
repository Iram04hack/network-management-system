"""
Commande de validation pour vérifier si le module AI Assistant est prêt pour la production.

Cette commande exécute une série de tests de validation pour s'assurer que le module
AI Assistant répond à tous les critères de qualité nécessaires pour la production.
"""

import sys
import os
import time
import inspect
import importlib
import re
import django
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import termcolors

from ai_assistant.config import di, settings as ai_settings
from ai_assistant.domain.interfaces import AIClient, CommandExecutor, KnowledgeBase, AIAssistantRepository
from ai_assistant.domain.exceptions import AIClientException, CommandExecutionException, KnowledgeBaseException


class Command(BaseCommand):
    help = "Valide que le module AI Assistant est prêt pour la production"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.success_count = 0
        self.fail_count = 0
        self.warning_count = 0
        self.total_checks = 0

    def success(self, message):
        """Affiche un message de succès"""
        self.stdout.write(termcolors.make_style(fg='green')('✓ ' + message))
        self.success_count += 1
        self.total_checks += 1

    def fail(self, message):
        """Affiche un message d'échec"""
        self.stdout.write(termcolors.make_style(fg='red')('✗ ' + message))
        self.fail_count += 1
        self.total_checks += 1

    def warning(self, message):
        """Affiche un message d'avertissement"""
        self.stdout.write(termcolors.make_style(fg='yellow')('! ' + message))
        self.warning_count += 1
        self.total_checks += 1

    def section(self, title):
        """Affiche un titre de section"""
        self.stdout.write(termcolors.make_style(fg='cyan', opts=('bold',))('\n' + title))
        self.stdout.write(termcolors.make_style(fg='cyan')('-' * len(title)))

    def handle(self, *args, **options):
        """Exécute la commande de validation"""
        start_time = time.time()
        
        self.stdout.write(termcolors.make_style(fg='white', opts=('bold',))
                        ('Validation du module AI Assistant pour la production\n'))
        
        # Effectuer les validations
        self.validate_dependencies()
        self.validate_configuration()
        self.validate_interfaces()
        self.validate_openai_api()
        self.validate_error_handling()
        self.validate_di_setup()
        self.validate_security()
        self.validate_code_quality()
        
        # Afficher le résumé des résultats
        self.section("Résumé des validations")
        duration = time.time() - start_time
        self.stdout.write(f"Durée: {duration:.2f} secondes")
        self.stdout.write(f"Total des vérifications: {self.total_checks}")
        self.stdout.write(termcolors.make_style(fg='green')(f"Réussites: {self.success_count}"))
        self.stdout.write(termcolors.make_style(fg='yellow')(f"Avertissements: {self.warning_count}"))
        self.stdout.write(termcolors.make_style(fg='red')(f"Échecs: {self.fail_count}"))
        
        # Calcul du score final et détermination du statut
        score_percentage = (self.success_count / self.total_checks) * 100
        self.stdout.write(f"\nScore de validation: {score_percentage:.1f}%")
        
        if self.fail_count > 0:
            self.stdout.write(termcolors.make_style(fg='red', opts=('bold',))
                            ("RÉSULTAT: NON PRÊT POUR LA PRODUCTION"))
            return False
        elif self.warning_count > 0:
            self.stdout.write(termcolors.make_style(fg='yellow', opts=('bold',))
                            ("RÉSULTAT: PRÊT AVEC AVERTISSEMENTS"))
            return True
        else:
            self.stdout.write(termcolors.make_style(fg='green', opts=('bold',))
                            ("RÉSULTAT: PRÊT POUR LA PRODUCTION"))
            return True

    def validate_dependencies(self):
        """Valide que toutes les dépendances requises sont disponibles"""
        self.section("Validation des dépendances")
        
        # Vérifier les dépendances Python
        dependencies = [
            ("openai", "1.0.0"),  # Nouvelle API OpenAI
            ("elasticsearch", "8.0.0"),  # Pour la base de connaissances
            ("django", "3.2.0"),  # Pour le framework web
            ("pytest", "6.0.0")   # Pour les tests
        ]
        
        for package, min_version in dependencies:
            try:
                module = importlib.import_module(package)
                if hasattr(module, "__version__"):
                    version = module.__version__
                    if self._version_greater_equal(version, min_version):
                        self.success(f"{package} version {version} (>= {min_version})")
                    else:
                        self.warning(f"{package} version {version} (< {min_version} recommandé)")
                else:
                    self.success(f"{package} installé (version non détectable)")
            except ImportError:
                if package == "elasticsearch" and not ai_settings.REQUIRE_ELASTICSEARCH:
                    self.warning(f"{package} non installé (optionnel)")
                else:
                    self.fail(f"{package} non installé (requis)")
    
    def _version_greater_equal(self, version1, version2):
        """Compare deux versions au format x.y.z"""
        v1_parts = [int(x) for x in version1.split(".")]
        v2_parts = [int(x) for x in version2.split(".")]
        
        # Compléter avec des zéros si nécessaire
        while len(v1_parts) < len(v2_parts):
            v1_parts.append(0)
        while len(v2_parts) < len(v1_parts):
            v2_parts.append(0)
            
        # Comparer partie par partie
        for i in range(len(v1_parts)):
            if v1_parts[i] > v2_parts[i]:
                return True
            elif v1_parts[i] < v2_parts[i]:
                return False
                
        # Égales
        return True

    def validate_configuration(self):
        """Valide la configuration du module"""
        self.section("Validation de la configuration")
        
        # Vérifier les paramètres de configuration critiques
        if ai_settings.ENABLE_AI_CLIENT:
            if ai_settings.DEFAULT_AI_API_KEY:
                self.success("Clé API configurée")
            else:
                self.fail("Clé API non configurée")
        else:
            self.warning("Client AI désactivé")
            
        if ai_settings.REQUIRE_ELASTICSEARCH:
            try:
                kb = di.get_knowledge_base()
                if kb.client and kb.client.ping():
                    self.success("Elasticsearch connecté et opérationnel")
                else:
                    self.fail("Elasticsearch requis mais non opérationnel")
            except Exception as e:
                self.fail(f"Erreur de connexion à Elasticsearch: {str(e)}")
        else:
            self.warning("Elasticsearch marqué comme optionnel")
            
        # Vérifier les paramètres de sécurité
        if ai_settings.ALLOWED_COMMAND_TYPES:
            self.success(f"Types de commandes autorisés configurés: {', '.join(ai_settings.ALLOWED_COMMAND_TYPES)}")
        else:
            self.warning("Aucun type de commande autorisé configuré")
            
        if ai_settings.MAX_RESPONSE_TOKENS <= 2000:
            self.success(f"Limite de tokens configurée ({ai_settings.MAX_RESPONSE_TOKENS})")
        else:
            self.warning(f"Limite de tokens potentiellement élevée ({ai_settings.MAX_RESPONSE_TOKENS})")

    def validate_interfaces(self):
        """Valide que les interfaces sont correctement implémentées"""
        self.section("Validation des interfaces")
        
        # Vérifier l'implémentation de CommandExecutor
        try:
            executor = di.get_command_executor()
            executor_class = executor.__class__
            
            # Vérifier que la méthode execute accepte command_type
            sig = inspect.signature(executor_class.execute)
            if 'command_type' in sig.parameters:
                self.success("Signature de CommandExecutor.execute correcte")
            else:
                self.fail("Signature de CommandExecutor.execute incorrecte (manque command_type)")
                
            # Vérifier que la méthode validate accepte command_type
            sig = inspect.signature(executor_class.validate)
            if 'command_type' in sig.parameters:
                self.success("Signature de CommandExecutor.validate correcte")
            else:
                self.fail("Signature de CommandExecutor.validate incorrecte (manque command_type)")
        except Exception as e:
            self.fail(f"Erreur lors de la validation de CommandExecutor: {str(e)}")
            
        # Vérifier l'implémentation de KnowledgeBase
        try:
            kb = di.get_knowledge_base()
            kb_class = kb.__class__
            
            # Vérifier que la méthode search accepte threshold
            sig = inspect.signature(kb_class.search)
            if 'threshold' in sig.parameters:
                self.success("Signature de KnowledgeBase.search correcte")
            else:
                self.fail("Signature de KnowledgeBase.search incorrecte (manque threshold)")
                
            # Vérifier la valeur par défaut du threshold
            if sig.parameters['threshold'].default == 0.7:
                self.success("Valeur par défaut du threshold correcte (0.7)")
            else:
                self.warning(f"Valeur par défaut du threshold non standard ({sig.parameters['threshold'].default})")
        except Exception as e:
            self.fail(f"Erreur lors de la validation de KnowledgeBase: {str(e)}")
            
        # Vérifier l'implémentation de AIAssistantRepository
        try:
            repo = di.get_repository()
            
            # Vérifier que les méthodes requises sont présentes
            required_methods = [
                'create_conversation',
                'get_conversation',
                'get_user_conversations',
                'update_conversation',
                'delete_conversation',
                'add_message',
                'get_conversation_messages',
                'delete_message'
            ]
            
            missing_methods = []
            for method in required_methods:
                if not hasattr(repo, method):
                    missing_methods.append(method)
            
            if not missing_methods:
                self.success("Toutes les méthodes requises sont implémentées dans le repository")
            else:
                self.fail(f"Méthodes manquantes dans le repository: {', '.join(missing_methods)}")
                
            # Vérifier que l'ancienne méthode save_conversation n'existe plus
            if hasattr(repo, 'save_conversation'):
                self.fail("Méthode obsolète save_conversation toujours présente dans le repository")
            else:
                self.success("Méthode obsolète save_conversation correctement remplacée")
        except Exception as e:
            self.fail(f"Erreur lors de la validation du repository: {str(e)}")

    def validate_openai_api(self):
        """Valide l'utilisation de la nouvelle API OpenAI"""
        self.section("Validation de l'API OpenAI")
        
        try:
            # Obtenir le code source du client AI
            ai_client = di.get_ai_client()
            ai_client_source = inspect.getsource(ai_client.__class__)
            
            # Vérifier l'importation moderne
            if "from openai import OpenAI" in ai_client_source:
                self.success("Importation moderne 'from openai import OpenAI' utilisée")
            else:
                self.fail("Importation moderne 'from openai import OpenAI' manquante")
                
            # Vérifier l'initialisation du client
            if re.search(r"client\s*=\s*OpenAI\(", ai_client_source):
                self.success("Initialisation moderne du client OpenAI utilisée")
            else:
                self.fail("Initialisation moderne du client OpenAI manquante")
                
            # Vérifier l'appel à l'API moderne
            if re.search(r"client\.chat\.completions\.create\(", ai_client_source):
                self.success("Appel moderne 'client.chat.completions.create' utilisé")
            else:
                self.fail("Appel moderne 'client.chat.completions.create' manquant")
                
            # Vérifier que l'ancien appel n'est plus utilisé
            if re.search(r"openai\.ChatCompletion\.create\(", ai_client_source):
                self.fail("Ancien appel 'openai.ChatCompletion.create' toujours utilisé")
            else:
                self.success("Ancien appel 'openai.ChatCompletion.create' correctement remplacé")
        except Exception as e:
            self.fail(f"Erreur lors de la validation de l'API OpenAI: {str(e)}")

    def validate_error_handling(self):
        """Valide la gestion des erreurs"""
        self.section("Validation de la gestion des erreurs")
        
        try:
            # Vérifier la gestion des erreurs dans le client AI
            ai_client = di.get_ai_client()
            ai_client_source = inspect.getsource(ai_client.__class__)
            
            if "raise AIClientException" in ai_client_source:
                self.success("Gestion d'erreurs correcte dans AIClient (utilise AIClientException)")
            else:
                self.warning("Gestion d'erreurs potentiellement incorrecte dans AIClient (pas d'utilisation de AIClientException)")
                
            # Vérifier la gestion des erreurs pour Elasticsearch
            kb = di.get_knowledge_base()
            kb_source = inspect.getsource(kb.__class__)
            
            if ai_settings.REQUIRE_ELASTICSEARCH:
                if "raise KnowledgeBaseException" in kb_source:
                    self.success("Gestion d'erreurs correcte pour Elasticsearch requis (utilise KnowledgeBaseException)")
                else:
                    self.fail("Gestion d'erreurs incorrecte pour Elasticsearch requis (n'utilise pas KnowledgeBaseException)")
            else:
                if "logger.warning" in kb_source:
                    self.success("Gestion d'erreurs correcte pour Elasticsearch optionnel (utilise logger.warning)")
                else:
                    self.warning("Gestion d'erreurs potentiellement incorrecte pour Elasticsearch optionnel (pas d'utilisation de logger.warning)")
                    
            # Vérifier l'absence de silencieux except: pass
            sources = [
                ai_client_source,
                kb_source,
                inspect.getsource(di.get_command_executor().__class__)
            ]
            
            bad_patterns = [
                r"except.*:\s*pass",
                r"except.*:\s*return",
                r"except\s+Exception.*:\s*pass",
            ]
            
            for source in sources:
                for pattern in bad_patterns:
                    if re.search(pattern, source):
                        self.fail(f"Mauvaise gestion d'erreurs trouvée: {pattern}")
                        break
                else:
                    self.success("Pas de silencieux except: pass détecté")
        except Exception as e:
            self.fail(f"Erreur lors de la validation de la gestion des erreurs: {str(e)}")

    def validate_di_setup(self):
        """Valide la configuration de l'injection de dépendances"""
        self.section("Validation de l'injection de dépendances")
        
        try:
            # Vérifier que le module di expose les fonctions attendues
            expected_functions = [
                'validate_configuration',
                'get_ai_client',
                'get_knowledge_base',
                'get_command_executor',
                'get_repository',
                'get_ai_assistant_service'
            ]
            
            for func_name in expected_functions:
                if hasattr(di, func_name):
                    self.success(f"Fonction {func_name} correctement exposée")
                else:
                    self.fail(f"Fonction {func_name} manquante dans le module di")
                    
            # Vérifier que validate_configuration fonctionne
            try:
                di.validate_configuration()
                self.success("La fonction validate_configuration s'exécute sans erreur")
            except Exception as e:
                self.fail(f"Erreur lors de l'exécution de validate_configuration: {str(e)}")
                
            # Vérifier que get_ai_assistant_service renvoie la bonne implémentation
            di._ai_assistant_service_instance = None  # Réinitialiser l'instance pour forcer la recréation
            service = di.get_ai_assistant_service()
            
            # Vérifier que le service est importé depuis ai_assistant_service.py et non services.py
            service_module = service.__class__.__module__
            if service_module == 'ai_assistant.application.ai_assistant_service':
                self.success("Le service est correctement importé depuis ai_assistant_service")
            else:
                self.fail(f"Le service est importé depuis le mauvais module: {service_module}")
        except Exception as e:
            self.fail(f"Erreur lors de la validation de l'injection de dépendances: {str(e)}")

    def validate_security(self):
        """Valide les aspects de sécurité"""
        self.section("Validation de la sécurité")
        
        # Vérifier la validation des commandes
        try:
            executor = di.get_command_executor()
            
            # Tester la validation avec un type de commande non autorisé
            invalid_type = "unauthorized_command_type"
            if invalid_type not in ai_settings.ALLOWED_COMMAND_TYPES:
                is_valid = executor.validate("echo test", invalid_type)
                if not is_valid:
                    self.success("La validation des types de commandes non autorisés fonctionne correctement")
                else:
                    self.fail("La validation accepte des types de commandes non autorisés")
            else:
                self.warning("Impossible de tester la validation des commandes non autorisées")
                
            # Vérifier la présence de commandes dangereuses
            dangerous_commands = [
                "rm -rf",
                "> /dev/",
                "shutdown",
                "reboot",
                ";",
                "&&",
                "||",
                "|"
            ]
            
            source = inspect.getsource(executor.__class__)
            for cmd in dangerous_commands:
                if cmd in source and "forbidden" in source.lower() and cmd in source.lower():
                    self.success(f"La commande dangereuse '{cmd}' est correctement détectée")
                else:
                    self.warning(f"La détection de la commande dangereuse '{cmd}' n'est pas évidente")
        except Exception as e:
            self.fail(f"Erreur lors de la validation de la sécurité: {str(e)}")

    def validate_code_quality(self):
        """Valide la qualité du code"""
        self.section("Validation de la qualité du code")
        
        try:
            # Vérifier l'absence de méthodes de simulation
            simulation_patterns = [
                r'def\s+_?simulate',
                r'def\s+_?mock',
                r'def\s+_?fake',
                r'mock_response',
                r'fake_data',
                r'simulated_',
                r'# SIMULATION'
            ]
            
            # Répertoires à analyser
            directories = [
                os.path.join(settings.BASE_DIR, 'ai_assistant', 'domain'),
                os.path.join(settings.BASE_DIR, 'ai_assistant', 'application'),
                os.path.join(settings.BASE_DIR, 'ai_assistant', 'infrastructure'),
                os.path.join(settings.BASE_DIR, 'ai_assistant', 'config')
            ]
            
            # Exclure certains répertoires
            excluded_dirs = ['__pycache__', 'migrations', 'tests']
            
            simulation_found = False
            
            for directory in directories:
                if not os.path.exists(directory):
                    self.warning(f"Répertoire {directory} introuvable")
                    continue
                    
                for root, dirs, files in os.walk(directory):
                    # Filtrer les répertoires exclus
                    dirs[:] = [d for d in dirs if d not in excluded_dirs]
                    
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    
                                    # Vérifier chaque pattern
                                    for pattern in simulation_patterns:
                                        matches = re.findall(pattern, content)
                                        if matches and "test" not in file.lower():
                                            self.fail(f"Pattern de simulation '{pattern}' trouvé dans {file}")
                                            simulation_found = True
                            except UnicodeDecodeError:
                                self.warning(f"Impossible de lire {file_path} (encodage non UTF-8)")
            
            if not simulation_found:
                self.success("Aucun pattern de simulation trouvé dans le code")
                
            # Vérifier que les tests de simulation existent
            test_files = [
                'test_anti_simulation.py',
                'test_anti_simulation_reinforced.py'
            ]
            
            test_dir = os.path.join(settings.BASE_DIR, 'ai_assistant', 'tests')
            for test_file in test_files:
                if os.path.exists(os.path.join(test_dir, test_file)):
                    self.success(f"Fichier de test {test_file} présent")
                else:
                    self.fail(f"Fichier de test {test_file} manquant")
                    
            # Vérifier que les tests de performance existent
            performance_file = 'test_performance.py'
            if os.path.exists(os.path.join(test_dir, performance_file)):
                self.success(f"Fichier de test {performance_file} présent")
            else:
                self.fail(f"Fichier de test {performance_file} manquant")
                
            # Vérifier que les tests d'intégration réelle existent
            integration_file = 'test_real_integration.py'
            if os.path.exists(os.path.join(test_dir, integration_file)):
                self.success(f"Fichier de test {integration_file} présent")
            else:
                self.fail(f"Fichier de test {integration_file} manquant")
        except Exception as e:
            self.fail(f"Erreur lors de la validation de la qualité du code: {str(e)}")


if __name__ == "__main__":
    # Permettre l'exécution directe du script
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nms_backend.settings")
    django.setup()
    cmd = Command()
    sys.exit(0 if cmd.handle() else 1) 