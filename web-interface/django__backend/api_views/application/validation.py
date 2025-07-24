"""
Framework de validation pour les vues API.

Ce module fournit un framework de validation standardisé pour les vues API,
permettant de valider les entrées de manière cohérente et réutilisable.
"""

import re
from typing import Dict, Any, List, Callable, Optional, Union, Type
from dataclasses import dataclass
from datetime import datetime
from ipaddress import IPv4Address, IPv6Address, AddressValueError
import logging
import uuid

from .base_use_case import ValidationResult, ValidationError, BaseValidator

logger = logging.getLogger(__name__)


@dataclass
class FieldValidationRule:
    """Règle de validation pour un champ."""
    
    field: str
    validator: Callable[[Any], bool]
    error_message: str
    error_code: str = "invalid"
    condition: Optional[Callable[[Dict[str, Any]], bool]] = None
    
    def applies_to(self, data: Dict[str, Any]) -> bool:
        """
        Vérifie si cette règle s'applique aux données.
        
        Args:
            data: Données à vérifier
            
        Returns:
            True si la règle s'applique
        """
        if self.condition is None:
            return True
        
        return self.condition(data)


class StandardValidator(BaseValidator):
    """
    Validateur standard pour les données d'entrée des vues API.
    
    Ce validateur permet de définir des règles de validation réutilisables
    et de les appliquer de manière cohérente.
    """
    
    def __init__(self, rules: List[FieldValidationRule] = None):
        """
        Initialise le validateur avec des règles de validation.
        
        Args:
            rules: Liste de règles de validation
        """
        self.rules = rules or []
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        Valide les données d'entrée selon les règles définies.
        
        Args:
            data: Données à valider
            
        Returns:
            Résultat de la validation
        """
        errors = []
        
        # Appliquer les règles de validation
        for rule in self.rules:
            if not rule.applies_to(data):
                continue
                
            field_value = data.get(rule.field)
            
            # Vérifier si le champ est requis et absent
            if field_value is None:
                continue
                
            # Appliquer la validation
            if not rule.validator(field_value):
                errors.append(ValidationError(
                    field=rule.field,
                    message=rule.error_message,
                    code=rule.error_code
                ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def add_rule(self, rule: FieldValidationRule) -> None:
        """
        Ajoute une règle de validation.
        
        Args:
            rule: Règle de validation à ajouter
        """
        self.rules.append(rule)
    
    def add_rules(self, rules: List[FieldValidationRule]) -> None:
        """
        Ajoute plusieurs règles de validation.
        
        Args:
            rules: Règles de validation à ajouter
        """
        self.rules.extend(rules)
    
    @classmethod
    def with_rules(cls, rules: List[FieldValidationRule]) -> 'StandardValidator':
        """
        Crée un validateur avec les règles spécifiées.
        
        Args:
            rules: Règles de validation
            
        Returns:
            Validateur initialisé
        """
        return cls(rules)


# Validateurs prédéfinis pour les types communs
def is_string(value: Any) -> bool:
    """Vérifie si la valeur est une chaîne de caractères."""
    return isinstance(value, str)

def is_integer(value: Any) -> bool:
    """Vérifie si la valeur est un entier."""
    return isinstance(value, int) and not isinstance(value, bool)

def is_boolean(value: Any) -> bool:
    """Vérifie si la valeur est un booléen."""
    return isinstance(value, bool)

def is_list(value: Any) -> bool:
    """Vérifie si la valeur est une liste."""
    return isinstance(value, list)

def is_dict(value: Any) -> bool:
    """Vérifie si la valeur est un dictionnaire."""
    return isinstance(value, dict)

def is_email(value: Any) -> bool:
    """Vérifie si la valeur est une adresse email valide."""
    if not isinstance(value, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, value))

def is_url(value: Any) -> bool:
    """Vérifie si la valeur est une URL valide."""
    if not isinstance(value, str):
        return False
    
    pattern = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'
    return bool(re.match(pattern, value))

def is_ip_address(value: Any) -> bool:
    """Vérifie si la valeur est une adresse IP valide."""
    if not isinstance(value, str):
        return False
    
    try:
        IPv4Address(value)
        return True
    except AddressValueError:
        try:
            IPv6Address(value)
            return True
        except AddressValueError:
            return False

def is_date(value: Any) -> bool:
    """Vérifie si la valeur est une date valide."""
    if isinstance(value, datetime):
        return True
    
    if not isinstance(value, str):
        return False
    
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False

def min_length(min_len: int) -> Callable[[Any], bool]:
    """
    Crée un validateur de longueur minimale.
    
    Args:
        min_len: Longueur minimale
        
    Returns:
        Fonction de validation
    """
    def validator(value: Any) -> bool:
        if value is None:
            return False
        
        if hasattr(value, '__len__'):
            return len(value) >= min_len
        
        return False
    
    return validator

def max_length(max_len: int) -> Callable[[Any], bool]:
    """
    Crée un validateur de longueur maximale.
    
    Args:
        max_len: Longueur maximale
        
    Returns:
        Fonction de validation
    """
    def validator(value: Any) -> bool:
        if value is None:
            return True
        
        if hasattr(value, '__len__'):
            return len(value) <= max_len
        
        return True
    
    return validator

def min_value(min_val: Union[int, float]) -> Callable[[Any], bool]:
    """
    Crée un validateur de valeur minimale.
    
    Args:
        min_val: Valeur minimale
        
    Returns:
        Fonction de validation
    """
    def validator(value: Any) -> bool:
        if isinstance(value, (int, float)):
            return value >= min_val
        
        return False
    
    return validator

def max_value(max_val: Union[int, float]) -> Callable[[Any], bool]:
    """
    Crée un validateur de valeur maximale.
    
    Args:
        max_val: Valeur maximale
        
    Returns:
        Fonction de validation
    """
    def validator(value: Any) -> bool:
        if isinstance(value, (int, float)):
            return value <= max_val
        
        return False
    
    return validator

def pattern(regex: str) -> Callable[[Any], bool]:
    """
    Crée un validateur de motif regex.
    
    Args:
        regex: Expression régulière
        
    Returns:
        Fonction de validation
    """
    compiled_regex = re.compile(regex)
    
    def validator(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        
        return bool(compiled_regex.match(value))
    
    return validator

def one_of(allowed_values: List[Any]) -> Callable[[Any], bool]:
    """
    Crée un validateur de valeurs autorisées.
    
    Args:
        allowed_values: Liste des valeurs autorisées
        
    Returns:
        Fonction de validation
    """
    def validator(value: Any) -> bool:
        return value in allowed_values
    
    return validator

def is_instance_of(cls: Type) -> Callable[[Any], bool]:
    """
    Crée un validateur de type.
    
    Args:
        cls: Type attendu
        
    Returns:
        Fonction de validation
    """
    def validator(value: Any) -> bool:
        return isinstance(value, cls)
    
    return validator

def required(field: str, message: str = "Ce champ est requis") -> FieldValidationRule:
    """Crée une règle de validation pour un champ requis."""
    return FieldValidationRule(
        field=field,
        validator=lambda x: x is not None and x != "",
        error_message=message,
        error_code="required"
    )

def date_format(field: str, format_str: str = "%Y-%m-%d", 
               message: str = "Format de date invalide") -> FieldValidationRule:
    """Crée une règle de validation pour un format de date."""
    def validate_date(value):
        if not isinstance(value, str):
            return False
        try:
            datetime.strptime(value, format_str)
            return True
        except ValueError:
            return False
    
    return FieldValidationRule(
        field=field,
        validator=validate_date,
        error_message=message,
        error_code="date_format"
    )

def conditional(condition: Callable[[Dict[str, Any]], bool], 
               rule: FieldValidationRule) -> FieldValidationRule:
    """
    Crée une règle de validation conditionnelle.
    
    La règle ne sera appliquée que si la condition est remplie.
    
    Args:
        condition: Fonction qui prend les données et renvoie un booléen
        rule: Règle de validation à appliquer conditionnellement
        
    Returns:
        Règle de validation conditionnelle
    """
    rule.condition = condition
    return rule

class ValidationBuilder:
    """
    Constructeur de validateur fluent.
    
    Cette classe permet de construire un validateur de manière fluide.
    """
    
    def __init__(self):
        self.rules = []
    
    def add_rule(self, rule: FieldValidationRule) -> 'ValidationBuilder':
        """Ajoute une règle de validation."""
        self.rules.append(rule)
        return self
    
    def required(self, field: str, message: str = "Ce champ est requis") -> 'ValidationBuilder':
        """Ajoute une règle de validation pour un champ requis."""
        return self.add_rule(required(field, message))
    
    def min_length(self, field: str, min_len: int, message: str = None) -> 'ValidationBuilder':
        """Ajoute une règle de validation pour une longueur minimale."""
        return self.add_rule(min_length(min_len))
    
    def max_length(self, field: str, max_len: int, message: str = None) -> 'ValidationBuilder':
        """Ajoute une règle de validation pour une longueur maximale."""
        return self.add_rule(max_length(max_len))
    
    def pattern(self, field: str, regex: str, message: str = "Format invalide") -> 'ValidationBuilder':
        """Ajoute une règle de validation pour un motif regex."""
        return self.add_rule(pattern(regex))
    
    def email(self, field: str, message: str = "Adresse email invalide") -> 'ValidationBuilder':
        """Ajoute une règle de validation pour une adresse email."""
        return self.add_rule(email(field))
    
    def number_range(self, field: str, min_val: float = None, max_val: float = None, 
                    message: str = None) -> 'ValidationBuilder':
        """Ajoute une règle de validation pour une plage numérique."""
        return self.add_rule(number_range(field, min_val, max_val, message))
    
    def date_format(self, field: str, format_str: str = "%Y-%m-%d", 
                   message: str = "Format de date invalide") -> 'ValidationBuilder':
        """Ajoute une règle de validation pour un format de date."""
        return self.add_rule(date_format(field, format_str, message))
    
    def one_of(self, field: str, choices: List[Any], 
              message: str = "Valeur non autorisée") -> 'ValidationBuilder':
        """Ajoute une règle de validation pour une liste de valeurs autorisées."""
        return self.add_rule(one_of(choices))
    
    def ip_address(self, field: str, ipv4_only: bool = False, ipv6_only: bool = False,
                  message: str = "Adresse IP invalide") -> 'ValidationBuilder':
        """Ajoute une règle de validation pour une adresse IP."""
        return self.add_rule(ip_address(field, ipv4_only, ipv6_only, message))
    
    def conditional(self, condition: Callable[[Dict[str, Any]], bool], 
                   rule_builder: Callable[['ValidationBuilder'], 'ValidationBuilder']) -> 'ValidationBuilder':
        """Ajoute une ou plusieurs règles de validation conditionnelles."""
        # Créer un nouveau builder pour les règles conditionnelles
        conditional_builder = ValidationBuilder()
        
        # Appliquer le builder de règle conditionnelle
        rule_builder(conditional_builder)
        
        # Ajouter la condition à toutes les règles
        for rule in conditional_builder.rules:
            rule.condition = condition
            self.rules.append(rule)
        
        return self
    
    def build(self) -> StandardValidator:
        """Construit le validateur."""
        return StandardValidator(self.rules)


class ValidationMixin:
    """
    Mixin pour intégrer facilement la validation avancée dans les sérialiseurs.
    
    Ce mixin permet d'ajouter des capacités de validation avancée aux sérialiseurs
    DRF en utilisant le framework de validation standardisé.
    """
    
    def get_validation_rules(self) -> List[FieldValidationRule]:
        """
        Retourne les règles de validation spécifiques à ce sérialiseur.
        
        Returns:
            Liste des règles de validation
        """
        return getattr(self, 'validation_rules', [])
    
    def get_custom_validator(self) -> Optional[StandardValidator]:
        """
        Retourne un validateur personnalisé pour ce sérialiseur.
        
        Returns:
            Validateur personnalisé ou None
        """
        rules = self.get_validation_rules()
        if not rules:
            return None
        
        return StandardValidator(rules)
    
    def validate_with_framework(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les données en utilisant le framework de validation.
        
        Args:
            data: Données à valider
            
        Returns:
            Données validées
            
        Raises:
            ValidationError: Si la validation échoue
        """
        validator = self.get_custom_validator()
        if not validator:
            return data
        
        result = validator.validate(data)
        if not result.is_valid:
            # Convertir les erreurs du framework en erreurs DRF
            error_dict = {}
            for error in result.errors:
                if error.field in error_dict:
                    if isinstance(error_dict[error.field], list):
                        error_dict[error.field].append(error.message)
                    else:
                        error_dict[error.field] = [error_dict[error.field], error.message]
                else:
                    error_dict[error.field] = error.message
            
            from rest_framework.exceptions import ValidationError as DRFValidationError
            raise DRFValidationError(error_dict)
        
        return data
    
    def apply_business_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Applique la validation métier spécifique.
        
        Args:
            data: Données à valider
            
        Returns:
            Données validées
            
        Raises:
            ValidationError: Si la validation métier échoue
        """
        # Méthode de base - peut être overridée dans les sérialiseurs concrets
        return data
    
    def validate_user_context(self, data: Dict[str, Any], user) -> Dict[str, Any]:
        """
        Valide les données dans le contexte utilisateur.
        
        Args:
            data: Données à valider
            user: Utilisateur de la requête
            
        Returns:
            Données validées
            
        Raises:
            ValidationError: Si la validation contextuelle échoue
        """
        # Validation de base - peut être overridée dans les sérialiseurs concrets
        return data


class APIValidationRules:
    """
    Collection de règles de validation prédéfinies pour les API.
    
    Cette classe fournit des règles de validation communes pour les différents
    types de données utilisés dans les API du système.
    """
    
    @staticmethod
    def dashboard_type_rule() -> FieldValidationRule:
        """Règle de validation pour les types de dashboard."""
        valid_types = [
            'system-overview', 'network-status', 'security-dashboard',
            'monitoring-dashboard', 'user-dashboard', 'custom'
        ]
        
        return FieldValidationRule(
            field='dashboard_type',
            validator=one_of(valid_types),
            error_message=f"Type de dashboard invalide. Types autorisés: {', '.join(valid_types)}",
            error_code='invalid_dashboard_type'
        )
    
    @staticmethod
    def widget_type_rule() -> FieldValidationRule:
        """Règle de validation pour les types de widget."""
        valid_types = [
            'alerts', 'devices', 'metrics', 'charts', 
            'topology', 'security', 'custom'
        ]
        
        return FieldValidationRule(
            field='type',
            validator=one_of(valid_types),
            error_message=f"Type de widget invalide. Types autorisés: {', '.join(valid_types)}",
            error_code='invalid_widget_type'
        )
    
    @staticmethod
    def time_range_rule() -> FieldValidationRule:
        """Règle de validation pour les plages de temps."""
        valid_ranges = ['1h', '24h', '7d', '30d', '90d', 'custom']
        
        return FieldValidationRule(
            field='time_range',
            validator=one_of(valid_ranges),
            error_message=f"Plage de temps invalide. Plages autorisées: {', '.join(valid_ranges)}",
            error_code='invalid_time_range'
        )
    
    @staticmethod
    def network_id_rule() -> FieldValidationRule:
        """Règle de validation pour les IDs de réseau."""
        return FieldValidationRule(
            field='network_id',
            validator=lambda x: isinstance(x, str) and len(x.strip()) > 0,
            error_message="ID de réseau invalide",
            error_code='invalid_network_id'
        )
    
    @staticmethod
    def device_type_rule() -> FieldValidationRule:
        """Règle de validation pour les types d'équipement."""
        valid_types = ['router', 'switch', 'firewall', 'server', 'other']
        
        return FieldValidationRule(
            field='device_type',
            validator=one_of(valid_types),
            error_message=f"Type d'équipement invalide. Types autorisés: {', '.join(valid_types)}",
            error_code='invalid_device_type'
        )
    
    @staticmethod
    def ip_address_rule(field: str = 'ip_address') -> FieldValidationRule:
        """Règle de validation pour les adresses IP."""
        return FieldValidationRule(
            field=field,
            validator=is_ip_address,
            error_message="Adresse IP invalide",
            error_code='invalid_ip_address'
        )
    
    @staticmethod
    def port_range_rule(field: str = 'port') -> FieldValidationRule:
        """Règle de validation pour les numéros de port."""
        return FieldValidationRule(
            field=field,
            validator=lambda x: isinstance(x, int) and 1 <= x <= 65535,
            error_message="Numéro de port invalide (doit être entre 1 et 65535)",
            error_code='invalid_port'
        )
    
    @staticmethod
    def severity_rule(field: str = 'severity') -> FieldValidationRule:
        """Règle de validation pour les niveaux de sévérité."""
        valid_severities = ['critical', 'warning', 'info', 'debug']
        
        return FieldValidationRule(
            field=field,
            validator=one_of(valid_severities),
            error_message=f"Niveau de sévérité invalide. Niveaux autorisés: {', '.join(valid_severities)}",
            error_code='invalid_severity'
        )
    
    @staticmethod
    def discovery_status_rule() -> FieldValidationRule:
        """Règle de validation pour les statuts de découverte."""
        valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
        
        return FieldValidationRule(
            field='status',
            validator=one_of(valid_statuses),
            error_message=f"Statut de découverte invalide. Statuts autorisés: {', '.join(valid_statuses)}",
            error_code='invalid_discovery_status'
        )


