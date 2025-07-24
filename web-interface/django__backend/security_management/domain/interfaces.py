"""
Interfaces du domaine pour le module security_management.

Ce fichier définit les interfaces abstraites pour les repositories et services utilisés
dans le module security_management selon les principes de l'architecture hexagonale.
Ces interfaces permettent de découpler le domaine de l'infrastructure.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, TypeVar, Generic
from datetime import datetime
import ipaddress

from .entities import (
    SecurityRule, SecurityAlert, AuditLog, BannedIP, Jail, 
    TrafficBaseline, TrafficAnomaly, IPReputation, 
    CorrelationRule, CorrelationRuleMatch, EntityId,
    RuleType, SeverityLevel, AlertStatus
)

# Type générique pour les entités du domaine
T = TypeVar('T')


class Repository(Generic[T], ABC):
    """
    Interface générique pour tous les repositories.
    
    Définit les méthodes CRUD de base que tous les repositories doivent implémenter.
    """
    
    @abstractmethod
    def get_by_id(self, entity_id: EntityId) -> Optional[T]:
        """
        Récupère une entité par son ID.
        
        Args:
            entity_id: Identifiant unique de l'entité
            
        Returns:
            L'entité correspondante ou None si non trouvée
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[T]:
        """
        Liste toutes les entités.
        
        Returns:
            Liste des entités
        """
        pass
    
    @abstractmethod
    def save(self, entity: T) -> T:
        """
        Sauvegarde une entité (création ou mise à jour).
        
        Args:
            entity: L'entité à sauvegarder
            
        Returns:
            L'entité sauvegardée avec son ID attribué si c'est une création
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: EntityId) -> bool:
        """
        Supprime une entité.
        
        Args:
            entity_id: Identifiant unique de l'entité à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        pass


class SecurityRuleRepository(Repository[SecurityRule], ABC):
    """
    Interface pour le repository de règles de sécurité.
    
    Étend le repository générique avec des méthodes spécifiques aux règles de sécurité.
    """
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[SecurityRule]:
        """
        Recherche une règle par son nom.
        
        Args:
            name: Nom de la règle à rechercher
            
        Returns:
            La règle correspondante ou None si non trouvée
        """
        pass
    
    @abstractmethod
    def find_by_type(self, rule_type: RuleType) -> List[SecurityRule]:
        """
        Recherche des règles par leur type.
        
        Args:
            rule_type: Type de règle à rechercher
            
        Returns:
            Liste des règles correspondantes
        """
        pass
    
    @abstractmethod
    def find_active(self) -> List[SecurityRule]:
        """
        Recherche les règles actives.
        
        Returns:
            Liste des règles actives
        """
        pass
    
    @abstractmethod
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[SecurityRule]:
        """
        Recherche des règles selon des critères multiples.
        
        Args:
            criteria: Dictionnaire de critères de recherche
            
        Returns:
            Liste des règles correspondantes
        """
        pass
    
    @abstractmethod
    def find_conflicting_rules(self, rule: SecurityRule) -> List[SecurityRule]:
        """
        Recherche des règles pouvant être en conflit avec une règle donnée.
        
        Args:
            rule: Règle pour laquelle rechercher des conflits
            
        Returns:
            Liste des règles potentiellement en conflit
        """
        pass


class SecurityAlertRepository(Repository[SecurityAlert], ABC):
    """
    Interface pour le repository d'alertes de sécurité.
    
    Étend le repository générique avec des méthodes spécifiques aux alertes de sécurité.
    """
    
    @abstractmethod
    def find_by_status(self, status: AlertStatus) -> List[SecurityAlert]:
        """
        Recherche des alertes par statut.
        
        Args:
            status: Statut des alertes à rechercher
            
        Returns:
            Liste des alertes correspondantes
        """
        pass
    
    @abstractmethod
    def find_by_severity(self, severity: SeverityLevel) -> List[SecurityAlert]:
        """
        Recherche des alertes par niveau de gravité.
        
        Args:
            severity: Niveau de gravité des alertes à rechercher
            
        Returns:
            Liste des alertes correspondantes
        """
        pass
    
    @abstractmethod
    def find_by_source_ip(self, source_ip: str) -> List[SecurityAlert]:
        """
        Recherche des alertes par adresse IP source.
        
        Args:
            source_ip: Adresse IP source à rechercher
            
        Returns:
            Liste des alertes correspondantes
        """
        pass
    
    @abstractmethod
    def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[SecurityAlert]:
        """
        Recherche des alertes dans une plage temporelle.
        
        Args:
            start_time: Date/heure de début
            end_time: Date/heure de fin
            
        Returns:
            Liste des alertes correspondantes
        """
        pass
    
    @abstractmethod
    def find_related_alerts(self, alert: SecurityAlert) -> List[SecurityAlert]:
        """
        Recherche des alertes liées à une alerte donnée.
        
        Args:
            alert: Alerte pour laquelle rechercher des alertes liées
            
        Returns:
            Liste des alertes liées
        """
        pass


