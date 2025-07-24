#!/usr/bin/env python3
"""
Intégration Workflow Simulation dans le Framework
=================================================

Ce module s'intègre de manière transparente dans le framework existant
pour déclencher automatiquement le workflow Django réaliste après 
l'injection de trafic.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from .django_modules_coordinator import RealisticWorkflowSimulator

logger = logging.getLogger(__name__)

# Variable d'état pour indiquer la disponibilité du simulateur
WORKFLOW_SIMULATION_AVAILABLE = True

class WorkflowIntegrationManager:
    """
    Gestionnaire d'intégration qui s'interface avec le framework principal
    pour déclencher le workflow simulé de manière transparente.
    """
    
    def __init__(self):
        self.simulator = None
        self.integration_active = False
        self.workflow_results = {}
        logger.info("Gestionnaire d'intégration workflow initialisé")
    
    async def trigger_post_injection_workflow(self, 
                                            project_data: Dict[str, Any],
                                            test_config: Dict[str, Any], 
                                            equipment_list: List[Dict],
                                            traffic_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal - déclenche le workflow après injection de trafic.
        
        Cette méthode est appelée automatiquement par le framework principal
        après la fin de l'injection de trafic.
        
        Args:
            project_data: Données du projet GNS3 (nom, équipements, etc.)
            test_config: Configuration du test (type, niveau, durée)
            equipment_list: Liste complète des équipements
            traffic_results: Résultats de l'injection de trafic
            
        Returns:
            Résultats complets du workflow Django
        """
        logger.info("Déclenchement automatique du workflow Django post-injection")
        logger.info(f"Trafic injecté analysé: {traffic_results.get('packets_injected', 0)} paquets")
        
        try:
            # Initialiser le simulateur
            self.simulator = RealisticWorkflowSimulator()
            self.integration_active = True
            
            # Extraire les paramètres nécessaires
            project_name = project_data.get('name', 'hybrido')
            test_type = test_config.get('type', 'intermediate')
            test_level = test_config.get('level', 'medium')
            
            # Démarrer le workflow complet
            workflow_results = await self.simulator.start_realistic_workflow(
                project_name=project_name,
                test_type=test_type,
                test_level=test_level,
                equipment_list=equipment_list,
                traffic_data=traffic_results
            )
            
            # Stocker les résultats pour accès ultérieur
            self.workflow_results = workflow_results
            self.integration_active = False
            
            # Logger le succès
            if workflow_results.get('success'):
                total_duration = workflow_results.get('total_duration', 0)
                modules_activated = workflow_results.get('modules_activated', 0)
                reports_generated = workflow_results.get('reports_generated', 0)
                notifications_sent = workflow_results.get('notifications_sent', {}).get('total_sent', 0)
                
                logger.info(f"Workflow Django terminé avec succès:")
                logger.info(f"   - Durée totale: {total_duration:.1f} secondes")
                logger.info(f"   - Modules activés: {modules_activated}")
                logger.info(f"   - Rapports générés: {reports_generated}")
                logger.info(f"   - Notifications envoyées: {notifications_sent}")
            else:
                logger.error(f"Erreur workflow Django: {workflow_results.get('error', 'Unknown')}")
            
            return workflow_results
            
        except Exception as e:
            logger.error(f"Erreur intégration workflow: {e}")
            self.integration_active = False
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_workflow_status(self) -> Dict[str, Any]:
        """
        Retourne le statut actuel du workflow.
        
        Returns:
            Statut du workflow en cours ou résultats finaux
        """
        if self.integration_active and self.simulator:
            return {
                'status': 'active',
                'session_id': self.simulator.session_id,
                'start_time': self.simulator.start_time.isoformat(),
                'modules_status': self.simulator.modules
            }
        elif self.workflow_results:
            return {
                'status': 'completed',
                'results': self.workflow_results
            }
        else:
            return {
                'status': 'inactive'
            }
    
    def is_workflow_active(self) -> bool:
        """Vérifie si un workflow est actuellement en cours."""
        return self.integration_active
    
    def get_last_results(self) -> Optional[Dict[str, Any]]:
        """Retourne les derniers résultats de workflow."""
        return self.workflow_results if self.workflow_results else None

# Instance globale pour l'intégration
workflow_manager = WorkflowIntegrationManager()

# Fonctions d'interface pour le framework principal
async def trigger_django_workflow(project_data: Dict[str, Any],
                                test_config: Dict[str, Any],
                                equipment_list: List[Dict],
                                traffic_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interface principale pour déclencher le workflow Django.
    
    Cette fonction est appelée par le framework principal après l'injection de trafic.
    """
    return await workflow_manager.trigger_post_injection_workflow(
        project_data=project_data,
        test_config=test_config,
        equipment_list=equipment_list,
        traffic_results=traffic_results
    )

def get_django_workflow_status() -> Dict[str, Any]:
    """Interface pour obtenir le statut du workflow Django."""
    return workflow_manager.get_workflow_status()

def is_django_workflow_active() -> bool:
    """Interface pour vérifier si un workflow Django est actif."""
    return workflow_manager.is_workflow_active()

def get_last_django_results() -> Optional[Dict[str, Any]]:
    """Interface pour obtenir les derniers résultats Django."""
    return workflow_manager.get_last_results()