"""
Entités du domaine pour la gestion de la sécurité.

Ce module définit les entités du domaine security_management,
indépendamment de toute infrastructure ou technologie spécifique.
Les entités représentent les concepts métier fondamentaux et sont
pures, ne dépendant d'aucun framework ou base de données.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum, auto


class RuleType(Enum):
    """Types de règles de sécurité supportés par le système."""
    SURICATA = "suricata"
    FAIL2BAN = "fail2ban"
    FIREWALL = "firewall"
    ACL = "acl"
    CUSTOM = "custom"
    ANOMALY = "anomaly"
    ACCESS_CONTROL = "access_control"


class SeverityLevel(Enum):
    """Niveaux de gravité pour les alertes et règles de sécurité."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionType(Enum):
    """Actions possibles pour les règles de sécurité."""
    ALLOW = "allow"
    DENY = "deny"
    REJECT = "reject"
    LOG = "log"


class CategoryType(Enum):
    """Catégories de règles de sécurité."""
    MALWARE = "malware"
    WEB_ATTACK = "web-attack"
    NETWORK = "network"
    DOS = "dos"
    SCAN = "scanning"
    BACKDOOR = "backdoor"
    PHISHING = "phishing"
    OTHER = "other"


class AlertStatus(Enum):
    """Statuts possibles pour une alerte de sécurité."""
    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


@dataclass(frozen=True)
class EntityId:
    """Identifiant unique et typé pour une entité du domaine."""
    value: Union[int, str]
    
    def __eq__(self, other):
        if not isinstance(other, EntityId):
            return False
        return self.value == other.value
    
    def __hash__(self):
        return hash(self.value)


@dataclass
class SecurityRule:
    """
    Règle de sécurité pour différents systèmes (firewall, IDS, etc.).
    
    Cette entité encapsule les informations nécessaires pour définir
    et appliquer une règle de sécurité dans le système.
    """
    id: Optional[EntityId] = None
    name: str = ""
    rule_type: RuleType = RuleType.CUSTOM
    content: str = ""
    description: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.MEDIUM
    is_active: bool = True
    is_system: bool = False
    category: Optional[CategoryType] = None
    enabled: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    action: Optional[ActionType] = None
    priority: int = 0
    
    def enable(self) -> None:
        """Active la règle."""
        self.is_active = True
        self.enabled = True
        
    def disable(self) -> None:
        """Désactive la règle."""
        self.is_active = False
        self.enabled = False
    
    def __eq__(self, other):
        if not isinstance(other, SecurityRule):
            return False
        return self.id == other.id if self.id and other.id else self.name == other.name


@dataclass
class SecurityAlert:
    """
    Alerte de sécurité générée par un système de détection ou de prévention.
    
    Cette entité représente un événement de sécurité qui nécessite une attention
    ou une action de la part des administrateurs ou des systèmes automatisés.
    """
    id: Optional[EntityId] = None
    source: str = ""
    event_type: str = ""
    severity: SeverityLevel = SeverityLevel.MEDIUM
    source_ip: str = ""
    destination_ip: str = ""
    message: str = ""
    rule_id: Optional[EntityId] = None
    status: AlertStatus = AlertStatus.NEW
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    correlation_ids: List[EntityId] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def resolve(self, resolution_notes: str) -> None:
        """Marque l'alerte comme résolue avec des notes."""
        self.status = AlertStatus.RESOLVED
        self.resolution_notes = resolution_notes
        self.updated_at = datetime.now()
    
    def acknowledge(self, assigned_to: Optional[str] = None) -> None:
        """Marque l'alerte comme prise en compte."""
        self.status = AlertStatus.ACKNOWLEDGED
        if assigned_to:
            self.assigned_to = assigned_to
        self.updated_at = datetime.now()
    
    def mark_in_progress(self, assigned_to: Optional[str] = None) -> None:
        """Marque l'alerte comme étant en cours de traitement."""
        self.status = AlertStatus.IN_PROGRESS
        if assigned_to:
            self.assigned_to = assigned_to
        self.updated_at = datetime.now()
    
    def mark_false_positive(self, notes: Optional[str] = None) -> None:
        """Marque l'alerte comme étant un faux positif."""
        self.status = AlertStatus.FALSE_POSITIVE
        if notes:
            self.resolution_notes = notes if not self.resolution_notes else f"{self.resolution_notes}\n---\n{notes}"
        self.updated_at = datetime.now()


