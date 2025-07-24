"""
Repositories Django ORM sophistiqués pour le module security_management.

Ce module contient les implémentations des repositories avec des requêtes optimisées,
la mise en cache, les agrégations complexes, et l'intégration avec les services Docker.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple, Union
from collections import defaultdict
from functools import wraps

from django.db import transaction, connection
from django.db.models import Q, Count, Avg, Sum, Max, Min, F, Case, When, Value
from django.db.models.functions import TruncDate, TruncHour, Coalesce
from django.core.cache import cache
from django.core.paginator import Paginator
from django.utils import timezone
from django.conf import settings

from ..domain.interfaces import (
    SecurityRuleRepository, SecurityAlertRepository, AuditLogRepository,
    CorrelationRuleRepository, CorrelationRuleMatchRepository
)
from ..domain.entities import (
    SecurityRule, SecurityAlert, AuditLog, CorrelationRule, CorrelationRuleMatch,
    EntityId, RuleType, SeverityLevel, AlertStatus
)
from ..models import (
    SecurityRuleModel, SecurityAlertModel, AuditLogModel, 
    CorrelationRuleModel, CorrelationRuleMatchModel
)

logger = logging.getLogger(__name__)


def cache_result(timeout=300, key_prefix=""):
    """
    Décorateur pour mettre en cache les résultats des méthodes de repository.
    
    Args:
        timeout: Durée de cache en secondes
        key_prefix: Préfixe pour la clé de cache
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Générer une clé de cache basée sur les arguments
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Essayer de récupérer depuis le cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit pour {cache_key}")
                return result
            
            # Exécuter la méthode et mettre en cache
            result = func(self, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            logger.debug(f"Cache set pour {cache_key}")
            
            return result
        return wrapper
    return decorator


class BaseRepository:
    """
    Repository de base avec des fonctionnalités communes.
    """
    
    def __init__(self, model_class):
        """
        Initialise le repository avec le modèle Django.
        
        Args:
            model_class: Classe du modèle Django
        """
        self.model_class = model_class
        self._cache_timeout = 300  # 5 minutes par défaut
        
    def _get_cache_key(self, prefix: str, *args) -> str:
        """Génère une clé de cache."""
        return f"repo:{self.model_class.__name__.lower()}:{prefix}:{hash(str(args))}"
    
    def _invalidate_cache_pattern(self, pattern: str):
        """Invalide tous les caches correspondant à un pattern."""
        # Django ne supporte pas nativement la suppression par pattern
        # mais on peut implémenter une version simple
        try:
            cache.delete_many([pattern])
        except Exception as e:
            logger.warning(f"Erreur lors de l'invalidation du cache: {str(e)}")
    
    def get_queryset(self):
        """Retourne le queryset de base optimisé."""
        return self.model_class.objects.select_related().prefetch_related()
    
    def bulk_create_optimized(self, objects: List[Any], batch_size: int = 1000) -> List[Any]:
        """Création en lot optimisée."""
        try:
            return self.model_class.objects.bulk_create(objects, batch_size=batch_size)
        except Exception as e:
            logger.error(f"Erreur lors de la création en lot: {str(e)}")
            raise
    
    def bulk_update_optimized(self, objects: List[Any], fields: List[str], batch_size: int = 1000) -> int:
        """Mise à jour en lot optimisée."""
        try:
            return self.model_class.objects.bulk_update(objects, fields, batch_size=batch_size)
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour en lot: {str(e)}")
            raise


class DjangoSecurityRuleRepository(BaseRepository, SecurityRuleRepository):
    """
    Repository Django sophistiqué pour les règles de sécurité.
    """
    
    def __init__(self):
        """Initialise le repository pour les règles de sécurité."""
        super().__init__(SecurityRuleModel)
        logger.info("DjangoSecurityRuleRepository initialisé")
    
    def get_by_id(self, entity_id: EntityId) -> Optional[SecurityRule]:
        """Récupère une règle par son ID."""
        try:
            model = self.get_queryset().get(id=entity_id.value)
            return self._model_to_entity(model)
        except self.model_class.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la règle {entity_id}: {str(e)}")
            return None
    
    @cache_result(timeout=600, key_prefix="rules_all")
    def list_all(self) -> List[SecurityRule]:
        """Liste toutes les règles de sécurité."""
        try:
            models = self.get_queryset().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la liste des règles: {str(e)}")
            return []
    
    @transaction.atomic
    def save(self, entity: SecurityRule) -> SecurityRule:
        """Sauvegarde une règle de sécurité."""
        try:
            if entity.id:
                # Mise à jour
                model = self.model_class.objects.get(id=entity.id.value)
                self._update_model_from_entity(model, entity)
            else:
                # Création
                model = self._entity_to_model(entity)
            
            model.save()
            
            # Invalider les caches
            self._invalidate_related_caches()
            
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la règle: {str(e)}")
            raise
    
    def delete(self, entity_id: EntityId) -> bool:
        """Supprime une règle de sécurité."""
        try:
            deleted, _ = self.model_class.objects.filter(id=entity_id.value).delete()
            
            if deleted > 0:
                self._invalidate_related_caches()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la règle {entity_id}: {str(e)}")
            return False
    
    @cache_result(timeout=300, key_prefix="rules_by_name")
    def find_by_name(self, name: str) -> Optional[SecurityRule]:
        """Recherche une règle par son nom."""
        try:
            model = self.get_queryset().filter(name__iexact=name).first()
            return self._model_to_entity(model) if model else None
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par nom {name}: {str(e)}")
            return None
    
    @cache_result(timeout=300, key_prefix="rules_by_type")
    def find_by_type(self, rule_type: RuleType) -> List[SecurityRule]:
        """Recherche des règles par leur type."""
        try:
            models = self.get_queryset().filter(rule_type=rule_type.value).all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par type {rule_type}: {str(e)}")
            return []
    
    @cache_result(timeout=180, key_prefix="rules_active")
    def find_active(self) -> List[SecurityRule]:
        """Recherche les règles actives."""
        try:
            models = self.get_queryset().filter(enabled=True).all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des règles actives: {str(e)}")
            return []
    
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[SecurityRule]:
        """Recherche des règles selon des critères multiples."""
        try:
            queryset = self.get_queryset()
            
            # Construire les filtres dynamiquement
            filters = Q()
            
            if 'rule_type' in criteria:
                filters &= Q(rule_type=criteria['rule_type'])
            
            if 'enabled' in criteria:
                filters &= Q(enabled=criteria['enabled'])
            
            if 'severity' in criteria:
                filters &= Q(severity=criteria['severity'])
            
            if 'source_ip' in criteria:
                filters &= Q(source_ip=criteria['source_ip'])
            
            if 'destination_ip' in criteria:
                filters &= Q(destination_ip=criteria['destination_ip'])
            
            if 'content_contains' in criteria:
                filters &= Q(content__icontains=criteria['content_contains'])
            
            if 'created_after' in criteria:
                filters &= Q(created_at__gte=criteria['created_after'])
            
            if 'created_before' in criteria:
                filters &= Q(created_at__lte=criteria['created_before'])
            
            # Filtres de priorité
            if 'priority_min' in criteria:
                filters &= Q(priority__gte=criteria['priority_min'])
            
            if 'priority_max' in criteria:
                filters &= Q(priority__lte=criteria['priority_max'])
            
            models = queryset.filter(filters).all()
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par critères: {str(e)}")
            return []
    
    def find_conflicting_rules(self, rule: SecurityRule) -> List[SecurityRule]:
        """Recherche des règles pouvant être en conflit avec une règle donnée."""
        try:
            # Rechercher des règles similaires qui pourraient créer des conflits
            queryset = self.get_queryset().filter(rule_type=rule.rule_type)
            
            # Exclure la règle elle-même si elle a un ID
            if rule.id:
                queryset = queryset.exclude(id=rule.id.value)
            
            conflicts = Q()
            
            # Conflit potentiel si même IP source/destination
            if rule.source_ip:
                conflicts |= Q(source_ip=rule.source_ip)
            
            if rule.destination_ip:
                conflicts |= Q(destination_ip=rule.destination_ip)
            
            # Conflit potentiel si même port
            if hasattr(rule, 'source_port') and rule.source_port:
                conflicts |= Q(source_port=rule.source_port)
            
            if hasattr(rule, 'destination_port') and rule.destination_port:
                conflicts |= Q(destination_port=rule.destination_port)
            
            # Conflit potentiel si contenu similaire (pour les règles IDS)
            if rule.rule_type == RuleType.SURICATA and rule.content:
                # Extraire le SID de la règle
                import re
                sid_match = re.search(r'sid\s*:\s*(\d+)', rule.content)
                if sid_match:
                    sid = sid_match.group(1)
                    conflicts |= Q(content__icontains=f'sid:{sid}')
            
            models = queryset.filter(conflicts).all()
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de conflits: {str(e)}")
            return []
    
    def get_rules_statistics(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les règles."""
        try:
            cache_key = self._get_cache_key("stats")
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # Requêtes d'agrégation optimisées
            stats = self.model_class.objects.aggregate(
                total_rules=Count('id'),
                active_rules=Count('id', filter=Q(enabled=True)),
                inactive_rules=Count('id', filter=Q(enabled=False)),
                firewall_rules=Count('id', filter=Q(rule_type=RuleType.FIREWALL.value)),
                ids_rules=Count('id', filter=Q(rule_type=RuleType.SURICATA.value)),
                avg_priority=Avg('priority'),
                max_priority=Max('priority'),
                min_priority=Min('priority')
            )
            
            # Statistiques par type de règle
            type_stats = self.model_class.objects.values('rule_type').annotate(
                count=Count('id'),
                active_count=Count('id', filter=Q(enabled=True))
            ).order_by('rule_type')
            
            stats['by_type'] = {item['rule_type']: item for item in type_stats}
            
            # Statistiques par sévérité
            severity_stats = self.model_class.objects.values('severity').annotate(
                count=Count('id')
            ).order_by('severity')
            
            stats['by_severity'] = {item['severity']: item['count'] for item in severity_stats}
            
            # Tendances temporelles (derniers 30 jours)
            thirty_days_ago = timezone.now() - timedelta(days=30)
            daily_stats = self.model_class.objects.filter(
                created_at__gte=thirty_days_ago
            ).annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            stats['daily_creation'] = list(daily_stats)
            
            cache.set(cache_key, stats, 300)  # Cache 5 minutes
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {}
    
    def search_rules_advanced(self, query: str, filters: Dict[str, Any] = None, 
                            page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """Recherche avancée avec pagination et scoring."""
        try:
            queryset = self.get_queryset()
            
            # Recherche textuelle avec scoring
            search_filters = Q()
            if query:
                search_filters = (
                    Q(name__icontains=query) |
                    Q(description__icontains=query) |
                    Q(content__icontains=query)
                )
                
                # Ajouter un score de pertinence
                queryset = queryset.annotate(
                    relevance_score=Case(
                        When(name__icontains=query, then=Value(3)),
                        When(description__icontains=query, then=Value(2)),
                        When(content__icontains=query, then=Value(1)),
                        default=Value(0)
                    )
                )
            
            # Appliquer les filtres additionnels
            if filters:
                additional_filters = Q()
                
                for key, value in filters.items():
                    if key == 'rule_types' and isinstance(value, list):
                        additional_filters &= Q(rule_type__in=value)
                    elif key == 'enabled':
                        additional_filters &= Q(enabled=value)
                    elif key == 'severity_levels' and isinstance(value, list):
                        additional_filters &= Q(severity__in=value)
                    elif key == 'date_from':
                        additional_filters &= Q(created_at__gte=value)
                    elif key == 'date_to':
                        additional_filters &= Q(created_at__lte=value)
                
                search_filters &= additional_filters
            
            # Appliquer les filtres
            queryset = queryset.filter(search_filters)
            
            # Ordonner par pertinence puis par date
            if query:
                queryset = queryset.order_by('-relevance_score', '-created_at')
            else:
                queryset = queryset.order_by('-created_at')
            
            # Pagination
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)
            
            # Convertir en entités
            rules = [self._model_to_entity(model) for model in page_obj.object_list]
            
            return {
                'rules': rules,
                'total_count': paginator.count,
                'page_count': paginator.num_pages,
                'current_page': page,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
                'page_size': page_size
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche avancée: {str(e)}")
            return {
                'rules': [],
                'total_count': 0,
                'page_count': 0,
                'current_page': page,
                'has_next': False,
                'has_previous': False,
                'page_size': page_size
            }
    
    def _model_to_entity(self, model: SecurityRuleModel) -> SecurityRule:
        """Convertit un modèle Django en entité du domaine."""
        return SecurityRule(
            id=EntityId(model.id),
            name=model.name,
            rule_type=RuleType(model.rule_type),
            content=model.content,
            enabled=model.enabled,
            severity=model.severity,
            description=model.description,
            source_ip=model.source_ip,
            destination_ip=model.destination_ip,
            action=model.action,
            priority=model.priority,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model(self, entity: SecurityRule) -> SecurityRuleModel:
        """Convertit une entité du domaine en modèle Django."""
        return SecurityRuleModel(
            name=entity.name,
            rule_type=entity.rule_type.value if entity.rule_type else None,
            content=entity.content,
            enabled=entity.enabled,
            severity=entity.severity,
            description=entity.description,
            source_ip=entity.source_ip,
            destination_ip=entity.destination_ip,
            action=entity.action,
            priority=entity.priority
        )
    
    def _update_model_from_entity(self, model: SecurityRuleModel, entity: SecurityRule):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.name = entity.name
        model.rule_type = entity.rule_type.value if entity.rule_type else None
        model.content = entity.content
        model.enabled = entity.enabled
        model.severity = entity.severity
        model.description = entity.description
        model.source_ip = entity.source_ip
        model.destination_ip = entity.destination_ip
        model.action = entity.action
        model.priority = entity.priority
    
    def _invalidate_related_caches(self):
        """Invalide les caches liés aux règles."""
        patterns = [
            "repo:securityrulemodel:rules_all:",
            "repo:securityrulemodel:rules_by_type:",
            "repo:securityrulemodel:rules_active:",
            "repo:securityrulemodel:stats"
        ]
        
        for pattern in patterns:
            try:
                cache.delete_many([pattern])
            except Exception:
                pass


class DjangoSecurityAlertRepository(BaseRepository, SecurityAlertRepository):
    """
    Repository Django sophistiqué pour les alertes de sécurité.
    """
    
    def __init__(self):
        """Initialise le repository pour les alertes de sécurité."""
        super().__init__(SecurityAlertModel)
        logger.info("DjangoSecurityAlertRepository initialisé")
    
    def get_by_id(self, entity_id: EntityId) -> Optional[SecurityAlert]:
        """Récupère une alerte par son ID."""
        try:
            model = self.get_queryset().get(id=entity_id.value)
            return self._model_to_entity(model)
        except self.model_class.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'alerte {entity_id}: {str(e)}")
            return None
    
    @cache_result(timeout=60, key_prefix="alerts_all")
    def list_all(self) -> List[SecurityAlert]:
        """Liste toutes les alertes de sécurité."""
        try:
            # Limiter aux alertes récentes par défaut
            one_week_ago = timezone.now() - timedelta(days=7)
            models = self.get_queryset().filter(timestamp__gte=one_week_ago).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la liste des alertes: {str(e)}")
            return []
    
    @transaction.atomic
    def save(self, entity: SecurityAlert) -> SecurityAlert:
        """Sauvegarde une alerte de sécurité."""
        try:
            if entity.id:
                # Mise à jour
                model = self.model_class.objects.get(id=entity.id.value)
                self._update_model_from_entity(model, entity)
            else:
                # Création
                model = self._entity_to_model(entity)
            
            model.save()
            
            # Invalider les caches
            self._invalidate_related_caches()
            
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'alerte: {str(e)}")
            raise
    
    def delete(self, entity_id: EntityId) -> bool:
        """Supprime une alerte de sécurité."""
        try:
            deleted, _ = self.model_class.objects.filter(id=entity_id.value).delete()
            
            if deleted > 0:
                self._invalidate_related_caches()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de l'alerte {entity_id}: {str(e)}")
            return False
    
    @cache_result(timeout=120, key_prefix="alerts_by_status")
    def find_by_status(self, status: AlertStatus) -> List[SecurityAlert]:
        """Recherche des alertes par statut."""
        try:
            models = self.get_queryset().filter(status=status.value).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par statut {status}: {str(e)}")
            return []
    
    @cache_result(timeout=120, key_prefix="alerts_by_severity")
    def find_by_severity(self, severity: SeverityLevel) -> List[SecurityAlert]:
        """Recherche des alertes par niveau de gravité."""
        try:
            models = self.get_queryset().filter(severity=severity.value).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par sévérité {severity}: {str(e)}")
            return []
    
    @cache_result(timeout=120, key_prefix="alerts_by_source_ip")
    def find_by_source_ip(self, source_ip: str) -> List[SecurityAlert]:
        """Recherche des alertes par adresse IP source."""
        try:
            models = self.get_queryset().filter(source_ip=source_ip).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par IP source {source_ip}: {str(e)}")
            return []
    
    def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[SecurityAlert]:
        """Recherche des alertes dans une plage temporelle."""
        try:
            models = self.get_queryset().filter(
                timestamp__gte=start_time,
                timestamp__lte=end_time
            ).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par plage temporelle: {str(e)}")
            return []
    
    def find_related_alerts(self, alert: SecurityAlert) -> List[SecurityAlert]:
        """Recherche des alertes liées à une alerte donnée."""
        try:
            # Rechercher des alertes dans une fenêtre temporelle
            time_window = timedelta(hours=1)
            start_time = alert.timestamp - time_window
            end_time = alert.timestamp + time_window
            
            # Construire les critères de similarité
            related_filters = Q(timestamp__range=(start_time, end_time))
            
            # Exclure l'alerte elle-même
            if alert.id:
                related_filters &= ~Q(id=alert.id.value)
            
            similarity_filters = Q()
            
            # Alertes de la même IP source
            if alert.source_ip:
                similarity_filters |= Q(source_ip=alert.source_ip)
            
            # Alertes de la même IP destination
            if alert.destination_ip:
                similarity_filters |= Q(destination_ip=alert.destination_ip)
            
            # Alertes du même type
            if alert.alert_type:
                similarity_filters |= Q(alert_type=alert.alert_type)
            
            # Alertes de même sévérité
            if alert.severity:
                similarity_filters |= Q(severity=alert.severity)
            
            models = self.get_queryset().filter(
                related_filters & similarity_filters
            ).order_by('-timestamp')[:20]  # Limiter à 20 résultats
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche d'alertes liées: {str(e)}")
            return []
    
    def get_alerts_statistics(self, time_range_days: int = 30) -> Dict[str, Any]:
        """Retourne des statistiques sur les alertes."""
        try:
            cache_key = self._get_cache_key("stats", time_range_days)
            cached_stats = cache.get(cache_key)
            if cached_stats:
                return cached_stats
            
            # Période d'analyse
            end_date = timezone.now()
            start_date = end_date - timedelta(days=time_range_days)
            
            # Statistiques générales
            queryset = self.model_class.objects.filter(timestamp__gte=start_date)
            
            stats = queryset.aggregate(
                total_alerts=Count('id'),
                critical_alerts=Count('id', filter=Q(severity='critical')),
                high_alerts=Count('id', filter=Q(severity='high')),
                medium_alerts=Count('id', filter=Q(severity='medium')),
                low_alerts=Count('id', filter=Q(severity='low')),
                resolved_alerts=Count('id', filter=Q(status='resolved')),
                open_alerts=Count('id', filter=Q(status='open')),
                investigating_alerts=Count('id', filter=Q(status='investigating'))
            )
            
            # Statistiques par type d'alerte
            type_stats = queryset.values('alert_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            stats['by_type'] = {item['alert_type']: item['count'] for item in type_stats}
            
            # Top 10 des IPs sources génératrices d'alertes
            top_source_ips = queryset.exclude(
                source_ip__isnull=True
            ).values('source_ip').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            stats['top_source_ips'] = list(top_source_ips)
            
            # Tendances horaires
            hourly_stats = queryset.annotate(
                hour=TruncHour('timestamp')
            ).values('hour').annotate(
                count=Count('id')
            ).order_by('hour')
            
            stats['hourly_trend'] = list(hourly_stats)
            
            # Temps de résolution moyen (pour les alertes résolues)
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT AVG(EXTRACT(EPOCH FROM (updated_at - timestamp))) / 3600 as avg_resolution_hours
                    FROM security_management_securityalertmodel 
                    WHERE status = 'resolved' 
                    AND timestamp >= %s
                    AND updated_at > timestamp
                """, [start_date])
                
                result = cursor.fetchone()
                stats['avg_resolution_hours'] = round(result[0] or 0, 2)
            
            # Taux de faux positifs (estimation basée sur les alertes fermées rapidement)
            quick_closures = queryset.filter(
                status='resolved',
                updated_at__lte=F('timestamp') + timedelta(minutes=30)
            ).count()
            
            total_resolved = stats['resolved_alerts']
            stats['estimated_false_positive_rate'] = round(
                (quick_closures / max(total_resolved, 1)) * 100, 2
            )
            
            cache.set(cache_key, stats, 300)  # Cache 5 minutes
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques d'alertes: {str(e)}")
            return {}
    
    def get_correlation_matrix(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Calcule une matrice de corrélation entre différents types d'alertes."""
        try:
            # Période d'analyse
            end_time = timezone.now()
            start_time = end_time - timedelta(hours=time_range_hours)
            
            # Récupérer les alertes dans la période
            alerts = self.model_class.objects.filter(
                timestamp__gte=start_time
            ).values('alert_type', 'source_ip', 'timestamp').order_by('timestamp')
            
            # Construire la matrice de corrélation
            correlation_matrix = defaultdict(lambda: defaultdict(int))
            alert_types = set()
            
            # Grouper les alertes par fenêtres de 10 minutes
            time_windows = defaultdict(lambda: defaultdict(set))
            
            for alert in alerts:
                alert_type = alert['alert_type']
                source_ip = alert['source_ip']
                timestamp = alert['timestamp']
                
                alert_types.add(alert_type)
                
                # Calculer la fenêtre temporelle (tranches de 10 minutes)
                window = timestamp.replace(minute=(timestamp.minute // 10) * 10, second=0, microsecond=0)
                time_windows[window][alert_type].add(source_ip)
            
            # Calculer les corrélations
            for window_alerts in time_windows.values():
                alert_types_in_window = list(window_alerts.keys())
                
                # Pour chaque paire de types d'alertes dans la même fenêtre
                for i, type1 in enumerate(alert_types_in_window):
                    for j, type2 in enumerate(alert_types_in_window):
                        if i <= j:  # Éviter les doublons
                            # Vérifier s'il y a des IPs communes
                            common_ips = window_alerts[type1] & window_alerts[type2]
                            if common_ips:
                                correlation_matrix[type1][type2] += len(common_ips)
                                if type1 != type2:
                                    correlation_matrix[type2][type1] += len(common_ips)
            
            # Normaliser la matrice
            max_correlation = max(
                max(row.values()) if row else 0 
                for row in correlation_matrix.values()
            ) or 1
            
            normalized_matrix = {}
            for type1 in alert_types:
                normalized_matrix[type1] = {}
                for type2 in alert_types:
                    value = correlation_matrix[type1][type2]
                    normalized_matrix[type1][type2] = round(value / max_correlation, 3)
            
            return {
                'correlation_matrix': normalized_matrix,
                'alert_types': sorted(alert_types),
                'time_range_hours': time_range_hours,
                'total_correlations': sum(
                    sum(row.values()) for row in correlation_matrix.values()
                )
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la matrice de corrélation: {str(e)}")
            return {}
    
    def _model_to_entity(self, model: SecurityAlertModel) -> SecurityAlert:
        """Convertit un modèle Django en entité du domaine."""
        return SecurityAlert(
            id=EntityId(model.id),
            alert_type=model.alert_type,
            severity=SeverityLevel(model.severity) if model.severity else None,
            title=model.title,
            description=model.description,
            source_ip=model.source_ip,
            destination_ip=model.destination_ip,
            timestamp=model.timestamp,
            status=AlertStatus(model.status) if model.status else None,
            rule_id=EntityId(model.rule_id) if model.rule_id else None,
            raw_data=json.loads(model.raw_data) if model.raw_data else {},
            metadata=json.loads(model.metadata) if model.metadata else {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model(self, entity: SecurityAlert) -> SecurityAlertModel:
        """Convertit une entité du domaine en modèle Django."""
        return SecurityAlertModel(
            alert_type=entity.alert_type,
            severity=entity.severity.value if entity.severity else None,
            title=entity.title,
            description=entity.description,
            source_ip=entity.source_ip,
            destination_ip=entity.destination_ip,
            timestamp=entity.timestamp,
            status=entity.status.value if entity.status else None,
            rule_id=entity.rule_id.value if entity.rule_id else None,
            raw_data=json.dumps(entity.raw_data) if entity.raw_data else None,
            metadata=json.dumps(entity.metadata) if entity.metadata else None
        )
    
    def _update_model_from_entity(self, model: SecurityAlertModel, entity: SecurityAlert):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.alert_type = entity.alert_type
        model.severity = entity.severity.value if entity.severity else None
        model.title = entity.title
        model.description = entity.description
        model.source_ip = entity.source_ip
        model.destination_ip = entity.destination_ip
        model.timestamp = entity.timestamp
        model.status = entity.status.value if entity.status else None
        model.rule_id = entity.rule_id.value if entity.rule_id else None
        model.raw_data = json.dumps(entity.raw_data) if entity.raw_data else None
        model.metadata = json.dumps(entity.metadata) if entity.metadata else None
    
    def _invalidate_related_caches(self):
        """Invalide les caches liés aux alertes."""
        patterns = [
            "repo:securityalertmodel:alerts_all:",
            "repo:securityalertmodel:alerts_by_status:",
            "repo:securityalertmodel:alerts_by_severity:",
            "repo:securityalertmodel:stats"
        ]
        
        for pattern in patterns:
            try:
                cache.delete_many([pattern])
            except Exception:
                pass


class DjangoCorrelationRuleRepository(BaseRepository, CorrelationRuleRepository):
    """
    Repository Django sophistiqué pour les règles de corrélation.
    """
    
    def __init__(self):
        """Initialise le repository pour les règles de corrélation."""
        super().__init__(CorrelationRuleModel)
        logger.info("DjangoCorrelationRuleRepository initialisé")
    
    def get_by_id(self, entity_id: EntityId) -> Optional[CorrelationRule]:
        """Récupère une règle de corrélation par son ID."""
        try:
            model = self.get_queryset().get(id=entity_id.value)
            return self._model_to_entity(model)
        except self.model_class.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la règle de corrélation {entity_id}: {str(e)}")
            return None
    
    @cache_result(timeout=300, key_prefix="correlation_rules_all")
    def list_all(self) -> List[CorrelationRule]:
        """Liste toutes les règles de corrélation."""
        try:
            models = self.get_queryset().all()
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la liste des règles de corrélation: {str(e)}")
            return []
    
    @transaction.atomic
    def save(self, entity: CorrelationRule) -> CorrelationRule:
        """Sauvegarde une règle de corrélation."""
        try:
            if entity.id:
                # Mise à jour
                model = self.model_class.objects.get(id=entity.id.value)
                self._update_model_from_entity(model, entity)
            else:
                # Création
                model = self._entity_to_model(entity)
            
            model.save()
            
            # Invalider les caches
            self._invalidate_related_caches()
            
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la règle de corrélation: {str(e)}")
            raise
    
    def delete(self, entity_id: EntityId) -> bool:
        """Supprime une règle de corrélation."""
        try:
            deleted, _ = self.model_class.objects.filter(id=entity_id.value).delete()
            
            if deleted > 0:
                self._invalidate_related_caches()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la règle de corrélation {entity_id}: {str(e)}")
            return False
    
    @cache_result(timeout=180, key_prefix="correlation_rules_active")
    def find_active_rules(self) -> List[CorrelationRule]:
        """Récupère toutes les règles de corrélation actives."""
        try:
            models = self.get_queryset().filter(enabled=True).order_by('priority', 'name')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des règles actives: {str(e)}")
            return []
    
    @transaction.atomic
    def increment_trigger_count(self, rule_id: EntityId) -> None:
        """Incrémente le compteur de déclenchements d'une règle."""
        try:
            self.model_class.objects.filter(id=rule_id.value).update(
                trigger_count=F('trigger_count') + 1,
                last_triggered=timezone.now()
            )
            
            # Invalider le cache
            cache.delete(self._get_cache_key("correlation_rules_active"))
            
        except Exception as e:
            logger.error(f"Erreur lors de l'incrémentation du compteur: {str(e)}")
    
    def _model_to_entity(self, model: CorrelationRuleModel) -> CorrelationRule:
        """Convertit un modèle Django en entité du domaine."""
        return CorrelationRule(
            id=EntityId(model.id),
            name=model.name,
            description=model.description,
            conditions=json.loads(model.conditions) if model.conditions else [],
            time_window_minutes=model.time_window_minutes,
            min_events=model.min_events,
            enabled=model.enabled,
            severity=model.severity,
            priority=model.priority,
            correlation_fields=json.loads(model.correlation_fields) if model.correlation_fields else [],
            trigger_count=model.trigger_count,
            last_triggered=model.last_triggered,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model(self, entity: CorrelationRule) -> CorrelationRuleModel:
        """Convertit une entité du domaine en modèle Django."""
        return CorrelationRuleModel(
            name=entity.name,
            description=entity.description,
            conditions=json.dumps(entity.conditions) if entity.conditions else None,
            time_window_minutes=entity.time_window_minutes,
            min_events=entity.min_events,
            enabled=entity.enabled,
            severity=entity.severity,
            priority=entity.priority,
            correlation_fields=json.dumps(entity.correlation_fields) if entity.correlation_fields else None,
            trigger_count=entity.trigger_count or 0,
            last_triggered=entity.last_triggered
        )
    
    def _update_model_from_entity(self, model: CorrelationRuleModel, entity: CorrelationRule):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.name = entity.name
        model.description = entity.description
        model.conditions = json.dumps(entity.conditions) if entity.conditions else None
        model.time_window_minutes = entity.time_window_minutes
        model.min_events = entity.min_events
        model.enabled = entity.enabled
        model.severity = entity.severity
        model.priority = entity.priority
        model.correlation_fields = json.dumps(entity.correlation_fields) if entity.correlation_fields else None
        model.trigger_count = entity.trigger_count or 0
        model.last_triggered = entity.last_triggered
    
    def _invalidate_related_caches(self):
        """Invalide les caches liés aux règles de corrélation."""
        patterns = [
            "repo:correlationrulemodel:correlation_rules_all:",
            "repo:correlationrulemodel:correlation_rules_active:"
        ]
        
        for pattern in patterns:
            try:
                cache.delete_many([pattern])
            except Exception:
                pass


class DjangoCorrelationRuleMatchRepository(BaseRepository, CorrelationRuleMatchRepository):
    """
    Repository Django sophistiqué pour les correspondances de règles de corrélation.
    """
    
    def __init__(self):
        """Initialise le repository pour les correspondances de règles."""
        super().__init__(CorrelationRuleMatchModel)
        logger.info("DjangoCorrelationRuleMatchRepository initialisé")
    
    def get_by_id(self, entity_id: EntityId) -> Optional[CorrelationRuleMatch]:
        """Récupère une correspondance par son ID."""
        try:
            model = self.get_queryset().get(id=entity_id.value)
            return self._model_to_entity(model)
        except self.model_class.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la correspondance {entity_id}: {str(e)}")
            return None
    
    def list_all(self) -> List[CorrelationRuleMatch]:
        """Liste toutes les correspondances."""
        try:
            models = self.get_queryset().order_by('-matched_at')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la liste des correspondances: {str(e)}")
            return []
    
    @transaction.atomic
    def save(self, entity: CorrelationRuleMatch) -> CorrelationRuleMatch:
        """Sauvegarde une correspondance de règle."""
        try:
            if entity.id:
                # Mise à jour
                model = self.model_class.objects.get(id=entity.id.value)
                self._update_model_from_entity(model, entity)
            else:
                # Création
                model = self._entity_to_model(entity)
            
            model.save()
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la correspondance: {str(e)}")
            raise
    
    def delete(self, entity_id: EntityId) -> bool:
        """Supprime une correspondance."""
        try:
            deleted, _ = self.model_class.objects.filter(id=entity_id.value).delete()
            return deleted > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression de la correspondance {entity_id}: {str(e)}")
            return False
    
    def find_by_rule_id(self, rule_id: EntityId) -> List[CorrelationRuleMatch]:
        """Récupère les correspondances pour une règle donnée."""
        try:
            models = self.get_queryset().filter(
                correlation_rule_id=rule_id.value
            ).order_by('-matched_at')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par règle {rule_id}: {str(e)}")
            return []
    
    def find_recent_matches(self, limit: int = 50) -> List[CorrelationRuleMatch]:
        """Récupère les correspondances récentes."""
        try:
            models = self.get_queryset().order_by('-matched_at')[:limit]
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des correspondances récentes: {str(e)}")
            return []
    
    def _model_to_entity(self, model: CorrelationRuleMatchModel) -> CorrelationRuleMatch:
        """Convertit un modèle Django en entité du domaine."""
        return CorrelationRuleMatch(
            id=EntityId(model.id),
            correlation_rule_id=EntityId(model.correlation_rule_id),
            matched_at=model.matched_at,
            triggering_events=json.loads(model.triggering_events) if model.triggering_events else [],
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model(self, entity: CorrelationRuleMatch) -> CorrelationRuleMatchModel:
        """Convertit une entité du domaine en modèle Django."""
        return CorrelationRuleMatchModel(
            correlation_rule_id=entity.correlation_rule_id.value,
            matched_at=entity.matched_at,
            triggering_events=json.dumps(entity.triggering_events) if entity.triggering_events else None
        )
    
    def _update_model_from_entity(self, model: CorrelationRuleMatchModel, entity: CorrelationRuleMatch):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.correlation_rule_id = entity.correlation_rule_id.value
        model.matched_at = entity.matched_at
        model.triggering_events = json.dumps(entity.triggering_events) if entity.triggering_events else None


class DjangoAuditLogRepository(BaseRepository, AuditLogRepository):
    """
    Repository Django sophistiqué pour les journaux d'audit.
    """
    
    def __init__(self):
        """Initialise le repository pour les journaux d'audit."""
        super().__init__(AuditLogModel)
        logger.info("DjangoAuditLogRepository initialisé")
    
    def get_by_id(self, entity_id: EntityId) -> Optional[AuditLog]:
        """Récupère un journal d'audit par son ID."""
        try:
            model = self.get_queryset().get(id=entity_id.value)
            return self._model_to_entity(model)
        except self.model_class.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du journal {entity_id}: {str(e)}")
            return None
    
    def list_all(self) -> List[AuditLog]:
        """Liste tous les journaux d'audit."""
        try:
            # Limiter aux logs récents par défaut
            one_month_ago = timezone.now() - timedelta(days=30)
            models = self.get_queryset().filter(timestamp__gte=one_month_ago).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la liste des journaux: {str(e)}")
            return []
    
    @transaction.atomic
    def save(self, entity: AuditLog) -> AuditLog:
        """Sauvegarde un journal d'audit."""
        try:
            if entity.id:
                # Mise à jour
                model = self.model_class.objects.get(id=entity.id.value)
                self._update_model_from_entity(model, entity)
            else:
                # Création
                model = self._entity_to_model(entity)
            
            model.save()
            return self._model_to_entity(model)
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du journal: {str(e)}")
            raise
    
    def delete(self, entity_id: EntityId) -> bool:
        """Supprime un journal d'audit."""
        try:
            deleted, _ = self.model_class.objects.filter(id=entity_id.value).delete()
            return deleted > 0
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du journal {entity_id}: {str(e)}")
            return False
    
    def find_by_user(self, user: str) -> List[AuditLog]:
        """Recherche des journaux par utilisateur."""
        try:
            models = self.get_queryset().filter(user=user).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par utilisateur {user}: {str(e)}")
            return []
    
    def find_by_action(self, action: str) -> List[AuditLog]:
        """Recherche des journaux par action."""
        try:
            models = self.get_queryset().filter(action=action).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par action {action}: {str(e)}")
            return []
    
    def find_by_entity(self, entity_type: str, entity_id: str) -> List[AuditLog]:
        """Recherche des journaux par entité."""
        try:
            models = self.get_queryset().filter(
                entity_type=entity_type,
                entity_id=entity_id
            ).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par entité {entity_type}:{entity_id}: {str(e)}")
            return []
    
    def find_by_time_range(self, start_time: datetime, end_time: datetime) -> List[AuditLog]:
        """Recherche des journaux dans une plage temporelle."""
        try:
            models = self.get_queryset().filter(
                timestamp__gte=start_time,
                timestamp__lte=end_time
            ).order_by('-timestamp')
            return [self._model_to_entity(model) for model in models]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche par plage temporelle: {str(e)}")
            return []
    
    def _model_to_entity(self, model: AuditLogModel) -> AuditLog:
        """Convertit un modèle Django en entité du domaine."""
        return AuditLog(
            id=EntityId(model.id),
            user=model.user,
            action=model.action,
            entity_type=model.entity_type,
            entity_id=model.entity_id,
            timestamp=model.timestamp,
            details=json.loads(model.details) if model.details else {},
            ip_address=model.ip_address,
            user_agent=model.user_agent,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _entity_to_model(self, entity: AuditLog) -> AuditLogModel:
        """Convertit une entité du domaine en modèle Django."""
        return AuditLogModel(
            user=entity.user,
            action=entity.action,
            entity_type=entity.entity_type,
            entity_id=entity.entity_id,
            timestamp=entity.timestamp,
            details=json.dumps(entity.details) if entity.details else None,
            ip_address=entity.ip_address,
            user_agent=entity.user_agent
        )
    
    def _update_model_from_entity(self, model: AuditLogModel, entity: AuditLog):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.user = entity.user
        model.action = entity.action
        model.entity_type = entity.entity_type
        model.entity_id = entity.entity_id
        model.timestamp = entity.timestamp
        model.details = json.dumps(entity.details) if entity.details else None
        model.ip_address = entity.ip_address
        model.user_agent = entity.user_agent


class DjangoSecurityPolicyRepository:
    """Repository Django pour les politiques de sécurité."""
    
    def save(self, policy):
        """Sauvegarde une politique de sécurité."""
        from ..infrastructure.models import SecurityPolicyModel
        if policy.id:
            model = SecurityPolicyModel.objects.get(id=policy.id.value)
            self._update_model_from_entity(model, policy)
        else:
            model = self._entity_to_model(policy)
        model.save()
        policy.id = EntityId(model.id)
        return policy
    
    def get_by_id(self, policy_id):
        """Récupère une politique par son ID."""
        try:
            from ..infrastructure.models import SecurityPolicyModel
            model = SecurityPolicyModel.objects.get(id=policy_id.value)
            return self._model_to_entity(model)
        except SecurityPolicyModel.DoesNotExist:
            return None
    
    def get_all(self):
        """Récupère toutes les politiques."""
        from ..infrastructure.models import SecurityPolicyModel
        models = SecurityPolicyModel.objects.all()
        return [self._model_to_entity(model) for model in models]
    
    def get_active_policies(self):
        """Récupère les politiques actives."""
        from ..infrastructure.models import SecurityPolicyModel
        models = SecurityPolicyModel.objects.filter(is_active=True)
        return [self._model_to_entity(model) for model in models]
    
    def delete(self, policy_id):
        """Supprime une politique."""
        try:
            from ..infrastructure.models import SecurityPolicyModel
            SecurityPolicyModel.objects.get(id=policy_id.value).delete()
            return True
        except SecurityPolicyModel.DoesNotExist:
            return False
    
    def _model_to_entity(self, model):
        """Convertit un modèle Django en entité du domaine."""
        from ..domain.entities import SecurityPolicy
        return SecurityPolicy(
            id=EntityId(model.id),
            name=model.name,
            description=model.description,
            rules=model.rules,
            is_active=model.is_active,
            created_by=model.created_by
        )
    
    def _entity_to_model(self, entity):
        """Convertit une entité du domaine en modèle Django."""
        from ..infrastructure.models import SecurityPolicyModel
        return SecurityPolicyModel(
            name=entity.name,
            description=entity.description,
            rules=entity.rules,
            is_active=entity.is_active,
            created_by=entity.created_by
        )
    
    def _update_model_from_entity(self, model, entity):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.name = entity.name
        model.description = entity.description
        model.rules = entity.rules
        model.is_active = entity.is_active
        model.created_by = entity.created_by


class DjangoVulnerabilityRepository:
    """Repository Django pour les vulnérabilités."""
    
    def save(self, vulnerability):
        """Sauvegarde une vulnérabilité."""
        from ..infrastructure.models import VulnerabilityModel
        if vulnerability.id:
            model = VulnerabilityModel.objects.get(id=vulnerability.id.value)
            self._update_model_from_entity(model, vulnerability)
        else:
            model = self._entity_to_model(vulnerability)
        model.save()
        vulnerability.id = EntityId(model.id)
        return vulnerability
    
    def get_by_id(self, vuln_id):
        """Récupère une vulnérabilité par son ID."""
        try:
            from ..infrastructure.models import VulnerabilityModel
            model = VulnerabilityModel.objects.get(id=vuln_id.value)
            return self._model_to_entity(model)
        except VulnerabilityModel.DoesNotExist:
            return None
    
    def get_by_cve_id(self, cve_id):
        """Récupère une vulnérabilité par son CVE ID."""
        try:
            from ..infrastructure.models import VulnerabilityModel
            model = VulnerabilityModel.objects.get(cve_id=cve_id)
            return self._model_to_entity(model)
        except VulnerabilityModel.DoesNotExist:
            return None
    
    def get_all(self):
        """Récupère toutes les vulnérabilités."""
        from ..infrastructure.models import VulnerabilityModel
        models = VulnerabilityModel.objects.all()
        return [self._model_to_entity(model) for model in models]
    
    def get_by_severity(self, severity):
        """Récupère les vulnérabilités par sévérité."""
        from ..infrastructure.models import VulnerabilityModel
        models = VulnerabilityModel.objects.filter(severity=severity)
        return [self._model_to_entity(model) for model in models]
    
    def get_by_status(self, status):
        """Récupère les vulnérabilités par statut."""
        from ..infrastructure.models import VulnerabilityModel
        models = VulnerabilityModel.objects.filter(status=status)
        return [self._model_to_entity(model) for model in models]
    
    def get_affecting_system(self, system):
        """Récupère les vulnérabilités affectant un système."""
        from ..infrastructure.models import VulnerabilityModel
        models = VulnerabilityModel.objects.filter(affected_systems__contains=[system])
        return [self._model_to_entity(model) for model in models]
    
    def _model_to_entity(self, model):
        """Convertit un modèle Django en entité du domaine."""
        from ..domain.entities import Vulnerability, SeverityLevel
        return Vulnerability(
            id=EntityId(model.id),
            cve_id=model.cve_id,
            title=model.title,
            description=model.description,
            severity=SeverityLevel(model.severity),
            cvss_score=model.cvss_score,
            cvss_vector=model.cvss_vector,
            cwe_id=model.cwe_id,
            affected_systems=model.affected_systems,
            affected_software=model.affected_software,
            affected_versions=model.affected_versions,
            status=model.status,
            discovered_date=model.discovered_date,
            published_date=model.published_date,
            patched_date=model.patched_date,
            references=model.references,
            patch_available=model.patch_available,
            patch_info=model.patch_info,
            assigned_to=model.assigned_to,
            priority=model.priority
        )
    
    def _entity_to_model(self, entity):
        """Convertit une entité du domaine en modèle Django."""
        from ..infrastructure.models import VulnerabilityModel
        return VulnerabilityModel(
            cve_id=entity.cve_id,
            title=entity.title,
            description=entity.description,
            severity=entity.severity.value,
            cvss_score=entity.cvss_score,
            cvss_vector=entity.cvss_vector,
            cwe_id=entity.cwe_id,
            affected_systems=entity.affected_systems,
            affected_software=entity.affected_software,
            affected_versions=entity.affected_versions,
            status=entity.status,
            discovered_date=entity.discovered_date,
            published_date=entity.published_date,
            patched_date=entity.patched_date,
            references=entity.references,
            patch_available=entity.patch_available,
            patch_info=entity.patch_info,
            assigned_to=entity.assigned_to,
            priority=entity.priority
        )
    
    def _update_model_from_entity(self, model, entity):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.cve_id = entity.cve_id
        model.title = entity.title
        model.description = entity.description
        model.severity = entity.severity.value
        model.cvss_score = entity.cvss_score
        model.cvss_vector = entity.cvss_vector
        model.cwe_id = entity.cwe_id
        model.affected_systems = entity.affected_systems
        model.affected_software = entity.affected_software
        model.affected_versions = entity.affected_versions
        model.status = entity.status
        model.discovered_date = entity.discovered_date
        model.published_date = entity.published_date
        model.patched_date = entity.patched_date
        model.references = entity.references
        model.patch_available = entity.patch_available
        model.patch_info = entity.patch_info
        model.assigned_to = entity.assigned_to
        model.priority = entity.priority


class DjangoThreatIntelligenceRepository:
    """Repository Django pour l'intelligence de menaces."""
    
    def save(self, threat):
        """Sauvegarde un indicateur de menace."""
        from ..infrastructure.models import ThreatIntelligenceModel
        if threat.id:
            model = ThreatIntelligenceModel.objects.get(id=threat.id.value)
            self._update_model_from_entity(model, threat)
        else:
            model = self._entity_to_model(threat)
        model.save()
        threat.id = EntityId(model.id)
        return threat
    
    def get_by_id(self, threat_id):
        """Récupère un indicateur par son ID."""
        try:
            from ..infrastructure.models import ThreatIntelligenceModel
            model = ThreatIntelligenceModel.objects.get(id=threat_id.value)
            return self._model_to_entity(model)
        except ThreatIntelligenceModel.DoesNotExist:
            return None
    
    def get_by_indicator(self, indicator_type, value):
        """Récupère un indicateur par type et valeur."""
        try:
            from ..infrastructure.models import ThreatIntelligenceModel
            model = ThreatIntelligenceModel.objects.get(
                indicator_type=indicator_type, 
                indicator_value=value
            )
            return self._model_to_entity(model)
        except ThreatIntelligenceModel.DoesNotExist:
            return None
    
    def get_active_indicators(self):
        """Récupère les indicateurs actifs."""
        from ..infrastructure.models import ThreatIntelligenceModel
        models = ThreatIntelligenceModel.objects.filter(is_active=True)
        return [self._model_to_entity(model) for model in models]
    
    def get_by_threat_type(self, threat_type):
        """Récupère les indicateurs par type de menace."""
        from ..infrastructure.models import ThreatIntelligenceModel
        models = ThreatIntelligenceModel.objects.filter(threat_type=threat_type)
        return [self._model_to_entity(model) for model in models]
    
    def _model_to_entity(self, model):
        """Convertit un modèle Django en entité du domaine."""
        from ..domain.entities import ThreatIntelligence, SeverityLevel
        return ThreatIntelligence(
            id=EntityId(model.id),
            indicator_type=model.indicator_type,
            indicator_value=model.indicator_value,
            threat_type=model.threat_type,
            confidence=model.confidence,
            severity=SeverityLevel(model.severity),
            title=model.title,
            description=model.description,
            tags=model.tags,
            source=model.source,
            source_reliability=model.source_reliability,
            external_id=model.external_id,
            first_seen=model.first_seen,
            last_seen=model.last_seen,
            valid_until=model.valid_until,
            is_active=model.is_active,
            is_whitelisted=model.is_whitelisted,
            context=model.context
        )
    
    def _entity_to_model(self, entity):
        """Convertit une entité du domaine en modèle Django."""
        from ..infrastructure.models import ThreatIntelligenceModel
        return ThreatIntelligenceModel(
            indicator_type=entity.indicator_type,
            indicator_value=entity.indicator_value,
            threat_type=entity.threat_type,
            confidence=entity.confidence,
            severity=entity.severity.value,
            title=entity.title,
            description=entity.description,
            tags=entity.tags,
            source=entity.source,
            source_reliability=entity.source_reliability,
            external_id=entity.external_id,
            first_seen=entity.first_seen,
            last_seen=entity.last_seen,
            valid_until=entity.valid_until,
            is_active=entity.is_active,
            is_whitelisted=entity.is_whitelisted,
            context=entity.context
        )
    
    def _update_model_from_entity(self, model, entity):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.indicator_type = entity.indicator_type
        model.indicator_value = entity.indicator_value
        model.threat_type = entity.threat_type
        model.confidence = entity.confidence
        model.severity = entity.severity.value
        model.title = entity.title
        model.description = entity.description
        model.tags = entity.tags
        model.source = entity.source
        model.source_reliability = entity.source_reliability
        model.external_id = entity.external_id
        model.first_seen = entity.first_seen
        model.last_seen = entity.last_seen
        model.valid_until = entity.valid_until
        model.is_active = entity.is_active
        model.is_whitelisted = entity.is_whitelisted
        model.context = entity.context


class DjangoIncidentResponseWorkflowRepository:
    """Repository Django pour les workflows de réponse aux incidents."""
    
    def save(self, workflow):
        """Sauvegarde un workflow."""
        from ..infrastructure.models import IncidentResponseWorkflowModel
        if workflow.id:
            model = IncidentResponseWorkflowModel.objects.get(id=workflow.id.value)
            self._update_model_from_entity(model, workflow)
        else:
            model = self._entity_to_model(workflow)
        model.save()
        workflow.id = EntityId(model.id)
        return workflow
    
    def get_by_id(self, workflow_id):
        """Récupère un workflow par son ID."""
        try:
            from ..infrastructure.models import IncidentResponseWorkflowModel
            model = IncidentResponseWorkflowModel.objects.get(id=workflow_id.value)
            return self._model_to_entity(model)
        except IncidentResponseWorkflowModel.DoesNotExist:
            return None
    
    def get_all(self):
        """Récupère tous les workflows."""
        from ..infrastructure.models import IncidentResponseWorkflowModel
        models = IncidentResponseWorkflowModel.objects.all()
        return [self._model_to_entity(model) for model in models]
    
    def get_by_status(self, status):
        """Récupère les workflows par statut."""
        from ..infrastructure.models import IncidentResponseWorkflowModel
        models = IncidentResponseWorkflowModel.objects.filter(status=status)
        return [self._model_to_entity(model) for model in models]
    
    def get_by_trigger_type(self, trigger_type):
        """Récupère les workflows par type de déclencheur."""
        from ..infrastructure.models import IncidentResponseWorkflowModel
        models = IncidentResponseWorkflowModel.objects.filter(trigger_type=trigger_type)
        return [self._model_to_entity(model) for model in models]
    
    def _model_to_entity(self, model):
        """Convertit un modèle Django en entité du domaine."""
        from ..domain.entities import IncidentResponseWorkflow
        return IncidentResponseWorkflow(
            id=EntityId(model.id),
            name=model.name,
            description=model.description,
            version=model.version,
            trigger_type=model.trigger_type,
            trigger_conditions=model.trigger_conditions,
            steps=model.steps,
            auto_execute=model.auto_execute,
            requires_approval=model.requires_approval,
            timeout_minutes=model.timeout_minutes,
            assigned_team=model.assigned_team,
            escalation_rules=model.escalation_rules,
            status=model.status,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            execution_count=model.execution_count,
            success_count=model.success_count,
            last_executed=model.last_executed
        )
    
    def _entity_to_model(self, entity):
        """Convertit une entité du domaine en modèle Django."""
        from ..infrastructure.models import IncidentResponseWorkflowModel
        return IncidentResponseWorkflowModel(
            name=entity.name,
            description=entity.description,
            version=entity.version,
            trigger_type=entity.trigger_type,
            trigger_conditions=entity.trigger_conditions,
            steps=entity.steps,
            auto_execute=entity.auto_execute,
            requires_approval=entity.requires_approval,
            timeout_minutes=entity.timeout_minutes,
            assigned_team=entity.assigned_team,
            escalation_rules=entity.escalation_rules,
            status=entity.status,
            created_by=entity.created_by,
            execution_count=entity.execution_count,
            success_count=entity.success_count,
            last_executed=entity.last_executed
        )
    
    def _update_model_from_entity(self, model, entity):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.name = entity.name
        model.description = entity.description
        model.version = entity.version
        model.trigger_type = entity.trigger_type
        model.trigger_conditions = entity.trigger_conditions
        model.steps = entity.steps
        model.auto_execute = entity.auto_execute
        model.requires_approval = entity.requires_approval
        model.timeout_minutes = entity.timeout_minutes
        model.assigned_team = entity.assigned_team
        model.escalation_rules = entity.escalation_rules
        model.status = entity.status
        model.created_by = entity.created_by
        model.execution_count = entity.execution_count
        model.success_count = entity.success_count
        model.last_executed = entity.last_executed


class DjangoIncidentResponseExecutionRepository:
    """Repository Django pour les exécutions de workflows."""
    
    def save(self, execution):
        """Sauvegarde une exécution."""
        from ..infrastructure.models import IncidentResponseExecutionModel
        if execution.id:
            model = IncidentResponseExecutionModel.objects.get(id=execution.id.value)
            self._update_model_from_entity(model, execution)
        else:
            model = self._entity_to_model(execution)
        model.save()
        execution.id = EntityId(model.id)
        return execution
    
    def get_by_id(self, execution_id):
        """Récupère une exécution par son ID."""
        try:
            from ..infrastructure.models import IncidentResponseExecutionModel
            model = IncidentResponseExecutionModel.objects.get(id=execution_id.value)
            return self._model_to_entity(model)
        except IncidentResponseExecutionModel.DoesNotExist:
            return None
    
    def _model_to_entity(self, model):
        """Convertit un modèle Django en entité du domaine."""
        from ..domain.entities import IncidentResponseExecution
        return IncidentResponseExecution(
            id=EntityId(model.id),
            workflow_id=EntityId(model.workflow_id),
            triggered_by_event=model.triggered_by_event,
            status=model.status,
            started_at=model.started_at,
            completed_at=model.completed_at,
            current_step=model.current_step,
            steps_log=model.steps_log,
            assigned_to=model.assigned_to,
            approved_by=model.approved_by,
            approved_at=model.approved_at,
            output_data=model.output_data,
            error_message=model.error_message
        )
    
    def _entity_to_model(self, entity):
        """Convertit une entité du domaine en modèle Django."""
        from ..infrastructure.models import IncidentResponseExecutionModel
        return IncidentResponseExecutionModel(
            workflow_id=entity.workflow_id.value,
            triggered_by_event=entity.triggered_by_event,
            status=entity.status,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            current_step=entity.current_step,
            steps_log=entity.steps_log,
            assigned_to=entity.assigned_to,
            approved_by=entity.approved_by,
            approved_at=entity.approved_at,
            output_data=entity.output_data,
            error_message=entity.error_message
        )
    
    def _update_model_from_entity(self, model, entity):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.workflow_id = entity.workflow_id.value
        model.triggered_by_event = entity.triggered_by_event
        model.status = entity.status
        model.started_at = entity.started_at
        model.completed_at = entity.completed_at
        model.current_step = entity.current_step
        model.steps_log = entity.steps_log
        model.assigned_to = entity.assigned_to
        model.approved_by = entity.approved_by
        model.approved_at = entity.approved_at
        model.output_data = entity.output_data
        model.error_message = entity.error_message


class DjangoSecurityReportRepository:
    """Repository Django pour les rapports de sécurité."""
    
    def save(self, report):
        """Sauvegarde un rapport."""
        from ..infrastructure.models import SecurityReportModel
        if report.id:
            model = SecurityReportModel.objects.get(id=report.id.value)
            self._update_model_from_entity(model, report)
        else:
            model = self._entity_to_model(report)
        model.save()
        report.id = EntityId(model.id)
        return report
    
    def get_by_id(self, report_id):
        """Récupère un rapport par son ID."""
        try:
            from ..infrastructure.models import SecurityReportModel
            model = SecurityReportModel.objects.get(id=report_id.value)
            return self._model_to_entity(model)
        except SecurityReportModel.DoesNotExist:
            return None
    
    def get_all(self):
        """Récupère tous les rapports."""
        from ..infrastructure.models import SecurityReportModel
        models = SecurityReportModel.objects.all()
        return [self._model_to_entity(model) for model in models]
    
    def get_by_report_type(self, report_type):
        """Récupère les rapports par type."""
        from ..infrastructure.models import SecurityReportModel
        models = SecurityReportModel.objects.filter(report_type=report_type)
        return [self._model_to_entity(model) for model in models]
    
    def get_scheduled_reports(self):
        """Récupère les rapports programmés."""
        from ..infrastructure.models import SecurityReportModel
        models = SecurityReportModel.objects.filter(is_scheduled=True)
        return [self._model_to_entity(model) for model in models]
    
    def get_pending_reports(self):
        """Récupère les rapports en attente."""
        from ..infrastructure.models import SecurityReportModel
        models = SecurityReportModel.objects.filter(status='scheduled')
        return [self._model_to_entity(model) for model in models]
    
    def _model_to_entity(self, model):
        """Convertit un modèle Django en entité du domaine."""
        from ..domain.entities import SecurityReport
        return SecurityReport(
            id=EntityId(model.id),
            name=model.name,
            report_type=model.report_type,
            description=model.description,
            parameters=model.parameters,
            filters=model.filters,
            format=model.format,
            is_scheduled=model.is_scheduled,
            schedule_frequency=model.schedule_frequency,
            next_execution=model.next_execution,
            status=model.status,
            generated_at=model.generated_at,
            file_path=model.file_path,
            file_size=model.file_size,
            created_by=model.created_by,
            created_at=model.created_at,
            recipients=model.recipients,
            auto_send=model.auto_send
        )
    
    def _entity_to_model(self, entity):
        """Convertit une entité du domaine en modèle Django."""
        from ..infrastructure.models import SecurityReportModel
        return SecurityReportModel(
            name=entity.name,
            report_type=entity.report_type,
            description=entity.description,
            parameters=entity.parameters,
            filters=entity.filters,
            format=entity.format,
            is_scheduled=entity.is_scheduled,
            schedule_frequency=entity.schedule_frequency,
            next_execution=entity.next_execution,
            status=entity.status,
            generated_at=entity.generated_at,
            file_path=entity.file_path,
            file_size=entity.file_size,
            created_by=entity.created_by,
            recipients=entity.recipients,
            auto_send=entity.auto_send
        )
    
    def _update_model_from_entity(self, model, entity):
        """Met à jour un modèle Django depuis une entité du domaine."""
        model.name = entity.name
        model.report_type = entity.report_type
        model.description = entity.description
        model.parameters = entity.parameters
        model.filters = entity.filters
        model.format = entity.format
        model.is_scheduled = entity.is_scheduled
        model.schedule_frequency = entity.schedule_frequency
        model.next_execution = entity.next_execution
        model.status = entity.status
        model.generated_at = entity.generated_at
        model.file_path = entity.file_path
        model.file_size = entity.file_size
        model.created_by = entity.created_by
        model.recipients = entity.recipients
        model.auto_send = entity.auto_send


# Instances globales des repositories
security_rule_repository = DjangoSecurityRuleRepository()
security_alert_repository = DjangoSecurityAlertRepository()
security_policy_repository = DjangoSecurityPolicyRepository()
vulnerability_repository = DjangoVulnerabilityRepository()
threat_intelligence_repository = DjangoThreatIntelligenceRepository()
incident_response_workflow_repository = DjangoIncidentResponseWorkflowRepository()
incident_response_execution_repository = DjangoIncidentResponseExecutionRepository()
security_report_repository = DjangoSecurityReportRepository()
correlation_rule_repository = DjangoCorrelationRuleRepository()
correlation_rule_match_repository = DjangoCorrelationRuleMatchRepository()
audit_log_repository = DjangoAuditLogRepository()