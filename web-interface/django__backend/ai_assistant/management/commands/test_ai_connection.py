from django.core.management.base import BaseCommand
from ai_assistant.models import AIModel
from ai_assistant.application.chatbot_service import ChatbotService

class Command(BaseCommand):
    help = 'Teste la connectivité avec les services IA'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            help='Nom du modèle IA à tester (teste tous si non spécifié)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Affichage détaillé',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🔍 Test de connectivité des services IA...")
        
        # Sélectionner les modèles à tester
        if options['model']:
            models = AIModel.objects.filter(name=options['model'], is_active=True)
            if not models.exists():
                self.stderr.write(f"❌ Modèle '{options['model']}' non trouvé ou inactif")
                return
        else:
            models = AIModel.objects.filter(is_active=True)
        
        if not models.exists():
            self.stderr.write("❌ Aucun modèle IA actif trouvé")
            return
        
        self.stdout.write(f"📋 Test de {models.count()} modèle(s)...\n")
        
        # Initialiser le service chatbot
        try:
            chatbot_service = ChatbotService()
        except Exception as e:
            self.stderr.write(f"❌ Erreur d'initialisation du service chatbot: {e}")
            return
        
        success_count = 0
        total_count = models.count()
        
        for model in models:
            self.stdout.write(f"🧪 Test du modèle: {model.name} ({model.provider})")
            
            # Vérifier la configuration
            config_ok = True
            if model.provider in ['openai', 'anthropic'] and not model.api_key:
                self.stdout.write("  ⚠️  Clé API manquante")
                config_ok = False
            
            if not model.model_name:
                self.stdout.write("  ⚠️  Nom de modèle manquant")
                config_ok = False
            
            if not config_ok:
                self.stdout.write("  ❌ Configuration incomplète\n")
                continue
            
            # Test de connectivité
            try:
                test_message = "Bonjour, pouvez-vous me répondre brièvement ?"
                
                # Simuler une requête (à adapter selon votre implémentation)
                start_time = __import__('time').time()
                
                # NOTE: Cette partie doit être adaptée selon votre implémentation réelle
                # Si vous avez des simulations, ce test les détectera
                response = chatbot_service.process_message(
                    test_message, 
                    user_id=1,  # Utilisateur de test
                    force_model=model.name
                )
                
                end_time = __import__('time').time()
                latency = round(end_time - start_time, 3)
                
                if response and response.get('content'):
                    content = response['content']
                    
                    # Détecter les simulations
                    simulation_indicators = [
                        'simulation', 'simulé', 'placeholder', 'test',
                        'non implémenté', 'non implémentée', 'factice'
                    ]
                    
                    is_simulation = any(indicator in content.lower() for indicator in simulation_indicators)
                    
                    if is_simulation:
                        self.stdout.write(f"  ⚠️  Réponse simulée détectée: {content[:100]}...")
                        self.stdout.write("  ❌ SIMULATION - Pas d'implémentation réelle\n")
                    else:
                        self.stdout.write(f"  ✅ Réponse reçue ({latency}s)")
                        if options['verbose']:
                            self.stdout.write(f"     Contenu: {content[:100]}...")
                        self.stdout.write("  ✅ Test réussi\n")
                        success_count += 1
                else:
                    self.stdout.write("  ❌ Aucune réponse reçue\n")
                    
            except Exception as e:
                self.stdout.write(f"  ❌ Erreur: {str(e)}\n")
        
        # Résumé final
        self.stdout.write("=" * 50)
        self.stdout.write(f"📊 Résultats: {success_count}/{total_count} modèles fonctionnels")
        
        if success_count == total_count:
            self.stdout.write(self.style.SUCCESS("🎉 Tous les tests ont réussi !"))
        elif success_count > 0:
            self.stdout.write(self.style.WARNING(f"⚠️  {total_count - success_count} modèle(s) en échec"))
        else:
            self.stdout.write(self.style.ERROR("❌ Aucun modèle fonctionnel"))
        
        # Recommandations
        if success_count < total_count:
            self.stdout.write("\n💡 Recommandations:")
            self.stdout.write("  • Vérifiez les clés API dans l'admin Django")
            self.stdout.write("  • Contrôlez la connectivité Internet")
            self.stdout.write("  • Consultez les logs pour plus de détails")
            self.stdout.write("  • Éliminez toutes les simulations du code")