@dataclass
class AuditLog:
    """
    Journal d'audit pour tracer les actions sur le système de sécurité.
    
    Cette entité conserve une trace des actions réalisées sur le système
    pour des besoins d'audit, de conformité ou d'investigation.
    """
    id: Optional[EntityId] = None
    user: Optional[str] = None
    action: str = ""
    entity_type: str = ""
    entity_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None
    ip_address: str = ""
    success: bool = True
    
    def __post_init__(self):
        """Initialise l'horodatage si non fourni."""
        if not self.timestamp:
            self.timestamp = datetime.now()


@dataclass
class BannedIP:
    """
    Adresse IP bannie par un système de sécurité.
    
    Cette entité représente une adresse IP qui a été interdite d'accès
    à tout ou partie du système suite à une activité malveillante.
    """
    ip_address: str
    jail: str
    timestamp: Optional[datetime] = None
    reason: Optional[str] = None
    duration: Optional[int] = None  # Durée en secondes
    expiry: Optional[datetime] = None
    banned_by: str = "system"
    
    def __post_init__(self):
        """Initialise l'horodatage et la date d'expiration si nécessaire."""
        if not self.timestamp:
            self.timestamp = datetime.now()
        
        if self.duration and not self.expiry:
            self.expiry = self.timestamp.timestamp() + self.duration


@dataclass
class Jail:
    """
    Configuration d'une prison (jail) pour l'isolation de menaces.
    
    Cette entité définit un ensemble de règles pour détecter et bloquer
    des comportements malveillants sur certains services ou protocoles.
    """
    name: str
    enabled: bool = True
    filter: str = ""
    action: str = ""
    ban_time: int = 3600  # Durée par défaut en secondes
    find_time: int = 600
    max_retry: int = 5
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrafficBaseline:
    """
    Référence de trafic normal pour la détection d'anomalies.
    
    Cette entité établit une base de référence du trafic considéré normal
    pour un service ou une partie du réseau, afin de pouvoir détecter
    des variations anormales indicatrices de menaces.
    """
    id: Optional[EntityId] = None
    name: str = ""
    description: Optional[str] = None
    traffic_type: str = "network"  # 'http', 'network', etc.
    is_active: bool = True
    is_learning: bool = False
    learning_period_days: int = 7
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    start_learning: Optional[datetime] = None
    end_learning: Optional[datetime] = None
    avg_requests_per_minute: Optional[float] = None
    avg_bytes_per_minute: Optional[float] = None
    avg_connections_per_minute: Optional[float] = None
    request_threshold_pct: float = 50.0  # % au-dessus duquel une anomalie est détectée
    byte_threshold_pct: float = 50.0
    connection_threshold_pct: float = 50.0
    reference_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def start_learning_mode(self) -> None:
        """Démarre le mode d'apprentissage pour établir la référence."""
        self.is_learning = True
        self.start_learning = datetime.now()
        self.end_learning = None
    
    def stop_learning_mode(self) -> None:
        """Arrête le mode d'apprentissage et finalise la référence."""
        self.is_learning = False
        self.end_learning = datetime.now()
        self.updated_at = datetime.now()


