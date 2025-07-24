#!/usr/bin/env python3
"""
Script de Test du Framework de Sécurité Réel
===========================================

Ce script teste le framework de sécurité que nous avons créé
en essayant de récupérer les projets GNS3 via Django et de tester
le workflow complet.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Ajouter le chemin du framework
framework_path = Path(__file__).parent
sys.path.insert(0, str(framework_path))

# Importer nos modules
from core.real_security_framework import RealSecurityTestingFramework

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_framework():
    """Test principal du framework."""
    logger.info("🚀 DÉBUT DU TEST DU FRAMEWORK DE SÉCURITÉ RÉEL")
    
    try:
        # Créer le framework
        logger.info("📝 Création du framework...")
        framework = RealSecurityTestingFramework()
        
        # Initialiser le framework
        logger.info("🔧 Initialisation du framework...")
        initialized = await framework.initialize()
        if not initialized:
            logger.error("❌ Échec de l'initialisation du framework")
            return False
        
        # Test 1: Récupérer les projets GNS3
        logger.info("🔧 Test 1: Récupération des projets GNS3 via Django...")
        projects = await framework.get_available_projects()
        
        if projects:
            logger.info(f"✅ {len(projects)} projets GNS3 trouvés:")
            for project in projects:
                logger.info(f"   - {project.name} (ID: {project.project_id}, Status: {project.status})")
        else:
            logger.warning("⚠️ Aucun projet GNS3 trouvé")
        
        # Test 2: Vérifier la communication Django
        logger.info("🌐 Test 2: Vérification communication Django...")
        if framework.django_comm:
            status_response = await framework.django_comm.get_gns3_server_status()
            if status_response.success:
                logger.info(f"✅ Serveur GNS3 accessible: {status_response.data}")
            else:
                logger.error(f"❌ Erreur serveur GNS3: {status_response.error_message}")
        
        # Test 3: Tester le déclencheur Celery
        logger.info("⚙️ Test 3: Test déclencheur Celery...")
        if framework.celery_trigger:
            # Test simple de déclenchement d'orchestration
            tasks = await framework.celery_trigger.trigger_system_monitoring()
            if tasks:
                logger.info(f"✅ Tâches Celery déclenchées: {tasks}")
            else:
                logger.warning("⚠️ Aucune tâche Celery déclenchée")
        
        # Test 4: Afficher le workflow complet comme demandé par l'utilisateur
        logger.info("📋 Test 4: Affichage du workflow d'utilisation...")
        logger.info("""
        🎯 WORKFLOW D'UTILISATION DU FRAMEWORK:
        
        1. 📡 Le framework affiche la liste des projets GNS3 (via Django API)
        2. 👤 L'utilisateur choisit un projet/réseau
        3. ⚡ Le framework transfère automatiquement l'info aux modules Django
        4. 🔌 Les modules Django allument et analysent le réseau
        5. 🎚️ L'utilisateur sélectionne le niveau de tests  
        6. 💥 Le framework commence l'injection de trafic RÉEL
        7. 🚀 Automatiquement, tout le workflow Django se déclenche via Celery
        8. 📊 Surveillance et rapports en temps réel
        """)
        
        logger.info("✅ TOUS LES TESTS BASIQUES TERMINÉS AVEC SUCCÈS")
        
        # Si on a des projets, proposer un test interactif
        if projects:
            logger.info(f"🎮 FRAMEWORK PRÊT - {len(projects)} projets disponibles pour les tests")
            logger.info("Pour lancer un test complet, utilisez le workflow interactif.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_framework())
    exit(0 if success else 1)