class BusinessRuleValidator:
    """
    Validateur pour les règles métier complexes.
    
    Cette classe permet de définir et valider des règles métier qui impliquent
    plusieurs champs ou nécessitent des vérifications complexes.
    """
    
    @staticmethod
    def validate_dashboard_consistency(data: Dict[str, Any]) -> ValidationResult:
        """
        Valide la cohérence d'une configuration de dashboard.
        
        Args:
            data: Données du dashboard à valider
            
        Returns:
            Résultat de la validation
        """
        errors = []
        
        # Règle: un dashboard de type 'custom' doit avoir des widgets
        if data.get('dashboard_type') == 'custom':
            widgets = data.get('widgets', [])
            if not widgets:
                errors.append(ValidationError(
                    field='widgets',
                    message="Un dashboard personnalisé doit contenir au moins un widget",
                    code='custom_dashboard_no_widgets'
                ))
        
        # Règle: un layout 'fixed' nécessite des positions pour tous les widgets
        if data.get('layout') == 'fixed':
            widgets = data.get('widgets', [])
            for i, widget in enumerate(widgets):
                if not widget.get('position'):
                    errors.append(ValidationError(
                        field=f'widgets[{i}].position',
                        message="Position requise pour layout 'fixed'",
                        code='fixed_layout_missing_position'
                    ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    @staticmethod
    def validate_topology_discovery_params(data: Dict[str, Any]) -> ValidationResult:
        """
        Valide les paramètres de découverte de topologie.
        
        Args:
            data: Paramètres de découverte à valider
            
        Returns:
            Résultat de la validation
        """
        errors = []
        
        # Règle: si scan_type est 'subnet', un subnet doit être spécifié
        if data.get('scan_type') == 'subnet':
            if not data.get('subnet'):
                errors.append(ValidationError(
                    field='subnet',
                    message="Subnet requis pour scan_type='subnet'",
                    code='subnet_scan_missing_subnet'
                ))
        
        # Règle: les plages de ports doivent être valides
        port_range = data.get('port_range')
        if port_range:
            if isinstance(port_range, str) and '-' in port_range:
                try:
                    start, end = map(int, port_range.split('-'))
                    if start > end or start < 1 or end > 65535:
                        errors.append(ValidationError(
                            field='port_range',
                            message="Plage de ports invalide",
                            code='invalid_port_range'
                        ))
                except ValueError:
                    errors.append(ValidationError(
                        field='port_range',
                        message="Format de plage de ports invalide (attendu: 'start-end')",
                        code='invalid_port_range_format'
                    ))
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )


class ValidationRules:
    """Règles de validation pour les cas d'utilisation."""
    
    def __init__(self, rules: Dict[str, Dict[str, Any]]):
        """
        Initialise les règles de validation.
        
        Args:
            rules: Dictionnaire de règles de validation, où les clés sont les noms des champs
                 et les valeurs sont des dictionnaires de règles.
        """
        self.rules = rules
        
    def validate(self, data: Dict[str, Any]) -> None:
        """
        Valide les données selon les règles définies.
        
        Args:
            data: Données à valider
            
        Raises:
            ValidationError: Si les données ne sont pas valides
        """
        errors = []
        
        # Appliquer les valeurs par défaut
        self._apply_defaults(data)
        
        # Valider chaque champ
        for field, rules in self.rules.items():
            value = data.get(field)
            
            # Vérifier si le champ est requis
            if rules.get('required', False) and value is None:
                errors.append(ValidationError(field, "Ce champ est requis"))
                continue
                
            # Si le champ est conditionnel, vérifier la condition
            if 'conditional' in rules:
                condition_func = rules['conditional']
                if condition_func(data) and value is None:
                    errors.append(ValidationError(
                        field, 
                        "Ce champ est requis dans ce contexte"
                    ))
                    continue
            
            # Si le champ est absent et non requis, passer à la suite
            if value is None:
                continue
                
            # Valider le type
            if 'type' in rules:
                expected_type = rules['type']
                if not self._validate_type(value, expected_type):
                    errors.append(ValidationError(
                        field, 
                        f"Ce champ doit être du type {expected_type.__name__}"
                    ))
                    continue
                    
            # Valider les règles supplémentaires
            self._validate_additional_rules(field, value, rules, errors)
            
        # Si des erreurs ont été trouvées, lever une exception
        if errors:
            for error in errors:
                logger.warning(f"Validation error: {error.field} - {error.message}")
            raise ValidationError(
                "multiple",
                "\n".join([f"{e.field}: {e.message}" for e in errors])
            )
            
    def _validate_type(self, value: Any, expected_type: Any) -> bool:
        """
        Valide le type d'une valeur.
        
        Args:
            value: Valeur à valider
            expected_type: Type attendu
            
        Returns:
            True si le type est valide, False sinon
        """
        # Types primitifs standards
        if expected_type in (str, int, float, bool, dict, list):
            return isinstance(value, expected_type)
            
        # Types spéciaux
        if expected_type == datetime.datetime:
            try:
                if isinstance(value, str):
                    # Essayer de parser les dates ISO
                    datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return True
                return isinstance(value, datetime.datetime)
            except ValueError:
                return False
                
        if expected_type == uuid.UUID:
            try:
                if isinstance(value, str):
                    uuid.UUID(value)
                    return True
                return isinstance(value, uuid.UUID)
            except ValueError:
                return False
                
        # Type non reconnu
        return False
            
    def _validate_additional_rules(self, field: str, value: Any, 
                                 rules: Dict[str, Any], errors: List[ValidationError]) -> None:
        """
        Valide les règles supplémentaires pour un champ.
        
        Args:
            field: Nom du champ
            value: Valeur du champ
            rules: Règles de validation
            errors: Liste d'erreurs à compléter
            
        Returns:
            None
        """
        # Validation des choix
        if 'choices' in rules and value not in rules['choices']:
            errors.append(ValidationError(
                field, 
                f"Ce champ doit être l'une des valeurs suivantes: {', '.join(rules['choices'])}"
            ))
            
        # Validation de longueur minimale/maximale
        if isinstance(value, (str, list, dict)):
            if 'min_length' in rules and len(value) < rules['min_length']:
                errors.append(ValidationError(
                    field, 
                    f"Ce champ doit avoir au moins {rules['min_length']} caractères"
                ))
            if 'max_length' in rules and len(value) > rules['max_length']:
                errors.append(ValidationError(
                    field, 
                    f"Ce champ ne doit pas dépasser {rules['max_length']} caractères"
                ))
                
        # Validation de valeur minimale/maximale
        if isinstance(value, (int, float)):
            if 'min_value' in rules and value < rules['min_value']:
                errors.append(ValidationError(
                    field, 
                    f"Ce champ doit être supérieur ou égal à {rules['min_value']}"
                ))
            if 'max_value' in rules and value > rules['max_value']:
                errors.append(ValidationError(
                    field, 
                    f"Ce champ doit être inférieur ou égal à {rules['max_value']}"
                ))
                
        # Validation par expression régulière
        if isinstance(value, str) and 'pattern' in rules:
            pattern = rules['pattern']
            if not re.match(pattern, value):
                errors.append(ValidationError(
                    field, 
                    "Ce champ n'est pas au format attendu"
                ))
                
        # Validation d'adresse IP
        if rules.get('is_ip_address', False) and isinstance(value, str):
            try:
                ipaddress.ip_address(value)
            except ValueError:
                errors.append(ValidationError(
                    field, 
                    "Ce champ doit être une adresse IP valide"
                ))
                
        # Validation de fonction personnalisée
        if 'custom_validator' in rules:
            validator = rules['custom_validator']
            result = validator(value)
            if not result[0]:
                errors.append(ValidationError(field, result[1]))
                
    def _apply_defaults(self, data: Dict[str, Any]) -> None:
        """
        Applique les valeurs par défaut aux champs absents.
        
        Args:
            data: Données à compléter
            
        Returns:
            None
        """
        for field, rules in self.rules.items():
            if field not in data and 'default' in rules:
                data[field] = rules['default'] 