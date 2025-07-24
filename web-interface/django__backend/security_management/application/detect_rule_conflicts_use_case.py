"""
Cas d'utilisation pour la détection de conflits entre règles de sécurité.

Ce module définit le cas d'utilisation pour détecter, analyser et résoudre
les conflits potentiels entre différentes règles de sécurité, avec intégration
des services Docker pour validation en temps réel.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from ..domain.conflict_detector_factory import conflict_detector_factory
from ..domain.interfaces import RuleConflict
from ..domain.repository_interfaces import SecurityRuleRepository
from ..infrastructure.docker_integration import DockerServiceManager

logger = logging.getLogger(__name__)


class DetectRuleConflictsUseCase:
    """
    Cas d'utilisation pour détecter les conflits entre règles de sécurité.
    
    Ce cas d'utilisation fournit des méthodes pour analyser les potentiels
    conflits entre une nouvelle règle et des règles existantes, ainsi que
    pour analyser les conflits dans un ensemble complet de règles.
    """
    
    def __init__(self, security_rule_repository: SecurityRuleRepository):
        """
        Initialise le cas d'utilisation.
        
        Args:
            security_rule_repository: Repository pour accéder aux règles de sécurité
        """
        self._security_rule_repository = security_rule_repository
        self._docker_manager = DockerServiceManager()
        
    def detect_conflicts_for_new_rule(self, rule_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Détecte les conflits entre une nouvelle règle et les règles existantes.
        
        Args:
            rule_data: Données de la nouvelle règle, incluant au minimum:
                - rule_type: Type de règle (firewall, ids, access_control)
                - content: Contenu de la règle
                
        Returns:
            Un dictionnaire contenant:
                - conflicts: Liste des conflits détectés
                - conflict_count: Nombre total de conflits
                - statistics: Statistiques sur les types de conflits
                - validation_results: Résultats de validation Docker
        """
        # Validation des entrées
        rule_type = rule_data.get('rule_type')
        if not rule_type:
            raise ValueError("Le type de règle est requis")
            
        rule_content = rule_data.get('content')
        if not rule_content:
            raise ValueError("Le contenu de la règle est requis")
        
        try:
            # Validation préalable via services Docker
            validation_results = self._validate_rule_via_docker(rule_type, rule_content)
            
            # Récupérer les règles existantes du même type
            existing_rules = self._get_existing_rules_by_type(rule_type)
            
            # Détecter les conflits
            conflicts = conflict_detector_factory.detect_conflicts_by_type(
                rule_data, existing_rules, rule_type
            )
            
            # Compiler les statistiques
            conflict_types = {}
            severity_counts = {}
            
            for conflict in conflicts:
                # Statistiques par type de conflit
                conflict_type = conflict.get('type', 'unknown')
                if conflict_type not in conflict_types:
                    conflict_types[conflict_type] = 0
                conflict_types[conflict_type] += 1
                
                # Statistiques par sévérité
                severity = conflict.get('severity', 'medium')
                if severity not in severity_counts:
                    severity_counts[severity] = 0
                severity_counts[severity] += 1
            
            # Enrichir les conflits avec des informations de contexte
            enriched_conflicts = self._enrich_conflicts_with_context(conflicts, rule_type)
            
            return {
                'conflicts': enriched_conflicts,
                'conflict_count': len(conflicts),
                'statistics': {
                    'conflict_types': conflict_types,
                    'severity_counts': severity_counts,
                    'total_rules_checked': len(existing_rules),
                    'validation_status': validation_results.get('status', 'unknown')
                },
                'validation_results': validation_results,
                'recommendations': self._generate_overall_recommendations(conflicts, rule_type)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection de conflits: {str(e)}")
            raise
        
    def analyze_ruleset_conflicts(self, rule_type: str) -> Dict[str, Any]:
        """
        Analyse les conflits dans un ensemble complet de règles du même type.
        
        Args:
            rule_type: Type de règles à analyser
            
        Returns:
            Un dictionnaire contenant:
                - conflicts: Liste des conflits détectés
                - conflict_count: Nombre total de conflits
                - statistics: Statistiques sur les types de conflits
                - conflict_graph: Graphe des relations de conflit entre règles
                - health_score: Score de santé du jeu de règles (0-100)
        """
        if not rule_type:
            raise ValueError("Le type de règle est requis")
        
        try:
            # Récupérer toutes les règles du type spécifié
            rules = self._get_existing_rules_by_type(rule_type)
            
            if not rules:
                return {
                    'conflicts': [],
                    'conflict_count': 0,
                    'statistics': {'total_rules_analyzed': 0},
                    'conflict_graph': {},
                    'health_score': 100,
                    'message': f"Aucune règle de type '{rule_type}' trouvée"
                }
            
            # Obtenir le détecteur approprié
            detector = conflict_detector_factory.create_detector(rule_type)
            
            # Analyser l'ensemble des règles
            conflicts = detector.analyze_ruleset(rules)
            
            # Convertir les objets RuleConflict en dictionnaires
            conflict_dicts = [self._conflict_to_dict(conflict) for conflict in conflicts]
            
            # Compiler les statistiques et construire le graphe
            statistics, conflict_graph = self._build_analysis_statistics(conflict_dicts, rules)
            
            # Calculer le score de santé
            health_score = self._calculate_health_score(conflict_dicts, len(rules))
            
            # Enrichir avec des informations contextuelles
            enriched_conflicts = self._enrich_conflicts_with_context(conflict_dicts, rule_type)
            
            return {
                'conflicts': enriched_conflicts,
                'conflict_count': len(conflicts),
                'statistics': statistics,
                'conflict_graph': conflict_graph,
                'health_score': health_score,
                'recommendations': self._generate_ruleset_recommendations(conflict_dicts, rule_type),
                'optimization_suggestions': self._generate_optimization_suggestions(rules, conflict_dicts)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du jeu de règles: {str(e)}")
            raise
        
    def suggest_conflict_resolutions(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Suggère des résolutions pour les conflits détectés.
        
        Args:
            conflicts: Liste des conflits à résoudre
            
        Returns:
            Liste des suggestions de résolution avec priorités et impacts
        """
        if not conflicts:
            return []
        
        resolutions = []
        
        try:
            for conflict in conflicts:
                conflict_type = conflict.get('type', 'unknown')
                severity = conflict.get('severity', 'medium')
                
                resolution = {
                    'conflict_id': conflict.get('id'),
                    'conflict_type': conflict_type,
                    'severity': severity,
                    'suggestions': [],
                    'priority': self._calculate_resolution_priority(conflict),
                    'estimated_impact': self._estimate_resolution_impact(conflict)
                }
                
                # Suggérer des résolutions selon le type de conflit
                if conflict_type == 'shadow':
                    resolution['suggestions'].extend([
                        {
                            'action': 'delete',
                            'rule_id': conflict.get('rule1_id'),
                            'reason': 'La règle est complètement masquée et n\'aura jamais d\'effet',
                            'confidence': 0.9,
                            'risk_level': 'low'
                        },
                        {
                            'action': 'reorder',
                            'rule_ids': [conflict.get('rule1_id'), conflict.get('rule2_id')],
                            'reason': 'Placer la règle masquée avant la règle qui la masque',
                            'confidence': 0.8,
                            'risk_level': 'medium'
                        }
                    ])
                    
                elif conflict_type == 'redundant':
                    resolution['suggestions'].extend([
                        {
                            'action': 'merge',
                            'rule_ids': [conflict.get('rule1_id'), conflict.get('rule2_id')],
                            'reason': 'Les règles sont redondantes et peuvent être fusionnées',
                            'confidence': 0.85,
                            'risk_level': 'low'
                        },
                        {
                            'action': 'delete',
                            'rule_id': max(conflict.get('rule1_id', 0), conflict.get('rule2_id', 0)),
                            'reason': 'Supprimer la règle la plus récente si elles sont identiques',
                            'confidence': 0.7,
                            'risk_level': 'medium'
                        }
                    ])
                    
                elif conflict_type == 'correlation':
                    resolution['suggestions'].extend([
                        {
                            'action': 'reorder',
                            'rule_ids': [conflict.get('rule1_id'), conflict.get('rule2_id')],
                            'reason': 'Les règles se chevauchent partiellement, leur ordre est important',
                            'confidence': 0.75,
                            'risk_level': 'medium'
                        },
                        {
                            'action': 'modify',
                            'rule_ids': [conflict.get('rule1_id'), conflict.get('rule2_id')],
                            'reason': 'Préciser les conditions pour éviter le chevauchement',
                            'confidence': 0.8,
                            'risk_level': 'high'
                        }
                    ])
                    
                elif conflict_type == 'generalization':
                    resolution['suggestions'].extend([
                        {
                            'action': 'delete',
                            'rule_id': conflict.get('rule2_id'),
                            'reason': 'La règle spécifique est couverte par la règle plus générale',
                            'confidence': 0.8,
                            'risk_level': 'low'
                        },
                        {
                            'action': 'reorder',
                            'rule_ids': [conflict.get('rule2_id'), conflict.get('rule1_id')],
                            'reason': 'Placer la règle plus spécifique avant la règle générale',
                            'confidence': 0.9,
                            'risk_level': 'low'
                        }
                    ])
                
                # Ajouter des suggestions génériques si aucune spécifique
                if not resolution['suggestions']:
                    resolution['suggestions'].append({
                        'action': 'review',
                        'rule_ids': [conflict.get('rule1_id'), conflict.get('rule2_id')],
                        'reason': 'Révision manuelle recommandée pour ce type de conflit',
                        'confidence': 0.5,
                        'risk_level': 'high'
                    })
                
                resolutions.append(resolution)
            
            # Trier les résolutions par priorité
            resolutions.sort(key=lambda x: x['priority'], reverse=True)
            
            return resolutions
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des suggestions: {str(e)}")
            return []
    
    def _validate_rule_via_docker(self, rule_type: str, rule_content: str) -> Dict[str, Any]:
        """
        Valide une règle via les services Docker appropriés.
        
        Args:
            rule_type: Type de règle
            rule_content: Contenu de la règle
            
        Returns:
            Résultats de validation
        """
        try:
            # Vérifier la disponibilité des services Docker
            service_status = self._docker_manager.check_service_health(rule_type)
            
            if not service_status.get('available', False):
                return {
                    'status': 'unavailable',
                    'message': f"Service Docker pour {rule_type} non disponible",
                    'details': service_status
                }
            
            # Effectuer la validation
            validation_result = self._docker_manager.validate_rule(rule_type, rule_content)
            
            return {
                'status': 'validated',
                'valid': validation_result.get('valid', True),
                'errors': validation_result.get('errors', []),
                'warnings': validation_result.get('warnings', []),
                'suggestions': validation_result.get('suggestions', []),
                'service_info': service_status
            }
            
        except Exception as e:
            logger.warning(f"Erreur lors de la validation Docker: {str(e)}")
            return {
                'status': 'error',
                'message': f"Erreur de validation: {str(e)}",
                'valid': True  # Assumer valide en cas d'erreur
            }
    
    def _get_existing_rules_by_type(self, rule_type: str) -> List[Dict[str, Any]]:
        """
        Récupère les règles existantes par type.
        
        Args:
            rule_type: Type de règle
            
        Returns:
            Liste des règles existantes
        """
        try:
            rules = self._security_rule_repository.find_by_type(rule_type)
            
            # Convertir les entités en dictionnaires
            return [
                {
                    'id': rule.id,
                    'name': rule.name,
                    'rule_type': rule.rule_type,
                    'content': rule.content,
                    'enabled': rule.enabled,
                    'priority': getattr(rule, 'priority', 0),
                    'description': getattr(rule, 'description', '')
                }
                for rule in rules
            ]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des règles: {str(e)}")
            return []
    
    def _conflict_to_dict(self, conflict: RuleConflict) -> Dict[str, Any]:
        """
        Convertit un objet RuleConflict en dictionnaire.
        
        Args:
            conflict: Objet RuleConflict
            
        Returns:
            Dictionnaire représentant le conflit
        """
        return {
            'conflict_id': conflict.conflict_id,
            'rule1_id': conflict.rule1_id,
            'rule2_id': conflict.rule2_id,
            'conflict_type': conflict.conflict_type,
            'severity': conflict.severity,
            'description': conflict.description,
            'recommendation': conflict.recommendation,
            'type': conflict.conflict_type,  # Alias pour compatibilité
            'id': conflict.conflict_id,  # Alias pour compatibilité
        }
    
    def _build_analysis_statistics(self, conflicts: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Construit les statistiques et le graphe de conflits.
        
        Args:
            conflicts: Liste des conflits
            rules: Liste des règles
            
        Returns:
            Tuple (statistiques, graphe_de_conflits)
        """
        conflict_types = {}
        severity_counts = {}
        rule_conflicts = {}  # Nombre de conflits par règle
        conflict_graph = {}
        
        for conflict in conflicts:
            conflict_type = conflict.get('conflict_type', 'unknown')
            severity = conflict.get('severity', 'medium')
            rule1_id = conflict.get('rule1_id')
            rule2_id = conflict.get('rule2_id')
            
            # Statistiques par type de conflit
            if conflict_type not in conflict_types:
                conflict_types[conflict_type] = 0
            conflict_types[conflict_type] += 1
            
            # Statistiques par sévérité
            if severity not in severity_counts:
                severity_counts[severity] = 0
            severity_counts[severity] += 1
            
            # Compter les conflits par règle
            if rule1_id not in rule_conflicts:
                rule_conflicts[rule1_id] = 0
            if rule2_id not in rule_conflicts:
                rule_conflicts[rule2_id] = 0
            rule_conflicts[rule1_id] += 1
            rule_conflicts[rule2_id] += 1
            
            # Construction du graphe de conflits
            if rule1_id and rule2_id:
                # Ajouter les nœuds au graphe
                if rule1_id not in conflict_graph:
                    conflict_graph[rule1_id] = []
                if rule2_id not in conflict_graph:
                    conflict_graph[rule2_id] = []
                    
                # Ajouter les arêtes
                conflict_graph[rule1_id].append({
                    'rule_id': rule2_id,
                    'conflict_type': conflict_type,
                    'conflict_id': conflict.get('conflict_id'),
                    'severity': severity
                })
                conflict_graph[rule2_id].append({
                    'rule_id': rule1_id,
                    'conflict_type': conflict_type,
                    'conflict_id': conflict.get('conflict_id'),
                    'severity': severity
                })
        
        # Statistiques finales
        statistics = {
            'conflict_types': conflict_types,
            'severity_counts': severity_counts,
            'rules_with_conflicts': len(rule_conflicts),
            'rules_without_conflicts': len(rules) - len(rule_conflicts),
            'total_rules_analyzed': len(rules),
            'max_conflicts_per_rule': max(rule_conflicts.values()) if rule_conflicts else 0,
            'avg_conflicts_per_rule': sum(rule_conflicts.values()) / len(rule_conflicts) if rule_conflicts else 0
        }
        
        return statistics, conflict_graph
    
    def _calculate_health_score(self, conflicts: List[Dict[str, Any]], total_rules: int) -> int:
        """
        Calcule un score de santé pour le jeu de règles (0-100).
        
        Args:
            conflicts: Liste des conflits
            total_rules: Nombre total de règles
            
        Returns:
            Score de santé (0-100)
        """
        if total_rules == 0:
            return 100
        
        # Score de base
        base_score = 100
        
        # Pénalités selon le type et la sévérité des conflits
        severity_penalties = {
            'critical': 15,
            'high': 10,
            'warning': 5,
            'medium': 3,
            'low': 1,
            'info': 0.5
        }
        
        type_multipliers = {
            'shadow': 2.0,
            'redundant': 1.0,
            'correlation': 1.5,
            'generalization': 0.5
        }
        
        total_penalty = 0
        
        for conflict in conflicts:
            severity = conflict.get('severity', 'medium')
            conflict_type = conflict.get('conflict_type', 'unknown')
            
            penalty = severity_penalties.get(severity, 3)
            multiplier = type_multipliers.get(conflict_type, 1.0)
            
            total_penalty += penalty * multiplier
        
        # Calcul du score final
        final_score = max(0, base_score - total_penalty)
        
        # Bonus pour un faible ratio de conflits
        conflict_ratio = len(conflicts) / total_rules
        if conflict_ratio < 0.1:  # Moins de 10% de conflits
            final_score = min(100, final_score + 5)
        
        return int(final_score)
    
    def _enrich_conflicts_with_context(self, conflicts: List[Dict[str, Any]], rule_type: str) -> List[Dict[str, Any]]:
        """
        Enrichit les conflits avec des informations contextuelles.
        
        Args:
            conflicts: Liste des conflits
            rule_type: Type de règle
            
        Returns:
            Liste des conflits enrichis
        """
        enriched = []
        
        for conflict in conflicts:
            enriched_conflict = conflict.copy()
            
            # Ajouter des informations sur l'impact
            enriched_conflict['impact_assessment'] = self._assess_conflict_impact(conflict, rule_type)
            
            # Ajouter un timestamp
            enriched_conflict['detected_at'] = self._get_current_timestamp()
            
            # Ajouter des métriques de confiance
            enriched_conflict['confidence_score'] = self._calculate_conflict_confidence(conflict)
            
            enriched.append(enriched_conflict)
        
        return enriched
    
    def _assess_conflict_impact(self, conflict: Dict[str, Any], rule_type: str) -> Dict[str, Any]:
        """
        Évalue l'impact d'un conflit.
        
        Args:
            conflict: Conflit à évaluer
            rule_type: Type de règle
            
        Returns:
            Évaluation de l'impact
        """
        severity = conflict.get('severity', 'medium')
        conflict_type = conflict.get('conflict_type', 'unknown')
        
        # Impact sur la sécurité
        security_impact = {
            'critical': 'high',
            'high': 'medium',
            'warning': 'low',
            'medium': 'low',
            'low': 'minimal',
            'info': 'none'
        }.get(severity, 'low')
        
        # Impact sur les performances
        performance_impact = {
            'shadow': 'none',  # Règle masquée = pas d'impact
            'redundant': 'low',  # Règles redondantes = traitement inutile
            'correlation': 'medium',  # Peut causer des comportements imprévisibles
            'generalization': 'minimal'  # Impact limité
        }.get(conflict_type, 'low')
        
        return {
            'security_impact': security_impact,
            'performance_impact': performance_impact,
            'operational_impact': 'medium' if severity in ['critical', 'high'] else 'low',
            'urgency': 'high' if severity == 'critical' else 'medium' if severity == 'high' else 'low'
        }
    
    def _calculate_conflict_confidence(self, conflict: Dict[str, Any]) -> float:
        """
        Calcule un score de confiance pour un conflit détecté.
        
        Args:
            conflict: Conflit à évaluer
            
        Returns:
            Score de confiance (0.0 à 1.0)
        """
        base_confidence = 0.8
        
        # Ajuster selon le type de conflit
        type_confidence = {
            'shadow': 0.95,
            'redundant': 0.9,
            'correlation': 0.75,
            'generalization': 0.85
        }
        
        conflict_type = conflict.get('conflict_type', 'unknown')
        return type_confidence.get(conflict_type, base_confidence)
    
    def _calculate_resolution_priority(self, conflict: Dict[str, Any]) -> int:
        """
        Calcule la priorité de résolution d'un conflit (0-100).
        
        Args:
            conflict: Conflit à prioriser
            
        Returns:
            Score de priorité
        """
        severity_scores = {
            'critical': 100,
            'high': 80,
            'warning': 60,
            'medium': 40,
            'low': 20,
            'info': 10
        }
        
        type_multipliers = {
            'shadow': 1.2,
            'redundant': 0.8,
            'correlation': 1.0,
            'generalization': 0.6
        }
        
        severity = conflict.get('severity', 'medium')
        conflict_type = conflict.get('conflict_type', 'unknown')
        
        base_score = severity_scores.get(severity, 40)
        multiplier = type_multipliers.get(conflict_type, 1.0)
        
        return int(base_score * multiplier)
    
    def _estimate_resolution_impact(self, conflict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estime l'impact de la résolution d'un conflit.
        
        Args:
            conflict: Conflit à résoudre
            
        Returns:
            Estimation de l'impact
        """
        return {
            'complexity': 'low' if conflict.get('conflict_type') in ['redundant', 'generalization'] else 'medium',
            'risk': 'low' if conflict.get('severity') in ['info', 'low'] else 'medium',
            'effort': 'minimal' if conflict.get('conflict_type') == 'redundant' else 'moderate',
            'testing_required': conflict.get('severity') in ['critical', 'high']
        }
    
    def _generate_overall_recommendations(self, conflicts: List[Dict[str, Any]], rule_type: str) -> List[str]:
        """
        Génère des recommandations générales basées sur les conflits détectés.
        
        Args:
            conflicts: Liste des conflits
            rule_type: Type de règle
            
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        if not conflicts:
            recommendations.append(f"Aucun conflit détecté. Le jeu de règles {rule_type} semble cohérent.")
            return recommendations
        
        critical_count = sum(1 for c in conflicts if c.get('severity') == 'critical')
        if critical_count > 0:
            recommendations.append(f"Résoudre en priorité les {critical_count} conflits critiques détectés.")
        
        shadow_count = sum(1 for c in conflicts if c.get('conflict_type') == 'shadow')
        if shadow_count > 0:
            recommendations.append(f"Examiner les {shadow_count} règles masquées qui ne s'exécuteront jamais.")
        
        redundant_count = sum(1 for c in conflicts if c.get('conflict_type') == 'redundant')
        if redundant_count > 0:
            recommendations.append(f"Optimiser en fusionnant ou supprimant les {redundant_count} règles redondantes.")
        
        return recommendations
    
    def _generate_ruleset_recommendations(self, conflicts: List[Dict[str, Any]], rule_type: str) -> List[str]:
        """
        Génère des recommandations pour l'ensemble du jeu de règles.
        
        Args:
            conflicts: Liste des conflits
            rule_type: Type de règle
            
        Returns:
            Liste de recommandations
        """
        recommendations = []
        
        if len(conflicts) > 10:
            recommendations.append("Le nombre élevé de conflits suggère une révision complète du jeu de règles.")
        
        recommendations.append(f"Considérer l'utilisation d'un outil de validation {rule_type} automatisé.")
        recommendations.append("Implémenter un processus de révision par les pairs pour les nouvelles règles.")
        
        return recommendations
    
    def _generate_optimization_suggestions(self, rules: List[Dict[str, Any]], conflicts: List[Dict[str, Any]]) -> List[str]:
        """
        Génère des suggestions d'optimisation.
        
        Args:
            rules: Liste des règles
            conflicts: Liste des conflits
            
        Returns:
            Liste de suggestions d'optimisation
        """
        suggestions = []
        
        conflict_ratio = len(conflicts) / len(rules) if rules else 0
        
        if conflict_ratio > 0.2:
            suggestions.append("Taux de conflits élevé - considérer une réorganisation des règles.")
        
        if len(rules) > 100:
            suggestions.append("Jeu de règles volumineux - envisager une segmentation par priorité.")
        
        return suggestions
    
    def _get_current_timestamp(self) -> str:
        """Retourne le timestamp actuel en format ISO."""
        from datetime import datetime
        return datetime.now().isoformat()


# Classes utilitaires pour l'intégration Docker
class DockerServiceManager:
    """
    Gestionnaire pour les services Docker de validation.
    """
    
    def __init__(self):
        """Initialise le gestionnaire de services Docker."""
        from django.conf import settings
        
        self.services = {
            'firewall': getattr(settings, 'TRAFFIC_CONTROL_API_URL', 'http://nms-traffic-control:8003'),
            'ids': getattr(settings, 'SURICATA_API_URL', 'http://nms-suricata:8068'),
            'suricata': getattr(settings, 'SURICATA_API_URL', 'http://nms-suricata:8068'),
            'access_control': getattr(settings, 'FAIL2BAN_API_URL', 'http://nms-fail2ban:5001'),
            'fail2ban': getattr(settings, 'FAIL2BAN_API_URL', 'http://nms-fail2ban:5001'),
        }
        
        self._session = None
    
    def get_session(self):
        """Retourne une session requests réutilisable."""
        if not self._session:
            import requests
            self._session = requests.Session()
            self._session.timeout = 30
        return self._session
    
    def check_service_health(self, rule_type: str) -> Dict[str, Any]:
        """
        Vérifie la santé d'un service Docker.
        
        Args:
            rule_type: Type de règle/service
            
        Returns:
            Statut de santé du service
        """
        service_url = self.services.get(rule_type.lower())
        if not service_url:
            return {'available': False, 'reason': 'Service non configuré'}
        
        try:
            session = self.get_session()
            response = session.get(f"{service_url}/health", timeout=10)
            
            return {
                'available': response.status_code == 200,
                'status_code': response.status_code,
                'service_url': service_url,
                'response_time': response.elapsed.total_seconds()
            }
            
        except Exception as e:
            return {
                'available': False,
                'reason': str(e),
                'service_url': service_url
            }
    
    def validate_rule(self, rule_type: str, rule_content: str) -> Dict[str, Any]:
        """
        Valide une règle via le service Docker approprié.
        
        Args:
            rule_type: Type de règle
            rule_content: Contenu de la règle
            
        Returns:
            Résultat de validation
        """
        service_url = self.services.get(rule_type.lower())
        if not service_url:
            return {'valid': True, 'warning': 'Service de validation non disponible'}
        
        try:
            session = self.get_session()
            
            # Endpoint de validation selon le type
            endpoint_map = {
                'firewall': '/validate/firewall',
                'ids': '/validate/rule',
                'suricata': '/validate/rule',
                'access_control': '/validate/access_rule',
                'fail2ban': '/validate/rule'
            }
            
            endpoint = endpoint_map.get(rule_type.lower(), '/validate')
            
            response = session.post(
                f"{service_url}{endpoint}",
                json={'rule': rule_content},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'valid': False,
                    'error': f"Erreur de validation HTTP {response.status_code}"
                }
                
        except Exception as e:
            logger.warning(f"Erreur lors de la validation Docker: {str(e)}")
            return {
                'valid': True,
                'warning': f"Validation Docker échouée: {str(e)}"
            }