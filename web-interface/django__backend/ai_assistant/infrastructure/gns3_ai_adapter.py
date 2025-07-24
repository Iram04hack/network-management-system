"""
Adaptateur GNS3 pour l'assistant IA.

Ce module fournit l'interface entre l'assistant IA et le service
de contextualisation GNS3, permettant l'enrichissement des réponses
avec des informations de topologie réseau.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .gns3_context_service import gns3_context_service, NetworkTopologyContext
from ..domain.services.network_analysis_service import NetworkAnalysisService

logger = logging.getLogger(__name__)


class GNS3AIAdapter:
    """
    Adaptateur pour intégrer les données GNS3 dans l'assistant IA.
    
    Fournit des méthodes pour enrichir les réponses de l'IA avec
    le contexte de l'infrastructure réseau GNS3.
    """
    
    def __init__(self):
        """Initialise l'adaptateur GNS3 pour l'IA."""
        self.context_service = gns3_context_service
        self.network_analysis = NetworkAnalysisService()
        self._last_context_update = None
    
    async def get_network_context_for_ai(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Récupère le contexte réseau formaté pour l'assistant IA.
        
        Args:
            force_refresh: Force la mise à jour du cache
            
        Returns:
            Contexte réseau formaté pour l'IA
        """
        try:
            # Récupérer le contexte de topologie
            topology_context = await self.context_service.get_topology_context(force_refresh)
            
            # Générer le résumé textuel pour l'IA
            ai_summary = self.context_service.generate_ai_context_summary(topology_context)
            
            # Enrichir avec des analyses
            analysis_summary = self._generate_network_analysis_summary(topology_context)
            
            # Préparer le contexte complet
            context = {
                'topology_summary': ai_summary,
                'analysis_summary': analysis_summary,
                'infrastructure_stats': topology_context.topology_stats,
                'available_projects': [p.get('name') for p in topology_context.projects],
                'active_devices': [
                    n.get('name') for n in topology_context.nodes 
                    if n.get('status') == 'started'
                ],
                'device_types': list(topology_context.topology_stats.get('nodes_by_type', {}).keys()),
                'gns3_server_status': topology_context.server_info.status.value,
                'last_updated': topology_context.last_updated.isoformat(),
                'context_available': len(topology_context.nodes) > 0
            }
            
            self._last_context_update = datetime.now()
            return context
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du contexte réseau pour l'IA: {e}")
            return {
                'topology_summary': "Contexte réseau non disponible",
                'analysis_summary': "Analyse non disponible",
                'infrastructure_stats': {},
                'available_projects': [],
                'active_devices': [],
                'device_types': [],
                'gns3_server_status': 'error',
                'last_updated': datetime.now().isoformat(),
                'context_available': False,
                'error': str(e)
            }
    
    def _generate_network_analysis_summary(self, context: NetworkTopologyContext) -> str:
        """
        Génère un résumé d'analyse réseau.
        
        Args:
            context: Contexte de topologie réseau
            
        Returns:
            Résumé d'analyse pour l'IA
        """
        if not context.nodes:
            return "Aucune analyse réseau disponible."
        
        analysis_parts = []
        
        # Analyse de la connectivité
        total_nodes = len(context.nodes)
        total_links = len(context.links)
        running_nodes = len([n for n in context.nodes if n.get('status') == 'started'])
        
        if total_nodes > 0:
            connectivity_ratio = total_links / total_nodes if total_nodes > 0 else 0
            uptime_ratio = running_nodes / total_nodes if total_nodes > 0 else 0
            
            analysis_parts.append(f"Analyse de connectivité :")
            analysis_parts.append(f"- Ratio connectivité: {connectivity_ratio:.2f} (liens/nœuds)")
            analysis_parts.append(f"- Taux de disponibilité: {uptime_ratio:.2%}")
            
            # Recommandations basiques
            if connectivity_ratio < 1.5:
                analysis_parts.append("- Recommandation: Connectivité faible, considérer l'ajout de liens redondants")
            elif connectivity_ratio > 3.0:
                analysis_parts.append("- Observation: Réseau dense avec haute redondance")
            
            if uptime_ratio < 0.5:
                analysis_parts.append("- Alerte: Moins de 50% des dispositifs sont actifs")
            elif uptime_ratio > 0.9:
                analysis_parts.append("- État: Excellent taux de disponibilité des dispositifs")
        
        # Analyse des types de dispositifs
        device_types = context.topology_stats.get('nodes_by_type', {})
        if device_types:
            analysis_parts.append(f"\nDistribution des équipements :")
            for device_type, count in sorted(device_types.items(), key=lambda x: x[1], reverse=True)[:3]:
                percentage = (count / total_nodes) * 100 if total_nodes > 0 else 0
                analysis_parts.append(f"- {device_type}: {count} ({percentage:.1f}%)")
        
        # Analyse de la complexité
        complexity = context.topology_stats.get('network_complexity_score', 0)
        if complexity > 0:
            if complexity < 30:
                analysis_parts.append(f"\nComplexité: Réseau simple (score {complexity}) - Facile à gérer")
            elif complexity < 70:
                analysis_parts.append(f"\nComplexité: Réseau modéré (score {complexity}) - Gestion standard")
            else:
                analysis_parts.append(f"\nComplexité: Réseau complexe (score {complexity}) - Surveillance renforcée requise")
        
        return "\n".join(analysis_parts)
    
    async def analyze_device_context(self, device_name: str) -> Optional[Dict[str, Any]]:
        """
        Analyse le contexte d'un dispositif spécifique.
        
        Args:
            device_name: Nom du dispositif à analyser
            
        Returns:
            Contexte d'analyse du dispositif
        """
        try:
            device_details = await self.context_service.get_device_details(device_name)
            
            if not device_details:
                return None
            
            # Enrichir avec l'analyse réseau
            analysis_result = {}
            try:
                # Simuler une analyse de performance pour le dispositif
                analysis_result = self.network_analysis.analyze_device_performance(device_name)
            except Exception as e:
                logger.warning(f"Impossible d'analyser les performances de {device_name}: {e}")
            
            return {
                'device_info': device_details,
                'performance_analysis': analysis_result,
                'context_summary': self._generate_device_context_summary(device_details, analysis_result),
                'recommendations': self._generate_device_recommendations(device_details)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du contexte du dispositif {device_name}: {e}")
            return None
    
    def _generate_device_context_summary(self, device_info: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Génère un résumé contextuel pour un dispositif."""
        summary_parts = []
        
        name = device_info.get('name', 'Dispositif inconnu')
        device_type = device_info.get('type', 'Type inconnu')
        status = device_info.get('status', 'Statut inconnu')
        project = device_info.get('project', 'Projet inconnu')
        
        summary_parts.append(f"Dispositif {name} :")
        summary_parts.append(f"- Type: {device_type}")
        summary_parts.append(f"- Statut: {status}")
        summary_parts.append(f"- Projet: {project}")
        
        # Informations de console si disponibles
        if device_info.get('console_port'):
            summary_parts.append(f"- Console: {device_info.get('console_host', 'localhost')}:{device_info.get('console_port')}")
        
        # Analyse de performance si disponible
        if analysis and 'cpu_usage' in analysis:
            cpu = analysis['cpu_usage']
            memory = analysis['memory_usage']
            summary_parts.append(f"- CPU: {cpu.get('current', 0)}% ({cpu.get('status', 'inconnu')})")
            summary_parts.append(f"- Mémoire: {memory.get('current', 0)}% ({memory.get('status', 'inconnu')})")
        
        return "\n".join(summary_parts)
    
    def _generate_device_recommendations(self, device_info: Dict[str, Any]) -> List[str]:
        """Génère des recommandations pour un dispositif."""
        recommendations = []
        
        status = device_info.get('status', '').lower()
        device_type = device_info.get('type', '').lower()
        
        # Recommandations basées sur le statut
        if status == 'stopped':
            recommendations.append("Dispositif arrêté - Vérifier s'il doit être démarré")
        elif status == 'suspended':
            recommendations.append("Dispositif suspendu - Reprendre l'exécution si nécessaire")
        
        # Recommandations basées sur le type
        if 'router' in device_type:
            recommendations.append("Routeur - Vérifier la configuration de routage et les interfaces")
        elif 'switch' in device_type:
            recommendations.append("Commutateur - Surveiller les VLANs et les ports d'accès")
        elif 'firewall' in device_type:
            recommendations.append("Pare-feu - Auditer les règles de sécurité")
        
        return recommendations
    
    async def analyze_project_context(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Analyse le contexte d'un projet spécifique.
        
        Args:
            project_name: Nom du projet à analyser
            
        Returns:
            Contexte d'analyse du projet
        """
        try:
            project_topology = await self.context_service.get_project_topology(project_name)
            
            if not project_topology:
                return None
            
            # Analyser la topologie du projet
            topology_analysis = self._analyze_project_topology(project_topology)
            
            return {
                'project_info': project_topology['project'],
                'topology_stats': project_topology['stats'],
                'topology_analysis': topology_analysis,
                'devices': project_topology['nodes'],
                'connections': project_topology['links'],
                'recommendations': self._generate_project_recommendations(project_topology)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du contexte du projet {project_name}: {e}")
            return None
    
    def _analyze_project_topology(self, project_topology: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse la topologie d'un projet."""
        stats = project_topology['stats']
        nodes = project_topology['nodes']
        links = project_topology['links']
        
        analysis = {
            'network_density': 0,
            'central_devices': [],
            'isolated_devices': [],
            'redundancy_level': 'low',
            'topology_health': 'unknown'
        }
        
        total_nodes = stats['total_nodes']
        total_links = stats['total_links']
        
        if total_nodes > 0:
            # Calculer la densité du réseau
            max_possible_links = total_nodes * (total_nodes - 1) / 2
            analysis['network_density'] = (total_links / max_possible_links) * 100 if max_possible_links > 0 else 0
            
            # Identifier les dispositifs centraux (plus de connexions)
            device_connections = {}
            for link in links:
                for node in link.get('nodes', []):
                    node_id = node.get('node_id')
                    if node_id:
                        device_connections[node_id] = device_connections.get(node_id, 0) + 1
            
            # Dispositifs avec le plus de connexions
            sorted_devices = sorted(device_connections.items(), key=lambda x: x[1], reverse=True)
            central_device_ids = [d[0] for d in sorted_devices[:3] if d[1] > 2]
            
            analysis['central_devices'] = [
                node.get('name', 'Inconnu') for node in nodes 
                if node.get('node_id') in central_device_ids
            ]
            
            # Dispositifs isolés (aucune connexion)
            connected_device_ids = set(device_connections.keys())
            all_device_ids = {node.get('node_id') for node in nodes if node.get('node_id')}
            isolated_device_ids = all_device_ids - connected_device_ids
            
            analysis['isolated_devices'] = [
                node.get('name', 'Inconnu') for node in nodes 
                if node.get('node_id') in isolated_device_ids
            ]
            
            # Évaluer le niveau de redondance
            if analysis['network_density'] > 50:
                analysis['redundancy_level'] = 'high'
            elif analysis['network_density'] > 25:
                analysis['redundancy_level'] = 'medium'
            else:
                analysis['redundancy_level'] = 'low'
            
            # Santé globale de la topologie
            running_ratio = stats['running_nodes'] / total_nodes if total_nodes > 0 else 0
            if running_ratio > 0.8 and analysis['network_density'] > 20:
                analysis['topology_health'] = 'excellent'
            elif running_ratio > 0.6:
                analysis['topology_health'] = 'good'
            elif running_ratio > 0.3:
                analysis['topology_health'] = 'fair'
            else:
                analysis['topology_health'] = 'poor'
        
        return analysis
    
    def _generate_project_recommendations(self, project_topology: Dict[str, Any]) -> List[str]:
        """Génère des recommandations pour un projet."""
        recommendations = []
        stats = project_topology['stats']
        
        # Recommandations basées sur les statistiques
        if stats['running_nodes'] < stats['total_nodes']:
            stopped_count = stats['total_nodes'] - stats['running_nodes']
            recommendations.append(f"Démarrer les {stopped_count} dispositif(s) arrêté(s)")
        
        if stats['total_links'] < stats['total_nodes']:
            recommendations.append("Ajouter des connexions pour améliorer la redondance")
        
        # Recommandations basées sur les types de dispositifs
        node_types = stats.get('node_types', [])
        if 'router' in node_types and 'switch' not in node_types:
            recommendations.append("Considérer l'ajout de commutateurs pour la segmentation")
        
        if len(node_types) == 1:
            recommendations.append("Diversifier les types d'équipements pour une topologie plus réaliste")
        
        return recommendations
    
    def is_available(self) -> bool:
        """Vérifie si l'adaptateur GNS3 est disponible."""
        return self.context_service.is_available()
    
    def get_last_update_info(self) -> Dict[str, Any]:
        """Retourne les informations de dernière mise à jour."""
        return {
            'last_context_update': self._last_context_update.isoformat() if self._last_context_update else None,
            'gns3_available': self.is_available(),
            'cache_valid': self.context_service._topology_cache is not None
        }


# Instance globale de l'adaptateur
gns3_ai_adapter = GNS3AIAdapter()