class AuditLogRepository(Repository[AuditLog], ABC):
    """
    Interface pour le repository des journaux d'audit.
    
    Étend le repository générique avec des méthodes spécifiques aux journaux d'audit.
    """
    
    @abstractmethod
    def find_by_user(self, user: str) -> List[AuditLog]:
        """
        Recherche des journaux d'audit par utilisateur.
        
        Args:
            user: Nom d'utilisateur à rechercher
            
        Returns:
            Liste des journaux d'audit correspondants
        """
        pass
    
    @abstractmethod
    def find_by_action(self, action: str) -> List[AuditLog]:
        """
        Recherche des journaux d'audit par type d'action.
        
        Args:
            action: Type d'action à rechercher
            
        Returns:
            Liste des journaux d'audit correspondants
        """
        pass
    
    @abstractmethod
    def find_by_entity(self, entity_type: str, entity_id: str) -> List[AuditLog]:
        """
        Recherche des journaux d'audit par entité.
        
        Args:
            entity_type: Type d'entité concernée
            entity_id: ID de l'entité concernée
            
        Returns:
            Liste des journaux d'audit correspondants
        """
        pass
    
    @abstractmethod
    def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[AuditLog]:
        """
        Recherche des journaux d'audit dans une plage temporelle.
        
        Args:
            start_time: Date/heure de début
            end_time: Date/heure de fin
            
        Returns:
            Liste des journaux d'audit correspondants
        """
        pass