@dataclass
class TrafficAnomaly:
    """
    Anomalie de trafic détectée par rapport à une référence.
    
    Cette entité représente une déviation significative par rapport
    au trafic normal, pouvant indiquer une menace de sécurité.
    """
    id: Optional[EntityId] = None
    baseline_id: Optional[EntityId] = None
    anomaly_type: str = ""  # 'volume', 'pattern', 'connection', etc.
    severity: SeverityLevel = SeverityLevel.MEDIUM
    current_value: float = 0.0
    baseline_value: float = 0.0
    deviation_percent: float = 0.0
    source_ip: Optional[str] = None
    status: str = "new"  # 'new', 'acknowledged', 'resolved', 'false_positive'
    timestamp: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    review_timestamp: Optional[datetime] = None
    alert_id: Optional[EntityId] = None


@dataclass
class IPReputation:
    """
    Réputation d'une adresse IP basée sur son comportement.
    
    Cette entité maintient une évaluation de la confiance accordée à
    une adresse IP, basée sur son historique et son comportement.
    """
    id: Optional[EntityId] = None
    ip_address: str = ""
    reputation_score: int = 50  # 0-100, 0=mauvais, 100=bon
    is_whitelisted: bool = False
    is_blacklisted: bool = False
    last_seen: Optional[datetime] = None
    first_seen: Optional[datetime] = None
    alert_count: int = 0
    traffic_volume: float = 0.0
    classification: str = "unknown"  # 'normal', 'suspicious', 'malicious', 'unknown'
    details: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialise les horodatages si nécessaire."""
        now = datetime.now()
        if not self.last_seen:
            self.last_seen = now
        if not self.first_seen:
            self.first_seen = now
    
    def update_score(self, delta: int) -> None:
        """
        Met à jour le score de réputation.
        
        Args:
            delta: Valeur d'ajustement du score (peut être positif ou négatif)
        """
        self.reputation_score = max(0, min(100, self.reputation_score + delta))
        self.last_seen = datetime.now()


@dataclass
class CorrelationRule:
    """
    Règle de corrélation pour la détection de motifs complexes.
    
    Cette entité définit un ensemble de conditions qui, lorsqu'elles sont
    toutes remplies dans une fenêtre de temps donnée, déclenchent une alerte
    ou une action de sécurité plus sophistiquée que de simples règles.
    """
    id: Optional[EntityId] = None
    name: str = ""
    description: Optional[str] = None
    is_enabled: bool = True
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    action: str = "alert"  # 'alert', 'block', 'notify', 'escalate', 'custom'
    action_parameters: Dict[str, Any] = field(default_factory=dict)
    time_window: int = 300  # Fenêtre de temps en secondes
    threshold: int = 1  # Nombre minimum d'événements
    trigger_count: int = 0
    last_triggered: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None


@dataclass
class CorrelationRuleMatch:
    """
    Correspondance d'une règle de corrélation avec des événements.
    
    Cette entité représente une instance où une règle de corrélation
    a été déclenchée par un ensemble d'événements de sécurité.
    """
    id: Optional[EntityId] = None
    correlation_rule_id: Optional[EntityId] = None
    matched_at: Optional[datetime] = None
    triggering_events: List[Dict[str, Any]] = field(default_factory=list)
    generated_alert_id: Optional[EntityId] = None
    context_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialise l'horodatage si nécessaire."""
        if not self.matched_at:
            self.matched_at = datetime.now()


