"""
Tests unitaires pour les services du domaine du module security_management.

Ce fichier contient les tests unitaires pour les services du domaine
qui implémentent la logique métier du module security_management.
"""

import unittest
from unittest.mock import Mock, patch
import re
from datetime import datetime

from ..domain.entities import (
    SecurityRule, EntityId, RuleType, ActionType, SeverityLevel
)
from ..domain.services import (
    rule_validator_factory, RuleConflictDetector,
    SuricataRuleValidationStrategy, FirewallRuleValidationStrategy
)


class SuricataRuleValidationStrategyTests(unittest.TestCase):
    """Tests pour la stratégie de validation des règles Suricata."""
    
    def setUp(self):
        """Initialise les objets pour les tests."""
        self.validator = SuricataRuleValidationStrategy()
        
        # Créer une règle Suricata valide
        self.valid_rule = SecurityRule(
            id=EntityId("1"),
            name="Test Suricata Rule",
            description="A test rule",
            rule_type=RuleType.SURICATA,
            content="alert tcp any any -> $HOME_NET any (msg:\"Test rule\"; sid:1000001; rev:1;)",
            source_ip=None,
            destination_ip=None,
            action=ActionType.ALERT,
            enabled=True
        )
    
    def test_validate_valid_rule(self):
        """Teste la validation d'une règle Suricata valide."""
        is_valid, errors = self.validator.validate(self.valid_rule)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_invalid_rule_type(self):
        """Teste la validation d'une règle avec un type incorrect."""
        rule = SecurityRule(
            id=EntityId("1"),
            name="Invalid Rule Type",
            description="A rule with invalid type",
            rule_type=RuleType.FIREWALL,  # Type incorrect
            content="alert tcp any any -> $HOME_NET any (msg:\"Test rule\"; sid:1000001; rev:1;)",
            source_ip=None,
            destination_ip=None,
            action=ActionType.ALERT,
            enabled=True
        )
        
        is_valid, errors = self.validator.validate(rule)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("Type de règle incorrect", errors[0])
    
    def test_validate_missing_content(self):
        """Teste la validation d'une règle sans contenu."""
        rule = SecurityRule(
            id=EntityId("1"),
            name="Missing Content",
            description="A rule without content",
            rule_type=RuleType.SURICATA,
            content=None,  # Contenu manquant
            source_ip=None,
            destination_ip=None,
            action=ActionType.ALERT,
            enabled=True
        )
        
        is_valid, errors = self.validator.validate(rule)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("Le contenu de la règle est obligatoire", errors[0])
    
    def test_validate_missing_msg(self):
        """Teste la validation d'une règle sans message."""
        rule = SecurityRule(
            id=EntityId("1"),
            name="Missing Message",
            description="A rule without msg option",
            rule_type=RuleType.SURICATA,
            content="alert tcp any any -> $HOME_NET any (sid:1000001; rev:1;)",  # msg manquant
            source_ip=None,
            destination_ip=None,
            action=ActionType.ALERT,
            enabled=True
        )
        
        is_valid, errors = self.validator.validate(rule)
        self.assertFalse(is_valid)
        self.assertIn("L'option 'msg' est obligatoire", errors[0])
    
    def test_validate_missing_sid(self):
        """Teste la validation d'une règle sans SID."""
        rule = SecurityRule(
            id=EntityId("1"),
            name="Missing SID",
            description="A rule without sid option",
            rule_type=RuleType.SURICATA,
            content="alert tcp any any -> $HOME_NET any (msg:\"Test rule\"; rev:1;)",  # sid manquant
            source_ip=None,
            destination_ip=None,
            action=ActionType.ALERT,
            enabled=True
        )
        
        is_valid, errors = self.validator.validate(rule)
        self.assertFalse(is_valid)
        self.assertIn("L'option 'sid' est obligatoire", errors[0])


class FirewallRuleValidationStrategyTests(unittest.TestCase):
    """Tests pour la stratégie de validation des règles de pare-feu."""
    
    def setUp(self):
        """Initialise les objets pour les tests."""
        self.validator = FirewallRuleValidationStrategy()
        
        # Créer une règle de pare-feu valide
        self.valid_rule = SecurityRule(
            id=EntityId("2"),
            name="Test Firewall Rule",
            description="A test firewall rule",
            rule_type=RuleType.FIREWALL,
            content=None,
            source_ip="192.168.1.100",
            destination_ip=None,
            action=ActionType.BLOCK,
            enabled=True
        )
    
    def test_validate_valid_rule(self):
        """Teste la validation d'une règle de pare-feu valide."""
        is_valid, errors = self.validator.validate(self.valid_rule)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_invalid_rule_type(self):
        """Teste la validation d'une règle avec un type incorrect."""
        rule = SecurityRule(
            id=EntityId("2"),
            name="Invalid Rule Type",
            description="A rule with invalid type",
            rule_type=RuleType.SURICATA,  # Type incorrect
            content=None,
            source_ip="192.168.1.100",
            destination_ip=None,
            action=ActionType.BLOCK,
            enabled=True
        )
        
        is_valid, errors = self.validator.validate(rule)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 1)
        self.assertIn("Type de règle incorrect", errors[0])
    
    def test_validate_missing_action(self):
        """Teste la validation d'une règle sans action."""
        rule = SecurityRule(
            id=EntityId("2"),
            name="Missing Action",
            description="A rule without action",
            rule_type=RuleType.FIREWALL,
            content=None,
            source_ip="192.168.1.100",
            destination_ip=None,
            action=None,  # Action manquante
            enabled=True
        )
        
        is_valid, errors = self.validator.validate(rule)
        self.assertFalse(is_valid)
        self.assertIn("L'action est obligatoire", errors[0])
    
    def test_validate_missing_ip_addresses(self):
        """Teste la validation d'une règle sans adresses IP."""
        rule = SecurityRule(
            id=EntityId("2"),
            name="Missing IP Addresses",
            description="A rule without IP addresses",
            rule_type=RuleType.FIREWALL,
            content=None,
            source_ip=None,  # Source IP manquante
            destination_ip=None,  # Destination IP manquante
            action=ActionType.BLOCK,
            enabled=True
        )
        
        is_valid, errors = self.validator.validate(rule)
        self.assertFalse(is_valid)
        self.assertIn("Au moins une adresse IP doit être spécifiée", errors[0])