class SecurityDeviceRepository(ABC):
    """
    Interface pour le repository des équipements de sécurité.
    
    Définit les méthodes pour manipuler les équipements de sécurité.
    """
    
    @abstractmethod
    def get_device(self, device_id: EntityId) -> Dict[str, Any]:
        """
        Récupère un équipement de sécurité par son ID.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Données de l'équipement de sécurité
        """
        pass
    
    @abstractmethod
    def list_devices(self, device_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Liste les équipements de sécurité, éventuellement filtrés par type.
        
        Args:
            device_type: Type d'équipement (optionnel)
            
        Returns:
            Liste des équipements de sécurité
        """
        pass
    
    @abstractmethod
    def get_device_status(self, device_id: EntityId) -> Dict[str, Any]:
        """
        Récupère le statut d'un équipement de sécurité.
        
        Args:
            device_id: ID de l'équipement
            
        Returns:
            Statut de l'équipement
        """
        pass


class CorrelationRuleRepository(Repository[CorrelationRule], ABC):
    """
    Interface pour le repository des règles de corrélation.
    
    Étend le repository générique avec des méthodes spécifiques aux règles de corrélation.
    """
    
    @abstractmethod
    def find_active_rules(self) -> List[CorrelationRule]:
        """
        Récupère toutes les règles de corrélation actives.
        
        Returns:
            Liste des règles de corrélation actives
        """
        pass
    
    @abstractmethod
    def increment_trigger_count(self, rule_id: EntityId) -> None:
        """
        Incrémente le compteur de déclenchements d'une règle.
        
        Args:
            rule_id: ID de la règle
        """
        pass


class CorrelationRuleMatchRepository(Repository[CorrelationRuleMatch], ABC):
    """
    Interface pour le repository des correspondances de règles de corrélation.
    
    Étend le repository générique avec des méthodes spécifiques aux correspondances
    de règles de corrélation.
    """
    
    @abstractmethod
    def find_by_rule_id(self, rule_id: EntityId) -> List[CorrelationRuleMatch]:
        """
        Récupère les correspondances pour une règle de corrélation donnée.
        
        Args:
            rule_id: ID de la règle de corrélation
            
        Returns:
            Liste des correspondances pour cette règle
        """
        pass
    
    @abstractmethod
    def find_recent_matches(self, limit: int = 50) -> List[CorrelationRuleMatch]:
        """
        Récupère les correspondances de règles les plus récentes.
        
        Args:
            limit: Nombre maximum de résultats à retourner
            
        Returns:
            Liste des correspondances récentes
        """
        pass


class SuricataService(ABC):
    """
    Interface pour le service d'intégration avec Suricata IDS.
    
    Définit les méthodes pour interagir avec le système Suricata IDS.
    """
    
    @abstractmethod
    def add_rule(self, rule_content: str, filename: Optional[str] = None) -> bool:
        """
        Ajoute une règle Suricata au fichier de règles approprié.
        
        Args:
            rule_content: Contenu de la règle au format Suricata
            filename: Nom du fichier de règles (optionnel)
            
        Returns:
            True si l'ajout a réussi
        """
        pass
    
    @abstractmethod
    def delete_rule(self, rule_id: str) -> bool:
        """
        Supprime une règle Suricata par son ID.
        
        Args:
            rule_id: ID de la règle Suricata
            
        Returns:
            True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def reload_rules(self) -> bool:
        """
        Recharge les règles Suricata sans redémarrer le service.
        
        Returns:
            True si le rechargement a réussi
        """
        pass
    
    @abstractmethod
    def get_alerts(self, since: Optional[datetime] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les alertes générées par Suricata.
        
        Args:
            since: Date/heure à partir de laquelle récupérer les alertes (optionnel)
            limit: Nombre maximum d'alertes à récupérer
            
        Returns:
            Liste des alertes Suricata
        """
        pass
    
    @abstractmethod
    def validate_rule(self, rule_content: str) -> Dict[str, Any]:
        """
        Valide la syntaxe d'une règle Suricata.
        
        Args:
            rule_content: Contenu de la règle à valider
            
        Returns:
            Résultat de la validation avec éventuelles erreurs
        """
        pass


class Fail2BanService(ABC):
    """
    Interface pour le service d'intégration avec Fail2Ban.
    
    Définit les méthodes pour interagir avec le système Fail2Ban.
    """
    
    @abstractmethod
    def get_jails(self) -> List[Jail]:
        """
        Récupère la liste des prisons (jails) configurées.
        
        Returns:
            Liste des prisons Fail2Ban
        """
        pass
    
    @abstractmethod
    def get_banned_ips(self, jail: Optional[str] = None) -> List[BannedIP]:
        """
        Récupère la liste des IPs bannies, éventuellement filtrée par prison.
        
        Args:
            jail: Nom de la prison (optionnel)
            
        Returns:
            Liste des IPs bannies
        """
        pass
    
    @abstractmethod
    def ban_ip(self, ip: str, jail: str, duration: Optional[int] = None) -> bool:
        """
        Banni manuellement une IP dans une prison donnée.
        
        Args:
            ip: Adresse IP à bannir
            jail: Nom de la prison
            duration: Durée du bannissement en secondes (optionnel)
            
        Returns:
            True si le bannissement a réussi
        """
        pass
    
    @abstractmethod
    def unban_ip(self, ip: str, jail: Optional[str] = None) -> bool:
        """
        Lève le bannissement d'une IP, éventuellement seulement dans une prison donnée.
        
        Args:
            ip: Adresse IP à débannir
            jail: Nom de la prison (optionnel, toutes les prisons si non spécifié)
            
        Returns:
            True si le débannissement a réussi
        """
        pass


class FirewallService(ABC):
    """
    Interface pour le service de gestion du pare-feu.
    
    Définit les méthodes pour interagir avec le pare-feu du système.
    """
    
    @abstractmethod
    def add_rule(self, rule_definition: Dict[str, Any]) -> bool:
        """
        Ajoute une règle au pare-feu.
        
        Args:
            rule_definition: Définition de la règle de pare-feu
            
        Returns:
            True si l'ajout a réussi
        """
        pass
    
    @abstractmethod
    def delete_rule(self, rule_identifier: str) -> bool:
        """
        Supprime une règle du pare-feu.
        
        Args:
            rule_identifier: Identifiant de la règle à supprimer
            
        Returns:
            True si la suppression a réussi
        """
        pass
    
    @abstractmethod
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Récupère les règles actuelles du pare-feu.
        
        Returns:
            Liste des règles de pare-feu
        """
        pass
    
    @abstractmethod
    def block_ip(self, ip: Union[str, ipaddress.IPv4Address, ipaddress.IPv6Address], duration: Optional[int] = None) -> bool:
        """
        Bloque une adresse IP dans le pare-feu.
        
        Args:
            ip: Adresse IP à bloquer
            duration: Durée du blocage en secondes (optionnel)
            
        Returns:
            True si le blocage a réussi
        """
        pass
    
    @abstractmethod
    def unblock_ip(self, ip: Union[str, ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
        """
        Débloque une adresse IP dans le pare-feu.
        
        Args:
            ip: Adresse IP à débloquer
            
        Returns:
            True si le déblocage a réussi
        """
        pass
    
    @abstractmethod
    def is_ip_blocked(self, ip: Union[str, ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
        """
        Vérifie si une adresse IP est actuellement bloquée.
        
        Args:
            ip: Adresse IP à vérifier
            
        Returns:
            True si l'adresse IP est bloquée
        """
        pass


# Interfaces pour la détection de conflits et l'analyse d'impact

from dataclasses import dataclass


@dataclass
class RuleConflict:
    """
    Représente un conflit entre règles de sécurité.
    """
    conflict_id: str
    rule1_id: int
    rule2_id: int
    conflict_type: str
    severity: str
    description: str
    recommendation: str


class ConflictDetector(ABC):
    """
    Interface pour les détecteurs de conflits entre règles de sécurité.
    """
    
    @abstractmethod
    def detect_conflicts(self, rule_data: Dict[str, Any], existing_rules: List[Dict[str, Any]]) -> List[RuleConflict]:
        """
        Détecte les conflits entre une règle et des règles existantes.
        
        Args:
            rule_data: Données de la règle à vérifier
            existing_rules: Liste des règles existantes
            
        Returns:
            Liste des conflits détectés
        """
        pass
    
    @abstractmethod
    def analyze_ruleset(self, rules: List[Dict[str, Any]]) -> List[RuleConflict]:
        """
        Analyse un ensemble de règles pour détecter tous les conflits.
        
        Args:
            rules: Ensemble de règles à analyser
            
        Returns:
            Liste des conflits détectés
        """
        pass


@dataclass
class ImpactMetric:
    """
    Métrique d'impact pour l'analyse des règles de sécurité.
    """
    name: str
    value: float
    description: str
    category: str
    
    def is_acceptable(self, threshold: float = 0.7) -> bool:
        """
        Détermine si la métrique est acceptable selon un seuil.
        
        Args:
            threshold: Seuil d'acceptabilité (0.0 à 1.0)
            
        Returns:
            True si la métrique est acceptable
        """
        return self.value <= threshold


@dataclass
class ImpactAnalysisResult:
    """
    Résultat d'une analyse d'impact de règle de sécurité.
    """
    rule_id: int
    rule_type: str
    metrics: List[ImpactMetric]
    is_acceptable: bool
    recommendation: str


class ImpactAnalyzer(ABC):
    """
    Interface pour les analyseurs d'impact des règles de sécurité.
    """
    
    @abstractmethod
    def analyze_impact(self, rule_data: Dict[str, Any]) -> ImpactAnalysisResult:
        """
        Analyse l'impact d'une règle de sécurité.
        
        Args:
            rule_data: Données de la règle à analyser
            
        Returns:
            Résultat de l'analyse d'impact
        """
        pass


class RuleMetricsCalculator(ABC):
    """
    Interface pour les calculateurs de métriques de règles.
    """
    
    @abstractmethod
    def calculate_metrics(self, rule_data: Dict[str, Any]) -> List[ImpactMetric]:
        """
        Calcule les métriques d'impact pour une règle.
        
        Args:
            rule_data: Données de la règle
            
        Returns:
            Liste des métriques calculées
        """
        pass


class RecommendationGenerator(ABC):
    """
    Interface pour les générateurs de recommandations.
    """
    
    @abstractmethod
    def generate_recommendation(self, metrics: List[ImpactMetric], is_acceptable: bool, rule_data: Dict[str, Any]) -> str:
        """
        Génère une recommandation basée sur les métriques d'impact.
        
        Args:
            metrics: Liste des métriques d'impact
            is_acceptable: Indique si l'impact global est acceptable
            rule_data: Données de la règle
            
        Returns:
            Recommandation sous forme de texte
        """
        pass


class DockerServiceConnector(ABC):
    """
    Interface pour les connecteurs aux services Docker.
    
    Définit les méthodes de base pour interagir avec les services Docker
    via leurs APIs REST.
    """
    
    @abstractmethod
    def test_connection(self) -> bool:
        """
        Teste la connexion au service Docker.
        
        Returns:
            True si la connexion est établie
        """
        pass
    
    @abstractmethod
    def get_service_status(self) -> Dict[str, Any]:
        """
        Récupère le statut du service Docker.
        
        Returns:
            Statut du service avec informations détaillées
        """
        pass
    
    @abstractmethod
    def call_api(self, endpoint: str, method: str = 'GET', data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Effectue un appel API vers le service Docker.
        
        Args:
            endpoint: Point de terminaison de l'API
            method: Méthode HTTP (GET, POST, PUT, DELETE)
            data: Données à envoyer (pour POST/PUT)
            
        Returns:
            Réponse de l'API
        """
        pass


# D'autres interfaces peuvent être ajoutées selon les besoins du module
# comme IPReputationRepository, ThreatIntelligenceService, etc. 