@dataclass
class SecurityPolicy:
    """
    Politique de sécurité définissant des règles et contraintes.
    
    Cette entité définit un ensemble de règles et contraintes de sécurité
    qui doivent être appliquées dans l'ensemble du système.
    """
    id: Optional[EntityId] = None
    name: str = ""
    description: Optional[str] = None
    rules: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    
    def validate_password(self, password: str) -> bool:
        """
        Valide un mot de passe selon les règles de la politique.
        
        Args:
            password: Le mot de passe à valider
            
        Returns:
            bool: True si le mot de passe est valide, False sinon
        """
        if 'password' not in self.rules:
            return True
            
        password_rules = self.rules['password']
        
        # Vérifier la longueur minimale
        if 'min_length' in password_rules and len(password) < password_rules['min_length']:
            return False
            
        # Vérifier la présence de majuscules
        if password_rules.get('require_uppercase', False) and not any(c.isupper() for c in password):
            return False
            
        # Vérifier la présence de minuscules
        if password_rules.get('require_lowercase', False) and not any(c.islower() for c in password):
            return False
            
        # Vérifier la présence de chiffres
        if password_rules.get('require_numbers', False) and not any(c.isdigit() for c in password):
            return False
            
        # Vérifier la présence de caractères spéciaux
        if password_rules.get('require_special', False):
            special_chars = set("!@#$%^&*()_+-=[]{}|;:,.<>?/~`")
            if not any(c in special_chars for c in password):
                return False
                
        return True


@dataclass
class Vulnerability:
    """
    Vulnérabilité de sécurité identifiée dans le système.
    
    Cette entité représente une faiblesse ou une faille de sécurité
    qui pourrait être exploitée par une menace.
    """
    id: Optional[EntityId] = None
    cve_id: Optional[str] = None
    title: str = ""
    description: str = ""
    severity: SeverityLevel = SeverityLevel.MEDIUM
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    cwe_id: Optional[str] = None
    affected_systems: List[str] = field(default_factory=list)
    affected_software: Optional[str] = None
    affected_versions: Optional[str] = None
    status: str = "identified"  # identified, confirmed, in_progress, patched, mitigated, false_positive, accepted_risk
    discovered_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    patched_date: Optional[datetime] = None
    references: List[Dict[str, str]] = field(default_factory=list)
    patch_available: bool = False
    patch_info: Dict[str, Any] = field(default_factory=dict)
    assigned_to: Optional[str] = None
    priority: int = 3  # 1-5, 1 étant la plus haute priorité
    
    def __post_init__(self):
        """Initialise les dates si nécessaire."""
        if not self.discovered_date:
            self.discovered_date = datetime.now()
    
    def get_exploitability_score(self) -> float:
        """
        Calcule un score d'exploitabilité basé sur le CVSS et d'autres facteurs.
        
        Returns:
            float: Score d'exploitabilité entre 0 et 10
        """
        base_score = self.cvss_score if self.cvss_score is not None else 5.0
        
        # Ajuster en fonction de la disponibilité d'un patch
        if self.patch_available:
            base_score *= 0.8  # Réduire le score si un patch est disponible
            
        # Ajuster en fonction des systèmes affectés
        if len(self.affected_systems) > 10:
            base_score *= 1.2  # Augmenter le score si beaucoup de systèmes sont affectés
            
        return min(10.0, base_score)


