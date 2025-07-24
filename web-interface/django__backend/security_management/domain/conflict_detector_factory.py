"""
Factory pour créer des détecteurs de conflits de règles de sécurité.

Ce module implémente le pattern Factory pour créer les détecteurs
appropriés selon le type de règle de sécurité, avec intégration Docker.
"""

from typing import Dict, Any, List, Optional
import logging

from .interfaces import ConflictDetector, RuleConflict
from .conflict_detector import (
    FirewallRuleConflictDetector,
    IDSRuleConflictDetector, 
    AccessControlRuleConflictDetector
)

logger = logging.getLogger(__name__)


class ConflictDetectorFactory:
    """
    Factory pour créer des détecteurs de conflits selon le type de règle.
    """
    
    def __init__(self):
        """Initialise la factory avec les détecteurs disponibles."""
        self._detectors = {
            'firewall': FirewallRuleConflictDetector,
            'ids': IDSRuleConflictDetector,
            'access_control': AccessControlRuleConflictDetector,
            'suricata': IDSRuleConflictDetector,  # Alias pour IDS
            'fail2ban': AccessControlRuleConflictDetector,  # Utilise access_control pour fail2ban
        }
    
    def create_detector(self, rule_type: str) -> ConflictDetector:
        """
        Crée un détecteur de conflits approprié pour le type de règle.
        
        Args:
            rule_type: Type de règle (firewall, ids, access_control, suricata, fail2ban)
            
        Returns:
            Détecteur de conflits approprié
            
        Raises:
            ValueError: Si le type de règle n'est pas pris en charge
        """
        rule_type = rule_type.lower()
        
        if rule_type not in self._detectors:
            raise ValueError(f"Type de règle non pris en charge: {rule_type}")
        
        detector_class = self._detectors[rule_type]
        return detector_class()
    
    def detect_conflicts_by_type(self, rule_data: Dict[str, Any], 
                                existing_rules: List[Dict[str, Any]], 
                                rule_type: str) -> List[Dict[str, Any]]:
        """
        Détecte les conflits pour un type de règle spécifique.
        
        Args:
            rule_data: Données de la nouvelle règle
            existing_rules: Liste des règles existantes
            rule_type: Type de règle
            
        Returns:
            Liste des conflits détectés au format dictionnaire
        """
        try:
            detector = self.create_detector(rule_type)
            conflicts = detector.detect_conflicts(rule_data, existing_rules)
            
            # Convertir les objets RuleConflict en dictionnaires
            return [self._conflict_to_dict(conflict) for conflict in conflicts]
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection de conflits pour {rule_type}: {str(e)}")
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
    
    def get_supported_rule_types(self) -> List[str]:
        """
        Retourne la liste des types de règles pris en charge.
        
        Returns:
            Liste des types de règles supportés
        """
        return list(self._detectors.keys())


# Instance globale de la factory
conflict_detector_factory = ConflictDetectorFactory()