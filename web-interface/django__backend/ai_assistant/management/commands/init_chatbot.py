from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ai_assistant.models import AIModel, KnowledgeBase, Command

class Command(BaseCommand):
    help = 'Initialise le chatbot avec les données de base'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-models',
            action='store_true',
            help='Skip AI models creation',
        )
        parser.add_argument(
            '--skip-knowledge',
            action='store_true', 
            help='Skip knowledge base creation',
        )
        parser.add_argument(
            '--skip-commands',
            action='store_true',
            help='Skip commands creation',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 Initialisation du chatbot...")
        
        created_count = 0
        
        # Créer les modèles IA par défaut
        if not options['skip_models']:
            models_data = [
                {
                    "name": "ChatGPT-3.5",
                    "provider": "openai",
                    "model_name": "gpt-3.5-turbo",
                    "capabilities": {
                        "chat": True,
                        "code_generation": True,
                        "analysis": True
                    },
                    "max_tokens": 4096,
                    "temperature": 0.7
                },
                {
                    "name": "ChatGPT-4",
                    "provider": "openai", 
                    "model_name": "gpt-4",
                    "capabilities": {
                        "chat": True,
                        "code_generation": True,
                        "analysis": True,
                        "complex_reasoning": True
                    },
                    "max_tokens": 8192,
                    "temperature": 0.7
                },
                {
                    "name": "Claude-3",
                    "provider": "anthropic",
                    "model_name": "claude-3-sonnet-20240229",
                    "capabilities": {
                        "chat": True,
                        "analysis": True,
                        "safety": True
                    },
                    "max_tokens": 4096,
                    "temperature": 0.7
                }
            ]
            
            for model_data in models_data:
                model, created = AIModel.objects.get_or_create(
                    name=model_data["name"],
                    defaults=model_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  ✅ Modèle IA créé: {model_data['name']}")
        
        # Créer la base de connaissances par défaut
        if not options['skip_knowledge']:
            knowledge_data = [
                {
                    "category": "network",
                    "question": "Comment configurer un VLAN ?",
                    "answer": "Pour configurer un VLAN, utilisez les commandes suivantes:\n1. Entrez en mode configuration: enable -> configure terminal\n2. Créez le VLAN: vlan [numéro]\n3. Nommez le VLAN: name [nom]\n4. Assignez des ports: interface [port] -> switchport mode access -> switchport access vlan [numéro]",
                    "keywords": ["vlan", "configuration", "réseau", "switch"],
                    "related_commands": ["vlan", "interface", "switchport"]
                },
                {
                    "category": "security",
                    "question": "Comment sécuriser les ports SSH ?",
                    "answer": "Pour sécuriser SSH:\n1. Changez le port par défaut dans /etc/ssh/sshd_config\n2. Désactivez l'authentification par mot de passe\n3. Utilisez des clés SSH\n4. Configurez fail2ban\n5. Limitez les utilisateurs autorisés",
                    "keywords": ["ssh", "sécurité", "authentification", "fail2ban"],
                    "related_commands": ["ssh", "scp", "ssh-keygen"]
                },
                {
                    "category": "troubleshooting",
                    "question": "Comment diagnostiquer des problèmes de connectivité réseau ?",
                    "answer": "Étapes de diagnostic:\n1. Vérifiez la connectivité physique\n2. Testez avec ping\n3. Vérifiez la table de routage (route -n)\n4. Contrôlez les règles firewall\n5. Analysez les logs systèmes\n6. Utilisez traceroute pour tracer le chemin",
                    "keywords": ["diagnostic", "connectivité", "ping", "route", "firewall"],
                    "related_commands": ["ping", "traceroute", "netstat", "ss"]
                },
                {
                    "category": "monitoring",
                    "question": "Comment surveiller les performances réseau ?",
                    "answer": "Outils de monitoring réseau:\n1. SNMP pour les équipements\n2. Nagios/Zabbix pour la supervision\n3. Wireshark pour l'analyse de trafic\n4. iftop/nload pour la bande passante\n5. MRTG/Cacti pour les graphiques\n6. Logs d'événements",
                    "keywords": ["monitoring", "snmp", "nagios", "wireshark", "surveillance"],
                    "related_commands": ["snmpwalk", "iftop", "nload", "tcpdump"]
                }
            ]
            
            for kb_data in knowledge_data:
                kb, created = KnowledgeBase.objects.get_or_create(
                    question=kb_data["question"],
                    defaults=kb_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  📚 Entrée KB créée: {kb_data['category']}")
        
        # Créer les commandes par défaut
        if not options['skip_commands']:
            commands_data = [
                {
                    "name": "ping",
                    "category": "network",
                    "description": "Teste la connectivité vers une adresse IP",
                    "command_template": "ping -c 4 {target}",
                    "parameters": {
                        "target": {
                            "type": "string",
                            "required": True,
                            "description": "Adresse IP ou nom d'hôte cible"
                        }
                    },
                    "required_permission": "read",
                    "is_safe": True,
                    "timeout_seconds": 30
                },
                {
                    "name": "show_interfaces",
                    "category": "network",
                    "description": "Affiche l'état des interfaces réseau",
                    "command_template": "ip addr show",
                    "parameters": {},
                    "required_permission": "read",
                    "is_safe": True,
                    "timeout_seconds": 10
                },
                {
                    "name": "show_routes",
                    "category": "network", 
                    "description": "Affiche la table de routage",
                    "command_template": "ip route show",
                    "parameters": {},
                    "required_permission": "read",
                    "is_safe": True,
                    "timeout_seconds": 10
                },
                {
                    "name": "restart_service",
                    "category": "system",
                    "description": "Redémarre un service système",
                    "command_template": "systemctl restart {service}",
                    "parameters": {
                        "service": {
                            "type": "string",
                            "required": True,
                            "description": "Nom du service à redémarrer"
                        }
                    },
                    "required_permission": "admin",
                    "is_safe": False,
                    "timeout_seconds": 60
                },
                {
                    "name": "check_disk_space",
                    "category": "monitoring",
                    "description": "Vérifie l'espace disque disponible",
                    "command_template": "df -h",
                    "parameters": {},
                    "required_permission": "read",
                    "is_safe": True,
                    "timeout_seconds": 10
                }
            ]
            
            for cmd_data in commands_data:
                cmd, created = Command.objects.get_or_create(
                    name=cmd_data["name"],
                    defaults=cmd_data
                )
                if created:
                    created_count += 1
                    self.stdout.write(f"  ⚡ Commande créée: {cmd_data['name']}")
        
        # Créer un utilisateur système pour le bot
        system_user, created = User.objects.get_or_create(
            username='ai_assistant_system',
            defaults={
                'email': 'ai-assistant@nms.local',
                'first_name': 'AI',
                'last_name': 'Assistant',
                'is_staff': False,
                'is_active': True
            }
        )
        
        if created:
            created_count += 1
            self.stdout.write("  👤 Utilisateur système créé")
        
        # Statistiques finales
        total_models = AIModel.objects.count()
        total_knowledge = KnowledgeBase.objects.count()
        total_commands = Command.objects.count()
        
        self.stdout.write("\n📊 État du système:")
        self.stdout.write(f"  • Modèles IA: {total_models}")
        self.stdout.write(f"  • Entrées KB: {total_knowledge}")
        self.stdout.write(f"  • Commandes: {total_commands}")
        self.stdout.write(f"  • Créés cette session: {created_count}")
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Chatbot initialisé avec succès !"))
        
        # Conseils pour la suite
        self.stdout.write("\n💡 Prochaines étapes recommandées:")
        self.stdout.write("  1. Configurez les clés API dans les modèles IA")
        self.stdout.write("  2. Testez la connectivité avec: python manage.py test_ai_connection")
        self.stdout.write("  3. Créez des migrations: python manage.py makemigrations")
        self.stdout.write("  4. Appliquez les migrations: python manage.py migrate")