@dataclass
class ThreatIntelligence:
    """
    Indicateur de menace provenant de sources d'intelligence.
    
    Cette entité représente un indicateur de compromission (IOC) ou
    une autre information de menace utilisée pour détecter des activités malveillantes.
    """
    id: Optional[EntityId] = None
    indicator_type: str = ""  # ip, domain, url, hash_md5, hash_sha1, hash_sha256, email, etc.
    indicator_value: str = ""
    threat_type: str = ""  # malware, phishing, botnet, apt, ransomware, etc.
    confidence: float = 0.5  # 0.0 à 1.0
    severity: SeverityLevel = SeverityLevel.MEDIUM
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None
    source_reliability: str = "medium"  # low, medium, high, confirmed
    external_id: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    is_active: bool = True
    is_whitelisted: bool = False
    context: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialise les dates si nécessaire."""
        now = datetime.now()
        if not self.first_seen:
            self.first_seen = now
        if not self.last_seen:
            self.last_seen = now
    
    def is_expired(self) -> bool:
        """
        Vérifie si l'indicateur de menace est expiré.
        
        Returns:
            bool: True si l'indicateur est expiré, False sinon
        """
        if not self.valid_until:
            return False
        return datetime.now() > self.valid_until


@dataclass
class IncidentResponseWorkflow:
    """
    Workflow de réponse aux incidents de sécurité.
    
    Cette entité définit un processus automatisé ou semi-automatisé
    pour répondre à un incident de sécurité détecté.
    """
    id: Optional[EntityId] = None
    name: str = ""
    description: Optional[str] = None
    version: str = "1.0"
    trigger_type: str = ""  # alert_severity, alert_source, ioc_match, vulnerability_score, correlation_rule, manual
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    auto_execute: bool = False
    requires_approval: bool = True
    timeout_minutes: int = 60
    assigned_team: Optional[str] = None
    escalation_rules: Dict[str, Any] = field(default_factory=dict)
    status: str = "draft"  # draft, active, inactive, archived
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    execution_count: int = 0
    success_count: int = 0
    last_executed: Optional[datetime] = None
    
    def __post_init__(self):
        """Initialise les dates si nécessaire."""
        now = datetime.now()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
    
    def get_success_rate(self) -> float:
        """
        Calcule le taux de réussite du workflow.
        
        Returns:
            float: Taux de réussite entre 0 et 1
        """
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count


@dataclass
class IncidentResponseExecution:
    """
    Exécution d'un workflow de réponse aux incidents.
    
    Cette entité représente une instance d'exécution d'un workflow
    de réponse à un incident spécifique.
    """
    id: Optional[EntityId] = None
    workflow_id: Optional[EntityId] = None
    triggered_by_alert_id: Optional[EntityId] = None
    triggered_by_event: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending, running, completed, failed, cancelled, timeout
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_step: int = 0
    steps_log: List[Dict[str, Any]] = field(default_factory=list)
    assigned_to: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """Initialise les dates si nécessaire."""
        if not self.started_at:
            self.started_at = datetime.now()
    
    def get_duration(self) -> Optional[float]:
        """
        Calcule la durée d'exécution en secondes.
        
        Returns:
            Optional[float]: Durée en secondes ou None si l'exécution n'est pas terminée
        """
        if not self.completed_at:
            return None
        return (self.completed_at - self.started_at).total_seconds()
    
    def complete(self, success: bool = True, output_data: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> None:
        """
        Marque l'exécution comme terminée.
        
        Args:
            success: True si l'exécution a réussi, False sinon
            output_data: Données de sortie optionnelles
            error_message: Message d'erreur optionnel en cas d'échec
        """
        self.status = "completed" if success else "failed"
        self.completed_at = datetime.now()
        if output_data:
            self.output_data = output_data
        if error_message:
            self.error_message = error_message


@dataclass
class SecurityReport:
    """
    Rapport de sécurité généré par le système.
    
    Cette entité représente un rapport contenant des informations
    sur la sécurité du système, généré manuellement ou automatiquement.
    """
    id: Optional[EntityId] = None
    name: str = ""
    report_type: str = ""  # vulnerability, threat_intelligence, incident_response, compliance, security_posture, alert_summary, custom
    description: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    filters: Dict[str, Any] = field(default_factory=dict)
    format: str = "pdf"  # pdf, json, csv, html, excel
    is_scheduled: bool = False
    schedule_frequency: Optional[str] = None  # daily, weekly, monthly
    next_execution: Optional[datetime] = None
    status: str = "scheduled"  # generating, completed, failed, scheduled
    generated_at: Optional[datetime] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    recipients: List[str] = field(default_factory=list)
    auto_send: bool = False
    
    def __post_init__(self):
        """Initialise les dates si nécessaire."""
        if not self.created_at:
            self.created_at = datetime.now()


# Autres entités de domaine omises pour concision, à implémenter selon les besoins:
# - Vulnerability
# - ThreatIntelligence
# - IncidentResponseWorkflow
# - IncidentResponseExecution
# - SecurityReport 