class RuleValidatorFactoryTests(unittest.TestCase):
    """Tests pour la fabrique de validateurs de règles."""
    
    def test_get_suricata_validator(self):
        """Teste l'obtention d'un validateur pour les règles Suricata."""
        validator = rule_validator_factory(RuleType.SURICATA)
        self.assertIsInstance(validator, SuricataRuleValidationStrategy)
    
    def test_get_firewall_validator(self):
        """Teste l'obtention d'un validateur pour les règles de pare-feu."""
        validator = rule_validator_factory(RuleType.FIREWALL)
        self.assertIsInstance(validator, FirewallRuleValidationStrategy)
    
    def test_unsupported_rule_type(self):
        """Teste l'obtention d'un validateur pour un type de règle non supporté."""
        with self.assertRaises(ValueError):
            rule_validator_factory("unsupported_type")


class RuleConflictDetectorTests(unittest.TestCase):
    """Tests pour le détecteur de conflits entre règles."""
    
    def setUp(self):
        """Initialise les objets pour les tests."""
        self.detector = RuleConflictDetector()
        
        # Créer des règles de pare-feu pour les tests
        self.rule1 = SecurityRule(
            id=EntityId("1"),
            name="Block Traffic",
            description="Block traffic from source",
            rule_type=RuleType.FIREWALL,
            content=None,
            source_ip="192.168.1.100",
            destination_ip=None,
            action=ActionType.BLOCK,
            enabled=True
        )
        
        self.rule2 = SecurityRule(
            id=EntityId("2"),
            name="Allow Traffic",
            description="Allow traffic from source",
            rule_type=RuleType.FIREWALL,
            content=None,
            source_ip="192.168.1.100",  # Même adresse IP que rule1
            destination_ip=None,
            action=ActionType.ALLOW,  # Action opposée à rule1
            enabled=True
        )
        
        self.rule3 = SecurityRule(
            id=EntityId("3"),
            name="Block Traffic",
            description="Block traffic from another source",
            rule_type=RuleType.FIREWALL,
            content=None,
            source_ip="192.168.1.200",  # Adresse IP différente
            destination_ip=None,
            action=ActionType.BLOCK,
            enabled=True
        )
    
    def test_detect_action_conflict(self):
        """Teste la détection de conflits d'action."""
        conflicts = self.detector.detect_conflicts(self.rule1, [self.rule2])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["conflict_type"], "action_conflict")
    
    def test_no_conflict_different_ips(self):
        """Teste qu'il n'y a pas de conflit avec des adresses IP différentes."""
        conflicts = self.detector.detect_conflicts(self.rule1, [self.rule3])
        self.assertEqual(len(conflicts), 0)
    
    def test_no_conflict_same_action(self):
        """Teste qu'il n'y a pas de conflit avec la même action."""
        # Créer une règle avec la même action mais une adresse IP différente
        rule4 = SecurityRule(
            id=EntityId("4"),
            name="Block Traffic Too",
            description="Block traffic from yet another source",
            rule_type=RuleType.FIREWALL,
            content=None,
            source_ip="192.168.1.300",
            destination_ip=None,
            action=ActionType.BLOCK,  # Même action que rule1
            enabled=True
        )
        
        conflicts = self.detector.detect_conflicts(self.rule1, [rule4])
        self.assertEqual(len(conflicts), 0)
    
    def test_extract_sid_from_suricata_rule(self):
        """Teste l'extraction du SID d'une règle Suricata."""
        rule_content = "alert tcp any any -> $HOME_NET any (msg:\"Test rule\"; sid:1000001; rev:1;)"
        sid = self.detector._extract_sid(rule_content)
        self.assertEqual(sid, "1000001")
    
    def test_extract_sid_missing(self):
        """Teste l'extraction du SID lorsqu'il est manquant."""
        rule_content = "alert tcp any any -> $HOME_NET any (msg:\"Test rule\"; rev:1;)"
        sid = self.detector._extract_sid(rule_content)
        self.assertIsNone(sid)


if __name__ == '__main__':
    unittest.main() 